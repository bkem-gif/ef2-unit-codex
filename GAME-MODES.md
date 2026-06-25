# EF2 Game Modes & Battle Architecture

A companion to the **Unit Mechanics Codex**. Where the codex documents *units* (how each one
fights), this documents the *battle modes* that wrap them — focused on **Infinite Ranking**, the
competitive PvP ladder, and the shared battle-controller architecture behind every game mode.

> **Sourcing.** Reverse-engineered read-only from the **live game bundle `1.11.52`**
> (`runtime/bundles/mounted/1.11.52/assets/index.js`). Note: the Unit Codex was built on `1.11.42`,
> which the game has since superseded — `1.11.52` is the current client. Byte offsets below are into
> the `1.11.52` bundle and are provided as provenance; they will drift on the next update. Mechanics
> are exact from the code. Matchmaking, scoring, and reward grants are **server-side** and noted as such.

---

## Part 1 — The battle-controller architecture

Every *finite* battle in EF2 is a subclass of one base battle controller. They all share the unit
combat engine (the `qQ` unit hierarchy, weapons, buffs and status effects the codex documents) and
differ only in **setup** (who's on each side, at what level) and **resolution** (`checkVictory` /
`checkDefeat`). The endless idle climb is the one exception — it is *not* a battle controller at all.

| Mode | Controller (class) | Win condition | Loss / timeout |
|---|---|---|---|
| **Idle / endless climb** | *(none — wave loop)* | never "wins" — climbs `wL.maxWave` forever | — |
| Guild War | `GuildWarBattleController` (`r8`) | all enemies dead | all allies dead, or time limit |
| Tower | `TowerBattleController` | all enemies dead | all allies dead, or time limit |
| Dungeon | *(dungeon controller)* | enemy castle razed / all enemies dead | timeout, with a defeat grace period |
| Raid | *(raid controller)* | boss dead | all allies dead, or time limit → report damage |
| **Infinite Ranking** | **`PVP2BattleController` (`Tst`)**, march mode | **wipe the enemy team** | 60s timeout → fewer units alive |
| *(PvP castle-duel)* | `PVP2BattleController`, castle mode / `PVPBattleController` (`a8`) | raze enemy castle | 90/60s timeout → lower castle-HP% |

**The shared loop.** The base controller ticks `checkProgress(){ checkVictory() ? handleVictory()
: checkDefeat() && handleDefeat() }` with a one-shot `battleEnded` latch. Each subclass only overrides
`checkVictory` / `checkDefeat` / `onVictoryCallback` / `onDefeatCallback`.

**The runtime mode flag.** One global stat manager `KN` holds a `_battleContext` (enum `NN`:
`Normal · Sprite · Dungeon · GuildPvp · Pvp · Tower`). Entering a battle calls
`KN.getInstance().setBattleContext(NN.X)`, which clears the multiplier cache; every per-unit stat
lookup is then keyed by that context (`maxHp = baseMaxHp * getMultiplier(..., _battleContext)`). This
is how the *same* unit gets different scaling in scenario vs. dungeon vs. PvP without touching the
unit code.

---

## Part 2 — Infinite Ranking (the deep dive)

**What it is.** An asynchronous "ghost" PvP ladder. You fight frozen **snapshots of other players'
defense teams** — never a live player, never AI. It runs in **4-day cycles**, sorts players into
**leagues** (`userPvp.grade`: `1–4` → `C/B/A/S`), and at the end of each round pays **Gems + Honor
Coins by final rank** (mailed out). The whole fight is **simulated on your device**; the server only
matches you and keeps score.

### Knight Order Level — the equalizer

In the idle game, live power swings wildly (idle buffs, rebirth stacks). Infinite Ranking throws all
of that out and re-levels **every unit on both sides** to a single number derived purely from
progression:

```
knightLevel = Math.floor(wL.maxWave / 100)      // 1 level per 100 waves
```

`maxWave` is **server-authoritative** (copied into the client from the server payload); the client
only *derives* the level. In **Infinite Ranking** a unit's normal level is discarded and the team is
built directly at the plain knight level — yours from `wL.maxWave`, the opponent's from their `maxWave`:

```js
// PvP / ranking team build (all 7 team-VO sites use the plain floor, no bonus):
vo.level = Math.floor(wL.maxWave / 100)        // ally;  opponent: Math.floor(opInfo.maxWave / 100)
spawnUnit(..., level) → u.level = level → applyRawBvoStats(unit, kind, trans, level)
```

