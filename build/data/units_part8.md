# EF2 unit mechanics — Part 8 (Boars, RoboBombs, Frogs, Castles, Raid Kings)

> **Scope note on descriptions / kindNums.** None of these 12 classes appear in `/tmp/unit_desc.json`.
> That table only covers playable *heroic* units (kindNum 1–96, 1001–1062) and the four named act-bosses
> (10001 Elf Castle, 20001 King Slime, 30001 Orc Flower, 40001 Hammer Mole, 50001 Dark Hermit).
> In the bundle, `fx` is a pure className string-enum (`t.Boar1="Boar1"`, …) with **no numeric kindNum** —
> verified at byte 854200–854900. So **Boar/RoboBomb/Frog are enemy wave units**, **Castle0/1/2 are the
> player's defended structure**, and **ScorpionKing/HarpyKing/GolemKing are raid bosses** that are *not*
> the act-bosses in unit_desc. There are no `UNIT_NATK_<k>` / `UNIT_SATK_<k>` strings for any of them
> (the only Castle locale keys are upgrade names like `CASTLE_NAME_4 "Multi-Shot"`). Each section below
> states this explicitly under "Description (in-game)" rather than inventing a kindNum match.

Shared base-class facts used below (all verified in-bundle):
- `blow(vx,vy,vh)` (knockback) is scaled by weight: `factor = 1 - 0.2*(weight-1)`, and is a no-op if `blowImmune`.
- `heal(t, src, isPercent=true, ...)`: if `isPercent` ⇒ amount `= maxHp * 0.01 * t` (t is **% of max HP**); if `false` ⇒ flat `t`.
- `getEnemiesWithin(r)` / `getEnemiesWithPos(x,y,r)` = alive, targetable enemies inside radius `r` (square + circle test).

---

### Boar1 — `Boar1` (kindNum: none — enemy wave unit, not in unit_desc)
**Role:** basic enemy (melee, knockback)
**Description (in-game):** No `UNIT_NATK`/`UNIT_SATK` entry exists for this class (see scope note).
**How it works (code):** Trivial melee attacker extending `qQ`. `attackMain()` calls `super.attackMain()` (the hit lands on attack-frame 50 per `objAtk={50:1}`) then, if the target is alive, knocks it back with `blow(3*direction, -3.5)` — a small horizontal shove in its facing direction plus a slight upward pop. No skill (`hasSkill` not set), no buffs, no cooldown logic. `setSize(.95)`.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| objAtk | `{50:1}` | hit fires on attack-anim frame 50 (1 hit) |
| blow vx | `3*direction` | horizontal knockback impulse |
| blow vy | `-3.5` | upward knockback impulse |
| radius / hitHeight / hitWidth | 13 / 22 / 15 | collision box |
| setSize | 0.95 | sprite scale |
**Formulas:** knockback magnitude further scaled by target weight `1-0.2*(weight-1)`.
**Buffs/debuffs applied:** none (only the per-hit knockback).
**Δ description vs code:** n/a — no in-game description exists to compare against.

---

