# EF2 unit mechanics — Part 7 (DeathKnight1, Golem1, GreatMage1, Ant1, WolfWarrior1, Artillery1, SSlime1/2/3, Pilot1, Spider1/2)

> Bundle: `runtime/bundles/mounted/1.11.42/assets/index.js`. Classes extend base `qQ`.
> Shared semantics referenced below:
> - `doMeleeAttack(t,i=1)` / `doRangeAttack(t)` apply `doDamage(t,i)`; `i` is the **damage multiplier** (fraction of this unit's ATK). `1`=100%, `.3`=30%.
> - `getEnemiesWithin(r)` = enemies within radius `r` (px). `taunt(r)` forces every enemy within radius `r` (whose `target!==this`) to retarget this unit.
> - Skill gating (base `qQ`): a unit with `hasSkill` enters skill state when `this.mana >= this.maxMana` (mana builds through combat). `skillMain()` runs on the `objSkill` frame.
> - `numShot>1` (base normal attack): primary target always hit, then up to `numShot-1` extra nearby enemies get an additional attack with **decreasing probability** (`chance(numShot-1)`, then `chance(numShot-2)`, …).

---

### Death Knight / Death Knight Ⅱ — `DeathKnight1` (kindNum: 59, 60 evolved)
**Role:** melee dps / summoner
**Description (in-game):**
- Normal (`UNIT_NATK_59`): "Delivers a heavy melee strike that deals AoE damage to enemies ahead and has a chance to inflict Curse."
- Skill (`UNIT_SATK_59`): "Summons skeleton soldiers to support you in battle."
- (evolved 60) Normal: "...higher chance to inflict Curse." Skill: "Summons stronger skeleton soldiers..."

**How it works (code):** Base stats `baseMaxHp=150, atkDmg=3, def=10, moveSpd=2.6, atkRange=8`. `attackMain()` melee-hits the main target at full damage, has chance `i` to `curse(s)` it, then hits up to `h` extra enemies in a forward box at offset `e*direction` (`getEnemiesAtPos`) for `n×` damage, each with the same curse chance. Curse chance/duration and AoE scale with evolution. **Skill is mana-gated at DOUBLE mana** — `execute()` overrides the base gate: when `mana >= 2*maxMana` it calls `skillMain()` and zeroes mana. `skillMain()` summons skeleton soldiers (`summonUnitSync`) up to a cap, tinted `0xFF8888`, with leash/detect ranges set per battle context; evolved summons a different (stronger) skeleton kind, higher level (+3 level bonus), bigger scale, longer duration. Also has `onKillEnemy`: every kill buffs all of its alive **summoned** skeletons with ATK-speed, move-speed, AND ATK-damage buffs.

**Hard values:**
| variable | value | meaning |
|---|---|---|
| objAtk / objSkill | {37:1} / {88:1} | hit frame for attack / skill |
| skill mana gate | `mana >= 2*maxMana` | needs 2 full mana bars |
| curse chance | .2 base / .3 evolved | per-target curse chance |
| curse duration | 60 / 80 | ticks |
| AoE 2ndary dmg mult | .5 / .6 | fraction of ATK on extra targets |
| AoE box offset (e) | 40 / 50 (×direction) | forward reach |
| AoE max extra targets (h) | 4 / 6 | |
| SKELETON_KIND_NUM_1/2 | 14 / 39 | summon kind (base=Dark Mage kind 14, evolved=39) |
| SKELETON_DURATION_1/2 | 1200 / 1500 | summon lifetime ticks |
| MAX_SKELETONS_1/2 | 3 / 5 | concurrent summon cap |
| SKELETON_SCALE_1/2 | .9 / 1 | |
| SKELETON_LEVEL_BONUS_2 | 3 | evolved summon level bonus |
| SKELETON_LEASH_RANGE | 90 | summon leash (mine-battle context) |
| onKill buff value | 1.2 base / 1.35 evolved | see formulas |
| onKill buff duration | 60 / 80 | ticks |

**Formulas:** onKill buffs use the standard multiplicative convention: `addAttackSpeedBuff/addMoveSpeedBuff/addAttackDamageBuff(this.kindNum, 1.2|1.35, dur)` ⇒ +120% (base) / +135% (evolved) to summoned skeletons. Since all use `id=this.kindNum`, multiple Death Knights of the same evolution don't stack these (max).

**Buffs/debuffs applied:**
- `curse(60|80)` on hit targets (debuff on enemy).
- onKill: ATK-speed, move-speed, ATK-dmg buffs (id=`kindNum`, value 1.2/1.35, dur 60/80) on **own summoned skeletons only**.

**Δ description vs code:** none material — matches. Description omits (a) the skill costs TWO full mana bars, and (b) the hidden on-kill buff broadcast to its skeletons. Curse is on both the main hit and the AoE hits.

**Notes:** Summoned skeleton kind switches 14→39 on evolution (a genuinely different unit, not just a stat bump), plus +3 levels and +duration/+cap (3→5).

---

### Golem / Golem Ⅱ — `Golem1` (kindNum: 62, 71 evolved)
**Role:** tank / melee AoE
**Description (in-game):**
- Normal (`UNIT_NATK_62`): "Deals AoE damage to nearby enemies with its giant fists and has a chance to stun them."
- Skill (`UNIT_SATK_62`): "Deals a powerful AoE strike and deploys a physical barrier. Using it a set number of times triggers a taunt."
- (evolved 71) Normal: "...to more enemies...higher chance to stun." Skill: "...Taunt activates after a set number of uses."

**How it works (code):** `setData` sets `evolved = evolStage>=1`. `attackMain()`: melee-hits the main ground target (full dmg, `doMeleeAttack(t,1)`) with stun chance `t`; then `getEnemiesWithin(55)` hits each extra **ground** enemy for `0.3×` dmg, applying stun (chance `t`, `dur i`) up to `s` total stuns. Air targets are skipped (`!isAir`). `skillMain()` (mana-gated): increments `skillUseCount`, and **every 3rd use** calls `taunt(120)`; deploys a physical shield for `t` ticks; then a big strike — main target `2|2.5×` dmg + guaranteed `stun(60)`, plus `getEnemiesWithin(50)` extra ground targets at `.5|.7×` with `stun(60)` (chance `e`) up to `n` stuns.

**Hard values:**
| variable | value | meaning |
|---|---|---|
| objAtk / objSkill | {53:1} / {76:1} | hit frames |
| atk stun chance (t) | .3 / .4 | normal-attack stun chance |
| atk stun dur (i) | 50 / 60 | ticks |
| atk max stuns (s) | 4 / 6 | |
| atk AoE radius | 55 | px (`getEnemiesWithin`) |
| atk 2ndary dmg mult | .3 | |
| taunt cadence | every 3rd skill use | `skillUseCount%3==0` |
| taunt radius | 120 | px |
| physical shield dur | 110 / 130 | ticks |
| skill main dmg mult | 2 / 2.5 | on main target |
| skill 2ndary dmg mult | .5 / .7 | |
| skill 2ndary stun chance (e) | .5 / 1 | evolved = guaranteed |
| skill stun dur | 60 | ticks (both main & 2ndary) |
| skill AoE radius | 50 | px |
| skill max 2ndary stuns (n) | 6 / 10 | |

**Formulas:** n/a (no stat buffs; shield = damage-block effect via `showPhysicalShield(dur)`).

**Buffs/debuffs applied:** stun on enemies (normal + skill); `showPhysicalShield(110|130)` self-shield; `taunt(120)` every 3rd skill.

**Δ description vs code:** none — matches. The "more enemies / higher chance" for evolved is realized as larger stun caps (4→6, 6→10) and chances (.3→.4 normal, .5→1 skill 2ndary). Both normal and skill ignore airborne enemies (not stated). Skill always stuns the main target (the chance only governs the AoE splash).

---

### Fire Mage / Fire Mage Ⅱ — `GreatMage1` (kindNum: 66, 75 evolved)
**Role:** ranged mage / summoner
**Description (in-game):**
- Normal (`UNIT_NATK_66`): "Fires flaming magic projectiles to attack enemies from range."
- Skill (`UNIT_SATK_66`): "Summons multiple fire birds that spread damage across enemies."
- (evolved 75) Normal: same. Skill: "Summons more fire birds to deal spread damage to enemies."

**How it works (code):** `unitType=RANGE`, `weaponClass=FireMagicBall1`. `setData` sets `numShot` = `NUM_SHOT_1=2` (base) / `NUM_SHOT_2=3` (evolved) — so a normal attack fires the magic ball at the main target plus 1 (base) / 2 (evolved) extra nearby enemies via the base `numShot` multi-target mechanic. `skillMain()` (mana-gated): picks the nearest `BIRD_COUNT` attackable enemies (`getAttackableEnemyList`) and spawns `BIRD_COUNT` `FireMageBird1` weapons at `0.6×` damage, distributing them round-robin across the available targets (`s[t%s.length]`), each tagged with the mage's `direction`.

**Hard values:**
| variable | value | meaning |
|---|---|---|
| weaponClass | FireMagicBall1 | normal projectile |
| objAtk / objSkill | {37:1} / {64:1} | hit frames |
| NUM_SHOT_1 / _2 | 2 / 3 | normal-attack targets (incl. main) |
| BIRD_COUNT_1 / _2 | 7 / 14 | fire-birds summoned on skill |
| fire-bird dmg mult | .6 | per `generateWeapon(...,.6)` |

**Formulas:** n/a (no stat buffs).

**Buffs/debuffs applied:** none.

**Δ description vs code:** none — matches. "More fire birds" is the literal 7→14 jump on evolution; normal-attack spread (numShot 2→3) is undocumented but consistent with "magic projectiles" plural.

**Notes:** Class is named `GreatMage1` but is the **Fire Mage** (66/75), not a "Great Mage" — identified by `FireMagicBall1`/`FireMageBird1` and the fire-bird skill.

---

### Ent / Ent Ⅱ — `Ant1` (kindNum: 65, 74 evolved)
**Role:** melee AoE / ranged-skill bruiser
**Description (in-game):**
- Normal (`UNIT_NATK_65`): "Performs a melee attack with its massive body, dealing AoE damage to nearby enemies."
- Skill (`UNIT_SATK_65`): "Drops a boulder onto enemies, launching them into the air."
- (evolved 74) Normal: "...damage to a wider area of enemies." Skill: "Drops more boulders to launch enemies into the air."

**How it works (code):** `setData` sets `evolved`. `attackMain()`: melee-hits the main ground target at full dmg, then `getEnemiesWithin(t)` hits up to `i` total **ground** enemies (`!isAir`) for `0.4×` dmg each. Both the AoE radius and the cap grow on evolution. `skillMain()` (mana-gated): gathers enemies within `160` px and throws `t` boulders (`generateWeapon(target, AntRock1, 1)` = full dmg) at them, round-robin (`i[s%i.length]`).

**Hard values:**
| variable | value | meaning |
|---|---|---|
| objAtk / objSkill | {50:1} / {76:1} | hit frames |
| atk AoE radius (t) | 40 / 50 | px (base / evolved) |
| atk max targets (i) | 4 / 6 | incl. main |
| atk 2ndary dmg mult | .4 | |
| skill boulder count (t) | 3 / 4 | base / evolved |
| skill target-search radius | 160 | px |
| skill boulder weapon | AntRock1 @ 1× | the "boulder" projectile |

**Formulas:** n/a.

**Buffs/debuffs applied:** none (boulder launch/knock-up is a weapon effect, not a buff).

**Δ description vs code:** none — matches. The class name `Ant1` is a misnomer for the **Ent**; the `AntRock1` projectile is the boulder. "Drops more boulders" = 3→4 evolved. Both attacks ignore airborne enemies.

---

### Wolf Warrior / Wolf Warrior Ⅱ — `WolfWarrior1` (kindNum: 64, 73 evolved)
**Role:** assassin (teleport-combo)
**Description (in-game):**
- Normal (`UNIT_NATK_64`): "Teleports to enemies and unleashes an assassination-style combo attack."
- Skill (`UNIT_SATK_64`): "Teleports up to 10 times to deliver a chain of strikes, then taunts enemies to draw their attacks."
- (evolved 73) Skill same; Normal adds: "Teleport chain attacks can also trigger during normal attacks."

**How it works (code):** `baseMaxHp=150`. Multi-frame attack/skill driven by `attackCallIndex`/`skillCallIndex` (reset on start frames). Normal `attackMain()` fires 3 hit-frames (`objAtk={48,53,56}`): hit 1 strikes the current target; hits 2 & 3 — **only when evolStage>=1** — re-acquire a random enemy within `90` px, teleport to it (`x=target.x-20*direction`), and strike (this is the "teleport during normal attack" evolved-only behavior). Skill `onSkillStartFrame` saves position; `skillMain()` runs across many skill hit-frames (`objSkill` lists 8 frames): on call 1 it hits the current target, on calls **2–10** it teleports to a random enemy within `100` px, hits it, and with `.3` chance knocks it back; after the 10th it returns to the saved position and `taunt(100)`.

**Hard values:**
| variable | value | meaning |
|---|---|---|
| objAtk | {48:1,53:1,56:1} | 3 normal hit frames |
| objSkill | {91,94,97,100,103,104,108,112} | skill hit frames |
| normal retarget radius | 90 | px (evolved hits 2 & 3 only) |
| skill teleport count | ≤10 | calls 2–10 teleport+strike |
| skill retarget radius | 100 | px |
| skill knockback chance | .3 | per teleport hit |
| knockBack args | (2*direction, 0, 20) | impulse |
| teleport offset | 20 px (×direction) | lands just in front of target |
| taunt radius | 100 | px, after the chain |

**Formulas:** n/a.

**Buffs/debuffs applied:** `knockBack` on teleport-struck enemies (chance .3); `taunt(100)` at end of skill.

**Δ description vs code:** none — matches. "Up to 10 teleports" is exact (skillCallIndex 2–10). The evolved-only "teleport chain during normal attacks" is implemented as the 2nd/3rd normal-attack hits retargeting+teleporting; base normal attack does NOT teleport (hits 2 & 3 are evolStage-gated).

---

### Artillery — `Artillery1` (kindNum: none found)
**Role:** ranged dps (enemy/basic) — skill is a no-op stub
**Description (in-game):** none. No `Artillery` name appears in `en.json` or `unit_desc.json`; this class has no kindNum description, so it is an enemy/unmapped unit (no UNIT_NATK/SATK text).
**How it works (code):** `baseMaxHp=150, atkDmg=3, def=10, moveSpd=2.6, atkDuration=200, atkRange=8`, `unitType=RANGE`, `weaponClass=YellowEnergyBall`. It fires `YellowEnergyBall` projectiles at the nearest enemy on its `objAtk={87:1}` frame via the base ranged-attack path. `hasSkill=!0` and `objSkill={155:1,166:1,177:1}` are declared, but **`skillMain(){}` is completely empty** — the skill plays its animation and does nothing.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| baseMaxHp / atkDmg / def | 150 / 3 / 10 | base stats |
| moveSpd / atkDuration / atkRange | 2.6 / 200 / 8 | |
| weaponClass | YellowEnergyBall | normal projectile |
| objAtk / objSkill | {87:1} / {155,166,177} | hit frames (skill frames unused) |
**Formulas:** `atkDuration=200` ⇒ attack interval; standard base ranged attack.
**Buffs/debuffs applied:** none.
**Δ description vs code:** No in-game description to compare. **Notable:** `hasSkill=true` with an **empty `skillMain()`** — when mana fills it enters skill state and wastes the cast (animation only, zero effect). Likely an unfinished/placeholder or pure-flavor enemy.
**Notes:** Default stat block (150/3/10/2.6/200/8) is shared verbatim with DeathKnight1 — looks like an uncustomized template.

---

### Slime 1 — `SSlime1` (kindNum: 1060)
**Role:** basic enemy (smallest split-slime)
**Description (in-game):**
- Normal (`UNIT_NATK_1060`): "None"
- Skill: "Special Skill" (no real skill)
**How it works (code):** Smallest of the split chain: `hitHeight=12, hitWidth=10, radius=6`, `dieIncFrame=.4` (slow death anim). Plain melee attacker on `objAtk={58:1}`; `skillFrames` alias the attack frames and there is **no `skillMain`, no `onDie`** — it does NOT split further (terminal slime).
**Hard values:**
| variable | value | meaning |
|---|---|---|
| hitHeight / hitWidth / radius | 12 / 10 / 6 | smallest body |
| objAtk | {58:1} | melee hit frame |
| dieIncFrame | .4 | death-anim speed |
**Formulas:** n/a.
**Buffs/debuffs applied:** none.
**Δ description vs code:** none — "None"/"Special Skill" matches; it's a trivial melee enemy with no skill and no split.

---

### Slime 2 — `SSlime2` (kindNum: 1061)
**Role:** basic enemy (splits on death)
**Description (in-game):** Normal: "None"; Skill: "Special Skill".
**How it works (code):** Medium body (`hitHeight=23, hitWidth=14, radius=8`, `dieIncFrame=.4`). Plain melee (`objAtk={58:1}`, no `skillMain`). **`onDie()` splits it** (only in mine/`mii` battle context): spawns `SPLIT_COUNT=3` enemies of `SPLIT_KIND_NUM=1060` (= **SSlime1**) via `spawnEnemyAt`, scattered in a ring around the death point — angle `2π·r/3 + 0.5·rand` and distance `20 + 15·rand` px — each inheriting the parent's `lastPercentHp` and `lastPercentAtkDmg` (so children carry over its HP%/ATK% scaling) at the same `level`.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| hitHeight / hitWidth / radius | 23 / 14 / 8 | medium body |
| objAtk | {58:1} | melee hit frame |
| SPLIT_KIND_NUM | 1060 | spawns SSlime1 |
| SPLIT_COUNT | 3 | children per death |
| ring distance | 20 + 15·rand | px from death point |
| ring angle | 2π·i/3 + .5·rand | even thirds + jitter |
**Formulas:** child stat carry-over via `lastPercentHp` / `lastPercentAtkDmg` percentages passed to `spawnEnemyAt`.
**Buffs/debuffs applied:** none.
**Δ description vs code:** none stated to compare; the split-into-3-smaller-slimes is the real "special" behavior. **Split only fires inside a mine/`mii` battle** (`if(!(this.battleController instanceof mii))return`) — outside that context it dies without splitting.

---

### Slime 3 — `SSlime3` (kindNum: 1062)
**Role:** basic enemy (largest slime)
**Description (in-game):** Normal: "None"; Skill: "Special Skill".
**How it works (code):** Largest body (`hitHeight=22, hitWidth=18, radius=10`) with its **own stat block**: `maxHp=100, atkDmg=10, def=10, moveSpd=2.2, atkDuration=100, atkRange=15`. Plain melee on `objAtk={58:1}`. **No `onDie` override and no SPLIT constants** — so in this build SSlime3 does **NOT** split on death (despite being the largest, one might expect it to split into SSlime2).
**Hard values:**
| variable | value | meaning |
|---|---|---|
| maxHp / atkDmg / def | 100 / 10 / 10 | own stats (only slime with explicit block) |
| moveSpd / atkDuration / atkRange | 2.2 / 100 / 15 | |
| hitHeight / hitWidth / radius | 22 / 18 / 10 | largest body |
| objAtk | {58:1} | melee hit frame |
**Formulas:** `atkDuration=100` ⇒ faster attack interval than the others.
**Buffs/debuffs applied:** none.
**Δ description vs code:** none stated. **Notable:** only **SSlime2** splits; SSlime3 (largest) and SSlime1 (smallest) have no `onDie` split. So the death chain is one-step: SSlime2 → 3× SSlime1. SSlime3 is a standalone tankier slime, not the top of a split ladder.

---

### Pilot / Pilot Ⅱ — `Pilot1` (kindNum: 79, 80 evolved)
**Role:** air ranged dps
**Description (in-game):**
- Normal (`UNIT_NATK_79`): "Fires consecutive shots from the air at multiple enemies."
- Skill (`UNIT_SATK_79`): "Launches a missile and taunts 1 enemy, forcing them to target you."
- (evolved 80) Normal: "...at more enemies." Skill: "Fires more missiles and taunts 1 enemy..."

**How it works (code):** `isAir=true, airHeight=75`, `unitType=RANGE`, normal `weaponClass=FireBullet`, `skillWeaponClass=PilotMissile1`. `setData` sets `skillShotCount` and `maxAttackTargets` by evolution. Normal attack builds a target list (`getEnemiesForDirection` up to `maxAttackTargets`, main target first), then `attackMain()` fires at them: base has `.85` chance to fire one shot per call; **evolved fires one shot then keeps firing extra shots while `random.chance(.4)` succeeds** (geometric burst), cycling through `attackTargetList`. `skillMain()`: takes nearest 5 attackable enemies, launches `skillShotCount` missiles at `1.5×` dmg (round-robin over them), then **taunts exactly 1 enemy** — sets `s.target=this` for the first enemy whose target isn't already the Pilot, then `break`.

**Hard values:**
| variable | value | meaning |
|---|---|---|
| isAir / airHeight | true / 75 | flying unit |
| weaponClass / skillWeaponClass | FireBullet / PilotMissile1 | normal / skill projectiles |
| objAtk / objSkill | {45,50,55} / {70:1} | hit frames |
| maxAttackTargets | 4 / 7 | normal-attack target pool (base/evolved) |
| skillShotCount | 3 / 5 | missiles per skill (base/evolved) |
| normal single-shot chance (base) | .85 | per attack call |
| evolved burst chance | .4 | extra-shot continuation prob |
| skill target search | nearest 5 | `getAttackableEnemyList(5)` |
| skill dmg mult | 1.5 | missile damage |
| taunt count | 1 enemy | first enemy not already targeting Pilot |

**Formulas:** evolved normal-attack shot count is a geometric burst: 1 + Geometric(.4) shots per call (expected ≈ 1.67), each at a cycled target.

**Buffs/debuffs applied:** taunt-of-one — directly reassigns `target=this` on a single enemy (not the radius `taunt()` helper).

**Δ description vs code:** none — matches. "Fires more missiles" = 3→5; "more enemies" = maxAttackTargets 4→7 plus the evolved burst-firing. The "taunt 1 enemy" is a direct single-target retarget (`s.target=this; break`), not an AoE taunt; constants `skillShotCount`/`maxAttackTargets` are stored on the instance and overwritten in `setData`.

---

### Spider — `Spider1` (kindNum: none found)
**Role:** basic enemy (poison melee)
**Description (in-game):** none — no `Spider` name in `en.json`/`unit_desc.json`; unmapped enemy (no UNIT_NATK/SATK).
**How it works (code):** `hitHeight=18, hitWidth=15, radius=13, setSize(.9)`. Calls base `attackMain()` (standard melee) then with `.1` chance `poison(40)` the target. **`onDie()`** is a death-burst: takes up to 5 enemies within `40` px and, for each, `.4` chance to `poison(40)` plus `doDamage(i,1)` (full-ATK hit).
**Hard values:**
| variable | value | meaning |
|---|---|---|
| size / radius | .9 / 13 | body |
| objAtk | {57:1} | melee hit frame |
| on-hit poison chance / dur | .1 / 40 | per normal attack |
| onDie radius | 40 | px |
| onDie max targets | 5 | |
| onDie poison chance / dur | .4 / 40 | |
| onDie dmg mult | 1 | full ATK to each |
**Formulas:** `poison(t)` applies a slow effect with magnitude/duration `t` (sets `numSlow`).
**Buffs/debuffs applied:** `poison(40)` (slow) on hit and on death-burst targets.
**Δ description vs code:** No description to compare. Behavior: poison-on-hit melee enemy with a death-burst that poisons + damages nearby units.

---

### Spider (Ⅱ) — `Spider2` (kindNum: none found)
**Role:** basic enemy (stronger poison melee)
**Description (in-game):** none — unmapped enemy.
**How it works (code):** Identical structure to Spider1 but stronger: `setSize(1.1)` (bigger), on-hit poison chance `.15`/dur `60`; `onDie()` death-burst over `55` px, up to 5 enemies, `.5` poison chance/dur `60`, plus `doDamage(i,1)` each. The evolved/upgraded Spider.
**Hard values:**
| variable | value | meaning |
|---|---|---|
| size / radius | 1.1 / 13 | larger body |
| objAtk | {57:1} | melee hit frame |
| on-hit poison chance / dur | .15 / 60 | per normal attack |
| onDie radius | 55 | px |
| onDie max targets | 5 | |
| onDie poison chance / dur | .5 / 60 | |
| onDie dmg mult | 1 | full ATK each |
**Formulas:** same `poison(t)` slow mechanic.
**Buffs/debuffs applied:** `poison(60)` on hit and on death-burst.
**Δ description vs code:** No description. **Note:** Spider2 is Spider1 with bumped numbers (size .9→1.1, poison chance .1→.15 / .4→.5, duration 40→60, onDie radius 40→55) — a difficulty-tier variant, not an evolStage of Spider1.
