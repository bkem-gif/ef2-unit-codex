# EF2 unit-mechanics — part 5 (reformatted)

Bundle: `runtime/bundles/mounted/1.11.42/assets/index.js` (v1.11.42). Tick rate ≈ 60/s at 1× game speed; durations shown as `Nt (~Ns)`. Damage convention: `doMeleeAttack(t, mult)` / `doDamage(t, mult)` / `doRangeAttack(t)` apply `mult × atkDmg`, subject to miss/block/evade and day-night tribe modifiers. Mana-gated skills accrue `mana += 1`/tick and fire at `mana >= maxMana` (interval ≈ maxMana ticks).

---

### Bigfoot — `OrcBigFoot1` (kindNum: 61 · Ⅱ 70)
**TL;DR.** A melee bruiser that body-slams everything in front of it for splash damage and can freeze each enemy it hits, with a wider freezing slam as its skill.

**At a glance**
- **Role:** Melee tank / AoE bruiser (with freeze)
- **Attack:** full hit on the main target, then a forward sweep hitting up to 4 (Ⅱ 5) extra enemies at ×0.4
- **Freeze:** 30% (Ⅱ 40%) per target on normal; 50% (Ⅱ 60%) on skill
- **Skill:** wider forward slam at ×1.0, up to 4 (Ⅱ 8) enemies, fired on mana fill

**In-game text**
- Normal: "Deals AoE damage to nearby enemies with its huge body and has a chance to freeze them." (Ⅱ: "…massive body…")
- Skill: "Unleashes a powerful AoE strike forward, freezing multiple enemies." (Ⅱ: "Strikes forward in a wider area with a powerful blow, freezing multiple enemies.")

**Normal attack**
- Hits the main target with a full `doMeleeAttack`, freezing it at 30% (Ⅱ 40%) for 60t (Ⅱ 70t).
- Then sweeps a forward box (offset/half-extent `h` = 30, Ⅱ 45) hitting up to 4 (Ⅱ 5) extra enemies for ×0.4 each, each freezeable at the same 30% (Ⅱ 40%) chance.

**Skill — wide slam (mana fill, frame 85)**
- Sweeps a wider forward box (radius `i` = 55, Ⅱ 70) dealing ×1.0 to up to 4 (Ⅱ 8) enemies.
- Freezes each at 50% (Ⅱ 60%) for 70t (~1.2s) (Ⅱ 80t). Spawns an `IceExplode2` effect.
- `hasSkill=true` but no `maxMana` in body → uses base default mana behavior.

**Buffs & debuffs**
- Freeze (enemy): normal 30%→40% for 60t→70t; skill 50%→60% for 70t→80t. No ally buffs.

**Base → Ⅱ**
- Normal freeze 30%→40%, dur 60t→70t; sweep box 30→45; extra hits 4→5.
- Skill radius 55→70; skill hits 4→8; skill freeze 50%→60%, dur 70t→80t.

**Key values**
| | base | Ⅱ |
|---|---|---|
| normal freeze chance (`s`) | 30% (0.3) | 40% (0.4) |
| normal freeze dur (`e`) | 60t (~1.0s) | 70t (~1.2s) |
| normal sweep box (`h`) | 30 | 45 |
| normal max extra hits (`n`) | 4 | 5 |
| extra-hit dmg mult | ×0.4 | ×0.4 |
| skill radius (`i`) | 55 | 70 |
| skill max hits (`s`) | 4 | 8 |
| skill freeze chance (`e`) | 50% (0.5) | 60% (0.6) |
| skill freeze dur (`n`) | 70t (~1.2s) | 80t (~1.3s) |
| skill dmg mult | ×1.0 | ×1.0 |
| objAtk / objSkill | {51:1} / {85:1} | same |

**Formulas**
- Freeze applies via `target.freeze(durTicks)` only if `!freezeImmune` and the new duration exceeds the current `numFreeze`.

**✓ Matches description** — body sweep + per-target freeze = NATK; forward box at ×1.0 freezing up to `s`/8 = SATK; Ⅱ "wider area" = box 55→70 and caps 4→8.

---

### Ice Mage — `OrcBlizzardMage1` (kindNum: 67 · Ⅱ 76) — Orc-tribe variant
**TL;DR.** A ranged caster that pelts enemies with ice shards and rains spread-damage ice on several targets at once as its skill — and each rain drop can also briefly freeze.

