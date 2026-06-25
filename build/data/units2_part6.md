# EF2 unit mechanics — Part 6 (12 classes)

Source bundle: `runtime/bundles/mounted/1.11.42/assets/index.js` (v1.11.42).
All classes extend base `qQ`. Tick rate ≈ 60/s at 1× game speed.

---

### Red Slime — `SlimeRed` (kindNum: 20002)
**TL;DR.** A trivial melee minion that just walks into range and hits once — no real skill.

**At a glance**
- **Role:** Basic enemy (trivial melee minion)
- **Attack:** plain melee, one hit on attack frame 36
- **Skill:** none (inherits all combat from base; `hasSkill` defaults false)
- **Sprite:** recolor of the shared KingSlime spritesheet (like SlimeBlue/SlimeYellow)

**In-game text**
- Normal: "None"
- Skill: "Special Skill"  (generic placeholder used for all non-hero enemy minions)

**Normal attack**
- Data-only class: `initializeData()` sets the spritesheet and frames; everything else inherits from `qQ`. Walks into range and lands a single hit on the `objAtk` frame. Damage comes from inherited spawn stats.

**Key values**
| variable | value | meaning |
|---|---|---|
| radius | 7 | collision radius |
| hitHeight | 15 | hit-box height |
| objAtk | {36:1} | 1 hit on attack-anim frame 36 |
| idle/move/attack/skill/die frames | 0-19 / 20-30 / 31-41 / 31-41 / 42-54 | animation ranges (skill = attack) |

**✓ Matches description** — the "None"/"Special Skill" text is the generic minion placeholder; the code is a plain melee attacker with no skill.

**Notes**
- `skillFrames` aliased to `attackFrames` (31-41), confirming no distinct skill animation. Identical structure to SlimeBlue/SlimeYellow/KingSlime base.

---

### Yellow Slime — `SlimeYellow` (kindNum: 20004)
**TL;DR.** A trivial melee minion identical to Red Slime apart from palette and id.

**At a glance**
- **Role:** Basic enemy (trivial melee minion)
- **Attack:** plain melee, one hit on attack frame 36
- **Skill:** none (inherits all combat from base)
- **Sprite:** shares the KingSlime spritesheet; just a different palette/kindNum

**In-game text**
- Normal: "None"
- Skill: "Special Skill"  (generic placeholder)

**Normal attack**
- Data-only class, byte-for-byte the same init logic as SlimeRed apart from `className`. No overrides; plain melee body.

**Key values**
| variable | value | meaning |
|---|---|---|
| radius | 7 | collision radius |
| hitHeight | 15 | hit-box height |
| objAtk | {36:1} | 1 hit on frame 36 |
| idle/move/attack/die frames | 0-19 / 20-30 / 31-41 / 42-54 | animation ranges |

**✓ Matches description** — generic placeholder description; plain melee body.

**Notes**
- Slime variants (Red/Blue/Yellow) are summoned/spawned by the Dark Hermit boss (its `kindNums:[20002,20003,20004]`).

---

### Hammer Mole — `HammerMole` (kindNum: 40001)
**TL;DR.** An immobile, fully status-immune turret-boss that knocks attackers back on melee and rains a probabilistic projectile shower as its skill.

**At a glance**
- **Role:** Boss (immobile turret/castle-type; status-immune)
- **Melee:** knocks nearby enemies back directionally (left-side units shoved left, others right)
- **Skill:** scans enemies within 300, each has a 60% chance to be shot with a `MoleFire` projectile
- **Immobile & un-CC-able:** `moveSpd=0`; every CC method is a no-op; locked facing left

**In-game text**
- Normal: "Knockback"
- Skill: "Special Skill"

**Normal attack — knockback melee**
- `attackMain()` grabs all enemies within 150. On attack frames 40/56 it shoves left-side units back with `blow(-5,-7)`; on other hit-frames it shoves right-side units with `blow(5,-7)`, then `doMeleeAttack`. 4 hit frames `{40,48,56,62}`.

**Skill — MoleFire shower (mana-gated)**
- `skillMain()` gathers enemies within 300; for each, `random.chance(.6)` fires a `MoleFire` projectile via `generateWeapon`. A probabilistic AoE: up to N nearby enemies each have a 60% chance to be shot. 2 skill hit frames `{93,97}`.

