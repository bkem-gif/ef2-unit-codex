# EF2 unit mechanics — Part 4 (12 classes)

Source: `runtime/bundles/mounted/1.11.42/assets/index.js`. Classes registered with `Kt(<var>,"<Name>")`, base class `qQ`. Damage helpers: `doMeleeAttack(target, mult=1)` and `doRangeAttack(target, n=0)` (2nd arg = damage multiplier / extra-shot index). Buff signature `(id, value, durationTicks[, refresh])`. Times are game ticks (~60/s at 1×).

---

### Orc Fighter — `OrcFighter1` (kindNum: 19 · Ⅱ 44)
**TL;DR.** Melee bruiser that hits twice per swing; its skill is a heavy blow that knocks the target backward.

**At a glance**
- **Role:** Melee DPS
- **Attack:** melee double-hit (two hit-frames per swing)
- **Skill:** heavy strike + knockback
- **Stats:** 150 HP, ATK 3, DEF 10, moveSpd 2.6, atkDuration 200, melee range 8

**In-game text**
- Normal: "Attacks enemies with a rapid double melee strike." (Ⅱ: "Attacks enemies with a melee double-hit.")
- Skill: "Delivers a heavy strike that deals massive damage and knocks enemies back." (Ⅱ: "Strikes with tremendous force, dealing even greater damage and sending enemies flying farther back.")

**Normal attack**
- Double-hit: `objAtk={51:1,60:1}` fires the hit on two anim frames (51 and 60), each at 1×.

**Skill — heavy strike + knockback**
- `doMeleeAttack(target, ×2)` (**Ⅱ ×2.5**) on frames `objSkill={97:1,105:1}`.
- Then `target.blow(±k, k)` with `k = 2` (**Ⅱ 3**); sign is `+` if target is to the right, `−` if left.
- Evolved gated by `this.evolStage>=1` inside `skillMain` (no cached flag).

**Base → Ⅱ**
- Skill damage ×2 → ×2.5; knockback k 2 → 3 ("flying farther back").

**Key values**
| | base | Ⅱ |
|---|---|---|
| skill damage mult | ×2 | ×2.5 |
| knockback k | 2 | 3 |
| baseMaxHp | 150 | 150 |
| atkDmg / def | 3 / 10 | 3 / 10 |
| moveSpd | 2.6 | 2.6 |
| atkDuration | 200 | 200 |
| atkRange | 8 | 8 |

**Formulas**
- Skill dmg = atk × 2 (base) / × 2.5 (Ⅱ). Normal = 2× `objAtk` frames at 1× each.

**✓ Matches description** — double-hit normal + heavy-damage knockback skill; evolved raises mult (2→2.5) and knockback (2→3).

---

### Orc Hammerman — `OrcHammer1` (kindNum: 24 · Ⅱ 49)
**TL;DR.** Melee hammer unit whose skill summons a short-lived ice decoy to soak hits; evolved adds a small forward AoE to its normal swing.

**At a glance**
- **Role:** Melee DPS / summoner (decoy)
- **Attack:** melee hammer; **Ⅱ** adds a 1-target forward AoE
- **Skill:** summons an `OrcIcePhantom1` ice decoy (aggro magnet, no attack)
- **Decoy lifetime:** 180t (~3.0s) → **220t (~3.7s)** at Ⅱ

**In-game text**
- Normal: "Attacks enemies in melee with a hammer." (Ⅱ: "Swings a hammer to deal AoE damage to nearby enemies.")
- Skill: "Summons an ice decoy to draw enemy attacks in your place." (Ⅱ: "Summons an ice clone for a longer duration to take hits in your place.")

**Normal attack**
- Base: `doMeleeAttack(target, 1)` on `objAtk={58:1}`.
- **Ⅱ only:** also sweeps for up to **1** extra ground enemy in a 30-unit box centered 30 units ahead (`n = x + direction*30`, radius² = 30² = 900) and hits it with `doMeleeAttack(a, 0.7)` — this is the evolved "AoE".

**Skill — summon ice decoy**
- `summonPhantom(dur)` spawns `OrcIcePhantom1` via `getUnitSync` on frame `objSkill={99:1}`.
- Copies source VO at 0.3 scale (`setData(sourceVo, .3)`), placed at a random angle 40 units away.
- `summonDuration = 180` (**Ⅱ 220**). Phantom just stands and `die()`s when its `summonTimer` hits 0 — draws aggro, never attacks.