**No race/tribe bonus applies in ranking.** The *idle game* does grant a race bonus: when
`battleContext === NN.Normal`, a unit's `totalLevelExp` adds `getKnightLevel(tribe)` =
`floor(maxWave/100)+1` for units matching your own tribe (the "(+@@)" the in-game text shows). **That term
is gated to the idle game only** — `totalLevelExp` early-returns `level + enhance + extraLevel − 1` whenever
`battleContext !== NN.Normal` (and always for enemies). Infinite Ranking runs in `NN.Pvp`, so **every unit
fights at the plain Knight Order Level with no own-race advantage**.

> Two bonuses that belong to *other* modes, not ranking: the per-grade **`heroLevelBonus`**
> (`getPlusLevel(grade)`) is set only by the **guild-war** corps path (`setTeams`/`setupCorp`); and the
> +3%/level **medal** gameplay buff is an idle-game gameplay buff (a sibling of the `PlusLv` total that
> `totalLevelExp` likewise gates to `NN.Normal`). Neither is confirmed in the PvP ranking path.

### The combat pipeline

1. **Launch.** Menu category `aet.INFINITE_RANKING (=2)` → opponent-list popup → VS/ready popup
   (`PVP2ReadyPopup`). "Fight" posts `/pvp/startBattle {oppoId}`; the server returns a `battleId`.
   The client then runs the fight locally via
   `PVP2BattleController.startMarchBattle(myTeam, oppTeam, floor(oppMaxWave/100))`, which sets
   `marchMode = true` and `setBattleContext(NN.Pvp)`. (The controller's declared `battleType` is
   `GUILD_WAR` — Infinite Ranking **reuses the guild-war formation engine**; `NN.Pvp` is what swaps
   in PvP scaling.)
2. **Opponents.** `/pvp/getOpponentList` returns candidate records — each with
   `uid, name, rank, point, win, maxWave,` and a **`team`** string. The team string is decoded by
   `parseTeamData`: format `"kindNum-trans|kindNum-trans|…"` (unit id + transcendence/star). The
   enemy units are then **fabricated client-side** from `(kindNum, level, trans)` with `id = -1`
   (synthetic, no server object) and placed into a fixed 10-slot `ENEMY_FORMATION` (the ally formation
   mirrored across x). **No RNG seed is sent.**