**Passive / special**
- Completely status-immune: `stun/knockBack/freeze/curse/silence/poison/blow/binding/shock/onHitted/addDotDamage` all overridden to no-ops.
- Never moves: `gotoMoveState`/`doMove` are no-ops; `lookAt` locked to face left (`super.lookAt(-1)`). It defends rather than chases — only attacks enemies that enter range.
- Clickable (`pointerdown` toggles its attack-range overlay via `JB`).

**Buffs & debuffs**
- Knockback on every melee hit: `blow(-5,-7)` for left-side units, `blow(5,-7)` for right-side — this is the "Knockback" normal attack.

**Key values**
| variable | value | meaning |
|---|---|---|
| moveSpd | 0 | immobile boss |
| radius / hitHeight | 40 / 140 | large body |
| maxMana | 300 | mana pool (gates skill via inherited logic) |
| atkRange (attackMain scan) | 150 | melee scan radius |
| skill scan radius | 300 | `MoleFire` skill range |
| MoleFire fire chance | 0.6 | per-enemy chance to launch a projectile |
| blow (left) | (-5,-7) | knockback vector for enemies on its left |
| blow (right) | (5,-7) | knockback vector for enemies on its right |
| objAtk | {40:1,48:1,56:1,62:1} | 4 melee hit frames |
| objSkill | {93:1,97:1} | 2 skill hit frames |
| firePoint | (0,-80) | projectile spawn offset |
| weaponClass | YX.Rock (default), YX.MoleFire (skill) | projectile types |

**Formulas**
- Projectile spawn jitter: `x = this.x + firePoint.x + 15 − 30·rand`, `y = this.y + firePoint.y + 10·rand`; aim `rotation = atan2(dy,dx)`.

**✓ Matches description** — "Knockback" = the directional `blow` on melee hits; "Special Skill" = the `MoleFire` barrage. Both present; descriptions are the generic boss placeholders.

---

### Mole Soldier 1 — `MoleSoldier1` (kindNum: 40002)
**TL;DR.** A trivial melee foot-soldier add for the Hammer Mole boss; one hit, no skill.

**At a glance**
- **Role:** Basic enemy (trivial melee minion)
- **Attack:** plain melee, one hit on attack frame 56
- **Skill:** none (inherits all combat from base)
- **Sprite:** shares the HammerMole spritesheet

**In-game text**
- Normal: "None"
- Skill: "Special Skill"  (generic placeholder)

**Normal attack**
- Data-only class, no combat overrides. Lands one hit on `objAtk` frame 56; inherits damage/targeting from `qQ`.

**Key values**
| variable | value | meaning |
|---|---|---|
| radius | 7 | collision radius |
| hitHeight | 27 | hit-box height |
| objAtk | {56:1} | 1 hit on frame 56 |
| idle/move/attack/die frames | 0-29 / 30-46 / 47-71 / 72-111 | animation ranges |

**✓ Matches description** — generic placeholder; plain melee minion.

**Notes**
- Differs from MoleSoldier2 only in `hitHeight` (27 vs 33); MoleSoldier2 is the slightly taller variant. Same frames and `objAtk`.

---

### Mole Soldier 2 — `MoleSoldier2` (kindNum: 40003)
**TL;DR.** The taller variant of Mole Soldier 1 — same trivial melee body, bigger hit-box.

**At a glance**
- **Role:** Basic enemy (trivial melee minion)
- **Attack:** plain melee, one hit on attack frame 56
- **Skill:** none (inherits all combat from base)
- **Sprite:** shares the HammerMole spritesheet

**In-game text**
- Normal: "None"
- Skill: "Special Skill"  (generic placeholder)

**Normal attack**
- Data-only class, identical frame ranges and `objAtk={56:1}` to MoleSoldier1. No overrides; plain melee. Only the hit-box height differs (33 vs 27), i.e. a bigger mole add.

**Key values**
| variable | value | meaning |
|---|---|---|
| radius | 7 | collision radius |
| hitHeight | 33 | hit-box height (taller than MoleSoldier1) |
| objAtk | {56:1} | 1 hit on frame 56 |
| idle/move/attack/die frames | 0-29 / 30-46 / 47-71 / 72-111 | animation ranges |

**✓ Matches description** — generic placeholder; plain melee minion.

**Notes**
- Only delta vs MoleSoldier1 is `hitHeight`. No `evolStage` gating in either.

