# EF2 unit mechanics — Part 8 (Boars, RoboBombs, Frogs, Castles, Raid Kings)

> **Scope note on descriptions / kindNums.** None of these 12 classes appear in `/tmp/unit_desc.json`.
> That table only covers playable *heroic* units (kindNum 1–96, 1001–1062) and the four named act-bosses
> (10001 Elf Castle, 20001 King Slime, 30001 Orc Flower, 40001 Hammer Mole, 50001 Dark Hermit).
> In the bundle, `fx` is a pure className string-enum (`t.Boar1="Boar1"`, …) with **no numeric kindNum** —
> verified at byte 854200–854900. So **Boar/RoboBomb/Frog are enemy wave units**, **Castle0/1/2 are the
> player's defended structure**, and **ScorpionKing/HarpyKing/GolemKing are raid bosses** that are *not*
> the act-bosses in unit_desc. There are no `UNIT_NATK_<k>` / `UNIT_SATK_<k>` strings for any of them
> (the only Castle locale keys are upgrade names like `CASTLE_NAME_4 "Multi-Shot"`). Because none of these
> units has a localized description, each one ends with a short **Description vs code** note rather than a
> verbatim quote / validated delta.

Shared base-class facts used below (all verified in-bundle):
- `blow(vx,vy,vh)` (knockback) is scaled by weight: `factor = 1 - 0.2*(weight-1)`, and is a no-op if `blowImmune`.
- `heal(t, src, isPercent=true, ...)`: if `isPercent` ⇒ amount `= maxHp * 0.01 * t` (t is **% of max HP**); if `false` ⇒ flat `t`.
- `getEnemiesWithin(r)` / `getEnemiesWithPos(x,y,r)` = alive, targetable enemies inside radius `r` (square + circle test).

---

### Boar1 — `Boar1` (kindNum: none — enemy wave unit, not in unit_desc)
**TL;DR.** A plain melee enemy that shoves whatever it hits a short distance backward.

**At a glance**
- **Role:** Basic enemy (melee, knockback)
- **Attack:** basic melee on the nearest enemy, hit lands on attack-frame 50
- **Signature:** every landed hit knocks the target back (small horizontal shove + slight upward pop)
- **No skill, no buffs, no cooldown logic**

**Normal attack**
- Calls `super.attackMain()` (hit fires on frame 50 per `objAtk={50:1}`); if the target survives, applies `blow(3*direction, -3.5)` — a horizontal shove in its facing direction plus a slight upward pop.

**Key values**
| variable | value | meaning |
|---|---|---|
| objAtk | `{50:1}` | hit fires on attack-anim frame 50 (1 hit) |
| blow vx | `3*direction` | horizontal knockback impulse |
| blow vy | `-3.5` | upward knockback impulse |
| radius / hitHeight / hitWidth | 13 / 22 / 15 | collision box |
| setSize | 0.95 | sprite scale |

**Formulas**
- Knockback magnitude further scaled by target weight: `1 - 0.2*(weight-1)`.

**Description vs code**
- No in-game description exists for this class (see scope note), so there is nothing to compare against.

---

### Boar2 — `Boar2` (kindNum: none — enemy wave unit, not in unit_desc)
**TL;DR.** The elite boar — harder knockback than Boar1 and it lifesteals 3% of its max HP on every hit.

**At a glance**
- **Role:** Basic enemy (melee, knockback, self-heal — the "elite" boar)
- **Attack:** basic melee, hit on frame 50
- **Signature:** stronger knockback `4/-4.5` **plus** self-heal of **3% max HP per landed hit**
- The heal is part of the normal attack — no discrete skill/cooldown