**Passive / special**
- Caches `this.sourceVo` in `setData` to clone into the phantom; `this.evolved = this.evolStage>=1`.

**Base → Ⅱ**
- Normal gains a 1-target forward AoE at 0.7×; phantom duration 180t → 220t.

**Key values**
| | base | Ⅱ |
|---|---|---|
| evolved AoE range / radius | — | 30 / 30 (radius²=900) |
| evolved AoE maxTargets | — | 1 |
| evolved AoE damage mult | — | 0.7 |
| phantom duration | 180t (~3.0s) | 220t (~3.7s) |
| phantom setData scale | 0.3 | 0.3 |
| phantom spawn radius | 40 | 40 |
| objAtk / objSkill frame | 58 / 99 | 58 / 99 |

**Formulas**
- Evolved secondary hit dmg = atk × 0.7.

**✓ Matches description** — evolved "AoE normal" = exactly one extra forward ground hit at 0.7×; evolved decoy lasts longer (180→220t). The decoy only soaks aggro then expires; it never attacks.

---

### Orc Hunter — `OrcHunter1` (kindNum: 20 · Ⅱ 45)
**TL;DR.** Melee assassin that teleports to the farthest forward enemy, hits hard, freezes it, and buffs its own dodge against ranged attacks.

**At a glance**
- **Role:** Melee assassin (teleport + freeze + self-evade)
- **Attack:** plain melee strike
- **Skill:** teleport to farthest forward enemy → heavy hit → freeze → self ranged-evade buff
- **Stats:** 150 HP, ATK 3, DEF 10, moveSpd 2.6, atkDuration 200, melee range 8

**In-game text**
- Normal: "Attacks enemies with a melee strike." (Ⅱ: "Attacks enemies with a basic melee strike.")
- Skill: "Teleports to the farthest enemy, delivers a heavy strike, freezes the target, and grants itself a ranged evasion buff." (Ⅱ: "Teleports to the farthest enemy, delivering a more powerful strike and freezing them for longer. Grants yourself a ranged evasion buff.")

**Skill — teleport strike (`objSkill={103:1}`)**
- Scans `enemyList` for the ground, non-air, targetable enemy with the **largest +x offset** (farthest ahead) within |dx|≤200, |dy|≤200 AND dx²+dy²<40000.
- Teleports beside it (snaps `this.x` to `target.x ∓ hitWidths`), then `doDamage(target, ×2)` (**Ⅱ ×3**).
- `target.freeze(30)` (**Ⅱ 50**).
- Self-buffs `addRangeEvadeChanceBuff(id=1, 0.6, 180)` + the `OrcHunterEvadeBuff` visual for 180t.

**Buffs & debuffs**
- Self ranged-evade: +60% (value 0.6, additive), 180t (~3s) — id 1
- Target freeze: 30t (**Ⅱ 50t**)

**Base → Ⅱ**
- Skill dmg ×2 → ×3; freeze 30t → 50t.

**Key values**
| | base | Ⅱ |
|---|---|---|
| skill damage mult | ×2 | ×3 |
| freeze duration | 30t | 50t |
| rangeEvade value | 0.6 (+60%) | 0.6 |
| rangeEvade duration | 180t (~3s) | 180t |
| search box | |dx|,|dy|≤200; dist²<40000 | same |
| baseMaxHp / atkDmg / def | 150 / 3 / 10 | same |
| moveSpd / atkDuration / atkRange | 2.6 / 200 / 8 | same |

**Formulas**
- `rangeEvadeChange = orgRangeEvadeChange + 0.6` (additive ⇒ +60% chance to dodge ranged hits) for 180t. Skill dmg = atk × 2 / × 3.

**✓ Matches description** — evolved bumps dmg (2→3) and freeze (30→50). Note "farthest enemy" is implemented as farthest **in +x (forward) direction within a 200/√40000 box**, not globally farthest.

---

### Frost Mage / Ice Mage Ⅱ — `OrcIceMage1` (kindNum: 21 · Ⅱ 46)
**TL;DR.** Ranged ice mage; evolved fires faster with a chance for an extra projectile, and its freeze-bolt skill can hit a second enemy.

**At a glance**
- **Role:** Ranged mage (ice)
- **Attack:** fires `OrcIceMageFire1` ice projectiles
- **Skill:** enhanced freeze bolt (`OrcIceMageFireSkill1`); **Ⅱ** adds a 50%-chance second bolt
- **Ⅱ normal:** numShot 1 → 1.3 (~30% chance of an extra projectile)