### Boar2 — `Boar2` (kindNum: none — enemy wave unit, not in unit_desc)
**Role:** basic enemy (melee, knockback, self-heal — the "elite" boar)
**Description (in-game):** No `UNIT_NATK`/`UNIT_SATK` entry exists (see scope note).
**How it works (code):** Same shape as Boar1 but stronger and **self-healing**. `attackMain()` knocks the target back with `blow(4*direction, -4.5)` (harder than Boar1's 3/-3.5) and then calls `this.heal(3, this, true)` — because `isPercent=true`, that heals **3% of its own max HP every time it lands a hit** (NOT a flat 3). Hit fires on frame 50 (`objAtk={50:1}`). No discrete skill/cooldown; the heal is part of the normal attack. `setSize(1.05)` (bigger than Boar1).
**Hard values:**
| variable | value | meaning |
|---|---|---|
| objAtk | `{50:1}` | hit on frame 50 |
| blow vx / vy | `4*direction` / `-4.5` | knockback (stronger than Boar1) |
| heal amount | `3` (percent) | lifesteal = 3% of max HP per landed hit |
| radius / hitHeight | 13 / 24 | collision |
| setSize | 1.05 | sprite scale |
**Formulas:** heal `= maxHp * 0.01 * 3` = 3% max HP per hit; knockback weight-scaled as above.
**Buffs/debuffs applied:** none on enemies; self-heal on hit only.
**Δ description vs code:** n/a — no in-game description.
**Notes:** vs Boar1: +knockback, +size, and the on-hit 3%-max-HP self-heal is the defining upgrade.

---

### RoboBomb1 — `RoboBomb1` (kindNum: none — enemy wave unit, not in unit_desc)
**Role:** basic enemy — **suicide bomber** (explode-on-arrival)
**Description (in-game):** No `UNIT_NATK`/`UNIT_SATK` entry exists (see scope note).
**How it works (code):** A walking bomb. It does **no normal attack**; instead, once it gets a target within attack range, `execute()` starts a fuse: `fuseStarted=true`, then `fuseTimer++` each tick. When `fuseTimer >= fuseDelay (60)` it sets `selfDestruct=true`, calls `die()`, and spawns a `RoboExplode` effect (`start(100)`) at its position. `onDie()` (guarded by `selfDestruct`) then grabs every enemy within radius **70**, deals **10** flat damage each via `doDamage(i,10)`, and to survivors applies `blow(±7, -7)` (sign depends on whether they're left/right of the bomb). If it dies *without* self-destructing (killed first), `onDie()` returns early — **no explosion if you kill it before the fuse completes.**
**Hard values:**
| variable | value | meaning |
|---|---|---|
| fuseDelay | 60 | ticks (~1.0 s @1×) in-range before it detonates |
| explosion radius | 70 | px AoE on detonation |
| explosion damage | 10 | flat damage to each enemy in radius |
| knockback | `±7, -7` | survivors blown horizontally/up |
| objAtk | `{14:1}` | (unused for damage — it explodes, not attacks) |
**Formulas:** detonation gated by `fuseTimer >= 60` while target in `atkRange`.
**Buffs/debuffs applied:** none.
**Δ description vs code:** n/a — no in-game description.
**Notes:** Killing it before the fuse fills cancels the blast entirely (`onDie` early-returns when `!selfDestruct`).

---

### RoboBomb2 — `RoboBomb2` (kindNum: none — enemy wave unit, not in unit_desc)
**Role:** basic enemy — **cloaked suicide bomber** (bigger blast, fuse warning)
**Description (in-game):** No `UNIT_NATK`/`UNIT_SATK` entry exists (see scope note).
**How it works (code):** Upgraded RoboBomb. Spawns **cloaked** (`setData` sets `this.cloaking=true`). Same fuse loop, but with a *warning phase*: once in range, `fuseTimer++`; at `fuseTimer >= fuseWarning (40)` it begins **blinking red** (`this.tint = (fuseTimer>>1 & 1) ? 16724787 : 16777215` — alternating red/white per ~2 ticks); at `fuseTimer >= fuseDelay (60)` it forces tint white, sets `selfDestruct`, `die()`s, and spawns `RoboExplode (start(100))`. `onDie()` (if self-destructed): enemies within radius **80** take **15** flat damage (`doDamage(i,15)`), survivors get `blow(±7, -7)`.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| fuseDelay | 60 | ticks in-range to detonate |
| fuseWarning | 40 | tick at which it starts blinking red |
| cloaking | true | starts hidden until engaged |
| explosion radius | 80 | px AoE (bigger than RoboBomb1's 70) |
| explosion damage | 15 | flat damage each (vs RoboBomb1's 10) |
| knockback | `±7, -7` | survivor knockback |
| warn tint | `16724787` red / `16777215` white | blink colors |
**Formulas:** blink: `tint = (fuseTimer>>1 & 1) ? red : white`; detonate at `fuseTimer>=60`.
**Buffs/debuffs applied:** none.
**Δ description vs code:** n/a — no in-game description.
**Notes:** vs RoboBomb1: +cloak on spawn, +20-tick red-blink telegraph, +radius (80 vs 70), +damage (15 vs 10). Same "no kill ⇒ no boom" rule (`onDie` returns unless `selfDestruct`).

---

### Frog1 — `Frog1` (kindNum: none — enemy wave unit, not in unit_desc)
**Role:** basic enemy — **flying jumper** that dives the castle and single-target melees
**Description (in-game):** No `UNIT_NATK`/`UNIT_SATK` entry exists (see scope note).
**How it works (code):** Spawns **flying** (`flying=true, isAir=true, airHeight=55`) and ignores normal AI while airborne. `doFlying()` finds the castle (`findCastleTarget()` = first alive enemy with `isCastle`) and homes toward it at `moveSpd`; when within `landDistance (40)` it calls `startLanding()`, descends over `landingDuration (12)` ticks, and on touchdown, if it `landedNearCastle`, deals **1** flat damage to the castle (`doDamage(castle,1)`) then drops into normal idle/melee. While airborne it is **invulnerable** (its `health` setter ignores writes while `flying||landingTimer>0`) and **stun-immune** (`stun()` no-ops while flying). It can be knocked out of the air: `onHitted()` increments `airHitCount` and forces a landing once `airHitCount >= 2`. After landing it's an ordinary frame-74 single-target melee (`objAtk={74:1}`).
**Hard values:**
| variable | value | meaning |
|---|---|---|
| airHeight (start) | 55 | spawn altitude |
| landDistance | 40 | px from castle at which it starts to land |
| landingDuration | 12 | ticks of descent animation |
| airFrames | `QK(0,12)` | in-air anim loop |
| airHitCount to drop | 2 | hits needed to force it down |
| castle landing damage | 1 | flat dmg on touchdown if near castle |
| objAtk | `{74:1}` | post-landing melee hit frame |
**Formulas:** descent: `airHeight = startAirHeight*(1 - t)` where `t = 1 - landingTimer/landingDuration`.
**Buffs/debuffs applied:** none.
**Δ description vs code:** n/a — no in-game description.
**Notes:** Invulnerable + stun-immune while airborne; only ranged/AoE that registers `onHitted` twice can drop it before it reaches the castle.

---

### Frog2 — `Frog2` (kindNum: none — enemy wave unit, not in unit_desc)
**Role:** basic enemy — **flying jumper** with an AoE ground attack (the "toad" upgrade)
**Description (in-game):** No `UNIT_NATK`/`UNIT_SATK` entry exists (see scope note).
**How it works (code):** Same fly-to-castle behavior as Frog1, but **flies higher** (`airHeight=88` vs 55) and is **tougher to drop** — `onHitted()` needs `airHitCount >= 3` (vs 2) to force a landing. Touchdown still deals **1** to the castle. The key upgrade is its **AoE melee**: `attackMain()` targets a point `35*direction` in front, gathers up to **5** ground enemies within radius **35** via `getEnemiesWithPos` (excludes air units), deals **1** flat damage each and `blow(3*direction, -3.5)` to survivors. Hit fires on frame 86 (`objAtk={86:1}`). Same airborne invulnerability/stun-immunity as Frog1.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| airHeight (start) | 88 | spawn altitude (higher than Frog1) |
| airHitCount to drop | 3 | hits to force landing (vs 2) |
| landDistance / landingDuration | 40 / 12 | same as Frog1 |
| airFrames | `QK(0,19)` | longer in-air loop |
| AoE offset | `35*direction` | center of the ground swipe |
| AoE radius | 35 | px |
| AoE max targets | 5 | enemies hit per swing |
| AoE damage | 1 | flat each |
| AoE knockback | `3*direction, -3.5` | per survivor |
| castle landing damage | 1 | on touchdown |
| objAtk | `{86:1}` | melee hit frame |
**Formulas:** same descent curve as Frog1.
**Buffs/debuffs applied:** none.
**Δ description vs code:** n/a — no in-game description.
**Notes:** vs Frog1: higher spawn, +1 hit to knock down, and a 5-target/35-radius AoE swipe with knockback (Frog1 is single-target).

---

### Castle (base) — `BaseCastle` (`QQ`) — the player's structure
**Role:** castle (defended HP structure that also auto-fires)
**Description (in-game):** No `UNIT_NATK`/`UNIT_SATK`; the related locale keys are *upgrade* names: `CASTLE_NAME_1 "Castle Durability"`, `CASTLE_NAME_2 "Castle Range"`, `CASTLE_NAME_3 "Castle Atk Speed"`, `CASTLE_NAME_4 "Multi-Shot"`, `CASTLE_NAME_5 "Bounce Shot"`. Castle0/1/2 below all extend this `QQ` base.
**How it works (code):** `isCastle=true`, `isImmovable=true`. It **passively regenerates**: `execute()` increments `regenTimer`, and every `REGEN_INTERVAL (450)` ticks it `heal(0.5, null, true)` ⇒ **0.5% of max HP per 450 ticks** if not full. It is **immune to every status/crowd-control**: `stun/knockBack/onHitted/addDotDamage/shock/freeze/curse/silence/poison/blow/binding` are all overridden to no-ops; `updateCrowdControl()` just decrements its shield counters and returns false. A damage-state visual ("castle on fire") escalates through **9 levels** as HP drops in 10% steps (`updateDamageFire`: ≤10%→level 9 … ≤90%→level 1), adding/scaling fire effects at fixed `FIRE_POSITIONS`. It's clickable (`onPointerDown` toggles the attack-range circle and shows the health bar for 225 ticks). `doIdle()` finds the nearest enemy and attacks when in range.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| numShot (base) | 1 | shots per attack (raised by upgrades) |
| hpRegenPerSec | 0.001 | (declared; effective regen below) |
| REGEN_INTERVAL | 450 | ticks between regen ticks (~7.5 s @1×) |
| regen heal | 0.5 (percent) | 0.5% of max HP each interval |
| damage-fire levels | 9 | fire stages at 10% HP increments |
| health-bar show time | 225 | ticks the bar stays after a click |
**Formulas:** regen `= maxHp*0.01*0.5` per 450 ticks. Player upgrades feed in via setters: `setPlayerNumShot(t)⇒numShot=1+t`, `setPlayerNumBounce(t)⇒numBounce=t`, `setPlayerAtkRange(t)⇒atkRange=baseAtkRange+t`, `setPlayerAtkDuration(t)⇒atkDuration=1e4/(baseAtkDuration+t)`.
**Buffs/debuffs applied:** none.
**Δ description vs code:** n/a — no unit description; matches the upgrade-key intent (multi-shot, bounce, range, atk-speed, durability).
**Notes:** Total CC-immunity and immovability are the defining structural traits; HP only changes from incoming damage and the slow 0.5%/450-tick self-heal.

---

### Castle0 — `Castle0` (kindNum: none — player castle, not in unit_desc)
**Role:** castle (the starting / fixed-loadout castle, RANGE)
**Description (in-game):** No `UNIT_NATK`/`UNIT_SATK` (see Castle-base note).
**How it works (code):** Extends `QQ` (BaseCastle). A stationary (`moveSpd=0`) **ranged** tower firing `SpeedArrow2`. It's the only Castle variant that **hard-codes `numShot=3`** in `initializeData` (Castle1/Castle2 leave it at the base `1`, expecting it to be raised by the player's Multi-Shot upgrade). `attackMain()` is a **fractional multi-shot**: it pulls `ceil(numShot)` attackable enemies, then for each successive target rolls `random.chance(s)` with `s` starting at `numShot` and decrementing by 1 — so e.g. `numShot=3.4` fires at the 1st/2nd/3rd targets for sure and the 4th with 40% chance. `generateWeapon` spawns the arrow from a point 35px toward the target, carrying `bounceCount = numBounce`. Hit frame 23 (`objAtk={23:1}`).
**Hard values:**
| variable | value | meaning |
|---|---|---|
| numShot | 3 | hard-coded shot count (unique to Castle0) |
| moveSpd | 0 | immobile |
| radius / hitHeight | 22 / 67 | collision |
| weaponClass | `SpeedArrow2` | projectile fired |
| objAtk | `{23:1}` | hit/fire frame |
| numBlock | 0 | blocks no enemies |
**Formulas:** multi-shot: target `e` fired iff `random.chance(numShot - e)`; weapon offset `x+35*cos(angle), y-25+35*sin(angle)`.
**Buffs/debuffs applied:** none.
**Δ description vs code:** n/a.
**Notes:** Identical body to Castle1/Castle2 except for the `numShot=3` literal in `initializeData`.

---

### Castle1 — `Castle1` (kindNum: none — player castle, not in unit_desc)
**Role:** castle (RANGE, upgrade-driven shot count)
**Description (in-game):** No `UNIT_NATK`/`UNIT_SATK` (see Castle-base note).
**How it works (code):** Identical to Castle0 in every method (`SpeedArrow2`, `moveSpd=0`, fractional-`numShot` multishot via `random.chance`, bounce via `numBounce`, fire frame 23) **except it does NOT set `numShot` in `initializeData`** — it keeps the base `numShot=1` and relies on the player's Multi-Shot upgrade (`setPlayerNumShot`) to raise it. Functionally a mid-tier castle skin/tier whose firepower comes from player progression, not a built-in literal.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| numShot | (inherited 1) | not overridden — driven by upgrades |
| moveSpd / radius / hitHeight | 0 / 22 / 67 | same as Castle0 |
| weaponClass | `SpeedArrow2` | projectile |
| objAtk | `{23:1}` | fire frame |
**Formulas:** same multishot/bounce/offset formulas as Castle0.
**Buffs/debuffs applied:** none.
**Δ description vs code:** n/a.
**Notes:** Only delta vs Castle0 is the absence of the `numShot=3` literal.

---

### Castle2 — `Castle2` (kindNum: none — player castle, not in unit_desc)
**Role:** castle (RANGE, top-tier skin, upgrade-driven)
**Description (in-game):** No `UNIT_NATK`/`UNIT_SATK` (see Castle-base note).
**How it works (code):** Byte-for-byte the same method bodies as Castle1 (and Castle0 minus the literal): extends `QQ`, `SpeedArrow2`, `moveSpd=0`, `radius=22`, `hitHeight=67`, fractional-`numShot` multishot, `numBounce` bounce, fire frame 23, `die()` re-shows the sprite. `numShot` is **not** set in `initializeData` (stays base 1, raised by player upgrades). It is the highest castle tier; mechanically distinguished from Castle1 only by its tier/art, not by code constants.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| numShot | (inherited 1) | upgrade-driven |
| moveSpd / radius / hitHeight | 0 / 22 / 67 | identical to Castle1 |
| weaponClass | `SpeedArrow2` | projectile |
| objAtk | `{23:1}` | fire frame |
**Formulas:** same as Castle0/Castle1.
**Buffs/debuffs applied:** none.
**Δ description vs code:** n/a.
**Notes:** No mechanical delta from Castle1 in code; difference is tier/cosmetic.

---

## Raid-boss base — `BaseRaidUnit` (`E2`/`A2`)
The three "King" bosses below all extend `BaseRaidUnit`. Shared framework (verified):
- **Spine-animated** (`spineKey`, `bossScale=1.3` default, per-boss `spineTimeScale`); state→animation mapping; a **weak-point bone** (head) drives flash/tint feedback.
- **Total CC-immunity**, doubly enforced: constructor sets `blowImmune/stunImmune/freezeImmune/knockImmune=true` AND `stun/freeze/curse/silence/binding/poison/shock/knockBack/blow` are no-op overrides. `weight=5`, `bossType=1`.
- **Raid-stun ("groggy") mechanic**: `applyRaidStun(frames)` is a *separate* system from normal CC — it sets `raidStunFrames`, plays the groggy animation, and freezes attacks for the duration (this is the intended "hit the weak point to stagger the boss" loop).
- **Skill selection** (`pickSkill`): if a queued `arrAttackTypeList` exists it shifts from that; else it walks a per-battle random **`attackOrderList`** sequence; else the first `numForSkillAttack (=2)` attacks are forced to the normal attack (skill 0), after which it rolls against the descending **`skillRatio`** thresholds to pick a skill index. `skill0` = normal attack; `skillN(i)` = skill `i`.
- **Wander AI** between attacks (`wanderEnabled`, `wanderInterval`, bounded by `wanderMin/MaxX/Y` = 100–540 / 200–950), plus `targetSwapChance` (re-roll target on each attack) and `wanderAfterAttackChance`.
- **Outgoing damage** is multiplied by `getRaidBossDamageMultiplier()` from the battle controller (a raid-difficulty scalar). `radialBlow/radialKnockback` push enemies away from an impact point, scaled by per-boss `BLOW_SCALE`.

---

### ScorpionKing — `ScorpionKing` (kindNum: none — raid boss, not in unit_desc)
**Role:** boss (raid) — poison/pull bruiser
**Description (in-game):** No `UNIT_NATK`/`UNIT_SATK` entry (raid bosses are not in the unit_desc table).
**How it works (code):** Spine boss (`raids/raid1/Scorpion`, `spineTimeScale=.82`, `wanderEnabled`). Four moves, sequenced by `attackOrderList` (three preset patterns) then `skillRatio=[.78,.55,.3,0]`, `numForSkillAttack=2`. **att_01 (normal):** dash to the target (`startAttackDashTo`), then radial AoE at the `target_01` bone — radius **100**, `random.range(1,3)` damage to all in-radius, plus `radialBlow`. **att_02 (skill 1) — pull + poison splash:** over the splash window it **pulls** all movable enemies toward the splash center within radius **200** at speed **12**, then once applies a radius-**150** splash: `random.range(1.5,3)` damage + `poison(random 100–150)` to each, a `radialBlow`, and spawns a **lingering poison area** (`ScorpionPoisonArea`, ellipse 112.5×54, **1200**-tick duration, **1 dmg/sec**). **att_03 (skill 2) — poison-bullet volley:** dashes to the enemy centroid, then fires up to **7 batches × 16 bullets** (`ScorpionPoisonBullet`, `random.range(1,2)` dmg each, staggered by `delay=floor(n/4)`) from the `tail_ball` bone at random targets. **att_04 (skill 3) — impact slam:** radius-**110** impact (`random.range(1,3)` dmg + **stun 240** ticks to each), a radius-**200** `radialBlow`, and on the `baby_att_hit` spine event a radius-**100** `radialKnockback` (power 6–10, dur 18). `escapeSkill()` forces att_04.
**Hard values (selected; all `zt(S2,…)`):**
| variable | value | meaning |
|---|---|---|
| BLOW_SCALE | 0.7 | knockback multiplier |
| skillRatio / numForSkillAttack | `[.78,.55,.3,0]` / 2 | skill-pick thresholds; 2 forced normals |
| ATT1_RADIUS / DAMAGE | 100 / `1–3` | normal-attack AoE |
| ATT2_PULL_RADIUS / SPEED | 200 / 12 | vacuum pull |
| ATT2_SPLASH_RADIUS / DAMAGE | 150 / `1.5–3` | splash hit |
| ATT2_POISON_MIN/MAX | 100 / 150 | poison stacks applied |
| ATT2 poison-area | 112.5×54, dur 1200, 1 dmg/s | lingering pool |
| ATT3 bullets | 16/batch × 7 batches, `1–2` dmg | poison-bullet volley |
| ATT4_IMPACT_RADIUS / DAMAGE | 110 / `1–3` | slam core |
| ATT4_STUN_DURATION | 240 | ticks stunned |
| ATT4_BLOW_RADIUS | 200 | slam knockback radius |
| ATT4_KNOCKBACK (radius/power/dur) | 100 / `6–10` / 18 | baby-hit knockback |
**Formulas:** pull step `= min(dist, PULL_SPEED*(0.4 + (1 - dist/PULL_RADIUS)))` (closer = stronger pull). `radialBlow` impulse `= (min + rand*(max-min)) * BLOW_SCALE`.
**Buffs/debuffs applied to enemies:** poison (att_02 splash 100–150 + 1 dmg/s pool), stun 240 (att_04), plus knockback/blow.
**Δ description vs code:** n/a — no in-game description.

---

### HarpyKing — `HarpyKing` (kindNum: none — raid boss, not in unit_desc)
**Role:** boss (raid) — **flying** air-only diver / feather-storm caster
**Description (in-game):** No `UNIT_NATK`/`UNIT_SATK` entry (raid boss).
**How it works (code):** Spine boss (`raids/raid1/Harpy`, `spineTimeScale=.84`, `wanderEnabled`, `airTargetOnly=true`, `hitHeight=200`). Five attack slots driven by very long preset `attackOrderList` rows, with `skillRatio=[.75,.55,.35,.15,0]`. Note `pickSkill()` overrides skill index **1 → 0** (so "skill 1" resolves to a re-dash normal). **att1 (normal) — dive:** dashes to a random alive *corp* (squad) center; during the hover window it tracks that corp (`ATT1_HOVER_SPEED 3` from frame 20), and on each hit event deals up to **7** hits (`ATT1_HITS_PER_EVENT`) of `random.range(1,2)` within radius **100**. **att2 (skillMain2) — slam + tornadoes:** `blow`s every enemy within 300×200, then `spawnSlamTornadoes()` drops **1 tornado** (2 after `TORNADO_TWO_AFTER_FRAMES=5400` battle-frames) — `HarpyTornado` ellipse **70×56**, **1200**-tick duration, dealing **`TORNADO_DAMAGE_PERCENT=0.5`** (i.e. 0.5 → percent-style tornado damage), following an aggro/random corp center. **att4 (skillMain3) — cone knockback:** a forward cone (radius **300**, half-angle **π/4**), `random.range(1,2)` dmg + `knockBack(power 8–14, dur 12)` to non-immovable enemies in the cone; facing is locked during it. **att5 (updateAtt5Feathers) — feather barrage:** during the att5 anim it fires **7 bursts** (at spine frames 28–40) of **20 feathers** each (`HarpyFeather`, `random.range(1.2,2.5)` dmg) radiating from the `shout` bone at corp/aggro targets (first `FEATHER_AGGRO_BURSTS=3` bursts prefer the highest-aggro corp). `escapeSkill()` ⇒ skill 4.
**Hard values (selected; `zt(T2,…)`):**
| variable | value | meaning |
|---|---|---|
| BLOW_SCALE | 0.75 | knockback multiplier |
| ATT1_RADIUS / HITS_PER_EVENT / DAMAGE | 100 / 7 / `1–2` | dive multi-hit |
| ATT1_HOVER_SPEED / START_FRAME | 3 / 20 | corp-tracking hover |
| ATT4_RADIUS / CONE_HALF_ANGLE | 300 / `π/4` | cone sweep |
| ATT4_KNOCKBACK power/dur | `8–14` / 12 | cone knockback |
| FEATHER_PER_BURST / fire frames | 20 / `[28,30,32,34,36,38,40]` | feathers/burst, 7 bursts |
| FEATHER_DAMAGE | `1.2–2.5` | per feather |
| FEATHER_AGGRO_BURSTS | 3 | first bursts target aggro corp |
| TORNADO (radius/dur/dmg%) | 70×56 / 1200 / 0.5 | slam tornado AoE |
| TORNADO_TWO_AFTER_FRAMES | 5400 | battle-frame threshold for 2 tornadoes |
**Formulas:** cone test `dirToEnemy · facing ≥ cos(π/4)`; tornado uses `setMoveTargetProvider` to chase a corp center.
**Buffs/debuffs applied to enemies:** knockback (att2 blow, att4 cone), plus DoT from lingering tornadoes; no stun/freeze.
**Δ description vs code:** n/a — no in-game description.
**Notes:** `airTargetOnly` + `hitHeight=200` mark it as a true aerial boss; the `pickSkill` 1→0 remap means slot 1 is effectively an extra dashing normal.

---

### GolemKing — `GolemKing` (kindNum: none — raid boss, not in unit_desc)
**Role:** boss (raid) — **teleporting** heavy slammer
**Description (in-game):** No `UNIT_NATK`/`UNIT_SATK` entry (raid boss).
**How it works (code):** Spine boss (`raids/raid1/Golem`, `spineTimeScale=.8`, `wanderEnabled`, `hitHeight=180`, weak point = `Head` bone, offset −25). Six skill slots; `skillRatio=[.78,.6,.42,.26,.12,0]`, `numForSkillAttack=2`. `BLOW_SCALE = 0.75*0.6 = 0.45` (extra-damped knockback). **att1 (normal) — double-tick slam:** AoE at the `R_Arm_01` bone, radius **200**, up to **80** targets, `random.range(1,2.5)` dmg + per-target knockback; then it queues a **second tick** `ATT1_SECOND_TICK_DELAY=10` ticks later that repeats the slam. **att3 (skillMain2) — radial slam:** `radialBlow` at self, radius **300**, blow power 3–12. **att5 (skillMain4) — pillar barrage:** for each of **9** `stone_pillar_0X` bones it does a radius-**70** blast (up to **10** targets, `random.range(1.4,2.8)` dmg + knockback). **att2 (skillN 1) — charge:** locks facing toward aggro/centroid and **slides forward** at `ATT2_CHARGE_SPEED=3` for `ATT2_DURATION_FRAMES=120`, doing a radius-**80** hit (≤5 targets, `random.range(1.5,2.5)`) every `ATT2_TICK_INTERVAL=3` frames at an offset point. **Teleport (skill `SKILL_TELEPORT=5`):** plays `teleport_out`, becomes `attackable=false`+`isUntagetable`, freezes player units in place (`freezeAlliesInPlace`), stays underground `TELEPORT_UNDERGROUND_FRAMES=120` ticks, **relocates randomly** within wander bounds, plays `teleport_in`, then **emerges with a huge slam**: `emergeRadialBlow` radius **480**, power **15.2–24.3** (vh 10.6–18.2) — the biggest hit in its kit. `escapeSkill()` ⇒ teleport.
**Hard values (selected; `zt(O2,…)`):**
| variable | value | meaning |
|---|---|---|
| BLOW_SCALE | `0.75*0.6` = 0.45 | knockback multiplier (heavily damped) |
| skillRatio / numForSkillAttack | `[.78,.6,.42,.26,.12,0]` / 2 | 6-slot pick; 2 forced normals |
| ATT1_RADIUS / MAX_TARGETS / DAMAGE | 200 / 80 / `1–2.5` | main slam |
| ATT1_SECOND_TICK_DELAY | 10 | ticks until the repeat slam |
| ATT3_RADIUS / POWER | 300 / `3–12` | radial slam |
| ATT5 pillars | 9 bones, r70, ≤10 tgt, `1.4–2.8` dmg | pillar barrage |
| ATT2 charge | speed 3, 120 frames, r80, ≤5 tgt, `1.5–2.5`, tick 3 | moving charge |
| TELEPORT_UNDERGROUND_FRAMES | 120 | time hidden/untargetable |
| EMERGE_RADIUS / POWER | 480 / `15.2–24.3` (vh 10.6–18.2) | emergence slam (biggest) |
**Formulas:** `BLOW_SCALE` doubly damped (0.75×0.6) so its knockbacks are short despite large power numbers; emergence uses the same `radialBlow` with the EMERGE_* constants.
**Buffs/debuffs applied to enemies:** knockback on nearly every hit; teleport freezes player units' positions; no stun/poison.
**Δ description vs code:** n/a — no in-game description.
**Notes:** The teleport→relocate→emerge-slam (radius 480) is the signature combo, and it's `attackable=false`+untargetable for those 120 underground ticks. att1's built-in second tick (after 10 ticks) means its "normal" attack double-hits.
