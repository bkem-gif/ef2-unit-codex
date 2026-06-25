# EF2 unit-mechanics extraction — Part 2 (12 classes)

Bundle: `runtime/bundles/mounted/1.11.42/assets/index.js` (1.11.42). Locale: `assets/locales/en.json`.
Damage convention: `doDamage(target, mult, isRanged)` deals `atkDmg*mult` (with night/tribe/block/evade modifiers). `doMeleeAttack(t,mult)` / `doRangeAttack(t)` / `generateWeapon(t,WeaponType,mult)` all route through `doDamage`. Recompute formulas: `atkSpd=orgAtkSpd*(1+activeAttackSpeedBuff.value)`, `atkDmg=orgAtkDmg*(1+activeDamageBuff.value)`, `moveSpd=orgMoveSpd*(1+activeMoveSpeedBuff.value)`. Times are game ticks (~60/s @ 1×).

NOTE ON kindNum: kindNum→className is supplied at runtime by server `bookList` data (`setBookData`), NOT hard-coded in the bundle. kindNums below are assigned by behavior-match to `/tmp/unit_desc.json`. Succubus1, CrowKnight1, GriffinRider1 have NO entry in unit_desc.json or en.json (UNIT_NAME/NATK/SATK absent) — they are newer units shipped without localized descriptions, so their kindNum cannot be pinned and the in-game description is stated as absent.

---

### Dark Ninja / Dark Ninja Ⅱ — `DarkNinja1` (kindNum: 87, 88 evolved)
**Role:** melee dps / assassin (teleporting lifesteal bruiser)
**Description (in-game):**
- Normal (`UNIT_NATK_87`): "Teleports to an enemy at random and unleashes a series of close-range attacks, restoring a small amount of HP with each hit."
- Skill (`UNIT_SATK_87`): "Fires a Dark Chain to pull in distant enemies (including airborne units), then attacks nearby enemies with a spinning attack."
- (`UNIT_SATK_88`, evolved): "Fires Dark Chain to pull in 2 distant enemies (including aerial units), then strikes nearby enemies with a spinning attack."
**How it works (code):** Base stats maxHp 150, atkDmg 3, def 10, moveSpd 2.6, atkDuration 200, atkRange 8, maxMana 250. `attackMain()`: with 50% chance scans enemies within 120, and for each (in-bounds, 30% chance) re-targets to it, then **teleports** beside that enemy (±30 px). Hits target with `doMeleeAttack(target, 0.8)` and **lifesteals** `+0.005*maxHp` per hit. Skill is mana-gated, not cooldown-gated: in `execute()`, when IDLE with `mana>=IDLE_SKILL_MANA(500)` and enemies present, it enters skill state. `skillMain()` builds a prioritized chain-target list (`findChainTargets`, sorted FARTHEST-first within 150 px; air targets and ranged units down-weighted via score penalties). If the nearest chain target has `weight>=4` it teleports to it and `doMeleeAttack(_, 1.5)`; otherwise it fires a `DarkChain1` projectile to pull it in — **evolved fires a second DarkChain1** at chain target [1] (if its `weight<=3`). The spinning AoE happens in `execute()` on `whirlAttackFrame` frames (9 frames): each fires `doDamage(_, 0.5)` to up to 2 enemies within `1.5*atkRange` and `blow()`s them (knock-up).
**Hard values:**
| variable | value | meaning |
|---|---|---|
| IDLE_SKILL_MANA | 500 | mana threshold to auto-cast spin/chain skill |
| maxMana | 250 | (note: < IDLE_SKILL_MANA — see Δ) |
| attack mult | 0.8 | per normal melee hit |
| lifesteal | 0.005*maxHp | HP restored per normal hit |
| teleport-scan radius | 120 | normal-attack random-teleport search |
| teleport offset | 30 px | placed beside target |
| whirl AoE mult | 0.5 | per spin-frame hit, max 2 targets |
| whirl radius | 1.5*atkRange (=12) | spin hit radius |
| blow | (±0.2, −4) | knock-up applied by spin |
| OBJ_ATK_1 / _2 | {48,54,59,64,69,74} / {48,51,54,57,61,64,69,74} | base 6 hits / evolved 8 hits per attack anim |
**Formulas:** lifesteal `hp = min(maxHp, hp + 0.005*maxHp)`; normal teleport: `x = targetX ∓ 30`.
**Buffs/debuffs applied:** none to allies; applies `blow` (knock-up) to enemies during spin.
**Δ description vs code:** Mostly matches. (1) Description frames the spin as the skill; in code the spin AoE is driven by `whirlAttackFrame` in `execute()` during the skill animation — consistent. (2) The "chain pulls in 1 (base) / 2 (evolved)" matches `evolStage>=1 && t.length>=2` second chain. (3) Notable: `maxMana=250` but the auto-cast gate is `mana>=500`. This means the documented mana threshold can never be reached from `maxMana` alone — the skill must be enabled by external mana grants/over-cap, or `IDLE_SKILL_MANA` is effectively a high bar; the description doesn't mention a mana cost at all.
**Notes:** Evolved: 8-hit normal combo (vs 6), second Dark Chain on skill. Normal-attack damage is low per hit (0.8×) but rapid multi-hit + lifesteal makes it a sustain bruiser.

