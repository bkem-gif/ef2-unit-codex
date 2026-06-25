# EF2 unit mechanics — Part 1 (12 undead/dark-faction classes)

Bundle: `runtime/bundles/mounted/1.11.42/assets/index.js` (v1.11.42). Base class `qQ`.

**`numShot` semantics** (from base `attackMain`): the unit always hits its primary target once; if `numShot>1` it then tries `ceil(numShot-1)` additional nearby enemies, each struck with probability equal to the running remainder `t` (starts at `numShot-1`, decremented by 1 per extra target). So `numShot=1.3` ⇒ 1 guaranteed + 30% for a 2nd; `numShot=2.5` ⇒ 2 guaranteed extra + 50% for a 3rd. Works for melee (`doMeleeAttack`) and ranged (`doRangeAttack`); ranged extras are delayed by `multiShotDelay*(1+e)`.

---

### Wolf — `NWolf` (kindNum: 1001)
**TL;DR.** A plain gray wolf that just bites the nearest enemy — no skill, no special tricks.

**At a glance**
- **Role:** Basic enemy / summoned melee
- **Attack:** single-target melee, hit on attack-frame 54
- **No skill, no evolve:** all HP/ATK/DEF come from unit data, not hard-coded

**In-game text**
- Normal: "None"
- Skill: "Special Skill" (placeholder — no real skill text)

**Passive / special**
- Used as the Wolf Rider's summon and as a basic mob. The Ice Wolf is a separate class (`IceWolf`, kindNum 1003).

**Key values**
| variable | value | meaning |
|---|---|---|
| radius | 13 | body radius |
| hitHeight / hitWidth | 20 / 15 | hitbox |
| objAtk | {54:1} | 1 hit on attack-frame 54 |
| setSize | 0.9 | render scale |

**⚠️ Description vs code**
- No real description to compare (placeholder text only). No skill and no evolStage handling; pure stat-block unit.

---

### Dark Mage / Dark Mage Ⅱ — `BlackMage1` (kindNum: 14 · Ⅱ 39)
**TL;DR.** A ranged mage that fires dark bullets and casts a single heavy dark orb; evolving adds a chance to splash a second target rather than truly firing faster.

**At a glance**
- **Role:** Ranged DPS (mage)
- **Attack:** fires `BlackMageBall1` projectiles; Ⅱ adds +30% chance for a 2nd target
- **Skill:** one heavy dark orb (`DarkMageDarkBall1`) at the current target
- **Skill damage:** ×1.5 base → **×2** at Ⅱ

**In-game text**
- Normal: "Attacks enemies from range with dark bullets." (Ⅱ: "Unleashes dark projectiles at an increased fire rate for ranged attacks.")
- Skill: "Fires a dark orb that deals massive damage to enemies." (Ⅱ: "Launches a dark orb that deals even greater damage to enemies.")

**Normal attack**
- Fires `BlackMageBall1`, hit on `objAtk={62:1}`. `numShot=1` base, **1.3** evolved (Ⅱ adds a 30% chance to splash a 2nd nearby enemy per shot — not a literal fire-rate change).

**Skill — heavy dark orb (skill-frame {103:1})**
- `generateWeapon(this.target, DarkMageDarkBall1, mult)` — one heavy orb at the current target, `mult=1.5` base / **2** evolved. Targets only `this.target` despite "enemies" plural in the text.

**Base → Ⅱ**
- `numShot` 1 → 1.3 (+30% 2nd-target chance); skill damage ×1.5 → ×2.

**Key values**
| | base | Ⅱ |
|---|---|---|
| numShot | 1 | 1.3 (+30% 2nd target) |
| skill dmg mult | ×1.5 | ×2 |
| weaponClass | BlackMageBall1 | BlackMageBall1 |
| skill projectile | DarkMageDarkBall1 | DarkMageDarkBall1 |
| objAtk / objSkill | {62:1} / {103:1} | {62:1} / {103:1} |
| firePoint | (16,-2) | (16,-2) |

**Formulas**
- Skill damage = ATK × `1.5` (base) or `× 2` (evolved).