**In-game text**
- Normal: "Fires ice magic projectiles to attack enemies from a distance." (Ⅱ: "Fires enhanced ice magic projectiles at an increased fire rate, with a chance to strike additional targets.")
- Skill: "Fires enhanced freezing projectiles that deal massive damage to enemies." (Ⅱ: "Fires an enhanced freezing projectile that deals heavy damage to enemies.")

**Normal attack**
- Ranged (`unitType=RANGE`, `weaponClass=OrcIceMageFire1`), fires on `objAtk={42:1}`.
- `setData` sets `numShot = 1` (**Ⅱ 1.3**) — the fractional count means ~30% chance of an extra projectile per attack, resolved by base shot logic.

**Skill — freeze bolt (`objSkill={68:1}`)**
- Fires the enhanced `OrcIceMageFireSkill1` at the target.
- **Ⅱ only:** scans `getAttackableEnemyList(2)` and, for the first non-target enemy, fires a second skill projectile with `random.chance(.5)` (50%).

**Base → Ⅱ**
- numShot 1 → 1.3; skill gains a 50%-chance second freeze bolt at the nearest other enemy.

**Key values**
| | base | Ⅱ |
|---|---|---|
| numShot | 1 | 1.3 (~30% extra) |
| evolved 2nd-skill chance | — | 0.5 |
| objAtk / objSkill frame | 42 / 68 | 42 / 68 |
| weaponClass (normal) | OrcIceMageFire1 | same |
| weaponClass (skill) | OrcIceMageFireSkill1 | same |

**Formulas**
- Evolved extra-shot expectation ≈ 0.3 projectiles/attack (numShot 1.3). Evolved skill expected bolts = 1 + 0.5 = 1.5.

**Notes**
- Freeze/CC is carried by the `OrcIceMage...` weapon objects, not this class — no buff/debuff applied directly here.

**✓ Matches description** — "increased fire rate / additional targets" = numShot 1→1.3; evolved skill's "additional" bolt = one 50%-chance second projectile at the nearest other enemy.

---

### Orc Spearman — `OrcSpearMan1` (kindNum: none — basic ranged enemy)
**TL;DR.** A fast, low-HP enemy spearman that just throws spears — no skill at all.

**At a glance**
- **Role:** Basic enemy (ranged, no skill)
- **Attack:** throws `OrcSpearmanSpear1` spears (very fast cadence)
- **Stats:** 100 HP, ATK 10, DEF 10, moveSpd 1.6, atkDuration 20, range 150
- **No skill:** `hasSkill` unset, no `skillMain`/`objSkill`/`attackMain` override

**How it works**
- Pure ranged auto-attacker. `unitType=RANGE`, `weaponClass=OrcSpearmanSpear1`, throws a spear on `objAtk={51:1}`, `firePoint=(3,-25)`. Uses base attack only.

**Key values**
| variable | value | meaning |
|---|---|---|
| baseMaxHp | 100 | HP |
| atkDmg / def | 10 / 10 | attack / defense |
| moveSpd | 1.6 | move speed |
| atkDuration | 20 | ticks between shots (~3 shots/s) |
| atkRange | 150 | ranged reach |
| weaponClass | OrcSpearmanSpear1 | spear projectile |

**Formulas**
- atkDuration = 20 ⇒ ~3 shots/s at 1×.

**⚠️ Description vs code**
- No localized description to compare (kindNum absent from `unit_desc.json` 1–96). The playable Orc-faction analog at this slot is the melee line; this is an internal/enemy spearman minion. Documented from code only: a fast, low-HP ranged spear-thrower with no skill. Stated explicitly rather than forcing a wrong kindNum.

---

### Orc Wing — `OrcWing1` (kindNum: 22 · Ⅱ 47)
**TL;DR.** Airborne ranged attacker that fires energy balls; its skill is the same projectile cranked up to a higher power level.

**At a glance**
- **Role:** Ranged DPS (flyer)
- **Attack:** fires `OrcWingBall1` energy balls from the air (`airHeight=75`)
- **Skill:** same projectile at power level 2 (enhanced damage)
- **Evolved difference:** render size only (0.85 → 0.95)

**In-game text**
- Normal: "Fires energy projectiles from the air to attack enemies at range." (Ⅱ: "Fires energy projectiles from the air for ranged attacks.")
- Skill: "Fires enhanced energy projectiles that deal massive damage." (Ⅱ: "Fires an enhanced energy projectile that deals heavy damage.")

