# EF2 unit mechanics — Part 3 (12 Elf/allied-faction units)

Source bundle: `runtime/bundles/mounted/1.11.42/assets/index.js`.
Constants below are quoted verbatim from the bundle (`zt(Class,"NAME",value)` static defs). Times are game ticks (~60/s at 1× game speed). "evolved" = `evolStage>=1`.

---

### Steam Punk — `SteamPunk1` (kindNum: 82, 85 evolved)
**Role:** ranged dps (multi-target homing missiles + stun)
**Description (in-game):**
- Normal (`UNIT_NATK_82`): "Fires a homing missile that has a chance to stun 2 enemies." (evolved `_85`: "…stun 3 enemies.")
- Skill (`UNIT_SATK_82`): "Fires multiple missiles at enemies within range." (evolved `_85`: "…with a chance to fire additional missiles.")
**How it works (code):** On each attack it builds a `targetList` of the nearest `2` (base) / `3` (evolved) enemies in its facing arc (`getEnemiesForDirection`), then `attackMain()` fires one homing `SteamFire1` per target across the attack-anim hit frames (`OBJ_ATK_1={90:1,95:1}` base → 2 missiles; `OBJ_ATK_2={90:1,93:1,96:1}` evolved → 3 missiles). Each `SteamFire1` on hit rolls `chance(0.3/0.4)` to `stun(40/50)` the primary target and additionally splash-damages up to 3 enemies within ~25px (`doDamage(...,0.4,true)`). The skill (`onSkillStartFrame`) gathers up to all enemies within `220`, then `skillMain` fires `SteamMissile1` projectiles at each in turn; evolved has a `chance(0.2)` to fire a second missile that cycle.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| OBJ_ATK_1 / OBJ_ATK_2 | {90,95} / {90,93,96} | basic-attack hit frames → 2 / 3 missiles (base/evolved) |
| basic targets | 2 / 3 | nearest enemies engaged per attack (base/evolved) |
| SteamFire1 stun chance | 0.3 / 0.4 | per-missile stun roll (base/evolved) |
| SteamFire1 stun dur | 40 / 50 | stun ticks (base/evolved) |
| SteamFire1 splash | ≤3 × 0.4 dmg | within ~25px (`s²+e²<625`, `|Δ|≤35`) |
| skill gather range | 220 | radius to collect skill targets |
| SteamMissile1 dmg | 1.5 | `setData(1.5)` damage multiplier |
| evolved extra-missile chance | 0.2 | second skill missile that cycle |
**Formulas:** stun applied per missile independently → "stun 2/3 enemies" = 2/3 missiles each rolling stun.
**Buffs/debuffs applied:** stun (status) on missile hit, dur `40/50`, chance `0.3/0.4`, primary target only.
**Δ description vs code:** none — matches. The "stun 2/3 enemies" reflects the 2/3 separate homing missiles each able to stun their target; evolved bumps both target count (2→3) and stun chance/dur.
**Notes:** First skill missile always fires at the locked `target` then nearest others; `weaponClass=YX.SteamFire1`, skill weapon `SteamMissile1`. `maxMana` not set on basic (mana-gated skill via base class).

---

