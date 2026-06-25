# EF2 unit mechanics — Part 4 (12 classes)

Source: `runtime/bundles/mounted/1.11.42/assets/index.js`. Classes registered with `Kt(<var>,"<Name>")`, base class `qQ`. Damage helpers: `doMeleeAttack(target, mult=1)` and `doRangeAttack(target, n=0)` (2nd arg = damage multiplier / extra-shot index). Buff signature `(id, value, durationTicks[, refresh])`. Times are game ticks (~60/s at 1×).

---

### Orc Fighter — `OrcFighter1` (kindNum: 19, 44 evolved)
**Role:** melee dps
**Description (in-game):**
- Normal (`UNIT_NATK_19`): "Attacks enemies with a rapid double melee strike." (evolved `UNIT_NATK_44`: "Attacks enemies with a melee double-hit.")
- Skill (`UNIT_SATK_19`): "Delivers a heavy strike that deals massive damage and knocks enemies back." (evolved `UNIT_SATK_44`: "Strikes with tremendous force, dealing even greater damage and sending enemies flying farther back.")
**How it works (code):** Basic attack is a melee double-hit — `objAtk={51:1,60:1}` fires the hit on two attack-anim frames (51 and 60). The skill (`skillMain`, `objSkill={97:1,105:1}`) calls `doMeleeAttack(target, evolved?2.5:2)` for a high-multiplier blow, then knocks the target back via `target.blow(±k, k)` where `k = evolved?3:2`, sign chosen by whether the target is to the right (`+`) or left (`-`) of the unit. Stats are hard-coded: 150 HP, ATK 3, DEF 10, moveSpd 2.6, atkDuration 200, atkRange 8 (melee).
**Hard values:**
| variable | value | meaning |
|---|---|---|
| baseMaxHp | 150 | base HP |
| atkDmg / def | 3 / 10 | base attack / defense |
| moveSpd | 2.6 | move speed |
| atkDuration | 200 | ticks between attacks |
| atkRange | 8 | melee reach |
| skill damage mult | 2 / 2.5 | base / evolved (`doMeleeAttack`) |
| knockback k | 2 / 3 | base / evolved `blow(±k,k)` |
**Formulas:** skill dmg = atk × 2 (base) / × 2.5 (evolved). Double-hit normal = 2× `objAtk` frames at 1× each.
**Buffs/debuffs applied:** none (knockback is a positional effect, not a buff).
**Δ description vs code:** none — matches. Double-hit normal + heavy-damage + knockback skill; evolved raises mult (2→2.5) and knockback (2→3) ("flying farther back").
**Notes:** evolved gating via `this.evolStage>=1` inside `skillMain` (no cached `evolved` flag here).

---

### Orc Hammerman — `OrcHammer1` (kindNum: 24, 49 evolved)
**Role:** melee dps / summoner (decoy)
**Description (in-game):**
- Normal (`UNIT_NATK_24`): "Attacks enemies in melee with a hammer." (evolved `UNIT_NATK_49`: "Swings a hammer to deal AoE damage to nearby enemies.")
- Skill (`UNIT_SATK_24`): "Summons an ice decoy to draw enemy attacks in your place." (evolved `UNIT_SATK_49`: "Summons an ice clone for a longer duration to take hits in your place.")
**How it works (code):** Normal attack `doMeleeAttack(target,1)` on `objAtk={58:1}`. When **evolved**, the same `attackMain` additionally sweeps for up to **1** extra ground enemy (`s=1` cap) within a 30-unit box centered 30 units ahead (`n=x+direction*30`, radius² = 30²=900) and hits it with `doMeleeAttack(a, 0.7)` — this is the "AoE" of the evolved normal. Skill `summonPhantom(dur)` spawns an `OrcIcePhantom1` decoy via `getUnitSync`, copying the source VO at 0.3 scale-factor (`setData(sourceVo,.3)`), placed at a random angle 40 units away; `summonDuration = evolved?220:180`. The phantom (`OrcIcePhantom1`) just stands and `die()`s when its `summonTimer` reaches 0, drawing aggro meanwhile.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| objAtk frame | 58 | normal hit frame |
| objSkill frame | 99 | summon frame |
| evolved AoE: range / radius | 30 / 30 | ahead-offset / box half-size (radius²=900) |
| evolved AoE: maxTargets | 1 | extra enemies hit |
| evolved AoE: damage mult | 0.7 | secondary-hit multiplier |
| phantom duration | 180 / 220 | ticks, base / evolved |
| phantom setData scale | 0.3 | source-VO scale factor |
| phantom spawn radius | 40 | placement distance |
**Formulas:** evolved secondary hit dmg = atk × 0.7. Phantom lifetime ≈ 180/60≈3.0 s (base), 220/60≈3.7 s (evolved).
**Buffs/debuffs applied:** none (summons a decoy unit).
**Δ description vs code:** none — matches. Evolved "AoE normal" = exactly one extra forward ground hit at 0.7×; evolved decoy lasts longer (180→220 ticks). The decoy's only function is aggro + expiry; it doesn't attack.
**Notes:** caches `this.sourceVo` in `setData` to clone into the phantom; `this.evolved=this.evolStage>=1`.