---

### Dark Hermit — `DarkHermit` (kindNum: 50001)
**TL;DR.** An immobile, status-immune caster-boss that radially shoves attackers on melee and fires a deterministic 10-missile barrage once its mana overcharges; it's the slime summoner of its map.

**At a glance**
- **Role:** Boss (immobile mana-gated caster; status-immune; slime summoner)
- **Melee:** radially knocks back every enemy within 150 (magnitude 3, dur 30)
- **Skill:** mana-gated — when mana ≥ 400, fires exactly 10 `DarkHermitMissile`s round-robin across enemies within 280
- **Summons:** carries slime `kindNums:[20002,20003,20004]` + a `slimeVO`

**In-game text**
- Normal: "Knockback"
- Skill: "Special Skill"

**Normal attack — radial knockback melee**
- `attackMain()`: for every enemy within 150, computes a radial unit vector and calls `i.knockBack(3·dx/e, 3·dy/e, 30)` (magnitude 3, duration 30) then `doMeleeAttack` — shoves all nearby enemies outward. Hit on `objAtk` frame 36.

**Skill — 10-missile barrage (mana ≥ 400)**
- `execute()` triggers `gotoSkillState()` when `mana >= maxMana + 100` (= 400) — it must overcharge by 100 before each cast.
- `skillMain()` loops `MISSILE_COUNT=10` times, cycling through enemies within 280 and firing a `DarkHermitMissile` (`generateWeapon(..., 1)`, damage-scale 1) at each. Round-robins targets if fewer than 10 are present. Always exactly 10 missiles (deterministic).

**Passive / special**
- Status-immune: `stun/knockBack/freeze/curse/silence/poison/blow/binding/shock/onHitted/addDotDamage` all no-op.
- Never moves; locked facing (`lookAt → super.lookAt(-1)`). Clickable to toggle a range overlay (same `JB` pattern as Hammer Mole).
- Slime-summoning boss: holds `kindNums:[20002,20003,20004]` and a `slimeVO`; slimes spawn via map/wave logic referencing those kinds.

**Buffs & debuffs**
- Radial knockBack on every melee hit: magnitude 3, duration 30, all enemies within 150.

**Key values**
| variable | value | meaning |
|---|---|---|
| moveSpd | 0 | immobile boss |
| radius / hitHeight | 40 / 140 | large body |
| maxMana | 300 | mana pool |
| skill trigger | mana ≥ maxMana+100 = 400 | fires when overfilled by 100 |
| MISSILE_COUNT | 10 | DarkHermitMissiles per cast |
| melee scan radius | 150 | `getEnemiesWithin(150)` in attackMain |
| skill scan radius | 280 | `getEnemiesWithin(280)` in skillMain |
| knockBack | (3·dx/e, 3·dy/e, 30) | radial shove, magnitude 3, dur 30 |
| objAtk | {36:1} | melee hit on frame 36 |
| weaponClass | YX.Rock (default), YX.DarkHermitMissile (skill) | projectile types |
| kindNums | [20002,20003,20004] | summonable Red/Blue/Yellow slimes |

**Formulas**
- Radial knockback unit vector `(dx/e, dy/e)` where `e=sqrt(dx²+dy²)` (clamped to 1 if 0), scaled ×3.
- Skill target cycling: `target = list[i % list.length]` for `i in 0..9`.

**✓ Matches description** — "Knockback" = the radial melee shove; "Special Skill" = the 10-missile barrage. The slime kindNums/slimeVO confirm it's the slime-summoning boss of the map.

**Notes**
- Same immobile/status-immune archetype as Hammer Mole, but the skill is deterministic (always 10 missiles) and mana-gated (≥400), vs Hammer Mole's probabilistic per-enemy roll.

---

### Clam Soldier — `Crab` (kindNum: 50003)
**TL;DR.** A trivial ranged minion that lobs Pearl projectiles at the nearest enemy; no skill.

**At a glance**
- **Role:** Ranged enemy (trivial ranged minion)
- **Attack:** ranged — fires a `Pearl` projectile, released on frame 55
- **Skill:** none (inherits all combat from base)
- **Sprite:** shares the DarkHermit spritesheet (a Dark Hermit map add)

**In-game text**
- Normal: "None"
- Skill: "Special Skill"  (generic placeholder)

