# EF2 Wave Call (the "Rage Gauge")

A companion to the **Unit Mechanics Codex**. Where the codex documents *units* and
[`GAME-MODES.md`](GAME-MODES.md) documents the *battle modes*, this documents one mechanic in depth:
**Wave Call** — the resource that advances battle waves — its regeneration math, every buff that feeds
it, the caps that bound it, and how powerful it can become.

> **Sourcing.** Reverse-engineered read-only from the live game bundle **`1.11.55`**
> (`runtime/bundles/mounted/1.11.55/assets/index.js`), the decrypted `books-decrypted.json`, and the
> `en.json` locale. Mechanics and formulas are exact from the client code. The bank-cap *value* and the
> per-wave reward resolution are **server-side** and noted as such. Per-copy skill values resolved
> through the `Bx` lookup table were not dumped — figures that depend on them are marked **[INFERRED]**.

---

## TL;DR

Wave Call is a **"Rage gauge"** that charges over **real wall-clock time** and is spent to advance
waves. It has four independent levers:

| Lever | What it controls | Capped? |
|---|---|---|
| **Regen rate** (`i`) | how fast the gauge charges | **No** — additive, no clamp, no awakening path; gated only by unit ownership |
| **Bank cap** (`maxWaveCall`) | how many charges you can hold | **Server-authoritative** (can't read the ceiling client-side) |
| **Double Wave** (`n`) | waves sent per call | the **awakened** portion caps at **70%**; active unique-skill stacks on top |
| **Instant charge** | one-off gauge top-ups | per-source (e.g. Aladin coin +0.5 s) |

Key surprise: **GameSpeed does *not* speed up regen** — the gauge is anchored to the wall clock, not the
battle clock. GameSpeed only makes already-called waves resolve faster.

---

## Part 1 — What it is

Wave Call ("놀이터" / Playground in the guild building list; internally the **Rage gauge**, 분노 게이지)
is a regenerating, capped resource. When enough Rage has charged, you spend one charge to **call the next
wave**, advancing progression without waiting for the auto-battle. The gauge:

- charges continuously based on **elapsed real time × a buff multiplier**,
- **banks** up to a server-set cap (`maxWaveCall`),
- on spend, sends `callNextWave(count)` to the server, which resolves the actual wave advance + rewards.

It is exposed through `WaveCallService`:

```
POST /wave-call/getWaveCallInfo {}        -> { success, maxWaveCall, lastWaveCallTime }
POST /wave-call/callNextWave   { count }
POST /wave-call/increaseMaxWaveCall { amount }   // no in-bundle caller
```

---

## Part 2 — The regeneration formula

The core math is identical in `callWave()` and the UI bar widget:

```js
t = ix.time - this.lastCallTime;                          // elapsed WALL-CLOCK milliseconds
i = KN.getInstance().getGameplayMultiplier("wavecall");   // the wavecall buff multiplier
s = 0.001 * t * i;                                        // elapsed seconds, scaled by i
available = Math.min(Math.floor(s / this.maxEnergy), this.maxCall);   // maxEnergy = 100
```

with hard-coded **`maxEnergy = 100`** (the Rage cost of one call) and **`maxCall = maxWaveCall`** (the
server-set bank cap).

### Base rate

At `i = 1` (no buffs), one charge accrues every **`maxEnergy / i = 100` seconds**:

> **Base = 1 call per 100 seconds (0.01 calls/sec) at 1×.**  Regen interval = **`100 / i` seconds**.

### The multiplier `i` (additive)

`i` is the **additive** sum of every `"wavecall"` source — the buff registry marks it `merge:"add"`, and
`wavecall` is excluded from both `heroIsolatedCodes` and `OWNERSHIP_BASED_CODES`, so it takes the normal
additive path. There is **no `Math.min` clamp** on the result of `getGameplayMultiplier`:

> **`i = 1 + (Σ all wavecall % buffs) / 100`** — uncapped.

Examples: +50% total → `i = 1.5` → 1 call / 66.7 s. +100% → `i = 2.0` → 1 call / 50 s.

### Why GameSpeed does **not** feed regen

`ix.time = Date.now() + timeOffset` — a server-synced **wall clock** (`updateTime()` / `setTime()`),
**not** scaled by GameSpeed and **never** `battleTime`. Both regen sites use it. GameSpeed instead flows
`getGameplayTotal("gamespeed") → updateGameSpeed() → BG.setSpeed()`, scaling only the **battle
simulation** — so it makes *called* waves resolve faster, but does nothing to charge the gauge.

### Anchor bookkeeping (after a call)

With `c = maxEnergy / i` seconds per charge, consuming `e` calls:

- **below cap:** `lastCallTime += 1000 * c` (consumes exactly one charge's worth of time),
- **at cap (`e >= maxCall`):** `lastCallTime = ix.time - (e-1) * c * 1000` (rewinds to preserve the surplus).

### Instant charge (separate path)

`addRageEnergy(t)` does `lastCallTime -= 1000 * t`, granting `t` seconds of charge instantly. Callers:
generic **pet rage grants**, and the **Aladin's Lamp coin** (`onCoinExpired`): a `COIN_EXPIRE_RAGE_CHANCE
= 0.1` (10%) chance to `addRageEnergy(COIN_EXPIRE_RAGE_SECONDS = 0.5)` → +0.5 s.

---

## Part 3 — Double Wave (waves per call)

A **separate** lever from regen — it sets how many waves a single call sends:

```js
n = KN.getInstance().getGameplayTotal("doublewave") + getRaptiOwnedDoubleWaveContribution();
o = (1 + Math.floor(n / 100)) + (100 * Math.random() < (n % 100) ? 1 : 0);
callNextWave(o);   // sent to the server
```

So `n ≥ 100` guarantees **≥2 waves per call**, with the remainder `n % 100` giving a percentage chance of
one more. The `showDoubleWaveEffect` animation (`updateDoubleWaveEffect`, 60-frame fade/rise) is purely
cosmetic — it does not compute the doubling.

---

## Part 4 — Every source

**Effect key:** *Regen* = feeds `i` · *Cap* = sets `maxWaveCall` · *Double* = feeds `n` · *Instant* =
`addRageEnergy` · *Speed* = GameSpeed (battle-resolution only, indirect).

### Hero Unique Skills (`HERO_UNIQUE_SKILL` book)

| Skill | Effect | Value tiers | kindNum |
|---|---|---|---|
| `waveCall` — "Rage gauge charges N% faster (Stacks)" | Regen | 1 / 2 / 3 / 4 / 5 / 7 % | 34–38, 60 |
| `doubleWave` — "N% chance to call 2 waves (Stacks)" | Double | 1 / 2 / 3 / 4 / 5 % | 61–65 |
| `GameSpeed` — "Base game speed +N% (Stacks)" | Speed (indirect) | 1 / 2 / 3 / 4 / 5 / 7 % | 29–33, 59 |

### Units (always-active `uniqueSkill`, per owned copy + transcend)

Only **three families** carry a wave-call unique skill:

| Unit (family) | Grade | Effect | Value |
|---|---|---|---|
| **Wolf Rider** (OrcWolfRider) | g5 / g6 | Regen | waveCall **4% / 7%** per copy |
| **Bigfoot** (OrcBigFoot) | g5 / g6 | Regen | waveCall **4% / 7%** per copy |
| **Raptor Rider** (OrcRapterRider) | g5 / g6 | Double | doubleWave **2% / 4%** per copy |

Each owned copy contributes once, plus once per transcend stage (`trans[0..2]`). **[INFERRED]** the
*applied* value is the unit's own `getSkill1Value(...)` `Bx` lookup, which may differ from the raw buff-def %.

### Pets

| Pet (kindNum) | Effect | Value |
|---|---|---|
| **Piggy** (4) | Regen | waveCall 0.5 / 0.7 / 0.9 / 1.2 / 1.5 % (5 tiers) |
| **Woola** (11) | Regen | waveCall 0.5 / 0.7 / 0.9 / 1.2 / 1.5 % |
| **Rapty** (20, awakened) | Double | +1%(5★)/+2%(6★) per owned Raptor Rider — **capped +70%** (see Part 5) |
| GameSpeed pets (9,10,13,21,22,23,1002,1003) | Speed (indirect) | 0.4–8% per tier |

### Castle (`CASTLE_SPECIAL` book)

| Source | Effect | Detail |
|---|---|---|
| **Orc Arcane Art** ("Call Wave", orcSecret kindNum 5) | **Cap** | unlocks the gauge + raises `maxWaveCall`; maxLv 5, 700 gem/lvl, reqWaves 50→350. Client sets `maxCall = castle.level + 1`; the real integer is server-side. |
| Elf Arcane Art ("Skip Wave", elfSecret kindNum 3) | *(adjacent)* | 0/3/6/9/12/15% chance to auto-clear a scenario battle — **not** a Rage call. |

### Verified negatives

No wave-call / double-wave grants in **gold skills**, achievements, IAP/ads/products, quests, guild,
tower, PvP, VIP, research, spirit, citadel, mine, treasures (those give GameSpeed only), or any
season/active-buff table. Sources are exhaustively the above.

---

## Part 5 — The awakening "owned-contribution" caps

Several pets, when **awakened**, contribute a buff drawn from your *owned* (even benched / barracks)
couple-units, via `sumAwakenedCoupleContribution(petKindNum, val5, val6, cap)` or a dedicated
`computeXxxOwned…()`, each ending in **`Math.min(Σ, cap)`**. The complete cap inventory:

| Awakening pet | Buff it feeds | Cap | Constant |
|---|---|---|---|
| Cold | Divine Blessing (`godbless`) | **30%** | `COLD_OWNED_GODBLESS_CAP_PCT` |
| Moon | Rebirth start floor (`startwave`) | **50%** | `MOON_STARTWAVE_COMBINED_CAP_PCT` |
| **Rapti** | **Double Wave (`doublewave`)** | **70%** | `RAPTI_OWNED_DOUBLEWAVE_CAP_PCT` |
| Tingkey | Elf skip-wave (`elfsecret`) | **30%** | `TINGKEY_OWNED_ELFSECRET_CAP_PCT` |
| Wyvern | max unit level (`maxlv`) | 200 | `sumAwakenedCoupleContribution(…, 200)` |
| Sylphid | bonus level (`pluslv`) | 100 | `sumAwakenedCoupleContribution(…, 100)` |
| GameSpeed pets | `gamespeed` | ~10% each | `GAMESPEED_AWAKENINGS[i].cap` |
| (QuestGold) | quest gold | 1 | `QG_OWNED_CAP_PCT` |

**The key result for Wave Call:** there is **no wave-call awakening at all**. The entire
`compute…Owned…` family covers GodBless, StartWave, DoubleWave, ElfSecret, MedalCap, maxLv, plusLv and
GameSpeed — **never `waveCall`**. The wavecall total is just `getGameplayMultiplier("wavecall")` with no
added owned/awakening term (unlike Double Wave, which literally does
`getGameplayTotal("doublewave") + getRaptiOwnedDoubleWaveContribution()`).

So the cap touches **only the Double Wave throughput** (the awakened/benched Rapti portion, ≤70%) — the
active Raptor-Rider unique-skill Double Wave stacks on top of it. The **regen rate is not awakening-fed,
and therefore not awakening-capped.**

---

## Part 6 — How powerful it can become

- **Regen rate — uncapped (ownership-gated).** The ceiling on `i` is purely how many **Wolf Rider +
  Bigfoot** copies/transcends you own (each +7% at g6, additive), plus Piggy/Woola (+1.5% each) and hero
  unique skills. No code cap, no awakening, no clamp. **[INFERRED]** reaching +100% total → `i = 2.0` →
  **1 call / 50 s**, and nothing in the client stops it climbing further.
- **Bank cap — server-gated.** `maxCall` is read back from `getWaveCallInfo`; the orc-art-level → cap
  table lives server-side, and `increaseMaxWaveCall` has no in-bundle caller. The numeric ceiling is
  **not determinable client-side**.
- **Throughput per call — Double Wave.** Rapti's awakened contribution caps at **+70%**; hero unique
  (+5%/copy) and active Raptor Rider (+4%/copy) Double Wave stack on top. Pushing `n ≥ 100` makes **every
  call send ≥2 waves**; **[INFERRED]** `n = 170` → guaranteed 2 + 70% chance of a 3rd ≈ **2.7 waves/call**.
- **GameSpeed — compounds consumption, not regen.** It scales the battle sim so called waves clear
  faster, shrinking the practical bottleneck — but it never touches the `i/100` calls/sec figure.

> **Net:** `effective waves/sec ≈ (i / 100) × E[waves per call] × battle-speed-unblocking`. The three
> levers are independent and multiply. Fastest regen = stack Wolf Rider + Bigfoot (uncapped). Best
> throughput = max Double Wave (Rapti 70% cap + active unique skills). GameSpeed multiplies only the
> consumption side.

---

## Part 7 — Client vs server split

| Aspect | Authority |
|---|---|
| Regen *rate* (`i`) | **Client** — computed from the wall-clock anchor × the buff multiplier |
| Available count | **Client** — derived from the server's `lastWaveCallTime` anchor + elapsed time |
| Bank cap (`maxWaveCall`) | **Server** — issued by `getWaveCallInfo`; client only reads it |
| Each call | **Server** — `callNextWave(count)`; server resolves the wave advance + rewards |

So the rate is client-computed but anchored to a server timestamp, the cap is server-owned, and the
actual wave/reward resolution is server-side — the client can't fabricate progression here.

---

## Part 8 — Honest gaps & corrections

**Server-side (not determinable from the client):**
1. The `maxWaveCall` integer ceiling (the orc-art-level → cap table; `increaseMaxWaveCall`'s increment/cost/cap).
2. What one call actually yields in waves advanced + loot.

**Inferred (not byte-traced):**
3. The per-copy *applied* value vs the buff-def % — the `getSkill1Value(...)` `Bx` table wasn't dumped, so
   the max-power regen/throughput figures are **illustrative ceilings, not exact**.
4. The pet 5-tier value indexing (which tier is active per star/transcend).

**Corrected false-positives (flagged for the record):**
5. An early pass claimed ~49 unit families grant wave-call via **gold** buffs — **refuted**. A unit's
   `goldBuffs` index the `HERO_GOLD_SKILL` book (combat/economy stats only — zero wave-call); the apparent
   "waveCall 7%" was actually gold-skill `QGGU` (quest gold). The real roster is the 6 `uniqueSkill`
   entries in Part 4.
6. "GameSpeed indirectly speeds regen" — **refuted**. Both regen sites use `ix.time` (wall clock), never
   `battleTime`. GameSpeed affects only consumption/battle speed.

---

## Appendix — code anchors (`1.11.55`)

| What | Where (grep needle) |
|---|---|
| Regen + double-wave + anchor bookkeeping | `callWave` ; bar widget `this.cnt=10` |
| Multiplier engine (additive, no clamp) | `getGameplayMultiplier(t){` · `resolveGameplayMergeMode` · `heroIsolatedCodes` · `OWNERSHIP_BASED_CODES` |
| Wall-clock anchor | `ix.time=this.serverTime` (`updateTime` / `setTime`) |
| Bank cap | castle `5===i.kindNum` → `maxCall=i.level+1` ; `getWaveCallInfo` → `maxCall=body.maxWaveCall` |
| Awakening contributions + caps | `sumAwakenedCoupleContribution` · `computeRaptiOwnedDoubleWave` · `getMoonOwnedStartWaveContribution` · `*_CAP_PCT` |
| Instant charge | `addRageEnergy` ; `onCoinExpired` + `COIN_EXPIRE_RAGE_CHANCE/SECONDS` |
| Service / endpoints | `WaveCallService` ; `WAVE_CALL` URL block |

*Byte offsets drift on each bundle update; the needles above are stable enough to relocate the code.*
