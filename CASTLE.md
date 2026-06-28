# EF2 Castle — Code-Derived Reference

A companion to the **Unit Mechanics Codex**. Where the codex documents *units* and
[`GAME-MODES.md`](GAME-MODES.md) documents the *battle modes*, and [`WAVE-CALL.md`](WAVE-CALL.md)
documents the Rage gauge, this documents the **player castle** ("Valkion Castle") in depth: what it
is, the three upgrade tracks that power it, the buffs it grants, its combat behaviour, and all eight
special "Arcane" books.

> **Sourcing.** Reverse-engineered read-only from the live game bundle **`1.11.55`**
> (`runtime/bundles/mounted/1.11.55/assets/index.js`) and the `assets/locales/*.json` locale files.
> All identifiers in parentheses are the minified symbol names / locale keys present in the shipped
> client, so a developer can locate the code. Mechanics, formulas, and caps are exact from the client
> code; items marked *(uncertain)* are inferred but not directly confirmed. Per-level magnitudes
> (costs, grant values, max levels) are **server-authoritative** — loaded from the `CASTLE` /
> `CASTLE_SPECIAL` datasheets at runtime and **not** present in the bundle.

---

## Overview

There is exactly **one** player castle in EF2: **"Valkion Castle"** (locale `GAME_530` = `Valkion Castle` / `발키온 성`). It is the player's home tower and a fully active combat unit, not a passive structure.

- The castle is modeled as a **`UnitVO`** (class `bx`, alias `yx`) with `isCastle = true` — it shares the unit data model, not a dedicated castle class. Default `castleKindNum = 10001`.
- It is **not** a multi-type system. The only enumerable "kinds" are upgrade *books*, not castle skins. `/castle/updateCastleKindNum` exists in the API layer but **has no caller** in the bundle, and `10002+` never appear as literals — the castle skin is effectively fixed to `10001`.
- State is **server-authoritative**, persisted under `body.castle` and synced via `/castle/*` endpoints.
- The on-screen name `Valkion Castle` lives **only in locale assets**, not the JS bundle (searching the bundle for "Valkion" returns 0 hits).

The castle exposes two distinct upgrade axes plus a third currency track:
- **Level** (gold, per-book power),
- **Enhance** (medal, a single global `+N` multiplier with gem-priced reset),
- **Special books** (gem, 8 "Arcane" abilities).

It grants benefits in two categories: (1) **combat stats to the castle entity itself** (HP/atk/def/range/atk-speed/multi-shot/bounce), and (2) **account-wide gameplay buffs** from its special books. **It does not buff the player's heroes' combat stats** — `CastleBuffSource.getBuffList()` returns `[]`.

---

## Castle types

**There is only one player castle type.** Several "Castle"-named symbols exist but are unrelated to the player castle data model:

| Symbol | What it actually is |
|---|---|
| **Valkion Castle** (`castleKindNum 10001`, in-battle `BaseCastle`/`ElfTown5`) | The player's home tower. The only player castle. |
| `Castle0` / `Castle1` / `Castle2` (enum `ox`; classes `i2`/`Z1`/`J1`, aliases `s2`/`t2`/`Q1`) | Battlefield **enemy-castle sprite/render classes**. `unitType = RANGE`, `weaponClass = SpeedArrow2`, `moveSpd = 0`, `numBlock = 0`, `radius = 22`, `hitHeight = 67`; `Castle0` has `numShot = 3` (others inherit `1`). Registered in a kindNum→class render map. Not the player castle. |
| `castleId` / `castleIndex` / `castleIdStr` | **Guild-War / Guild-Defense** subsystem (PvP combat logs, defense slots). `castleId` is a lowercase string label (e.g. `'s'`) uppercased for display. Unrelated to the personal castle. |
| `CastleSortValue` (`targetCastleSortValue`) | PvP/tournament matchmaking **sort key** (returns `castleIndex`, or `999` if invalid). Not a buff/stat. |
| `CastleDefense` / `CastleStatus` | Guild REST endpoints (`/guildDefense/getCastleDefense`, `/guildWar/getCastleStatus`). Server, not local combat. |
| `CastlePoint` / `CastleMotion` | Main-menu UI for the Castle button (`menus[2]`). |

> The Castle Info icon (`CastleIcon`, class `S9t`/`C9t`) hardcodes texture `Castle2` from atlas `UI_Ekkorr` and never swaps by `castleKindNum` — reinforcing the single-visual-type finding.

### Data model