---

### Succubus1 — `Succubus1` (kindNum: not in desc.json — newer unit, no localized description)
**Role:** support/buffer (gender-selective ally hastener) + ranged attacker
**Description (in-game):** none present — no `UNIT_NAME/NATK/SATK` entry in en.json or unit_desc.json for this class.
**How it works (code):** Air unit (airHeight 40), RANGE, weapon `SuccubusBlade1`, normal attack fires the blade on objAtk frame 56. `skillMain()` (objSkill frame 101): iterates `allyList` and, for every alive ally whose **`sex=="M"`** (male), calls `showLoveShield(120)`. `showLoveShield(t)` is a misnomer — it applies NO damage shield; it sets `numLoveShield=t` (a 120-tick timer) and grants the ally **two movement-related buffs**: `addMoveSpeedBuff(Succubus1_MOVESPEED_BUFF, 0.5, 120)` and `addMoveSpeedBuff(Succubus1_ATTACKSPEED_BUFF, 0.4, 120)`. The skill also spawns 20 `SuccubusLove` visual effects (cosmetic).
**Hard values:**
| variable | value | meaning |
|---|---|---|
| love-buff duration | 120 | ticks (≈2 s @ 1×) |
| MOVESPEED buff value | 0.5 | +50% move speed |
| "ATTACKSPEED" buff value | 0.4 | +40% — but applied as a MOVE-speed buff (see Δ) |
| airHeight | 40 | flying unit |
| love-effect count | 20 | cosmetic SuccubusLove sprites |
**Formulas:** `moveSpd = orgMoveSpd*(1+0.5+0.4)` when both apply ⇒ effectively +90% move speed (two distinct buff ids ⇒ summed).
**Buffs/debuffs applied:** to male (`sex=="M"`) allies only — buff id `Succubus1_MOVESPEED_BUFF` value 0.5 (+50%), and buff id `Succubus1_ATTACKSPEED_BUFF` value 0.4 (+40%), both `addMoveSpeedBuff`, duration 120. Distinct ids ⇒ stack additively.
**Δ description vs code:** No in-game description to compare. CODE-INTERNAL bug/quirk worth flagging: the buff named `Succubus1_ATTACKSPEED_BUFF` is applied via `addMoveSpeedBuff`, not `addAttackSpeedBuff` — so it grants movement speed, NOT attack speed. Both buffs feed `activeMoveSpeedBuff`; net is +90% move speed and **zero attack-speed change**. Also "shield" in `showLoveShield` is a misnomer: there is no damage mitigation, only the speed buffs.
**Notes:** Gender-gated: only buffs male allies. Re-cast does not stack same-id (max kept) but refreshes uptime.

---