**Normal attack — ranged Pearl throw**
- Data-only class configured as ranged: `weaponClass=YX.Pearl`, `firePoint=(46,-14)`. No combat-method overrides — uses inherited `qQ` ranged behavior to lob a Pearl at the nearest enemy in range; hit registered on `objAtk` frame 55.

**Key values**
| variable | value | meaning |
|---|---|---|
| radius | 7 | collision radius |
| hitHeight | 27 | hit-box height |
| weaponClass | YX.Pearl | fires Pearl projectiles |
| firePoint | (46,-14) | projectile spawn offset |
| objAtk | {55:1} | projectile released on frame 55 |
| idle/move/attack/die frames | 0-29 / 30-50 / 51-63 / 65-104 | animation ranges |

**✓ Matches description** — a basic ranged minion; the only non-default is being a Pearl-throwing ranged unit rather than melee.

**Notes**
- Internal class name is "Crab" but the in-game name is "Clam Soldier". Only ranged one of the three Dark-Hermit map adds (StarFish is melee). `weaponClass` + `firePoint` are the sole behavioral difference from a stock melee minion.

---

### Starfish Soldier — `StarFish` (kindNum: 50002)
**TL;DR.** A trivial melee add for the Dark Hermit map; one hit, no skill.

**At a glance**
- **Role:** Basic enemy (trivial melee minion)
- **Attack:** plain melee, one hit on attack frame 64
- **Skill:** none (inherits all combat from base)
- **Sprite:** shares the DarkHermit spritesheet; no `weaponClass` set → default melee

**In-game text**
- Normal: "None"
- Skill: "Special Skill"  (generic placeholder)

**Normal attack**
- Data-only class, no overrides. Lands one hit on `objAtk` frame 64.

**Key values**
| variable | value | meaning |
|---|---|---|
| radius | 7 | collision radius |
| hitHeight | 15 | hit-box height |
| objAtk | {64:1} | melee hit on frame 64 |
| idle/move/attack/die frames | 0-29 / 30-46 / 47-76 / 77-116 | animation ranges |

**✓ Matches description** — generic placeholder; plain melee minion.

**Notes**
- Melee counterpart to the ranged Crab/Clam on the same DarkHermit spritesheet.

---

### Unicorn Archer — `Unicorn1` (kindNum: 51 · Ⅱ 52)
**TL;DR.** A player-side arcing archer that pelts up to 3 enemies per shot and fires an arrow volley as its skill; evolving widens the skill burst but — due to a dead code branch — does not actually speed up the normal attack.

**At a glance**
- **Role:** Ranged DPS (multi-target arcing archer; player hero, evolution-gated)
- **Normal:** fires `UniArrow` at up to 3 targets, round-robin (hit frames 40/45/51)
- **Skill:** an arc-angled arrow burst — base 1–2 arrows, Ⅱ averages more (1–3)
- **Evolved quirk:** the normal-attack double-shot branch is unreachable (see ⚠️)

**In-game text**
- Normal: "Fires arcing arrows that can hit up to 3 enemies at once." (both base & Ⅱ)
- Skill (base): "Fires a volley of arcing arrows in succession, dealing damage to enemies across a wide area."
- Skill (Ⅱ): "Fires more arcing arrows at a faster rate, dealing damage to enemies across a wide area."

**Normal attack — up to 3 targets**
- `onAttackStartFrame` builds `targetList = getAttackableEnemyList(3)` (≤3 targets), pinning the current `target` to the front. `attackMain()` calls `fireNextAttackTarget()` once, round-robining a `doRangeAttack` through the list.
- It then checks `numShot >= 1.5` for a 35%-chance second shot — but max `numShot` is 1.2 (evolved), so this branch never fires (see ⚠️).

**Skill — arcing arrow volley**
- `onSkillStartFrame` gathers `getEnemiesWithin(220, true)` plus the current target into `skillTargetList`.
- `skillMain()` fires a burst whose size depends on evolStage: base `t = chance(0.65)?2:1`; **Ⅱ:** `t = rand<0.3?3 : rand<0.6?2 : 1` (averages more arrows).
- Each arrow is a `UniArrow` fired with a random arc `riseAngleDeg = 35 + 20·rand`.