---

### Orc Hunter — `OrcHunter1` (kindNum: 20, 45 evolved)
**Role:** melee assassin (teleport + freeze + self-evade)
**Description (in-game):**
- Normal (`UNIT_NATK_20`): "Attacks enemies with a melee strike." (evolved `UNIT_NATK_45`: "Attacks enemies with a basic melee strike.")
- Skill (`UNIT_SATK_20`): "Teleports to the farthest enemy, delivers a heavy strike, freezes the target, and grants itself a ranged evasion buff." (evolved `UNIT_SATK_45`: "Teleports to the farthest enemy, delivering a more powerful strike and freezing them for longer. Grants yourself a ranged evasion buff.")
**How it works (code):** Plain melee normal (HP 150, ATK 3, DEF 10, moveSpd 2.6, atkDuration 200, atkRange 8). Skill (`skillMain`, `objSkill={103:1}`): scans `enemyList` for the ground, non-air, targetable enemy with the **largest +x offset** (`e>t`, i.e. farthest ahead) within |dx|≤200, |dy|≤200 AND dx²+dy²<40000; teleports next to it (snaps `this.x` to `target.x ∓ hitWidths`), then `doDamage(target, evolved?3:2)`, `target.freeze(evolved?50:30)`, and `addRangeEvadeChanceBuff(id=1, 0.6, 180)` on itself plus the `OrcHunterEvadeBuff` visual for 180 ticks.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| baseMaxHp / atkDmg / def | 150 / 3 / 10 | base stats |
| moveSpd / atkDuration / atkRange | 2.6 / 200 / 8 | melee stats |
| search box | |dx|,|dy| ≤ 200; dist² < 40000 | teleport target gate |
| skill damage mult | 2 / 3 | base / evolved (`doDamage`) |
| freeze duration | 30 / 50 | ticks, base / evolved |
| rangeEvade value | 0.6 | +60% ranged-evade chance (additive) |
| rangeEvade duration | 180 | ticks (~3 s) |
**Formulas:** `rangeEvadeChange = orgRangeEvadeChange + 0.6` (additive ⇒ +60% chance to dodge ranged hits) for 180 ticks. Skill dmg = atk × 2 / × 3.
**Buffs/debuffs applied:** **self** ranged-evade — `addRangeEvadeChanceBuff(OrcHunter1_RANGEEVADE_BUFF=1, 0.6, 180)`. **Target** debuff — `freeze(30/50)`.
**Δ description vs code:** none — matches. Note "farthest enemy" is implemented as farthest **in +x (forward) direction within a 200/√40000 box**, not globally farthest. Evolved bumps dmg (2→3) and freeze (30→50).

---