### Winged Knight — `WingKnight1` (kindNum: 89, 93 evolved)
**Role:** melee dps (3-hit combo + knockback) with two passive states (Flash, Survival) + teleport-slam skill
**Description (in-game):**
- Normal (`UNIT_NATK_89`/`_93`): "Deals 3 consecutive hits to enemies and also damages nearby enemies. The final hit knocks enemies back. **Flash:** After defeating a set number of enemies, an Attack and Haste buff is triggered, and each kill instantly moves you to the next target. **Survival:** When HP falls below a certain level, a shield is briefly formed and attack speed and attack power greatly increase."
- Skill (`UNIT_SATK_89`/`_93`): "Teleports to an enemy and deals area damage to nearby enemies."
**How it works (code):** `attackMain` cycles `comboIndex%3` dealing `ATK_DMG=[.7,.8,1]` per hit, plus one nearby splash victim within `COMBO_SPLASH_RANGE=60` at the same multiplier; on the 3rd hit (`i===2`) it `knockBack(direction*COMBO_KB_VX, COMBO_KB_VY=-2, COMBO_KB_DUR)`. **Flash passive:** `onKillEnemy` increments `killCount`; at `KILL_THRESHOLD=6` it fires `activateFlashBuff()` (move/atk-dmg/atk-spd buffs + extended detect range `1200`) and enters skill state; while Flash is active each kill snaps to a new target within `FLASH_DETECT_RANGE=1200`. **Survival passive:** `onHpDroppedBelow20` (≤20% HP) sets HP floor to `max(1, maxHp*0.2)`, casts a power shield for `180`, applies berserk atk-spd/atk-dmg buffs for `600`, and forces a skill cast; gated by `SURVIVE_SKILL_COOLDOWN=3600`. **Skill** (`skillMain`): teleports onto nearest enemy within `SKILL_TARGET_RANGE=500`, `stun`s it (`30`/`45` evolved) — evolved also stuns enemies within `DASH_STUN_RANGE=60` — then `doSkillSlam` deals `SKILL_SLAM_DMG=2.5/3` to up to 15 enemies within `SKILL_SLAM_RANGE=110/150`.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| ATK_DMG | [.7,.8,1] | 3-hit combo damage multipliers |
| COMBO_SPLASH_RANGE | 60 | nearby splash victim radius (one extra) |
| COMBO_KB_VX / _VX_E | 3 / 4 | 3rd-hit knockback x-velocity (base/evolved) |
| COMBO_KB_VY | -2 | knockback y-velocity |
| COMBO_KB_DUR / _DUR_E | 30 / 40 | knockback duration |
| KILL_THRESHOLD | 6 | kills to trigger Flash |
| FLASH_BUFF_DUR | 480 | Flash buff/timer duration |
| FLASH_DETECT_RANGE | 1200 | Flash detect/retarget range |
| FLASH_MOVSPD / _ATKSPD / _ATKDMG | 1.5 / 0.5 / 0.5 | Flash buff values |
| SURVIVE_HP_THRESHOLD | 0.2 | ≤20% HP triggers Survival |
| SURVIVE_SHIELD_DUR | 180 | survival power-shield ticks |
| SURVIVE_BERSERK_DUR | 600 | survival buff duration |
| SURVIVE_ATKSPD / _ATKDMG | 1 / 1 | survival buff values (+100% each) |
| SURVIVE_SKILL_COOLDOWN | 3600 | survival re-trigger gate (~60s) |
| DASH_STUN_DUR / _DUR_E | 30 / 45 | skill teleport stun (base/evolved) |
| DASH_STUN_RANGE | 60 | evolved-only AoE stun radius |
| SKILL_TARGET_RANGE | 500 | skill teleport target search |
| SKILL_SLAM_RANGE / _E | 110 / 150 | slam AoE radius (base/evolved) |
| SKILL_SLAM_DMG / _E | 2.5 / 3 | slam damage mult (base/evolved); ≤15 targets |
| maxMana | 900 | mana pool |
**Formulas:** `atkSpd=orgAtkSpd*(1+0.5)` ⇒ +50% (Flash) / `*(1+1.0)` ⇒ +100% (Survival). `atkDmg` buffs +50% (Flash) / +100% (Survival, additive value 1).
**Buffs/debuffs applied (self):**
- Flash: `addMoveSpeedBuff(WingKnight1_FLASH_MOVSPD, 1.5, 480, refresh)` (+150%), `addAttackDamageBuff(WingKnight1_DASH_BUFF, 0.5, 480)`, `addAttackSpeedBuff(WingKnight1_FLASH_ATKSPD, 0.5, 480, refresh)` (+50%).
- Survival: `addAttackSpeedBuff(WingKnight1_BERSERK_ATKSPD, 1, 600, refresh)` (+100%), `addAttackDamageBuff(WingKnight1_BERSERK_ATKDMG, 1, 600)`, power shield `180`.
- On targets: stun (skill teleport), knockback (combo 3rd hit).
**Δ description vs code:** none — matches, and the code is richer than the text. Description's "Attack and Haste buff" = the Flash atk-dmg + atk-spd + move-spd buffs; "shield…attack speed and attack power greatly increase" = the Survival branch (verified `+100%` each). Distinct buff ids per state so Flash and Survival buffs co-exist.
**Notes:** Flash and Survival are passive (NATK), not the mana skill. `normalSize=.8`, `evolSize=.85`. During Flash it drains `mana` each tick and on timer expiry casts a finishing slam. HP-floor logic prevents the killing blow when Survival is available.