- **`CastleDataManager`** (class `mN`, alias `wN`, singleton `.instance`): holds `castleVO` (a `UnitVO` with `isCastle=true`, built via `yx.getVO()`), `bookList` (5 gold books), `specialBookList` (8 special books), and `_enhance`.
  - `get castleLevel()` → `Math.max(1, bookList[0].level)`
  - `get castleEnhance()` → `_enhance`
  - Both mirrored into `castleVO.level` / `castleVO.enhance`.
- **`CastleVO`** (class `vN`, alias `bN`): the upgrade-**book/entry** descriptor (NOT a castle instance). 19 fields: `kindNum, name, short, code, initValue, incValue, maxLv, initCost, incCost, desc, level, type, costType, initReqWave, incReqWave, isPowered, costData, reqWaveData, valuesData`.
- **User/account model** (class `mL`) defaults: `castleKindNum = 10001`, `castleLevel = 0`, `castleEnhance = 0`, `castleGoldLevels = [0×10]`, `castleMedalLevels = [0×10]`. Arrays are 10-slot over-sized backing stores (only 5 gold / 8 special books are populated).
  - `castleMedalLevels` appears **exactly once** in the ~5.9 MB bundle (its declaration) — it is **dead/unused** client-side; medal spend is the single scalar Enhance, not a 10-slot track.
  - A parallel static helper set (`getCastleLevel` / `setCastleLevel` / `upgradeCastleLevel` / `getCastleLevelsString`) operates 1-indexed (`level-1`) over `castleGoldLevels` and serializes it as a `|`-joined string. Distinct from the `wN.bookList` path.
- **Persistence** (`CastleDataManager.setData(t)`): reads `t.kindNums[]`/`t.levels[]` (regular), `t.specialKindNums[]`/`t.specialLevels[]` (special, guarded by presence + `Math.min` clamp), `t.enhance`, `t.castleKindNum`. Routed from `setUserInfo` via `t.castle && (wN.getInstance().setData(t.castle), KN.getInstance().recalculate())` — `KN` is the BuffManager.
- **Datasheets**: loaded as `gD.CASTLE` (`"CASTLE"`) and `gD.CASTLE_SPECIAL` (`"CASTLE_SPECIAL"`) via `wD.getInstance().getBook(...)`, then `wN.setBookData` (regular) / `wN.setBookDataForSpecial` (special, forced `type=2`). Local-storage cache key `CASTLE_BOOK = "CB"` (one of `UB/CB/QB/TB/SB/SPB`). `BOOK_CONFIGS` lists `CASTLE` and `CASTLE_SPECIAL` (each `priority:0`, `dependencies:[]`).

---

## Upgrades & costs

The castle has **three upgrade systems with three currencies**.

### 1. GOLD track — 5 regular "research-lab" books (`bookList`, kindNum 1–5)

| kindNum | Name (`CASTLE_NAME_n`) | Desc (`CASTLE_DESC_n`) | Effect |
|---|---|---|---|
| 1 | Castle Durability | Castle Level Up | Drives the castle's level (HP/atk/def via ×1.03 exponent) |
| 2 | Castle Range | Castle Range Up | `atkRange = baseAtkRange + value` |
| 3 | Castle Atk Speed | Castle Atk Speed Up | `atkDuration = 10000 / (baseAtkDuration + value)` |
| 4 | Multi-Shot | Multi-Shot Chance | `numShot = 1 + value` |
| 5 | Bounce Shot | Bounce Shot Chance | `numBounce = value` (flat) |

- Setters: `setPlayerAtkRange` / `setPlayerAtkDuration` / `setPlayerNumShot` / `setPlayerNumBounce`, wired to `getBookDataByKindNum(2..5).value`. (`1e4 = 10000`; higher atk-speed value ⇒ shorter cooldown ⇒ faster fire.)
- Display: kindNum 4/5 render as `(100*value).toFixed(0) %`.

**Per-book value** (`CastleVO.value`):
```
value = (type === 2 && valuesData)
        ? valuesData.split('|').map(Number)[level] || 0
        : initValue + incValue * level
```

**Per-book cost** (`CastleVO.cost`):
```
cost = (type === 2 && costData) ? costData.split('|').map(Number)[level] || 0
     : isPowered                ? Math.floor(initCost * incCost^level)   // geometric
     :                            Math.floor(initCost + incCost * level) // linear
```
- `getTotalCost(t, i)` sums `cost` over `[t, i)` (temporarily mutating then restoring `level`).
- `canUpgrade()` = `level < maxLv`.
- `isPowered` is set from the server field `isPowered === 'Y'`.

