# EF2 unit mechanics — Part 1 (12 undead/dark-faction classes)

Bundle: `runtime/bundles/mounted/1.11.42/assets/index.js` (v1.11.42).
Base class `qQ`. `numShot` semantics (from base `attackMain`): the unit always hits its primary
target once; if `numShot>1` it then tries `ceil(numShot-1)` additional nearby enemies, each struck
with probability equal to the running remainder `t` (starts at `numShot-1`, decremented by 1 per
extra target). So `numShot=1.3` ⇒ 1 guaranteed + 30% for a 2nd; `numShot=2.5` ⇒ 2 guaranteed extra
+ 50% for a 3rd. Works for both melee (`doMeleeAttack`) and ranged (`doRangeAttack`); ranged extras
are delayed by `multiShotDelay*(1+e)`.

---

### Wolf — `NWolf` (kindNum: 1001)
**Role:** basic enemy / summoned melee
**Description (in-game):**
- Normal (`UNIT_NATK_1001`): "None"
- Skill (`UNIT_SATK_1001`): "Special Skill"  (placeholder — no real skill text)
**How it works (code):** Trivial melee attacker. `initializeData()` only sets geometry, anim frames,
and sounds — `objAtk={54:1}` (hit fires on attack-frame 54), `attackFrames=skillFrames=QK(40,69)`.
No `hasSkill`, no `setData` override, no `attackMain`/`skillMain` override, so it inherits the base
melee attack with `numShot=1` (single target). This is the plain gray wolf (the Ice Wolf is a
separate class `IceWolf`, kindNum 1003). Used as the Wolf Rider's summon and as a basic mob.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| radius | 13 | body radius |
| hitHeight / hitWidth | 20 / 15 | hitbox |
| objAtk | {54:1} | 1 hit on attack-frame 54 |
| setSize | 0.9 | render scale |
**Formulas:** n/a (inherits base melee).
**Buffs/debuffs applied:** none.
**Δ description vs code:** none — there is no description to contradict (placeholder text only).
**Notes:** No skill, no evolStage handling. Pure stat-block unit; all numbers (HP/ATK/DEF) come from
unit data, not hard-coded here (contrast SkeletonX1 below).

---

### Dark Mage / Dark Mage Ⅱ — `BlackMage1` (kindNum: 14, 39 evolved)
**Role:** ranged dps (mage)
**Description (in-game):**
- Normal (`UNIT_NATK_14`): "Attacks enemies from range with dark bullets."  (Ⅱ `UNIT_NATK_39`: "Unleashes dark projectiles at an increased fire rate for ranged attacks.")
- Skill (`UNIT_SATK_14`): "Fires a dark orb that deals massive damage to enemies."  (Ⅱ `UNIT_SATK_39`: "Launches a dark orb that deals even greater damage to enemies.")
**How it works (code):** Ranged mage. Normal attack fires `BlackMageBall1` projectiles (`weaponClass`),
hit on `objAtk={62:1}`. `setData` sets `numShot=1.3` when evolved (evolStage≥1) else `1` — so the
evolved version has a 30% chance to splash a 2nd nearby enemy per shot (NOT a literal fire-rate
change). Skill (`hasSkill`, fires on skill-frame `objSkill={103:1}`) calls
`generateWeapon(this.target, DarkMageDarkBall1, mult)` with damage multiplier `2` evolved / `1.5`
base — a single heavy dark orb at the current target.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| weaponClass | BlackMageBall1 | normal-attack projectile |
| numShot (base / evolved) | 1 / 1.3 | extra-target multiplier (evolved: +30% chance 2nd target) |
| skill projectile | DarkMageDarkBall1 | skill orb |
| skill dmg mult (base / evolved) | 1.5 / 2 | doDamage multiplier on the orb |
| objAtk / objSkill | {62:1} / {103:1} | hit frames |
| firePoint | (16,-2) | muzzle offset |
**Formulas:** skill damage = base ATK × `1.5` (base) or `× 2` (evolved).
**Buffs/debuffs applied:** none.
**Δ description vs code:** none — matches. The "increased fire rate" wording for the evolved normal
attack is realized in code as a `numShot` multi-target bump (1→1.3), not an `atkSpd` change; worth
noting the flavor text ("fire rate") differs from the mechanism (extra target chance).
**Notes:** Skill targets only `this.target` (single orb), despite "enemies" plural in the text.

