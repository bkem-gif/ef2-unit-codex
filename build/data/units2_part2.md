# EF2 unit-mechanics extraction — Part 2 (12 classes)

Bundle: `runtime/bundles/mounted/1.11.42/assets/index.js` (1.11.42). Locale: `assets/locales/en.json`.
Damage convention: `doDamage(target, mult, isRanged)` deals `atkDmg*mult` (with night/tribe/block/evade modifiers). `doMeleeAttack(t,mult)` / `doRangeAttack(t)` / `generateWeapon(t,WeaponType,mult)` all route through `doDamage`. Recompute formulas: `atkSpd=orgAtkSpd*(1+activeAttackSpeedBuff.value)`, `atkDmg=orgAtkDmg*(1+activeDamageBuff.value)`, `moveSpd=orgMoveSpd*(1+activeMoveSpeedBuff.value)`. Times are game ticks (~60/s @ 1×).

NOTE ON kindNum: kindNum→className is supplied at runtime by server `bookList` data (`setBookData`), NOT hard-coded in the bundle. kindNums below are assigned by behavior-match to `/tmp/unit_desc.json`. Succubus1, CrowKnight1, GriffinRider1 have NO entry in unit_desc.json or en.json (UNIT_NAME/NATK/SATK absent) — they are newer units shipped without localized descriptions, so their kindNum cannot be pinned and the in-game description is stated as absent.

---

### Dark Ninja / Dark Ninja Ⅱ — `DarkNinja1` (kindNum: 87 · Ⅱ 88)
**TL;DR.** Teleporting assassin that blinks beside random enemies for rapid lifesteal hits, and on skill yanks far foes in with dark chains before a knock-up spin.

**At a glance**
- **Role:** Melee DPS / assassin (teleporting lifesteal bruiser)
- **Attack:** blinks beside a random nearby enemy, low-damage rapid multi-hit (0.8× each) with lifesteal
- **Skill:** mana-gated (≥500) — Dark Chain pull (×1, ×2 at Ⅱ) + spinning AoE knock-up
- **Stats:** maxHp 150, atkDmg 3, def 10, moveSpd 2.6, atkRange 8, maxMana 250

**In-game text**
- Normal: "Teleports to an enemy at random and unleashes a series of close-range attacks, restoring a small amount of HP with each hit."
- Skill: "Fires a Dark Chain to pull in distant enemies (including airborne units), then attacks nearby enemies with a spinning attack."
- Skill (Ⅱ): "Fires Dark Chain to pull in 2 distant enemies (including aerial units), then strikes nearby enemies with a spinning attack."

**Normal attack**
- 50% chance to scan enemies within 120; for each in-bounds enemy, 30% chance to re-target to it, then **teleport** beside it (±30 px).
- Hits with `doMeleeAttack(target, 0.8)` and lifesteals `+0.005*maxHp` per hit.
- Combo length: 6 hits base (OBJ_ATK_1) → **8 hits at Ⅱ** (OBJ_ATK_2).

**Skill — spin + chain (mana ≥ 500)**
- Mana-gated, not cooldown-gated: triggers when IDLE with `mana>=500` and enemies present.
- Builds a chain-target list (`findChainTargets`, FARTHEST-first within 150 px; air/ranged units down-weighted).
- If nearest chain target has `weight>=4`, teleports to it and `doMeleeAttack(_, 1.5)`; otherwise fires a `DarkChain1` projectile to pull it in. **Ⅱ fires a second DarkChain1** at chain target [1] (if its `weight<=3`).
- Spinning AoE: on each of 9 `whirlAttackFrame` frames, fires `doDamage(_, 0.5)` to up to 2 enemies within `1.5*atkRange` (=12) and `blow()`s them (knock-up).

**Passive / special**
- Lifesteal on every normal hit: `hp = min(maxHp, hp + 0.005*maxHp)`.

**Buffs & debuffs**
- Applies `blow` (knock-up, ±0.2/−4) to enemies during the spin. No ally buffs.

**Base → Ⅱ**
- Normal combo 6 hits → 8 hits; skill fires a second Dark Chain.

**Key values**
| | base | Ⅱ |
|---|---|---|
| normal attack mult | 0.8 | 0.8 |
| lifesteal per hit | 0.005×maxHp | 0.005×maxHp |
| combo hits | 6 (OBJ_ATK_1 {48,54,59,64,69,74}) | 8 (OBJ_ATK_2 {48,51,54,57,61,64,69,74}) |
| chain teleport mult | 1.5 | 1.5 |
| Dark Chains on skill | 1 | 2 |
| whirl AoE mult | 0.5 (≤2 targets) | 0.5 (≤2 targets) |
| whirl radius | 1.5×atkRange (=12) | 12 |
| IDLE_SKILL_MANA | 500 | 500 |
| maxMana | 250 | 250 |
| teleport-scan radius | 120 | 120 |
| teleport offset | 30 px | 30 px |
| blow | (±0.2, −4) | (±0.2, −4) |