**kindNum 1 is special-cased** (does not use the `CastleVO` cost formula):
- Cost = `vV.getTotalGold(level, level+N)` from **`HeroUpgradeManager`** (`wV`/`vV`) — the **shared hero-leveling gold table**.
- Cap = `vV.getMaxLevel(5)` (the **grade-5 hero max-level cap**, not a castle constant):
  ```
  getMaxLevel(5) = min(acc.length-1,
                       getBaseMaxLevelForGrade(5)   // base; falls back to BASE_MAX_LEVEL
                     + getGameplayTotal(MaxLv)      // MaxLv buff
                     + petPoint
                     + 0                            // s*TRANS_MAX_LEVEL_BONUS; s=0 for the castle call ⇒ 0
                     + floor(totalTransPoint)
                     + wyvernRiderContribution)
  ```
  - `BASE_MAX_LEVEL` ← clientData `HERO_MAX_LEVEL`, default **`1000`**. `TRANS_MAX_LEVEL_BONUS = 100` (does not apply to the castle since `s=0`).
- Currency: deducts `wL.gold`; `COMMON_359` ("Not enough gold"), `COMMON_369` ("Max Level").
- `HeroUpgradeManager.setBookData` parses `t[0].golds` (`|`-delimited), pops a trailing `0`, prepends `0` → cumulative `acc`. `getTotalGold(t,i) = acc[i] - acc[t]` (clamped).

**Network**: batched via `CastleService.upgrade(kindNums, levels, gold, goldPerSec)` → `/castle/upgrade {kindNums, levels, gold, goldPerSec}` (debounced through `sendToServer`).

> **Reset behavior**: `resetCastleGoldInfo()` zeroes every `type===1` book (`level=0`, `castleGoldLevels[i]=0`) and sets `castleVO.level=1` — i.e. the gold (level/range/atk-speed/multi-shot/bounce) track is a **per-run progression reset on rebirth**.

### 2. MEDAL track — single global Enhance (`+N`)

- Cap: **`CASTLE_MAX_ENHANCE`** ← clientData, default **`3000`** (server-overridable; sibling `HERO_MAX_ENHANCE` default `1000`). Lazily cached on class `wx`/`vx` from sentinel `-1`.
- Cost: shared **`HeroMedalEnhanceManager`** (`s7`, alias `e7`). `getCost(t) = acc[t] - acc[t-1]`. `+1/+10/+100` buttons sum `e7.getCost` per new level. Target clamped to `CASTLE_MAX_ENHANCE`.
- Two cost modes (`setBookData`):
  - If clientData `MEDAL_ENHANCE_USE_FORMULA === '1'` **and** segments present: per-level cost
    ```
    cost_h = Math.round(exp^(h/5) + 3*h) + offset      // active segment = highest startLevel <= h
    acc[h] = acc[h-1] + cost_h,  for h in [1, HERO_MAX_ENHANCE]
    ```
  - Else: `acc = [0, ...book[0].medal.split('|').map(Number)]`.
- Currency: `wL.medal`; `GAME_48` ("Not enough Medals").
- **Reset**: costs **100 gems** via `/castle/enhanceReset` (empty body), gated `wL.gem < 100` → `COMMON_352` ("Not enough gems"). Reset button `iconText` is hardcoded `"100"`, enabled only when `gem >= 100 && enhance > 0`. New enhance comes back from the server response.
- **Caveat (verified)**: `buildFromSegments` only fills `acc` up to `HERO_MAX_ENHANCE` (default 1000). Since `CASTLE_MAX_ENHANCE` defaults to 3000 > 1000, **castle `getCost` for levels >1000 returns 0** client-side (the `t >= acc.length` branch) unless the table is longer or the server reconciles. The shared engine's table length is hero-bounded.
- **Network**: `CastleService.enhanceUp(t)` → `/castle/enhanceUp {enhance:t}`. A second route also exists: `enhance(t)` → `/castle/enhance {enhance:t}`. Castle medal-enhance is debounced separately at `ENHANCE_DEBOUNCE_DELAY = 3000 ms` (on `CastleDetailPopup` `T9t`).

### 3. GEM track — 8 special "Arcane" books (`specialBookList`, kindNum 1–8)