**⚠️ Description vs code**
- The evolved "increased fire rate" wording is realized as a `numShot` multi-target bump (1→1.3), **not** an `atkSpd` change — flavor text ("fire rate") differs from the mechanism (extra-target chance).

---

### Graveyard Hero — `SkeletonX1` (kindNum: 1002)
**TL;DR.** A summoned skeleton with a fixed, hard-coded stat kit that just hits the nearest enemy — no skill.

**At a glance**
- **Role:** Basic / summoned melee (fixed stat-block)
- **Attack:** single-target melee, hit on attack-frame 58
- **Unique:** base stats baked into the class (HP/ATK/DEF/speed are constants, not data-driven)
- **No skill, no evolve**

**In-game text**
- Normal: "None"
- Skill: "Special Skill" (placeholder)

**Passive / special**
- The "Graveyard Hero" summon (e.g. a raised skeleton with a fixed kit) — the only class in this set that hard-codes its stats rather than reading them from unit data.

**Key values**
| variable | value | meaning |
|---|---|---|
| baseMaxHp / maxHp / hp | 100 | health |
| atkDmg | 10 | attack damage |
| def | 10 | defense |
| moveSpd | 1.6 | move speed |
| atkDuration | 200 | ticks between attacks |
| atkRange | 8 | melee range |
| objAtk | {58:1} | hit on attack-frame 58 |

**Formulas**
- `atkSpd = 1e4 / atkDuration` = 1e4/200 = **50**.

**⚠️ Description vs code**
- Placeholder description only — nothing to compare. No evolStage handling.

---

### Skeleton Soldier / Skeleton Soldier Ⅱ — `SkeletonMan1` (kindNum: 13 · Ⅱ 38)
**TL;DR.** A melee skeleton whose skill is a heavy bone strike that can stun the target.

**At a glance**
- **Role:** Melee DPS
- **Attack:** single-target melee (bone), hit on frame 58
- **Skill:** heavy strike ×2 (Ⅱ ×3) with a chance to stun
- **Stun:** 5% chance → **15%** at Ⅱ; 120t (~2s) either way

**In-game text**
- Normal: "Attacks nearby enemies using a bone as a weapon." (Ⅱ: "Attacks enemies with a bone in melee combat.")
- Skill: "Delivers a heavy strike that deals massive damage and has a chance to stun enemies." (Ⅱ: "Delivers a powerful heavy strike for massive damage with a high chance to stun.")

**Skill — heavy strike (skill-frame {102:1})**
- `doMeleeAttack(target, mult)` with `mult=2` base / **3** evolved; then if the target survives, `random.chance(p) && target.stun(120)` with `p=0.05` base / **0.15** evolved. Stun = 120t (~2s).

**Base → Ⅱ**
- Skill damage ×2 → ×3; stun chance 5% → 15%. Stun duration (120t) is constant.

**Key values**
| | base | Ⅱ |
|---|---|---|
| skill dmg mult | ×2 | ×3 |
| stun chance | 0.05 (5%) | 0.15 (15%) |
| stun duration | 120t (~2s) | 120t (~2s) |
| objAtk / objSkill | {58:1} / {102:1} | {58:1} / {102:1} |

**Formulas**
- Skill damage = ATK × `2` / `3`.

**✓ Matches description** — "massive damage" + "chance to stun"; evolve raises both damage (2→3) and stun chance (0.05→0.15), consistent with "high chance to stun."

---

### (basic skeleton) — `SkeletonMan2` (kindNum: none — basic enemy variant)
**TL;DR.** A stripped-down Skeleton Soldier used as a basic mob: plain melee, no skill.

**At a glance**
- **Role:** Basic enemy melee
- **Attack:** single-target melee, hit on frame 58
- **No skill, no evolve, no hard-coded stats**

**Passive / special**
- Same anims/sounds as SkeletonMan1 but with no skill — presented as a basic mob, not a hero, so it has no `UNIT_NATK/SATK` text. Distinguished from SkeletonMan1 by the absent heavy-strike/stun skill, and from SkeletonX1 by the absent hard-coded stats.

**Key values**
| variable | value | meaning |
|---|---|---|
| objAtk | {58:1} | 1 hit on attack-frame 58 |
| radius / hitHeight | 7 / 27 | hitbox |