### Frost Mage / Ice Mage Ⅱ — `OrcIceMage1` (kindNum: 21, 46 evolved)
**Role:** ranged mage (ice)
**Description (in-game):**
- Normal (`UNIT_NATK_21`): "Fires ice magic projectiles to attack enemies from a distance." (evolved `UNIT_NATK_46`: "Fires enhanced ice magic projectiles at an increased fire rate, with a chance to strike additional targets.")
- Skill (`UNIT_SATK_21`): "Fires enhanced freezing projectiles that deal massive damage to enemies." (evolved `UNIT_SATK_46`: "Fires an enhanced freezing projectile that deals heavy damage to enemies.")
**How it works (code):** Ranged unit (`unitType=RANGE`, `weaponClass=OrcIceMageFire1`); normal attack fires that weapon on `objAtk={42:1}`. `setData` sets `numShot = evolStage>=1 ? 1.3 : 1` (the "chance to strike additional targets" — fractional shot count ⇒ ~30% chance of an extra projectile per attack, resolved by the base shot logic). Skill (`skillMain`, `objSkill={68:1}`) fires the enhanced `OrcIceMageFireSkill1` at the target; when **evolved**, it then scans `getAttackableEnemyList(2)` and, for the first non-target enemy, fires a second skill projectile with `random.chance(.5)` (50%).
**Hard values:**
| variable | value | meaning |
|---|---|---|
| objAtk / objSkill frame | 42 / 68 | normal / skill hit frame |
| numShot | 1 / 1.3 | base / evolved (fractional ⇒ ~30% extra shot) |
| evolved 2nd-skill chance | 0.5 | `random.chance(.5)` for extra freeze bolt |
| weaponClass (normal) | OrcIceMageFire1 | projectile |
| weaponClass (skill) | OrcIceMageFireSkill1 | enhanced freeze projectile |
**Formulas:** evolved extra-shot expectation ≈ 0.3 projectiles/attack (numShot 1.3). Evolved skill expected bolts = 1 + 0.5 = 1.5.
**Buffs/debuffs applied:** none directly here (freeze/CC is carried by the `OrcIceMage...` weapon objects, not this class).
**Δ description vs code:** none — matches. The "increased fire rate / additional targets" of the evolved normal is the `numShot 1→1.3` change; the evolved skill's "additional" bolt is a single 50%-chance second projectile at the nearest other enemy.

---

### Orc Spearman — `OrcSpearMan1` (kindNum: none in playable list — basic ranged enemy)
**Role:** basic enemy (ranged, no skill)
**Description (in-game):** no `UNIT_NATK/UNIT_SATK` match in `unit_desc.json` (the playable Orc-faction analog at this slot is the melee line; this class is an internal/enemy spearman minion).
**How it works (code):** Pure ranged auto-attacker. `unitType=RANGE`, `weaponClass=OrcSpearmanSpear1`, throws a spear on `objAtk={51:1}`, `firePoint=(3,-25)`. `hasSkill` is **not** set and there is no `skillMain`/`objSkill`/`attackMain` override — it uses base attack only. Hard stats: 100 HP, ATK 10, DEF 10, moveSpd 1.6, atkDuration 20 (very fast), atkRange 150.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| baseMaxHp | 100 | HP |
| atkDmg / def | 10 / 10 | attack / defense |
| moveSpd | 1.6 | move speed |
| atkDuration | 20 | ticks between shots (fast) |
| atkRange | 150 | ranged reach |
| weaponClass | OrcSpearmanSpear1 | spear projectile |
**Formulas:** atkDuration=20 ⇒ ~3 shots/s at 1×.
**Buffs/debuffs applied:** none.
**Δ description vs code:** No matching playable description (kindNum absent from `unit_desc.json` 1–96). Documented from code only: a fast, low-HP ranged spear-thrower with no skill. Stated explicitly rather than forcing a wrong kindNum.

---