---

### Graveyard Hero — `SkeletonX1` (kindNum: 1002)
**Role:** basic / summoned melee (fixed stat-block)
**Description (in-game):**
- Normal (`UNIT_NATK_1002`): "None"
- Skill (`UNIT_SATK_1002`): "Special Skill"  (placeholder)
**How it works (code):** Trivial melee skeleton with **hard-coded base stats baked into the class**
(unique among these 12): `baseMaxHp=100`, `maxHp=hp=100`, `atkDmg=10`, `def=10`, `moveSpd=1.6`,
`atkDuration=200`, `atkRange=8`. No `hasSkill`, no `setData`, no attack/skill override → inherits
base single-target melee. This is the "Graveyard Hero" summon (e.g. revived/raised skeleton with a
fixed kit), which is why its stats are constants here rather than data-driven.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| baseMaxHp / maxHp / hp | 100 | health |
| atkDmg | 10 | attack damage |
| def | 10 | defense |
| moveSpd | 1.6 | move speed |
| atkDuration | 200 | ticks between attacks (atkSpd = 1e4/200 = 50) |
| atkRange | 8 | melee range |
| objAtk | {58:1} | hit on attack-frame 58 |
**Formulas:** atkSpd = 1e4 / atkDuration = 1e4/200 = **50**.
**Buffs/debuffs applied:** none.
**Δ description vs code:** none — placeholder description only.
**Notes:** Only class in this set that hard-codes HP/ATK/DEF/moveSpd/atkDuration/atkRange; no
evolStage handling.

---

### Skeleton Soldier / Skeleton Soldier Ⅱ — `SkeletonMan1` (kindNum: 13, 38 evolved)
**Role:** melee dps
**Description (in-game):**
- Normal (`UNIT_NATK_13`): "Attacks nearby enemies using a bone as a weapon."  (Ⅱ `UNIT_NATK_38`: "Attacks enemies with a bone in melee combat.")
- Skill (`UNIT_SATK_13`): "Delivers a heavy strike that deals massive damage and has a chance to stun enemies."  (Ⅱ `UNIT_SATK_38`: "Delivers a powerful heavy strike for massive damage with a high chance to stun.")
**How it works (code):** Melee attacker; normal attack is inherited single-target melee
(`objAtk={58:1}`). Skill (`hasSkill`, `objSkill={102:1}`): `doMeleeAttack(target, mult)` with
multiplier `3` evolved / `2` base, then if the target survives, `random.chance(p) && target.stun(120)`
with stun chance `p=0.15` evolved / `0.05` base, stun = **120 ticks (≈2 s)**.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| skill dmg mult (base / evolved) | 2 / 3 | heavy-strike damage multiplier |
| stun chance (base / evolved) | 0.05 / 0.15 | 5% → 15% on evolve |
| stun duration | 120 | ticks (~2 s) |
| objAtk / objSkill | {58:1} / {102:1} | hit frames |
**Formulas:** skill damage = ATK × `2`/`3`.
**Buffs/debuffs applied:** debuff `stun(120)` on the skill target (conditional, RNG-gated).
**Δ description vs code:** none — matches ("massive damage" + "chance to stun"; evolve raises both
damage 2→3 and stun chance 0.05→0.15, consistent with "high chance to stun").
**Notes:** Stun duration (120) is constant across base/evolved; only the *chance* and *damage* scale.

---