**Base → Ⅱ**
- `numShot` 1 → 1.2 (but buys nothing — see ⚠️).
- Skill burst: base 1–2 arrows (2 @ 65%) → Ⅱ 1–3 arrows (3 @ 30% / 2 @ 30% / 1 @ 40%).
- Sprite scale 0.95 → 1.02. OBJ_ATK_2/OBJ_SKL_2 are set but identical to OBJ_ATK_1/OBJ_SKL_1.

**Key values**
| | base | Ⅱ |
|---|---|---|
| numShot | 1 (NUM_SHOT_1) | 1.2 (NUM_SHOT_2) |
| max normal targets | 3 | 3 |
| extra-shot threshold | numShot ≥ 1.5 | numShot ≥ 1.5 (never met) |
| extra-shot chance | 0.35 (if gate met) | 0.35 (if gate met) |
| skill scan radius | 220 | 220 |
| skill burst | 2 @ 65% else 1 | 3 (30%) / 2 (30%) / 1 (40%) |
| skill arc angle | 35 + 20·rand deg | 35 + 20·rand deg |
| OBJ_ATK | {40:1,45:1,51:1} | {40:1,45:1,51:1} |
| OBJ_SKL | {76:1,82:1,88:1,91:1} | {76:1,82:1,88:1,91:1} |
| firePoint | (20,-34) | (20,-34) |
| sprite size | 0.95 | 1.02 |
| weaponClass | YX.UniArrow | YX.UniArrow |

**Formulas**
- Arrow spawn `x = this.x + firePoint.x·direction·currentSize`, `y = this.y + firePoint.y·currentSize`; arc `riseAngleDeg = 35 + 20·rand`.
- evolStage gating in `setData`: `evolStage>=1` ⇒ `numShot=NUM_SHOT_2(1.2)` + OBJ_ATK_2/OBJ_SKL_2, else NUM_SHOT_1(1)/OBJ_ATK_1.

**⚠️ Description vs code**
- Mostly matches, one dead branch. "Hit up to 3 enemies" = the `getAttackableEnemyList(3)` cap — confirmed. The evolved "fires more arrows" claim holds for the skill (up to 3 vs base 2) — confirmed.
- BUT the normal-attack double-shot branch `numShot >= 1.5 && chance(.35)` is **unreachable**: max `numShot = 1.2 < 1.5`, so a second normal arrow is never fired even when evolved. The evolved "faster rate" never materializes on the normal attack — `numShot` 1.2 buys nothing because the 1.5 threshold is never crossed. Evolved Unicorn's only real upgrade is the richer skill-burst distribution (OBJ_ATK_2/OBJ_SKL_2 are identical to base) plus a slightly larger sprite.

**Notes**
- Player-side hero (UNIT_NAME 51/52), unlike the rest of this batch (enemy/reward units). The "1.2 vs 1.5" gap is the only genuine code-vs-intent oddity — looks like the threshold was meant to be ≤1.2 (or NUM_SHOT_2 meant to be ≥1.5) so evolved would actually double-fire.

---

### Ice Wolf — `IceWolf` (kindNum: 1003)
**TL;DR.** A summoned melee wolf with hard-coded stats that has a 25% chance to freeze whatever it hits.

**At a glance**
- **Role:** Summoned melee DPS (freeze-on-hit wolf summon)
- **Attack:** fast melee (moveSpd 2.2), one hit on frame 54
- **Proc:** 25% chance per hit to freeze the target for 70t (~1.17s)
- **Stats:** fully hard-coded (HP 100, atk 10, def 10), not spawn-scaled

**In-game text**
- Normal: "None"
- Skill: "Special Skill"  (generic summon placeholder)

**Normal attack — freeze-on-hit**
- `attackMain()` calls `super.attackMain()`, then if the target is alive rolls `random.chance(.25)` to `target.freeze(70)` — 25% chance to freeze for 70 ticks (~1.17s) on each hit. Single melee hit on `objAtk` frame 54.

**Passive / special**
- No separate active skill: `skillFrames` alias attackFrames (40-69). The "Special Skill" text maps to the freeze-on-hit proc, not a distinct cast.

**Buffs & debuffs**
- Freeze on enemy: `freeze(70)` (70t ~1.17s) at 25% chance per hit.