- Forced `type=2`; `costData`/`reqWaveData`/`valuesData` from server `cost`/`reqWaves`/`values` (`|`-delimited, indexed by `level`).
- Buy (`onBuy`): `level >= maxLv` → `COMMON_369`; `wL.maxWave < reqWave` → `GAME_91` ("You must clear Wave ##.", `##` = wave); `wL.gem < cost` → `COMMON_352`. Then `CastleService.upgradeSpecial(kindNum, level+1)` → `/castle/upgradeSpecial {kindNum, level}`. (kindNum 7 / Rebirth Team uses the same checks via `onBuyClick`.)
- The upgrade list (`CastleUpgradeSubView`) filters: always hide **kindNum 7** (Rebirth Team), and hide **kindNum 8** (Soul Rest) unless `wL.bestMedalPerMin > 0`.

### Currency / cap summary

| Track | Currency | Cap | Reset |
|---|---|---|---|
| Gold books (1–5) | Gold (`wL.gold`); kindNum 1 also gold | per-book `maxLv` (server); kindNum 1 → grade-5 hero cap (base 1000 + bonuses) | zeroed on rebirth (`resetCastleGoldInfo`) |
| Enhance (`+N`) | Medals (`wL.medal`) | `CASTLE_MAX_ENHANCE` (default 3000) | 100 gems (`/castle/enhanceReset`) |
| Special books (1–8) | Gems (`wL.gem`) | per-book `maxLv` (server), wave-gated | — |

> `castleGoldLevels` mirrors the gold `bookList` levels; `castleMedalLevels` is declared but dead. They are **not** two parallel tracks for the same upgrades.

---

## Bonuses & buffs

### Combat-stat scaling (castle entity only)

All castle stats use the shared **`UnitVO`** curve:
```
stat = baseStat(bvo) * 1.03^totalLevelExp * transStatMultiplier * transPointBonusMultiplier
```
applied to `maxHp`, `atkDmg`, `def`, `phyDef`, `magDef`.

- `transStatMultiplier = 1 + 0.4 * trans`
- `transPointBonusMultiplier = 1 + min(calcHeroTransPoint, 100) / 100`  *(global trans-medal cap `TRANS_MEDAL_GLOBAL_CAP = 2000`)*

**`totalLevelExp`** depends on battle context:
- **Normal battle, friendly unit** (how the player castle runs):
  ```
  totalLevelExp = level + enhance + getKnightLevel(tribe) + getGameplayTotal(PlusLv) + extraLevel - 1
  ```
- **Enemy unit OR non-Normal context** (`battleContext !== NN.Normal`: Pvp/March/Dungeon/Tower/Sprite/GuildPvp):
  ```
  totalLevelExp = level + enhance + extraLevel - 1     // no knightLevel, no PlusLv
  ```
- `getKnightLevel(t) = (t===0 || account.tribe!==t) ? 0 : floor(maxWave/100) + 1` — applies only when the unit's tribe matches the account tribe.
- `PlusLv` = `getGameplayTotal("pluslv")`.

So each **Enhance** and **extraLevel** point adds ×1.03 to HP/atk/def in normal play; knightLevel/PlusLv are context- and tribe-gated.

### `extraLevel` — citadel "CastleLevelUp" bonus (shown as `(+N)`)

- `castleVO.extraLevel = getCitadelOwnershipTotalWithAwakening(CastleLevelUp)`, assigned at battle setup, on revive, and re-synced each frame in `refreshHeroBuffs`. The UI label `(+N)` (`lblCastleBonus`, next to `GAME_530`) uses the same value.
- Source: pet awakening **`petKindNum 19`** → `CastleLevelUp` (`"castlelevelup"`), tiers `[10, 20, 30, 50, 80]`.
  - `citadelTier`: grade 5 → `10`; grade 6 → `[20, 30, 50, 80]` by trans 0/1/2/3.
  - Returns the **un-awakened** total unless `isPetAwakened(19)`. Contributors sum.
- `CastleLevelUp` is one of three **`OWNERSHIP_BASED_CODES`** = `{offlinemax, offlinespeed, castlelevelup}`, capped at the **top-5 contributors** (`MAX_OWNERSHIP_SLOTS = 5`), gated behind `CITADEL_UNLOCK_WAVE = 100` (`isCitadelLocked`).
  - Sibling awakenings: `OfflineSpeed` (pet 17, `[50,100,200,300,500]`), `OfflineMax` (pet 18, `[2,4,5,6,7]`).

### `OurTowerHp` (OTH) multiplier

- Castle HP is additionally multiplied by `getMultiplier(unitType, tribe, IN.OurTowerHp)` where `IN.OurTowerHp = "OTH"`.
- Applied to `baseMaxHp` at battle start (if `≠1`) and refreshed each frame (`refreshHeroBuffs`); the HP orb shows `maxHp * multiplier`.
- **No source in the bundle emits an `OTH` combat skillcode** (grep `_OTH` → 0 hits), so in practice this multiplier is **`1.0` unless** a server-defined hero/treasure/pet carries an OTH buff. *(uncertain whether any live source provides OTH; only HP is shown scaled by it — atk/def are not.)*

