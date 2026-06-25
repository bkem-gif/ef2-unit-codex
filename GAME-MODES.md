# EF2 Game Modes & Battle Architecture

A companion to the **Unit Mechanics Codex**. Where the codex documents *units* (how each one
fights), this documents the *battle modes* that wrap them — the shared battle-controller architecture
and the competitive modes that ride on it: **Infinite Ranking**, **Guild War**, and **Guild Raid**.

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

## Part 5 — Guild War ("Guild PvP")

A scheduled guild-vs-guild **castle siege**. (The feature is "Guild War"; each scheduled match is a "Guild
Battle".) The war state — matchmaking, scoring, eligibility, rewards — is **server-authoritative**; the client
only simulates individual attack battles and renders server data.

### Format (locale-stated, enforced server-side)
- **Auto-matched every 12 h; each war lasts 23 h** (the last 1 h is settlement + prep) — `GAME_988`.
- **17+ members** required to participate — `GAME_989`. **ELO matchmaking** vs similar guilds — `GAME_990`.
  (None of these — cadence, member floor, ELO — exist as constants in any client book; all server-enforced.)
- Win = *"defend your own castles while taking down the enemy castles; the guild with the higher score wins"* — `GAME_991`.

### The map: 17 castles, 4 grades
A fixed graph of **17 castles** (`GAME_998`–`GAME_1002`): **1 S** (center) · **4 A** (inner) · **4 B** (middle) ·
**8 C** (outer), with a fixed adjacency graph (`s` borders the four `a`s; each `c` borders one `b`; …). A castle
opens for attack by **accumulated score** in grade order **C → B → A → S** (`GAME_1005/1006`), or by capturing an
**adjacent** castle. Capturing the **S castle advances the war Stage** (up to 3).

### Defense (set in advance)
- The **Guild Master / Vice-Master** assign members to defend a castle **grade**; unassigned members auto-place —
  one per castle first, then extras in order **S→A→B→C** (`GAME_996`, `GAME_1095`).
- A member's **defense team persists** to the next war unless changed (`GAME_997`); a slot that **successfully
  defends is protected** for a while (`GAME_1010`); a member who leaves mid-war keeps the slot + rewards (`GAME_1018`).
- Stored via `/guildDefense/{getCastleDefense,getMyTeams,setTeam}`; grade assignment via
  `/guildWar/{get,set}TierAssignments` — two separate server subsystems.

### Attack & the actual combat
- **2 attack attempts per member** per war (`GAME_1004`); one attacker per slot at a time; new joiners can't act
  in an ongoing war.
- Each attack is **one elimination battle** run by **`GuildWarBattleController`** in **`NN.GuildPvp`** context:
  ```js
  checkVictory = initialEnemyCount !== 0 && countAlive(enemyList) === 0          // wipe the defenders → capture
  checkDefeat  = initialAllyCount  !== 0 && (countAlive(friendList) === 0 || battleTime >= 7200)  // 7200f ≈ 120s
  ```
  It reports a **binary WIN/LOSE** (`fireOnComplete`) — no in-battle score. Capturing a castle = defeating **all**
  its defending squads (`GAME_1009`).
- **Asymmetric leveling.** The **attacker's** knight level is `Math.floor(wL.maxWave/100)` (your own progression);
  the **defender's** knight level is **supplied by the server** in the attack response (`enemyKnightLevel`), *not*
  derived from your wave. On top of that the **defending hero** gets `enemyHeroLevelBonus = getPlusLevel(grade)` —
  the `plusS/A/B/C` from the config book — added to its level (soldiers don't get it; they spawn at
  `knightLevel + their tier's plusLevel`).
- **GAME_979 "all soldiers of the same type join regardless of Evolved/Elite":** `squadsToCorpsRich` sends *every*
  stored soldier tier (each barrack tier with count > 0 as its own corp), not a single evolved/elite tier; tiers
  shift up one when the tribe's barracks are "awakened" (`getShiftedSoldierTier`). Both sides' squads come from the
  server attack-start body. Two attack protocols exist — `attackStart/End` (V1) and `attackV3Start/End` + `attackV3Mock`
  (V3); resolution is server-side (`attackV3End` returns the gems/honor).

### Config book — `GUILD_WAR_CONFIG` (3 rows = Stages 1–3)
| Stage | req to open C/B/A/S | clear (squads) C/B/A/S | defender lvl bonus +C/B/A/S | win/lose pts |
|---|---|---|---|---|
| 1 | 0 / 36 / 56 / 80 | 5 / 7 / 9 / 12 | 0 / 1 / 2 / 3 | +3 / +1 |
| 2 | 0 / 150 / 180 / 220 | 9 / 12 / 16 / 20 | 3 / 4 / 5 / 7 | +4 / +1 |
| 3 | 0 / 340 / 380 / 450 | 16 / 20 / 24 / 30 | 7 / 9 / 11 / 13 | +5 / +1 |

`reqX` = accumulated score to open that grade · `clearX` = squads to clear (and capture points) by grade · `plusX` =
the **defender hero level bonus** (feeds `enemyHeroLevelBonus`) · `win/lose` = points per attack. **Live war scores
(`myScore`/`oppScore`) are read from the server**, not computed by the client.

### Rewards (mailed after the war)
- **Per attack:** win **100 Gems + 40 Honor Coins**; loss **50 Gems + 20 Honor Coins**.
- **Per successful defense:** **20 Gems + 10 Honor Coins** (≤ 10× per war).
- **Guild outcome:** win → **200 Guild Coins + 100 Guild Points + 2 Pet Fragments** each; loss → 100 / 50 / 1.
- **After 30+ wars:** a rebirth **Medal Buff by guild rank** — a hardcoded client table (rank 1 = +300%, 2 = +280%,
  3 = +260%, … 101+ = +70%); the value actually applied is fetched from the server (`getGuildWarBuff`).

### Feeder systems
- **Guild Barracks** (`GUILD_BARRACK`, 16 rows = 4 tribes × 4 barracks; `/guildBarracks/{getAll,unlockKind,boost}`):
  trains the **shared soldiers** that fill war squads — 5 soldier tiers per barrack (`unitKindNums` + `plusLevel`
  `[0,0,6,12,18]`), `maxNum` 30, `openCost` ∈ {0 (first free), 500, 700, 1000}, instructor heroes (grade ≥ 5 only),
  and per-stat combat buffs (att/hp/def/move/range) that are **applied server-side** (the client only sends
  kind/count/plusLevel into the sim).
- **Pets:** `PET_94`–`PET_133` are Guild-PvP-only hero buffs — 94–101 buff all heroes across 8 stats
  (HP/ATK/DEF/atk-spd/move-spd/crit-rate/crit-dmg/range); 102–133 repeat those per race.

---

## Part 6 — Guild Raid (Guild Subjugation Battle)

A **co-op PvE boss kill** — *not* guild-vs-guild. (`GAME_630` "Guild Raid" and `GAME_631` "Guild Subjugation Battle"
are synonyms.) The guild collectively whittles a shared boss; each member contributes damage.

### Combat
- Run by **`RaidBattleController`**. **Win = the boss is dead** (a boss-kill objective). **Lose = the time limit**
  (`TIME_LIMIT_FRAMES = 10800` ≈ 180 s at 60 fps) **or all your units dead**.
- You field **multiple corps** (a `"kind-kind|…"` squads string across `CORP_COUNT` corps; saved per-user in
  `localStorage` under `ef2.guildRaid.attackSquads.<userId>`).
- **Player damage ramps up as the clock runs down** — a comeback mechanic: ×1.5 at frame 1800, ×2 at 3600, ×2.5 at
  5400, ×3 at 7200, ×4 at 9000 (`getRaidBossDamageMultiplier`).
- It's a **cumulative-damage** objective: even a non-kill run records damage. On end the client posts
  `endBattle{battleId, damage, elapsedTime}` — **no win flag**; `damage = clamp(0, bossStartHp, bossStartHp − bossHp)`,
  `time = clamp(3, 300, battleTime/60)s`. Whether the boss was *defeated* vs merely *damaged* comes back as the
  server's `isClear`.

### Structure & the boss
- Hierarchy **main → difficulty → sub**, each sub → a boss `kindNum`. **Only main 1 is live** (`LIVE_MAINS = [1]`);
  the data manager hardcodes 5 main names as Korean literals (`고대유적지`, `불타는 대지`, `죽음의 늪지`, `지옥군주의 성채`,
  `얼어붙은 고대 문명` — English glosses would be a translation, not present in the data) and fallback boss kinds
  `{1:100000, 2:100001, 3:100002}`.
- The boss is one of three reused raid-boss Kings — **Scorpion King** (`100000`, default), **Harpy King** (`100001`),
  **Golem King** (`100002`) — selected by kindNum. **Boss HP comes from the server** (`battle.startHp`), not a book.

### Economy & ranking (server-authoritative)
- **Endpoints** (`GuildRaidService`, 10): `getAllInfo, getMainInfo, getSubInfo, open, giveUp, claimReward, startBattle,
  endBattle, getRanking, getGuildAndUserRanking`.
- **Opening** a raid *stage* (a `main`'s difficulty tier) is a one-time unlock that consumes that stage's
  **`openCost` in Guild Coins** (`GAME_812`; the confirm dialog reads "…{openCost} Guild Coins consumed"). The
  `openCost` is server-provided per stage (defaults to `0` — there's no raid config book, so the live amount isn't
  in the client); the server deducts it and returns the opening member's new personal Guild-Coin balance. This is
  separate from **attack tickets** — the per-user, **server-gated** currency you spend to fight each battle
  (`startBattle`); the client only displays the server's `userTicket`. `claimReward(raidId, sub)` pays out when the
  server returns a `CLEAR` status — **reward contents, boss HP, tickets, and difficulty tiers are all server-side**;
  there is **no Guild-Raid config book** in the client.
- **Contribution ranking is entirely server-side**: `getRanking` / `getGuildAndUserRanking` exist, but the shipped UI
  has **no caller** that computes contribution — the client only renders what the server returns.

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