**At a glance**
- **Role:** Ranged mage (ice rain AoE)
- **Attack:** fires `IceFlake` projectiles; Ⅱ fires twice per swing ("continuously")
- **Skill:** rains projectiles on the nearest 3 (Ⅱ 4) enemies in a 220 (Ⅱ 260) radius at ×0.4 each
- **Freeze:** each rain drop has a 20% chance to freeze its target for 60t (~1.0s)

**In-game text**
- Normal: "Fires ice shards to attack enemies from range." (Ⅱ: "…continuously…")
- Skill: "Unleashes a barrage of ice rain on multiple enemies in range, dealing spread damage." (Ⅱ: "…over a larger area…")

**Normal attack**
- Fires `IceFlake`; base `objAtk={39:1}` (one hit), Ⅱ `objAtk={39:1,42:1}` (two hits/swing) → matches "continuously."

**Skill — ice rain (frames 49–79)**
- Gathers enemies within radius 220 (Ⅱ 260), filters those already hit (`attackedSet`), takes the nearest 3 (Ⅱ 4), and rains `OrcBlizzardMageRain1` at ×0.4 each. Each raindrop's `onHitMain` rolls `chance(.2)` → `freeze(60)` (~1.0s) on its target.
- `attackedSet` resets once candidates are exhausted, so it cycles fresh targets across the 4 skill rain frames.

**Base → Ⅱ**
- Normal hits 1→2/swing; skill radius 220→260; skill targets/batch 3→4.

**Key values**
| | base | Ⅱ |
|---|---|---|
| skill radius (`i`) | 220 | 260 |
| skill targets/batch (`s`) | 3 | 4 |
| rain dmg mult | ×0.4 | ×0.4 |
| rain freeze | 20% → `freeze(60)` | same |
| objAtk | {39:1} | {39:1,42:1} |
| objSkill | {62:1,66:1,71:1,75:1} | same |
| weaponClass | IceFlake | IceFlake |

**⚠️ Description vs code**
- Behaviour matches the generic "Ice Mage" text, BUT this is a **naming/tribe mismatch**: the class is `OrcBlizzardMage1` (Orc tribe, own `sheetName`) yet reuses the generic Ice-Mage (67/76) description string — kindNum binding matched here by behaviour only; confirm in the data config.
- It is NOT the in-game "Frost Mage" (kindNum 21, enhanced freezing projectiles): this unit's hits are mostly spread damage, but the **skill rain does apply a light freeze** — `OrcBlizzardMageRain1` rolls 20% → `freeze(60)` per drop (an earlier note here that said "no freeze" was wrong).

---

### Ice Decoy — `OrcIcePhantom1` (no own kindNum; summoned by Orc Hammerman 24 · Ⅱ 49)
**TL;DR.** A no-damage ice clone the Orc Hammerman summons to taunt nearby enemies and soak hits in his place for a few seconds.

**At a glance**
- **Role:** Summoned taunt-decoy (no attack, draws aggro)
- **Stats:** 0.3× the summoner's stats (`setData(sourceVo, 0.3)`)
- **Lifetime:** 180t (~3.0s) base, 220t (~3.7s) evolved — set by the summoner
- **Taunt:** every 5 ticks, force-retargets enemies within 160px onto itself