### Account-wide gameplay buffs (special books)

- **`CastleBuffSource`** (class `yN`, alias `_N`, `sourceId = "castle"`):
  ```
  getGameplayBuffs(): for each specialBook with level>0 && code:
      code = book.code.toLowerCase()
      value = (code === 'retreat') ? (book.value>0 ? book.value : (level>=1 ? 1 : 0)) : book.value
      push {code, value}
  getBuffList(): []     // NO combat buffs
  ```
- **`CastleBuffAccessor`** (class `HN`, alias `WN`): exposes only `getGameplayBuff` (sums via `LN`) — it has **no `getBattleBuff`** method (the sibling accessor `jN` does), confirming the castle contributes zero combat buffs.
- **Enhance does NOT scale gameplay buffs.** Unlike `GoldBuffSource` (`pN`), which doubles a buff once `enhance >= dN[i]` threshold, `CastleBuffSource.getGameplayBuffs` references no `.enhance` and no `*2`. Castle enhance affects only the ×1.03 stat exponent.
- **Merge** (`BuffManager.getGameplayMultiplier`): default additive — accumulate `h += value` across sources, return `(1 + h/100)`, times isolated-source factors `(1 + s/100)`; a per-code `multiplicative` mode does `n *= 1 + s/100` instead. The castle is one source feeding `perSourceGameplay`.

---

## Combat role

The castle (`BaseCastle`, class `VQ`, registered `"BaseCastle"`, extends `WQ` = `HQ`) is an **active combat unit**.

- **Placement / setup** (endless-wave mode, `BattleController` `cii`/`lii`, `battleType = gV.IDLE`): instantiated from `castleVO.className` as `this.player`, `id = 0`, `numShot = 1`, positioned at center **(320, 320)**, pushed to `friendList`; `enemyList` = the wave, `allyList` = friends. `extraLevel` set from `CastleLevelUp`; OurTowerHp applied here. Only this controller applies the Range/AtkSpeed/Multi-Shot/Bounce books.
- **Targeting** (`doIdle`): acquires nearest in-range enemy (RANGE/MELEE-aware via `findNearestTarget`), drops out-of-range targets, faces the target, and `attack`s when `attackCoolDown <= 0`. Concrete skins fire `weaponClass SpeedArrow2`.
- **Immovable**: `moveSpd = 0`, `isImmovable = true` (set in `initializeData`), `numBlock = 0`.
- **Regeneration**: `execute()` increments `regenTimer`; every `REGEN_INTERVAL = 450` ticks it calls `heal(.5, null, true, "")` when `hp < maxHp`. `heal` with the percent flag true → `maxHp * 0.01 * 0.5` = **0.5% maxHp** per 450 ticks.
  - `hpRegenPerSec = 0.001` is **dead/vestigial** (never read); the regen amount is the hardcoded `0.5`.
  - Interval is in `execute()` **ticks**, not seconds. *(uncertain real-time interval; depends on tick rate.)*
- **Crowd-control immunity**: `stun`, `knockBack`, `onHitted`, `addDotDamage`, `shock`, `freeze`, `curse`, `silence`, `poison`, `blow`, `binding` are all empty no-ops; `updateCrowdControl` only decrements shield counters and returns `false`.
- **Tap interaction**: `onPointerDown` toggles the range circle (`AttackRangeCircle` singleton `$B`/`VB`) and shows the health bar for **225 ticks** (`showHealthBarTemporary`); auto-hides via countdown in `doIdle`.
- **Death is game over** and the castle **freezes on its last death frame** rather than despawning (`isCastle` short-circuits removal).
- **Multi-shot override (verified)**: the book-4 wiring `setPlayerNumShot(value)` sets `numShot = 1 + value`, **overwriting** any per-unit default. In wave mode `this.player.numShot = 1` is also set before `setData`, so an un-upgraded castle is `numShot = 1`.

### Burning-castle damage state