---

### (Forest-Guardian-slot variant) — `Aladin1` (kindNum: **no matching description in `/tmp/unit_desc.json`**)
**Role:** ranged dps / area-denial "genie" — throws gold coins that orbit and grant random wishes (buffer hybrid)
**Description (in-game):** No `UNIT_NATK`/`UNIT_SATK` entry exists for an "Aladin"/genie/coin unit in `/tmp/unit_desc.json` (names 1–96 + specials checked exhaustively; closest by slot order is Forest Guardian 81/84, whose text — "fires magic arrows…self Speed buff" — does NOT match this coin/wish behavior). Documented from code only.
**How it works (code):** Wanders within a leash (`WANDER_RADIUS=180`) and every `ATK_COOLDOWN=200` throws `ATK_COIN_COUNT=3` (+2 evolved) `AladinCoin1` projectiles (`damagePercent=0.6`, `lifeDuration=COIN_LIFE=900`) that scatter and persist on the ground; global cap `GLOBAL_COIN_CAP=50`. Damage scales with nearby coins via `goldDmgMultiplier = 1 + n*GOLD_DMG_PER_COIN(0.03)` up to `GOLD_MAX_COINS=25` (→ up to +75%). **Skill** auto-triggers when `mana>=maxMana(400)` AND ≥3 coins are within `COLLECT_RADIUS=175`: `liftCoins()` then `launchCoinOrbit()` makes nearby coins orbit (`ORBIT_RADIUS=155`) and spawns the `AladinGenie1` effect, then `scheduleWish()`. **Wishes** (random 1 of 3 after `WISH_TRIGGER_DELAY=180`): **Gold** = spawn `WISH_GOLD_BONUS_COINS=8` extra coins + faster attacks for `300` ticks (`WISH_GOLD_FAST_RATIO=0.5` ⇒ cooldown halved); **Blessing** = `addAttackDamageBuff(Aladin1_BLESSING_ATKDMG, 0.15, 480)` to ALL allies (+15% ATK, 480 ticks); **Foresight** = next orbit launch has `WISH_FORESIGHT_RANGE_MULT=1.3` range and `WISH_FORESIGHT_DMG_MULT=2`× coin damage. `onHitted` re-launches a random idle coin defensively; expired coins have `chance(0.1)` to add `0.5s` of rage energy.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| ATK_COOLDOWN | 200 | ticks between coin throws |
| ATK_COIN_COUNT | 3 (+2 evolved) | coins per throw |
| COIN_LIFE | 900 | coin lifetime |
| GLOBAL_COIN_CAP | 50 | max coins on field (all Aladins) |
| GOLD_DMG_PER_COIN / GOLD_MAX_COINS | 0.03 / 25 | dmg mult +3% per nearby coin, cap 25 → +75% |
| COLLECT_RADIUS / ORBIT_RADIUS | 175 / 155 | coin gather / orbit radii |
| maxMana | 400 | skill mana gate (also needs ≥3 coins near) |
| WISH_TRIGGER_DELAY | 180 | delay before wish resolves |
| WISH_GOLD_BONUS_COINS | 8 | extra coins on Gold wish |
| WISH_GOLD_FAST_FRAMES / _RATIO | 300 / 0.5 | fast-attack duration / cooldown multiplier |
| WISH_BLESSING_ATKDMG / _FRAMES | 0.15 / 480 | ally ATK buff value / duration |
| WISH_FORESIGHT_DMG_MULT / _RANGE_MULT | 2 / 1.3 | next-orbit dmg / range multipliers |
| AladinCoin1 damagePercent | 0.6 | per-coin damage |
| COIN_EXPIRE_RAGE_CHANCE / _SECONDS | 0.1 / 0.5 | rage energy on coin expiry |
**Formulas:** `goldDmgMultiplier = 1 + min(coins,25)*0.03`. Blessing: `atkDmg` of allies via additive buff value `0.15` ⇒ +15%.
**Buffs/debuffs applied:** Blessing wish → `addAttackDamageBuff(Aladin1_BLESSING_ATKDMG, 0.15, 480)` to every alive ally (removed on death via `removeAttackDamageBuff`). Self: Gold wish fast-attack (no buff-id; direct `goldFastTimer`). `Aladin1_SAND_SLOW` enum id (260) exists but no slow call observed in this class body.
**Δ description vs code:** **No in-game description to compare** — this kindNum's text is absent from `/tmp/unit_desc.json`. The class is a fully self-contained coin/wish system; flagged as undocumented.
**Notes:** `static allCoins[]` is shared across all Aladin1 instances (global field). `normalSize=.75`, `evolSize=.8`, `weaponClass` via `AladinCoin1`. `objAtk={}` (no anim-frame hit; coins thrown procedurally in `execute`).