### Orc Wing — `OrcWing1` (kindNum: 22, 47 evolved)
**Role:** ranged dps (flyer)
**Description (in-game):**
- Normal (`UNIT_NATK_22`): "Fires energy projectiles from the air to attack enemies at range." (evolved `UNIT_NATK_47`: "Fires energy projectiles from the air for ranged attacks.")
- Skill (`UNIT_SATK_22`): "Fires enhanced energy projectiles that deal massive damage." (evolved `UNIT_SATK_47`: "Fires an enhanced energy projectile that deals heavy damage.")
**How it works (code):** Air unit (`isAir=true`, `airHeight=75`); ranged, `weaponClass=OrcWingBall1`, normal hit on `objAtk={59:1}`. Skill (`skillMain`, `objSkill={97:1}`): `generateWeapon(target, OrcWingBall1, 2)` — same projectile but the 3rd arg `2` boosts power/damage (the "enhanced energy projectile, massive damage"). Sizes: `normalSize=.85`, `evolSize=.95`.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| objAtk / objSkill frame | 59 / 97 | normal / skill hit frame |
| airHeight | 75 | hover height |
| firePoint | (18, 5−75) | muzzle offset (above) |
| weaponClass | OrcWingBall1 | energy ball (normal + skill) |
| skill power arg | 2 | `generateWeapon(...,2)` enhanced |
| normalSize / evolSize | 0.85 / 0.95 | render scale base / evolved |
**Formulas:** skill projectile = normal `OrcWingBall1` at power level 2 (≈ enhanced damage; exact multiplier lives in the weapon class).
**Buffs/debuffs applied:** none.
**Δ description vs code:** none — matches. Skill is the same projectile at power 2. No mechanical difference between base/evolved skill here beyond size; both fire one enhanced ball.

---

### Orc Axeman — `OrcAxe1` (kindNum: 23, 48 evolved)
**Role:** melee dps (forward AoE + thrown axes)
**Description (in-game):**
- Normal (`UNIT_NATK_23`): "Strikes with an axe in melee and deals AoE damage to enemies ahead." (evolved `UNIT_NATK_48`: "Strikes with an axe in melee, dealing wider AoE damage to enemies ahead.")
- Skill (`UNIT_SATK_23`): "After a melee attack, throws an axe to strike additional enemies. Can also hit airborne enemies." (evolved `UNIT_SATK_48`: "After a melee attack, hurls more axes to strike additional enemies. Can also hit airborne targets.")
**How it works (code):** Normal `attackMain`: `doMeleeAttack(target,1)` on `objAtk={78:1}`, then a forward AoE sweep — box centered `direction*range` ahead (`range = evolved?35:30`, radius² = (evolved?35:30)²) hitting up to `evolved?3:2` extra **ground** enemies at `doMeleeAttack(a, evolved?0.7:0.5)`. Skill `skillMain` (`objSkill={133:1,135:1,137:1}`, three throw frames): first a melee hit on the target, then `getAttackableEnemyList(t+1, false)` (the `false` allows **air** targets) and throws `OrcAxeBall1` at up to `t = evolved?5:3` non-target enemies via `generateWeapon`.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| objAtk frame | 78 | melee hit frame |
| normal AoE: range/radius | 30 / 30 (base), 35 / 35 (evolved) | forward offset / box half-size |
| normal AoE: maxTargets | 2 / 3 | base / evolved extra ground enemies |
| normal AoE: damage mult | 0.5 / 0.7 | base / evolved secondary hit |
| skill throws | 3 / 5 | base / evolved thrown axes (`OrcAxeBall1`) |
| skill target query | `getAttackableEnemyList(t+1,false)` | `false` ⇒ includes airborne |
**Formulas:** normal forward AoE dmg = atk × 0.5 (base) / × 0.7 (evolved), up to 2/3 extra ground targets. Skill = 1 melee + N thrown axes (3/5).
**Buffs/debuffs applied:** none.
**Δ description vs code:** none — matches. "Wider AoE" (evolved) = range/radius 30→35, targets 2→3, mult 0.5→0.7. "Hit airborne enemies" = skill's `getAttackableEnemyList(...,false)` includes air units (the normal AoE explicitly skips `a.isAir`).

---