**Formulas**
- Lifesteal: `hp = min(maxHp, hp + 0.005*maxHp)`.
- Normal teleport: `x = targetX ∓ 30`.

**✓ Matches description** — chain pull (1 base / 2 evolved) and spin AoE both match; evolved scaling (8-hit combo, second chain) is consistent.

**Notes**
- `maxMana=250` but the auto-cast gate is `mana>=500`, so the threshold can never be reached from `maxMana` alone — the skill must rely on external mana grants/over-cap; the description mentions no mana cost.
- Low per-hit damage (0.8×) but rapid multi-hit + lifesteal makes it a sustain bruiser.

---

### Succubus1 — `Succubus1` (kindNum: not in desc.json — newer unit, no localized description)
**TL;DR.** Flying ranged attacker whose skill hastes only male allies — code names one of its two speed buffs "attack speed" but actually applies it as a second move-speed buff.

**At a glance**
- **Role:** Support buffer (gender-selective ally hastener) + ranged attacker
- **Attack:** flying ranged unit, fires `SuccubusBlade1` (objAtk frame 56)
- **Skill:** buffs every alive **male** (`sex=="M"`) ally with move speed for 120t (~2s)
- **Quirk:** the "attack speed" buff is wired to move speed; net is +90% move speed, zero atk-speed

**In-game text**
- (none — no `UNIT_NAME/NATK/SATK` entry in en.json or unit_desc.json)

**Skill — love buff (male allies only)**
- objSkill frame 101: iterates `allyList`; for each alive ally with `sex=="M"`, calls `showLoveShield(120)`.
- `showLoveShield(t)` applies NO damage shield (misnomer) — it sets `numLoveShield=t` (120-tick timer) and grants two movement buffs.
- Spawns 20 `SuccubusLove` visual effects (cosmetic).

**Buffs & debuffs** (to male `sex=="M"` allies only — distinct ids ⇒ stack additively)
- Move speed: +50% (value 0.5), 120t (~2s) — id `Succubus1_MOVESPEED_BUFF`
- "Attack speed": +40% (value 0.4), 120t — id `Succubus1_ATTACKSPEED_BUFF`, but applied via `addMoveSpeedBuff` (see ⚠️)

**Key values**
| variable | value | meaning |
|---|---|---|
| love-buff duration | 120 | ticks (~2s @ 1×) |
| MOVESPEED buff value | 0.5 | +50% move speed |
| "ATTACKSPEED" buff value | 0.4 | +40% — but applied as a MOVE-speed buff |
| airHeight | 40 | flying unit |
| love-effect count | 20 | cosmetic SuccubusLove sprites |

**Formulas**
- `moveSpd = orgMoveSpd*(1 + 0.5 + 0.4)` ⇒ effectively +90% move speed (two distinct buff ids ⇒ summed).

**⚠️ Description vs code**
- No in-game description to compare. CODE-INTERNAL quirk: the buff named `Succubus1_ATTACKSPEED_BUFF` is applied via `addMoveSpeedBuff`, not `addAttackSpeedBuff` — it grants movement speed, NOT attack speed. Net = +90% move speed and **zero atk-speed change**. Also `showLoveShield` is a misnomer: no damage mitigation, only the speed buffs.

**Notes**
- Gender-gated: only buffs male allies. Re-cast doesn't stack same-id (max kept) but refreshes uptime.

---

### Abyss Mage / Abyss Mage Ⅱ — `Abyss1` (kindNum: 91 · Ⅱ 95)
**TL;DR.** Ranged chain-lightning mage — basic attacks bounce between enemies for decaying damage and refund mana on kills; skill chains a shock that locks enemies' actions.

**At a glance**
- **Role:** Ranged DPS / mage (chain-lightning)
- **Attack:** lightning chains to 4 enemies (5 at Ⅱ), damage decaying per link; +30 mana on kill
- **Skill:** hits up to 10 enemies in 360 range, ×2 dmg (×3 at Ⅱ) + 60t Shock each
- **Type:** RANGE

**In-game text**
- Normal: "When you attack an enemy, chain lightning jumps to nearby enemies, dealing gradually reduced damage. Restore mana when defeating an enemy."
- Skill: "Strikes multiple enemies in range with lightning in succession, dealing AoE damage and briefly inflicting Shock, disabling their actions."

