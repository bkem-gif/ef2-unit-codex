# EF2 unit mechanics — Part 6 (12 classes)

Source bundle: `runtime/bundles/mounted/1.11.42/assets/index.js` (v1.11.42).
All classes extend base `qQ`. Tick rate ≈ 60/s at 1× game speed.

---

### Red Slime — `SlimeRed` (kindNum: 20002)
**Role:** basic enemy (trivial melee minion)
**Description (in-game):**
- Normal (`UNIT_NATK_20002`): "None"
- Skill (`UNIT_SATK_20002`): "Special Skill"
**How it works (code):** Pure data-only class — `initializeData()` sets `sheetName="KingSlime"` and animation frames; everything else inherits from `qQ`. No `attackMain`/`skill`/`execute` overrides, no `hasSkill` (defaults false). It is a stock melee body that walks into range and lands one hit on the `objAtk` frame. Visually a recolor of the shared KingSlime spritesheet (same as SlimeBlue/SlimeYellow). The "None"/"Special Skill" description text is a placeholder used for all non-hero enemy minions.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| radius | 7 | collision radius |
| hitHeight | 15 | hit-box height |
| objAtk | {36:1} | hit fires on attack-anim frame 36, 1 hit |
| idle/move/attack/skill/die frames | 0-19 / 20-30 / 31-41 / 31-41 / 42-54 | animation ranges (skill = attack) |
**Formulas:** n/a (no buffs/skills; uses inherited damage from spawn stats).
**Buffs/debuffs applied:** none
**Δ description vs code:** none — matches. Description is the generic minion placeholder; code is a plain melee attacker with no skill.
**Notes:** `skillFrames` aliased to `attackFrames` (31-41), confirming there is no distinct skill animation. Identical structure to SlimeBlue/SlimeYellow/KingSlime base.

---

### Yellow Slime — `SlimeYellow` (kindNum: 20004)
**Role:** basic enemy (trivial melee minion)
**Description (in-game):**
- Normal (`UNIT_NATK_20004`): "None"
- Skill (`UNIT_SATK_20004`): "Special Skill"
**How it works (code):** Identical structure to SlimeRed — data-only class sharing the `sheetName="KingSlime"` spritesheet, same frame ranges, same `objAtk={36:1}`. No overrides; inherits all combat behavior from `qQ`. A plain melee attacker, just a different palette/kindNum.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| radius | 7 | collision radius |
| hitHeight | 15 | hit-box height |
| objAtk | {36:1} | hit on frame 36, 1 hit |
| idle/move/attack/die frames | 0-19 / 20-30 / 31-41 / 42-54 | animation ranges |
**Formulas:** n/a
**Buffs/debuffs applied:** none
**Δ description vs code:** none — matches (generic placeholder description; plain melee body).
**Notes:** Byte-for-byte the same init logic as SlimeRed apart from `className`. Slime variants (Red/Yellow/Blue) are summoned/spawned by the Dark Hermit boss (its `kindNums:[20002,20003,20004]`).

---