### BigDrumer (Drums of the Battlefield) — `BigDrumer1` (kindNum: 69, 78 evolved) — worked example, verified
**Role:** support / buffer (no damage)
**Description (in-game):**
- Normal (`UNIT_NATK_69`): "Supports allies by beating a drum instead of attacking." (evolved `UNIT_NATK_78`: same.)
- Skill (`UNIT_SATK_69`): "Temporarily increases ATK, attack speed, and movement speed for all allied heroes." (evolved `UNIT_SATK_78`: "Further boosts ATK, attack speed, and movement speed of all allied heroes for a limited time.")
**How it works (code):** Doesn't attack. `attackMain` is gated by `skillCoolDown` (decremented in `execute`, reset to **500**): gathers all alive `allyList`, sorts by squared distance, and buffs the nearest `min(SKILL_MAX_TARGETS=30, n)` allies with `addAttackSpeedBuff(BUFF_ID=8001, s, dur, true)` and `addMoveSpeedBuff(8001, s, dur, true)`, where `s = evolved?1.3:1.2` and `dur = evolved?400:350`. First cooldown is randomized `500*random.next()` so instances desync. Constructor seeds `skillCoolDown=300`, overwritten to the random value in `setData`.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| skillCoolDown | 500 | ticks between buff pulses (~8.3 s); first pulse `500*random` |
| BUFF_ID | 8001 | shared id for both atkSpd + moveSpd buffs |
| SKILL_MAX_TARGETS | 30 | max allies buffed per pulse |
| buff value s | 1.2 / 1.3 | base / evolved |
| buff duration dur | 350 / 400 | ticks, base / evolved |
| objAtk frame | 48 | drum-beat frame |
**Formulas:** `atkSpd = orgAtkSpd*(1+1.2)` ⇒ **+120%** (base), `*(1+1.3)` ⇒ **+130%** (evolved); same magnitude for moveSpd.
**Buffs/debuffs applied:** **allies (≤30 nearest)** — `addAttackSpeedBuff(8001, 1.2/1.3, 350/400, refresh)` + `addMoveSpeedBuff(8001, 1.2/1.3, 350/400, refresh)`. Both use id 8001.
**Δ description vs code:** **MISMATCH (validated).** Description says it boosts "ATK, attack speed, and movement speed," but the code calls ONLY `addAttackSpeedBuff` + `addMoveSpeedBuff` — there is **no** `addAttackDamageBuff`, so raw ATK is **not** buffed. Confirmed by reading the full `attackMain` (two buff calls only).
**Notes:** Multiple drummers share id 8001 ⇒ per aggregation rule (max value per id) they do **not** stack value, only improve uptime via the `refresh` flag. Static fields verified in bundle: `zt(u0,"BUFF_ID",8001),zt(u0,"SKILL_MAX_TARGETS",30)`.

---