### (basic skeleton) — `SkeletonMan2` (kindNum: not in description set — basic enemy variant)
**Role:** basic enemy melee
**Description (in-game):** No dedicated description entry. Behaviorally a stripped Skeleton Soldier
(same anims/sounds as SkeletonMan1) with **no skill**; presented as a basic mob, not a hero, so it
has no `UNIT_NATK/SATK` text of its own.
**How it works (code):** Plain single-target melee. Same geometry/sounds as SkeletonMan1
(`SFX_BATTLE_SWORD_ATTACK1`, undead go/die), `objAtk={58:1}`, `attackFrames=skillFrames=QK(45,74)`.
No `hasSkill`, no `objSkill`, no `setData`, no overrides → base melee with `numShot=1`.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| objAtk | {58:1} | 1 hit on attack-frame 58 |
| radius / hitHeight | 7 / 27 | hitbox |
**Formulas:** n/a (inherits base melee).
**Buffs/debuffs applied:** none.
**Δ description vs code:** No matching kindNum description found in `/tmp/unit_desc.json` — this is a
basic enemy skeleton, not a playable hero, so there is nothing to compare. Stated explicitly rather
than forcing a match to 13/38 (those belong to SkeletonMan1, which has the stun skill SkeletonMan2 lacks).
**Notes:** Distinguished from SkeletonMan1 purely by the absence of the heavy-strike/stun skill and
from SkeletonX1 by the absence of hard-coded stats.

---

### Skeleton Warrior / Skeleton Warrior Ⅱ — `SkeletonWarrior1` (kindNum: 16, 41 evolved)
**Role:** melee dps / assassin
**Description (in-game):**
- Normal (`UNIT_NATK_16`): "Strikes enemies with a melee double hit."  (Ⅱ `UNIT_NATK_41`: "Attacks enemies with a melee double-hit.")
- Skill (`UNIT_SATK_16`): "While invisible, unleashes a rapid flurry of attacks that deals multiple hits."  (Ⅱ `UNIT_SATK_41`: "From stealth, unleashes a furious rapid-fire combo that deals massive damage.")
**How it works (code):** Normal attack is a **double hit** — `objAtk={38:1, 41:1}` (two hit frames per
swing). Skill (`hasSkill`, `objSkill={63:1,65:1,67:1,69:1,71:1,73:1}` = **six** hit frames): first
calls `transparent(40)` (go invisible/untargetable for 40 ticks), then if a target exists,
`doMeleeAttack(target, mult)` per skill hit frame with multiplier `1` evolved / `0.9` base; if no
target, returns to idle. So the skill is an invisible 6-hit flurry on one target.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| objAtk | {38:1, 41:1} | double-hit normal (2 hits/swing) |
| objSkill | {63,65,67,69,71,73 → 1 each} | 6-hit skill flurry |
| transparent | 40 | invisibility duration (ticks) during skill |
| skill dmg mult (base / evolved) | 0.9 / 1 | per-hit multiplier |
| normalSize / evolSize | 1 / 1.05 | render scale grows on evolve |
**Formulas:** skill damage = ATK × `0.9`/`1` **per hit**, ×6 hit frames ⇒ ~5.4× / 6× total if all land.
**Buffs/debuffs applied:** self status `transparent(40)` (stealth) during the skill — not a stat buff.
**Δ description vs code:** none — matches: double-hit normal, invisible multi-hit flurry skill. Note
the per-hit multiplier is below 1× (0.9 base); "massive damage" comes from the **6** stacked hits,
not a high single multiplier.
**Notes:** evolStage only changes the per-hit multiplier (0.9→1) and body size (1→1.05); invisibility
duration (40) and hit count (6) are constant.

---