---

### Elf Archer — `ElfArcher1` (kindNum: 7, 32 evolved)
**Role:** ranged dps (3-arrow volley skill)
**Description (in-game):**
- Normal (`UNIT_NATK_7`/`_32`): "Fires arrows to attack enemies from range."
- Skill (`UNIT_SATK_7`/`_32`): "Fires 3 arrows at once, hitting up to 3 enemies simultaneously."
**How it works (code):** 8-direction archer: `gotoAttackState` picks one of 5 directional attack/skill frame sets + firepoints by the angle to the target. Basic `attackMain` sets `numShot=1.3` and calls `super.attackMain()` (the base multishot fires `NormalArrow` projectiles; the 1.3 yields an occasional extra arrow). Skill `skillMain` sets `numShot=3` ⇒ 3 simultaneous arrows. `multiShotDelay=3`, `weaponClass=YX.NormalArrow` (`PhysicalHitEffect`, `g=.1, speed=10`).
**Hard values:**
| variable | value | meaning |
|---|---|---|
| numShot (basic) | 1.3 | arrows per basic attack (fractional → avg 1.3) |
| numShot (skill) | 3 | arrows in skill volley |
| multiShotDelay | 3 | frame delay between multishot arrows |
| normalSize / evolSize | .95 / 1.03 | sprite scale |
**Formulas:** numShot fractional → `floor + chance(frac)` extra arrow (base-class multishot).
**Buffs/debuffs applied:** none.
**Δ description vs code:** none — matches. "3 arrows / up to 3 enemies" = `numShot=3`. (Note evolved 32 shares identical mechanics in this class; the evolution difference is via book stats, not code branches here.)
**Notes:** Same 8-direction frame/firepoint scaffold as HighArcher1/PoisonArcher1's archer family. No `evolved` branch in code; basic `numShot` is always 1.3.

---

### High Elf Archer — `HighArcher1` (kindNum: 10, 35 evolved)
**Role:** ranged dps (rapid magic-arrow volleys)
**Description (in-game):**
- Normal (`UNIT_NATK_10`): "Attacks enemies from range with precise magic arrows." (evolved `_35`: "…at an increased fire rate…")
- Skill (`UNIT_SATK_10`): "Rapidly fires magic arrows to hit multiple enemies at once." (evolved `_35`: "Fires a rapid volley…")
**How it works (code):** Same 8-direction frame/firepoint system as ElfArcher1, but uses `weaponClass=YX.SpeedArrow` and is evolution-aware via `this.evolved=evolStage>=1`. Basic `attackMain`: `numShot = evolved?1.8:1.3`. Skill `skillMain`: `numShot = evolved?4:3`. `multiShotDelay=3`.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| numShot (basic) | 1.3 / 1.8 | base / evolved basic arrows |
| numShot (skill) | 3 / 4 | base / evolved volley arrows |
| multiShotDelay | 3 | inter-arrow frame delay |
| weaponClass | SpeedArrow | faster projectile vs ElfArcher's NormalArrow |
**Formulas:** fractional numShot → extra-arrow chance.
**Buffs/debuffs applied:** none.
**Δ description vs code:** none — matches. "increased fire rate" / "rapid volley" reflects the evolved numShot bump (1.3→1.8 basic, 3→4 skill) and the SpeedArrow weapon.
**Notes:** The ONLY archer in this family with a real `evolved` code branch on numShot. `dieFrames=QK(190,221)`, distinct directional firepoints `(30,-20)/(24,-37)/(0,-54)/(18,-3)/(6,12)`.