### Wolf Rider — `OrcWolfRider1` (kindNum: 25, 50 evolved)
**Role:** summoner + melee dps + buffer
**Description (in-game):**
- Normal (`UNIT_NATK_25`): "Deals AoE damage to nearby enemies along with a melee attack." (evolved `UNIT_NATK_50`: same.)
- Skill (`UNIT_SATK_25`): "Summons a wolf and grants nearby allies a movement speed and attack speed buff. Activates Taunt after a set number of uses." (evolved `UNIT_SATK_50`: "Increases the number of wolves that can be summoned and strengthens the movement speed and attack speed buffs granted to nearby allies. Activates Taunt after a set number of uses.")
**How it works (code):** Normal `attackMain`: `doMeleeAttack(target)` then a forward AoE — box centered `i` units ahead (`i = evolved?50:40`, radius² = i²) hitting up to `e = evolved?6:4` other enemies at `doDamage(o, evolved?0.8:0.65)`. Skill `skillMain` (`objSkill={58:1}`): increments `skillUseCount`; if current summoned-wolf count < `MAX_WOLVES (2/3)`, summons `WOLF_KIND_NUM=1003` ("Ice Wolf") via `summonUnitSync` with duration `WOLF_DURATION (1200/1500)`, wolf level = `this.level+this.enhance+WOLF_LEVEL_BONUS (6/10)`, scaled `WOLF_SCALE (1.05/1.15)`, with `detectRange` set up; then **every 3rd use** (`skillUseCount%3==0`) calls `taunt(80)` (80-tick taunt) and finally `buffNearbyAllies()`. `buffNearbyAllies`: for allies within radius `i = evolved?90:70` (radius² = i²), `addMoveSpeedBuff(this.kindNum, s, e)` + `addAttackSpeedBuff(this.kindNum, s, e)` with `s = evolved?0.4:0.25`, `e (duration) = evolved?120:100`. `setData` rolls starting mana `250+150*random`.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| WOLF_KIND_NUM | 1003 | summoned unit = "Ice Wolf" |
| WOLF_DURATION_1 / _2 | 1200 / 1500 | wolf lifetime ticks, base / evolved |
| MAX_WOLVES_1 / _2 | 2 / 3 | concurrent wolves, base / evolved |
| WOLF_SCALE_1 / _2 | 1.05 / 1.15 | wolf size, base / evolved |
| WOLF_LEVEL_BONUS_1 / _2 | 6 / 10 | added wolf level, base / evolved |
| normal AoE: range i | 40 / 50 | forward offset & box half-size (radius²=i²) |
| normal AoE: maxTargets e | 4 / 6 | base / evolved extra enemies |
| normal AoE: damage mult | 0.65 / 0.8 | base / evolved secondary hit |
| ally-buff radius | 70 / 90 | base / evolved (radius²) |
| ally-buff value s | 0.25 / 0.4 | +25% / +40% (atkSpd & moveSpd) |
| ally-buff duration e | 100 / 120 | ticks, base / evolved |
| taunt cadence | every 3rd skill | `skillUseCount%3==0`, `taunt(80)` |
| starting mana | 250 + 150·rand | randomized |
**Formulas:** ally `atkSpd = orgAtkSpd*(1+0.25)` ⇒ +25% (base) / `*(1+0.4)` ⇒ +40% (evolved); same for moveSpd. Normal AoE dmg = atk × 0.65 / × 0.8.
**Buffs/debuffs applied:** **nearby allies (radius 70/90)** — `addMoveSpeedBuff(kindNum=25/50, 0.25/0.4, 100/120)` + `addAttackSpeedBuff(kindNum=25/50, 0.25/0.4, 100/120)`; both keyed by `this.kindNum` (so same kindNum ⇒ no stacking, max kept). **Self/enemies** — `taunt(80)` every 3rd skill use.
**Δ description vs code:** none — matches. "Increases number of wolves" = MAX_WOLVES 2→3 and longer duration (1200→1500); "strengthens buffs" = value 0.25→0.4, radius 70→90, duration 100→120, and stronger wolves (level +6→+10, scale 1.05→1.15). The summoned "wolf" is internally kindNum 1003 = "Ice Wolf".
**Notes:** When `battleController instanceof mii` (hero/own-side context) the wolf gets a smaller detectRange (150) and, if on the friendly hero list, full hero treatment (`applyToHero`, hp=maxHp). Taunt fires on skill uses 3, 6, 9, …

---