**⚠️ Description vs code**
- No localized description to compare — no matching kindNum in the description set. This is a basic enemy skeleton, not a playable hero (kindNums 13/38 belong to SkeletonMan1, which has the stun skill this unit lacks).

---

### Skeleton Warrior / Skeleton Warrior Ⅱ — `SkeletonWarrior1` (kindNum: 16 · Ⅱ 41)
**TL;DR.** A melee assassin that hits twice per swing and whose skill is a 6-hit flurry delivered from invisibility.

**At a glance**
- **Role:** Melee DPS / assassin
- **Attack:** double-hit melee (2 hits per swing)
- **Skill:** go invisible for 40t, then a 6-hit flurry on one target
- **Skill per-hit:** ×0.9 base → **×1** at Ⅱ (~5.4× / 6× total if all land)

**In-game text**
- Normal: "Strikes enemies with a melee double hit." (Ⅱ: "Attacks enemies with a melee double-hit.")
- Skill: "While invisible, unleashes a rapid flurry of attacks that deals multiple hits." (Ⅱ: "From stealth, unleashes a furious rapid-fire combo that deals massive damage.")

**Normal attack**
- Double hit: `objAtk={38:1, 41:1}` — two hit frames per swing.

**Skill — invisible flurry (6 hit frames {63,65,67,69,71,73})**
- First `transparent(40)` (invisible/untargetable for 40t), then if a target exists, `doMeleeAttack(target, mult)` on each of the 6 skill hit frames with `mult=0.9` base / **1** evolved. If no target, returns to idle.

**Passive / special**
- Self status `transparent(40)` (stealth) during the skill — not a stat buff.

**Base → Ⅱ**
- Per-hit multiplier 0.9 → 1; body size 1 → 1.05. Invisibility duration (40t) and hit count (6) are constant.

**Key values**
| | base | Ⅱ |
|---|---|---|
| skill dmg mult (per hit) | ×0.9 | ×1 |
| skill hit count | 6 | 6 |
| transparent (stealth) | 40t | 40t |
| normalSize / evolSize | 1 | 1.05 |
| objAtk | {38:1, 41:1} | {38:1, 41:1} |
| objSkill | {63,65,67,69,71,73 → 1 each} | (same) |

**Formulas**
- Skill damage = ATK × `0.9` / `1` **per hit**, ×6 hit frames ⇒ ~5.4× / 6× total if all land.

**✓ Matches description** — double-hit normal, invisible multi-hit flurry skill. Note "massive damage" comes from the **6** stacked hits, not a high single multiplier (per-hit is below 1× at base).

---

### Great Hammer / Great Hammer Ⅱ — `GreatHammer1` (kindNum: 17 · Ⅱ 42)
**TL;DR.** A hammer bruiser whose normal swing can stun, and whose skill smashes the main target plus a fan of up to 5 nearby enemies, stunning them too.

**At a glance**
- **Role:** Melee DPS (AoE / control)
- **Normal:** every hit has a chance to stun (20% → **40%** at Ⅱ)
- **Skill:** heavy main hit + AoE (radius 80) on ≤5 nearby enemies, each can be stunned
- **Skill main damage:** ×1.5 → **×2** at Ⅱ

**In-game text**
- Normal: "Strikes enemies with a hammer and has a chance to stun them." (Ⅱ: "Swings a hammer in melee combat with a chance to stun enemies.")
- Skill: "Delivers a heavy strike that deals massive damage, inflicts AoE damage on nearby enemies, and has a chance to stun them." (Ⅱ: "Strikes with devastating power, dealing heavy damage over a wider area with a high chance to stun.")

**Normal attack**
- Base melee, then if the target is alive `random.chance(p) && target.stun(d)` — `p=0.2`/`d=30` base, **`p=0.4`/`d=40`** evolved. Built-in chance-to-stun on every normal hit.

**Skill — hammer smash (skill-frame {109:1})**
- Main target: `doDamage(target, mult)` with `mult=1.5` base / **2** evolved.
- AoE: `getEnemiesWithin(80, true)` and for each (excluding main) `doDamage(e, 0.5/0.7)` + `random.chance(0.6) && e.stun(60)`. Capped at **5 secondary enemies** (loop breaks after `s>4`).