**Normal attack**
- Builds a chain from the target, repeatedly `findChainTarget` (nearest un-hit enemy within `CHAIN_RANGE=120`) up to 4 links base / **5 at Ⅱ**.
- Each link deals `doDamage(_, CHAIN_DMGS[r], ranged)` with `CHAIN_DMGS=[1, 0.7, 0.5, 0.4, 0.3]` (links past index 4 default to 0.5).
- On a kill: +30 mana.

**Skill — chained shock**
- `onSkillStartFrame` collects up to 10 enemies within 360; `skillMain` fires one per objSkill frame (10 frames).
- Each hit: `doDamage(target, 2 base / 3 Ⅱ, ranged)` + `target.shock(60)` (60-tick action-disable).

**Buffs & debuffs**
- Enemy `shock(60)` on each skill hit (disables actions), ~1s. No ally buffs.

**Base → Ⅱ**
- Chain links 4 → 5; skill mult ×2 → ×3.

**Key values**
| | base | Ⅱ |
|---|---|---|
| chain links | 4 | 5 |
| CHAIN_RANGE | 120 | 120 |
| CHAIN_DMGS | [1, 0.7, 0.5, 0.4, 0.3] | same |
| KILL_MANA_GAIN | 30 | 30 |
| skill dmg mult | 2 | 3 |
| SKILL_RANGE | 360 | 360 |
| SKILL_TARGET_MAX | 10 | 10 |
| shock | 60t | 60t |
| LIGHTNING_DUR / STEP | 58 / 36 | 58 / 36 |

**Formulas**
- Chain damage per link r = `atkDmg * CHAIN_DMGS[r]` (head 1.0× → 0.7 → 0.5 …).

**✓ Matches description** — "gradually reduced damage" = `CHAIN_DMGS` decay; "restore mana when defeating" = +30 on kill; "briefly inflicting Shock" = `shock(60)`. Evolved adds a chain link and raises skill mult; the locale text just doesn't enumerate numbers.

**Notes**
- Skill targets are pre-collected on the start frame, then consumed one-per-frame, so all collected enemies are hit in sequence.

---

### CrowKnight1 — `CrowKnight1` (kindNum: not in desc.json — newer unit, no localized description)
**TL;DR.** Boss-tier flying archer that gains an orbiting crow on every kill — each crow auto-shoots and self-buffs the knight's damage and speed — then sacrifices the whole swarm in a kamikaze burst on skill.

**At a glance**
- **Role:** Boss / ranged DPS with stacking kill-fed pet swarm (self-buffing)
- **Attack:** homing `CrowKnightBullet1` (×1) + orbiting crows auto-fire (×0.4 each)
- **Kill loop:** +1 crow per kill (max 12); sheds 1 crow per 300t with no kill
- **Skill:** tops crows to 6, then launches ALL crows as kamikaze (×3.5) and empties the swarm
- **Stats:** atkRange 350, maxHp 1500, atkDmg 12, maxMana 500, air unit

**In-game text**
- (none — no `UNIT_NAME/NATK/SATK` entry for this class)

**Normal attack**
- Fires a homing `CrowKnightBullet1` (mult 1) at nearest enemy.
- Orbiting crows each auto-fire a bullet (×0.4) every 150 (+0–30 jitter) ticks at enemies within 220.

**Passive / special — the crow swarm**
- Spawns 0 crows at init.
- `onKillEnemy`: spawns one more crow (up to 12) and resets the decay timer.
- If no kill for 300 ticks, sheds one crow (down to base count 0).
- `refreshOrbitBuff` re-applies the self-buff whenever crow count changes.

**Skill — kamikaze swarm**
- objSkill frame 134: collects up to 12 enemies within 400; tops crows up to 6.
- Launches ALL orbit crows as "pending executions" — they arc out (`SKILL_FLY_FRAMES=20`) to enemy positions and fire `CrowKnightBullet1` at ×3.5, speed 14, staggered by 4 ticks.
- Consumes all orbit crows (`orbitCrows.length=0`).

**Buffs & debuffs** (SELF only, refreshed on every crow-count change)
- Attack speed: +6% per crow (value `n*0.06`), dur 9999 — id `CrowKnight1_ORBIT_ATKSPD`
- Attack damage: +4% per crow (value `n*0.04`), dur 9999 — id `CrowKnight1_ORBIT_ATKDMG`
- No enemy debuffs (pure damage).