### Abyss Mage / Abyss Mage Ⅱ — `Abyss1` (kindNum: 91, 95 evolved)
**Role:** ranged dps / mage (chain-lightning)
**Description (in-game):**
- Normal (`UNIT_NATK_91`): "When you attack an enemy, chain lightning jumps to nearby enemies, dealing gradually reduced damage. Restore mana when defeating an enemy."
- Skill (`UNIT_SATK_91`): "Strikes multiple enemies in range with lightning in succession, dealing AoE damage and briefly inflicting Shock, disabling their actions."
**How it works (code):** RANGE. `attackMain()` builds a chain: starts at target, repeatedly `findChainTarget` (nearest un-hit enemy within `CHAIN_RANGE=120`) up to `CHAIN_COUNT=4` (base) / `CHAIN_COUNT_E=5` (evolved). Each link takes `doDamage(_, CHAIN_DMGS[r], isRanged=true)` where `CHAIN_DMGS=[1, 0.7, 0.5, 0.4, 0.3]` (links past index 4 default to 0.5). On a kill, `+KILL_MANA_GAIN=30` mana. Draws lightning arcs between links (`placeLightning`). Skill (`onSkillStartFrame` collects up to `SKILL_TARGET_MAX=10` enemies within `SKILL_RANGE=360`; `skillMain` fires one per objSkill frame, 10 frames): `doDamage(target, 3 evolved / 2 base, ranged)` + `target.shock(60)` (60-tick action-disable) + sky-to-ground lightning visual.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| CHAIN_RANGE | 120 | max jump distance between chain links |
| CHAIN_COUNT / _E | 4 / 5 | links per normal attack (base / evolved) |
| CHAIN_DMGS | [1, 0.7, 0.5, 0.4, 0.3] | per-link damage mult, decays down the chain |
| KILL_MANA_GAIN | 30 | mana on enemy kill |
| skill dmg mult | 2 / 3 | base / evolved, per skill hit |
| SKILL_RANGE | 360 | skill target-collection radius |
| SKILL_TARGET_MAX | 10 | max skill targets |
| shock | 60 | ticks of Shock (action lock) on skill hit |
| LIGHTNING_DUR / STEP | 58 / 36 | arc visual lifetime / segment spacing |
**Formulas:** chain damage per link r = `atkDmg * CHAIN_DMGS[r]` (head 1.0× → 0.7 → 0.5 …).
**Buffs/debuffs applied:** enemy debuff `shock(60)` on each skill hit (disables actions). No ally buffs.
**Δ description vs code:** None — matches well. "Gradually reduced damage" = `CHAIN_DMGS` decay; "restore mana when defeating" = `+30` on kill; "briefly inflicting Shock" = `shock(60)`. Evolved adds one chain link (5 vs 4) and raises skill mult 3 vs 2 (matches "Ⅱ" being stronger). Damage values are identical between 91 and 95 descriptions, but code does differ (chain count, skill mult) — the locale text just doesn't enumerate the numbers.
**Notes:** Skill targets are pre-collected on the start frame, then consumed one-per-frame, so all collected enemies are hit in sequence.

---