Purely visual; **`CastleFire1`/`CastleFire2` are effect sprites (classes `Mq`/`Eq`, `Aq`/`Sq`, extending `XK`), NOT weapons.**
- `updateDamageFire` (invoked from the `health` setter, so it updates on every HP change) maps `hp/maxHp` to **9 fire tiers**: `<=0.9 → 1` … `<=0.1 → 9` (tier 0 = no fire above 90%).
- `applyDamageFires(t)` adds fires at fixed positions `0..4` and scales the set at tiers 3/5/6/9 (×1.1/1.2/1.3/1.5).
- `FIRE_POSITIONS` = `[(10,-15),(-15,-8),(3,-4),(-15,-28),(5,-35)]`; `FIRE_TYPES` = `[CastleFire2, CastleFire1, CastleFire2, CastleFire1, CastleFire1]`.

### Game-over flow

- `isGameOver()` = `!this.player.isAlive || isGameOverFlag`.
- `handleCastleDestroyed()`: saves `KEY_GAME_OVER {wave, numRevive}`, POSTs `/user/castleDestroyed`, pokes `PowerSaveManager.onCastleDestroyed`, then `showGameOver(wave, onRebirth, onRebirthWithBonus, onContinueGame)`; runs `startTutorialRevive` only when `numRevive == 0`.
- **"Continue game"** = `performRetreat()`: wave = `max(1, (min active wave or current) − 1)`, clears enemies, revives player + heroes, resets flags. A retreat-of-1, **not** a restart.

### Enemy castle (other modes)

A separate `this.enemyCastle` exists in Dungeon and PvP/Guild-War (distinct from the player castle):
- **PvP**: `ElfTown5` (kindNum 10001), `detectRange = 600`, `atkRange = 250`, `numShot = 1`. `checkVictory` keys off `!enemyCastle.isAlive` (plus a time-expiry HP%-tiebreak).
- **Dungeon**: built from `dungonBossVO.className`, `stayAfterDeath = true`, `isImmovable = true`, `maxHp *= 4/DungeonBossHp`, move speed ×1.3 then forced immovable, revive disabled (`maxRevive=0`).
- Guild/March variants use `detectRange = 1400`. In PvP/March the player castle's **books are ignored** (`setupCastles`/`setupMarchCastles` hardcode `atkRange=250, numShot=1`), consistent with non-Normal `totalLevelExp` (loses knightLevel/PlusLv there too).

### Enemy AI vs. the castle

Airborne enemies actively target it: `findCastleTarget()` scans `enemyList` for the first `isCastle && isAlive`, then flies toward and lands near it when distance `<= landDistance (40)` (e.g. `Frog1`; `RoboBomb1` is a sibling flyer).

### Castle Health Orb

`CastleHealthOrb` (singleton `F8`, sheet `UI_Ekkorr`): shows HP and HP%; percent color red `<=20%` (`0xFF4444`), orange `<=50%` (`0xFFAA44`), else pale yellow (`0xFFDDAA`).

---

## Special abilities

Eight special books (kindNum 1–8), keyed by `kindNum`; name/desc/short keys all derive from it (`getSpecialNameKey/DescKey/ShortKey`). The **NAME** column is themed as race "Arcane Arts," but the **SHORT** label and the gameplay **code** describe the real effect.

| # | NAME (`CASTLE_SPECIAL_NAME_n`) | SHORT (`_SHORT_n`) | Code | Mechanic |
|---|---|---|---|---|
| 1 | Arcane of Life | Castle HP Up | `retreat` | **Continue-on-death.** "If the castle falls, you can continue by spending a life." `specialBookList[0]` gates the Continue button (visible only when `level>0`); `maxHeart = specialBookList[0].valuesData.split('|')[level]` (0 if `level<=0`). |
| 2 | Human Arcane Art | Complete Now | `humansecret` | **Instantly completes a random developed quest.** `humanSecretDuration = 1000*(60 - total)` ms (60 s base, −5 s/level; sentinel `999999999999999` when `total<=0`). `triggerHumanSecret` picks a random quest with `level>=1` and collects its gold (`wL.updateGold(quest.gold)`). |
| 3 | Elf Arcane Art | Skip Wave | `elfsecret` | **Chance to auto-skip a wave.** On `getNextWave`, if `random < (getGameplayTotal(ElfSecret) + Tingkey pet contribution)/100`, the wave is skipped (`skippedWave` set, index +1, `ElfSecretSkillToast` shown). |
| 4 | Undead Arcane Art | Skill Cooldown Reduction | `undeadsecret` | **Reduces skill-slot 2–3 cooldowns** (−10% on unlock, −5%/level). Per-slot cd = `max(30, floor((30 + 15*slotIndex) * (1 − 0.01*total)))`. |
| 5 | Orc Arcane Art | Call Wave | `wavecall` (Rage) | **Unlocks the Rage gauge to manually call the next wave.** `callable = min(floor(elapsedSec * WaveCall_mult / maxEnergy), maxCall)`; if 0 → `GAME_186` ("Rage gauge is not fully charged yet"). `maxWaveCall` from `/wave-call/*`. **Note**: the literal `orcsecret` enum/buff-name exists but has **no mechanical consumer** — the real mechanic is `wavecall`. |
| 6 | Medal Buff | Medal Acquisition Buff | `medal` | **+10% rebirth medals per level.** Feeds `getGameplayMultiplier(MedalBuff)`; `currentBuffMultiplier = getGameplayMultiplier(MedalBuff) + event/team/pet additive terms`; final medals = `floor(baseMedal * currentBuffMultiplier * eventMulti)`. |
| 7 | Rebirth Team | Rebirth Team Formation | — | **Assigns a hero team whose buffs apply on rebirth.** Unlocked via purchase (`GAME_605` "Unlock Rebirth Team"), reqWave-gated. When `level>=1` the UI hides Buy/SoulRest and shows the Formation button (`GAME_607`). Routes `/user/setReviveTeam`, `/user/getReviveTeam`. |
| 8 | Soul Rest | Soul Rest | — | **Keeps earning medals while the game is closed** (idle/offline accrual). Only listed when `bestMedalPerMin > 0`. Uses icon `UI_PREMIUM11` (others use `CastleUp${kindNum}`) and `GAME_898`/`GAME_903` fallbacks. Backed by `soulRest.getRecords(200, false)`; fields `bestMedalPerMin`, `soulRestNextStartAt`, `soulRestEndAt` parsed from server data. |