### Hammer Mole — `HammerMole` (kindNum: 40001)
**Role:** boss (immobile turret/castle-type boss; status-immune)
**Description (in-game):**
- Normal (`UNIT_NATK_40001`): "Knockback"
- Skill (`UNIT_SATK_40001`): "Special Skill"
**How it works (code):** Stationary boss (`moveSpd=0`, big `radius=40`, `hitHeight=140`, visible health bar). It is clickable (`pointerdown` → toggles its attack-range overlay via `JB`). Melee `attackMain()`: grabs all enemies within 150; on attack frames 40/56 it knocks units on its left back with `blow(-5,-7)` and on other hit-frames knocks right-side units with `blow(5,-7)`, then `doMeleeAttack`. Mana-style skill `skillMain()`: gathers enemies within 300 and, for each, with `random.chance(.6)` fires a `MoleFire` projectile via `generateWeapon`. Has 4 attack hit-frames `{40,48,56,62}` and 2 skill hit-frames `{93,97}`. **Completely status-immune**: `stun/knockBack/freeze/curse/silence/poison/blow/binding/shock/onHitted/addDotDamage` are all overridden to no-ops. `lookAt` is locked to face left (`super.lookAt(-1)`). `gotoMoveState`/`doMove` are no-ops (never moves).
**Hard values:**
| variable | value | meaning |
|---|---|---|
| moveSpd | 0 | immobile boss |
| radius / hitHeight | 40 / 140 | large body |
| maxMana | 300 | mana pool (gates skill via inherited logic) |
| atkRange (getEnemiesWithin) | 150 | melee skill scan radius (attackMain) |
| skill scan radius | 300 | `MoleFire` skill range |
| MoleFire fire chance | 0.6 | per-enemy chance to launch a projectile in skill |
| blow (left) | (-5,-7) | knockback vector for enemies on its left |
| blow (right) | (5,-7) | knockback vector for enemies on its right |
| objAtk | {40:1,48:1,56:1,62:1} | 4 melee hit frames |
| objSkill | {93:1,97:1} | 2 skill hit frames |
| firePoint | (0,-80) | projectile spawn offset |
| weaponClass | YX.Rock (default), YX.MoleFire (skill) | projectile types |
**Formulas:** projectile spawn jitter: `x = this.x + firePoint.x + 15 − 30·rand`, `y = this.y + firePoint.y + 10·rand`; aim `rotation = atan2(dy,dx)`.
**Buffs/debuffs applied:** debuff — knockback on every melee hit (the "Knockback" normal attack), via `blow(±5,−7)`.
**Δ description vs code:** none — matches. "Knockback" = the directional `blow` on melee hits; "Special Skill" = the `MoleFire` barrage. Both are present; descriptions are the generic boss placeholders.
**Notes:** A defending boss-objective: it does not chase (`doMove` empty), only attacks enemies that enter range. Status immunity makes it un-CC-able. The `MoleFire` skill is a probabilistic AoE shower (each of up to N nearby enemies has a 60% chance to be shot).

---

### Mole Soldier 1 — `MoleSoldier1` (kindNum: 40002)
**Role:** basic enemy (trivial melee minion)
**Description (in-game):**
- Normal (`UNIT_NATK_40002`): "None"
- Skill (`UNIT_SATK_40002`): "Special Skill"
**How it works (code):** Data-only class (shares `sheetName="HammerMole"` spritesheet). No combat overrides — a plain melee attacker that lands one hit on `objAtk` frame 56. Inherits all damage/targeting from `qQ`. The small foot-soldier add for the Hammer Mole boss.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| radius | 7 | collision radius |
| hitHeight | 27 | hit-box height |
| objAtk | {56:1} | hit on frame 56, 1 hit |
| idle/move/attack/die frames | 0-29 / 30-46 / 47-71 / 72-111 | animation ranges |
**Formulas:** n/a
**Buffs/debuffs applied:** none
**Δ description vs code:** none — matches (generic placeholder; plain melee minion).
**Notes:** Differs from MoleSoldier2 only in `hitHeight` (27 vs 33) — MoleSoldier2 is the slightly taller/bigger variant; both share identical frames and `objAtk`.

---