### CrowKnight1 — `CrowKnight1` (kindNum: not in desc.json — newer unit, no localized description)
**Role:** boss / ranged dps with stacking pet swarm (self-buffing)
**Description (in-game):** none present — no `UNIT_NAME/NATK/SATK` entry for this class.
**How it works (code):** Heavyweight: atkRange 350, maxHp 1500, atkDmg 12, maxMana 500, air unit. Spawns `ORBIT_BASE_COUNT=0` crows at init. Normal `attackMain()` fires a homing `CrowKnightBullet1` (mult 1) at nearest enemy. **Orbiting crows** (companions) circle the knight and each auto-fire a bullet (`ORBIT_FIRE_DMG=0.4`) every `ORBIT_FIRE_INTERVAL=150` (+0–30 jitter) ticks at enemies within `ORBIT_FIRE_RANGE=220`. On every kill (`onKillEnemy`), spawns one more crow (up to `ORBIT_MAX_COUNT=12`) and resets a decay timer. If no kill for `ORBIT_DECAY_FRAMES=300` ticks, sheds one crow (down to base count). Each crow grants the knight a **self-buff**: `refreshOrbitBuff` sets `addAttackSpeedBuff(value = n*0.06, 9999)` and `addAttackDamageBuff(value = n*0.04, 9999)` where n = current crow count. Skill (`skillMain`, objSkill frame 134): collects up to `SKILL_TARGET_MAX=12` enemies within `SKILL_TARGET_RANGE=400`, tops crows up to `SKILL_MIN_CROWS=6`, then launches ALL orbit crows as kamikaze "pending executions" that fly out (arc, `SKILL_FLY_FRAMES=20`) to enemy positions and fire `CrowKnightBullet1` at `SKILL_DMG=3.5`, `SKILL_BULLET_SPEED=14`, staggered by `SKILL_FIRE_INTERVAL=4` ticks. Skill consumes all orbit crows (`orbitCrows.length=0`).
**Hard values:**
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
| (base) atkRange/maxHp/atkDmg/maxMana | 350 / 1500 / 12 / 500 | boss-tier base stats |
**Formulas:** self atkSpd `= orgAtkSpd*(1 + n*0.06)`; self atkDmg `= orgAtkDmg*(1 + n*0.04)`; with 12 crows ⇒ +72% atk speed, +48% atk damage.
**Buffs/debuffs applied:** SELF only — `CrowKnight1_ORBIT_ATKSPD` value `n*0.06`, `CrowKnight1_ORBIT_ATKDMG` value `n*0.04`, dur 9999, refreshed whenever crow count changes. No enemy debuffs (pure damage).
**Δ description vs code:** No in-game description to compare. Mechanically rich: a snowballing kill-fed swarm that buffs itself and converts into a burst nuke on skill (sacrifices all crows).
**Notes:** Crow count is the central resource — kills add crows (more dps + bigger skill), idle time sheds them. Skill empties the swarm, so dps drops right after a cast until kills rebuild it.

---

### Infantry / Infantry Ⅱ — `FootMan1` (kindNum: 1, 26 evolved)
**Role:** melee dps (basic sword infantry)
**Description (in-game):**
- Normal (`UNIT_NATK_1`): "Strikes nearby enemies with a sword."
- Skill (`UNIT_SATK_1`): "Delivers a powerful strike that damages enemies and has a chance to stun them."
- (`UNIT_SATK_26`, evolved): "Unleashes a powerful strike that deals greater damage and stuns enemies with a higher chance."
**How it works (code):** Basic melee attacker (normal attack via base `attackMain`, objAtk frame 49). `skillMain()` (objSkill frame 127): `doMeleeAttack(target, 2.5 evolved / 1.5 base)` then with chance `0.5 evolved / 0.3 base` applies `stun(60 evolved / 50 base)`.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| skill dmg mult | 1.5 / 2.5 | base / evolved |
| stun chance | 0.3 / 0.5 | base / evolved |
| stun duration | 50 / 60 | ticks, base / evolved |
| normalSize / evolSize | 1.05 / 1.12 | sprite scale |
**Formulas:** n/a (uses base atk).
**Buffs/debuffs applied:** enemy `stun` on skill (chance-gated).
**Δ description vs code:** None — matches. Evolved: higher dmg (2.5 vs 1.5), higher stun chance (0.5 vs 0.3) and longer stun (60 vs 50), exactly as "greater damage / higher chance" implies.

---