### Sylphid — `Sylphid1` (kindNum: 90, 94 evolved)
**Role:** ranged dps (shuriken stacker / rage)
**Description (in-game):**
- Normal (`UNIT_NATK_90` / `_94`): "Fires shurikens in rapid succession, and each hit gradually increases attack speed.\nRage: When attack speed reaches its maximum, additional shurikens are fired with each normal attack."
- Skill (`UNIT_SATK_90` / `_94`): "Fire tornados in succession to deal damage to enemies."
**How it works (code):** Ranged, `weaponClass=SylphidShuriken1`, `numBounce=3` (shurikens bounce up to 3×), `maxMana=600`. Normal `attackMain`: `doRangeAttack(target)`, and **while raging** (`rageTimer>0`) also `doRangeAttack(target, 4)` (extra shurikens). On each shuriken landing, `onShurikenHit` (suppressed during rage) bumps `atkStack` up to `ATKSPD_MAX_STACK=25`, sets `stackResetTimer=STACK_BUFF_DUR=600`, and applies `addAttackSpeedBuff(Sylphid1_ATKSPD_STACK=220, atkStack*ATKSPD_PER_STACK, 600, refresh)` — i.e. +0.04 atkSpd per stack. At max stacks (25) it `activateRage()`: `rageTimer=RAGE_DURATION=180`, resets stacks, applies the full `25*0.04=1.0` atkSpd buff for the rage duration, and shows the Accelerate FX. In `execute`, when not raging the stack decays after `stackResetTimer` ticks (full reset to 0); when rage ends, the atkSpd buff is cleared (`addAttackSpeedBuff(220, 0, 1, refresh)`). Skill `skillMain` fires `SylphidTornado1` projectiles (power `i = evolved?1.2:1`): base spawns the tornado on the target plus one "most divergent" (most opposite-direction) target via `findMostDivergentTarget` (gated by `DIVERGE_THRESHOLD=0.7` dot-product), else a random-offset extra; **evolved** adds a 3rd tornado at the next most-divergent target (excluding the first two). If no live target, it scatters `spawnTornadoAtRandomOffset` tornados (2 base / 3 evolved).
**Hard values:**
| variable | value | meaning |
|---|---|---|
| ATKSPD_PER_STACK | 0.04 | +4% atkSpd per stack |
| ATKSPD_MAX_STACK | 25 | max stacks ⇒ +100% atkSpd, triggers rage |
| STACK_BUFF_DUR | 600 | stack buff / reset window (ticks, ~10 s) |
| RAGE_DURATION | 180 | rage length (ticks, ~3 s) |
| DIVERGE_THRESHOLD | 0.7 | dot-product gate for "divergent" tornado target |
| numBounce | 3 | shuriken bounces |
| maxMana | 600 | mana pool |
| rage extra shot | `doRangeAttack(target,4)` | bonus shurikens while raging |
| skill power | 1 / 1.2 | base / evolved tornado strength |
| Sylphid1_ATKSPD_STACK id | 220 | atkSpd buff id |
**Formulas:** `atkSpd = orgAtkSpd*(1 + 0.04*stacks)`; at 25 stacks ⇒ `*(1+1.0)` = **+100%** (×2), which also fires rage. Rage holds the +100% for 180 ticks.
**Buffs/debuffs applied:** **self** atkSpd — `addAttackSpeedBuff(220, 0.04·stacks, 600, refresh)` ramping; on rage, `(220, 1.0, 180, refresh)`; cleared with value 0 when rage ends.
**Δ description vs code:** none — matches. "Each hit increases attack speed" = +0.04/stack (`onShurikenHit`); "max attack speed → additional shurikens" = at 25 stacks rage triggers and normal attacks fire the extra `doRangeAttack(target,4)`. Skill = tornados, evolved fires one more (3 vs 2 max) at 1.2× power. Note: during rage `onShurikenHit` is skipped, so stacks don't accumulate while raging (rage is a fixed 180-tick window).

---

