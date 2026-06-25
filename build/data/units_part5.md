# EF2 unit-mechanics extraction — part 5

Bundle: `runtime/bundles/mounted/1.11.42/assets/index.js` (v1.11.42). Constants quoted verbatim from the
minified source. Damage convention: `doMeleeAttack(t, mult)` / `doDamage(t, mult)` / `doRangeAttack(t)` apply
`mult × atkDmg` to the target (mult default 1), subject to miss/block/evade and day-night tribe modifiers.
Mana-gated skills: units with `hasSkill` + a `maxMana` accrue `mana += 1` every tick in `execute()` and fire
their skill (`gotoSkillState`) when `mana >= maxMana`; that interval (≈ maxMana ticks) replaces a fixed
`skillCoolDown` for these units. Tick rate ≈ 60/s at 1× game speed.

---

### Bigfoot — `OrcBigFoot1` (kindNum: 61, 70 evolved)
**Role:** melee tank / AoE bruiser (with freeze)
**Description (in-game):**
- Normal (`UNIT_NATK_61`): "Deals AoE damage to nearby enemies with its huge body and has a chance to freeze them."
- Skill (`UNIT_SATK_61`): "Unleashes a powerful AoE strike forward, freezing multiple enemies."
- (evolved 70 NATK): "Deals AoE damage to nearby enemies with its massive body and has a chance to freeze them."
- (evolved 70 SATK): "Strikes forward in a wider area with a powerful blow, freezing multiple enemies."
**How it works (code):** Melee. `attackMain()` hits the main target with a normal `doMeleeAttack`, then with `chance(s)` freezes it for `e` ticks; it then sweeps a forward AoE box (`getEnemiesAtPos(x+h·dir, y, h)`) hitting up to `n` extra enemies for `0.4×` damage each, each freezeable with `chance(s)`. `skillMain()` (frame 85, fired on mana fill) sweeps a wider forward box (radius `i`), dealing `1.0×` damage to up to `s` enemies, freezing each with `chance(e)` for `n` ticks. Spawns an `IceExplode2` effect. Evolved widens box, raises hit caps, freeze chance and duration. `hasSkill=true` but no `maxMana` set in body → uses base default mana behavior.
**Hard values:**
| variable | value (base → evolved) | meaning |
|---|---|---|
| normal freeze chance `s` | 0.3 → 0.4 | per-target freeze chance on normal attack |
| normal freeze dur `e` | 60 → 70 | freeze ticks |
| normal AoE box `h` | 30 → 45 | forward offset & half-extent of sweep |
| normal max extra hits `n` | 4 → 5 | extra enemies hit per normal attack |
| extra-hit dmg mult | 0.4 | damage to swept enemies |
| skill radius `i` | 55 → 70 | forward AoE box for skill |
| skill max hits `s` | 4 → 8 | enemies hit by skill |
| skill freeze chance `e` | 0.5 → 0.6 | per-target skill freeze chance |
| skill freeze dur `n` | 70 → 80 | skill freeze ticks |
| skill dmg mult | 1.0 | full damage on skill |
| objAtk / objSkill | {51:1} / {85:1} | hit frames |
| normalSize / evolSize | 0.94 / 1.05 | sprite scale |
**Formulas:** freeze applied via `target.freeze(durTicks)` (only if `!freezeImmune` and longer than current `numFreeze`).
**Buffs/debuffs applied:** Debuff = freeze on enemies (durations above). No ally buffs.
**Δ description vs code:** none — matches. NATK "AoE + chance to freeze" = body sweep + per-target `chance(s)` freeze; SATK "powerful forward AoE, freeze multiple" = forward box, 1.0× damage, freeze up to `s`/`8` enemies. Evolved "wider area" = box 55→70 and caps 4→8.

---