### Gunner / Gunner Ⅱ — `Gunner1` (kindNum: 4, 29 evolved)
**Role:** ranged dps (multi-shot gunner with directional firing)
**Description (in-game):**
- Normal (`UNIT_NATK_4`): "Attacks enemies from range with precise shots."
- Skill (`UNIT_SATK_4`): "Fires a powerful projectile that guarantees a stun."
- (`UNIT_SATK_29`, evolved): "Fires an enhanced bullet that guarantees a longer stun on enemies."
**How it works (code):** RANGE, base stats maxHp 100, atkDmg 10, def 10, moveSpd 1.6, atkDuration 20 (fast), atkRange 150. Weapon `Bullet1`. Has 5 directional anim/firepoint sets (`gotoAttackState`/`gotoSkillState` pick frames/firePoint by the angle to target, in 36° bands). `attackMain()` sets `numShot = 1.8 evolved / 1.2 base`, `multiShotDelay=3`, then base multi-shot logic (extra shots are chance-gated by the fractional numShot). Skill (`skillMain`): `generateWeapon(target, Bullet1, 3.5 evolved / 2.5 base)` and **guaranteed** `target.stun(50 evolved / 30 base)`.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| atkDuration | 20 | very fast attack interval |
| atkRange | 150 | |
| numShot | 1.2 / 1.8 | base / evolved (fractional ⇒ chance of extra shot) |
| multiShotDelay | 3 | ticks between staggered shots |
| skill dmg mult | 2.5 / 3.5 | base / evolved |
| skill stun (guaranteed) | 30 / 50 | ticks, base / evolved |
| Bullet1 on-hit stun | 20% × 50t | NORMAL bullets also stun (see Δ) |
**Formulas:** extra-shot chance = fractional part of `numShot` (e.g. 1.8 ⇒ 80% chance of a 2nd shot).
**Buffs/debuffs applied:** enemy `stun` — guaranteed on skill; ALSO 20%/50t on every normal `Bullet1` hit.
**Δ description vs code:** Skill matches ("guaranteed stun", evolved longer: 50 vs 30, and higher dmg). DELTA on normal: the description says only "precise shots" with no stun, but the `Bullet1` weapon's `onHitMain` applies `stun(50)` at 20% on EVERY normal hit (`random.chance(.2)&&target.stun(50)`). So Gunner's basic attack already has an undocumented 20% stun chance.

---

### Heavy Armor / Heavy Armor Ⅱ — `HeavyWarrior1` (kindNum: 2, 27 evolved)
**Role:** tank (self power-shield on skill)
**Description (in-game):**
- Normal (`UNIT_NATK_2`): "Attacks nearby enemies with a melee strike."
- Skill (`UNIT_SATK_2`): "After attacking, deploys a power shield that blocks almost all physical and magic damage for a period of time."
- (`UNIT_SATK_27`, evolved): "After attacking, deploys a Power Shield that blocks nearly all physical and magical damage for a set duration."
**How it works (code):** Tanky base stats maxHp 150, atkDmg 3 (low), def 10, moveSpd 2.6, atkDuration 200 (slow), atkRange 8. `skillMain()`: `doMeleeAttack(target, 1)` then `showPowerShield(150)`. A Power Shield multiplies all incoming damage by `0.01` (≈1%) for its duration — "blocks almost all" both physical and magical.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| maxHp | 150 | tanky |
| atkDmg | 3 | low (defensive unit) |
| atkDuration | 200 | slow attacker |
| skill dmg mult | 1 | normal-strength hit before shield |
| powerShield duration | 150 | ticks of 1%-damage shield |
| powerShield mult | 0.01 | incoming damage ×0.01 (numPowerShield>0) |
**Formulas:** while shielded: `incomingDamage *= 0.01`.
**Buffs/debuffs applied:** self Power Shield (damage reduction to 1%), 150 ticks. No ally/enemy effects.
**Δ description vs code:** None — matches. "Blocks almost all physical and magic damage" = `c*=.01` applies to both damage types (the 0.01 multiplier is checked before the type-specific physical/magical full-block shields). Base and evolved code are identical here (the same `showPowerShield(150)`); the "Ⅱ" wording is essentially cosmetic — no numeric difference found in code for the shield itself.
**Notes:** Δ: unlike Infantry/HammerKnight, HeavyWarrior shows NO base/evolved branch in `skillMain` — the shield value (150) is the same regardless of evolStage. Evolved benefit comes only from scaled base stats, not the shield.

---