**Normal attack**
- Air unit (`isAir=true`, `airHeight=75`), ranged, `weaponClass=OrcWingBall1`, hit on `objAtk={59:1}`, `firePoint=(18, 5−75)`.

**Skill — enhanced energy ball (`objSkill={97:1}`)**
- `generateWeapon(target, OrcWingBall1, 2)` — same projectile, 3rd arg `2` boosts power/damage. One enhanced ball.

**Base → Ⅱ**
- `normalSize` 0.85 → `evolSize` 0.95 (render scale only); skill is mechanically identical base/Ⅱ.

**Key values**
| | base | Ⅱ |
|---|---|---|
| skill power arg | 2 | 2 |
| objAtk / objSkill frame | 59 / 97 | 59 / 97 |
| airHeight | 75 | 75 |
| firePoint | (18, 5−75) | same |
| weaponClass | OrcWingBall1 | same |
| render scale | 0.85 | 0.95 |

**Formulas**
- Skill projectile = normal `OrcWingBall1` at power level 2 (exact multiplier lives in the weapon class).

**✓ Matches description** — skill is the same projectile at power 2; no mechanical base/evolved difference beyond size.

---

### Orc Axeman — `OrcAxe1` (kindNum: 23 · Ⅱ 48)
**TL;DR.** Melee axe fighter with a forward cleave on its normal hit, and a skill that throws axes to hit multiple extra enemies — including airborne ones.

**At a glance**
- **Role:** Melee DPS (forward AoE + thrown axes)
- **Attack:** melee hit + forward AoE cleave (up to 2 → **3** ground enemies)
- **Skill:** melee hit + throw 3 → **5** axes (`OrcAxeBall1`), can hit air
- **Evolved:** wider AoE box (30→35) and stronger secondary hits (0.5→0.7)

**In-game text**
- Normal: "Strikes with an axe in melee and deals AoE damage to enemies ahead." (Ⅱ: "Strikes with an axe in melee, dealing wider AoE damage to enemies ahead.")
- Skill: "After a melee attack, throws an axe to strike additional enemies. Can also hit airborne enemies." (Ⅱ: "After a melee attack, hurls more axes to strike additional enemies. Can also hit airborne targets.")

**Normal attack**
- `doMeleeAttack(target, 1)` on `objAtk={78:1}`, then a forward AoE sweep.
- Box centered `direction*range` ahead (`range = 30`, **Ⅱ 35**; radius² = range²), hitting up to 2 (**Ⅱ 3**) extra **ground** enemies at `doMeleeAttack(a, 0.5)` (**Ⅱ 0.7**). Explicitly skips `a.isAir`.

**Skill — axe throw (`objSkill={133:1,135:1,137:1}`, three throw frames)**
- First a melee hit on the target, then `getAttackableEnemyList(t+1, false)` (the `false` allows **air** targets).
- Throws `OrcAxeBall1` at up to `t = 3` (**Ⅱ 5**) non-target enemies via `generateWeapon`.

**Base → Ⅱ**
- Normal AoE range/radius 30→35, targets 2→3, mult 0.5→0.7; skill throws 3→5.

**Key values**
| | base | Ⅱ |
|---|---|---|
| normal AoE range / radius | 30 / 30 | 35 / 35 |
| normal AoE maxTargets | 2 | 3 |
| normal AoE damage mult | 0.5 | 0.7 |
| skill throws | 3 | 5 |
| objAtk frame | 78 | 78 |
| skill target query | `getAttackableEnemyList(t+1,false)` (incl. air) | same |

**Formulas**
- Normal forward AoE dmg = atk × 0.5 (base) / × 0.7 (Ⅱ), up to 2/3 extra ground targets. Skill = 1 melee + N thrown axes (3/5).

**✓ Matches description** — "wider AoE" (Ⅱ) = range/radius 30→35, targets 2→3, mult 0.5→0.7. "Hit airborne enemies" = skill's `getAttackableEnemyList(...,false)` includes air units (normal AoE skips air).

---

### Drums of the Battlefield — `BigDrumer1` (kindNum: 69 · Ⅱ 78)
**TL;DR.** Support drummer — pulses an attack-speed + move-speed buff to the whole team every ~8s; deals no damage.