**Key values**
| variable | value | meaning |
|---|---|---|
| ORBIT_BASE_COUNT / MAX | 0 / 12 | starting / max orbiting crows |
| ORBIT_ATKSPD_PER | 0.06 | +6% atk speed per crow (self) |
| ORBIT_ATKDMG_PER | 0.04 | +4% atk damage per crow (self) |
| ORBIT_BUFF_DUR | 9999 | ~permanent (refreshed each crow change) |
| ORBIT_FIRE_DMG | 0.4 | per orbit-crow auto-shot |
| ORBIT_FIRE_INTERVAL | 150 (+0–30) | ticks between orbit-crow shots |
| ORBIT_FIRE_RANGE | 220 | orbit-crow targeting radius |
| ORBIT_DECAY_FRAMES | 300 | ticks of no-kill before shedding a crow |
| SKILL_TARGET_MAX / RANGE | 12 / 400 | skill targets / radius |
| SKILL_MIN_CROWS | 6 | crows topped-up before skill launch |
| SKILL_DMG / BULLET_SPEED | 3.5 / 14 | kamikaze crow bullet mult / speed |
| SKILL_FLY_FRAMES | 20 | crow arc-out duration |
| SKILL_FIRE_INTERVAL | 4 | ticks between kamikaze shots |
| atkRange/maxHp/atkDmg/maxMana | 350 / 1500 / 12 / 500 | boss-tier base stats |

**Formulas**
- Self atkSpd `= orgAtkSpd*(1 + n*0.06)`; self atkDmg `= orgAtkDmg*(1 + n*0.04)`. With 12 crows ⇒ +72% atk speed, +48% atk damage.

**⚠️ Description vs code**
- No in-game description to compare. Mechanically a snowballing kill-fed swarm that buffs itself and converts into a burst nuke on skill (sacrifices all crows).

**Notes**
- Crow count is the central resource — kills add crows (more dps + bigger skill), idle time sheds them. Skill empties the swarm, so dps drops right after a cast until kills rebuild it.

---

### Infantry / Infantry Ⅱ — `FootMan1` (kindNum: 1 · Ⅱ 26)
**TL;DR.** Basic melee swordsman; its skill is a heavy strike with a chance to stun.

**At a glance**
- **Role:** Melee DPS (basic sword infantry)
- **Attack:** basic sword on the nearest enemy (objAtk frame 49)
- **Skill:** heavy strike (×1.5, ×2.5 at Ⅱ) + chance to stun

**In-game text**
- Normal: "Strikes nearby enemies with a sword."
- Skill: "Delivers a powerful strike that damages enemies and has a chance to stun them."
- Skill (Ⅱ): "Unleashes a powerful strike that deals greater damage and stuns enemies with a higher chance."

**Skill — heavy strike**
- objSkill frame 127: `doMeleeAttack(target, 1.5 base / 2.5 Ⅱ)`, then 30% (50% at Ⅱ) chance to `stun(50 base / 60 Ⅱ)`.

**Base → Ⅱ**
- Damage ×1.5 → ×2.5; stun chance 30% → 50%; stun 50t → 60t.

**Key values**
| | base | Ⅱ |
|---|---|---|
| skill dmg mult | 1.5 | 2.5 |
| stun chance | 0.3 | 0.5 |
| stun duration | 50t | 60t |

**✓ Matches description** — evolved scales damage, stun chance, and stun duration exactly as "greater damage / higher chance" implies.

---

### Gunner / Gunner Ⅱ — `Gunner1` (kindNum: 4 · Ⅱ 29)
**TL;DR.** Fast ranged multi-shot gunner whose skill fires a guaranteed-stun bullet — and whose ordinary bullets carry a hidden 20% stun the description never mentions.

**At a glance**
- **Role:** Ranged DPS (multi-shot gunner with directional firing)
- **Attack:** very fast (atkDuration 20), 1.2 shots base / 1.8 at Ⅱ; bullets have hidden 20%/50t stun
- **Skill:** `Bullet1` at ×2.5 (×3.5 at Ⅱ) + **guaranteed** stun 30t (50t at Ⅱ)
- **Stats:** maxHp 100, atkDmg 10, def 10, moveSpd 1.6, atkRange 150

**In-game text**
- Normal: "Attacks enemies from range with precise shots."
- Skill: "Fires a powerful projectile that guarantees a stun."
- Skill (Ⅱ): "Fires an enhanced bullet that guarantees a longer stun on enemies."

**Normal attack**
- 5 directional anim/firepoint sets — `gotoAttackState`/`gotoSkillState` pick frames/firePoint by angle to target (36° bands).
- Sets `numShot = 1.2 base / 1.8 Ⅱ`, `multiShotDelay=3`, then base multi-shot (fractional ⇒ chance of extra shot).
- Every normal `Bullet1` hit also rolls 20% → `stun(50)` (undocumented — see ⚠️).