### Hammer Knight / Hammer Knight Ⅱ — `HammerKnight1` (kindNum: 5, 30 evolved)
**Role:** melee dps / off-tank (AoE slam, stun, taunt)
**Description (in-game):**
- Normal (`UNIT_NATK_5`): "Delivers a melee blow with a heavy hammer."
- Skill (`UNIT_SATK_5`): "Slams the ground with great force, dealing AoE damage to nearby enemies, with a chance to stun them and trigger Taunt."
- (`UNIT_SATK_30`, evolved): "Slams a wider area with a powerful strike, dealing heavy damage, stunning enemies with a higher chance, and can activate Taunt."
**How it works (code):** Normal attack via base (objAtk frame 57); `attackMain()` override: evolved only, 10% chance to `showPhysicalShield(50)` (50-tick PHYSICAL immunity). `skillMain()`: with chance `tauntChance` taunt(60); `doMeleeAttack(target, mainMult)`; `target.stun(stunMain)`; then AoE — gathers enemies at a point `aoeRange` ahead via `getEnemiesAtPos`, hits up to 3 with `doDamage(_, 0.3)` and chance-stuns each.
**Hard values:**
| variable | value (base / evolved) | meaning |
|---|---|---|
| taunt chance | 0.3 / 0.35 | chance to taunt(60) at skill start |
| main dmg mult | 1.5 / 2 | primary skill hit on target |
| AoE secondary stun chance | 0.3 / 0.4 | per AoE-hit enemy |
| main-target stun | 50 / 50 | wait—`h=t?60:50` ⇒ 50 base / 60 evolved |
| AoE stun | 50 / 60 | `n=t?60:50` |
| AoE range | 30 / 40 | forward offset & radius |
| AoE dmg mult | 0.3 | each of up to 3 secondary targets |
| AoE max targets | 3 | secondary hit cap |
| evolved physShield | 10% × 50t | on normal attack only (evolved) |
**Formulas:** taunt radius `taunt(60)`; AoE at `(x + range*direction, y)`.
**Buffs/debuffs applied:** enemy `taunt(60)` (chance), `stun` on main target (60 evolved / 50 base) and on AoE targets (chance-gated, 60 evolved / 50 base). Self: evolved 10% `physicalShield(50)` on normal attack (blocks all PHYSICAL for 50t).
**Δ description vs code:** Matches. Evolved: wider AoE (40 vs 30), higher dmg (2 vs 1.5), higher stun chances (0.35/0.4 vs 0.3/0.3) and longer stuns (60 vs 50). Extra (undocumented for normal attack): evolved gains a 10% physical-shield proc on its NORMAL attack, which the descriptions don't mention.

---

### Mounted Knight / Mounted Knight Ⅱ — `HorseKnight1` (kindNum: 6, 31 evolved)
**Role:** melee dps (rapid combo, kill-fed move-speed, periodic taunt)
**Description (in-game):**
- Normal (`UNIT_NATK_6`): "Unleashes a rapid flurry of melee hits on enemies."
- Skill (`UNIT_SATK_6`): "Launches a combo attack that alternates between the main target and nearby enemies. Taunt triggers after a certain number of uses."
- (`UNIT_NATK_31`, evolved normal): "Strikes with rapid melee combos. Killing an enemy grants a movement speed buff."
- (`UNIT_SATK_31`, evolved skill): "Delivers an enhanced combo attack alternating between the main target and nearby enemies. Activates Taunt after a set number of uses."
**How it works (code):** Base stats maxHp 150, atkDmg 3, def 10, moveSpd 2.6, atkRange 8. Normal attack = 3-hit combo (objAtk frames 45,52,61). `onKillEnemy`: `addMoveSpeedBuff(kindNum, 2, 60)` — a +200% move-speed burst for 60 ticks on every kill. Skill (objSkill 6 frames): `onSkillStartFrame` increments `skillUseCount`; every 3rd use ⇒ `taunt(100)`. `skillMain` runs per hit-frame: hit #1 and #6 hit the main target (`doMeleeAttack(target, comboMult)`), the rest hit a nearby enemy (`attackNearbyEnemy`) — alternating main/nearby. comboMult = `1.2 evolved / 1`.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| combo dmg mult | 1 / 1.2 | base / evolved per combo hit |
| onKill move buff value | 2 | +200% move speed |
| onKill buff dur | 60 | ticks |
| taunt cadence | every 3rd skill use | `skillUseCount%3==0` |
| taunt duration | 100 | ticks |
| nearby-search radius | 40 | `attackNearbyEnemy` |
| objAtk (normal) | {45,52,61} | 3-hit flurry |
| objSkill | {100,104,108,112,116,120} | 6 combo strikes |
**Formulas:** kill move buff: `moveSpd = orgMoveSpd*(1+2)` ⇒ ×3 for 60 ticks (buff id = kindNum ⇒ self-stacks as max, refreshes uptime).
**Buffs/debuffs applied:** SELF `addMoveSpeedBuff(kindNum, 2, 60)` on each kill (+200% move, 60t). Enemy `taunt(100)` every 3rd skill cast.
**Δ description vs code:** Matches. The kill→move-speed buff is in the base class too (`onKillEnemy` is unconditional), but the locale only documents it on the EVOLVED normal text (UNIT_NATK_31). So base Mounted Knight ALSO gets the +200% move-speed-on-kill that its base description (UNIT_NATK_6) omits — a documentation delta where the buff is present in base code but only mentioned for the evolved tier. Combo main/nearby alternation and "taunt after N uses" (every 3rd) both match.