### Forest Guardian — `TigerRider1` (kindNum: 81, 84 evolved)
**Role:** ranged dps (multi-target volley + self speed buff)
**Description (in-game):**
- Normal (`UNIT_NATK_81`): "Fires magic arrows at enemies within range." (evolved `UNIT_NATK_84`: "Fires magic arrows at more enemies within range.")
- Skill (`UNIT_SATK_81`): "Attacks multiple enemies at once with a barrage of arrows, and has a chance to grant itself a Speed Up buff." (evolved `UNIT_SATK_84`: "Attacks multiple enemies at once with a volley of arrows, and has a chance to grant itself an enhanced Speed buff.")
**How it works (code):** Ranged, `weaponClass=TigerRiderArrow1`. Direction-aware animation: `selectDirectionFrames` swaps 5 attack/skill frame sets + fire points by the firing angle (`atan2`). Normal: `onAttackStartFrame` builds `targetList = getAttackableEnemyList(NUM_ATK_TARGETS = evolved?4:3)` with the current target forced to the front; `attackMain` fires one arrow per call, cycling `attackIndex` through the list (`doRangeAttack`). Skill: `gotoSkillState` sets `mana=0` and, with `random.chance(.5)` (50%), self-buffs `addAttackSpeedBuff(TigerRider1_ATKSPD_BUFF=210, s, dur)` + `addMoveSpeedBuff(TigerRider1_MOVESPD_BUFF=211, s, dur)` where `s = evolved?1.1:0.8`, `dur = evolved?300:240`, plus the Accelerate FX. `onSkillStartFrame` collects `getEnemiesWithin(220, true)` into `skillTargetList`; `skillMain` fires N skill arrows (`fireSkillArrow`, bounceCount=`numBounce`): N = base `random.chance(.7)?2:1`; evolved `rand<.3?3 : rand<.75?2 : 1`.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| NUM_ATK_TARGETS_1 / _2 | 3 / 4 | normal-attack target count, base / evolved |
| BUFF_VALUE_1 / _2 | 0.8 / 1.1 | self atkSpd & moveSpd buff value, base / evolved |
| BUFF_DURATION_1 / _2 | 240 / 300 | self-buff duration ticks, base / evolved |
| self-buff chance | 0.5 | `random.chance(.5)` per skill cast |
| skill arrows (base) | 1 or 2 | 70% → 2, else 1 |
| skill arrows (evolved) | 1/2/3 | rand<.3→3, <.75→2, else 1 |
| skill target query | `getEnemiesWithin(220,true)` | 220-radius volley pool |
| ATKSPD/MOVESPD buff ids | 210 / 211 | distinct ids (sum, not max) |
| weaponClass | TigerRiderArrow1 | arrow (normal + skill) |
**Formulas:** self `atkSpd = orgAtkSpd*(1+0.8)` ⇒ +80% (base) / `*(1+1.1)` ⇒ +110% (evolved); same magnitude moveSpd. Because atkSpd (210) and moveSpd (211) use distinct ids they don't interfere.
**Buffs/debuffs applied:** **self** (50% per skill) — `addAttackSpeedBuff(210, 0.8/1.1, 240/300)` + `addMoveSpeedBuff(211, 0.8/1.1, 240/300)`.
**Δ description vs code:** none — matches. "Fires magic arrows at more enemies" (evolved) = NUM_ATK_TARGETS 3→4; "barrage/volley" = 1–2 (base) / 1–3 (evolved) skill arrows; "chance to grant itself a Speed Up" = the 50% self atkSpd+moveSpd buff; "enhanced Speed buff" (evolved) = value 0.8→1.1, duration 240→300. (Structurally near-identical to `Unicorn1`/Unicorn Archer, but Unicorn1 has NO self-buff — that self-buff is the distinguishing Forest-Guardian trait.)

---

### Druid (Druid2) — `Druid2` (kindNum: none — stub/placeholder ranged unit)
**Role:** ranged (stub — no functional skill); registered support-line class with an empty skill
**Description (in-game):** no matching `UNIT_NATK/UNIT_SATK` in `unit_desc.json`. ("Druid" is an internal class name; no `Druid` display string exists in the locale.)
**How it works (code):** Minimal ranged unit. `unitType=RANGE`, `sheetName="Game1"`, `firePoint=(14,-14)`, `objAtk={76:1}`, `objSkill={112:1}`, `hasSkill=true`, but: `attackMain` is just `this.target&&this.target.isAlive&&this.doRangeAttack(this.target)` (a single default ranged hit — **and note no `weaponClass` is assigned** in `initializeData`), and `skillMain` is the **dead expression** `this.target&&this.target.isAlive;` — it evaluates the truthiness and does nothing else (no damage, no buff, no projectile). It is only referenced in the className→class map (`[fx.Druid2]:v2`); no static constants, no kindNum wiring.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| objAtk / objSkill frame | 76 / 112 | animation hit frames (skill frame unused) |
| firePoint | (14, −14) | muzzle offset |
| normalSize | 0.9 | render scale |
| weaponClass | (none set) | no projectile assigned |
**Formulas:** n/a.
**Buffs/debuffs applied:** none — `skillMain` is a no-op.
**Δ description vs code:** No description to compare (no kindNum). The notable finding is that `skillMain` is an **empty/no-op** despite `hasSkill=true` and an allocated skill frame range — this class is effectively an inert placeholder (or a support unit whose skill was stripped/never implemented in this build). Stated explicitly rather than inventing a match.
**Notes:** Sister class `Druid1` (`Q1`) is fully implemented (vine/tendril entangle CC via `DruidTangle1`), so `Druid2` being empty is conspicuous — likely an unfinished evolved/variant or cut content in 1.11.42.