**Buffs & debuffs**
- Stun on normal hit: chance 0.2 → 0.4, duration 30t → 40t, on the target.
- Stun on each AoE skill enemy: chance 0.6, 60t, ≤5 targets (constant across base/Ⅱ).

**Base → Ⅱ**
- Normal stun chance 0.2 → 0.4, duration 30 → 40; skill main mult 1.5 → 2; AoE mult 0.5 → 0.7. AoE radius (80), AoE stun chance (0.6), AoE stun duration (60t), and target cap (5) are constant.

**Key values**
| | base | Ⅱ |
|---|---|---|
| normal stun chance | 0.2 | 0.4 |
| normal stun dur | 30t | 40t |
| skill main dmg mult | ×1.5 | ×2 |
| skill AoE dmg mult | ×0.5 | ×0.7 |
| skill AoE radius | 80 | 80 |
| skill AoE stun chance | 0.6 | 0.6 |
| skill AoE stun dur | 60t | 60t |
| skill max secondary targets | 5 | 5 |
| objAtk / objSkill | {71:1} / {109:1} | {71:1} / {109:1} |

**Formulas**
- Main skill dmg = ATK × `1.5` / `2`; AoE dmg = ATK × `0.5` / `0.7` to ≤5 nearby enemies.

**✓ Matches description** — but note "higher chance to stun" on evolve refers to the **normal-attack** stun (0.2→0.4); the skill's AoE stun (chance 0.6) is unchanged. Evolve scaling is on damage and the normal-hit stun, not the skill's AoE stun.

---

### Ghost / Ghost Ⅱ — `Ghost1` (kindNum: 15 · Ⅱ 40)
**TL;DR.** A flying mage that throws spirit orbs and can vanish to dodge enemy targeting; the skill is pure invisibility, no damage.

**At a glance**
- **Role:** Ranged DPS (mage, flying)
- **Attack:** fires `GhostBall1` orbs; Ⅱ adds +30% chance for a 2nd target
- **Skill:** go invisible/untargetable — 70t base → **90t** at Ⅱ, no damage
- **Flying:** `isAir=true`, airHeight 40

**In-game text**
- Normal: "Attacks enemies from range with a spirit orb." (Ⅱ: "Hurls ghost orbs at an increased fire rate for ranged attacks.")
- Skill: "Becomes invisible and avoids enemy targeting for a certain period of time." (Ⅱ: "Turns invisible for a longer duration, evading enemy attacks.")

**Normal attack**
- Fires `GhostBall1` (`objAtk={60:1}`). `numShot=1.3` **only when evolved** (base stays 1) — Ⅱ adds a 30% chance for a 2nd nearby enemy per orb.

**Skill — vanish (skill-frame {60:1})**
- Just `transparent(d)` with `d=70` base / **90** evolved. Pure invisibility/untargetable window, no damage.

**Passive / special**
- Self status `transparent(70/90)` (stealth) — not a stat buff.

**Base → Ⅱ**
- Invisibility 70t → 90t; `numShot` 1 → 1.3 (+30% 2nd-target normal).

**Key values**
| | base | Ⅱ |
|---|---|---|
| numShot | 1 | 1.3 (+30% 2nd target) |
| skill transparent | 70t | 90t |
| normalSize / evolSize | 0.85 | 0.95 |
| weaponClass | GhostBall1 | GhostBall1 |
| isAir / airHeight | true / 40 | true / 40 |
| objAtk / objSkill | {60:1} / {60:1} | {60:1} / {60:1} |

**⚠️ Description vs code**
- The evolved "increased fire rate" normal is again implemented as `numShot` 1→1.3 (extra-target chance), **not** an `atkSpd` increase. (Skill deals no damage — invisibility is the entire skill.)

---

### Dark Sorcerer / Dark Sorcerer Ⅱ — `DarkMage1` (kindNum: 18 · Ⅱ 43)
**TL;DR.** A multi-role caster that fires dark projectiles, periodically summons skeletons, and on cast curses enemies + shields allies — and can resurrect slain low-grade enemies to fight for you.