---

### Firebird / Firebird Ⅱ — `FireBird1` (kindNum: 3, 28 evolved)
**Role:** ranged dps (long-range flying caster)
**Description (in-game):**
- Normal (`UNIT_NATK_3`): "Soars through the sky and launches flaming shots from extreme range."
- Skill (`UNIT_SATK_3`): "Fires a powerful fireball that deals heavy damage and has a chance to stun enemies."
- (`UNIT_SATK_28`, evolved): "Fires a powerful fireball that deals greater damage and stuns enemies with a higher chance."
**How it works (code):** Air unit (airHeight 75 — "extreme range" flyer), RANGE, weapon `FireBirdBall1`. Normal attack fires the ball (objAtk frame 35). `skillMain()` (objSkill frame 35): `generateWeapon(target, FireBirdBall1, 3.5 evolved / 2.5 base)`, then if target alive, `random.chance(0.5 evolved / 0.3 base)` ⇒ `target.stun(50)`.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| airHeight | 75 | high-flying |
| skill dmg mult | 2.5 / 3.5 | base / evolved |
| skill stun chance | 0.3 / 0.5 | base / evolved |
| skill stun duration | 50 | ticks (same both tiers) |
**Formulas:** n/a.
**Buffs/debuffs applied:** enemy `stun(50)` on skill (chance-gated).
**Δ description vs code:** None — matches. Evolved: greater dmg (3.5 vs 2.5) and higher stun chance (0.5 vs 0.3); stun length 50 unchanged.

---