**At a glance**
- **Role:** Support buffer (no attack)
- **Cadence:** every 500t (~8.3s); first pulse randomized so drummers desync
- **Buffs:** +120% atk-speed & +120% move-speed → **+130%** at Ⅱ
- **Targets:** ≤30 nearest allies (= your whole team)

**In-game text**
- Normal: "Supports allies by beating a drum instead of attacking." (Ⅱ: same.)
- Skill: "Temporarily increases ATK, attack speed, and movement speed for all allied heroes." (Ⅱ: "Further boosts ATK, attack speed, and movement speed of all allied heroes for a limited time.")

**Skill — the drum beat (every 500t)**
- Doesn't attack. `attackMain` is gated by `skillCoolDown` (decremented in `execute`, reset to 500): gathers all alive `allyList`, sorts by squared distance, and buffs the nearest `min(SKILL_MAX_TARGETS=30, n)` allies.
- Both buffs use id 8001, so re-beats refresh rather than stack. Buff strength `s = 1.2` (**Ⅱ 1.3**), duration `dur = 350t` (**Ⅱ 400t**).
- First cooldown is randomized `500*random.next()` so instances desync (constructor seeds `skillCoolDown=300`, overwritten in `setData`). Drum-beat frame `objAtk={48:1}`.

**Buffs & debuffs**
- Attack speed: +120% (Ⅱ +130%), 350t (Ⅱ 400t), ≤30 allies — id 8001
- Move speed: +120% (Ⅱ +130%), 350t (Ⅱ 400t), ≤30 allies — id 8001

**Base → Ⅱ**
- Buff strength +120% → +130%; duration 350t → 400t.

**Key values**
| | base | Ⅱ |
|---|---|---|
| buff strength | +120% (value 1.2) | +130% (value 1.3) |
| buff duration | 350t (~5.8s) | 400t (~6.7s) |
| pulse cooldown | 500t (~8.3s) | 500t |
| max targets | 30 | 30 |
| BUFF_ID | 8001 | 8001 |
| objAtk frame | 48 | 48 |

**Formulas**
- `atkSpd = orgAtkSpd × (1 + value)` → value 1.2 = +120%, value 1.3 = +130%. Same for move speed.

**⚠️ Description vs code**
- Blurb claims an **ATK** boost, but the code calls only `addAttackSpeedBuff` + `addMoveSpeedBuff` — no `addAttackDamageBuff`, so raw ATK is **not** buffed. Confirmed by reading the full `attackMain` (two buff calls only).

**Notes**
- Multiple drummers share id 8001 ⇒ per the max-per-id aggregation rule they don't stack strength, only extend uptime via the `refresh` flag. Static fields verified in bundle: `zt(u0,"BUFF_ID",8001), zt(u0,"SKILL_MAX_TARGETS",30)`.

---

### Wolf Rider — `OrcWolfRider1` (kindNum: 25 · Ⅱ 50)
**TL;DR.** Hybrid melee/summoner/buffer — cleaves nearby enemies, summons ice wolves, periodically taunts, and grants nearby allies an attack/move-speed buff.

**At a glance**
- **Role:** Summoner + melee DPS + buffer
- **Attack:** melee hit + forward AoE (up to 4 → **6** enemies)
- **Skill:** summon Ice Wolf (max 2 → **3**) + ally speed buff; taunt every 3rd use
- **Ally buff:** +25% atk/move-speed → **+40%** (radius 70 → **90**)

**In-game text**
- Normal: "Deals AoE damage to nearby enemies along with a melee attack." (Ⅱ: same.)
- Skill: "Summons a wolf and grants nearby allies a movement speed and attack speed buff. Activates Taunt after a set number of uses." (Ⅱ: "Increases the number of wolves that can be summoned and strengthens the movement speed and attack speed buffs granted to nearby allies. Activates Taunt after a set number of uses.")

**Normal attack**
- `doMeleeAttack(target)` then a forward AoE — box centered `i` units ahead (`i = 40`, **Ⅱ 50**; radius² = i²) hitting up to `e = 4` (**Ⅱ 6**) other enemies at `doDamage(o, 0.65)` (**Ⅱ 0.8**).