**Skill — guaranteed-stun shot**
- `generateWeapon(target, Bullet1, 2.5 base / 3.5 Ⅱ)` and **guaranteed** `target.stun(30 base / 50 Ⅱ)`.

**Buffs & debuffs**
- Enemy `stun` — guaranteed on skill (30/50t); ALSO 20% × 50t on every normal `Bullet1` hit.

**Base → Ⅱ**
- numShot 1.2 → 1.8; skill dmg ×2.5 → ×3.5; skill stun 30t → 50t.

**Key values**
| | base | Ⅱ |
|---|---|---|
| numShot | 1.2 | 1.8 |
| skill dmg mult | 2.5 | 3.5 |
| skill stun (guaranteed) | 30t | 50t |
| atkDuration | 20 | 20 |
| atkRange | 150 | 150 |
| multiShotDelay | 3 | 3 |
| normal Bullet1 stun | 20% × 50t | 20% × 50t |

**Formulas**
- Extra-shot chance = fractional part of `numShot` (e.g. 1.8 ⇒ 80% chance of a 2nd shot).

**⚠️ Description vs code**
- Skill matches (guaranteed stun, evolved longer 50 vs 30, higher dmg). DELTA on normal: the description says only "precise shots" with no stun, but `Bullet1`'s `onHitMain` applies `stun(50)` at 20% on EVERY normal hit (`random.chance(.2)&&target.stun(50)`). The basic attack has an undocumented 20% stun.

---

### Heavy Armor / Heavy Armor Ⅱ — `HeavyWarrior1` (kindNum: 2 · Ⅱ 27)
**TL;DR.** Slow tank that strikes and then drops a power shield reducing nearly all incoming damage to ~1% for a few seconds.

**At a glance**
- **Role:** Tank (self power-shield on skill)
- **Attack:** slow melee (atkDuration 200), low atkDmg 3
- **Skill:** melee hit (×1) then a 150t Power Shield (incoming damage ×0.01)
- **Stats:** maxHp 150, def 10, moveSpd 2.6, atkRange 8

**In-game text**
- Normal: "Attacks nearby enemies with a melee strike."
- Skill: "After attacking, deploys a power shield that blocks almost all physical and magic damage for a period of time."
- Skill (Ⅱ): "After attacking, deploys a Power Shield that blocks nearly all physical and magical damage for a set duration."

**Skill — power shield**
- `doMeleeAttack(target, 1)` then `showPowerShield(150)`.
- Power Shield multiplies all incoming damage by 0.01 (≈1%, both physical and magical) for its duration.

**Passive / special**
- While shielded (`numPowerShield>0`): `incomingDamage *= 0.01`.

**Buffs & debuffs**
- Self Power Shield (damage to 1%), 150 ticks. No ally/enemy effects.

**Base → Ⅱ**
- No numeric change to the shield — code is identical (`showPowerShield(150)` both tiers). Evolved benefit comes only from scaled base stats.

**Key values**
| variable | value | meaning |
|---|---|---|
| maxHp | 150 | tanky |
| atkDmg | 3 | low (defensive unit) |
| atkDuration | 200 | slow attacker |
| skill dmg mult | 1 | normal-strength hit before shield |
| powerShield duration | 150 | ticks of 1%-damage shield |
| powerShield mult | 0.01 | incoming damage ×0.01 (numPowerShield>0) |

**Formulas**
- While shielded: `incomingDamage *= 0.01`.

**✓ Matches description** — "blocks almost all physical and magic damage" = `c*=.01` applies to both types (checked before the type-specific full-block shields). The "Ⅱ" wording is cosmetic for the shield — no numeric difference in code.

**Notes**
- Unlike Infantry/HammerKnight, HeavyWarrior shows NO base/evolved branch in `skillMain` — the shield value (150) is identical regardless of evolStage.

---

### Hammer Knight / Hammer Knight Ⅱ — `HammerKnight1` (kindNum: 5 · Ⅱ 30)
**TL;DR.** Off-tank that slams the ground for AoE damage, stuns the main target plus nearby enemies, and can taunt — with an extra physical-shield proc on the evolved tier's basic attack.

**At a glance**
- **Role:** Melee DPS / off-tank (AoE slam, stun, taunt)
- **Attack:** heavy hammer melee (objAtk frame 57); Ⅱ adds 10% physShield(50) proc
- **Skill:** chance to taunt, main hit (×1.5, ×2 at Ⅱ) + stun, then AoE (×0.3) to ≤3 enemies with chance-stun
- **Taunt:** 30% (35% at Ⅱ) at skill start, taunt(60)

**In-game text**
- Normal: "Delivers a melee blow with a heavy hammer."
- Skill: "Slams the ground with great force, dealing AoE damage to nearby enemies, with a chance to stun them and trigger Taunt."
- Skill (Ⅱ): "Slams a wider area with a powerful strike, dealing heavy damage, stunning enemies with a higher chance, and can activate Taunt."