### Great Hammer / Great Hammer Ⅱ — `GreatHammer1` (kindNum: 17, 42 evolved)
**Role:** melee dps (AoE / control)
**Description (in-game):**
- Normal (`UNIT_NATK_17`): "Strikes enemies with a hammer and has a chance to stun them."  (Ⅱ `UNIT_NATK_42`: "Swings a hammer in melee combat with a chance to stun enemies.")
- Skill (`UNIT_SATK_17`): "Delivers a heavy strike that deals massive damage, inflicts AoE damage on nearby enemies, and has a chance to stun them."  (Ⅱ `UNIT_SATK_42`: "Strikes with devastating power, dealing heavy damage over a wider area with a high chance to stun.")
**How it works (code):** Normal attack (`attackMain`) does base melee, then if target alive,
`random.chance(p) && target.stun(d)` with `p=0.4`/`d=40` evolved, `p=0.2`/`d=30` base — a built-in
chance-to-stun on every normal hit. Skill (`objSkill={109:1}`): `doDamage(target, mult)` with
`mult=2` evolved / `1.5` base on the main target, then `getEnemiesWithin(80, true)` and for each
(excluding the main target) `doDamage(e, 0.7/0.5)` and `random.chance(0.6) && e.stun(60)`, capped at
**5 secondary enemies** (`s>4 → return`).
**Hard values:**
| variable | value | meaning |
|---|---|---|
| normal stun chance (base / evolved) | 0.2 / 0.4 | per normal hit |
| normal stun dur (base / evolved) | 30 / 40 | ticks |
| skill main dmg mult (base / evolved) | 1.5 / 2 | main-target multiplier |
| skill AoE dmg mult (base / evolved) | 0.5 / 0.7 | per secondary enemy |
| skill AoE radius | 80 | `getEnemiesWithin(80,true)` |
| skill AoE stun chance | 0.6 | per secondary enemy |
| skill AoE stun dur | 60 | ticks |
| skill max secondary targets | 5 | loop breaks after s>4 |
| objAtk / objSkill | {71:1} / {109:1} | hit frames |
**Formulas:** main skill dmg = ATK×`1.5`/`2`; AoE dmg = ATK×`0.5`/`0.7` to ≤5 nearby enemies.
**Buffs/debuffs applied:** debuffs only — `stun` on normal hit (0.2/0.4 chance, 30/40t) and on each
AoE skill enemy (0.6 chance, 60t).
**Δ description vs code:** none — matches. Note the AoE stun (radius 80, chance 0.6, 60t, ≤5 targets)
is constant across base/evolved; "higher chance to stun" on evolve refers to the **normal-attack**
stun (0.2→0.4) and the main-skill stun is actually the AoE 0.6 (unchanged) — the evolve scaling is on
damage and the normal-hit stun, not the skill's AoE stun.

---

### Ghost / Ghost Ⅱ — `Ghost1` (kindNum: 15, 40 evolved)
**Role:** ranged dps (mage, flying)
**Description (in-game):**
- Normal (`UNIT_NATK_15`): "Attacks enemies from range with a spirit orb."  (Ⅱ `UNIT_NATK_40`: "Hurls ghost orbs at an increased fire rate for ranged attacks.")
- Skill (`UNIT_SATK_15`): "Becomes invisible and avoids enemy targeting for a certain period of time."  (Ⅱ `UNIT_SATK_40`: "Turns invisible for a longer duration, evading enemy attacks.")
**How it works (code):** Flying (`isAir=true`, `airHeight=40`) ranged attacker firing `GhostBall1`
(`unitType=RANGE`, `objAtk={60:1}`). `setData` sets `this.evolved = evolStage>=1`. `attackMain`
sets `numShot=1.3` **only when evolved** (then calls base attack) — evolved adds a 30% chance to hit
a 2nd nearby enemy per orb. Skill (`objSkill={60:1}`) is just `transparent(d)` with `d=90` evolved /
`70` base — pure invisibility/untargetable window, no damage.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| weaponClass | GhostBall1 | orb projectile |
| isAir / airHeight | true / 40 | flying unit |
| numShot when evolved | 1.3 | +30% chance 2nd target (base stays 1) |
| skill transparent (base / evolved) | 70 / 90 | invisibility ticks |
| normalSize / evolSize | 0.85 / 0.95 | render scale |
| objAtk / objSkill | {60:1} / {60:1} | hit frames |
**Formulas:** n/a (skill deals no damage).
**Buffs/debuffs applied:** self status `transparent(70/90)` (stealth) — not a stat buff.
**Δ description vs code:** none — matches. The evolved "increased fire rate" normal is again
implemented as `numShot` 1→1.3 (extra-target chance), not an `atkSpd` increase.
**Notes:** Invisibility is the entire skill (no offense); evolve extends it 70→90t and adds the
multi-target normal.

---