**At a glance**
- **Role:** Ranged DPS + summoner / support
- **Attack:** fires `DarkMageBall1`; numShot 1.5 → **2.5** at Ⅱ
- **Skill:** curse ≤3 (Ⅱ ≤4) enemies + shield 1 (Ⅱ 2) allies + summon a skeleton
- **Passive summon:** a Skeleton Soldier (kind 13) every 1000t
- **Revive passive:** on kill of a grade≤2 enemy, energy-gated chance to resurrect it as an ally

**In-game text**
- Normal: "Fires dark projectiles from a distance and periodically summons skeleton soldiers." (Ⅱ: "Fires dark projectiles at an increased fire rate. Periodically summons a skeleton soldier.")
- Skill: "Curses enemies, grants a shield to allies, and summons skeletons." (Ⅱ: "Curses more enemies, shields more allies, and summons skeletons to fight at your side.")

**Normal attack**
- Fires `DarkMageBall1`; `numShot = 1.5` base (1 guaranteed extra + 50% for a 2nd) / **2.5** evolved (2 extra + 50% for a 3rd).

**Skill — curse + shield + summon (`skillMain`)**
- (1) `getAttackableEnemyList(i)` with `i=3` base / **4** evolved; fires `DarkMageSkillBall1` (mult 1.5) at the **first** enemy, and `curse(180)` on **every** enemy in the list.
- (2) Shields `s` random alive allies (`s=1` base / **2** evolved) via `showPowerShield(120)`.
- (3) Calls `trySummonSkeleton()`.

**Passive / special**
- **Passive summon:** every `SUMMON_COOLDOWN=1000` ticks, summons a skeleton (`SKELETON_KIND_NUM=13`) for 1000t base / **1300t** evolved, tinted `16746632`.
- **Revive on kill** (`onKillEnemy`): if the killed enemy is `grade≤2`, not air, not summoned, and `reviveEnergy ≥ REVIVE_ENERGY` (350 base / **220** evolved), then with chance 0.1 base / **0.2** evolved, resurrects a copy as an ally (`summonUnitSync(reviveVO, REVIVE_DURATION=600, 0)`, at the corpse, `revive()`, `initDelay=8`). `reviveEnergy` increments +1/tick and resets to 0 on a successful revive.

**Buffs & debuffs**
- Curse: 180t, on ≤3 (Ⅱ ≤4) enemies (the whole attackable list) — skill.
- Shield: `showPowerShield`, 120t, on 1 (Ⅱ 2) random allies — skill.

**Base → Ⅱ**
- numShot 1.5 → 2.5; curse targets 3 → 4; shield count 1 → 2; summon duration 1000 → 1300; revive energy 350 → 220; revive chance 0.1 → 0.2.

**Key values**
| | base | Ⅱ |
|---|---|---|
| numShot | 1.5 | 2.5 |
| skill curse targets | 3 | 4 |
| curse duration | 180t | 180t |
| skill shield count | 1 | 2 |
| showPowerShield (ally) | 120t | 120t |
| SUMMON_COOLDOWN | 1000t | 1000t |
| summon duration | 1000t | 1300t |
| SKELETON_KIND_NUM | 13 | 13 |
| REVIVE_ENERGY | 350 | 220 |
| revive chance | 0.1 | 0.2 |
| REVIVE_DURATION | 600t | 600t |
| skill projectile | DarkMageSkillBall1 (mult 1.5) | (same) |
| tint | 16746632 | 16746632 |

**Formulas**
- Skill orb dmg = ATK × `1.5`. Revive gate: `reviveEnergy` (+1/tick) must reach 350/220; resets to 0 on a successful revive.

**✓ Matches description** — all three skill clauses (curse / ally shield / summon) plus the passive summon are present. The **revive passive** (resurrecting defeated enemies) is an extra mechanic beyond literal skill text; evolve broadens it (energy 350→220, chance 0.1→0.2), consistent with "more enemies / more allies / skeletons to fight at your side."

**Notes**
- Only grade≤2 (non-air, non-summoned) enemies can be revived. The skill curse hits the whole attackable list (3/4) but the skill **orb** only hits list[0]. Revived/summoned units share the orange tint `16746632` and `initDelay=8`.

---