**Skill — summon + buff (`objSkill={58:1}`)**
- Increments `skillUseCount`; if current wolf count < `MAX_WOLVES` (2, **Ⅱ 3**), summons `WOLF_KIND_NUM=1003` ("Ice Wolf") via `summonUnitSync`, duration `WOLF_DURATION` (1200, **Ⅱ 1500**), wolf level = `level + enhance + WOLF_LEVEL_BONUS` (6, **Ⅱ 10**), scale `WOLF_SCALE` (1.05, **Ⅱ 1.15**), with `detectRange` set.
- **Every 3rd use** (`skillUseCount%3==0`): `taunt(80)` (80-tick taunt; fires on uses 3, 6, 9…).
- Then `buffNearbyAllies()`.

**Buffs & debuffs**
- Ally atk-speed: +25% (Ⅱ +40%, value 0.25/0.4), 100t (Ⅱ 120t), allies within radius 70 (Ⅱ 90) — id = kindNum (25/50)
- Ally move-speed: +25% (Ⅱ +40%), 100t (Ⅱ 120t), same radius — id = kindNum (25/50)
- Taunt: 80t, every 3rd skill use

**Passive / special**
- `setData` rolls starting mana `250 + 150·random`.
- When `battleController instanceof mii` (hero/own-side context) the wolf gets a smaller `detectRange` (150) and, if on the friendly hero list, full hero treatment (`applyToHero`, hp=maxHp).

**Base → Ⅱ**
- Wolves: max 2→3, duration 1200→1500, level bonus 6→10, scale 1.05→1.15. Normal AoE: range 40→50, targets 4→6, mult 0.65→0.8. Ally buff: value 0.25→0.4, radius 70→90, duration 100→120.

**Key values**
| | base | Ⅱ |
|---|---|---|
| WOLF_KIND_NUM | 1003 (Ice Wolf) | 1003 |
| WOLF_DURATION | 1200t | 1500t |
| MAX_WOLVES | 2 | 3 |
| WOLF_SCALE | 1.05 | 1.15 |
| WOLF_LEVEL_BONUS | 6 | 10 |
| normal AoE range i | 40 | 50 |
| normal AoE maxTargets e | 4 | 6 |
| normal AoE damage mult | 0.65 | 0.8 |
| ally-buff radius | 70 | 90 |
| ally-buff value s | 0.25 (+25%) | 0.4 (+40%) |
| ally-buff duration e | 100t | 120t |
| taunt | every 3rd skill, `taunt(80)` | same |
| starting mana | 250 + 150·rand | same |

**Formulas**
- Ally `atkSpd = orgAtkSpd × (1+0.25)` ⇒ +25% / `×(1+0.4)` ⇒ +40%; same for moveSpd. Normal AoE dmg = atk × 0.65 / × 0.8.
- Both ally buffs keyed by `this.kindNum` (25/50) ⇒ same kindNum doesn't stack, max kept.

**✓ Matches description** — "increases number of wolves" = MAX_WOLVES 2→3 + longer duration; "strengthens buffs" = value/radius/duration up plus stronger wolves (level +6→+10, scale 1.05→1.15). Summoned "wolf" is internally kindNum 1003 = "Ice Wolf".

---

### Sylphid — `Sylphid1` (kindNum: 90 · Ⅱ 94)
**TL;DR.** Ranged shuriken thrower that ramps its own attack speed with every hit; at max stacks it enters Rage and spews extra shurikens, and its skill rains divergent tornados.

**At a glance**
- **Role:** Ranged DPS (shuriken stacker / rage)
- **Attack:** bouncing shurikens (`numBounce=3`); each hit +4% atk-speed (up to 25 stacks = +100%)
- **Rage:** at 25 stacks → 180t (~3s) window firing bonus shurikens (`doRangeAttack(target,4)`)
- **Skill:** `SylphidTornado1` volley at divergent targets; **Ⅱ** adds a 3rd tornado at 1.2× power

**In-game text**
- Normal: "Fires shurikens in rapid succession, and each hit gradually increases attack speed.\nRage: When attack speed reaches its maximum, additional shurikens are fired with each normal attack."
- Skill: "Fire tornados in succession to deal damage to enemies."

**Normal attack**
- `doRangeAttack(target)`; **while raging** (`rageTimer>0`) also `doRangeAttack(target, 4)` (extra shurikens). Shurikens bounce up to 3× (`numBounce=3`).
- On each shuriken landing, `onShurikenHit` (suppressed during rage) bumps `atkStack` up to `ATKSPD_MAX_STACK=25`, sets `stackResetTimer = STACK_BUFF_DUR = 600`, and applies `addAttackSpeedBuff(id=220, atkStack*0.04, 600, refresh)`.