### Dark Sorcerer / Dark Sorcerer Ⅱ — `DarkMage1` (kindNum: 18, 43 evolved)
**Role:** ranged dps + summoner / support
**Description (in-game):**
- Normal (`UNIT_NATK_18`): "Fires dark projectiles from a distance and periodically summons skeleton soldiers."  (Ⅱ `UNIT_NATK_43`: "Fires dark projectiles at an increased fire rate. Periodically summons a skeleton soldier.")
- Skill (`UNIT_SATK_18`): "Curses enemies, grants a shield to allies, and summons skeletons."  (Ⅱ `UNIT_SATK_43`: "Curses more enemies, shields more allies, and summons skeletons to fight at your side.")
**How it works (code):** Multi-role caster. Normal attack fires `DarkMageBall1`; `numShot` =
`NUM_SHOT_2=2.5` evolved / `NUM_SHOT_1=1.5` base (so base hits 1 guaranteed extra + 50% for a 2nd;
evolved hits 2 extra + 50% for a 3rd). **Skill** (`skillMain`): (1) gathers `getAttackableEnemyList(i)`
with `i=4` evolved / `3` base, fires `DarkMageSkillBall1` at the first, and `curse(180)` on **every**
enemy in that list; (2) shields `s` random alive allies (`s=2` evolved / `1` base) via
`showPowerShield(120)`; (3) calls `trySummonSkeleton()`. **Passive summon** (`execute` increments
`summonCooldownTimer` & `reviveEnergy` each tick): every `SUMMON_COOLDOWN=1000` ticks, summons a
skeleton (`SKELETON_KIND_NUM=13`) for `1300` (evolved) / `1000` ticks, tinted `16746632`. **Revive
passive** (`onKillEnemy`): if the killed enemy is `grade<=2`, not air, not summoned, and
`reviveEnergy >= REVIVE_ENERGY` (`220` evolved / `350` base), then with chance `0.2` evolved / `0.1`
base, resurrects a copy of that enemy as an ally (`summonUnitSync(reviveVO, REVIVE_DURATION=600, 0)`,
placed at the corpse, `revive()`, `initDelay=8`).
**Hard values:**
| variable | value | meaning |
|---|---|---|
| numShot (NUM_SHOT_1 / NUM_SHOT_2) | 1.5 / 2.5 | base / evolved normal multi-target |
| skill curse targets (base / evolved) | 3 / 4 | `getAttackableEnemyList(i)` |
| curse duration | 180 | ticks on each listed enemy |
| skill shield count (base / evolved) | 1 / 2 | random allies shielded |
| showPowerShield | 120 | ally shield duration (ticks) |
| skill projectile | DarkMageSkillBall1 | at list[0], mult 1.5 |
| SUMMON_COOLDOWN | 1000 | ticks between passive skeleton summons |
| summon duration (base / evolved) | 1000 / 1300 | summoned skeleton lifetime |
| SKELETON_KIND_NUM | 13 | summons a Skeleton Soldier |
| REVIVE_ENERGY (NORMAL / EVOLVED) | 350 / 220 | kill-energy threshold to enable revive |
| revive chance (base / evolved) | 0.1 / 0.2 | per qualifying kill |
| REVIVE_DURATION | 600 | revived ally lifetime (ticks) |
| tint | 16746632 | orange tint on summons/revives |
**Formulas:** skill orb dmg = ATK×`1.5`. Revive gate: `reviveEnergy` (+1/tick) must reach 350/220 and
reset to 0 on a successful revive.
**Buffs/debuffs applied:** debuff `curse(180)` on up to 3/4 enemies (skill); ally buff
`showPowerShield(120)` on 1/2 random allies (skill). Summons skeleton (kind 13) on a 1000-tick timer;
conditionally revives slain enemies as allies.
**Δ description vs code:** none — matches all three skill clauses (curse / ally shield / summon) plus
the passive summon. The **revive passive** ("summons skeletons" can be read as the resurrection of
defeated enemies) is an extra mechanic beyond the literal skill text; evolve broadens it (lower energy
threshold 350→220, higher chance 0.1→0.2) consistent with "more enemies / more allies / skeletons to
fight at your side." Skill curse hits the *whole* attackable list (3/4), but the skill **orb** only
hits list[0].
**Notes:** Only enemies of `grade<=2` (non-air, non-summoned) can be revived; revived/summoned units
share the orange tint `16746632` and `initDelay=8`.

---

