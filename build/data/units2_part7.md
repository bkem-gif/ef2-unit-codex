# EF2 unit mechanics — Part 7 (DeathKnight1, Golem1, GreatMage1, Ant1, WolfWarrior1, Artillery1, SSlime1/2/3, Pilot1, Spider1/2)

> Bundle: `runtime/bundles/mounted/1.11.42/assets/index.js`. Classes extend base `qQ`.
> Shared semantics referenced below:
> - `doMeleeAttack(t,i=1)` / `doRangeAttack(t)` apply `doDamage(t,i)`; `i` is the **damage multiplier** (fraction of this unit's ATK). `1`=100%, `.3`=30%.
> - `getEnemiesWithin(r)` = enemies within radius `r` (px). `taunt(r)` forces every enemy within radius `r` (whose `target!==this`) to retarget this unit.
> - Skill gating (base `qQ`): a unit with `hasSkill` enters skill state when `this.mana >= this.maxMana` (mana builds through combat). `skillMain()` runs on the `objSkill` frame.
> - `numShot>1` (base normal attack): primary target always hit, then up to `numShot-1` extra nearby enemies get an additional attack with **decreasing probability** (`chance(numShot-1)`, then `chance(numShot-2)`, …).

---

### Death Knight / Death Knight Ⅱ — `DeathKnight1` (kindNum: 59 · Ⅱ 60)
**TL;DR.** Cursing melee bruiser that cleaves enemies ahead, and on a double-charged skill summons skeleton soldiers that get stronger with every kill it makes.

**At a glance**
- **Role:** Melee DPS / summoner
- **Attack:** heavy melee on the main target + a forward AoE cleave, each hit can apply Curse
- **Skill:** mana-gated at **2 full bars**; summons up to 3 skeletons (Ⅱ 5)
- **Passive:** every kill buffs its own living skeletons (atk-speed, move-speed, atk-damage)

**In-game text**
- Normal: "Delivers a heavy melee strike that deals AoE damage to enemies ahead and has a chance to inflict Curse." (Ⅱ: "...higher chance to inflict Curse.")
- Skill: "Summons skeleton soldiers to support you in battle." (Ⅱ: "Summons stronger skeleton soldiers...")

**Normal attack**
- Melee-hits the main target at full damage with curse chance `i`; then hits up to `h` extra enemies in a forward box at offset `e×direction` (`getEnemiesAtPos`) for `n×` damage, each with the same curse chance.
- Curse: 20% chance / 60t base; **Ⅱ 30% / 80t**.

**Skill — summon skeletons (mana ≥ 2× maxMana)**
- `execute()` overrides the base gate: fires only when `mana >= 2*maxMana`, then zeroes mana.
- Summons skeleton soldiers (`summonUnitSync`) up to the cap, tinted `0xFF8888`, with leash/detect ranges set per battle context.
- **Ⅱ** summons a different (stronger) skeleton kind (14→39), +3 levels, bigger scale, longer duration, higher cap (3→5).

**Passive / special**
- `onKillEnemy`: every kill broadcasts ATK-speed + move-speed + ATK-damage buffs to all of its alive **summoned skeletons only**.

**Buffs & debuffs**
- Curse: 60t (Ⅱ 80t), on every hit target (main + AoE) — debuff on enemy
- On-kill atk-speed / move-speed / atk-damage: +120% (Ⅱ +135%), 60t (Ⅱ 80t), own summoned skeletons — id = `kindNum`

**Base → Ⅱ**
- Curse 20%→30%, 60t→80t; AoE 2ndary dmg .5→.6, box offset 40→50, max extra targets 4→6; skeleton kind 14→39, +3 levels, scale .9→1, duration 1200→1500, cap 3→5; on-kill buff 1.2→1.35, 60t→80t.

**Key values**
| | base | Ⅱ |
|---|---|---|
| objAtk / objSkill | {37:1} / {88:1} | same |
| skill mana gate | mana ≥ 2× maxMana | same |
| curse chance | 20% (.2) | 30% (.3) |
| curse duration | 60t | 80t |
| AoE 2ndary dmg mult | .5 | .6 |
| AoE box offset (e) | 40 (×dir) | 50 (×dir) |
| AoE max extra targets (h) | 4 | 6 |
| skeleton kind | 14 (Dark Mage) | 39 |
| skeleton duration | 1200t | 1500t |
| max skeletons | 3 | 5 |
| skeleton scale | .9 | 1 |
| skeleton level bonus | — | +3 |
| skeleton leash range | 90 (mine context) | 90 |
| on-kill buff value | 1.2 | 1.35 |
| on-kill buff duration | 60t | 80t |
| base stats | maxHp 150, atkDmg 3, def 10, moveSpd 2.6, atkRange 8 | same |

**Formulas**
- On-kill buffs: `addAttackSpeedBuff/addMoveSpeedBuff/addAttackDamageBuff(this.kindNum, 1.2|1.35, dur)` ⇒ +120% (base) / +135% (Ⅱ). All use `id=this.kindNum`, so multiple Death Knights of the same evolution don't stack (max-per-id).

**✓ Matches description** — the curse-cleave and "stronger skeletons" scaling all check out. The description simply omits two hidden facts: the skill costs **two** full mana bars, and the on-kill buff broadcast to its skeletons.

**Notes**
- The skeleton kind genuinely switches (14→39), a different unit and not just a stat bump.

---

### Golem / Golem Ⅱ — `Golem1` (kindNum: 62 · Ⅱ 71)
**TL;DR.** Ground-only AoE tank that fist-smashes and stuns nearby enemies, and on its skill drops a big strike behind a self-shield, taunting every 3rd cast.

**At a glance**
- **Role:** Tank / melee AoE
- **Attack:** full-dmg main hit + 0.3× AoE within 55px, both with stun chance (air enemies skipped)
- **Skill:** big strike (2× / Ⅱ 2.5×) + physical shield; guaranteed main-target stun
- **Cadence:** every 3rd skill use also taunts (radius 120)

**In-game text**
- Normal: "Deals AoE damage to nearby enemies with its giant fists and has a chance to stun them." (Ⅱ: "...to more enemies...higher chance to stun.")
- Skill: "Deals a powerful AoE strike and deploys a physical barrier. Using it a set number of times triggers a taunt." (Ⅱ: "...Taunt activates after a set number of uses.")

**Normal attack**
- Melee-hits the main **ground** target at full dmg with stun chance `t`; then `getEnemiesWithin(55)` hits each extra ground enemy for 0.3× dmg, applying stun (chance `t`, dur `i`) up to `s` total stuns.
- Airborne enemies are skipped (`!isAir`).

**Skill — big strike + shield (mana-gated)**
- Increments `skillUseCount`; **every 3rd use** (`skillUseCount%3==0`) calls `taunt(120)`.
- Deploys a physical shield for the shield duration (`showPhysicalShield`).
- Strike: main target takes 2× (Ⅱ 2.5×) + **guaranteed** `stun(60)`; then `getEnemiesWithin(50)` extra ground targets at .5× (Ⅱ .7×) with `stun(60)` at chance `e` up to `n` stuns.

**Buffs & debuffs**
- Stun (normal): dur `i` 50t (Ⅱ 60t), chance `t` 30% (Ⅱ 40%), ≤`s` targets — on enemies
- Stun (skill): 60t, main guaranteed; AoE chance `e` 50% (Ⅱ 100%), ≤`n` targets — on enemies
- Physical shield: 110t (Ⅱ 130t), self (damage-block, no stat change)
- Taunt: radius 120, every 3rd skill use

**Base → Ⅱ**
- Normal stun chance .3→.4, dur 50→60, cap 4→6; skill main dmg 2→2.5, 2ndary dmg .5→.7, 2ndary stun chance .5→1, cap 6→10; shield 110→130.

**Key values**
| | base | Ⅱ |
|---|---|---|
| objAtk / objSkill | {53:1} / {76:1} | same |
| atk stun chance (t) | .3 | .4 |
| atk stun dur (i) | 50t | 60t |
| atk max stuns (s) | 4 | 6 |
| atk AoE radius | 55px | 55px |
| atk 2ndary dmg mult | .3 | .3 |
| taunt cadence | every 3rd skill use | same |
| taunt radius | 120px | 120px |
| physical shield dur | 110t | 130t |
| skill main dmg mult | 2 | 2.5 |
| skill 2ndary dmg mult | .5 | .7 |
| skill 2ndary stun chance (e) | .5 | 1 (guaranteed) |
| skill stun dur | 60t | 60t |
| skill AoE radius | 50px | 50px |
| skill max 2ndary stuns (n) | 6 | 10 |

**✓ Matches description** — "more enemies / higher chance" is realized as larger stun caps (4→6, 6→10) and chances (.3→.4, .5→1). Two unstated details: both attacks **ignore airborne enemies**, and the skill **always** stuns the main target (the chance only governs the AoE splash).

---

### Fire Mage / Fire Mage Ⅱ — `GreatMage1` (kindNum: 66 · Ⅱ 75)
**TL;DR.** Ranged fire mage that lobs flaming projectiles at a few enemies, and on its skill summons a flock of fire birds that spread damage across the field.

**At a glance**
- **Role:** Ranged mage / summoner
- **Attack:** `FireMagicBall1` at the main target + 1 extra (Ⅱ 2 extra) nearby enemies (numShot 2 / Ⅱ 3)
- **Skill:** summons 7 (Ⅱ 14) fire birds at 0.6× dmg, round-robin across targets

**In-game text**
- Normal: "Fires flaming magic projectiles to attack enemies from range."
- Skill: "Summons multiple fire birds that spread damage across enemies." (Ⅱ: "Summons more fire birds to deal spread damage to enemies.")

**Normal attack**
- Multi-target via base `numShot`: hits the main target plus 1 (Ⅱ 2) extra nearby enemies with the magic ball (`numShot` = 2 / Ⅱ 3).

**Skill — fire-bird flock (mana-gated)**
- Picks the nearest `BIRD_COUNT` attackable enemies (`getAttackableEnemyList`) and spawns `BIRD_COUNT` `FireMageBird1` weapons at 0.6× damage.
- Birds are distributed round-robin across the available targets (`s[t%s.length]`), each tagged with the mage's `direction`.

**Base → Ⅱ**
- Normal targets numShot 2→3; fire-bird count 7→14.

**Key values**
| | base | Ⅱ |
|---|---|---|
| weaponClass | FireMagicBall1 | same |
| objAtk / objSkill | {37:1} / {64:1} | same |
| normal targets (incl. main) | 2 | 3 |
| fire-birds on skill | 7 | 14 |
| fire-bird dmg mult | .6 | .6 |

**✓ Matches description** — "more fire birds" is the literal 7→14 jump. The normal-attack spread (numShot 2→3) is undocumented but consistent with plural "magic projectiles".

**Notes**
- Class is named `GreatMage1` but is the **Fire Mage** (66/75), not a "Great Mage" — identified by `FireMagicBall1`/`FireMageBird1` and the fire-bird skill.

---

### Ent / Ent Ⅱ — `Ant1` (kindNum: 65 · Ⅱ 74)
**TL;DR.** Big melee bruiser that body-slams nearby ground enemies for AoE damage, and on its skill rains boulders that launch enemies into the air.

**At a glance**
- **Role:** Melee AoE / ranged-skill bruiser
- **Attack:** full-dmg main hit + 0.4× AoE on ground enemies within 40px (Ⅱ 50px), ≤4 targets (Ⅱ 6)
- **Skill:** throws 3 (Ⅱ 4) boulders (`AntRock1` @ 1×) at enemies within 160px

**In-game text**
- Normal: "Performs a melee attack with its massive body, dealing AoE damage to nearby enemies." (Ⅱ: "...damage to a wider area of enemies.")
- Skill: "Drops a boulder onto enemies, launching them into the air." (Ⅱ: "Drops more boulders to launch enemies into the air.")

**Normal attack**
- Melee-hits the main **ground** target at full dmg, then `getEnemiesWithin(t)` hits up to `i` total ground enemies (`!isAir`) for 0.4× dmg each.
- AoE radius and cap both grow on evolution.

**Skill — boulder drop (mana-gated)**
- Gathers enemies within 160px and throws `t` boulders (`generateWeapon(target, AntRock1, 1)` = full dmg), round-robin (`i[s%i.length]`).
- The boulder launch/knock-up is a weapon effect, not a buff.

**Base → Ⅱ**
- Atk AoE radius 40→50, max targets 4→6; skill boulder count 3→4.

**Key values**
| | base | Ⅱ |
|---|---|---|
| objAtk / objSkill | {50:1} / {76:1} | same |
| atk AoE radius (t) | 40px | 50px |
| atk max targets (i, incl. main) | 4 | 6 |
| atk 2ndary dmg mult | .4 | .4 |
| skill boulder count (t) | 3 | 4 |
| skill target-search radius | 160px | 160px |
| skill boulder weapon | AntRock1 @ 1× | same |

**✓ Matches description** — "drops more boulders" = 3→4; the wider-area normal = radius/cap bumps. Two notes: the class name `Ant1` is a misnomer for the **Ent** (the `AntRock1` projectile is the boulder), and both attacks ignore airborne enemies.

---

### Wolf Warrior / Wolf Warrior Ⅱ — `WolfWarrior1` (kindNum: 64 · Ⅱ 73)
**TL;DR.** Teleporting assassin that blinks to enemies for combo strikes, and on its skill chains up to 10 teleport hits before returning home and taunting.

**At a glance**
- **Role:** Assassin (teleport-combo)
- **Attack:** 3 hit-frames; hits 2 & 3 teleport-retarget **only at Ⅱ** (within 90px)
- **Skill:** up to 10 teleport strikes (within 100px), 30% knockback each, then return + taunt
- **Evolved-only:** teleport chaining during normal attacks

**In-game text**
- Normal: "Teleports to enemies and unleashes an assassination-style combo attack." (Ⅱ adds: "Teleport chain attacks can also trigger during normal attacks.")
- Skill: "Teleports up to 10 times to deliver a chain of strikes, then taunts enemies to draw their attacks."

**Normal attack**
- 3 hit-frames (`objAtk={48,53,56}`): hit 1 strikes the current target.
- Hits 2 & 3 — **only when evolStage≥1** — re-acquire a random enemy within 90px, teleport to it (`x=target.x−20×direction`), and strike. Base normal attack does NOT teleport.

**Skill — teleport chain (mana-gated)**
- `onSkillStartFrame` saves the starting position; `skillMain()` runs across 8 skill hit-frames.
- Call 1 hits the current target; calls 2–10 teleport to a random enemy within 100px, hit it, and with 30% chance knock it back.
- After the 10th, returns to the saved position and `taunt(100)`.

**Buffs & debuffs**
- Knockback: on teleport-struck enemies, 30% chance, impulse `(2×direction, 0, 20)`
- Taunt: radius 100, at end of skill

**Base → Ⅱ**
- Normal hits 2 & 3 gain teleport-retarget (off→on). Skill identical between tiers.

**Key values**
| | base | Ⅱ |
|---|---|---|
| objAtk | {48,53,56} | same |
| objSkill | {91,94,97,100,103,104,108,112} | same |
| normal retarget radius | — | 90px (hits 2 & 3) |
| skill teleport count | ≤10 (calls 2–10) | same |
| skill retarget radius | 100px | 100px |
| skill knockback chance | .3 | .3 |
| knockBack args | (2×dir, 0, 20) | same |
| teleport offset | 20px (×dir) | 20px |
| taunt radius | 100px | 100px |
| base stats | maxHp 150 | same |

**✓ Matches description** — "up to 10 teleports" is exact (skillCallIndex 2–10). The evolved-only "teleport chain during normal attacks" is the 2nd/3rd normal hits retargeting+teleporting; base normal hits 2 & 3 are evolStage-gated and do not teleport.

---

### Artillery — `Artillery1` (no kindNum)
**TL;DR.** A plain ranged enemy that fires energy balls at the nearest foe; its "skill" exists but does literally nothing.

**At a glance**
- **Role:** Ranged DPS (enemy/basic) — skill is a no-op stub
- **Attack:** fires `YellowEnergyBall` at the nearest enemy (base ranged path)
- **Skill:** enters skill state on full mana, plays animation, has **empty** `skillMain()` → zero effect

**In-game text**
- No localized description to compare (no `Artillery` name in `en.json`/`unit_desc.json`; unmapped enemy, no UNIT_NATK/SATK).

**Normal attack**
- Standard base ranged attack: fires `YellowEnergyBall` projectiles at the nearest enemy on the `objAtk={87:1}` frame.

**Skill — empty stub**
- `hasSkill=true` and `objSkill={155,166,177}` are declared, but `skillMain(){}` is completely empty — when mana fills it enters skill state and wastes the cast (animation only).

**Key values**
| variable | value | meaning |
|---|---|---|
| baseMaxHp / atkDmg / def | 150 / 3 / 10 | base stats |
| moveSpd / atkDuration / atkRange | 2.6 / 200 / 8 | |
| weaponClass | YellowEnergyBall | normal projectile |
| objAtk | {87:1} | hit frame |
| objSkill | {155,166,177} | declared but unused |

**Formulas**
- `atkDuration=200` ⇒ attack interval; standard base ranged attack.

**⚠️ Description vs code**
- No in-game description to compare. **Notable:** `hasSkill=true` with an **empty `skillMain()`** — the skill is a placeholder/unfinished or pure-flavor cast.

**Notes**
- Default stat block (150/3/10/2.6/200/8) is shared verbatim with DeathKnight1 — looks like an uncustomized template.

---

### Slime 1 — `SSlime1` (kindNum: 1060)
**TL;DR.** The smallest split-slime — a trivial melee enemy with no skill that does not split when it dies.

**At a glance**
- **Role:** Basic enemy (smallest, terminal split-slime)
- **Attack:** plain melee on `objAtk={58:1}`
- **No skill, no split:** `skillFrames` alias the attack frames; no `skillMain`, no `onDie`

**In-game text**
- Normal: "None"
- Skill: "Special Skill" (no real skill)

**Key values**
| variable | value | meaning |
|---|---|---|
| hitHeight / hitWidth / radius | 12 / 10 / 6 | smallest body |
| objAtk | {58:1} | melee hit frame |
| dieIncFrame | .4 | death-anim speed (slow) |

**✓ Matches description** — "None" / "Special Skill" matches; a trivial melee enemy with no skill and no split (terminal slime).

---

### Slime 2 — `SSlime2` (kindNum: 1061)
**TL;DR.** A medium melee slime that, only inside a mine battle, bursts into three smaller slimes on death.

**At a glance**
- **Role:** Basic enemy (splits on death)
- **Attack:** plain melee on `objAtk={58:1}`, no `skillMain`
- **Split:** `onDie()` spawns 3× SSlime1 (kind 1060) — **only in mine/`mii` battle context**

**In-game text**
- Normal: "None"
- Skill: "Special Skill"

**Passive / special**
- `onDie()` (only when `battleController instanceof mii`): spawns `SPLIT_COUNT=3` enemies of `SPLIT_KIND_NUM=1060` (SSlime1) via `spawnEnemyAt`, scattered in a ring — angle `2π·i/3 + 0.5·rand`, distance `20 + 15·rand` px.
- Children inherit the parent's `lastPercentHp` and `lastPercentAtkDmg` (HP%/ATK% scaling carry over) at the same `level`.
- Outside a mine battle (`if(!(this.battleController instanceof mii))return`) it dies without splitting.

**Key values**
| variable | value | meaning |
|---|---|---|
| hitHeight / hitWidth / radius | 23 / 14 / 8 | medium body |
| objAtk | {58:1} | melee hit frame |
| SPLIT_KIND_NUM | 1060 | spawns SSlime1 |
| SPLIT_COUNT | 3 | children per death |
| ring distance | 20 + 15·rand px | from death point |
| ring angle | 2π·i/3 + .5·rand | even thirds + jitter |

**Formulas**
- Child stat carry-over: `lastPercentHp` / `lastPercentAtkDmg` percentages passed to `spawnEnemyAt`.

**⚠️ Description vs code**
- No localized description to compare ("None" / "Special Skill"). The real "special" behavior is the split into 3 smaller slimes, which **fires only inside a mine/`mii` battle** — elsewhere it dies without splitting.

---

### Slime 3 — `SSlime3` (kindNum: 1062)
**TL;DR.** The largest, tankier slime with its own stat block and a faster attack — and, despite its size, it does not split on death.

**At a glance**
- **Role:** Basic enemy (largest slime, standalone)
- **Attack:** plain melee on `objAtk={58:1}`, faster cadence (atkDuration 100)
- **No split:** no `onDie` override and no SPLIT constants

**In-game text**
- Normal: "None"
- Skill: "Special Skill"

**Key values**
| variable | value | meaning |
|---|---|---|
| maxHp / atkDmg / def | 100 / 10 / 10 | own stats (only slime with explicit block) |
| moveSpd / atkDuration / atkRange | 2.2 / 100 / 15 | |
| hitHeight / hitWidth / radius | 22 / 18 / 10 | largest body |
| objAtk | {58:1} | melee hit frame |

**Formulas**
- `atkDuration=100` ⇒ faster attack interval than the other slimes.

**⚠️ Description vs code**
- No localized description to compare. **Notable:** only **SSlime2** splits; SSlime3 (largest) and SSlime1 (smallest) have no `onDie` split. The death chain is one-step: SSlime2 → 3× SSlime1. SSlime3 is a standalone tankier slime, not the top of a split ladder.

---

### Pilot / Pilot Ⅱ — `Pilot1` (kindNum: 79 · Ⅱ 80)
**TL;DR.** A flying gunner that strafes multiple enemies from the air, and on its skill fires a volley of missiles while taunting one foe to attack it.

**At a glance**
- **Role:** Air ranged DPS
- **Attack:** `FireBullet` at up to 4 (Ⅱ 7) targets; base 85% single shot, Ⅱ fires a geometric burst
- **Skill:** launches 3 (Ⅱ 5) `PilotMissile1` at 1.5× dmg, then taunts exactly 1 enemy
- **Flying:** `isAir=true`, airHeight 75

**In-game text**
- Normal: "Fires consecutive shots from the air at multiple enemies." (Ⅱ: "...at more enemies.")
- Skill: "Launches a missile and taunts 1 enemy, forcing them to target you." (Ⅱ: "Fires more missiles and taunts 1 enemy...")

**Normal attack**
- Builds a target list (`getEnemiesForDirection` up to `maxAttackTargets`, main target first), then fires.
- Base: 85% chance to fire one shot per call.
- **Ⅱ:** fires one shot, then keeps firing extra shots while `chance(.4)` succeeds (geometric burst), cycling through `attackTargetList`.

**Skill — missile volley + single taunt (mana-gated)**
- Takes the nearest 5 attackable enemies (`getAttackableEnemyList(5)`), launches `skillShotCount` missiles at 1.5× dmg round-robin across them.
- Then **taunts exactly 1 enemy**: sets `s.target=this` for the first enemy not already targeting the Pilot, then `break` (a direct retarget, not the radius `taunt()` helper).

**Buffs & debuffs**
- Taunt-of-one: directly reassigns `target=this` on a single enemy.

**Base → Ⅱ**
- maxAttackTargets 4→7; skillShotCount 3→5; normal firing goes from a flat 85% single shot to a .4 geometric burst.

**Key values**
| | base | Ⅱ |
|---|---|---|
| isAir / airHeight | true / 75 | same |
| weaponClass / skillWeaponClass | FireBullet / PilotMissile1 | same |
| objAtk / objSkill | {45,50,55} / {70:1} | same |
| maxAttackTargets | 4 | 7 |
| skillShotCount | 3 | 5 |
| normal single-shot chance | .85 | (burst) |
| evolved burst chance | — | .4 |
| skill target search | nearest 5 | nearest 5 |
| skill dmg mult | 1.5 | 1.5 |
| taunt count | 1 enemy | 1 enemy |

**Formulas**
- Ⅱ normal-attack shot count = 1 + Geometric(.4) per call (expected ≈ 1.67), each at a cycled target.

**✓ Matches description** — "fires more missiles" = 3→5; "more enemies" = maxAttackTargets 4→7 plus the evolved burst-firing. Note: the "taunt 1 enemy" is a direct single-target retarget (`s.target=this; break`), not an AoE taunt.

---

### Spider — `Spider1` (no kindNum)
**TL;DR.** A poison-melee enemy that has a small chance to poison on each hit, and on death bursts to poison and damage nearby units.

**At a glance**
- **Role:** Basic enemy (poison melee)
- **Attack:** standard melee, then 10% chance to `poison(40)` the target
- **Death-burst:** up to 5 enemies within 40px each get 40% poison + full-ATK hit

**In-game text**
- No localized description to compare (no `Spider` name in `en.json`/`unit_desc.json`; unmapped enemy, no UNIT_NATK/SATK).

**Normal attack**
- Base `attackMain()` (standard melee), then with 10% chance `poison(40)` the target.

**Passive / special**
- `onDie()` death-burst: takes up to 5 enemies within 40px and, for each, 40% chance to `poison(40)` plus `doDamage(i,1)` (full-ATK hit).

**Buffs & debuffs**
- Poison(40) (slow) on hit (10%) and on death-burst targets (40%) — on enemies

**Key values**
| variable | value | meaning |
|---|---|---|
| size / radius | .9 / 13 | body (`setSize(.9)`) |
| hitHeight / hitWidth | 18 / 15 | body |
| objAtk | {57:1} | melee hit frame |
| on-hit poison chance / dur | .1 / 40 | per normal attack |
| onDie radius | 40px | |
| onDie max targets | 5 | |
| onDie poison chance / dur | .4 / 40 | |
| onDie dmg mult | 1 | full ATK to each |

**Formulas**
- `poison(t)` applies a slow effect with magnitude/duration `t` (sets `numSlow`).

**⚠️ Description vs code**
- No localized description to compare. Behavior: poison-on-hit melee enemy with a death-burst that poisons + damages nearby units.

---

### Spider (Ⅱ) — `Spider2` (no kindNum)
**TL;DR.** A bigger, stronger Spider variant with harder-hitting poison on hit and a wider, deadlier death-burst.

**At a glance**
- **Role:** Basic enemy (stronger poison melee)
- **Attack:** standard melee, then 15% chance to `poison(60)`
- **Death-burst:** up to 5 enemies within 55px each get 50% poison(60) + full-ATK hit
- **Tier variant:** a difficulty bump of Spider1, not an evolStage

**In-game text**
- No localized description to compare (unmapped enemy).

**Normal attack**
- Base `attackMain()` (standard melee), then with 15% chance `poison(60)` the target.

**Passive / special**
- `onDie()` death-burst over 55px, up to 5 enemies, 50% chance to `poison(60)` plus `doDamage(i,1)` (full ATK each).

**Buffs & debuffs**
- Poison(60) (slow) on hit (15%) and on death-burst targets (50%) — on enemies

**Key values**
| variable | value | meaning |
|---|---|---|
| size / radius | 1.1 / 13 | larger body (`setSize(1.1)`) |
| objAtk | {57:1} | melee hit frame |
| on-hit poison chance / dur | .15 / 60 | per normal attack |
| onDie radius | 55px | |
| onDie max targets | 5 | |
| onDie poison chance / dur | .5 / 60 | |
| onDie dmg mult | 1 | full ATK each |

**Formulas**
- Same `poison(t)` slow mechanic.

**⚠️ Description vs code**
- No localized description to compare. **Note:** Spider2 is Spider1 with bumped numbers (size .9→1.1, poison chance .1→.15 / .4→.5, duration 40→60, onDie radius 40→55) — a difficulty-tier variant, not an evolStage of Spider1.