---

### Elf Warrior — `ElfWarrior1` (kindNum: 8, 33 evolved)
**Role:** melee dps (double-hit + triple-hit combo skill)
**Description (in-game):**
- Normal (`UNIT_NATK_8`/`_33`): "Strikes enemies with a melee double hit."
- Skill (`UNIT_SATK_8`/`_33`): "Unleashes a triple-hit combo with 1.5x power, dealing heavy melee damage."
**How it works (code):** Trivial melee with a skill. Basic attack lands on `objAtk={54:1,60:1}` (two hits = double hit). `skillMain` does a single `doMeleeAttack(this.target, 1.5)` but the skill animation reuses `objSkill={54:1,60:1,62:1}` (three hit frames) ⇒ triple-hit at 1.5× power. Skill frames `==` attack frames `QK(44,73)`.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| objAtk | {54,60} | basic double-hit frames |
| objSkill | {54,60,62} | skill triple-hit frames |
| skill power | 1.5 | `doMeleeAttack(target,1.5)` multiplier |
**Formulas:** n/a (plain melee multiplier).
**Buffs/debuffs applied:** none.
**Δ description vs code:** none — matches. Double-hit (2 objAtk frames) and triple-hit-at-1.5× (3 objSkill frames + 1.5 multiplier) confirmed.
**Notes:** No `setData`/evolved branch — evolution (33) differs only via book stats.

---

### (Elf basic swordsman) — `ElfSwordMan1` (kindNum: **no exact-name description; behavior = "Infantry"-class basic melee, closest text Elf Warrior NATK**)
**Role:** basic melee enemy/soldier (double-hit, no skill)
**Description (in-game):** No "ElfSwordMan"/"Swordsman" entry in `/tmp/unit_desc.json`. It is a stripped basic attacker (no `hasSkill`); its double-hit NATK reads identically to Elf Warrior's "Strikes enemies with a melee double hit" but it has no skill. Likely a basic spawned soldier variant (e.g., summoned/enemy infantry) rather than a deployable book unit.
**How it works (code):** Minimal class — only `initializeData`. `objAtk={49:1,53:1}` ⇒ melee double-hit. No `hasSkill`, no `skillMain`, no buffs. Sword sounds, `radius=7`, `hitHeight=27`.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| objAtk | {49,53} | double-hit attack frames |
| skillFrames | == attackFrames QK(36,65) | no separate skill |
**Formulas:** n/a.
**Buffs/debuffs applied:** none.
**Δ description vs code:** **No dedicated description** — it shares the "double melee hit" wording of Elf Warrior but lacks any skill. Flagged as an undocumented basic variant.
**Notes:** Trivial basic attacker. Compare ElfWarrior1 (same family) which adds the 1.5× triple skill.

---