**Key values**
| variable | value | meaning |
|---|---|---|
| maxHp / hp | 100 | health |
| atkDmg | 10 | attack damage |
| def | 10 | defense |
| moveSpd | 2.2 | movement speed (fast) |
| atkDuration | 100 | attack interval (ticks) |
| atkRange | 15 | melee range |
| freeze chance | 0.25 | chance to freeze per hit |
| freeze duration | 70 | freeze ticks (~1.17s) |
| objAtk | {54:1} | melee hit on frame 54 |
| hitHeight / hitWidth / radius | 20 / 15 / 13 | hit box |
| size | 0.9 | sprite scale |
| idle/move/attack/die frames | 0-29 / 30-39 / 40-69 / 70-104 | animation ranges |

**Formulas**
- Attack interval is the hard `atkDuration=100` (not `1e4/atkSpd`, since this unit sets atkDuration directly).

**✓ Matches description** — the "None"/"Special Skill" generic summon placeholder corresponds to the freeze-on-hit proc; the real mechanic is that freeze.

**Notes**
- The wolf summoned by Wolf-Rider type units (kindNum 1003 in the 100x summon block, alongside Wolf=1001, Graveyard Hero=1002). Carries its own fixed stats rather than scaling off a summoner, except whatever the summon code applies. No evolStage branch.

---

### Gold Goblin — `GoldGoblin` (no combat kindNum — gold-reward unit)
**TL;DR.** A clickable gold piñata that wanders the field, drops coins each tap, and flees or expires — it never fights.

**At a glance**
- **Role:** Reward unit (clickable gold piñata; wander/flee AI, non-combatant)
- **Taps:** 10 to "kill" (`MAX_LIVES`); 5 coins per tap, 30-coin jackpot on the 10th
- **Lifetime:** ~1800t (~30s @1×), then runs off the nearest edge
- **Combat:** deals/takes no damage (`atkDmg=0`, `atkDuration=9999`, empty `objAtk`)

**In-game text**
- No `UNIT_NATK`/`UNIT_SATK` (not a combat unit). Player tip (`TIP_DESC_33`): "Try quickly tapping the Gold Goblin that appears during the game 10 times." (matches `MAX_LIVES=10`.)

**Passive / special — tap, flee, wander, expire**
- **On tap (`onClicked`):** decrements `lives` (starts 10), plays `SFX_GOLD_GOBLIN`. If `lives<=0` → `onGoldDropMulti(x,y,0,DEATH_COINS=30)` then dies. Otherwise drops `onGoldDropMulti(x,y,0,COINS_PER_CLICK=5)`, plays its hurt/recoil animation, and after a speed-scaled `fleeDelay = round(8·(speed−1))` calls `flee()`.
- **Flee:** picks a random point 150–250px away (`150 + 100·rand` at angle `rand·2π`, clamped to bounds) and dashes there at `FLEE_SPEED=5`.
- **Expire (`doIdle`):** decrements `lifetime` (starts 1800t ≈ 30s); on expiry `escapeAndRemove()` runs it off the nearest screen edge at `2·FLEE_SPEED=10` and self-destructs after 3000ms.
- **Wander:** every `wanderInterval = 120 + rand(180)` ticks it picks a new target (30% an off-screen edge point, else on-screen) and walks at `NORMAL_SPEED=1.5`.

**Key values**
| variable | value | meaning |
|---|---|---|
| MAX_LIVES | 10 | taps needed to "kill" it (drops big reward) |
| COINS_PER_CLICK | 5 | coins per non-final tap |
| DEATH_COINS | 30 | bonus coins on the final (10th) tap |
| NORMAL_SPEED | 1.5 | wander move speed |
| FLEE_SPEED | 5 | dash speed after being tapped |
| escape speed | 10 | 2×FLEE_SPEED when lifetime expires |
| LIFETIME | 1800 | ticks alive before it escapes (~30s @1×) |
| wanderInterval | 120 + rand(180) | ticks between wander re-targets |
| flee distance | 150 + 100·rand px | dash distance after a tap |
| fleeDelay | round(8·(speed−1)) | tick delay before fleeing (0 at 1×) |
| escape removal | 3000 ms | setTimeout to die after running off-screen |
| maxHp | 100 | nominal (never damaged — only tap-based lives) |

**Formulas**
- `fleeDelay = round(8·(gameSpeed − 1))` — at 1× it flees immediately; faster speeds add reaction delay.
- Game-speed move compensation in `execute()`: while in MOVE state and `speed>1`, temporarily `orgMoveSpd /= speed`, `incFrame /= speed` so travel speed stays constant under fast-forward.