- Pet/citadel contributions stack on top of some specials: **ElfSecret** + `getTingkeyOwnedElfSecretContribution()` (Tingkey, awakening 5, capped `TINGKEY_OWNED_ELFSECRET_CAP_PCT = 30`); **WaveCall** + `getRaptiOwnedDoubleWaveContribution()` (DoubleWave).
- Korean DESCs corroborate: `DESC_2` "60초부터 시작해서 레벨업마다 5초씩 줄어듭니다", `DESC_4` "처음 개방시 10% 감소하고, 레벨업마다 5%씩 감소합니다", `DESC_5` unlocks "분노 게이지".

### Special-book detail UI

- `CastleSpecialDetailPopup` (class `P9t`, alias `R9t`; `LIST_WIDTH=540`, `LIST_MAX_HEIGHT=360`) is a **generic** per-special detail popup (default title `특수 능력 상세` "Special Ability Details"), showing each special's `getSpecialDescKey()`. **Only when `kindNum===8`** does it add the Soul Rest records UI (`ensureSoulRestUI`/`loadRecords`). Soul Rest record columns: **Medals/min** (`GAME_904`), **Medal** (`GAME_7`), **Interval(min)** (`GAME_905`), **Rebirth Time** (`GAME_906`). Records fetched newest-first then reversed for display.
- Value display: kindNum 2–6 append a `%` suffix **except kindNum 5** (Call Wave shows a raw rage-count number). Icon = `UI_PREMIUM11` for #8, else `CastleUp${kindNum}` (1–7).
- Soul Rest's item description uses `GAME_903` when a flag is set, instead of `CASTLE_SPECIAL_DESC_8`.

### Guild-War medal-buff reward table (distinct from special #6)

`createMedalBuffList` (Guild War Guide, `GAME_1021`) reuses the `CASTLE_SPECIAL_NAME_6` key as a column/server header but is a **PvP/guild-war ranking-reward table** (`medalBuffTime` shown in Days = `floor(medalBuffTime/60/24)`):
`rank 1 = +300%`, `2 = +280%`, `3 = +260%`, `4–5 = +240%`, … `71–100 = +80%`, **`101+` = +70%** (floor). This is **not** special #6's +10%/level.

---

## Combat-stat setter formulas (reference)

```
setPlayerAtkRange(v)    → atkRange    = baseAtkRange + v
setPlayerAtkDuration(v) → atkDuration = 10000 / (baseAtkDuration + v)   // higher v ⇒ faster
setPlayerNumShot(v)     → numShot     = 1 + v
setPlayerNumBounce(v)   → numBounce   = v
maxHp / atkDmg / def    = baseStat * 1.03^totalLevelExp * (1+0.4*trans) * (1 + min(transPoint,100)/100)
```

## API surface (`CastleService`, class `BP`; route group `JN.CASTLE`)