### Dark Archer / Dark Archer Ⅱ — `DarkArcher1` (kindNum: 57 · Ⅱ 58)
**TL;DR.** A ranged archer firing silence-tipped arrows that hit several enemies at once, with a heavy multi-target silence skill and a chance to revive slain enemies as allies.

**At a glance**
- **Role:** Ranged DPS (multi-target / control + summoner)
- **Attack:** silence arrows hitting 2 (Ⅱ 3) enemies in the firing arc
- **Skill:** heavy hit + long silence on ≤3 (Ⅱ ≤5) enemies
- **Revive passive:** on kill of a grade≤3 enemy, energy-gated chance to resurrect it as an ally

**In-game text**
- Normal: "Fires silence-infused arrows to hit multiple enemies at once. Defeated enemies have a chance to revive as allied soldiers." (Ⅱ: "Fires silence-infused arrows to hit more enemies at once. Defeated enemies have a higher chance to revive as allied soldiers.")
- Skill: "Fires an enhanced arrow that deals heavy damage to multiple enemies and applies a long silence." (Ⅱ: "Fires an enhanced arrow that hits even more enemies with heavy damage and an even longer silence.")

**Normal attack**
- Multi-target with silence. On `onAttackStartFrame` builds `targetList = getEnemiesForDirection(direction, atkRange, n)` with `n=2` base / **3** evolved (current `target` placed first). `objAtk` = `OBJ_ATK_1={80:1,90:1}` (2 frames) base / `OBJ_ATK_2={80:1,87:1,94:1}` (3 frames) evolved. Each hit pops the next target, does `doRangeAttack(i)` + `i.silence(t)` with `t=30` base / **40** evolved.

**Skill — enhanced arrow (skill-frame {132:1})**
- Shows `DarkArcherSkillEffect1`, then `getAttackableEnemyList(n)` with `n=3` base / **5** evolved; for each enemy `doDamage(e, mult)` (`mult=1.5` base / **2** evolved) + `silence(i)` with `i=90` base / **150** evolved (long silence).

**Passive / special**
- **Revive on kill** (`onKillEnemy`, `summonEnergy` +1/tick): if killed enemy `grade≤3`, not air, not summoned, and `summonEnergy ≥ SUMMON_ENERGY` (250 base / **150** evolved), then with chance 0.15 base / **0.3** evolved, revives a copy as an ally (`summonUnitSync(skeletonVO, SKELETON_DURATION=600, 0)`, at the corpse, `revive()`, tint `16746632`, `initDelay=8`).

**Buffs & debuffs**
- Silence on each normal-hit target: 30t base / 40t evolved.
- Silence on each skill target: 90t base / 150t evolved.

**Base → Ⅱ**
- Normal targets 2 → 3; normal silence 30 → 40; skill targets 3 → 5; skill dmg mult 1.5 → 2; skill silence 90 → 150; revive energy 250 → 150; revive chance 0.15 → 0.3.

**Key values**
| | base | Ⅱ |
|---|---|---|
| normal targets n | 2 | 3 |
| objAtk | {80,90} (OBJ_ATK_1) | {80,87,94} (OBJ_ATK_2) |
| normal silence | 30t | 40t |
| skill targets | 3 | 5 |
| skill dmg mult | ×1.5 | ×2 |
| skill silence | 90t | 150t |
| SUMMON_ENERGY | 250 | 150 |
| revive chance | 0.15 | 0.3 |
| SKELETON_DURATION | 600t | 600t |
| objSkill | {132:1} | {132:1} |

**Formulas**
- Skill dmg = ATK × `1.5` / `2` per target.

**✓ Matches description** — multi-target silence arrows, kill-revive passive, heavy multi-target silence skill. Evolve scales every axis (targets 2→3 / 3→5, silence 30→40 / 90→150, dmg 1.5→2, revive energy 250→150, chance 0.15→0.3), consistent with "more enemies / longer silence / higher revive chance."

**Notes**
- Revive grade gate (≤3) is **looser** than DarkMage1's (≤2). Both use the same orange tint `16746632` and `initDelay=8`.

---