**✓ Matches description** — no combat description to compare; matches the in-game tip (tap 10×, confirmed by `MAX_LIVES=10`, with 5 coins/tap and a 30-coin jackpot on the kill).

**Notes**
- Special non-combat reward object. Re-poolable via `resetGoldGoblin()`. The `onGoldDropMulti` callback is wired by the spawner to credit the player. Its "attack" animation is repurposed purely as the tapped-recoil-and-flee reaction, not a real attack.

---

### Ads Goblin — `AdsGoblin` (no combat kindNum — watch-ad reward unit)
**TL;DR.** An untargetable, indestructible billboard goblin that strolls across the screen and fires the rewarded-ad popup when tapped.

**At a glance**
- **Role:** Reward unit (clickable rewarded-ad trigger; untargetable, indestructible, non-combatant)
- **Trigger:** one tap → `onAdsReward(x,y)` (the rewarded-ad hook)
- **Movement:** scripted 8-phase walk across the field, then exits at x=-100
- **Combat-proof:** `maxHp=9999`, `def=9999`, `isUntagetable=true`, deals no damage

**In-game text**
- No `UNIT_NATK`/`UNIT_SATK` (not a combat unit).

**Passive / special — phase-machine walk + ad trigger**
- **Phase machine (1→8):** in each idle phase it waits ~180–300 ticks (`phaseTimer >= base + rand`) glancing left/right on a random `lookInterval = 40 + floor(50·rand)`, then `nextMovePhase` walks it to the next x-target along x only. Targets march it across the field: phase 2→`320+60·rand`, 4→`170+60·rand`, 6→`50+60·rand`, 8→`-100` (off-screen, where `onPhaseArrived` sets `visible=false, removed=true`).
- **Walk anims:** alternates `moveFramesA` (30-49) / `moveFramesB` (50-69); `useMoveB = chance(.3)` and when using B it flips its facing.
- **On tap (`onClicked`):** if alive and not already `waiting`, sets `waiting=true`, goes idle, and calls `onAdsReward(x,y)`. `resumeWalking()` polls `requestAnimationFrame` until `waitTimer >= WAIT_AFTER_POPUP=120`, then resumes the phase march via `resumeMovement()`.

**Key values**
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

**Formulas**
- Movement (`doMove`) is hand-rolled: unit-vector step toward `(tx,ty)` at `moveSpd`, snapping to target when within `moveSpd²`; facing flips on `useMoveB`. No combat formulas.

**✓ Matches description** — no combat description to compare; internally consistent as an untargetable, indestructible billboard goblin that grants a reward when tapped to watch an ad.

**Notes**
- Special non-combat reward object. Differs from GoldGoblin: (a) single-reward (one tap → ad popup, not 10 taps), (b) `isUntagetable` + 9999 HP/def so combat never touches it, (c) auto-exits after its 8-phase walk rather than on a lifetime countdown. Re-poolable via `resetAdsGoblin()`.
- Minor minification artifact: `resumeWalking` reuses the bundle's `Kt` helper name as a local `requestAnimationFrame` callback wrapper (`Kt(()=>{...},"checkResume")`), unrelated to the class-registration `Kt`.

---

## Cross-cutting notes
- **Trivial minions** (SlimeRed, SlimeYellow, MoleSoldier1/2, StarFish) and the **ranged minion** (Crab) are data-only: they inherit all combat from `qQ`; only frame ranges / `objAtk` / (for Crab) `weaponClass`+`firePoint` differ. Their "None / Special Skill" descriptions are generic enemy placeholders, not real skills.
- **Bosses** (HammerMole, DarkHermit) share an archetype: immobile, big body, health bar, click-to-show-range, and **total status immunity** (all CC methods overridden to no-ops). HammerMole's skill is probabilistic (60%/enemy MoleFire), DarkHermit's is deterministic (10 missiles) and mana-gated (≥400). DarkHermit additionally carries the slime kindNums it summons.
- **Reward units** (GoldGoblin, AdsGoblin) have **no combat kindNum** — they are clickable bonus objects (gold-per-tap piñata vs single-tap watch-ad trigger) with their own wander/flee/phase AI and game-speed compensation; they deal/take no damage.