**In-game text** (the decoy referenced by Hammerman's skill; it has no NATK/SATK of its own)
- Hammerman skill: "Summons an ice decoy to draw enemy attacks in your place." (evolved: "Summons an ice clone for a longer duration to take hits in your place.")

**Passive / special — taunt loop**
- Spawned via `HammerMole.summonPhantom(t)` → `getUnitSync(fx.OrcIcePhantom1)`, `isSummoned=true`, `summonTimer=t`. Hammerman passes t=180 (base) / 220 (evolved). Each tick `summonTimer--`; `die()` at 0.
- Deals NO damage. On a `battleTime % 5 == 0` cadence (desynced by `id%5`), scans `getEnemiesWithin(160, true)` and sets `enemy.target = this` for any enemy not already targeting a phantom, showing `AggroEffect`. Cycles its move animation while alive.

**Buffs & debuffs**
- Taunt (enemy): reassigns `enemy.target = this` — no numeric buff/debuff object.

**Base → Ⅱ (via summoner)**
- Lifetime 180t → 220t.

**Key values**
| variable | value | meaning |
|---|---|---|
| summonTimer | 180 / 220 (base/evolved) | lifetime ticks (set by summoner) |
| stat scale | 0.3 | 30% of summoner stats |
| aggro radius | 160 | taunt range |
| aggro cadence | every 5 ticks | `(battleTime + id%5) % 5 == 0` |
| hitHeight / radius | 29 / 7 | collision |

**✓ Matches description** — the taunt/aggro retarget loop = "ice decoy to draw enemy attacks"; "longer duration" (evolved) = summonTimer 180→220.

---

### Raptor Rider — `OrcRapterRider1` (kindNum: 83 · Ⅱ 86)
**TL;DR.** A ranged unit that hurls spears at several enemies in a round-robin, with a skill that throws a spread of five freezing spears.

**At a glance**
- **Role:** Ranged DPS (multi-target spear thrower)
- **Attack:** round-robins spears across up to 3 (Ⅱ 4) queued enemies; 2 (Ⅱ 3) hit frames/swing
- **Skill:** gathers enemies within 220px and throws 5 spears (`OrcRapterRiderSpear1`)
- **Freeze:** chance lives on the spear weapon, not this class

**In-game text**
- Normal: "Throws spears at enemies within range." (Ⅱ: "Throws a spear at more enemies within range.")
- Skill: "Throws multiple spears that have a chance to Freeze enemies within range." (Ⅱ: "Throws several spears that have a chance to Freeze enemies within range.")

**Normal attack**
- `onAttackStartFrame()` builds a `targetList` of up to 3 (Ⅱ 4) attackable enemies with the current target pulled to the front.
- `attackMain()` runs on each `objAtk` hit-frame and `doRangeAttack`s the next target in round-robin. Base `objAtk={61:1,66:1}` (2 frames); Ⅱ `{61:1,64:1,67:1}` (3 frames) → "a spear at more enemies."

**Skill — spear spread**
- `onSkillStartFrame()` gathers `getEnemiesWithin(220, true)` (current target first); `skillMain()` round-robins through 5 skill hit frames `{90,95,100,105,110}`, firing `OrcRapterRiderSpear1` at each.

**Buffs & debuffs**
- Freeze (enemy): chance is on the spear weapon `OrcRapterRiderSpear1`, not this class — magnitude not quotable here.

**Base → Ⅱ**
- Target cap 3→4; normal hit frames 2→3.

**Key values**
| | base | Ⅱ |
|---|---|---|
| normal target cap (`t`) | 3 | 4 |
| objAtk | {61:1,66:1} | {61:1,64:1,67:1} |
| objSkill | {90,95,100,105,110} | same |
| skill gather radius | 220 | 220 |
| weaponClass | OrcRapterRiderSpear1 | same |
| firePoint | (30, −57) | same |

**✓ Matches description** — round-robin `doRangeAttack` over `targetList` = NATK; Ⅱ "more enemies" = cap 3→4 + extra hit frame; SATK = 5 skill spears (freeze handled by the weapon).

---

### Wyvern Rider — `WyvernRider1` (kindNum: 92 · Ⅱ 96)
**TL;DR.** An airborne dagger-thrower whose skill freezes and spreads daggers radially, with the number of boomerang daggers scaling to how many kills it racked up since its last skill.

**At a glance**
- **Role:** Ranged DPS (air; boomerang-dagger AoE + freeze-spread skill)
- **Attack:** throws 2 knives (`WyvernRiderThrowingKnife1`) at ×1.1
- **Kill-scaling:** kills since last skill → 1/2/3/4 special boomerang knives next skill (thresholds 2/5/8)
- **Skill:** up to 3 targets in an 85 (Ⅱ 115) box; knife damage ×1.8 (Ⅱ ×2.2); freeze + radial spread on `…KnifeS1`

**In-game text** (96 text identical to 92)
- Normal: "Throws daggers at multiple enemies, dealing damage. Depending on the number of enemies defeated since the last skill, fires additional boomerang daggers on the next skill."
- Skill: "Fires daggers at multiple enemies. When a dagger hits, it freezes the target and spreads daggers outward in all directions from that spot, freezing enemies in their path before exploding after a short time."

**Normal attack**
- Air unit (`isAir`, `airHeight=75`). `attackMain()` throws a `WyvernRiderThrowingKnife1` at the main target at ×1.1, then one at one more enemy (2 targets total) at ×1.1.

**Skill — freeze-spread barrage**
- `onSkillStartFrame()` gathers up to 3 targets in a box around the current target (half-extent 85, Ⅱ 115).
- `skillMain()` fires per skill hit frame: knife 0 hits target[0] directly; later calls pick a "divergent" target (`pickDivergentTarget`, spreading outward within 250px) plus a random jitter (`SKILL_OFFSET_MIN..MAX` = 60..140).
- The first `tendrilCountForThisSkill` calls use the special `WyvernRiderThrowingKnifeS1` (boomerang/freeze-spread weapon); after that, the normal knife. Skill knife damage ×1.8 (Ⅱ ×2.2).

**Passive / special — kill-counting boomerang**
- `onKillEnemy()` increments `prepCount`. At `onSkillStartFrame()`, `tendrilCountForThisSkill = calcTendrilCount(prepCount)`, then `prepCount` resets.
- Tendril tier: 1 (<2 kills) / 2 (≥2) / 3 (≥5) / 4 (≥8) → that many `…KnifeS1` boomerang knives that skill.

**Buffs & debuffs**
- Freeze (enemy): applied on skill-knife hit by `WyvernRiderThrowingKnifeS1`, not this class.

**Base → Ⅱ**
- Skill knife damage ×1.8→×2.2; skill gather box 85→115. (Text unchanged.)

**Key values**
| | base | Ⅱ |
|---|---|---|
| normal targets | 2 | 2 |
| normal knife dmg | ×1.1 | ×1.1 |
| skill knife dmg | ×1.8 | ×2.2 |
| skill gather box | 85 | 115 |
| skill max targets | 3 | 3 |
| TENDRIL_T1/T2/T3 | 2 / 5 / 8 kills | same |
| tendril count | 1/2/3/4 (by threshold) | same |
| SKILL_OFFSET_MIN/MAX | 60 / 140 | same |
| divergent max dist | 250 (62500 = 250²) | same |
| objAtk / objSkill | {35:1} / {68,79,90,101} | same |
| airHeight / firePoint | 75 / (18, 5−75) | same |

**Formulas**
- Divergent target = minimize the dot product of the to-target direction vs the spread direction (fans knives outward).
- Tendril tier: `count = prepCount>=8 ? 4 : >=5 ? 3 : >=2 ? 2 : 1`.

**✓ Matches description** — "additional boomerang daggers depending on enemies defeated since last skill" = the `prepCount`→`calcTendrilCount` mechanic (2/5/8 thresholds → up to 4 `…KnifeS1` knives); "freezes + spreads radially + explodes" = the `…KnifeS1` weapon. Ⅱ raises skill dmg and gather box despite identical text.

---

### Blade Master — `BladeMaster1` (no matching kindNum in unit_desc; classVar y2, maxMana 900)
**TL;DR.** An unreleased dual-mode bruiser that switches between a teleporting melee reaper and a 12-direction blade-wave shooter, stacking attack buffs on kills and unleashing a multi-target reap on its skill.

**At a glance**
- **Role:** Boss-tier hybrid DPS — melee/range mode-switcher with teleport "reap" and kill-stacking buffs
- **Modes:** `toggleMode()` — mode 0 melee, mode 1 range; switching bursts AoE and self-heals
- **Skill (mana 900):** AoE hit + ring of spin-blades + reap teleport chain + self rush buff
- **Kill stacks:** up to 8 stacks of +6% atkspd / +5% atkdmg; melee kills also give 20 mana
- **No in-game text:** documented from code only (kindNums in desc data end at 96)

**In-game text**
- None — `/tmp/unit_desc.json` has no `UNIT_NATK`/`UNIT_SATK` entry for this class (descriptions stop at kindNum 96; this is an unreleased/data-only unit).

**Normal attack — melee mode (`attackMelee`)**
- Hits the target for ×0.95, then splashes up to 3 total enemies within 80 (Ⅱ 100) at ×0.95 each; spawns afterimages.
- If the target died, `tryTeleportToNextTarget()` blinks to the nearest enemy within 400px (landing 30px past it).

**Normal attack — range mode (`attackRange`)**
- 3-step combo (`rangeComboIdx % 3`) firing `BladeWave1` at snapped 30°-grid angles (12 directions) with per-step offsets [−20°, +20°, 0°], damage ×0.7 (Ⅱ ×1.0).
- After 6 range kills, the next 3rd-combo shot becomes a triple fan.

**Skill — AoE + spin-blades + reap (mana 900)**
- AoE melee hit ×1.5 to up to 12 enemies within 130 (Ⅱ 160).
- Fires `SpinBlade` in a ring (3 angles melee mode, 6 range mode) at ×0.8 (Ⅱ ×1.1).
- Then `startReap()` and self-buffs a rush (move +80%, atkspd +40% for 300t).

**Passive / special**
- **Reap (`startReap`/`advanceReap`):** sorts up to 5 enemies within 500px, teleports behind each (30px) one every 6 ticks dealing ×1.6, then returns to origin.
- **Mode switch (`applySwitchBurst`):** AoE ×1.0 to enemies within 100px, heals self 30. Entering range mode sets `atkRange=350` and a permanent +50% atkspd buff.
- **Kills (`onKillEnemy`):** melee kills give 20 mana; every kill stacks (≤8) +6% atkspd & +5% atkdmg for 600t.

**Buffs & debuffs** (self, ids in `fQ`)
- Melee move-speed: +30% (value 0.3), 9999t, self — id 253 (zeroed when entering range mode)
- Melee atk-damage: +15% (value 0.15), 9999t, self — id 254
- Range atk-speed: +50% (value 0.5), 9999t, self (range mode only) — id 252
- Kill atk-speed: +6%/stack (value stack×0.06), 600t, self (refresh) — id 250
- Kill atk-damage: +5%/stack (value stack×0.05), 600t, self — id 251
- Rush move-speed: +80% (value 0.8), 300t, self (post-skill) — id 256
- Rush atk-speed: +40% (value 0.4), 300t, self — id 255
- Debuffs: pure damage (no freeze/stun in code).

**Base → Ⅱ**
- Melee splash 80→100; blade-wave dmg ×0.7→×1.0; spin-blade dmg ×0.8→×1.1; skill range 130→160.

**Key values**
| variable | value | meaning |
|---|---|---|
| maxMana | 900 | skill mana cost (≈900 ticks) |
| DMG_HIT | ×0.95 | melee hit mult |
| SPLASH_RADIUS (/_E) | 80 / 100 | melee splash radius (base/Ⅱ) |
| MAX_HITS | 3 | melee enemies per swing |
| RANGE_ATK_RANGE | 350 | range-mode attack range |
| RANGE_WAVE_DMG (/_E) | ×0.7 / ×1.0 | blade-wave damage |
| RANGE_WAVE_OFFSETS | [−π/9, π/9, 0] | ±20°, 0 combo offsets |
| RANGE_ATKSPD_BUFF | +50% (0.5) | range-mode atkspd (dur 9999) |
| RANGE_KILL_STACK_MAX | 6 | range kills → triple-fan shot |
| SKILL_RANGE (/_E) | 130 / 160 | skill AoE radius |
| SKILL_DMG | ×1.5 | skill AoE hit mult |
| SKILL_MAX | 12 | skill AoE max targets |
| SPINBLADE_DMG (/_E) | ×0.8 / ×1.1 | spin-blade projectile damage |
| SPINBLADE_ANGLES melee/range | 3 / 6 | ring projectile count |
| KILL_STACK_MAX | 8 | max kill stacks |
| KILL_ATKSPD/ATKDMG_PER | +6% / +5% per stack | per-stack buff |
| KILL_BUFF_DUR | 600t | kill-buff ticks |
| MELEE_MOVESPD/ATKDMG_BUFF | +30% / +15% | passive melee buffs (dur 9999) |
| MELEE_KILL_MANA | 20 | mana per melee kill |
| RUSH_DURATION | 300t | rush buff ticks |
| RUSH_MOVESPD/ATKSPD_BONUS | +80% / +40% | post-skill rush buffs |
| SWITCH_BURST_RADIUS/DMG/HEAL | 100 / ×1.0 / 30 | mode-switch burst & self-heal |
| TELEPORT_MAX_DIST | 400 | blink range on target death |
| REAP_MAX/RANGE/STEP/DMG/BEHIND | 5 / 500 / 6t / ×1.6 / 30 | reap chain |
| normalSize / evolSize | 0.9 / 1 | scale |

**Formulas**
- `atkSpd = orgAtkSpd × (1 + Σ atkspd-buff.value)`; at 8 kill stacks → atkspd +48% (8×0.06) and atkdmg +40% (8×0.05).
- Range-mode passive +50% atkspd and rush +40% atkspd / +80% move are distinct ids → summed.
- `snapToDir` quantizes the aim angle to the nearest of 12 directions spaced 30° (π/6).

**⚠️ Description vs code**
- **No in-game description to compare** — `/tmp/unit_desc.json` has no entry for `BladeMaster1` (kindNums end at 96). Documented from code alone; kindNum not present in the desc data.

**Notes**
- Most mechanically complex of the 12: mode toggling, kill-stack scaling, reap teleport chain, and the 30°-snapped blade-wave combo are all bespoke. Buff ids 250–256 are contiguous and dedicated, so its self-buffs never collide with other units.

---

### Elf Castle — `ElfTown5` (kindNum: 10001)
**TL;DR.** The immobile, destructible base used by both sides — a stationary arrow turret that fires bouncing `SpeedArrow2` shots at nearby enemies.

**At a glance**
- **Role:** Castle / defensive structure (immobile ranged turret) — both player and enemy castle
- **Attack:** fires up to `ceil(numShot)` (=1) `SpeedArrow2` arrows per attack
- **Range:** detectRange 600, atkRange 250
- **Immobile:** `moveSpd=0`; movement/`lookAt`/`die` overridden; has a health bar (destructible)

**In-game text** (generic placeholder pair for non-player structures)
- Normal: "Knockback"
- Skill: "Special Skill"

**Normal attack**
- Confirmed kindNum 10001 by `setupCastles()` → `initializeUnitByKindNum(i, 10001, t)`, then sets `detectRange=600`, `atkRange=250`, `numShot=1`.
- `attackMain()` fires up to `ceil(numShot)` arrows: for each of the top `numShot` attackable enemies, `doRangeAttack` with probability `numShot` (decrementing) → a fractional `numShot` yields a probabilistic last shot (multishot if `numShot>1`).
- Custom `generateWeapon` aims `SpeedArrow2` from a 35px muzzle; the arrow carries `numBounce` bounces. Set up once per side at the side's center per battle.

**Key values**
| variable | value | meaning |
|---|---|---|
| kindNum | 10001 | bound via `initializeUnitByKindNum(...,10001)` |
| detectRange | 600 | target detection (set at setup) |
| atkRange | 250 | firing range (set at setup) |
| numShot | 1 | shots/attack (multishot if raised) |
| radius / hitHeight | 22 / 67 | collision / sprite |
| weaponClass | SpeedArrow2 | arrow (carries numBounce) |
| objAtk | {23:1} | hit frame |
| moveSpd | 0 | immobile |

**Formulas**
- Multishot loop: for shot `e`, fire with `random.chance(numShot)` then `numShot--` → expected arrows ≈ `numShot` (fractional handled probabilistically).

**⚠️ Description vs code**
- The "Knockback" / "Special Skill" text is a generic stub for non-player structures and does NOT reflect actual mechanics: the code has no knockback call and no skill (`hasSkill` not set) — it is just a stationary multishot arrow tower firing `SpeedArrow2`.

**Notes**
- The "5" in `ElfTown5` is a tier/skin index; all castle setups in the bundle use this same class for kindNum 10001.

---

### Orc Flower — `OrcFlower` (kindNum: 30001)
**TL;DR.** A big immobile, CC-immune summoner structure that pelts enemies with energy balls and periodically spawns ranged Flower Soldiers.

**At a glance**
- **Role:** Boss/castle-type summoner structure (immobile; spawns Flower Soldiers)
- **Attack:** round-robins `EnergyBall` across up to 10 queued targets over 8 hit frames
- **Skill (mana 300):** summons 2 `FlowerSoldier2` (kindNum 30003) per cast while allies < 30
- **Immune:** CC and DoT receivers all no-op'd (boss immunity)

**In-game text** (generic placeholder pair)
- Normal: "Knockback"
- Skill: "Special Skill"

**Normal attack**
- Large stationary structure (`moveSpd=0`, `radius=40`, `hitHeight=140`, `numBlock=0`). Targets the nearest enemy and attacks when in range.
- `attackMain()` is distributed across 8 `objAtk` frames {46,48,…,60}, round-robining `doRangeAttack` over up to 10 queued targets, firing `EnergyBall` (custom `generateWeapon` spawns with random muzzle jitter).

**Skill — summon (mana 300)**
- While ally count < 30, summons 2 `FlowerSoldier2` (kindNum 30003) via `summonUnit(VO, 1200)` (1200-tick lifetime).

**Passive / special**
- **CC/DoT immunity:** hard-overrides `stun, knockBack, freeze, curse, silence, poison, blow, binding, shock, addDotDamage, onHitted` to no-ops → immune to all CC and DoT. Clicking it shows its range (UI).

**Key values**
| variable | value | meaning |
|---|---|---|
| kindNum | 30001 | Orc Flower |
| maxMana | 300 | skill interval (≈300 ticks) |
| summons per skill | 2 | FlowerSoldier2 spawned per cast |
| summon kindNum | 30003 | `FlowerSoldier2` |
| summon lifetime | 1200t | `summonUnit(VO, 1200)` |
| ally cap | 30 | stops summoning at ≥30 allies |
| weaponClass | EnergyBall | normal projectile |
| normal target queue | 10 | `getAttackableEnemyList(10)` |
| objAtk | {46,48,50,52,54,56,58,60} | 8 hit frames |
| radius / hitHeight | 40 / 140 | large boss footprint |

**Formulas**
- Skill gated by `mana >= maxMana` (`mana += 1`/tick).

**⚠️ Description vs code**
- The "Knockback" / "Special Skill" stub understates a summoner-boss: no knockback exists; the "special skill" is summoning Flower Soldiers, and it is a CC-immune stationary boss firing EnergyBalls.

**Notes**
- Summons `FlowerSoldier2` (30003), NOT `FlowerSoldier1` (30002) — only the ranged soldier variant is summoned.

---

### Flower Soldier 1 — `FlowerSoldier1` (kindNum: 30002)
**TL;DR.** A plain melee minion of the Orc Flower with no skill of its own — it just walks up and hits the nearest enemy.

**At a glance**
- **Role:** Basic melee minion (Orc Flower add)
- **Attack:** base melee `doMeleeAttack` on the nearest enemy (frame 63)
- **No skill, no weapon:** pure melee; stats come from the kindNum data config

**In-game text** (placeholders)
- Normal: "None"
- Skill: "Special Skill"

**Normal attack**
- Only `initializeData()` (sprite `sheetName="OrcFlower"`, `radius=7`, `hitHeight=22`, `objAtk={63:1}`). No `attackMain`/skill override → uses base melee hitting the nearest target on frame 63.

**Key values**
| variable | value | meaning |
|---|---|---|
| kindNum | 30002 | Flower Soldier 1 |
| objAtk | {63:1} | melee hit frame |
| radius / hitHeight | 7 / 22 | collision |

**✓ Matches description** — trivially: "None"/"Special Skill" placeholders for a plain melee add with no skill. (atkDmg/hp come from the kindNum data config.)

---

### Flower Soldier 2 — `FlowerSoldier2` (kindNum: 30003)
**TL;DR.** A plain ranged minion the Orc Flower summons — it fires `FlowerBullet` at the nearest enemy and has no skill.

**At a glance**
- **Role:** Basic ranged minion (Orc Flower add; the one Orc Flower summons)
- **Attack:** base ranged fire of `FlowerBullet` at the nearest enemy (frame 61)
- **No skill:** stats come from the kindNum data config

**In-game text** (placeholders)
- Normal: "None"
- Skill: "Special Skill"

**Normal attack**
- Only `initializeData()` (`sheetName="OrcFlower"`, `weaponClass=FlowerBullet`, `radius=7`, `hitHeight=27`, `firePoint=(17,-17)`, `objAtk={61:1}`). No override → base ranged attack fires `FlowerBullet` at the nearest target on frame 61.

**Key values**
| variable | value | meaning |
|---|---|---|
| kindNum | 30003 | Flower Soldier 2 (summoned by Orc Flower) |
| weaponClass | FlowerBullet | ranged projectile |
| firePoint | (17, −17) | muzzle offset |
| objAtk | {61:1} | hit frame |
| radius / hitHeight | 7 / 27 | collision |

**✓ Matches description** — trivially: placeholders for a plain ranged add firing `FlowerBullet`, no skill.

---

### King Slime — `KingSlime` (kindNum: 20001)
**TL;DR.** A huge, CC-immune boss that rains rocks on every enemy in range with a 60% chance each and periodically summons waves of mixed-color slimes.

**At a glance**
- **Role:** Boss (immobile; ranged barrage + multi-color slime summoner; CC-immune)
- **Attack:** for each enemy within 300px, 60% chance to fire a `Rock` (probabilistic AoE barrage)
- **Skill (mana 300):** summons up to 5 slimes cycling kindNums [20002, 20003, 20004], lifetime 600t, while allies < 30
- **Immune:** all CC and DoT receivers no-op'd
- **No phases:** behaviour is constant; difficulty scales via kindNum data config + summon pressure

**In-game text** (generic placeholder pair)
- Normal: "Knockback"
- Skill: "Special Skill"

**Normal attack — rock barrage**
- Big stationary boss (`moveSpd=0`, `radius=40`, `hitHeight=135`, `numBlock=0`). Idle/move/lookAt overridden.
- `attackMain()` gathers ALL enemies within 300 and, for each, fires a `Rock` with `chance(0.6)` — a probabilistic AoE barrage, not single-target. Custom `generateWeapon` spawns `Rock` with random jitter.

**Skill — slime summon (mana 300)**
- Loops up to 5 times summoning slimes, cycling kindNums [20002, 20003, 20004] (Red, Blue, Yellow Slime) via `summonUnit(VO, 600)` (600-tick lifetime); stops early if ally count reaches 30.

**Passive / special**
- **CC/DoT immunity:** no-ops `stun, knockBack, freeze, curse, silence, poison, blow, binding, shock, addDotDamage, onHitted` → fully CC/DoT-immune.

**Key values**
| variable | value | meaning |
|---|---|---|
| kindNum | 20001 | King Slime |
| maxMana | 300 | skill interval (≈300 ticks) |
| attack radius | 300 | `getEnemiesWithin(300)` barrage range |
| per-target fire chance | 60% (0.6) | per enemy per attack |
| skill summon loop | 5 | up to 5 slimes per skill |
| summon kindNums | [20002, 20003, 20004] | Red / Blue / Yellow (cycled) |
| summon lifetime | 600t | ticks |
| ally cap | 30 | stops summoning at ≥30 |
| weaponClass | Rock | barrage projectile |
| radius / hitHeight | 40 / 135 | boss footprint |
| objAtk | {34:1} | hit frame |

**Formulas**
- Skill gated by `mana >= maxMana`. Barrage expected projectiles ≈ 0.6 × (enemies within 300).

**⚠️ Description vs code**
- The "Knockback" / "Special Skill" stub massively understates it: no knockback — a CC-immune boss raining `Rock` (60%/enemy within 300) and periodically summoning 5 mixed-color slimes (20002/20003/20004).
- **Boss check:** no per-HP phase transitions or enrage in the class; behaviour is constant, scaling only via the kindNum data config (level) and summon pressure.

---

### Blue Slime — `SlimeBlue` (kindNum: 20003)
**TL;DR.** A tiny, trivial add that King Slime summons — it just attacks on frame 36 with no skill of its own.

**At a glance**
- **Role:** Basic enemy minion (summoned by King Slime)
- **Attack:** base attack on frame 36 (no weaponClass → melee, or whatever its kindNum data sets)
- **No skill:** stats come from the kindNum 20003 data config
- **Siblings:** `SlimeRed` (20002) / `SlimeYellow` (20004) are structurally identical

**In-game text** (placeholders)
- Normal: "None"
- Skill: "Special Skill"

**Normal attack**
- Only `initializeData()` (`sheetName="KingSlime"`, `radius=7`, `hitHeight=15`, `objAtk={36:1}`). No `attackMain`/skill override and no weaponClass → base attack hitting on frame 36.

**Key values**
| variable | value | meaning |
|---|---|---|
| kindNum | 20003 | Blue Slime |
| objAtk | {36:1} | hit frame |
| radius / hitHeight | 7 / 15 | collision (tiny) |

**✓ Matches description** — trivially: "None"/"Special Skill" placeholders for a plain summoned add with no skill. Stats from the kindNum 20003 data config.