3. **Leveling.** Both armies are spawned at Knight Order Level (yours from local `wL.maxWave`, the
   opponent's from *their* server-provided `maxWave`), per Part 2 above.
4. **Simulation.** The same unit/weapon/buff engine as the codex, run to a conclusion.
5. **Resolution (the live branch — `marchMode = true`):**
   ```js
   checkVictory = (enemySpawnQueue empty && every enemy dead)
                || (timeExpired && myAliveCount >  enemyAliveCount)
   checkDefeat  = (allySpawnQueue  empty && every ally  dead)
                || (timeExpired && myAliveCount <= enemyAliveCount)
   ```
   So you win by **eliminating the enemy team**; if the **60-second** cap
   (`PVP_TIME_LIMIT_FRAMES = 3600`) expires, the side with **more units alive** wins — and a **tie
   goes to the defender** (defeat uses `<=`).
6. **Reporting.** On end the client posts only `/pvp/endBattle {battleId, isWin}` — a single boolean.
   The **server owns scoring**: it returns `{gainPoint, newPoint, gem}`, and the client just adopts the
   new point/gem totals and refreshes the rank UI.

### Client vs. server split

| | **Server provides** | **Client computes / simulates** |
|---|---|---|
| Matchmaking | opponent list (`uid/rank/point/win/maxWave/team`) | — |
| Battle handle | `battleId` (bare token) | — |
| Player state | `userPvp` (grade, rank, point, ticket), `maxWave` | `knightLevel = floor(maxWave/100)` |
| Army build | the `team` string only | decode → unit kind/level/trans → stats from local book/VO |
| The fight | nothing (no seed) | **entire simulation, kills, win/lose** |
| Outcome value | `{gainPoint, newPoint, gem}` on `/pvp/endBattle` | sends only `{battleId, isWin}` |

> **Notable:** the **outcome is client-authoritative** — the client reports a *trusted* `isWin`
> boolean and the server does not replay the fight. (Contrast the Fossil Excavation board, which is
> fully server-authoritative.) Scoring, league transitions, and the mailed rank rewards are server-side.

---

## Part 3 — The two PvP branches (the interesting part)

The win condition above is only *one* of two fully-implemented PvP resolutions in the bundle.
`PVP2BattleController` is a **dual-mode** controller gated by a `marchMode` flag, and there is a
*second, older* PvP controller that only does the other mode. Infinite Ranking uses the elimination
branch; the **castle-duel branch is dormant for ranking** but fully present.

### `PVP2BattleController` is dual-mode

`marchMode` defaults to **`false`**. The two entry points choose the branch:

```js
startBattle(t=10)            { this.cleanup(); setBattleContext(NN.Pvp); … }   // marchMode stays FALSE → castle duel
startMarchBattle(t,i,s,e,n=10){ this.cleanup(); this.marchMode = true; …    }   // → elimination (Infinite Ranking)
```

Its `checkVictory` / `checkDefeat` are a single ternary on `marchMode`:

```js
checkVictory = marchMode
  ? /* elimination, see Part 2 */
  : !enemyCastle.isAlive || (timeExpired && allyCastle.hp/maxHp >  enemyCastle.hp/maxHp);   // castle duel
checkDefeat  = marchMode
  ? /* elimination */
  : !allyCastle.isAlive  || (timeExpired && allyCastle.hp/maxHp <= enemyCastle.hp/maxHp);
```

So the **castle-duel branch**: win by **razing the enemy castle**; at timeout, the side with the
**higher castle-HP percentage** wins (tie → defender loses). Both Infinite Ranking callers go through
`startMarchBattle`, so this castle branch is reachable in code but not used by the live ranking menu.

### The legacy v1 — `PVPBattleController` (`a8`)

A completely separate, earlier controller that does **only** the castle duel, with its own distinctive
tuning:

```js
ENEMY_COUNT = 10
PVP_HP_MULTIPLIER = 5            // every non-castle unit: ×5 max HP
PVP_MOVE_SPD_MULTIPLIER = 1.4    // …and ×1.4 move speed
PVP_TIME_LIMIT = 90              // REAL-TIME seconds (Date.now()-based), not frames
// applied at spawn:
t.isCastle || (t.maxHp *= 5, t.hp = t.maxHp, t.moveSpd *= 1.4, …)
```

This produces a fast, super-tanky castle-rush brawl on a real-time 90-second clock — a noticeably
different feel from the frame-based 60s elimination match the live mode runs.

**Reachability.** `PVPBattleController` is only invoked through its `c8` alias from an `onPVP()` that
lives in an obvious **developer/QA test launcher** — a menu of bare `onIdle` / `onDungeon` / `onMap3`
/ `onMap4` / `onRaid` / `onPVP` handlers with `setMode(HORIZONTAL/VERTICAL)`, `setMapIndex(3/4)`, and a
hard-coded `bossKindNum: 100002`. It is **not** wired to the player-facing ranking UI.

### What this tells us

EF2's PvP was **redesigned**: an older castle-HP duel (super-tanky units, real-time clock — the v1
`PVPBattleController`) was replaced by a formation-elimination match leveled to Knight Order Level (the
`PVP2BattleController` march path). The old controller survives as dev-menu-only code, and the
castle-duel logic also lingers inside PVP2 as the dormant non-march branch. The live Infinite Ranking
you play today is exclusively the **march/elimination** path.

---

## Part 4 — Daily Ranking (for contrast)

Despite the name, **Daily Ranking is not a battle**. Its only endpoint of substance is
`/dailyRankingBattle/join`, whose consumer simply reads back `body.myScore` — it **submits your own
wave-survival score** for a 24-hour leaderboard (up to 30 players, ranked by highest rebirth floor
reached in the window). No opponent is fetched and no enemy side is constructed. Only the `pvp/*`
endpoints build an actual fight.

| | **Infinite Ranking** | **Daily Ranking** |
|---|---|---|
| What it is | async snapshot PvP battles | score submission / leaderboard |
| Cycle | 4-day rounds | 24-hour rounds |
| You fight | other players' defense snapshots | nobody (your own run) |
| Ranked by | win/loss → server point delta | highest rebirth floor in 24h |
| Combat | full client-side simulation | none |

---

## Caveats
- **Bundle version:** analysis is on `1.11.52` (current). The unit codex is on the now-superseded
  `1.11.42`; unit *mechanics* are largely stable across the bump, but exact offsets/constants here are
  `1.11.52`-specific.
- **Server-side blind spots:** matchmaking, the point/rank algorithm, league promotion, cycle
  scheduling, and the end-of-round reward grants are computed on the server and are not in the client
  bundle. This doc describes the rules the client operates under and the data it exchanges, not the
  server's scoring math.
- **Client-authoritative outcome:** the match result (`isWin`) is decided and reported by the client;
  the server trusts it for the point delta.