### Poison Archer — `PoisonArcher1` (kindNum: 9, 34 evolved)
**Role:** ranged dps + debuffer (poison/slow)
**Description (in-game):**
- Normal (`UNIT_NATK_9`/`_34`): "Fires a poison arrow that reduces enemies' movement speed and attack speed."
- Skill (`UNIT_SATK_9`/`_34`): "Fires a 1.5x power poison arrow that creates a poison cloud and slows nearby enemies."
**How it works (code):** Single-direction archer. Basic attack fires `weaponClass=YX.PoisonArcherArrow1`, whose `onHitMain` calls `target.poison(50)` (50-tick slow status that reduces move + attack speed). Skill `skillMain` fires `PoisonArcherArrowSkill1` via `generateWeapon(target, ..., 1.5)` (1.5× power). That skill arrow's `onHitMain` reads `owner.evolStage`: poisons the main target for `i = evolved?70:50` ticks, then `getEnemiesAtPos(x,y, s=evolved?60:50)` collects nearby enemies and poisons up to `n = evolved?6:4` of them for `e = evolved?30:20` ticks each (the "poison cloud").
**Hard values:**
| variable | value | meaning |
|---|---|---|
| basic poison | poison(50) | 50-tick slow on hit (PoisonArcherArrow1) |
| skill power | 1.5 | `generateWeapon(...,1.5)` damage mult |
| skill main poison | 70 / 50 | main-target poison ticks (evolved/base) |
| skill cloud radius | 60 / 50 | AoE search radius (evolved/base) |
| skill cloud max targets | 6 / 4 | nearby enemies poisoned (evolved/base) |
| skill cloud poison | 30 / 20 | secondary-target poison ticks (evolved/base) |
**Formulas:** `poison(t)` sets `numSlow = max(numSlow, t)` (status flag, consumed at ~0.5/tick) blocked by `numLoveShield`; the slow magnitude itself is applied through the status system (move + attack speed reduction while `numSlow>0`).
**Buffs/debuffs applied:** poison/slow debuff on enemies — durations 50 (basic), 70/50 main + 30/20 cloud (skill). Reduces target move & attack speed for the duration.
**Δ description vs code:** none — matches. "1.5x power poison arrow + poison cloud + slows nearby" = the skill's 1.5 multiplier + the `getEnemiesAtPos` AoE poison on up to 4/6 enemies. Evolved scales main/cloud durations, radius (50→60), and target count (4→6).
**Notes:** `objAtk={50:1}`, `objSkill={50:1}` (single hit each); `hitClassName="PhysicalHitEffect"`. The "reduces movement and attack speed" wording is the generic `poison()`/`numSlow` status, not a stat-buff call.

---

### Green Eagle — `GreenEagle1` (kindNum: 11, 36 evolved)
**Role:** ranged dps (air unit) with knockback skill
**Description (in-game):**
- Normal (`UNIT_NATK_11`/`_36`): "Soars through the sky and fires ranged projectiles at enemies."
- Skill (`UNIT_SATK_11`/`_36`): "Launches 3 consecutive wind attacks, dealing damage and knocking enemies back."
**How it works (code):** Air unit (`isAir=!0, airHeight=75`). Basic `attackMain`: `numShot=1` (single `GreenEagleBall1`). Skill `skillMain`: `numShot=3` ⇒ three consecutive balls. Each `GreenEagleBall1` on hit applies `knockBack(2*vx/s, 2*vy/s, 15)` (push along travel direction, 15-tick) and `chance(0.5)` to `poison(40)`. `multiShotDelay=3`.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| numShot (basic / skill) | 1 / 3 | balls per basic / skill |
| GreenEagleBall1 knockback | scale 2, dur 15 | per-hit knockback magnitude/duration |
| GreenEagleBall1 poison chance / dur | 0.5 / poison(40) | 50% to apply 40-tick slow |
| multiShotDelay | 3 | inter-shot frame delay |
| airHeight | 75 | flight height |
| normalSize / evolSize | 1.15 / 1.25 | sprite scale |
**Formulas:** knockback velocity = `2 * (vx,vy)/|v|` (normalized projectile direction ×2).
**Buffs/debuffs applied:** knockback (every hit) + 50% poison(40) slow on enemies.
**Δ description vs code:** **Minor delta — undocumented poison.** The description covers the "3 wind attacks + knockback" but omits the **50% chance to poison/slow (40 ticks)** that every Green Eagle projectile (basic AND skill) carries via `GreenEagleBall1.onHitMain`. Knockback applies on every hit, not just the skill. Validated: the `random.chance(.5)&&this.target.poison(40)` is on the shared weapon, so it fires on normal attacks too.
**Notes:** `weaponClass=YX.GreenEagleBall1`; `objAtk=objSkill={50:1}` (skill reuses attack frames). No evolved code branch (36 differs via book stats).

---