**Normal attack**
- Knocks the target back with `blow(4*direction, -4.5)` (harder than Boar1's 3/-3.5), then calls `heal(3, this, true)`. Because `isPercent=true`, that heals **3% of its own max HP** every time it lands a hit (NOT a flat 3).

**Passive / special**
- On-hit lifesteal: 3% of max HP per landed hit (defining upgrade over Boar1).

**Key values**
| variable | value | meaning |
|---|---|---|
| objAtk | `{50:1}` | hit on frame 50 |
| blow vx / vy | `4*direction` / `-4.5` | knockback (stronger than Boar1) |
| heal amount | `3` (percent) | lifesteal = 3% of max HP per landed hit |
| radius / hitHeight | 13 / 24 | collision |
| setSize | 1.05 | sprite scale |

**Formulas**
- Heal `= maxHp * 0.01 * 3` = 3% max HP per hit; knockback weight-scaled as `1 - 0.2*(weight-1)`.

**Description vs code**
- No in-game description exists; nothing to compare. (vs Boar1: +knockback, +size, and the on-hit 3%-max-HP self-heal.)

---

### RoboBomb1 — `RoboBomb1` (kindNum: none — enemy wave unit, not in unit_desc)
**TL;DR.** A walking suicide bomber that lights a ~1s fuse on reaching a target and explodes for flat AoE damage — kill it first and the blast is cancelled.

**At a glance**
- **Role:** Basic enemy — suicide bomber (explode-on-arrival)
- **No normal attack** — it detonates instead of hitting
- **Fuse:** 60 ticks (~1.0s) in attack range, then self-destructs
- **Blast:** radius 70, 10 flat damage each, survivors knocked back `±7,-7`
- **Kill-before-fuse ⇒ no explosion**

**Passive / special — fuse + detonation**
- Once a target is within attack range, `execute()` sets `fuseStarted=true` and increments `fuseTimer` each tick.
- At `fuseTimer >= fuseDelay (60)` it sets `selfDestruct=true`, calls `die()`, and spawns a `RoboExplode` effect (`start(100)`) at its position.
- `onDie()` (guarded by `selfDestruct`) grabs every enemy within radius **70**, deals **10** flat damage each via `doDamage(i,10)`, and applies `blow(±7, -7)` to survivors (sign depends on whether they're left/right of the bomb).
- If killed before the fuse completes, `onDie()` early-returns ⇒ **no explosion**.

**Key values**
| variable | value | meaning |
|---|---|---|
| fuseDelay | 60 | ticks (~1.0s @1×) in-range before it detonates |
| explosion radius | 70 | px AoE on detonation |
| explosion damage | 10 | flat damage to each enemy in radius |
| knockback | `±7, -7` | survivors blown horizontally/up |
| objAtk | `{14:1}` | unused for damage — it explodes, not attacks |

**Formulas**
- Detonation gated by `fuseTimer >= 60` while target stays in `atkRange`.

**Description vs code**
- No in-game description exists; nothing to compare. (Killing it before the fuse fills cancels the blast entirely — `onDie` early-returns when `!selfDestruct`.)

---

### RoboBomb2 — `RoboBomb2` (kindNum: none — enemy wave unit, not in unit_desc)
**TL;DR.** A cloaked suicide bomber with a bigger blast that blinks red as a fuse warning before it detonates.

**At a glance**
- **Role:** Basic enemy — cloaked suicide bomber (bigger blast, fuse warning)
- **Spawns cloaked** (`cloaking=true`) until engaged
- **Fuse:** warns at 40 ticks (blink red), detonates at 60 ticks
- **Blast:** radius 80, 15 flat damage each, survivors knocked back `±7,-7`
- **Kill-before-fuse ⇒ no explosion**

**Passive / special — fuse, warning blink, detonation**
- Spawns cloaked (`setData` sets `cloaking=true`). Once in range, `fuseTimer++`.
- **Warning phase:** at `fuseTimer >= fuseWarning (40)` it blinks red/white per ~2 ticks: `tint = (fuseTimer>>1 & 1) ? 16724787 : 16777215`.
- At `fuseTimer >= fuseDelay (60)` it forces tint white, sets `selfDestruct`, `die()`s, and spawns `RoboExplode` (`start(100)`).
- `onDie()` (if self-destructed): enemies within radius **80** take **15** flat damage (`doDamage(i,15)`); survivors get `blow(±7, -7)`.

**Base ↔ RoboBomb1 deltas**
- +cloak on spawn, +20-tick red-blink telegraph, radius 80 (vs 70), damage 15 (vs 10).

**Key values**
| variable | value | meaning |
|---|---|---|
| fuseDelay | 60 | ticks in-range to detonate |
| fuseWarning | 40 | tick at which it starts blinking red |
| cloaking | true | starts hidden until engaged |
| explosion radius | 80 | px AoE (bigger than RoboBomb1's 70) |
| explosion damage | 15 | flat damage each (vs RoboBomb1's 10) |
| knockback | `±7, -7` | survivor knockback |
| warn tint | `16724787` red / `16777215` white | blink colors |

**Formulas**
- Blink: `tint = (fuseTimer>>1 & 1) ? red : white`; detonate at `fuseTimer >= 60`.

**Description vs code**
- No in-game description exists; nothing to compare. (Same "no kill ⇒ no boom" rule — `onDie` returns unless `selfDestruct`.)

---

### Frog1 — `Frog1` (kindNum: none — enemy wave unit, not in unit_desc)
**TL;DR.** A flying jumper that dives at the castle while invulnerable, pokes it for 1 on landing, then fights as an ordinary single-target melee.

**At a glance**
- **Role:** Basic enemy — flying jumper that dives the castle and single-target melees
- **Spawns flying** (`airHeight=55`); invulnerable + stun-immune while airborne
- **Homes the castle**, lands within 40px, deals 1 on touchdown
- **Knock it down:** 2 hits (`airHitCount >= 2`) force an early landing
- **After landing:** ordinary frame-74 single-target melee

**Normal attack (after landing)**
- Ordinary single-target melee, hit on frame 74 (`objAtk={74:1}`).

**Passive / special — flight & dive**
- `doFlying()` finds the castle (`findCastleTarget()` = first alive enemy with `isCastle`) and homes toward it at `moveSpd`.
- Within `landDistance (40)` it calls `startLanding()` and descends over `landingDuration (12)` ticks; on touchdown, if `landedNearCastle`, deals **1** flat damage to the castle (`doDamage(castle,1)`), then drops into normal idle/melee.
- **Airborne invulnerability:** the `health` setter ignores writes while `flying || landingTimer > 0`.
- **Stun-immune** while airborne (`stun()` no-ops).
- **Knockdown:** `onHitted()` increments `airHitCount`; once `airHitCount >= 2` it is forced to land.

**Key values**
| variable | value | meaning |
|---|---|---|
| airHeight (start) | 55 | spawn altitude |
| landDistance | 40 | px from castle at which it starts to land |
| landingDuration | 12 | ticks of descent animation |
| airFrames | `QK(0,12)` | in-air anim loop |
| airHitCount to drop | 2 | hits needed to force it down |
| castle landing damage | 1 | flat dmg on touchdown if near castle |
| objAtk | `{74:1}` | post-landing melee hit frame |

**Formulas**
- Descent: `airHeight = startAirHeight*(1 - t)` where `t = 1 - landingTimer/landingDuration`.

**Description vs code**
- No in-game description exists; nothing to compare. (Only ranged/AoE that registers `onHitted` twice can drop it before it reaches the castle.)

---

### Frog2 — `Frog2` (kindNum: none — enemy wave unit, not in unit_desc)
**TL;DR.** The toad upgrade — flies higher, is harder to knock down, and lands a 5-target AoE swipe with knockback instead of a single-target poke.

**At a glance**
- **Role:** Basic enemy — flying jumper with an AoE ground attack (the "toad" upgrade)
- **Spawns higher** (`airHeight=88` vs 55); invulnerable + stun-immune while airborne
- **Tougher to drop:** 3 hits (`airHitCount >= 3`) vs Frog1's 2
- **Touchdown** still deals 1 to the castle
- **AoE melee:** up to 5 ground enemies in radius 35, 1 dmg each + knockback (hit frame 86)

**Normal attack — AoE swipe (frame 86)**
- `attackMain()` targets a point `35*direction` in front, gathers up to **5** ground enemies within radius **35** via `getEnemiesWithPos` (excludes air units), deals **1** flat damage each and `blow(3*direction, -3.5)` to survivors. Hit fires on frame 86 (`objAtk={86:1}`).

**Passive / special — flight & dive**
- Same fly-to-castle behavior as Frog1 (homes castle, lands within 40px over 12 ticks, deals **1** on touchdown).
- **Flies higher** (`airHeight=88` vs 55) and **tougher to drop** — `onHitted()` needs `airHitCount >= 3` (vs 2).
- Same airborne invulnerability + stun-immunity as Frog1.

**Key values**
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

**Formulas**
- Same descent curve as Frog1: `airHeight = startAirHeight*(1 - t)`.

**Description vs code**
- No in-game description exists; nothing to compare. (vs Frog1: higher spawn, +1 hit to knock down, and a 5-target/35-radius AoE swipe with knockback — Frog1 is single-target.)

---

### Castle (base) — `BaseCastle` (`QQ`) — the player's structure
**TL;DR.** The defended HP structure that also auto-fires at enemies — totally CC-immune, immovable, and slowly self-heals.

**At a glance**
- **Role:** Castle (defended HP structure that also auto-fires)
- **Immovable** (`isImmovable=true`) and **immune to every status/CC**
- **Passive regen:** 0.5% max HP every 450 ticks (~7.5s) when not full
- **9-stage "on fire" visual** as HP drops in 10% steps
- Castle0/1/2 all extend this `QQ` base

**Normal attack**
- `doIdle()` finds the nearest enemy and attacks when in range; `numShot` (base 1) raised by upgrades.

**Passive / special**
- **Regen:** `execute()` increments `regenTimer`; every `REGEN_INTERVAL (450)` ticks it `heal(0.5, null, true)` ⇒ **0.5% of max HP** if not full.
- **Total CC-immunity:** `stun/knockBack/onHitted/addDotDamage/shock/freeze/curse/silence/poison/blow/binding` are all no-op overrides; `updateCrowdControl()` only decrements shield counters and returns false.
- **Damage-fire visual:** escalates through **9 levels** as HP drops in 10% steps (`updateDamageFire`: ≤10%→level 9 … ≤90%→level 1), adding/scaling fire at fixed `FIRE_POSITIONS`.
- **Clickable:** `onPointerDown` toggles the attack-range circle and shows the health bar for 225 ticks.

**Key values**
| variable | value | meaning |
|---|---|---|
| numShot (base) | 1 | shots per attack (raised by upgrades) |
| hpRegenPerSec | 0.001 | declared; effective regen below |
| REGEN_INTERVAL | 450 | ticks between regen ticks (~7.5s @1×) |
| regen heal | 0.5 (percent) | 0.5% of max HP each interval |
| damage-fire levels | 9 | fire stages at 10% HP increments |
| health-bar show time | 225 | ticks the bar stays after a click |

**Formulas**
- Regen `= maxHp*0.01*0.5` per 450 ticks.
- Player upgrades feed in via setters: `setPlayerNumShot(t) ⇒ numShot=1+t`; `setPlayerNumBounce(t) ⇒ numBounce=t`; `setPlayerAtkRange(t) ⇒ atkRange=baseAtkRange+t`; `setPlayerAtkDuration(t) ⇒ atkDuration=1e4/(baseAtkDuration+t)`.

**Description vs code**
- No unit description exists. The code matches the upgrade-key intent: `CASTLE_NAME_1 "Castle Durability"`, `_2 "Castle Range"`, `_3 "Castle Atk Speed"`, `_4 "Multi-Shot"`, `_5 "Bounce Shot"`. Total CC-immunity and immovability are the defining structural traits; HP only changes from incoming damage and the slow 0.5%/450-tick self-heal.

---

### Castle0 — `Castle0` (kindNum: none — player castle, not in unit_desc)
**TL;DR.** The starting fixed-loadout ranged tower — the only castle that hard-codes a 3-shot fire instead of relying on the player's Multi-Shot upgrade.

**At a glance**
- **Role:** Castle (the starting / fixed-loadout castle, RANGE)
- **Stationary** (`moveSpd=0`) ranged tower firing `SpeedArrow2`
- **Unique:** hard-codes `numShot=3` in `initializeData` (Castle1/2 leave it at base 1)
- **Fractional multi-shot:** extra shots beyond the integer count rolled by chance
- Hit/fire frame 23

**Normal attack — fractional multi-shot**
- Pulls `ceil(numShot)` attackable enemies; for each successive target rolls `random.chance(s)` with `s` starting at `numShot` and decrementing by 1 — e.g. `numShot=3.4` fires at targets 1/2/3 for sure and the 4th with 40% chance.
- `generateWeapon` spawns the arrow from a point 35px toward the target, carrying `bounceCount = numBounce`. Hit frame 23 (`objAtk={23:1}`).

**Passive / special**
- Inherits all `BaseCastle` traits (CC-immunity, immovable, regen, damage-fire).

**Key values**
| variable | value | meaning |
|---|---|---|
| numShot | 3 | hard-coded shot count (unique to Castle0) |
| moveSpd | 0 | immobile |
| radius / hitHeight | 22 / 67 | collision |
| weaponClass | `SpeedArrow2` | projectile fired |
| objAtk | `{23:1}` | hit/fire frame |
| numBlock | 0 | blocks no enemies |

**Formulas**
- Multi-shot: target `e` fired iff `random.chance(numShot - e)`.
- Weapon offset: `x+35*cos(angle), y-25+35*sin(angle)`.

**Description vs code**
- No unit description exists; nothing to compare. (Identical body to Castle1/Castle2 except for the `numShot=3` literal in `initializeData`.)

---

### Castle1 — `Castle1` (kindNum: none — player castle, not in unit_desc)
**TL;DR.** A mid-tier ranged castle identical to Castle0 except its shot count comes from player upgrades, not a built-in literal.

**At a glance**
- **Role:** Castle (RANGE, upgrade-driven shot count)
- **Stationary** ranged tower firing `SpeedArrow2`
- **Keeps base `numShot=1`** — relies on the player's Multi-Shot upgrade (`setPlayerNumShot`)
- Same fractional-multishot / bounce / fire-frame-23 logic as Castle0

**Normal attack**
- Same as Castle0: fractional-`numShot` multishot via `random.chance`, bounce via `numBounce`, fire frame 23 — but `numShot` is **not** set in `initializeData`, so it stays base 1.

**Passive / special**
- Inherits all `BaseCastle` traits (CC-immunity, immovable, regen, damage-fire).

**Key values**
| variable | value | meaning |
|---|---|---|
| numShot | (inherited 1) | not overridden — driven by upgrades |
| moveSpd / radius / hitHeight | 0 / 22 / 67 | same as Castle0 |
| weaponClass | `SpeedArrow2` | projectile |
| objAtk | `{23:1}` | fire frame |

**Formulas**
- Same multishot/bounce/offset formulas as Castle0.

**Description vs code**
- No unit description exists; nothing to compare. (Only delta vs Castle0 is the absence of the `numShot=3` literal.)

---

### Castle2 — `Castle2` (kindNum: none — player castle, not in unit_desc)
**TL;DR.** The top-tier castle skin — byte-for-byte the same firing code as Castle1, differing only in tier/art, with shot count driven by player upgrades.

**At a glance**
- **Role:** Castle (RANGE, top-tier skin, upgrade-driven)
- **Stationary** ranged tower firing `SpeedArrow2`
- **Keeps base `numShot=1`** (raised by player upgrades)
- Mechanically identical to Castle1 — difference is tier/cosmetic only

**Normal attack**
- Same method bodies as Castle1: fractional-`numShot` multishot, `numBounce` bounce, fire frame 23; `die()` re-shows the sprite. `numShot` not set in `initializeData` (stays base 1).

**Passive / special**
- Inherits all `BaseCastle` traits (CC-immunity, immovable, regen, damage-fire).

**Key values**
| variable | value | meaning |
|---|---|---|
| numShot | (inherited 1) | upgrade-driven |
| moveSpd / radius / hitHeight | 0 / 22 / 67 | identical to Castle1 |
| weaponClass | `SpeedArrow2` | projectile |
| objAtk | `{23:1}` | fire frame |

**Formulas**
- Same as Castle0/Castle1.

**Description vs code**
- No unit description exists; nothing to compare. (No mechanical delta from Castle1 in code; difference is tier/cosmetic.)

---

## Raid-boss base — `BaseRaidUnit` (`E2`/`A2`)
The three "King" bosses below all extend `BaseRaidUnit`. Shared framework (verified):
- **Spine-animated** (`spineKey`, `bossScale=1.3` default, per-boss `spineTimeScale`); state→animation mapping; a **weak-point bone** (head) drives flash/tint feedback.
- **Total CC-immunity**, doubly enforced: constructor sets `blowImmune/stunImmune/freezeImmune/knockImmune=true` AND `stun/freeze/curse/silence/binding/poison/shock/knockBack/blow` are no-op overrides. `weight=5`, `bossType=1`.
- **Raid-stun ("groggy") mechanic**: `applyRaidStun(frames)` is a *separate* system from normal CC — it sets `raidStunFrames`, plays the groggy animation, and freezes attacks for the duration (the intended "hit the weak point to stagger the boss" loop).
- **Skill selection** (`pickSkill`): if a queued `arrAttackTypeList` exists it shifts from that; else it walks a per-battle random **`attackOrderList`** sequence; else the first `numForSkillAttack (=2)` attacks are forced to the normal attack (skill 0), after which it rolls against the descending **`skillRatio`** thresholds to pick a skill index. `skill0` = normal attack; `skillN(i)` = skill `i`.
- **Wander AI** between attacks (`wanderEnabled`, `wanderInterval`, bounded by `wanderMin/MaxX/Y` = 100–540 / 200–950), plus `targetSwapChance` (re-roll target on each attack) and `wanderAfterAttackChance`.
- **Outgoing damage** is multiplied by `getRaidBossDamageMultiplier()` from the battle controller (a raid-difficulty scalar). `radialBlow/radialKnockback` push enemies away from an impact point, scaled by per-boss `BLOW_SCALE`.

---

### ScorpionKing — `ScorpionKing` (kindNum: none — raid boss, not in unit_desc)
**TL;DR.** A raid boss that dashes in to slam, then vacuums your team together and drowns them in poison — splash poison, a lingering poison pool, a poison-bullet volley, and a stunning slam.

**At a glance**
- **Role:** Boss (raid) — poison/pull bruiser
- **Spine boss** (`raids/raid1/Scorpion`, `spineTimeScale=.82`, wander enabled)
- **4 moves**, sequenced by `attackOrderList` then `skillRatio=[.78,.55,.3,0]` (2 forced normals)
- **Signature:** pull + poison splash that drops a 1200-tick poison pool
- **Knockback scalar** `BLOW_SCALE=0.7`

**Normal attack — att_01 (dash slam)**
- `startAttackDashTo` the target, then radial AoE at the `target_01` bone — radius **100**, `random.range(1,3)` damage to all in-radius, plus `radialBlow`.

**Skill 1 — att_02 (pull + poison splash)**
- Over the splash window, **pulls** all movable enemies toward the splash center within radius **200** at speed **12**.
- Then once applies a radius-**150** splash: `random.range(1.5,3)` damage + `poison(random 100–150)` to each, a `radialBlow`, and spawns a **lingering poison area** (`ScorpionPoisonArea`, ellipse 112.5×54, **1200**-tick duration, **1 dmg/sec**).

**Skill 2 — att_03 (poison-bullet volley)**
- Dashes to the enemy centroid, then fires up to **7 batches × 16 bullets** (`ScorpionPoisonBullet`, `random.range(1,2)` dmg each, staggered by `delay=floor(n/4)`) from the `tail_ball` bone at random targets.

**Skill 3 — att_04 (impact slam)**
- Radius-**110** impact: `random.range(1,3)` dmg + **stun 240** ticks to each.
- Radius-**200** `radialBlow`.
- On the `baby_att_hit` spine event, a radius-**100** `radialKnockback` (power 6–10, dur 18).
- `escapeSkill()` forces att_04.

**Passive / special**
- Inherits full `BaseRaidUnit` CC-immunity (doubly enforced), `weight=5`, raid-stun "groggy" weak-point system.

**Buffs & debuffs (to enemies)**
- Poison: att_02 splash applies stacks of 100–150; the pool deals 1 dmg/s for 1200t.
- Stun: 240t (att_04 impact).
- Knockback/blow on att_01, att_02, att_04.

**Key values** (all `zt(S2,…)`)
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

**Formulas**
- Pull step `= min(dist, PULL_SPEED*(0.4 + (1 - dist/PULL_RADIUS)))` (closer = stronger pull).
- `radialBlow` impulse `= (min + rand*(max-min)) * BLOW_SCALE`.

**Description vs code**
- No in-game description exists for raid bosses; nothing to compare.

---

### HarpyKing — `HarpyKing` (kindNum: none — raid boss, not in unit_desc)
**TL;DR.** A flying raid boss that only targets air, divebombs squads, slams down tornadoes, and unleashes feather barrages — pure knockback and lingering AoE, no stun.

**At a glance**
- **Role:** Boss (raid) — flying air-only diver / feather-storm caster
- **Spine boss** (`raids/raid1/Harpy`, `spineTimeScale=.84`, wander enabled, `airTargetOnly=true`, `hitHeight=200`)
- **5 attack slots**, `skillRatio=[.75,.55,.35,.15,0]`; `pickSkill()` remaps skill 1 → 0 (extra dashing normal)
- **Signature:** feather barrage (7 bursts × 20 feathers) + lingering tornadoes
- **Knockback scalar** `BLOW_SCALE=0.75`

**Normal attack — att1 (dive)**
- Dashes to a random alive *corp* (squad) center; during the hover window tracks that corp (`ATT1_HOVER_SPEED 3` from frame 20).
- On each hit event deals up to **7** hits (`ATT1_HITS_PER_EVENT`) of `random.range(1,2)` within radius **100**.

**Skill — att2 (slam + tornadoes)**
- `blow`s every enemy within 300×200, then `spawnSlamTornadoes()` drops **1 tornado** (2 after `TORNADO_TWO_AFTER_FRAMES=5400` battle-frames).
- `HarpyTornado`: ellipse **70×56**, **1200**-tick duration, deals **`TORNADO_DAMAGE_PERCENT=0.5`** (percent-style tornado damage); follows an aggro/random corp center.

**Skill — att4 (cone knockback)**
- Forward cone (radius **300**, half-angle **π/4**): `random.range(1,2)` dmg + `knockBack(power 8–14, dur 12)` to non-immovable enemies in the cone. Facing locked during it.

**Skill — att5 (feather barrage)**
- During the att5 anim fires **7 bursts** (at spine frames 28–40) of **20 feathers** each (`HarpyFeather`, `random.range(1.2,2.5)` dmg) radiating from the `shout` bone at corp/aggro targets.
- First `FEATHER_AGGRO_BURSTS=3` bursts prefer the highest-aggro corp.
- `escapeSkill()` ⇒ skill 4.

**Passive / special**
- Inherits full `BaseRaidUnit` CC-immunity, `weight=5`, raid-stun system.
- `airTargetOnly` + `hitHeight=200` mark it as a true aerial boss; the `pickSkill` 1→0 remap makes slot 1 effectively an extra dashing normal.

**Buffs & debuffs (to enemies)**
- Knockback: att2 slam `blow` and att4 cone (power 8–14, dur 12).
- DoT: lingering tornadoes (0.5 percent-style, 1200t). No stun/freeze.

**Key values** (`zt(T2,…)`)
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

**Formulas**
- Cone test: `dirToEnemy · facing ≥ cos(π/4)`.
- Tornado uses `setMoveTargetProvider` to chase a corp center.

**Description vs code**
- No in-game description exists for raid bosses; nothing to compare.

---

### GolemKing — `GolemKing` (kindNum: none — raid boss, not in unit_desc)
**TL;DR.** A teleporting heavy slammer that double-taps its normal, drops pillar and radial slams, charges across the field, then vanishes underground and re-emerges with a massive 480-radius slam.

**At a glance**
- **Role:** Boss (raid) — teleporting heavy slammer
- **Spine boss** (`raids/raid1/Golem`, `spineTimeScale=.8`, wander enabled, `hitHeight=180`, weak point = `Head` bone, offset −25)
- **6 skill slots**, `skillRatio=[.78,.6,.42,.26,.12,0]` (2 forced normals)
- **Signature:** teleport → relocate → emerge-slam (radius 480, the biggest hit in its kit)
- **Heavily damped knockback** `BLOW_SCALE = 0.75*0.6 = 0.45`

**Normal attack — att1 (double-tick slam)**
- AoE at the `R_Arm_01` bone, radius **200**, up to **80** targets, `random.range(1,2.5)` dmg + per-target knockback.
- Queues a **second tick** `ATT1_SECOND_TICK_DELAY=10` ticks later that repeats the slam — so the "normal" attack double-hits.

**Skill — att3 (radial slam)**
- `radialBlow` at self, radius **300**, blow power 3–12.

**Skill — att5 (pillar barrage)**
- For each of **9** `stone_pillar_0X` bones, a radius-**70** blast (up to **10** targets, `random.range(1.4,2.8)` dmg + knockback).

**Skill — att2 (charge)**
- Locks facing toward aggro/centroid and **slides forward** at `ATT2_CHARGE_SPEED=3` for `ATT2_DURATION_FRAMES=120`, doing a radius-**80** hit (≤5 targets, `random.range(1.5,2.5)`) every `ATT2_TICK_INTERVAL=3` frames at an offset point.

**Skill — teleport (skill `SKILL_TELEPORT=5`)**
- Plays `teleport_out`, becomes `attackable=false` + `isUntagetable`, freezes player units in place (`freezeAlliesInPlace`).
- Stays underground `TELEPORT_UNDERGROUND_FRAMES=120` ticks, **relocates randomly** within wander bounds, plays `teleport_in`.
- **Emerges with a huge slam:** `emergeRadialBlow` radius **480**, power **15.2–24.3** (vh 10.6–18.2) — the biggest hit in its kit.
- `escapeSkill()` ⇒ teleport.

**Passive / special**
- Inherits full `BaseRaidUnit` CC-immunity, `weight=5`, raid-stun weak-point system.
- During teleport it is `attackable=false` + untargetable for the 120 underground ticks, and freezes player units' positions.

**Buffs & debuffs (to enemies)**
- Knockback on nearly every hit; teleport freezes player units' positions. No stun/poison.

**Key values** (`zt(O2,…)`)
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

**Formulas**
- `BLOW_SCALE` doubly damped (0.75×0.6) so its knockbacks are short despite large power numbers.
- Emergence uses the same `radialBlow` with the EMERGE_* constants.

**Description vs code**
- No in-game description exists for raid bosses; nothing to compare.