### Ice Mage — `OrcBlizzardMage1` (kindNum: 67, 76 evolved) — Orc-tribe variant
**Role:** ranged mage (ice rain AoE)
**Description (in-game):**
- Normal (`UNIT_NATK_67`): "Fires ice shards to attack enemies from range."
- Skill (`UNIT_SATK_67`): "Unleashes a barrage of ice rain on multiple enemies in range, dealing spread damage."
- (evolved 76 NATK): "Fires ice shards continuously to attack enemies from range."
- (evolved 76 SATK): "Unleashes a barrage of ice rain over a larger area, dealing spread damage to enemies."
**How it works (code):** Ranged. Normal attack fires `weaponClass = IceFlake` (base `objAtk = {39:1}`; evolved `objAtk = OBJ_ATK_2 = {39:1,42:1}` → fires twice per swing, matching "continuously"). `skillMain()` (skill frames 49–79, multiple hit frames) gathers all enemies within radius `i`, filters out already-hit ones (`attackedSet`), takes the nearest `s`, and rains `OrcBlizzardMageRain1` projectiles at `0.4×` damage each; `attackedSet` resets when all candidates are exhausted so it cycles fresh targets across the skill's hit frames.
**Hard values:**
| variable | value (base → evolved) | meaning |
|---|---|---|
| skill radius `i` | 220 → 260 | ice-rain gather radius |
| skill targets/burst `s` | 3 → 4 | enemies hit per hit-frame batch |
| rain dmg mult | 0.4 | per-projectile damage (spread) |
| objAtk | {39:1} → {39:1,42:1} | normal hit frame(s); evolved double-hit |
| objSkill | {62:1,66:1,71:1,75:1} | 4 skill rain frames |
| weaponClass | IceFlake | basic projectile |
**Formulas:** n/a (no stat buffs).
**Buffs/debuffs applied:** none (deals spread damage only; no freeze in code).
**Δ description vs code:** Behaviorally matches the generic "Ice Mage" text (ice shards + multi-target ice rain spread damage), and evolved "over a larger area" = radius 220→260 / targets 3→4. **Naming/tribe delta:** the class is `OrcBlizzardMage1` (Orc tribe, `sheetName` set via base) but reuses the generic Ice-Mage (67/76) description string — confirm the kindNum binding in the data config; matched here purely by behavior. Note: the in-game "Frost Mage" (21, enhanced freezing projectiles) does NOT match — this unit deals spread damage and applies no freeze.

---