### Wind Mage — `WindMage1` (kindNum: 12, 37 evolved)
**Role:** mage / ranged AoE (multi-target tornado skill)
**Description (in-game):**
- Normal (`UNIT_NATK_12`/`_37`): "Launches an energy ball to attack enemies from range."
- Skill (`UNIT_SATK_12`): "Summons a tornado at the enemy's location, dealing sustained damage." (evolved `_37`: "Summons a tornado for longer, hitting more enemies and dealing sustained damage.")
**How it works (code):** Basic attack fires `weaponClass=YX.GreenEnergyBall` with `numShot = NUM_SHOT_1=1.5` (base) / `NUM_SHOT_2=2.5` (evolved). Skill `skillMain` picks `t = 2*evolStage+2` targets (2 base, 4 evolved): the locked target plus nearest enemies within `200`, and spawns a `Twist` (tornado) on each via `spawnTwist`, each whirling for `whirlTotal = WHIRL_TOTAL_1=70` (base) / `WHIRL_TOTAL_2=100` (evolved) ⇒ longer + more tornados when evolved.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| NUM_SHOT_1 / NUM_SHOT_2 | 1.5 / 2.5 | basic energy-ball count (base/evolved) |
| skill target count | 2*evolStage+2 → 2 / 4 | tornados spawned (base/evolved) |
| skill gather range | 200 | radius to collect extra tornado targets |
| WHIRL_TOTAL_1 / _2 | 70 / 100 | tornado whirl duration (base/evolved) |
| Twist setData | 0.3 | tornado per-tick damage multiplier |
**Formulas:** evolved skill targets `2*1+2 = 4` vs base `2*0+2 = 2`.
**Buffs/debuffs applied:** none (Twist deals sustained DoT, no stat debuff).
**Δ description vs code:** none — matches. "for longer, hitting more enemies" = WHIRL_TOTAL 70→100 and target count 2→4 when evolved. (`OBJ_ATK_1==OBJ_ATK_2={57:1}` and `OBJ_SKL_1==OBJ_SKL_2={101:1}` — frame sets identical; only counts/durations differ.)
**Notes:** `weaponClass=YX.GreenEnergyBall` (`MagicalHitEffect`, speed 9). Tornado is weapon class `Twist`, spawned procedurally, drifts toward target then whirls in place.

---

### Fairy — `Fairy1` (kindNum: 53, 54 evolved)
**Role:** support/healer (air) — HP/mana restore + move-speed buff aura skill
**Description (in-game):**
- Normal (`UNIT_NATK_53`/`_54`): "Soars through the sky and attacks from range with music-note bullets."
- Skill (`UNIT_SATK_53`): "Grants nearby allies a buff that restores HP and mana, and increases movement speed." (evolved `_54`: "Restores more HP and mana to nearby allies, with a stronger movement speed boost.")
**How it works (code):** Air unit (`isAir=!0, airHeight=62`). Basic `attackMain` fires `FairyMusicNote` projectiles with `numShot = evolved?2:1.5`. Skill `skillMain` gathers alive allies (excluding self) within `SKILL_RADIUS_SQ=122500` (radius 350), sorts by distance, and supports up to `SKILL_MAX_TARGETS=20` nearest. For each: `heal(amount, this, true)` where amount = `s=evolved?12:6` for normal allies, or `(evolved?1:0.5)` for castles; non-castle allies also gain `mana += e (evolved?10:5)`, an `addMoveSpeedBuff(this.kindNum, n, h)` with `n=evolved?0.35:0.25` value for `h=evolved?150:100` ticks, and the Fairy-wing visual.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| numShot (basic) | 1.5 / 2 | music-note bullets (base/evolved) |
| SKILL_RADIUS_SQ | 122500 | ally search radius² (= 350) |
| SKILL_MAX_TARGETS | 20 | max allies buffed/healed |
| heal (ally) | 6 / 12 | HP restored per ally (base/evolved) |
| heal (castle) | 0.5 / 1 | HP restored to castles (base/evolved) |
| mana restore | 5 / 10 | mana given per non-castle ally (base/evolved) |
| movspd buff value | 0.25 / 0.35 | move-speed buff magnitude (base/evolved) |
| movspd buff dur | 100 / 150 | buff duration (base/evolved) |
| airHeight | 62 | flight height |
**Formulas:** `moveSpd = orgMoveSpd*(1 + value)` ⇒ +25% (base) / +35% (evolved). Buff id = `this.kindNum` (53 or 54), so base & evolved Fairy buffs use different ids and SUM; two Fairies of the same tier share an id and take max (no stack).
**Buffs/debuffs applied (to allies):** `addMoveSpeedBuff(kindNum, 0.25/0.35, 100/150)`; plus direct HP heal and mana restore (not buff-system). Self excluded.
**Δ description vs code:** none — matches. "restores HP and mana + increases movement speed" maps exactly to `heal` + `mana +=` + `addMoveSpeedBuff`; evolved bumps all four (heal 6→12, mana 5→10, buff 0.25→0.35, dur 100→150). Castles get reduced heal and no mana/move buff (an undocumented nuance, not a contradiction).
**Notes:** Buff-id = kindNum is unusual (most units use a named `fQ.*` enum). Heal/mana are applied directly, not via `addMaxHealthBuff`.