### Priest / Priest Ⅱ — `Priest1` (kindNum: 55, 56 evolved)
**Role:** healer / support (AoE heal + hit-blocking shields)
**Description (in-game):**
- Normal (`UNIT_NATK_55`): "Attacks from range with light energy and has a chance to stun enemies."
- Skill (`UNIT_SATK_55`): "Restores HP for all allies and grants them a shield."
- (`UNIT_SATK_56`, evolved): "Greatly restores HP for all allies and grants them an enhanced shield."
**How it works (code):** RANGE, weapon `YellowEnergyBall`. `attackMain()` sets `numShot = 2 evolved / 1.5 base` then base multi-shot. `setData` switches objAtk between OBJ_ATK_1 {39,46} (base, 2 hits) and OBJ_ATK_2 {39,44,49} (evolved, 3 hits). `skillMain()`: (1) cosmetic `showPriestLight(60)`; (2) gathers all alive allies; (3) **shield pass** — sorts allies by distance, takes nearest `SKILL_MAX_TARGETS=20`, calls `showPriestStart(shieldDur, shieldHits)` on each → sets `numPriestShield=shieldDur`, `priestShieldHits=shieldHits` (a shield that fully negates the next `shieldHits` incoming hits while the timer lasts); (4) **heal pass** — sorts allies by HP% ascending (lowest first), takes nearest 20, calls `heal(t, this, true)` where `t = healPct` for normal allies and `t = castlePct` for castles. `heal` with the percent-flag does `health += maxHp*0.01*t` (so `t` is a percent of max HP).
**Hard values:**
| variable | value (base / evolved) | meaning |
|---|---|---|
| ally heal pct | 5 / 10 | % of max HP healed (non-castle) |
| castle heal pct | 0.5 / 1 | % of max HP healed (isCastle) |
| shield duration | 90 / 120 | ticks the shield timer lasts |
| shield hits | 2 / 3 | number of incoming hits fully blocked |
| SKILL_MAX_TARGETS | 20 | max allies shielded / healed |
| numShot | 1.5 / 2 | normal-attack shots (fractional ⇒ chance) |
| objAtk | {39,46} / {39,44,49} | base 2-hit / evolved 3-hit normal |
**Formulas:** heal amount `= maxHp * 0.01 * healPct` (e.g. evolved 10 ⇒ +10% max HP). Shield: while `numPriestShield>0 && priestShieldHits>0`, an incoming hit is fully negated and `priestShieldHits--`; at 0 the shield clears.
**Buffs/debuffs applied:** to nearest ≤20 allies — a hit-blocking shield (`numPriestShield` dur, `priestShieldHits` count) and a % heal. Castles get a much smaller heal %. No enemy debuffs from the skill.
**Δ description vs code:** Heal+shield skill matches well ("greatly restores / enhanced shield" = 10% vs 5%, 3 hits / 120t vs 2 hits / 90t). DELTA on NORMAL attack: the description says it "has a chance to stun enemies," but the `YellowEnergyBall` weapon class has NO `onHitMain` and applies NO stun — the projectile only deals damage (`g=0, speed=8`). There is no stun call anywhere in `Priest1` or in `YellowEnergyBall`. So the documented normal-attack stun does NOT exist in code. (Contrast: `Bullet1`/Gunner does have the stun-on-hit hook.)
**Notes:** Heal targets the LOWEST-HP% allies first; shields target the NEAREST allies first — two different sort orders, both capped at 20. Castle heal % is ~10× smaller than ally heal %.

---

### GriffinRider1 — `GriffinRider1` (kindNum: not in desc.json — newer unit, no localized description)
**Role:** ranged dps (flying multi-target lancer, bouncing skill spears)
**Description (in-game):** none present — no `UNIT_NAME/NATK/SATK` entry for this class.
**How it works (code):** Air unit (airHeight 75), RANGE, weapon `GriffinSpear1`. `onAttackStartFrame`: gathers enemies in the facing direction within atkRange, up to `2 base / 3 evolved` targets (`getEnemiesForDirection`), and front-loads the current target. `attackMain()` cycles `attackIndex` through that target list, `doRangeAttack`-ing one per objAtk frame — so it spreads normal hits across 2 (base) / 3 (evolved) enemies. Skill (objSkill frames 152,170,188 — 3 casts): `onSkillStartFrame` collects enemies within 220 (target first); `skillMain` fires one `GriffinSuperSpear1` per cast at the next skill target via `fireSkillArrow`, with damage mult 1.5 and `bounceCount = this.numBounce` (a bouncing/chaining super-spear). Spear fire offset randomized `35 + 20*random`.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| airHeight | 75 | high-flyer |
| normal targets | 2 / 3 | base / evolved enemies hit per attack |
| skill collect radius | 220 | enemies gathered for super-spear |
| skill spear dmg mult | 1.5 | per `GriffinSuperSpear1` |
| skill spear bounces | `numBounce` | inherited bounce/chain count of super-spear |
| objSkill | {152,170,188} | 3 super-spear casts per skill anim |
**Formulas:** normal attack distributes across `min(targetsInDir, 2|3)` enemies, one per objAtk frame.
**Buffs/debuffs applied:** none confirmed in this class body (super-spear bounce/freeze, if any, lives in the `GriffinSuperSpear1` weapon, not here). No ally buffs.
**Δ description vs code:** No in-game description to compare. Behaviorally similar to a Wyvern/Raptor-style multi-target flyer with a bouncing super-spear finisher; evolved adds one more normal-attack target (3 vs 2).
**Notes:** Base/evolved difference is the normal-attack target count (2→3). The skill fires 3 bouncing super-spears regardless of tier.