**Passive / special — stack ramp & Rage**
- At 25 stacks → `activateRage()`: `rageTimer = RAGE_DURATION = 180`, resets stacks, applies the full `25*0.04 = 1.0` atkSpd buff for the rage duration, shows Accelerate FX.
- In `execute`: when not raging, stacks fully reset to 0 after `stackResetTimer` ticks; when rage ends, the atkSpd buff is cleared (`addAttackSpeedBuff(220, 0, 1, refresh)`).
- During rage `onShurikenHit` is skipped, so stacks don't accumulate while raging — rage is a fixed 180t window.

**Skill — tornado volley**
- Fires `SylphidTornado1` (power `i = 1`, **Ⅱ 1.2**): base spawns the tornado on the target plus one "most divergent" (most opposite-direction) target via `findMostDivergentTarget` (gated by `DIVERGE_THRESHOLD=0.7` dot-product), else a random-offset extra.
- **Ⅱ:** adds a 3rd tornado at the next most-divergent target (excluding the first two).
- If no live target, scatters `spawnTornadoAtRandomOffset` tornados (2 base / 3 Ⅱ).

**Buffs & debuffs**
- Self atk-speed (ramp): +4% per stack (value 0.04·stacks), 600t (~10s), refreshing — id 220
- Self atk-speed (rage): +100% (value 1.0), 180t (~3s) — id 220; cleared to value 0 when rage ends

**Base → Ⅱ**
- Skill tornado power 1→1.2; max tornados 2→3 (and random-scatter fallback 2→3).

**Key values**
| | base | Ⅱ |
|---|---|---|
| skill power | 1 | 1.2 |
| max tornados / scatter | 2 | 3 |
| ATKSPD_PER_STACK | 0.04 (+4%) | 0.04 |
| ATKSPD_MAX_STACK | 25 (⇒ +100%, triggers rage) | 25 |
| STACK_BUFF_DUR | 600t (~10s) | 600t |
| RAGE_DURATION | 180t (~3s) | 180t |
| DIVERGE_THRESHOLD | 0.7 | 0.7 |
| numBounce | 3 | 3 |
| maxMana | 600 | 600 |
| rage extra shot | `doRangeAttack(target,4)` | same |
| atkSpd buff id | 220 | 220 |

**Formulas**
- `atkSpd = orgAtkSpd × (1 + 0.04·stacks)`; at 25 stacks ⇒ `×(1+1.0)` = +100% (×2), which fires rage. Rage holds +100% for 180t.

**✓ Matches description** — "each hit increases attack speed" = +0.04/stack (`onShurikenHit`); "max attack speed → additional shurikens" = at 25 stacks rage triggers and normals fire the extra `doRangeAttack(target,4)`. Skill = tornados, evolved fires one more (3 vs 2) at 1.2× power.

---

### Forest Guardian — `TigerRider1` (kindNum: 81 · Ⅱ 84)
**TL;DR.** Ranged archer that volleys arrows at several enemies at once; its skill is a multi-target barrage with a chance to grant itself a speed buff.

**At a glance**
- **Role:** Ranged DPS (multi-target volley + self speed buff)
- **Attack:** cycles arrows across 3 → **4** nearest enemies
- **Skill:** arrow barrage (1–2 → **1–3** arrows) within radius 220; 50% chance to self-buff
- **Self buff:** +80% atk/move-speed → **+110%** (distinct ids ⇒ both apply)

**In-game text**
- Normal: "Fires magic arrows at enemies within range." (Ⅱ: "Fires magic arrows at more enemies within range.")
- Skill: "Attacks multiple enemies at once with a barrage of arrows, and has a chance to grant itself a Speed Up buff." (Ⅱ: "Attacks multiple enemies at once with a volley of arrows, and has a chance to grant itself an enhanced Speed buff.")

**Normal attack**
- Ranged, `weaponClass=TigerRiderArrow1`. `onAttackStartFrame` builds `targetList = getAttackableEnemyList(NUM_ATK_TARGETS = 3, Ⅱ 4)` with current target forced to front; `attackMain` fires one arrow per call, cycling `attackIndex` through the list (`doRangeAttack`).
- Direction-aware: `selectDirectionFrames` swaps 5 attack/skill frame sets + fire points by firing angle (`atan2`).