### Bomber / Bomber Ⅱ — `Bomber1` (kindNum: 68 · Ⅱ 77)
**TL;DR.** A ranged bomber that lobs handfuls of small bombs, drops big bombs on the densest enemy cluster, and goes into a self-buffing frenzy every 7 kills.

**At a glance**
- **Role:** Ranged DPS (AoE bomber, self-buff)
- **Attack:** throws 3 (Ⅱ 5) small bombs per attack
- **Skill:** drops 2 (Ⅱ 3) big bombs on the densest enemy cluster
- **Frenzy:** every 7 kills, self atk-speed + move-speed buff (+80% → **+110%** at Ⅱ)

**In-game text**
- Normal: "Throws multiple small bombs for ranged attacks. After defeating a certain number of enemies, enters a frenzy state." (Ⅱ: "Throws more small bombs for ranged attacks. After defeating a certain number of enemies, enters a stronger frenzy state.")
- Skill: "Detects the densest enemy cluster and drops 2 large bombs on that location." (Ⅱ: "Detects the densest enemy cluster and drops 3 large bombs on the location.")

**Normal attack**
- Throws `BomberSmallBomb1` with `numShot = 3` base (`NUM_SHOT_1`) / **5** evolved (`NUM_SHOT_2`). `maxMana=700`. Fire point `firePointNormal=(4,-36)`.

**Skill — big bomb drop (`skillMain`, fires when `currentFrame==100`)**
- Drops `BomberBigBomb1`, count `2` base / **3** evolved (`t?3:2`). Collects all alive enemies within a 220×220 box of itself (`|dx|≤220 && |dy|≤220`), shuffles them, then builds the bomb list starting with the current `target` and filling up to `count` extra. Each big bomb is staggered by `delay = 26 + 5·e`. Fire point `firePointSkill=(2,-60)`.

**Passive / special — frenzy (`onKillEnemy`)**
- Increments `killCount`; every **7 kills** it resets and applies `addAttackSpeedBuff(id 200, val, dur)` + `addMoveSpeedBuff(id 201, val, dur)` with `val=0.8`/`dur=200` base, **`val=1.1`/`dur=240`** evolved, plus an `Accelerate` effect. `killCount` is class state, not reset by the skill — frenzy is independent of the skill cooldown.

**Buffs & debuffs**
- Attack speed (self): +80% (Ⅱ +110%), 200t (Ⅱ 240t) — id 200
- Move speed (self): +80% (Ⅱ +110%), 200t (Ⅱ 240t) — id 201

**Base → Ⅱ**
- numShot 3 → 5; big-bomb count 2 → 3; frenzy buff value 0.8 → 1.1; frenzy buff duration 200 → 240.

**Key values**
| | base | Ⅱ |
|---|---|---|
| numShot (small bombs) | 3 | 5 |
| skill big-bomb count | 2 | 3 |
| frenzy buff value | 0.8 (+80%) | 1.1 (+110%) |
| frenzy buff duration | 200t | 240t |
| frenzy kill threshold | 7 | 7 |
| skill detect box | 220×220 | 220×220 |
| big-bomb stagger | 26 + 5·e | 26 + 5·e |
| maxMana | 700 | 700 |
| atkspd buff id / movespd buff id | 200 / 201 | 200 / 201 |
| firePoint normal / skill | (4,-36) / (2,-60) | (same) |
| objAtk / objSkill | {62:1} / {100:1} | {62:1} / {100:1} |

**Formulas**
- `atkSpd = orgAtkSpd × (1 + 0.8/1.1)` ⇒ **+80% / +110%** during frenzy; move speed uses the same formula. Both expire after 200/240 ticks.

**✓ Matches description** — multi small bombs, kill-count frenzy (every 7 kills), cluster-detect big-bomb skill (2/3 bombs).

**Notes**
- The two frenzy buffs use **distinct ids** (200, 201) so they don't collide; same-id buffs from multiple Bombers wouldn't stack (max kept).

---

### Hand of Death / Hand of Death Ⅱ — `DeathHand1` (kindNum: 63 · Ⅱ 72)
**TL;DR.** A big melee bruiser that knocks enemies back with each punch and whose skill is a 3-stage forward AoE that launches enemies into the air.