### Dark Archer / Dark Archer Ⅱ — `DarkArcher1` (kindNum: 57, 58 evolved)
**Role:** ranged dps (multi-target / control + summoner)
**Description (in-game):**
- Normal (`UNIT_NATK_57`): "Fires silence-infused arrows to hit multiple enemies at once. Defeated enemies have a chance to revive as allied soldiers."  (Ⅱ `UNIT_NATK_58`: "Fires silence-infused arrows to hit more enemies at once. Defeated enemies have a higher chance to revive as allied soldiers.")
- Skill (`UNIT_SATK_57`): "Fires an enhanced arrow that deals heavy damage to multiple enemies and applies a long silence."  (Ⅱ `UNIT_SATK_58`: "Fires an enhanced arrow that hits even more enemies with heavy damage and an even longer silence.")
**How it works (code):** Normal attack is **multi-target with silence**. On `onAttackStartFrame` it
builds `targetList = getEnemiesForDirection(direction, atkRange, n)` with `n=3` evolved / `2` base
(ensuring the current `target` is first). `objAtk` switches to `OBJ_ATK_2={80:1,87:1,94:1}` (3 hit
frames) when evolved else `OBJ_ATK_1={80:1,90:1}` (2 frames); each hit `attackMain` pops the next
target, does `doRangeAttack(i)` and `i.silence(t)` with silence `t=40` evolved / `30` base.
**Skill** (`objSkill={132:1}`): shows `DarkArcherSkillEffect1`, then `getAttackableEnemyList(n)` with
`n=5` evolved / `3` base, and for each enemy `doDamage(e, mult)` (`mult=2` evolved / `1.5` base) +
`silence(i)` with `i=150` evolved / `90` base (long silence). **Summon passive** (`onKillEnemy`,
`summonEnergy` +1/tick): if killed enemy `grade<=3`, not air, not summoned, and
`summonEnergy >= SUMMON_ENERGY` (`150` evolved / `250` base), then with chance `0.3` evolved / `0.15`
base, revives a copy of it as an ally (`summonUnitSync(skeletonVO, SKELETON_DURATION=600, 0)`, at the
corpse, `revive()`, tint `16746632`, `initDelay=8`).
**Hard values:**
| variable | value | meaning |
|---|---|---|
| normal targets n (base / evolved) | 2 / 3 | enemies in firing arc |
| objAtk (OBJ_ATK_1 / OBJ_ATK_2) | {80,90} / {80,87,94} | 2 / 3 hit frames |
| normal silence (base / evolved) | 30 / 40 | ticks per normal hit |
| skill targets (base / evolved) | 3 / 5 | `getAttackableEnemyList(n)` |
| skill dmg mult (base / evolved) | 1.5 / 2 | per skill target |
| skill silence (base / evolved) | 90 / 150 | ticks (long silence) |
| SUMMON_ENERGY (NORMAL / EVOLVED) | 250 / 150 | kill-energy threshold |
| revive chance (base / evolved) | 0.15 / 0.3 | per qualifying kill |
| SKELETON_DURATION | 600 | revived ally lifetime (ticks) |
| objSkill | {132:1} | skill hit frame |
**Formulas:** skill dmg = ATK×`1.5`/`2` per target.
**Buffs/debuffs applied:** debuff `silence` on every normal-hit target (30/40t) and every skill target
(90/150t). Conditionally revives slain enemies (grade≤3) as allies on kill.
**Δ description vs code:** none — matches: multi-target silence arrows, kill-revive passive, heavy
multi-target silence skill. Evolve scales every axis (targets 2→3 / 3→5, silence 30→40 / 90→150, dmg
1.5→2, revive energy 250→150, revive chance 0.15→0.3), consistent with "more enemies / longer silence
/ higher revive chance."
**Notes:** Revive grade gate (≤3) is **looser** than DarkMage1's (≤2). Both use the same orange tint
`16746632` and `initDelay=8` for revived units.

---