**Skill — arrow barrage**
- `gotoSkillState` sets `mana=0` and, with `random.chance(.5)` (50%), self-buffs atk-speed (id 210) + move-speed (id 211) at value `s = 0.8` (**Ⅱ 1.1**) for `dur = 240t` (**Ⅱ 300t**), plus Accelerate FX.
- `onSkillStartFrame` collects `getEnemiesWithin(220, true)` into `skillTargetList`; `skillMain` fires N skill arrows (`fireSkillArrow`, bounceCount=`numBounce`).
- N (base) = `random.chance(.7)?2:1`; N (Ⅱ) = `rand<.3?3 : rand<.75?2 : 1`.

**Buffs & debuffs**
- Self atk-speed (50% per skill): +80% (Ⅱ +110%, value 0.8/1.1), 240t (Ⅱ 300t) — id 210
- Self move-speed (50% per skill): +80% (Ⅱ +110%), 240t (Ⅱ 300t) — id 211

**Base → Ⅱ**
- Normal targets 3→4; skill arrows 1–2→1–3; self-buff value 0.8→1.1, duration 240→300.

**Key values**
| | base | Ⅱ |
|---|---|---|
| NUM_ATK_TARGETS | 3 | 4 |
| BUFF_VALUE | 0.8 (+80%) | 1.1 (+110%) |
| BUFF_DURATION | 240t | 300t |
| self-buff chance | 0.5 | 0.5 |
| skill arrows | 1 or 2 (70%→2) | 1/2/3 (<.3→3, <.75→2) |
| skill target query | `getEnemiesWithin(220,true)` | same |
| atkSpd / moveSpd buff ids | 210 / 211 (distinct ⇒ both apply) | 210 / 211 |
| weaponClass | TigerRiderArrow1 | same |

**Formulas**
- Self `atkSpd = orgAtkSpd × (1+0.8)` ⇒ +80% / `×(1+1.1)` ⇒ +110%; same magnitude moveSpd. atkSpd (210) and moveSpd (211) use distinct ids, so they don't interfere.

**✓ Matches description** — "fires arrows at more enemies" (Ⅱ) = NUM_ATK_TARGETS 3→4; "barrage/volley" = 1–2 (base) / 1–3 (Ⅱ) skill arrows; "chance to grant itself a Speed Up" = 50% self atk+move-speed buff; "enhanced Speed buff" (Ⅱ) = value 0.8→1.1, duration 240→300.

**Notes**
- Structurally near-identical to `Unicorn1`/Unicorn Archer, but Unicorn1 has NO self-buff — that self-buff is the distinguishing Forest-Guardian trait.

---

### Druid (Druid2) — `Druid2` (kindNum: none — stub/placeholder)
**TL;DR.** An inert placeholder ranged unit: it fires a default attack but its skill does literally nothing.

**At a glance**
- **Role:** Ranged (stub — no functional skill)
- **Attack:** single default `doRangeAttack` (no `weaponClass` even assigned)
- **Skill:** dead expression — no damage, no buff, no projectile
- **Status:** registered class with `hasSkill=true` but an empty `skillMain`

**How it works**
- Minimal ranged unit: `unitType=RANGE`, `sheetName="Game1"`, `firePoint=(14,-14)`, `objAtk={76:1}`, `objSkill={112:1}`, `hasSkill=true`.
- `attackMain` is just `this.target && this.target.isAlive && this.doRangeAttack(this.target)` — a single default ranged hit, and **no `weaponClass` is assigned** in `initializeData`.
- `skillMain` is the **dead expression** `this.target && this.target.isAlive;` — evaluates truthiness and does nothing else.
- Only referenced in the className→class map (`[fx.Druid2]:v2`); no static constants, no kindNum wiring.

**Key values**
| variable | value | meaning |
|---|---|---|
| objAtk / objSkill frame | 76 / 112 | hit frames (skill frame unused) |
| firePoint | (14, −14) | muzzle offset |
| normalSize | 0.9 | render scale |
| weaponClass | (none set) | no projectile assigned |

**⚠️ Description vs code**
- No localized description to compare (no kindNum). The notable finding: `skillMain` is an **empty/no-op** despite `hasSkill=true` and an allocated skill frame range — effectively an inert placeholder, or a unit whose skill was stripped/never implemented in this build. Stated explicitly rather than inventing a match.

**Notes**
- Sister class `Druid1` (`Q1`) is fully implemented (vine/tendril entangle CC via `DruidTangle1`), so `Druid2` being empty is conspicuous — likely an unfinished evolved/variant or cut content in 1.11.42.