| Method | Route | Payload |
|---|---|---|
| `getCastle` | `/castle/getCastle` | `{}` |
| `upgrade` | `/castle/upgrade` | `{kindNums, levels, gold, goldPerSec}` |
| `updateCastleKindNum` | `/castle/updateCastleKindNum` | `{castleKindNum}` — **no caller in bundle** |
| `upgradeSpecial` | `/castle/upgradeSpecial` | `{kindNum, level}` |
| `enhance` | `/castle/enhance` | `{enhance}` |
| `enhanceUp` | `/castle/enhanceUp` | `{enhance}` |
| `enhanceReset` | `/castle/enhanceReset` | `{}` |

Guild (unrelated to personal castle): `/guildDefense/getCastleDefense`, `/guildWar/getCastleStatus`, `/guildWar/attackV3Start` (`castleIdStr`). Game-over: `/user/castleDestroyed`. Rebirth team: `/user/setReviveTeam`, `/user/getReviveTeam`. Rage: `/wave-call/getWaveCallInfo`, `/wave-call/callNextWave`, `/wave-call/increaseMaxWaveCall`.

---

## Open questions

1. **Concrete server numbers**: the `CASTLE` / `CASTLE_SPECIAL` datasheets (each book's `initValue`/`incValue`/`maxLv`/`initCost`/`incCost`/`isPowered`, plus `cost|reqWaves|values` pipe-tables for specials), the gold `golds` cumulative table (`HERO_UPGRADE_TIER`), and the medal-enhance `medal` table or `exp/offset` segments (`HERO_MEDAL_ENHANCE_TIER`) are all loaded at runtime via `wD.getBook(...)` and are **not in the bundle**. A live `getCastle`/book payload is needed to recover the exact cost curves and per-level grant magnitudes (HP per Durability level, Range/AtkSpeed/MultiShot/Bounce per level, lives per Arcane-of-Life level).
2. **`MEDAL_ENHANCE_USE_FORMULA`**: whether it is set to `'1'` in live clientData (selecting the `round(exp^(h/5)+3*h)+offset` formula vs an explicit table) is not determinable from the bundle. If formula-mode and `CASTLE_MAX_ENHANCE > 1000`, client-side `getCost` returns 0 above level 1000 (hero-bounded table) — confirm whether the server reconciles.
3. **Multi-skin future**: does the server ever return `castleKindNum != 10001`? `/castle/updateCastleKindNum` exists but is uncalled; no `CASTLE_KIND_NAME_*` table or `10002+` literals exist. Confirm whether multiple castle kinds are shipped/selectable.
4. **Castle base stats**: the resolved `bvo` for `castleVO` (base `maxHp`/`atkDmg`/`def`, tribe, growth) comes from the unit `BookVO` table (`getBookVO(10001)`); the className `ElfTown5` *(uncertain)* suggests ELF/`tribe=2`, but base values are server-authoritative. The `SpeedArrow2` weapon's damage/projectile behavior (speed, AoE, pierce) was not traced.
5. **OTH multiplier**: no source in the bundle emits an `OurTowerHp` (`OTH`) combat code, so the castle HP multiplier may always be `1.0` unless live server hero/treasure/pet data defines OTH-coded buffs. Confirm whether any does; also confirm whether OTH scales only HP (as shown) or also atk/def.
6. **Special codes**: special book `.code` values are server-assigned (`setBookDataForSpecial` copies `s.code`). The index→code mapping (e.g. book 2 = `humansecret`, book 5 = `wavecall` vs the dead `orcsecret`) is inferred from locale + the `kx`/`xN` enums; verify against live book data — especially whether kindNum 5 carries `wavecall` or the unused `orcsecret`.
7. **Enhance→stat magnitude**: each enhance point adds ×1.03 via `totalLevelExp`, but the precise enhance-to-HP outcome runs through the shared combat-unit setData scaling and server unit params; not independently isolated.
8. **`castleMedalLevels`**: declared but unused client-side (no serializer). Confirm whether the server still reads/writes it (legacy) or it is fully deprecated.
9. **Medal Buff path**: confirm whether the special-#6 `medal` code feeds `getGameplayMultiplier(MedalBuff)` at the rebirth screen vs. the separate hero MedalBuff skill path.
10. **kindNum 1 final shot count**: wave setup sets `player.numShot = 1` then `setPlayerNumShot(1 + book4)` overrides — confirm the final effective shot count and that Castle0's base `numShot=3` is indeed superseded.
11. **Server-side game-over validation**: only client POSTs to `/user/castleDestroyed` and continue/rebirth are visible; whether revive/rebirth is gated or rewarded server-side is unknown.