---

### (Druid / vine-controller) — `Druid1` (kindNum: **no matching description in `/tmp/unit_desc.json`**)
**Role:** crowd-control / area-denial summoner — fires seeking tendrils that root (bind) enemies and apply DoT, spreading on kill
**Description (in-game):** No "Druid"/vine/tangle entry in `/tmp/unit_desc.json` (exhaustively searched). Documented from code only.
**How it works (code):** Basic `attackMain` spawns `TENDRIL_COUNT=4` seeking tendrils in a `TENDRIL_SPREAD_ARC=0.6π` fan toward the target; tendrils crawl (`TENDRIL_SPEED=7`, random-turning) up to `TENDRIL_MAX_DIST=280`, leaving trail effects, and on contact (`TENDRIL_HIT_RADIUS=24`) call `attachVine` on ground enemies (air units immune). A **vine** grows for `VINE_GROW_FRAMES=10`, then `binding(VINE_BIND_FRAMES=60)` roots the target and deals `VINE_DMG_PCT=1` damage every `VINE_DMG_INTERVAL=30` ticks until `VINE_TOTAL_LIFE=150`. `execute()` also runs `autoTangleCCEnemies()` — any enemy within `TANGLE_SEARCH_RANGE=400` already suffering knockback/blow/stun/freeze/shock gets auto-vined. `onKillEnemy` triggers `spreadAtPosition` — vines spread to up to `SPREAD_COUNT=4` nearby enemies within `SPREAD_RADIUS=150`. **Skill** (`skillMain`) spawns large `DruidDrill1` projectiles (`whirlTotal=90`, scale 3, `setData(0.6)`): toward the main target + a divergent second target (`pickDivergentTarget`), or two random-direction drills if no enemies in range (400).
**Hard values:**
| variable | value | meaning |
|---|---|---|
| TENDRIL_COUNT | 4 | tendrils per basic attack |
| TENDRIL_SPREAD_ARC | 0.6π | fan width |
| TENDRIL_SPEED / _MAX_DIST | 7 / 280 | crawl speed / max range |
| TENDRIL_HIT_RADIUS | 24 | contact radius to attach a vine |
| TENDRIL_MAX_TURN | 0.15 | per-tick random turn |
| VINE_GROW_FRAMES | 10 | grow time before binding |
| VINE_BIND_FRAMES | 60 | root/bind duration |
| VINE_TOTAL_LIFE | 150 | total vine lifetime |
| VINE_DMG_INTERVAL / _PCT | 30 / 1 | DoT every 30 ticks at 1.0× |
| TANGLE_SEARCH_RANGE | 400 | auto-tangle + skill search range |
| SPREAD_RADIUS / SPREAD_COUNT | 150 / 4 | on-kill vine spread radius / max |
| DruidDrill1 whirlTotal / setData | 90 / 0.6 | skill drill duration / dmg mult |
**Formulas:** DoT total ≈ `floor((150-grow)/30)` ticks × `VINE_DMG_PCT(1)` per vine while bound.
**Buffs/debuffs applied:** `binding(60)` (root/immobilize) on vined enemies + periodic damage; auto-applies to already-CC'd enemies; spreads on kill. Air units exempt throughout.
**Δ description vs code:** **No in-game description to compare** — kindNum text absent from `/tmp/unit_desc.json`. Behavior is a self-contained vine/root control system; flagged as undocumented.
**Notes:** Distinct from Druid2 (`v2`, a 5-direction archer) which immediately follows it in the bundle. `normalSize=.75`, `evolSize=.8`. `objAtk={86:1}`, `objSkill={152:1}`. No explicit `evolStage` branch in this class body (evolution via book stats / weapon).