### Bomber / Bomber Ⅱ — `Bomber1` (kindNum: 68, 77 evolved)
**Role:** ranged dps (AoE bomber, self-buff)
**Description (in-game):**
- Normal (`UNIT_NATK_68`): "Throws multiple small bombs for ranged attacks. After defeating a certain number of enemies, enters a frenzy state."  (Ⅱ `UNIT_NATK_77`: "Throws more small bombs for ranged attacks. After defeating a certain number of enemies, enters a stronger frenzy state.")
- Skill (`UNIT_SATK_68`): "Detects the densest enemy cluster and drops 2 large bombs on that location."  (Ⅱ `UNIT_SATK_77`: "Detects the densest enemy cluster and drops 3 large bombs on the location.")
**How it works (code):** Normal attack throws `BomberSmallBomb1` with `numShot` = `NUM_SHOT_2=5`
evolved / `NUM_SHOT_1=3` base (3 or 5 small bombs / multi-target). `maxMana=700`. **Skill**
(`skillMain`, fires when `currentFrame==100`): drops large bombs `BomberBigBomb1` — count `2` evolved
(`t?3:2`) wait, **count = 3 evolved / 2 base** — on the most-clustered enemies. It collects all alive
enemies within a 220×220 box of itself (`|dx|<=220 && |dy|<=220`), shuffles them, then builds the bomb
list starting with the current `target` and filling up to `count` extra; each big bomb is staggered by
`delay = 26 + 5*e`. Uses separate fire points: `firePointNormal=(4,-36)`, `firePointSkill=(2,-60)`.
**Frenzy self-buff** (`onKillEnemy`): increments `killCount`; every **7 kills** it resets and applies
`addAttackSpeedBuff(Bomber1_ATKSPD_BUFF=200, val, dur)` + `addMoveSpeedBuff(Bomber1_MOVESPD_BUFF=201,
val, dur)` with `val=1.1`/`dur=240` evolved, `val=0.8`/`dur=200` base, plus an `Accelerate` effect.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| numShot (NUM_SHOT_1 / NUM_SHOT_2) | 3 / 5 | small bombs per attack (base / evolved) |
| maxMana | 700 | mana pool |
| skill big-bomb count (base / evolved) | 2 / 3 | `BomberBigBomb1` dropped |
| skill detect box | 220×220 | half-extent for clustering (|dx|,|dy| ≤ 220) |
| big-bomb stagger | 26 + 5·e | delay (ticks) for the e-th bomb |
| frenzy kill threshold | 7 | kills to trigger self-buff |
| Bomber1_ATKSPD_BUFF id | 200 | attack-speed buff id |
| Bomber1_MOVESPD_BUFF id | 201 | move-speed buff id |
| frenzy buff value (base / evolved) | 0.8 / 1.1 | +80% / +110% |
| frenzy buff duration (base / evolved) | 200 / 240 | ticks |
| firePoint normal / skill | (4,-36) / (2,-60) | muzzle offsets |
| objAtk / objSkill | {62:1} / {100:1} | hit frames |
**Formulas:** atkSpd = orgAtkSpd × (1 + `0.8`/`1.1`) ⇒ **+80% / +110%** during frenzy;
moveSpd = orgMoveSpd × (1 + `0.8`/`1.1`) ⇒ same. Both expire after 200/240 ticks.
**Buffs/debuffs applied:** self buffs only — `addAttackSpeedBuff(id 200, 0.8/1.1, 200/240)` and
`addMoveSpeedBuff(id 201, 0.8/1.1, 200/240)` every 7 kills (the "frenzy").
**Δ description vs code:** none — matches: multi small bombs, kill-count frenzy (every 7 kills), and
the cluster-detect big-bomb skill (2/3 bombs). Note the buff value is *additive percent* per the
buff-id convention; the two buffs use **distinct ids** (200, 201) so they don't collide with each
other, and same-id buffs from multiple Bombers wouldn't stack (max kept).
**Notes:** `killCount` is class state, not reset by the skill; frenzy is a passive on-kill effect
independent of the skill cooldown.

---