**Normal attack**
- Base attack via objAtk frame 57.
- `attackMain()` override (evolved only): 10% chance to `showPhysicalShield(50)` (50-tick PHYSICAL immunity).

**Skill — ground slam**
- Chance `tauntChance` (0.3 base / 0.35 Ⅱ) → `taunt(60)`.
- `doMeleeAttack(target, mainMult)` (1.5 base / 2 Ⅱ); `target.stun(stunMain)` (50 base / 60 Ⅱ).
- AoE: gathers enemies at a point `aoeRange` ahead (30 base / 40 Ⅱ) via `getEnemiesAtPos`, hits up to 3 with `doDamage(_, 0.3)`, each chance-stunned (0.3 base / 0.4 Ⅱ → stun 50 base / 60 Ⅱ).

**Buffs & debuffs**
- Enemy `taunt(60)` (chance-gated), `stun` on main target (50 base / 60 Ⅱ) and on AoE targets (chance-gated, 50 base / 60 Ⅱ).
- Self: evolved 10% `physicalShield(50)` on normal attack (blocks all PHYSICAL for 50t).

**Base → Ⅱ**
- AoE range 30 → 40; main dmg ×1.5 → ×2; taunt chance 0.3 → 0.35; AoE stun chance 0.3 → 0.4; all stuns 50t → 60t; +10% physShield proc on normal.

**Key values**
| metric | base | Ⅱ |
|---|---|---|
| taunt chance | 0.3 | 0.35 |
| main dmg mult | 1.5 | 2 |
| main-target stun | 50t (`h=t?60:50`) | 60t |
| AoE secondary stun chance | 0.3 | 0.4 |
| AoE stun | 50t (`n=t?60:50`) | 60t |
| AoE range | 30 | 40 |
| AoE dmg mult | 0.3 | 0.3 |
| AoE max targets | 3 | 3 |
| taunt duration | 60t | 60t |
| evolved physShield (normal) | — | 10% × 50t |

**Formulas**
- AoE centered at `(x + range*direction, y)`.

**⚠️ Description vs code**
- Skill matches (wider AoE, higher dmg, higher stun chances, longer stuns at Ⅱ). DELTA: evolved gains an undocumented 10% physical-shield proc on its NORMAL attack, which the descriptions don't mention.

---

### Mounted Knight / Mounted Knight Ⅱ — `HorseKnight1` (kindNum: 6 · Ⅱ 31)
**TL;DR.** Rapid melee combo cavalry that alternates hits between its main target and nearby foes, taunts every third skill use, and gets a big move-speed burst on every kill — even at the base tier the text doesn't mention.

**At a glance**
- **Role:** Melee DPS (rapid combo, kill-fed move-speed, periodic taunt)
- **Attack:** 3-hit melee flurry (objAtk frames 45,52,61)
- **Skill:** 6-strike combo alternating main/nearby; taunt(100) every 3rd use
- **On-kill:** +200% move speed for 60t (base AND evolved)

**In-game text**
- Normal: "Unleashes a rapid flurry of melee hits on enemies."
- Skill: "Launches a combo attack that alternates between the main target and nearby enemies. Taunt triggers after a certain number of uses."
- Normal (Ⅱ): "Strikes with rapid melee combos. Killing an enemy grants a movement speed buff."
- Skill (Ⅱ): "Delivers an enhanced combo attack alternating between the main target and nearby enemies. Activates Taunt after a set number of uses."

**Normal attack**
- 3-hit combo (objAtk frames 45,52,61).

**Skill — alternating combo**
- objSkill 6 frames {100,104,108,112,116,120}: `onSkillStartFrame` increments `skillUseCount`; every 3rd use ⇒ `taunt(100)`.
- Per hit-frame: hits #1 and #6 hit the main target (`doMeleeAttack(target, comboMult)`); the rest hit a nearby enemy (`attackNearbyEnemy`, radius 40) — alternating main/nearby.
- comboMult = 1 base / 1.2 Ⅱ.

**Passive / special**
- `onKillEnemy` (unconditional, base + evolved): `addMoveSpeedBuff(kindNum, 2, 60)` — +200% move speed for 60t on every kill.

**Buffs & debuffs**
- SELF: `addMoveSpeedBuff(kindNum, 2, 60)` on each kill (+200% move, 60t). Buff id = kindNum ⇒ self-stacks as max, refreshes uptime.
- Enemy `taunt(100)` every 3rd skill cast.

**Base → Ⅱ**
- Combo mult 1 → 1.2. (On-kill move buff is present in base code too — see ⚠️.)