### Mole Soldier 2 — `MoleSoldier2` (kindNum: 40003)
**Role:** basic enemy (trivial melee minion)
**Description (in-game):**
- Normal (`UNIT_NATK_40003`): "None"
- Skill (`UNIT_SATK_40003`): "Special Skill"
**How it works (code):** Data-only class, `sheetName="HammerMole"`, identical frame ranges and `objAtk={56:1}` to MoleSoldier1. No overrides; plain melee attacker. Only the hit-box height differs (33 vs MoleSoldier1's 27), i.e. a bigger mole add.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| radius | 7 | collision radius |
| hitHeight | 33 | hit-box height (taller than MoleSoldier1) |
| objAtk | {56:1} | hit on frame 56, 1 hit |
| idle/move/attack/die frames | 0-29 / 30-46 / 47-71 / 72-111 | animation ranges |
**Formulas:** n/a
**Buffs/debuffs applied:** none
**Δ description vs code:** none — matches.
**Notes:** Only delta vs MoleSoldier1 is `hitHeight`. No `evolStage` gating in either.

---

### Dark Hermit — `DarkHermit` (kindNum: 50001)
**Role:** boss (immobile mana-gated caster boss; status-immune; slime summoner)
**Description (in-game):**
- Normal (`UNIT_NATK_50001`): "Knockback"
- Skill (`UNIT_SATK_50001`): "Special Skill"
**How it works (code):** Stationary boss (`moveSpd=0`, `radius=40`, `hitHeight=140`, health bar shown), clickable to toggle a range overlay (same `JB` pattern as Hammer Mole). Melee `attackMain()`: for every enemy within 150 it computes a radial unit vector and calls `i.knockBack(3·dx/e, 3·dy/e, 30)` (knockback magnitude 3, duration 30) then `doMeleeAttack` — i.e. it shoves all nearby enemies outward. **Mana-gated skill**: `execute()` triggers `gotoSkillState()` when `mana >= maxMana + 100` (= 400). `skillMain()` loops `MISSILE_COUNT=10` times, cycling through enemies within 280 and firing a `DarkHermitMissile` (`generateWeapon(..., 1)`, damage-scale 1) at each (round-robins targets if fewer than 10). **Status-immune**: `stun/knockBack/freeze/curse/silence/poison/blow/binding/shock/onHitted/addDotDamage` all no-op. Locked facing (`lookAt → super.lookAt(-1)`), never moves. Holds `kindNums:[20002,20003,20004]` and a `slimeVO` (slime spawn data) — the slime-summoning boss.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| moveSpd | 0 | immobile boss |
| radius / hitHeight | 40 / 140 | large body |
| maxMana | 300 | mana pool |
| skill trigger | mana ≥ maxMana+100 = 400 | fires skill when overfilled by 100 |
| MISSILE_COUNT | 10 | DarkHermitMissiles per skill cast |
| melee scan radius | 150 | `getEnemiesWithin(150)` in attackMain |
| skill scan radius | 280 | `getEnemiesWithin(280)` in skillMain |
| knockBack | (3·dx/e, 3·dy/e, 30) | radial shove, magnitude 3, duration 30 |
| objAtk | {36:1} | melee hit on frame 36 |
| weaponClass | YX.Rock (default), YX.DarkHermitMissile (skill) | projectile types |
| kindNums | [20002,20003,20004] | summonable Red/Blue/Yellow slimes |
**Formulas:** radial knockback unit vector `(dx/e, dy/e)` where `e=sqrt(dx²+dy²)` (clamped to 1 if 0), scaled ×3. Skill target cycling: `target = list[i % list.length]` for `i in 0..9`.
**Buffs/debuffs applied:** debuff — radial knockBack on every melee hit (magnitude 3, dur 30).
**Δ description vs code:** none — matches. "Knockback" = the radial melee shove; "Special Skill" = the 10-missile barrage. The slime kindNums/slimeVO confirm it is the slime-summoning boss of this map (slimes spawn via map/wave logic referencing those kinds).
**Notes:** Same immobile/status-immune boss archetype as Hammer Mole, but skill is **deterministic** (always exactly 10 missiles) and **mana-gated** rather than the probabilistic per-enemy roll Hammer Mole uses. Threshold of `maxMana+100` means it must overcharge before each cast.

---

### Clam Soldier — `Crab` (kindNum: 50003)
**Role:** ranged enemy (trivial ranged minion)
**Description (in-game):**
- Normal (`UNIT_NATK_50003`): "None"
- Skill (`UNIT_SATK_50003`): "Special Skill"
**How it works (code):** Data-only class but configured as a **ranged** attacker: `weaponClass=YX.Pearl` and `firePoint=(46,-14)`. No combat-method overrides — uses inherited `qQ` ranged behavior to lob a `Pearl` projectile at the nearest enemy in range, hit registered on `objAtk` frame 55. Shares `sheetName="DarkHermit"` spritesheet (a Dark Hermit map add). Internal class name is "Crab" but its in-game name is "Clam Soldier".
**Hard values:**
| variable | value | meaning |
|---|---|---|
| radius | 7 | collision radius |
| hitHeight | 27 | hit-box height |
| weaponClass | YX.Pearl | fires Pearl projectiles |
| firePoint | (46,-14) | projectile spawn offset |
| objAtk | {55:1} | projectile released on frame 55 |
| idle/move/attack/die frames | 0-29 / 30-50 / 51-63 / 65-104 | animation ranges |
**Formulas:** n/a (inherited ranged-attack/projectile logic).
**Buffs/debuffs applied:** none
**Δ description vs code:** none — matches. It is a basic ranged minion; the only non-default is being a Pearl-throwing ranged unit rather than melee.
**Notes:** Only one of the three Dark-Hermit map adds that is ranged (StarFish is melee). `weaponClass` + `firePoint` are the sole behavioral difference from a stock melee minion.

---

### Starfish Soldier — `StarFish` (kindNum: 50002)
**Role:** basic enemy (trivial melee minion)
**Description (in-game):**
- Normal (`UNIT_NATK_50002`): "None"
- Skill (`UNIT_SATK_50002`): "Special Skill"
**How it works (code):** Data-only class, `sheetName="DarkHermit"`. No `weaponClass` set → default melee. No overrides; lands one hit on `objAtk` frame 64. A plain melee add for the Dark Hermit boss map.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| radius | 7 | collision radius |
| hitHeight | 15 | hit-box height |
| objAtk | {64:1} | melee hit on frame 64 |
| idle/move/attack/die frames | 0-29 / 30-46 / 47-76 / 77-116 | animation ranges |
**Formulas:** n/a
**Buffs/debuffs applied:** none
**Δ description vs code:** none — matches (generic placeholder; plain melee minion).
**Notes:** Melee counterpart to the ranged Crab/Clam on the same DarkHermit spritesheet.

---

### Unicorn Archer — `Unicorn1` (kindNum: 51, 52 evolved)
**Role:** ranged dps (multi-target arcing archer; player hero unit, evolution-gated)
**Description (in-game):**
- Normal (`UNIT_NATK_51`): "Fires arcing arrows that can hit up to 3 enemies at once."
- Skill (`UNIT_SATK_51`): "Fires a volley of arcing arrows in succession, dealing damage to enemies across a wide area."
- Evolved Normal (`UNIT_NATK_52`): "Fires arcing arrows that can hit up to 3 enemies at once."
- Evolved Skill (`UNIT_SATK_52`): "Fires more arcing arrows at a faster rate, dealing damage to enemies across a wide area."
**How it works (code):** Ranged hero firing `UniArrow` projectiles. **Normal attack** (`onAttackStartFrame`): builds `targetList = getAttackableEnemyList(3)` (up to 3 targets), pinning the current `target` to the front. `attackMain()` calls `fireNextAttackTarget()` once, and if `numShot >= 1.5` (only true when evolved, numShot=1.2 < 1.5 so this is FALSE — see Δ) it would roll a 35% chance for a second shot. `fireNextAttackTarget` round-robins through the (≤3) target list doing a `doRangeAttack`. **Skill** (`onSkillStartFrame`): gathers `getEnemiesWithin(220, true)` plus the current target into `skillTargetList`. `skillMain()` fires a burst whose size depends on evolStage: base `t = chance(0.65)?2:1`; evolved `t = rand<0.3?3 : rand<0.6?2 : 1` (so evolved averages more arrows). Each arrow is a `UniArrow` fired with a random arc angle `riseAngleDeg = 35 + 20·rand`. Hit frames: attack `{40,45,51}`, skill `{76,82,88,91}` (identical for base and evolved).
**Hard values:**
| variable | value | meaning |
|---|---|---|
| NUM_SHOT_1 (base) | 1 | normal-attack shot multiplier |
| NUM_SHOT_2 (evolved) | 1.2 | normal-attack shot multiplier (evolved) |
| max normal targets | 3 | `getAttackableEnemyList(3)` |
| extra-shot threshold | numShot ≥ 1.5 | gate for bonus normal shot (never met) |
| extra-shot chance | 0.35 | bonus normal shot probability (if gate met) |
| skill scan radius | 220 | `getEnemiesWithin(220,true)` |
| skill burst (base) | 2 @ 65% else 1 | arrows per skill cast, base |
| skill burst (evolved) | 3 (30%) / 2 (30%) / 1 (40%) | arrows per skill cast, evolved |
| skill arc angle | 35 + 20·rand deg | per-arrow `riseAngleDeg` |
| OBJ_ATK (both) | {40:1,45:1,51:1} | 3 normal hit frames |
| OBJ_SKL (both) | {76:1,82:1,88:1,91:1} | 4 skill hit frames |
| firePoint | (20,-34) | arrow spawn offset (×direction×size) |
| normalSize / evolSize | 0.95 / 1.02 | sprite scale base/evolved |
| weaponClass | YX.UniArrow | arcing-arrow projectile |
**Formulas:** arrow spawn `x = this.x + firePoint.x·direction·currentSize`, `y = this.y + firePoint.y·currentSize`; arc `riseAngleDeg = 35 + 20·rand`. evolStage gating in `setData`: `evolStage>=1` ⇒ `numShot=NUM_SHOT_2(1.2)` + OBJ_ATK_2/OBJ_SKL_2, else NUM_SHOT_1(1)/OBJ_ATK_1.
**Buffs/debuffs applied:** none (pure damage).
**Δ description vs code:** **mostly matches, one dead branch.** "Hit up to 3 enemies" = the `getAttackableEnemyList(3)` cap — confirmed. The evolved description "fires more arrows at a faster rate": the skill **does** fire more arrows when evolved (up to 3 vs base 2) — confirmed. BUT the normal-attack double-shot branch `numShot >= 1.5 && chance(.35)` is **unreachable**: the max `numShot` is `NUM_SHOT_2 = 1.2 < 1.5`, so a second normal-attack arrow is **never** fired even when evolved. Evolved Unicorn's only real combat upgrades are the richer skill burst distribution and OBJ_ATK_2/OBJ_SKL_2 (which are identical to OBJ_ATK_1/OBJ_SKL_1 anyway) + slightly larger sprite. So the evolved normal attack is effectively identical to base — the `numShot` 1.2 value buys nothing because the 1.5 threshold is never crossed.
**Notes:** This is a player-side hero (UNIT_NAME 51/52), unlike the rest of this batch which are enemy/reward units. evolStage set in `setData(i,s,e,n)`. The "1.2 vs 1.5" gap is the only genuine code-vs-intent oddity — looks like the threshold was meant to be ≤1.2 (or NUM_SHOT_2 meant to be ≥1.5) so evolved would actually double-fire.

---

### Ice Wolf — `IceWolf` (kindNum: 1003)
**Role:** summoned melee dps (freeze-on-hit wolf summon)
**Description (in-game):**
- Normal (`UNIT_NATK_1003`): "None"
- Skill (`UNIT_SATK_1003`): "Special Skill"
**How it works (code):** A summoned wolf with **fully hard-coded combat stats** (unlike the spawn-stat minions above). Melee `attackMain()` calls `super.attackMain()` then, if the target is alive, rolls `random.chance(.25)` to `target.freeze(70)` — a 25% chance to freeze for 70 ticks (~1.17 s at 1×) on each hit. Single melee hit on `objAtk` frame 54. Fast mover (`moveSpd=2.2`). Sprite scaled to 0.9.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| maxHp / hp | 100 | health |
| atkDmg | 10 | attack damage |
| def | 10 | defense |
| moveSpd | 2.2 | movement speed |
| atkDuration | 100 | attack interval (ticks) |
| atkRange | 15 | melee range |
| freeze chance | 0.25 | chance to freeze on each hit |
| freeze duration | 70 | freeze ticks (~1.17 s) |
| objAtk | {54:1} | melee hit on frame 54 |
| hitHeight / hitWidth / radius | 20 / 15 / 13 | hit box |
| size | 0.9 | sprite scale |
| idle/move/attack/die frames | 0-29 / 30-39 / 40-69 / 70-104 | animation ranges |
**Formulas:** attack interval is the hard `atkDuration=100` (not `1e4/atkSpd`, since this unit sets atkDuration directly).
**Buffs/debuffs applied:** debuff on enemy — `freeze(70)` at 25% per hit.
**Δ description vs code:** none — matches. "Special Skill" placeholder corresponds to the freeze-on-hit proc (it has no separate active skill, `skillFrames` alias attackFrames 40-69). The "None"/"Special Skill" text is the generic summon placeholder; the real mechanic is the freeze proc.
**Notes:** This is the wolf summoned by Wolf-Rider type units (kindNum 1003 in the 100x summon block alongside Wolf=1001, Graveyard Hero=1002). It carries its own fixed stats rather than scaling off a summoner, except whatever scaling the summon code applies. No evolStage branch.

---

### Gold Goblin — `GoldGoblin` (no combat kindNum — gold-reward unit)
**Role:** reward unit (clickable gold piñata; wander/flee AI, non-combatant)
**Description (in-game):** No `UNIT_NATK`/`UNIT_SATK` entry — it is not a combat unit. Player-facing tip (`TIP_DESC_33`): "Try quickly tapping the Gold Goblin that appears during the game 10 times." (matches `MAX_LIVES=10`.)
**How it works (code):** A clickable bonus object that spawns, wanders, drops gold when tapped, and flees/expires. `atkDmg=0`, `def=0`, `atkDuration=9999`, `atkRange=0`, empty `objAtk` — **deals no damage and never attacks**. `onClicked`: decrements `lives` (starts at `MAX_LIVES=10`), plays `SFX_GOLD_GOBLIN`; if `lives<=0` it calls `onGoldDropMulti(x,y,0,DEATH_COINS=30)` and dies; otherwise drops `onGoldDropMulti(x,y,0,COINS_PER_CLICK=5)`, plays its attack/hurt animation, and on the next `doAttack` (after a speed-scaled `fleeDelay = round(8·(speed−1))`) calls `flee()`. `flee()` picks a random point 150-250px away (`150 + 100·rand` at angle `rand·2π`, clamped to bounds) and dashes there at `FLEE_SPEED=5`. `doIdle()` decrements `lifetime` (starts `LIFETIME=1800` ticks ≈ 30 s); on expiry `escapeAndRemove()` runs it off the nearest screen edge at `2·FLEE_SPEED=10` and self-destructs after 3000 ms. Otherwise it wanders: every `wanderInterval = 120 + rand(180)` ticks it picks a new wander target (30% chance an off-screen edge point, else an on-screen point) and walks at `NORMAL_SPEED=1.5`. `execute()` has a game-speed compensation that divides `orgMoveSpd`/`incFrame` by the speed multiplier while moving so its travel speed stays constant regardless of fast-forward.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| MAX_LIVES | 10 | taps needed to "kill" it (drops big reward) |
| COINS_PER_CLICK | 5 | coins dropped per non-final tap |
| DEATH_COINS | 30 | bonus coins on the final (10th) tap |
| NORMAL_SPEED | 1.5 | wander move speed |
| FLEE_SPEED | 5 | dash speed after being tapped |
| escape speed | 10 | 2×FLEE_SPEED when lifetime expires |
| LIFETIME | 1800 | ticks alive before it escapes (~30 s @1×) |
| wanderInterval | 120 + rand(180) | ticks between wander re-targets |
| flee distance | 150 + 100·rand px | dash distance after a tap |
| fleeDelay | round(8·(speed−1)) | tick delay before fleeing (0 at 1× speed) |
| escape removal | 3000 ms | setTimeout to die after running off-screen |
| maxHp | 100 | nominal (never damaged — only tap-based lives) |
**Formulas:** `fleeDelay = round(8·(gameSpeed − 1))` (so at 1× it flees immediately; faster speeds add reaction delay). Game-speed move compensation in `execute()`: temporarily `orgMoveSpd /= speed`, `incFrame /= speed` while MOVE state and `speed>1`.
**Buffs/debuffs applied:** none (no combat interaction). Drops gold via `onGoldDropMulti` callback.
**Δ description vs code:** none to a combat description (it has none). Matches the in-game tip: tap it 10× — confirmed by `MAX_LIVES=10`, with 5 coins per tap and a 30-coin jackpot on the kill. No mismatch.
**Notes:** Special non-combat reward object. Re-poolable via `resetGoldGoblin()`. The `onGoldDropMulti` callback is wired by the spawner to credit the player. Its `attack` animation is repurposed purely as the "got tapped, recoil + flee" reaction, not a real attack.

---

### Ads Goblin — `AdsGoblin` (no combat kindNum — watch-ad reward unit)
**Role:** reward unit (clickable rewarded-ad trigger; untargetable, indestructible, non-combatant)
**Description (in-game):** No `UNIT_NATK`/`UNIT_SATK` entry — not a combat unit.
**How it works (code):** A clickable object that walks across the screen and, when tapped, fires the rewarded-ad callback. Made effectively indestructible and ignored by combat: `maxHp=9999`, `def=9999`, `isUntagetable=true`, `healthBarVisible=false`, `atkDmg=0`, `atkDuration=9999`, `atkRange=0`, empty `objAtk`. Moves through a scripted **phase machine** (phases 1→8): in each idle phase it waits `~180-300` ticks (`phaseTimer >= base + rand`) glancing left/right on a random `lookInterval = 40 + floor(50·rand)`, then `nextMovePhase` walks it to the next x-target (`setMoveTarget` along x only). The phase targets march it leftward/rightward across the field: phase 2→`320+60·rand`, 4→`170+60·rand`, 6→`50+60·rand`, 8→`-100` (walks off-screen, where `onPhaseArrived` sets `visible=false, removed=true`). It uses two alternating walk animations (`moveFramesA` 30-49 / `moveFramesB` 50-69, `useMoveB = chance(.3)`, and when using B it flips its facing). **`onClicked`**: if alive and not already `waiting`, sets `waiting=true`, goes idle, and calls `onAdsReward(x,y)` — the rewarded-ad popup hook. `resumeWalking()` polls `requestAnimationFrame` until `waitTimer >= WAIT_AFTER_POPUP=120` then resumes its phase march via `resumeMovement()`.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| maxHp | 9999 | effectively indestructible |
| def | 9999 | effectively indestructible |
| isUntagetable | true | enemies/allies cannot target it |
| NORMAL_SPEED | 0.7 | walk speed (slow stroll) |
| WAIT_AFTER_POPUP | 120 | ticks to wait after ad popup before resuming |
| lookInterval | 40 + floor(50·rand) | ticks between random facing flips |
| phase 1 wait | 180 + rand(120) | ticks idling before move phase 2 |
| phase 3 wait | 240 + rand(120) | ticks idling before move phase 4 |
| phase 5 wait | 180 + rand(120) | ticks idling before move phase 6 |
| phase 7 wait | 120 + rand(60) | ticks idling before final exit (phase 8) |
| move targets | 320 / 170 / 50 / -100 (+60·rand except last) | x-positions for phases 2/4/6/8 |
| useMoveB chance | 0.3 | chance to use alt walk anim (flips facing) |
| healthBarVisible | false | no HP bar |
**Formulas:** movement (`doMove`) is hand-rolled: unit-vector step toward `(tx,ty)` at `moveSpd`, snapping to target when within `moveSpd²`; facing flips on `useMoveB`. No combat formulas.
**Buffs/debuffs applied:** none. Triggers `onAdsReward` callback on tap (rewarded-ad flow).
**Δ description vs code:** none to a combat description (it has none). Behavior is internally consistent: an untargetable, indestructible billboard goblin that grants a reward when tapped to watch an ad.
**Notes:** Special non-combat reward object, distinct from GoldGoblin in that (a) it is single-reward (one tap → ad popup, not 10 taps), (b) it is `isUntagetable` + 9999 HP/def so combat never touches it, (c) it auto-exits after its 8-phase walk rather than on a lifetime countdown. Re-poolable via `resetAdsGoblin()`. NOTE: a minor minification artifact — its `resumeWalking` reuses the bundle's `Kt` helper name as a local `requestAnimationFrame` callback wrapper (`Kt(()=>{...},"checkResume")`), unrelated to the class-registration `Kt`.

---

## Cross-cutting notes
- **Trivial minions** (SlimeRed, SlimeYellow, MoleSoldier1/2, StarFish) and the **ranged minion** (Crab) are data-only: they inherit all combat from `qQ`; only frame ranges / `objAtk` / (for Crab) `weaponClass`+`firePoint` differ. Their "None / Special Skill" descriptions are generic enemy placeholders, not real skills.
- **Bosses** (HammerMole, DarkHermit) share an archetype: immobile, big body, health bar, click-to-show-range, and **total status immunity** (all CC methods overridden to no-ops). HammerMole's skill is probabilistic (60%/enemy MoleFire), DarkHermit's is deterministic (10 missiles) and mana-gated (≥400). DarkHermit additionally carries the slime kindNums it summons.
- **Reward units** (GoldGoblin, AdsGoblin) have **no combat kindNum** — they are clickable bonus objects (gold-per-tap piñata vs single-tap watch-ad trigger) with their own wander/flee/phase AI and game-speed compensation; they deal/take no damage.