**At a glance**
- **Role:** Melee DPS (knockback / launcher, AoE control)
- **Normal:** punch + small forward-AoE knockback
- **Skill:** 3-stage forward AoE, each stage launches ≤4 (Ⅱ ≤7+1) enemies upward
- **Skill damage:** ×1 flat per hit; evolve widens area and launch height, not damage

**In-game text**
- Normal: "Delivers a melee attack with a powerful fist that knocks enemies back." (Ⅱ: same text.)
- Skill: "Unleashes consecutive AoE attacks forward, launching multiple enemies into the air." (Ⅱ: "Strikes forward with consecutive attacks in a wider area, launching multiple enemies even higher into the air.")

**Normal attack**
- `doMeleeAttack(target)`, then `target.knockBack(direction*i, 0, s)` with `i=2`/`s=12` base, **`i=3`/`s=15`** evolved. Also finds enemies near a point `e` units ahead (`getEnemiesWithPos(x+e·dir, y, e)`, `e=30` base / **40** evolved) and knocks each of them back too — a small forward-AoE knockback.

**Skill — 3-stage launch (`skillMain`, frames `objSkill={63:1,66:1,68:1}`)**
- For stage h (0,1,2, keyed off currentFrame 63/66/68): targets a box at `x + (40+40·h)·dir` (progressively farther forward), radius `i=55` base / **65** evolved; does `doDamage(u, 1)` + `u.blow(direction*s, e)` (air-launch) on up to `n+1` enemies (`n=4` base / **7** evolved), with blow horizontal `s=3`/`4` and vertical `e=-3.5`/`-4.2` (more negative = higher). Spawns `DeathHandSkillEffect1` at each stage.

**Buffs & debuffs**
- `knockBack` on normal hits (no stat change).
- `blow` (air-launch) on skill targets (no stat change).

**Base → Ⅱ**
- Normal knockback `i` 2→3, `s` 12→15, forward-AoE reach `e` 30→40; skill radius 55→65, max targets 4→7, blow horiz 3→4, blow vert −3.5→−4.2; body size 1→1.1.

**Key values**
| | base | Ⅱ |
|---|---|---|
| normal knockback dist `i` | ×2 | ×3 |
| normal knockback `s` | 12 | 15 |
| normal forward-AoE reach `e` | 30 | 40 |
| skill stages | 3 | 3 |
| skill box offset | 40 + 40·h | 40 + 40·h |
| skill radius `i` | 55 | 65 |
| skill max targets `n` | 4 (+1) | 7 (+1) |
| skill dmg mult | ×1 | ×1 |
| skill blow horiz `s` | 3 | 4 |
| skill blow vert `e` | −3.5 | −4.2 |
| normalSize / evolSize | 1 | 1.1 |
| objAtk / objSkill | {45:1} / {63,66,68} | (same) |

**Formulas**
- Skill damage = ATK × `1` per hit, across 3 stages; launch vertical velocity −3.5 / −4.2 (more negative = higher launch).

**✓ Matches description** — knockback fist normal + 3-stage forward AoE launch skill. Evolve widens every dimension (radius 55→65, targets 4→7, launch −3.5→−4.2, forward AoE reach 30→40), consistent with "wider area / launching enemies even higher."

**Notes**
- `getEnemiesWithPos` (local override) ignores air units (`h.isAir` skipped) and untargetable units, so both the normal forward-AoE and the skill only hit grounded enemies.

---

## Cross-cutting notes / deltas summary
- **`numShot` is the "fire rate" of evolved ranged units in flavor text** (BlackMage1, Ghost1) — code implements it as a multi-target chance bump (1→1.3), not an `atkSpd` change. DarkMage1 (1.5→2.5) and Bomber1 (3→5) use the same field for literal multi-projectile counts.
- **Revive/summon passives** (DarkMage1, DarkArcher1) are energy-gated on-kill mechanics with a grade filter (≤2 for DarkMage1, ≤3 for DarkArcher1), shared orange tint `16746632`, `initDelay=8`.
- **No mismatches like the drummer's missing ATK buff** were found in this set — every description clause is backed by a code call. The only "extra" mechanics beyond literal skill text are the DarkMage1/DarkArcher1 kill-revive passives (which the normal-attack text does mention).