### (Ice decoy summoned by Orc Hammerman) — `OrcIcePhantom1` (no own kindNum; spawned by kindNum 24/49 skill)
**Role:** summoned taunt-decoy (no attack, draws aggro)
**Description (in-game):** It has no UNIT_NATK/SATK of its own. It is the "ice decoy/clone" referenced by Orc Hammerman's skill:
- Hammerman skill (`UNIT_SATK_24`): "Summons an ice decoy to draw enemy attacks in your place."
- Hammerman skill evolved (`UNIT_SATK_49`): "Summons an ice clone for a longer duration to take hits in your place."
**How it works (code):** Spawned by `HammerMole.summonPhantom(t)` via `getUnitSync(fx.OrcIcePhantom1)`, set up with `setData(sourceVo, 0.3)` (0.3× the summoner's stats), `isSummoned=true`, `summonTimer = t`. Hammerman passes `t = 180` (base) / `220` (evolved). Each tick it `summonTimer--` and `die()`s at 0. It deals NO damage; instead, on a `battleTime % 5 == 0` cadence (desynced by `(id%5)`) it scans `getEnemiesWithin(160, true)` and force-retargets each enemy not already targeting a phantom: `enemy.target = this` + shows `AggroEffect` — i.e. a taunt that pulls enemy attacks onto the decoy. It cycles its move-frame animation while alive.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| summonTimer | 180 (base) / 220 (evolved) | lifetime ticks (set by summoner) |
| stat scale | 0.3 | `setData(sourceVo, 0.3)` → 30% of summoner stats |
| aggro radius | 160 | `getEnemiesWithin(160,true)` taunt range |
| aggro cadence | every 5 ticks | `(battleTime + id%5) % 5 == 0` |
| hitHeight / radius | 29 / 7 | collision |
**Formulas:** n/a.
**Buffs/debuffs applied:** Taunt — reassigns `enemy.target = this` (no numeric buff/debuff object).
**Δ description vs code:** none — matches. "Ice decoy to draw enemy attacks" = the taunt/aggro retarget loop; "longer duration" (evolved) = summonTimer 180→220.

---

### Raptor Rider — `OrcRapterRider1` (kindNum: 83, 86 evolved)
**Role:** ranged dps (multi-target spear thrower)
**Description (in-game):**
- Normal (`UNIT_NATK_83`): "Throws spears at enemies within range."
- Skill (`UNIT_SATK_83`): "Throws multiple spears that have a chance to Freeze enemies within range."
- (evolved 86 NATK): "Throws a spear at more enemies within range."
- (evolved 86 SATK): "Throws several spears that have a chance to Freeze enemies within range."
**How it works (code):** Ranged. `onAttackStartFrame()` builds a `targetList` of up to `t` attackable enemies (`t = 3` base / `4` evolved) with the current target pulled to the front; `attackMain()` is called on each attack hit-frame (`objAtk`) and throws a spear (`doRangeAttack`) at the next target in round-robin. So the multi-frame `objAtk` set distributes spears across the target list. `OBJ_ATK_1 = {61:1,66:1}` (2 normal hit frames); evolved `OBJ_ATK_2 = {61:1,64:1,67:1}` (3 frames → more spears, matching "a spear at more enemies"). Skill: `onSkillStartFrame()` gathers `getEnemiesWithin(220, true)` (+ current target first); `skillMain()` round-robins through the skill hit frames (`objSkill = {90,95,100,105,110}`) firing `OrcRapterRiderSpear1` at each. (Freeze is applied by the spear weapon on hit per the description; not in the unit body.)
**Hard values:**
| variable | value (base → evolved) | meaning |
|---|---|---|
| normal target cap `t` | 3 → 4 | distinct enemies queued per attack |
| objAtk | {61:1,66:1} → {61:1,64:1,67:1} | 2 → 3 normal hit frames (spears) |
| objSkill | {90,95,100,105,110} | 5 skill spear frames |
| skill gather radius | 220 | `getEnemiesWithin(220,true)` |
| weaponClass | OrcRapterRiderSpear1 | spear projectile |
| firePoint | (30, -57) | projectile spawn offset |
| normalSize / evolSize | 1 / 1.06 | scale |
**Formulas:** n/a (no self-buffs).
**Buffs/debuffs applied:** Freeze chance is on the spear weapon `OrcRapterRiderSpear1` (per description), not in the unit class.
**Δ description vs code:** matches. NATK "throws spears at enemies" = round-robin `doRangeAttack` over `targetList`; evolved "a spear at more enemies" = target cap 3→4 and an extra hit frame. SATK "multiple spears, chance to Freeze" = 5 skill spears via `OrcRapterRiderSpear1` (freeze handled by the weapon). **Note:** "chance to Freeze" magnitude is NOT in this class — it lives on the spear weapon class; not quotable here.

---

### Wyvern Rider — `WyvernRider1` (kindNum: 92, 96 evolved)
**Role:** ranged dps (air; boomerang-dagger AoE + freeze-spread skill)
**Description (in-game):**
- Normal (`UNIT_NATK_92`): "Throws daggers at multiple enemies, dealing damage. Depending on the number of enemies defeated since the last skill, fires additional boomerang daggers on the next skill."
- Skill (`UNIT_SATK_92`): "Fires daggers at multiple enemies. When a dagger hits, it freezes the target and spreads daggers outward in all directions from that spot, freezing enemies in their path before exploding after a short time."
- (96 text identical to 92.)
**How it works (code):** Air unit (`isAir`, `airHeight=75`). `attackMain()` throws a `WyvernRiderThrowingKnife1` at the main target at `1.1×`, then one at one more enemy (2 targets total) at `1.1×`. **Kill-counting boomerang mechanic:** `onKillEnemy()` increments `prepCount`; on `onSkillStartFrame()`, `tendrilCountForThisSkill = calcTendrilCount(prepCount)` then `prepCount` resets. `calcTendrilCount` returns 1/2/3/4 based on kill thresholds. The skill (`onSkillStartFrame` gathers up to 3 targets in a box around the current target — radius `85` base / `115` evolved) fires a sequence (`skillMain` called per skill hit frame): the first knife (`skillCallIdx 0`) hits target[0] directly; subsequent calls pick a "divergent" target (`pickDivergentTarget`, spreading outward, within 250px = `62500`²-dist) and add a random positional jitter (`SKILL_OFFSET_MIN..MAX`). For the first `tendrilCountForThisSkill` calls the skill uses the special `WyvernRiderThrowingKnifeS1` (boomerang/freeze-spread weapon); after that, the normal `WyvernRiderThrowingKnife1`. Skill knife damage `1.8×` base / `2.2×` evolved. The freeze + radial spread + explosion is implemented on the `...KnifeS1` weapon.
**Hard values:**
| variable | value (base → evolved) | meaning |
|---|---|---|
| normal targets | 2 | main + 1 extra knife |
| normal knife dmg | 1.1 | `fireKnife(t, 1.1, 0)` |
| skill knife dmg | 1.8 → 2.2 | `skillMain` damage mult |
| skill gather box | 85 → 115 | `getEnemiesAtPos(...,t)` half-extent |
| skill max targets | 3 | `skillTargets.length >= 3` cap |
| TENDRIL_T1 / T2 / T3 | 2 / 5 / 8 | kills→ tendril count thresholds |
| tendril count | 1 (<2 kills) /2 (≥2) /3 (≥5) /4 (≥8) | special boomerang knives next skill |
| SKILL_OFFSET_MIN / MAX | 60 / 140 | random jitter radius on spread knives |
| divergent-target max dist | 250 (62500 = 250²) | spread reach |
| objAtk / objSkill | {35:1} / {68,79,90,101} | hit frames (4 skill knives) |
| airHeight / firePoint | 75 / (18, 5−75) | air positioning |
| normalSize / evolSize | 1.05 / 1.12 | scale |
**Formulas:** divergent target chosen by minimizing the dot product of the to-target direction vs the spread direction (fans knives outward). Tendril tier: `count = prepCount>=8?4 : >=5?3 : >=2?2 : 1`.
**Buffs/debuffs applied:** Freeze (on skill knife hit) lives on `WyvernRiderThrowingKnifeS1`, not the unit.
**Δ description vs code:** matches well. "additional boomerang daggers depending on enemies defeated since last skill" = exactly the `prepCount`→`calcTendrilCount` mechanic (2/5/8 kill thresholds → up to 4 `...KnifeS1` knives). "Freezes + spreads daggers radially + explodes" = the `...KnifeS1` weapon behavior (not quotable from this class). Evolved 96 has identical text but code raises skill damage (1.8→2.2) and gather box (85→115).

---

### (Blade Master) — `BladeMaster1` (no matching kindNum in unit_desc; classVar y2, maxMana 900)
**Role:** melee/ranged dps hybrid — dual-mode bruiser with teleport "reap", mode-switch burst, kill-stacking buffs
**Description (in-game):** No `UNIT_NATK`/`UNIT_SATK` entry exists for this class in `/tmp/unit_desc.json` (descriptions stop at kindNum 96; this is an unreleased/data-only unit). Documented from code only.
**How it works (code):** Two modes selectable via `toggleMode()` (mode 0 = MELEE, mode 1 = RANGE). On spawn it is melee and self-applies a permanent (`MODE_BUFF_DUR = 9999`) move-speed buff (`MELEE_MOVESPD_BUFF = 0.3`) and attack-damage buff (`MELEE_ATKDMG_BUFF = 0.15`).
- **Melee mode `attackMelee()`:** hits the target for `DMG_HIT = 0.95×`, then splashes up to `MAX_HITS = 3` total enemies within `SPLASH_RADIUS = 80` (`100` evolved) at `0.95×` each; spawns afterimages. If the target died, `tryTeleportToNextTarget()` blinks to the nearest enemy within `TELEPORT_MAX_DIST = 400` (lands 30px past it).
- **Range mode `attackRange()`:** a 3-step combo (`rangeComboIdx % 3`) firing `BladeWave1` projectiles at snapped 30°-grid angles (`SNAP_DIRS`, 12 directions) with per-step offsets `RANGE_WAVE_OFFSETS = [-20°, +20°, 0°]`, damage `RANGE_WAVE_DMG = 0.7` (`1.0` evolved). After `RANGE_KILL_STACK_MAX = 6` range kills, the next 3rd-combo shot becomes a triple fan.
- **Skill `skillMain()` (mana 900):** AoE melee hit `SKILL_DMG = 1.5×` to up to `SKILL_MAX = 12` enemies within `SKILL_RANGE = 130` (`160` evolved); fires `SpinBlade` projectiles in a ring (3 angles in melee mode, 6 in range mode) at `SPINBLADE_DMG = 0.8` (`1.1` evolved); then `startReap()` (teleport chain) and self-buffs a rush (move +0.8, atkspd +0.4 for `RUSH_DURATION = 300`).
- **Reap (`startReap`/`advanceReap`):** sorts up to `REAP_MAX_TARGETS = 5` enemies within `REAP_RANGE = 500`, teleports behind each (`REAP_BEHIND_OFF = 30`) one every `REAP_STEP_FRAMES = 6` ticks dealing `REAP_DMG = 1.6×`, then returns to origin.
- **Mode switch (`toggleMode` → `applySwitchBurst`):** AoE `SWITCH_BURST_DMG = 1.0×` to enemies within `SWITCH_BURST_RADIUS = 100`, heals self `SWITCH_HEAL = 30`. Entering range mode sets `atkRange = 350` and a permanent atkspd buff `RANGE_ATKSPD_BUFF = 0.5`.
- **Kills (`onKillEnemy`):** melee kills give `MELEE_KILL_MANA = 20` mana; every kill stacks (up to `KILL_STACK_MAX = 8`) an atkspd buff `KILL_ATKSPD_PER = 0.06`/stack and atkdmg buff `KILL_ATKDMG_PER = 0.05`/stack for `KILL_BUFF_DUR = 600`.
**Hard values:** (selected; all `zt(b2,...)` statics)
| variable | value | meaning |
|---|---|---|
| maxMana | 900 | skill mana cost (≈900 ticks) |
| DMG_HIT | 0.95 | melee hit mult |
| SPLASH_RADIUS / _E | 80 / 100 | melee splash radius (base/evolved) |
| MAX_HITS | 3 | melee enemies per swing |
| RANGE_ATK_RANGE | 350 | range-mode attack range |
| RANGE_WAVE_DMG / _E | 0.7 / 1.0 | blade-wave damage |
| RANGE_WAVE_OFFSETS | [−π/9, π/9, 0] | ±20°,0 combo offsets |
| RANGE_ATKSPD_BUFF | 0.5 | +50% atkspd in range mode (dur 9999) |
| RANGE_KILL_STACK_MAX | 6 | range kills → triple-fan shot |
| SKILL_RANGE / _E | 130 / 160 | skill AoE radius |
| SKILL_DMG | 1.5 | skill AoE hit mult |
| SKILL_MAX | 12 | skill AoE max targets |
| SPINBLADE_DMG / _E | 0.8 / 1.1 | spin-blade projectile damage |
| SPINBLADE_ANGLES_MELEE/RANGE | 3 / 6 angles | ring projectile count |
| KILL_STACK_MAX | 8 | max kill stacks |
| KILL_ATKSPD_PER / ATKDMG_PER | 0.06 / 0.05 | per-stack buff (+6% atkspd, +5% atkdmg) |
| KILL_BUFF_DUR | 600 | kill-buff ticks |
| MELEE_MOVESPD_BUFF / ATKDMG_BUFF | 0.3 / 0.15 | passive melee buffs (dur 9999) |
| MELEE_KILL_MANA | 20 | mana per melee kill |
| RUSH_DURATION | 300 | rush buff ticks |
| RUSH_MOVESPD_BONUS / ATKSPD_BONUS | 0.8 / 0.4 | post-skill rush buffs |
| SWITCH_BURST_RADIUS / DMG / HEAL | 100 / 1.0 / 30 | mode-switch burst & self-heal |
| TELEPORT_MAX_DIST | 400 | blink range on target death |
| REAP_MAX_TARGETS / RANGE / STEP_FRAMES / DMG / BEHIND_OFF | 5 / 500 / 6 / 1.6 / 30 | reap chain |
| normalSize / evolSize | 0.9 / 1 | scale |
**Formulas:** `atkSpd = orgAtkSpd*(1 + Σ atkspd-buff.value)`; e.g. at max kill stacks (8) atkspd buff = `8×0.06 = 0.48` (+48%) and atkdmg buff = `8×0.05 = 0.40`; range-mode passive `+0.5` atkspd is +50%; rush adds `+0.4` atkspd and `+0.8` move on top (distinct ids → summed). `snapToDir` quantizes the aim angle to the nearest of 12 directions spaced 30° (π/6).
**Buffs/debuffs applied (self, ids in `fQ`):**
- `BladeMaster1_MELEE_MOVESPD` (id 253), value 0.3, dur 9999 (zeroed when entering range mode).
- `BladeMaster1_MELEE_ATKDMG` (id 254), value 0.15, dur 9999.
- `BladeMaster1_RANGE_ATKSPD` (id 252), value 0.5, dur 9999 (range mode only).
- `BladeMaster1_KILL_ATKSPD` (id 250), value stack×0.06, dur 600 (refresh).
- `BladeMaster1_KILL_ATKDMG` (id 251), value stack×0.05, dur 600.
- `BladeMaster1_RUSH_MOVESPD` (id 256), value 0.8, dur 300 (post-skill).
- `BladeMaster1_RUSH_ATKSPD` (id 255), value 0.4, dur 300.
Debuffs: pure damage (no freeze/stun in code).
**Δ description vs code:** **No in-game description to compare** — `/tmp/unit_desc.json` has no entry for BladeMaster1 (kindNums end at 96). Stated explicitly: this class is documented from code alone; its kindNum is not present in the provided desc data.
**Notes:** Most mechanically complex of the 12. `mode` toggling, kill-stack scaling, reap teleport chain, and the 30°-snapped blade-wave combo are all bespoke. Buff ids 250–256 are contiguous and dedicated, so its self-buffs never collide with other units.

---

### Elf Castle — `ElfTown5` (kindNum: 10001)
**Role:** castle / defensive structure (immobile ranged turret) — used as BOTH the player and enemy castle
**Description (in-game):**
- Normal (`UNIT_NATK_10001`): "Knockback"
- Skill (`UNIT_SATK_10001`): "Special Skill"
**How it works (code):** Stationary (`moveSpd=0`, `radius=22`, `numBlock=0`, `lookAt`/`die` overridden, no real movement). Confirmed as kindNum 10001 by `setupCastles()`: `initializeUnitByKindNum(i, 10001, t)`, then `detectRange=600`, `atkRange=250`, `numShot=1`. Fires `weaponClass = SpeedArrow2`. `attackMain()` fires up to `ceil(numShot)` arrows: for each of the top `numShot` attackable enemies it `doRangeAttack` with probability `numShot` (decrementing) — i.e. fractional `numShot` yields a probabilistic last shot (multishot if `numShot>1`). Custom `generateWeapon` aims `SpeedArrow2` from a 35px muzzle toward the target, carries `numBounce` bounces. Health-bar visible (it's a destructible base). The castle is set up once per battle for each side at the side's center.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| kindNum | 10001 | bound via `initializeUnitByKindNum(...,10001)` |
| detectRange | 600 | target detection (set at setup) |
| atkRange | 250 | firing range (set at setup) |
| numShot | 1 | shots per attack (set at setup; multishot if raised) |
| radius / hitHeight | 22 / 67 | collision / sprite |
| weaponClass | SpeedArrow2 | arrow projectile (carries numBounce) |
| objAtk | {23:1} | hit frame |
| moveSpd | 0 | immobile |
**Formulas:** multishot loop: for shot `e`, fire with `random.chance(numShot)` then `numShot--` → expected arrows ≈ `numShot` (fractional handled probabilistically).
**Buffs/debuffs applied:** none in this class (knockback/special-skill per description are generic placeholders; the bundle body adds none).
**Δ description vs code:** Description is the generic placeholder pair ("Knockback" / "Special Skill") used for non-player structures. The code has no knockback call and no skill (`hasSkill` not set; just a ranged turret firing `SpeedArrow2`). So the "Knockback"/"Special Skill" text is a stub and does NOT reflect actual mechanics — the real behavior is a stationary multishot arrow tower. **Note:** the "5" in `ElfTown5` is a tier/skin index; all castle setups in the bundle use this same class for kindNum 10001.

---

### Orc Flower — `OrcFlower` (kindNum: 30001)
**Role:** boss/castle-type summoner structure (immobile; spawns Flower Soldiers)
**Description (in-game):**
- Normal (`UNIT_NATK_30001`): "Knockback"
- Skill (`UNIT_SATK_30001`): "Special Skill"
**How it works (code):** Large stationary structure (`moveSpd=0`, `radius=40`, `hitHeight=140`, `numBlock=0`, `hasSkill`, `maxMana=300`). Movement/idle overridden so it never moves; it targets the nearest enemy and attacks when in range. Normal attack (`attackMain`, distributed across 8 `objAtk` frames {46,48,…,60}) round-robins `doRangeAttack` over up to 10 queued targets, firing `EnergyBall` projectiles (custom `generateWeapon` spawns them with random jitter from the muzzle). **Skill (`skillMain`, mana-gated at 300):** while ally count `< 30`, summons 2 `FlowerSoldier2` units (`kindNum 30003`) via `summonUnit(VO, 1200)` (1200-tick lifetime). Hard-overrides all crowd-control receivers (`stun`, `knockBack`, `freeze`, `curse`, `silence`, `poison`, `blow`, `binding`, `shock`, `addDotDamage`, `onHitted`) to no-ops → **immune to all CC and DoT** (boss immunity). Clicking it shows its range (UI).
**Hard values:**
| variable | value | meaning |
|---|---|---|
| kindNum | 30001 | Orc Flower |
| maxMana | 300 | skill interval (≈300 ticks) |
| summons per skill | 2 | FlowerSoldier2 spawned per skill |
| summon kindNum | 30003 | `FlowerSoldier2` (the `soldierVO.kindNum=30003`) |
| summon lifetime | 1200 | ticks (`summonUnit(VO,1200)`) |
| ally cap | 30 | stops summoning at ≥30 allies |
| weaponClass | EnergyBall | normal projectile |
| normal target queue | 10 | `getAttackableEnemyList(10)` |
| objAtk | {46,48,50,52,54,56,58,60} | 8 normal hit frames |
| radius / hitHeight | 40 / 140 | large boss footprint |
**Formulas:** n/a (no stat buffs); skill gated by `mana>=maxMana` (`mana += 1`/tick).
**Buffs/debuffs applied:** none. Notable: **CC/DoT immunity** via no-op overrides of `stun/knockBack/freeze/curse/silence/poison/blow/binding/shock/addDotDamage`.
**Δ description vs code:** Description is the generic placeholder ("Knockback" / "Special Skill"). Code reality: no knockback; the "special skill" is summoning Flower Soldiers (kindNum 30003) and it is a CC-immune stationary boss firing EnergyBalls. The stub text understates a summoner-boss. **Note:** summons `FlowerSoldier2` (30003), NOT FlowerSoldier1 (30002) — only the ranged soldier variant is summoned by the skill.

---

### Flower Soldier 1 — `FlowerSoldier1` (kindNum: 30002)
**Role:** basic melee minion (Orc Flower add)
**Description (in-game):**
- Normal (`UNIT_NATK_30002`): "None"
- Skill (`UNIT_SATK_30002`): "Special Skill"
**How it works (code):** Trivial melee attacker. Only `initializeData()` — sets sprite (`sheetName="OrcFlower"`), `radius=7`, `hitHeight=22`, frame ranges, and `objAtk={63:1}`. No `attackMain`/skill override → uses base `qQ` melee attack (`doMeleeAttack` of nearest target on frame 63). No weaponClass (pure melee).
**Hard values:**
| variable | value | meaning |
|---|---|---|
| kindNum | 30002 | Flower Soldier 1 |
| objAtk | {63:1} | melee hit frame |
| radius / hitHeight | 7 / 22 | collision |
**Formulas:** n/a.
**Buffs/debuffs applied:** none.
**Δ description vs code:** matches (trivially) — "None"/"Special Skill" placeholders; the unit is a plain melee add with no skill. (Stats like atkDmg/hp come from the kindNum data config, not this body.)

---

### Flower Soldier 2 — `FlowerSoldier2` (kindNum: 30003)
**Role:** basic ranged minion (Orc Flower add; the one Orc Flower summons)
**Description (in-game):**
- Normal (`UNIT_NATK_30003`): "None"
- Skill (`UNIT_SATK_30003`): "Special Skill"
**How it works (code):** Trivial ranged attacker. Only `initializeData()` — `sheetName="OrcFlower"`, `weaponClass = FlowerBullet`, `radius=7`, `hitHeight=27`, `firePoint = (17,-17)`, `objAtk={61:1}`. No `attackMain`/skill override → base ranged attack fires `FlowerBullet` at the nearest target on frame 61. This is the unit summoned by `OrcFlower`'s skill (kindNum 30003).
**Hard values:**
| variable | value | meaning |
|---|---|---|
| kindNum | 30003 | Flower Soldier 2 (summoned by Orc Flower) |
| weaponClass | FlowerBullet | ranged projectile |
| firePoint | (17, -17) | muzzle offset |
| objAtk | {61:1} | hit frame |
| radius / hitHeight | 7 / 27 | collision |
**Formulas:** n/a.
**Buffs/debuffs applied:** none.
**Δ description vs code:** matches (trivially) — placeholders; plain ranged add firing FlowerBullet, no skill.

---

### King Slime — `KingSlime` (kindNum: 20001)
**Role:** boss (immobile; ranged barrage + multi-color slime summoner; CC-immune)
**Description (in-game):**
- Normal (`UNIT_NATK_20001`): "Knockback"
- Skill (`UNIT_SATK_20001`): "Special Skill"
**How it works (code):** Big stationary boss (`moveSpd=0`, `radius=40`, `hitHeight=135`, `numBlock=0`, `hasSkill`, `maxMana=300`). Doesn't move (idle/move/lookAt overridden). **Normal attack (`attackMain`):** gathers ALL enemies within `300` and, for each, with `chance(0.6)` fires a `Rock` projectile — a probabilistic AoE barrage rather than single-target. Custom `generateWeapon` spawns `Rock` with random jitter. **Skill (`skillMain`, mana-gated at 300):** loops up to 5 times summoning slimes, cycling through `kindNums = [20002, 20003, 20004]` (Red, Blue, Yellow Slime) with `summonUnit(VO, 600)` (600-tick lifetime); stops early if ally count reaches 30. Like Orc Flower, it **no-ops all CC/DoT receivers** (`stun, knockBack, freeze, curse, silence, poison, blow, binding, shock, addDotDamage, onHitted`) → fully CC/DoT-immune boss.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| kindNum | 20001 | King Slime |
| maxMana | 300 | skill interval (≈300 ticks) |
| attack radius | 300 | `getEnemiesWithin(300)` barrage range |
| per-target fire chance | 0.6 | `random.chance(.6)` per enemy per attack |
| skill summon loop | 5 | up to 5 slimes per skill |
| summon kindNums | [20002, 20003, 20004] | Red / Blue / Yellow Slime (cycled) |
| summon lifetime | 600 | ticks |
| ally cap | 30 | stops summoning at ≥30 |
| weaponClass | Rock | barrage projectile |
| radius / hitHeight | 40 / 135 | boss footprint |
| objAtk | {34:1} | hit frame |
**Formulas:** skill gated by `mana>=maxMana`; barrage expected projectiles ≈ `0.6 × (enemies within 300)`.
**Buffs/debuffs applied:** none. Notable: **CC/DoT immunity** via no-op overrides; effectively a phase-free summoner boss (no HP-threshold phases in code — its "phases" are just the recurring mana-gated summon waves of mixed-color slimes).
**Δ description vs code:** Description is the generic placeholder ("Knockback" / "Special Skill"). Reality: no knockback — a CC-immune boss that rains `Rock` projectiles (60%/enemy within 300) and periodically summons 5 mixed-color slimes (20002/20003/20004). The stub massively understates it. **Boss check:** no per-HP phase transitions or enrage in the class; behavior is constant; difficulty scales via the kindNum data config (level) and the summon pressure.

---

### Blue Slime — `SlimeBlue` (kindNum: 20003)
**Role:** basic enemy minion (summoned by King Slime)
**Description (in-game):**
- Normal (`UNIT_NATK_20003`): "None"
- Skill (`UNIT_SATK_20003`): "Special Skill"
**How it works (code):** Trivial. Only `initializeData()` — `sheetName="KingSlime"`, `radius=7`, `hitHeight=15`, frame ranges, `objAtk={36:1}`. No `attackMain`/skill override and no weaponClass → base melee (or whatever its kindNum data sets) hitting on frame 36. One of the three slimes King Slime summons (the blue 20003 variant). Red/Yellow are sibling classes `SlimeRed`/`SlimeYellow` (kindNum 20002/20004), structurally identical.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| kindNum | 20003 | Blue Slime |
| objAtk | {36:1} | hit frame |
| radius / hitHeight | 7 / 15 | collision (tiny) |
**Formulas:** n/a.
**Buffs/debuffs applied:** none.
**Δ description vs code:** matches (trivially) — "None"/"Special Skill" placeholders; a plain summoned add with no skill of its own. Stats come from the kindNum 20003 data config.