**Key values**
| | base | Ⅱ |
|---|---|---|
| combo dmg mult | 1 | 1.2 |
| onKill move buff value | 2 (+200%) | 2 |
| onKill buff dur | 60t | 60t |
| taunt cadence | every 3rd use (`skillUseCount%3==0`) | same |
| taunt duration | 100t | 100t |
| nearby-search radius | 40 | 40 |
| objAtk (normal) | {45,52,61} | {45,52,61} |
| objSkill | {100,104,108,112,116,120} | same |

**Formulas**
- Kill move buff: `moveSpd = orgMoveSpd*(1+2)` ⇒ ×3 for 60 ticks.

**⚠️ Description vs code**
- Combo alternation and "taunt after N uses" (every 3rd) both match. DELTA: the kill→move-speed buff is in the BASE class too (`onKillEnemy` is unconditional), but the locale documents it only on the evolved normal text (UNIT_NATK_31). So base Mounted Knight ALSO gets the +200% move-speed-on-kill its base description (UNIT_NATK_6) omits.

---

### Firebird / Firebird Ⅱ — `FireBird1` (kindNum: 3 · Ⅱ 28)
**TL;DR.** High-flying ranged caster that lobs flaming shots from extreme range, with a heavy fireball skill that can stun.

**At a glance**
- **Role:** Ranged DPS (long-range flying caster)
- **Attack:** fires `FireBirdBall1` from a high-flying perch (airHeight 75)
- **Skill:** fireball ×2.5 (×3.5 at Ⅱ) + chance to stun 50t
- **Stun chance:** 30% base / 50% at Ⅱ

**In-game text**
- Normal: "Soars through the sky and launches flaming shots from extreme range."
- Skill: "Fires a powerful fireball that deals heavy damage and has a chance to stun enemies."
- Skill (Ⅱ): "Fires a powerful fireball that deals greater damage and stuns enemies with a higher chance."

**Normal attack**
- Fires `FireBirdBall1` (objAtk frame 35).

**Skill — fireball**
- objSkill frame 35: `generateWeapon(target, FireBirdBall1, 2.5 base / 3.5 Ⅱ)`, then if target alive, `random.chance(0.3 base / 0.5 Ⅱ)` ⇒ `target.stun(50)`.

**Buffs & debuffs**
- Enemy `stun(50)` on skill (chance-gated).

**Base → Ⅱ**
- Skill dmg ×2.5 → ×3.5; stun chance 30% → 50%; stun length 50t unchanged.

**Key values**
| | base | Ⅱ |
|---|---|---|
| skill dmg mult | 2.5 | 3.5 |
| skill stun chance | 0.3 | 0.5 |
| skill stun duration | 50t | 50t |
| airHeight | 75 | 75 |

**✓ Matches description** — evolved: greater dmg (3.5 vs 2.5) and higher stun chance (0.5 vs 0.3); stun length 50 unchanged.

---

### Priest / Priest Ⅱ — `Priest1` (kindNum: 55 · Ⅱ 56)
**TL;DR.** Ranged support healer that fires light bolts and casts an AoE heal plus a hit-negating shield on the team — but the "chance to stun" its normal attack claims doesn't exist in code.

**At a glance**
- **Role:** Healer / support (AoE heal + hit-blocking shields)
- **Attack:** ranged `YellowEnergyBall`, 1.5 shots base / 2 at Ⅱ (NO stun despite text)
- **Skill:** shields nearest ≤20 allies (blocks next 2/3 hits) + heals lowest-HP% ≤20 allies (5%/10% max HP)
- **Type:** RANGE

**In-game text**
- Normal: "Attacks from range with light energy and has a chance to stun enemies."
- Skill: "Restores HP for all allies and grants them a shield."
- Skill (Ⅱ): "Greatly restores HP for all allies and grants them an enhanced shield."

**Normal attack**
- `attackMain()` sets `numShot = 1.5 base / 2 Ⅱ` then base multi-shot.
- objAtk: OBJ_ATK_1 {39,46} (base, 2 hits) / OBJ_ATK_2 {39,44,49} (Ⅱ, 3 hits).
- `YellowEnergyBall` only deals damage (g=0, speed=8) — applies NO stun (see ⚠️).

**Skill — heal + shield**
- Cosmetic `showPriestLight(60)`.
- **Shield pass:** sorts allies by distance, takes nearest ≤20, calls `showPriestStart(shieldDur, shieldHits)` → sets `numPriestShield=shieldDur`, `priestShieldHits=shieldHits` (fully negates the next `shieldHits` hits while the timer lasts).
- **Heal pass:** sorts allies by HP% ascending (lowest first), takes nearest 20, `heal(t, this, true)` with `t = healPct` for normal allies / `castlePct` for castles.