### Hand of Death / Hand of Death Ⅱ — `DeathHand1` (kindNum: 63, 72 evolved)
**Role:** melee dps (knockback / launcher, AoE control)
**Description (in-game):**
- Normal (`UNIT_NATK_63`): "Delivers a melee attack with a powerful fist that knocks enemies back."  (Ⅱ `UNIT_NATK_72`: same text.)
- Skill (`UNIT_SATK_63`): "Unleashes consecutive AoE attacks forward, launching multiple enemies into the air."  (Ⅱ `UNIT_SATK_72`: "Strikes forward with consecutive attacks in a wider area, launching multiple enemies even higher into the air.")
**How it works (code):** Big melee bruiser (`sheetName="Game1"`, `hitHeight=48`, `radius=12`). **Normal**
(`attackMain`): `doMeleeAttack(target)`, then `target.knockBack(direction*i, 0, s)` with `i=3`/`s=15`
evolved, `i=2`/`s=12` base; additionally finds enemies near a point `e` units ahead
(`getEnemiesWithPos(x+e*dir, y, e)`, `e=40`/`30` evolved/base) and knocks each of them back too — so
the normal hit is a small forward-AoE knockback. **Skill** (`skillMain`, 3-stage on frames per
`objSkill={63:1,66:1,68:1}`): for stage h (0,1,2 keyed off currentFrame 63/66/68), targets a box at
`x + (40+40·h)·dir` (i.e. progressively farther forward), radius `i=65` evolved / `55` base, and does
`doDamage(u, 1)` + `u.blow(direction*s, e)` (launch into the air) on up to `n+1` enemies (`n=7`
evolved / `4` base), with blow horizontal `s=4`/`3` and vertical `e=-4.2`/`-3.5` (more negative =
higher launch). Spawns `DeathHandSkillEffect1` at each stage.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| normal knockback dist `i` (base / evolved) | 2 / 3 | × direction |
| normal knockback `s` (base / evolved) | 12 / 15 | knockback param |
| normal forward-AoE reach `e` (base / evolved) | 30 / 40 | radius ahead for extra knockbacks |
| skill stages | 3 | currentFrame 63/66/68 → h=0,1,2 |
| skill box offset | 40 + 40·h | forward distance per stage (×dir) |
| skill radius `i` (base / evolved) | 55 / 65 | per-stage AoE radius |
| skill max targets `n` (base / evolved) | 4 / 7 | loop breaks after c>n |
| skill dmg mult | 1 | `doDamage(u, 1)` (flat, both stages) |
| skill blow horiz `s` (base / evolved) | 3 / 4 | `blow(dir*s, e)` |
| skill blow vert `e` (base / evolved) | -3.5 / -4.2 | launch height (more neg = higher) |
| objAtk / objSkill | {45:1} / {63,66,68} | hit frames |
| normalSize / evolSize | 1 / 1.1 | render scale |
**Formulas:** skill damage = ATK×`1` per hit, across 3 stages; launch vertical velocity `-3.5`/`-4.2`.
**Buffs/debuffs applied:** debuffs only — `knockBack` on normal hits, `blow` (air-launch) on skill
targets. No stat buffs.
**Δ description vs code:** none — matches: knockback fist normal + 3-stage forward AoE launch skill.
Evolve widens every dimension (radius 55→65, targets 4→7, launch −3.5→−4.2, forward AoE reach 30→40),
consistent with "wider area / launching enemies even higher."
**Notes:** `getEnemiesWithPos` (local override) ignores air units (`h.isAir` skipped) and
untargetable units, so both the normal forward-AoE and the skill only hit grounded enemies.

---

## Cross-cutting notes / deltas summary
- **`numShot` is the "fire rate" of evolved ranged units in flavor text** (BlackMage1, Ghost1) — code
  implements it as a multi-target chance bump (1→1.3), not an `atkSpd` change. DarkMage1 (1.5→2.5)
  and Bomber1 (3→5) use the same field for literal multi-projectile counts.
- **Revive/summon passives** (DarkMage1, DarkArcher1) are energy-gated on-kill mechanics with a
  grade filter (≤2 for DarkMage1, ≤3 for DarkArcher1), shared orange tint `16746632`, `initDelay=8`.
- **No mismatches like the drummer's missing ATK buff** were found in this set — every description
  clause is backed by a code call. The only "extra" mechanics beyond literal skill text are the
  DarkMage1/DarkArcher1 kill-revive passives (which the normal-attack text does mention).