**Buffs & debuffs** (to nearest ≤20 allies)
- Hit-blocking shield: `numPriestShield` dur (90 base / 120 Ⅱ), `priestShieldHits` count (2 base / 3 Ⅱ).
- % heal: 5% base / 10% Ⅱ of max HP (castles get 0.5% / 1%). No enemy debuffs.

**Base → Ⅱ**
- Heal 5% → 10% (castle 0.5% → 1%); shield duration 90t → 120t; shield hits 2 → 3; numShot 1.5 → 2; normal 2-hit → 3-hit.

**Key values**
| metric | base | Ⅱ |
|---|---|---|
| ally heal pct | 5% | 10% |
| castle heal pct | 0.5% | 1% |
| shield duration | 90t | 120t |
| shield hits | 2 | 3 |
| SKILL_MAX_TARGETS | 20 | 20 |
| numShot | 1.5 | 2 |
| objAtk | {39,46} | {39,44,49} |

**Formulas**
- Heal amount `= maxHp * 0.01 * healPct` (evolved 10 ⇒ +10% max HP).
- Shield: while `numPriestShield>0 && priestShieldHits>0`, an incoming hit is fully negated and `priestShieldHits--`; at 0 the shield clears.

**⚠️ Description vs code**
- Heal+shield skill matches ("greatly restores / enhanced shield" = 10% vs 5%, 3 hits/120t vs 2 hits/90t). DELTA on NORMAL: the description says it "has a chance to stun enemies," but `YellowEnergyBall` has NO `onHitMain` and applies NO stun anywhere in `Priest1` or the weapon. The documented normal-attack stun does NOT exist in code (contrast `Bullet1`/Gunner, which does have the hook).

**Notes**
- Heal targets the LOWEST-HP% allies first; shields target the NEAREST allies first — two different sort orders, both capped at 20. Castle heal % is ~10× smaller than ally heal %.

---

### GriffinRider1 — `GriffinRider1` (kindNum: not in desc.json — newer unit, no localized description)
**TL;DR.** High-flying ranged lancer that spreads its basic attacks across multiple enemies in front of it and fires bouncing super-spears on skill.

**At a glance**
- **Role:** Ranged DPS (flying multi-target lancer, bouncing skill spears)
- **Attack:** `GriffinSpear1`, spread across 2 (base) / 3 (Ⅱ) enemies in the facing direction
- **Skill:** 3 `GriffinSuperSpear1` casts (×1.5) that bounce/chain (`numBounce`); each spear knocks back + `stun(30)` on hit
- **Stats:** air unit, airHeight 75

**In-game text**
- (none — no `UNIT_NAME/NATK/SATK` entry for this class)

**Normal attack**
- `onAttackStartFrame`: gathers enemies in the facing direction within atkRange, up to 2 (base) / 3 (Ⅱ) targets (`getEnemiesForDirection`), front-loading the current target.
- `attackMain()` cycles `attackIndex` through that list, `doRangeAttack`-ing one per objAtk frame — spreading hits across 2/3 enemies.

**Skill — bouncing super-spears**
- objSkill frames {152,170,188} (3 casts): `onSkillStartFrame` collects enemies within 220 (target first).
- `skillMain` fires one `GriffinSuperSpear1` per cast via `fireSkillArrow`, dmg mult 1.5, `bounceCount = this.numBounce`. Each spear's `onHitMain` applies **knockBack (power 10) + `stun(30)`** on hit.
- Spear fire offset randomized `35 + 20*random`.

**Buffs & debuffs**
- The skill spears carry the CC: `GriffinSuperSpear1.onHitMain` applies **knockBack (power 10) + `stun(30)`** on each hit (verified in the weapon, not this class). No freeze; no ally buffs.

**Base → Ⅱ**
- Normal-attack target count 2 → 3. Skill fires 3 bouncing super-spears regardless of tier.

**Key values**
| | base | Ⅱ |
|---|---|---|
| normal targets | 2 | 3 |
| skill collect radius | 220 | 220 |
| skill spear dmg mult | 1.5 | 1.5 |
| skill spear bounces | `numBounce` | `numBounce` |
| objSkill | {152,170,188} | same |
| airHeight | 75 | 75 |

**Formulas**
- Normal attack distributes across `min(targetsInDir, 2|3)` enemies, one per objAtk frame.

**⚠️ Description vs code**
- No in-game description to compare. Behaviorally a Wyvern/Raptor-style multi-target flyer with a bouncing super-spear finisher; evolved adds one more normal-attack target (3 vs 2).
