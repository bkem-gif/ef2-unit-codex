# EF2 Unit Mechanics Codex

A code-derived reference for **how every unit in Endless Frontier 2 works** — combat behaviour,
hard-coded values, formulas, buffs/debuffs — paired with the in-game description and a **validated
delta** wherever the two disagree. Reverse-engineered from the game bundle
`runtime/bundles/mounted/1.11.42/assets/index.js` (read-only; no game state was modified).

> **Scope & sourcing.** 96 unit *classes* (covering 116 described `kindNum`s) are documented. The
> **mechanics, formulas, and hard values are exact from the code.** Two things are *not* in the bundle
> and are therefore omitted/approximate: (1) the authoritative `kindNum → class → base-stat` table is
> server-loaded (`/api/book/get`), so kindNum links here are matched by **behaviour** (the description
> describes what the code does) and a few are flagged "no description"; (2) **base stats** (per-unit HP/ATK
> scaling) live in that same server table — only units with *hard-coded* stat blocks (mostly summons/enemies)
> show absolute HP/ATK here. Open the in-game Encyclopedia if you want to capture the book for exact base stats.

## How the combat engine works (read this first)

- **Time is in game ticks** (~60/sec at 1× speed). Every cooldown/duration below is a tick count; all of it
  runs proportionally faster at higher game speed (speed buffs, Divine Blessing, etc.). `≈ s` values assume 1×.
- **Units** extend base class `qQ`. Key members: `initializeData()` (animation frame ranges, `objAtk` =
  `{frame: hitCount}` i.e. which attack-frame fires the hit, `hasSkill`), `setData()` (sets `evolStage`;
  most do `evolved = evolStage >= 1`), `execute()` (per-tick; usually decrements a cooldown), `attackMain()`
  (the attack/skill action), and often `skillMain()`, `onKillEnemy()`, `onDie()`, `generateWeapon()`.
- **Attacking:** target the nearest enemy in range; attack interval `atkDuration = 1e4 / atkSpd`; projectiles
  via `generateWeapon(target, WeaponType)`. Many skills are **mana-gated** (cast when `mana ≥ maxMana`).
- **Cooldown desync:** units that pulse on a timer randomize the *first* cooldown (`skillCoolDown = N*random`)
  so multiple copies don't fire in lockstep.

### How skills fire (mana, casting, triggering)
Skills are **per-unit**, not global — every unit instance tracks its own mana and casts independently.

- **Mana fills passively:** each tick, `mana += 1` for every unit (in `execute`). A unit with `maxMana = N` becomes
  skill-ready after **N ticks** (≈ N/60 s at 1×) — attacking doesn't speed it up; it's pure elapsed time.
- **A cast replaces an attack:** a unit only acts on its attack cadence (`atkDuration = 1e4/atkSpd`, gated by
  `attackCoolDown`). When it's ready to swing at a target, `attack(t)` chooses
  **`hasSkill && mana ≥ maxMana ? gotoSkillState() : gotoAttackState(t)`** — so the skill *takes the place of* the next
  normal attack once mana is full. It is **not** on a separate timer and **cannot** fire without a valid target in range.
- **Casting resets mana** (`mana = 0`), restarting the cycle. The skill then plays its `skillFrames` animation, and the
  actual effect (projectiles, buffs, summons) fires on the `objSkill` hit-frames via
  `skillMain` / `onSkillStartFrame` / `onSkillEndFrame`.
- **Silence** blocks the cast (the `attack` gate bails on `numSilence > 0`) *and* drains 200 mana — delaying the next skill.
- **Per-unit gates / variants:** some units add a condition on top of full mana — a few require `mana ≥ 2·maxMana`,
  Gold Goblin needs ≥3 nearby coins, CrowKnight needs its Flash state. A separate family (drummer-type auras) doesn't use
  mana at all — they pulse from `attackMain` on a randomized `skillCoolDown` instead (see "Cooldown desync" above).

### The buff system (this is what "buffs" means mechanically)
Buffs are applied by calling, on a unit (self or an ally), one of:
`addAttackSpeedBuff` · `addMoveSpeedBuff` · `addAttackDamageBuff` · `addDefenseBuff` · `addMaxHealthBuff` ·
`addCritMultiplierBuff` · `addCritChanceBuff` · `addRangeEvadeChanceBuff`, each with signature
**`(buffId, value, durationTicks [, refreshFlag])`**.

**Stat formulas** (recomputed every tick):
| stat | formula | combine |
|---|---|---|
| attack speed | `atkSpd = orgAtkSpd * (1 + atkSpdBuff.value)` | multiplicative |
| move speed | `moveSpd = orgMoveSpd * (1 + moveSpdBuff.value)` | multiplicative |
| attack damage | `* (1 + damageBuff.value)` | multiplicative |
| defense / max-HP | `* (1 + buff.value)` | multiplicative |
| crit damage | `critDmg = orgCritDmg + critMultBuff.value` | **additive** |
| crit chance | `critChance = orgCritChance + critChanceBuff.value` | **additive** |
| range-evade | `rangeEvade = orgRangeEvade + rangeEvadeBuff.value` | **additive** |
| attack interval | `atkDuration = 1e4 / atkSpd` | derived |

So a buff **`value` of `1.2` means +120%** for the multiplicative stats (×2.2), `0.5` ⇒ +50%, etc.
`durationTicks` is the buff's `count`, decremented each tick, removed at `< 0`.

**Stacking (class `WQ`):** the collection's `.value = Σ over DISTINCT buff-ids of the MAX value per id`
(positive buffs). Consequences: **same id ⇒ no stacking** (only the max counts; the `refreshFlag`
overwrites value+count); **different ids ⇒ summed**. Clamped to `[min,max]` (default `[-1, 10]`). This is
why two copies of the same buffer don't stack magnitude (only uptime), but two *different* speed sources do.

### Status effects (on a target unit)
Each is a **tick countdown** (`numStun`, `numCurse`, … set by the call, decremented every tick), and most
show a floating effect sprite. What each actually does:

- **stun / freeze / shock** — **incapacitate**: the unit can neither attack nor move while active.
- **knockBack / blow** — shoved back by a velocity impulse; can't act mid-knockback.
- **binding** (root) — **can't move, but can still attack** (no effect on air units).
- **slow** — reduced move **and attack** speed. **The `poison()` call sets this slow** (`numSlow`, counts down 0.5/tick,
  so its value lasts ~2× in ticks) — it is **not** damage-over-time.
- **curse** — **50% chance to miss** on each of the cursed unit's own attacks (shows "Miss").
- **silence** — can't cast its skill, and immediately drains **200 mana**.
- **transparent** (stealth) — **untargetable**: incoming attacks miss; the unit fades to 50% alpha.
- **love** (Succubus) — charm: incapacitates like a stun.
- **DoT** — `addDotDamage` / `dotDamager`: periodic damage (separate from the "poison" slow above).
- **taunt / provoke** — forces enemy units within range to **retarget onto** the taunter.
- **shields** — `powerShield` cuts incoming damage to **~1%** for its duration; `priestShield` **negates
  the next N incoming hits**.

**Immunities:** `stunImmune` / `freezeImmune` skip those; **bosses and the castle no-op all CC** (full immunity).

### Evolution
A `kindNum` and its "Ⅱ" share one class; `evolStage ≥ 1` gates the stronger branch (bigger buff `value`,
longer duration, extra hit-frames via `objAtk` swaps, more targets/projectiles). Both kindNums are listed per unit.

---

## Key findings & validated deltas

**Description ↔ code mismatches (validated):**
1. **Drums of the Battlefield (`BigDrumer1`, 69/78):** description says it buffs "**ATK**, attack speed, movement
   speed" — code calls only `addAttackSpeedBuff` + `addMoveSpeedBuff` (id 8001). **No `addAttackDamageBuff` →
   no raw-ATK buff.** Multiple drummers share id 8001 ⇒ don't stack (max), only improve uptime.
2. **Priest (`Priest1`, 55):** `UNIT_NATK_55` claims a "chance to stun" — its `YellowEnergyBall` has no stun
   hook anywhere. **Priest's basic attack does not stun.**
3. **Gunner (`Gunner1`, 4):** **undocumented 20% stun** on its normal attack (`Bullet1 → chance(.2) && stun(50)`).
4. **Green Eagle (`GreenEagle1`, 11):** **undocumented** `chance(0.5)` poison/slow on *every* projectile; the
   text only mentions knockback.
5. **Mounted Knight (`HorseKnight1`, 6):** +200% move-speed-on-kill (`addMoveSpeedBuff(value 2, 60t)`) lives in
   **base** code but is only documented on the evolved tier — base unit gets an undescribed kill buff.
6. **Succubus (`Succubus1`):** internal mislabel — `Succubus1_ATTACKSPEED_BUFF` is applied via
   **`addMoveSpeedBuff`**, so male allies get **move** speed (+50%/+40% = +90%), not attack speed; "LoveShield"
   grants no damage mitigation.
7. **Evolved "increased fire rate"** on `BlackMage1` / `Ghost1` is a `numShot` multi-target *chance*
   (1 → 1.3), **not** an `atkSpd` change. Same field drives literal projectile counts elsewhere
   (`DarkMage1` 1.5→2.5, `Bomber1` 3→5).
8. **Unicorn Archer (`Unicorn1`, 51/52):** evolved normal attack has a **dead branch** — bonus shot gated on
   `numShot ≥ 1.5` but max `numShot = 1.2`, so it never fires; evolved normal attack ≈ base (only the skill improves).
9. **Elf Castle (`ElfTown5`, 10001):** its "Knockback / Special Skill" text is a placeholder stub with no
   matching code mechanic (it's a multishot arrow turret).
10. **DarkNinja1:** auto-cast gated on `mana ≥ 500` while its own `maxMana = 250` — condition unreachable as written.
11. **Skill-weapon CC (multi-weapon units):** units that fire a *different* weapon for their skill carry CC in that
    weapon which the blurbs omit — **Pilot1** missiles add 25% `stun(10)` + a 0.5× splash (35% `stun(8)`); **Wind Mage**
    & **Sylphid** tornados **root** (`binding`); **Griffin Rider** super-spears knockBack + `stun(30)`; **Ice Mage**
    (`OrcBlizzardMage1`) rain has a 20% `freeze(60)`. The inverse also bites: **Steam Punk**'s skill missile
    (`SteamMissile1`) does **not** stun — only its normal-attack `SteamFire1` does.

**Internal class name ≠ display name:** `TigerRider1` = **Forest Guardian** (81/84) · `GreatMage1` = **Fire Mage**
(66/75) · `Ant1` = **Ent** (65/74) · `OrcBlizzardMage1` = generic **Ice Mage** (67/76) · `OrcWolfRider1`'s
summon is internally **Ice Wolf** (1003).

**Cut / unreleased / unmapped (implemented but no localized `kindNum`):** `BladeMaster1` (most complex class —
dual-mode, teleport-reap, 7 buff ids, maxMana 900), `CrowKnight1`, `Succubus1`, `GriffinRider1`, `Aladin1`
(coin-throwing genie), `Druid1` (vine/root CC). **Stubs:** `Druid2` (`skillMain` is a no-op dead expression),
`Artillery1` (empty `skillMain` — wastes the cast). **Unmapped enemy minions:** `Spider1/2`, `OrcSpearMan1`, `SkeletonMan2`.

**Other notable mechanics:** stage & raid bosses + the castle are **fully CC-immune** (raid Kings stagger only via
a separate weak-point "groggy" system); only **`SSlime2` (1061)** splits (→ 3× `SSlime1`, mines only); **RoboBombs**
are suicide bombers with a "no kill ⇒ no explosion" rule; the **castle** self-heals 0.5% max-HP / 450 ticks and
fires fractional multi-shot (`chance(numShot − floor)`); kill-stacking buffs power `CrowKnight` (crow swarm),
`Sylphid` (rage stacks → +100% atkSpd), and `Bomber` (frenzy every 7 kills).

---


# Player heroes

### Infantry / Infantry Ⅱ — `FootMan1` (kindNum: 1 · Ⅱ 26)
**TL;DR.** Basic melee swordsman; its skill is a heavy strike with a chance to stun.

**At a glance**
- **Role:** Melee DPS (basic sword infantry)
- **Attack:** basic sword on the nearest enemy (objAtk frame 49)
- **Skill:** heavy strike (×1.5, ×2.5 at Ⅱ) + chance to stun

**In-game text**
- Normal: "Strikes nearby enemies with a sword."
- Skill: "Delivers a powerful strike that damages enemies and has a chance to stun them."
- Skill (Ⅱ): "Unleashes a powerful strike that deals greater damage and stuns enemies with a higher chance."

**Skill — heavy strike**
- objSkill frame 127: `doMeleeAttack(target, 1.5 base / 2.5 Ⅱ)`, then 30% (50% at Ⅱ) chance to `stun(50 base / 60 Ⅱ)`.

**Base → Ⅱ**
- Damage ×1.5 → ×2.5; stun chance 30% → 50%; stun 50t → 60t.

**Key values**
| | base | Ⅱ |
|---|---|---|
| skill dmg mult | 1.5 | 2.5 |
| stun chance | 0.3 | 0.5 |
| stun duration | 50t | 60t |

**✓ Matches description** — evolved scales damage, stun chance, and stun duration exactly as "greater damage / higher chance" implies.

---

### Heavy Armor / Heavy Armor Ⅱ — `HeavyWarrior1` (kindNum: 2 · Ⅱ 27)
**TL;DR.** Slow tank that strikes and then drops a power shield reducing nearly all incoming damage to ~1% for a few seconds.

**At a glance**
- **Role:** Tank (self power-shield on skill)
- **Attack:** slow melee (atkDuration 200), low atkDmg 3
- **Skill:** melee hit (×1) then a 150t Power Shield (incoming damage ×0.01)
- **Stats:** maxHp 150, def 10, moveSpd 2.6, atkRange 8

**In-game text**
- Normal: "Attacks nearby enemies with a melee strike."
- Skill: "After attacking, deploys a power shield that blocks almost all physical and magic damage for a period of time."
- Skill (Ⅱ): "After attacking, deploys a Power Shield that blocks nearly all physical and magical damage for a set duration."

**Skill — power shield**
- `doMeleeAttack(target, 1)` then `showPowerShield(150)`.
- Power Shield multiplies all incoming damage by 0.01 (≈1%, both physical and magical) for its duration.

**Passive / special**
- While shielded (`numPowerShield>0`): `incomingDamage *= 0.01`.

**Buffs & debuffs**
- Self Power Shield (damage to 1%), 150 ticks. No ally/enemy effects.

**Base → Ⅱ**
- No numeric change to the shield — code is identical (`showPowerShield(150)` both tiers). Evolved benefit comes only from scaled base stats.

**Key values**
| variable | value | meaning |
|---|---|---|
| maxHp | 150 | tanky |
| atkDmg | 3 | low (defensive unit) |
| atkDuration | 200 | slow attacker |
| skill dmg mult | 1 | normal-strength hit before shield |
| powerShield duration | 150 | ticks of 1%-damage shield |
| powerShield mult | 0.01 | incoming damage ×0.01 (numPowerShield>0) |

**Formulas**
- While shielded: `incomingDamage *= 0.01`.

**✓ Matches description** — "blocks almost all physical and magic damage" = `c*=.01` applies to both types (checked before the type-specific full-block shields). The "Ⅱ" wording is cosmetic for the shield — no numeric difference in code.

**Notes**
- Unlike Infantry/HammerKnight, HeavyWarrior shows NO base/evolved branch in `skillMain` — the shield value (150) is identical regardless of evolStage.

---

### Firebird / Firebird Ⅱ — `FireBird1` (kindNum: 3 · Ⅱ 28)
**TL;DR.** High-flying ranged caster that lobs flaming shots from extreme range, with a heavy fireball skill that can stun.

**At a glance**
- **Role:** Ranged DPS (long-range flying caster)
- **Attack:** fires `FireBirdBall1` from a high-flying perch (airHeight 75)
- **Skill:** fireball ×2.5 (×3.5 at Ⅱ) + chance to stun 50t
- **Stun chance:** 30% base / 50% at Ⅱ

**In-game text**
- Normal: "Soars through the sky and launches flaming shots from extreme range."
- Skill: "Fires a powerful fireball that deals heavy damage and has a chance to stun enemies."
- Skill (Ⅱ): "Fires a powerful fireball that deals greater damage and stuns enemies with a higher chance."

**Normal attack**
- Fires `FireBirdBall1` (objAtk frame 35).

**Skill — fireball**
- objSkill frame 35: `generateWeapon(target, FireBirdBall1, 2.5 base / 3.5 Ⅱ)`, then if target alive, `random.chance(0.3 base / 0.5 Ⅱ)` ⇒ `target.stun(50)`.

**Buffs & debuffs**
- Enemy `stun(50)` on skill (chance-gated).

**Base → Ⅱ**
- Skill dmg ×2.5 → ×3.5; stun chance 30% → 50%; stun length 50t unchanged.

**Key values**
| | base | Ⅱ |
|---|---|---|
| skill dmg mult | 2.5 | 3.5 |
| skill stun chance | 0.3 | 0.5 |
| skill stun duration | 50t | 50t |
| airHeight | 75 | 75 |

**✓ Matches description** — evolved: greater dmg (3.5 vs 2.5) and higher stun chance (0.5 vs 0.3); stun length 50 unchanged.

---

### Gunner / Gunner Ⅱ — `Gunner1` (kindNum: 4 · Ⅱ 29)
**TL;DR.** Fast ranged multi-shot gunner whose skill fires a guaranteed-stun bullet — and whose ordinary bullets carry a hidden 20% stun the description never mentions.

**At a glance**
- **Role:** Ranged DPS (multi-shot gunner with directional firing)
- **Attack:** very fast (atkDuration 20), 1.2 shots base / 1.8 at Ⅱ; bullets have hidden 20%/50t stun
- **Skill:** `Bullet1` at ×2.5 (×3.5 at Ⅱ) + **guaranteed** stun 30t (50t at Ⅱ)
- **Stats:** maxHp 100, atkDmg 10, def 10, moveSpd 1.6, atkRange 150

**In-game text**
- Normal: "Attacks enemies from range with precise shots."
- Skill: "Fires a powerful projectile that guarantees a stun."
- Skill (Ⅱ): "Fires an enhanced bullet that guarantees a longer stun on enemies."

**Normal attack**
- 5 directional anim/firepoint sets — `gotoAttackState`/`gotoSkillState` pick frames/firePoint by angle to target (36° bands).
- Sets `numShot = 1.2 base / 1.8 Ⅱ`, `multiShotDelay=3`, then base multi-shot (fractional ⇒ chance of extra shot).
- Every normal `Bullet1` hit also rolls 20% → `stun(50)` (undocumented — see ⚠️).

**Skill — guaranteed-stun shot**
- `generateWeapon(target, Bullet1, 2.5 base / 3.5 Ⅱ)` and **guaranteed** `target.stun(30 base / 50 Ⅱ)`.

**Buffs & debuffs**
- Enemy `stun` — guaranteed on skill (30/50t); ALSO 20% × 50t on every normal `Bullet1` hit.

**Base → Ⅱ**
- numShot 1.2 → 1.8; skill dmg ×2.5 → ×3.5; skill stun 30t → 50t.

**Key values**
| | base | Ⅱ |
|---|---|---|
| numShot | 1.2 | 1.8 |
| skill dmg mult | 2.5 | 3.5 |
| skill stun (guaranteed) | 30t | 50t |
| atkDuration | 20 | 20 |
| atkRange | 150 | 150 |
| multiShotDelay | 3 | 3 |
| normal Bullet1 stun | 20% × 50t | 20% × 50t |

**Formulas**
- Extra-shot chance = fractional part of `numShot` (e.g. 1.8 ⇒ 80% chance of a 2nd shot).

**⚠️ Description vs code**
- Skill matches (guaranteed stun, evolved longer 50 vs 30, higher dmg). DELTA on normal: the description says only "precise shots" with no stun, but `Bullet1`'s `onHitMain` applies `stun(50)` at 20% on EVERY normal hit (`random.chance(.2)&&target.stun(50)`). The basic attack has an undocumented 20% stun.

---

### Hammer Knight / Hammer Knight Ⅱ — `HammerKnight1` (kindNum: 5 · Ⅱ 30)
**TL;DR.** Off-tank that slams the ground for AoE damage, stuns the main target plus nearby enemies, and can taunt — with an extra physical-shield proc on the evolved tier's basic attack.

**At a glance**
- **Role:** Melee DPS / off-tank (AoE slam, stun, taunt)
- **Attack:** heavy hammer melee (objAtk frame 57); Ⅱ adds 10% physShield(50) proc
- **Skill:** chance to taunt, main hit (×1.5, ×2 at Ⅱ) + stun, then AoE (×0.3) to ≤3 enemies with chance-stun
- **Taunt:** 30% (35% at Ⅱ) at skill start, taunt(60)

**In-game text**
- Normal: "Delivers a melee blow with a heavy hammer."
- Skill: "Slams the ground with great force, dealing AoE damage to nearby enemies, with a chance to stun them and trigger Taunt."
- Skill (Ⅱ): "Slams a wider area with a powerful strike, dealing heavy damage, stunning enemies with a higher chance, and can activate Taunt."

**Normal attack**
- Base attack via objAtk frame 57.
- `attackMain()` override (evolved only): 10% chance to `showPhysicalShield(50)` (50-tick PHYSICAL immunity).

**Skill — ground slam**
- Chance `tauntChance` (0.3 base / 0.35 Ⅱ) → `taunt(60)`.
- `doMeleeAttack(target, mainMult)` (1.5 base / 2 Ⅱ); `target.stun(stunMain)` (50 base / 60 Ⅱ).
- AoE: gathers enemies at a point `aoeRange` ahead (30 base / 40 Ⅱ) via `getEnemiesAtPos`, hits up to 3 with `doDamage(_, 0.3)`, each chance-stunned (0.3 base / 0.4 Ⅱ → stun 50 base / 60 Ⅱ).

**Buffs & debuffs**
- Enemy `taunt(60)` (chance-gated), `stun` on main target (50 base / 60 Ⅱ) and on AoE targets (chance-gated, 50 base / 60 Ⅱ).
- Self: evolved 10% `physicalShield(50)` on normal attack (blocks all PHYSICAL for 50t).

**Base → Ⅱ**
- AoE range 30 → 40; main dmg ×1.5 → ×2; taunt chance 0.3 → 0.35; AoE stun chance 0.3 → 0.4; all stuns 50t → 60t; +10% physShield proc on normal.

**Key values**
| metric | base | Ⅱ |
|---|---|---|
| taunt chance | 0.3 | 0.35 |
| main dmg mult | 1.5 | 2 |
| main-target stun | 50t (`h=t?60:50`) | 60t |
| AoE secondary stun chance | 0.3 | 0.4 |
| AoE stun | 50t (`n=t?60:50`) | 60t |
| AoE range | 30 | 40 |
| AoE dmg mult | 0.3 | 0.3 |
| AoE max targets | 3 | 3 |
| taunt duration | 60t | 60t |
| evolved physShield (normal) | — | 10% × 50t |

**Formulas**
- AoE centered at `(x + range*direction, y)`.

**⚠️ Description vs code**
- Skill matches (wider AoE, higher dmg, higher stun chances, longer stuns at Ⅱ). DELTA: evolved gains an undocumented 10% physical-shield proc on its NORMAL attack, which the descriptions don't mention.

---

### Mounted Knight / Mounted Knight Ⅱ — `HorseKnight1` (kindNum: 6 · Ⅱ 31)
**TL;DR.** Rapid melee combo cavalry that alternates hits between its main target and nearby foes, taunts every third skill use, and gets a big move-speed burst on every kill — even at the base tier the text doesn't mention.

**At a glance**
- **Role:** Melee DPS (rapid combo, kill-fed move-speed, periodic taunt)
- **Attack:** 3-hit melee flurry (objAtk frames 45,52,61)
- **Skill:** 6-strike combo alternating main/nearby; taunt(100) every 3rd use
- **On-kill:** +200% move speed for 60t (base AND evolved)

**In-game text**
- Normal: "Unleashes a rapid flurry of melee hits on enemies."
- Skill: "Launches a combo attack that alternates between the main target and nearby enemies. Taunt triggers after a certain number of uses."
- Normal (Ⅱ): "Strikes with rapid melee combos. Killing an enemy grants a movement speed buff."
- Skill (Ⅱ): "Delivers an enhanced combo attack alternating between the main target and nearby enemies. Activates Taunt after a set number of uses."

**Normal attack**
- 3-hit combo (objAtk frames 45,52,61).

**Skill — alternating combo**
- objSkill 6 frames {100,104,108,112,116,120}: `onSkillStartFrame` increments `skillUseCount`; every 3rd use ⇒ `taunt(100)`.
- Per hit-frame: hits #1 and #6 hit the main target (`doMeleeAttack(target, comboMult)`); the rest hit a nearby enemy (`attackNearbyEnemy`, radius 40) — alternating main/nearby.
- comboMult = 1 base / 1.2 Ⅱ.

**Passive / special**
- `onKillEnemy` (unconditional, base + evolved): `addMoveSpeedBuff(kindNum, 2, 60)` — +200% move speed for 60t on every kill.

**Buffs & debuffs**
- SELF: `addMoveSpeedBuff(kindNum, 2, 60)` on each kill (+200% move, 60t). Buff id = kindNum ⇒ self-stacks as max, refreshes uptime.
- Enemy `taunt(100)` every 3rd skill cast.

**Base → Ⅱ**
- Combo mult 1 → 1.2. (On-kill move buff is present in base code too — see ⚠️.)

**Key values**
| | base | Ⅱ |
|---|---|---|
| combo dmg mult | 1 | 1.2 |
| onKill move buff value | 2 (+200%) | 2 |
| onKill buff dur | 60t | 60t |
| taunt cadence | every 3rd use (`skillUseCount%3==0`) | same |
| taunt duration | 100t | 100t |
| nearby-search radius | 40 | 40 |
| objAtk (normal) | {45,52,61} | {45,52,61} |
| objSkill | {100,104,108,112,116,120} | same |

**Formulas**
- Kill move buff: `moveSpd = orgMoveSpd*(1+2)` ⇒ ×3 for 60 ticks.

**⚠️ Description vs code**
- Combo alternation and "taunt after N uses" (every 3rd) both match. DELTA: the kill→move-speed buff is in the BASE class too (`onKillEnemy` is unconditional), but the locale documents it only on the evolved normal text (UNIT_NATK_31). So base Mounted Knight ALSO gets the +200% move-speed-on-kill its base description (UNIT_NATK_6) omits.

---

### Elf Archer — `ElfArcher1` (kindNum: 7 · Ⅱ 32)
**TL;DR.** Basic 8-direction archer; its skill fires a 3-arrow volley that can hit up to 3 enemies at once.

**At a glance**
- **Role:** Ranged DPS (3-arrow volley skill)
- **Attack:** `numShot=1.3` → avg 1.3 `NormalArrow` per basic
- **Skill:** `numShot=3` → 3 simultaneous arrows
- **No evolved code branch** (Ⅱ differs via book stats only)

**In-game text**
- Normal: "Fires arrows to attack enemies from range."
- Skill: "Fires 3 arrows at once, hitting up to 3 enemies simultaneously."

**Normal attack**
- 8-direction archer: `gotoAttackState` picks one of 5 directional frame sets + firepoints by angle to target.
- `attackMain` sets `numShot=1.3` and calls base multishot (fires `NormalArrow`; fractional 1.3 yields an occasional extra arrow).

**Skill — 3-arrow volley**
- `skillMain` sets `numShot=3` → 3 simultaneous arrows, hitting up to 3 enemies.

**Key values**
| variable | value | meaning |
|---|---|---|
| numShot (basic) | 1.3 | arrows per basic (fractional → avg 1.3) |
| numShot (skill) | 3 | arrows in skill volley |
| multiShotDelay | 3 | frame delay between multishot arrows |
| weaponClass | NormalArrow | `PhysicalHitEffect`, g=.1, speed=10 |
| normalSize / evolSize | .95 / 1.03 | sprite scale |

**Formulas**
- Fractional numShot → `floor + chance(frac)` extra arrow (base-class multishot).

**✓ Matches description** — "3 arrows / up to 3 enemies" = `numShot=3`. Evolved (32) shares identical mechanics; the evolution difference is via book stats, not code branches.

**Notes**
- Same 8-direction frame/firepoint scaffold as the HighArcher1/PoisonArcher1 archer family. Basic `numShot` is always 1.3.

---

### Elf Warrior — `ElfWarrior1` (kindNum: 8 · Ⅱ 33)
**TL;DR.** Plain melee soldier that lands a double-hit basic and a triple-hit skill combo at 1.5× power.

**At a glance**
- **Role:** Melee DPS (double-hit + triple-hit combo skill)
- **Attack:** 2 hit-frames `{54,60}` → double hit
- **Skill:** 3 hit-frames `{54,60,62}` + `doMeleeAttack(target, 1.5)` → triple-hit at 1.5×
- **No evolved code branch** (Ⅱ differs via book stats only)

**In-game text**
- Normal: "Strikes enemies with a melee double hit."
- Skill: "Unleashes a triple-hit combo with 1.5x power, dealing heavy melee damage."

**Normal attack**
- Lands on `objAtk={54,60}` → two hits (double hit).

**Skill — triple-hit combo**
- `skillMain` does a single `doMeleeAttack(target, 1.5)`, but the skill anim reuses `objSkill={54,60,62}` (three hit-frames) → triple-hit at 1.5× power. Skill frames `== `attack frames `QK(44,73)`.

**Key values**
| variable | value | meaning |
|---|---|---|
| objAtk | {54,60} | basic double-hit frames |
| objSkill | {54,60,62} | skill triple-hit frames |
| skill power | 1.5 | `doMeleeAttack(target,1.5)` multiplier |

**✓ Matches description** — double-hit (2 objAtk frames) and triple-hit-at-1.5× (3 objSkill frames + 1.5 multiplier) confirmed.

**Notes**
- No `setData`/evolved branch — evolution (33) differs only via book stats.

---

### Poison Archer — `PoisonArcher1` (kindNum: 9 · Ⅱ 34)
**TL;DR.** Ranged archer whose arrows slow move + attack speed; the skill is a 1.5× poison arrow that creates a slowing cloud over nearby enemies.

**At a glance**
- **Role:** Ranged DPS + debuffer (poison/slow)
- **Attack:** `PoisonArcherArrow1` → 50t slow on hit (move + attack speed)
- **Skill:** 1.5× poison arrow; main target 50t (Ⅱ 70t) + cloud poisons ≤4 (Ⅱ ≤6) nearby for 20t (Ⅱ 30t)
- **Single-direction archer**, single hit-frame each

**In-game text**
- Normal: "Fires a poison arrow that reduces enemies' movement speed and attack speed."
- Skill: "Fires a 1.5x power poison arrow that creates a poison cloud and slows nearby enemies."

**Normal attack**
- Fires `PoisonArcherArrow1`; `onHitMain` calls `target.poison(50)` — 50-tick slow status reducing move + attack speed.

**Skill — poison cloud (1.5×)**
- `skillMain` fires `PoisonArcherArrowSkill1` via `generateWeapon(target, …, 1.5)` (1.5× power).
- On hit: poisons the main target for 50t (Ⅱ 70t), then `getEnemiesAtPos` collects nearby enemies within radius 50 (Ⅱ 60) and poisons ≤4 (Ⅱ ≤6) of them for 20t (Ⅱ 30t) each (the "poison cloud").

**Buffs & debuffs**
- Poison/slow on enemies: 50t (basic); 50t main + 20t cloud (skill); Ⅱ 70t main + 30t cloud. Reduces move & attack speed for the duration.

**Base → Ⅱ**
- Skill main poison 50t → 70t; cloud radius 50 → 60; cloud max targets 4 → 6; cloud poison 20t → 30t.

**Key values**
| | base | Ⅱ |
|---|---|---|
| basic poison | poison(50) | poison(50) |
| skill power | 1.5 | 1.5 |
| skill main poison | 50t | 70t |
| skill cloud radius | 50 | 60 |
| skill cloud max targets | 4 | 6 |
| skill cloud poison | 20t | 30t |

**Formulas**
- `poison(t)` sets `numSlow = max(numSlow, t)` (status flag, consumed ~0.5/tick), blocked by `numLoveShield`. The move + attack-speed reduction is applied through the status system while `numSlow>0`.

**✓ Matches description** — "1.5x power poison arrow + poison cloud + slows nearby" = the 1.5 multiplier + the `getEnemiesAtPos` AoE poison on ≤4/6 enemies. Evolved scales durations, radius (50→60), and target count (4→6).

**Notes**
- `objAtk={50:1}`, `objSkill={50:1}` (single hit each); `hitClassName="PhysicalHitEffect"`. "Reduces movement and attack speed" is the generic `poison()`/`numSlow` status, not a stat-buff call.

---

### High Elf Archer — `HighArcher1` (kindNum: 10 · Ⅱ 35)
**TL;DR.** Faster-firing magic archer (uses SpeedArrow); the only archer in its family whose evolution actually bumps shot counts in code.

**At a glance**
- **Role:** Ranged DPS (rapid magic-arrow volleys)
- **Attack:** `numShot=1.3` → 1.8 evolved, using faster `SpeedArrow`
- **Skill:** `numShot=3` → 4 evolved
- **Evolution-aware in code** (real `evolved` branch on numShot)

**In-game text**
- Normal: "Attacks enemies from range with precise magic arrows." (Ⅱ: "…at an increased fire rate…")
- Skill: "Rapidly fires magic arrows to hit multiple enemies at once." (Ⅱ: "Fires a rapid volley…")

**Normal attack**
- Same 8-direction frame/firepoint system as ElfArcher1, but `weaponClass=SpeedArrow` (faster projectile).
- `attackMain`: `numShot = evolved ? 1.8 : 1.3`.

**Skill — rapid volley**
- `skillMain`: `numShot = evolved ? 4 : 3`.

**Base → Ⅱ**
- Basic numShot 1.3 → 1.8; skill numShot 3 → 4 ("increased fire rate" / "rapid volley").

**Key values**
| | base | Ⅱ |
|---|---|---|
| numShot (basic) | 1.3 | 1.8 |
| numShot (skill) | 3 | 4 |
| multiShotDelay | 3 | 3 |
| weaponClass | SpeedArrow | SpeedArrow |

**Formulas**
- Fractional numShot → extra-arrow chance.

**✓ Matches description** — "increased fire rate" / "rapid volley" reflects the evolved numShot bump (1.3→1.8 basic, 3→4 skill) plus the SpeedArrow weapon.

**Notes**
- The ONLY archer in this family with a real `evolved` code branch on numShot. `dieFrames=QK(190,221)`, directional firepoints `(30,-20)/(24,-37)/(0,-54)/(18,-3)/(6,12)`.

---

### Green Eagle — `GreenEagle1` (kindNum: 11 · Ⅱ 36)
**TL;DR.** Flying ranged attacker whose every projectile (basic and skill) knocks enemies back and has a 50% chance to slow them; the skill fires a 3-shot wind burst.

**At a glance**
- **Role:** Ranged DPS (air unit) with knockback skill
- **Attack:** 1 `GreenEagleBall1` (skill: 3 consecutive)
- **Every hit:** knockback (scale 2, 15t) + 50% poison(40) slow
- **No evolved code branch** (Ⅱ differs via book stats only)

**In-game text**
- Normal: "Soars through the sky and fires ranged projectiles at enemies."
- Skill: "Launches 3 consecutive wind attacks, dealing damage and knocking enemies back."

**Normal attack**
- Air unit (`isAir`, `airHeight=75`). `attackMain`: `numShot=1` → single `GreenEagleBall1`.

**Skill — 3 wind shots**
- `skillMain`: `numShot=3` → three consecutive balls.

**Passive / special (on every ball, basic + skill)**
- Knockback along travel direction: `knockBack(2·vx/s, 2·vy/s, 15)`.
- 50% chance to `poison(40)` (40-tick slow).

**Buffs & debuffs**
- Knockback (every hit) + 50% poison(40) slow on enemies.

**Key values**
| variable | value | meaning |
|---|---|---|
| numShot (basic / skill) | 1 / 3 | balls per basic / skill |
| ball knockback | scale 2, dur 15t | per-hit push magnitude/duration |
| ball poison chance / dur | 0.5 / poison(40) | 50% to apply 40-tick slow |
| multiShotDelay | 3 | inter-shot frame delay |
| airHeight | 75 | flight height |
| normalSize / evolSize | 1.15 / 1.25 | sprite scale |

**Formulas**
- Knockback velocity = `2 × (vx,vy)/|v|` (normalized projectile direction ×2).

**⚠️ Description vs code**
- **Undocumented poison.** The text covers "3 wind attacks + knockback" but omits the **50% chance to poison/slow (40 ticks)** that every projectile (basic AND skill) carries via `GreenEagleBall1.onHitMain`. Knockback also applies on every hit, not just the skill. Verified: `random.chance(.5)&&this.target.poison(40)` is on the shared weapon, so it fires on normal attacks too.

**Notes**
- `weaponClass=GreenEagleBall1`; `objAtk=objSkill={50:1}` (skill reuses attack frames). No evolved code branch (36 differs via book stats).

---

### Wind Mage — `WindMage1` (kindNum: 12 · Ⅱ 37)
**TL;DR.** Ranged mage that throws energy balls and, on skill, summons tornadoes on multiple enemies that deal sustained damage — more and longer-lasting when evolved.

**At a glance**
- **Role:** Mage / ranged AoE (multi-target tornado skill)
- **Attack:** `GreenEnergyBall` with `numShot=1.5` (Ⅱ 2.5)
- **Skill:** spawns 2 tornadoes (Ⅱ 4) on target + nearest enemies ≤200
- **Tornado:** whirls 70t (Ⅱ 100t); roots the target (`binding(12)` re-applied every 10t) + 0.3× damage every 30t

**In-game text**
- Normal: "Launches an energy ball to attack enemies from range."
- Skill: "Summons a tornado at the enemy's location, dealing sustained damage." (Ⅱ: "Summons a tornado for longer, hitting more enemies and dealing sustained damage.")

**Normal attack**
- Fires `GreenEnergyBall` with `numShot = 1.5` (Ⅱ 2.5).

**Skill — tornadoes**
- `skillMain` picks `t = 2·evolStage+2` targets → 2 base, 4 evolved: the locked target plus nearest enemies within 200.
- Spawns a `Twist` (tornado) on each via `spawnTwist`, each whirling for 70t (Ⅱ 100t). The tornado **pins the target to its position**, re-applies `binding(12)` (root) every 10t, and deals `0.3×` damage every 30t — a hard root, not just DoT.

**Base → Ⅱ**
- Basic numShot 1.5 → 2.5; skill targets 2 → 4; tornado whirl 70t → 100t ("for longer, hitting more enemies").

**Key values**
| | base | Ⅱ |
|---|---|---|
| numShot (basic) | 1.5 | 2.5 |
| skill target count | 2 (`2·0+2`) | 4 (`2·1+2`) |
| skill gather range | 200 | 200 |
| tornado whirl dur | 70t | 100t |
| Twist dmg (every 30t) | 0.3× | 0.3× |
| Twist root | `binding(12)` / 10t | same |

**Formulas**
- Evolved skill targets `2·1+2 = 4` vs base `2·0+2 = 2`.

**✓ Matches description** — "for longer, hitting more enemies" = whirl 70→100 and targets 2→4 when evolved. (`OBJ_ATK` `{57:1}` and `OBJ_SKL` `{101:1}` frame sets identical base/evolved; only counts/durations differ.)

**Notes**
- `weaponClass=GreenEnergyBall` (`MagicalHitEffect`, speed 9). Tornado is weapon class `Twist`, spawned procedurally; drifts toward target then whirls in place. **Twist is a hard root, not just DoT:** it re-binds the target (`binding(12)`) every 10t and drags it to the tornado's position, dealing 0.3× damage every 30t. (The in-game blurb only says "sustained damage" — the root is undocumented.)

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

### Dark Sorcerer / Dark Sorcerer Ⅱ — `DarkMage1` (kindNum: 18 · Ⅱ 43)
**TL;DR.** A multi-role caster that fires dark projectiles, periodically summons skeletons, and on cast curses enemies (50% to miss their own attacks) + shields allies — and can resurrect slain low-grade enemies to fight for you.

**At a glance**
- **Role:** Ranged DPS + summoner / support
- **Attack:** fires `DarkMageBall1`; numShot 1.5 → **2.5** at Ⅱ
- **Skill:** curse ≤3 (Ⅱ ≤4) enemies (each then has a **50% chance to miss every attack** for ~3s) + shield 1 (Ⅱ 2) allies + summon a skeleton
- **Passive summon:** a Skeleton Soldier (kind 13) every 1000t
- **Revive passive:** on kill of a grade≤2 enemy, energy-gated chance to resurrect it as an ally

**In-game text**
- Normal: "Fires dark projectiles from a distance and periodically summons skeleton soldiers." (Ⅱ: "Fires dark projectiles at an increased fire rate. Periodically summons a skeleton soldier.")
- Skill: "Curses enemies, grants a shield to allies, and summons skeletons." (Ⅱ: "Curses more enemies, shields more allies, and summons skeletons to fight at your side.")

**Normal attack**
- Fires `DarkMageBall1`; `numShot = 1.5` base (1 guaranteed extra + 50% for a 2nd) / **2.5** evolved (2 extra + 50% for a 3rd).

**Skill — curse + shield + summon (`skillMain`)**
- (1) `getAttackableEnemyList(i)` with `i=3` base / **4** evolved; fires `DarkMageSkillBall1` (mult 1.5) at the **first** enemy, and `curse(180)` on **every** enemy in the list. **Curse = a 50% chance to miss on each of the cursed unit's own attacks** (shows a "Miss"), for 180 ticks (~3s) — effectively halving the cursed enemies' damage output.
- (2) Shields `s` random alive allies (`s=1` base / **2** evolved) via `showPowerShield(120)`.
- (3) Calls `trySummonSkeleton()`.

**Passive / special**
- **Passive summon:** every `SUMMON_COOLDOWN=1000` ticks, summons a skeleton (`SKELETON_KIND_NUM=13`) for 1000t base / **1300t** evolved, tinted `16746632`.
- **Revive on kill** (`onKillEnemy`): if the killed enemy is `grade≤2`, not air, not summoned, and `reviveEnergy ≥ REVIVE_ENERGY` (350 base / **220** evolved), then with chance 0.1 base / **0.2** evolved, resurrects a copy as an ally (`summonUnitSync(reviveVO, REVIVE_DURATION=600, 0)`, at the corpse, `revive()`, `initDelay=8`). `reviveEnergy` increments +1/tick and resets to 0 on a successful revive.

**Buffs & debuffs**
- Curse (**50% chance to miss each attack** while active): 180t (~3s), on ≤3 (Ⅱ ≤4) enemies (the whole attackable list) — skill.
- Shield: `showPowerShield`, 120t, on 1 (Ⅱ 2) random allies — skill.

**Base → Ⅱ**
- numShot 1.5 → 2.5; curse targets 3 → 4; shield count 1 → 2; summon duration 1000 → 1300; revive energy 350 → 220; revive chance 0.1 → 0.2.

**Key values**
| | base | Ⅱ |
|---|---|---|
| numShot | 1.5 | 2.5 |
| skill curse targets | 3 | 4 |
| curse — 50% attack-miss | 180t (~3s) | 180t |
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

### Orc Fighter — `OrcFighter1` (kindNum: 19 · Ⅱ 44)
**TL;DR.** Melee bruiser that hits twice per swing; its skill is a heavy blow that knocks the target backward.

**At a glance**
- **Role:** Melee DPS
- **Attack:** melee double-hit (two hit-frames per swing)
- **Skill:** heavy strike + knockback
- **Stats:** 150 HP, ATK 3, DEF 10, moveSpd 2.6, atkDuration 200, melee range 8

**In-game text**
- Normal: "Attacks enemies with a rapid double melee strike." (Ⅱ: "Attacks enemies with a melee double-hit.")
- Skill: "Delivers a heavy strike that deals massive damage and knocks enemies back." (Ⅱ: "Strikes with tremendous force, dealing even greater damage and sending enemies flying farther back.")

**Normal attack**
- Double-hit: `objAtk={51:1,60:1}` fires the hit on two anim frames (51 and 60), each at 1×.

**Skill — heavy strike + knockback**
- `doMeleeAttack(target, ×2)` (**Ⅱ ×2.5**) on frames `objSkill={97:1,105:1}`.
- Then `target.blow(±k, k)` with `k = 2` (**Ⅱ 3**); sign is `+` if target is to the right, `−` if left.
- Evolved gated by `this.evolStage>=1` inside `skillMain` (no cached flag).

**Base → Ⅱ**
- Skill damage ×2 → ×2.5; knockback k 2 → 3 ("flying farther back").

**Key values**
| | base | Ⅱ |
|---|---|---|
| skill damage mult | ×2 | ×2.5 |
| knockback k | 2 | 3 |
| baseMaxHp | 150 | 150 |
| atkDmg / def | 3 / 10 | 3 / 10 |
| moveSpd | 2.6 | 2.6 |
| atkDuration | 200 | 200 |
| atkRange | 8 | 8 |

**Formulas**
- Skill dmg = atk × 2 (base) / × 2.5 (Ⅱ). Normal = 2× `objAtk` frames at 1× each.

**✓ Matches description** — double-hit normal + heavy-damage knockback skill; evolved raises mult (2→2.5) and knockback (2→3).

---

### Orc Hunter — `OrcHunter1` (kindNum: 20 · Ⅱ 45)
**TL;DR.** Melee assassin that teleports to the farthest forward enemy, hits hard, freezes it, and buffs its own dodge against ranged attacks.

**At a glance**
- **Role:** Melee assassin (teleport + freeze + self-evade)
- **Attack:** plain melee strike
- **Skill:** teleport to farthest forward enemy → heavy hit → freeze → self ranged-evade buff
- **Stats:** 150 HP, ATK 3, DEF 10, moveSpd 2.6, atkDuration 200, melee range 8

**In-game text**
- Normal: "Attacks enemies with a melee strike." (Ⅱ: "Attacks enemies with a basic melee strike.")
- Skill: "Teleports to the farthest enemy, delivers a heavy strike, freezes the target, and grants itself a ranged evasion buff." (Ⅱ: "Teleports to the farthest enemy, delivering a more powerful strike and freezing them for longer. Grants yourself a ranged evasion buff.")

**Skill — teleport strike (`objSkill={103:1}`)**
- Scans `enemyList` for the ground, non-air, targetable enemy with the **largest +x offset** (farthest ahead) within |dx|≤200, |dy|≤200 AND dx²+dy²<40000.
- Teleports beside it (snaps `this.x` to `target.x ∓ hitWidths`), then `doDamage(target, ×2)` (**Ⅱ ×3**).
- `target.freeze(30)` (**Ⅱ 50**).
- Self-buffs `addRangeEvadeChanceBuff(id=1, 0.6, 180)` + the `OrcHunterEvadeBuff` visual for 180t.

**Buffs & debuffs**
- Self ranged-evade: +60% (value 0.6, additive), 180t (~3s) — id 1
- Target freeze: 30t (**Ⅱ 50t**)

**Base → Ⅱ**
- Skill dmg ×2 → ×3; freeze 30t → 50t.

**Key values**
| | base | Ⅱ |
|---|---|---|
| skill damage mult | ×2 | ×3 |
| freeze duration | 30t | 50t |
| rangeEvade value | 0.6 (+60%) | 0.6 |
| rangeEvade duration | 180t (~3s) | 180t |
| search box | |dx|,|dy|≤200; dist²<40000 | same |
| baseMaxHp / atkDmg / def | 150 / 3 / 10 | same |
| moveSpd / atkDuration / atkRange | 2.6 / 200 / 8 | same |

**Formulas**
- `rangeEvadeChange = orgRangeEvadeChange + 0.6` (additive ⇒ +60% chance to dodge ranged hits) for 180t. Skill dmg = atk × 2 / × 3.

**✓ Matches description** — evolved bumps dmg (2→3) and freeze (30→50). Note "farthest enemy" is implemented as farthest **in +x (forward) direction within a 200/√40000 box**, not globally farthest.

---

### Frost Mage / Ice Mage Ⅱ — `OrcIceMage1` (kindNum: 21 · Ⅱ 46)
**TL;DR.** Ranged ice mage; evolved fires faster with a chance for an extra projectile, and its freeze-bolt skill can hit a second enemy.

**At a glance**
- **Role:** Ranged mage (ice)
- **Attack:** fires `OrcIceMageFire1` ice projectiles
- **Skill:** enhanced freeze bolt (`OrcIceMageFireSkill1`); **Ⅱ** adds a 50%-chance second bolt
- **Ⅱ normal:** numShot 1 → 1.3 (~30% chance of an extra projectile)

**In-game text**
- Normal: "Fires ice magic projectiles to attack enemies from a distance." (Ⅱ: "Fires enhanced ice magic projectiles at an increased fire rate, with a chance to strike additional targets.")
- Skill: "Fires enhanced freezing projectiles that deal massive damage to enemies." (Ⅱ: "Fires an enhanced freezing projectile that deals heavy damage to enemies.")

**Normal attack**
- Ranged (`unitType=RANGE`, `weaponClass=OrcIceMageFire1`), fires on `objAtk={42:1}`.
- `setData` sets `numShot = 1` (**Ⅱ 1.3**) — the fractional count means ~30% chance of an extra projectile per attack, resolved by base shot logic.

**Skill — freeze bolt (`objSkill={68:1}`)**
- Fires the enhanced `OrcIceMageFireSkill1` at the target.
- **Ⅱ only:** scans `getAttackableEnemyList(2)` and, for the first non-target enemy, fires a second skill projectile with `random.chance(.5)` (50%).

**Base → Ⅱ**
- numShot 1 → 1.3; skill gains a 50%-chance second freeze bolt at the nearest other enemy.

**Key values**
| | base | Ⅱ |
|---|---|---|
| numShot | 1 | 1.3 (~30% extra) |
| evolved 2nd-skill chance | — | 0.5 |
| objAtk / objSkill frame | 42 / 68 | 42 / 68 |
| weaponClass (normal) | OrcIceMageFire1 | same |
| weaponClass (skill) | OrcIceMageFireSkill1 | same |

**Formulas**
- Evolved extra-shot expectation ≈ 0.3 projectiles/attack (numShot 1.3). Evolved skill expected bolts = 1 + 0.5 = 1.5.

**Notes**
- Freeze/CC is carried by the `OrcIceMage...` weapon objects, not this class — no buff/debuff applied directly here.

**✓ Matches description** — "increased fire rate / additional targets" = numShot 1→1.3; evolved skill's "additional" bolt = one 50%-chance second projectile at the nearest other enemy.

---

### Orc Wing — `OrcWing1` (kindNum: 22 · Ⅱ 47)
**TL;DR.** Airborne ranged attacker that fires energy balls; its skill is the same projectile cranked up to a higher power level.

**At a glance**
- **Role:** Ranged DPS (flyer)
- **Attack:** fires `OrcWingBall1` energy balls from the air (`airHeight=75`)
- **Skill:** same projectile at power level 2 (enhanced damage)
- **Evolved difference:** render size only (0.85 → 0.95)

**In-game text**
- Normal: "Fires energy projectiles from the air to attack enemies at range." (Ⅱ: "Fires energy projectiles from the air for ranged attacks.")
- Skill: "Fires enhanced energy projectiles that deal massive damage." (Ⅱ: "Fires an enhanced energy projectile that deals heavy damage.")

**Normal attack**
- Air unit (`isAir=true`, `airHeight=75`), ranged, `weaponClass=OrcWingBall1`, hit on `objAtk={59:1}`, `firePoint=(18, 5−75)`.

**Skill — enhanced energy ball (`objSkill={97:1}`)**
- `generateWeapon(target, OrcWingBall1, 2)` — same projectile, 3rd arg `2` boosts power/damage. One enhanced ball.

**Base → Ⅱ**
- `normalSize` 0.85 → `evolSize` 0.95 (render scale only); skill is mechanically identical base/Ⅱ.

**Key values**
| | base | Ⅱ |
|---|---|---|
| skill power arg | 2 | 2 |
| objAtk / objSkill frame | 59 / 97 | 59 / 97 |
| airHeight | 75 | 75 |
| firePoint | (18, 5−75) | same |
| weaponClass | OrcWingBall1 | same |
| render scale | 0.85 | 0.95 |

**Formulas**
- Skill projectile = normal `OrcWingBall1` at power level 2 (exact multiplier lives in the weapon class).

**✓ Matches description** — skill is the same projectile at power 2; no mechanical base/evolved difference beyond size.

---

### Orc Axeman — `OrcAxe1` (kindNum: 23 · Ⅱ 48)
**TL;DR.** Melee axe fighter with a forward cleave on its normal hit, and a skill that throws axes to hit multiple extra enemies — including airborne ones.

**At a glance**
- **Role:** Melee DPS (forward AoE + thrown axes)
- **Attack:** melee hit + forward AoE cleave (up to 2 → **3** ground enemies)
- **Skill:** melee hit + throw 3 → **5** axes (`OrcAxeBall1`), can hit air
- **Evolved:** wider AoE box (30→35) and stronger secondary hits (0.5→0.7)

**In-game text**
- Normal: "Strikes with an axe in melee and deals AoE damage to enemies ahead." (Ⅱ: "Strikes with an axe in melee, dealing wider AoE damage to enemies ahead.")
- Skill: "After a melee attack, throws an axe to strike additional enemies. Can also hit airborne enemies." (Ⅱ: "After a melee attack, hurls more axes to strike additional enemies. Can also hit airborne targets.")

**Normal attack**
- `doMeleeAttack(target, 1)` on `objAtk={78:1}`, then a forward AoE sweep.
- Box centered `direction*range` ahead (`range = 30`, **Ⅱ 35**; radius² = range²), hitting up to 2 (**Ⅱ 3**) extra **ground** enemies at `doMeleeAttack(a, 0.5)` (**Ⅱ 0.7**). Explicitly skips `a.isAir`.

**Skill — axe throw (`objSkill={133:1,135:1,137:1}`, three throw frames)**
- First a melee hit on the target, then `getAttackableEnemyList(t+1, false)` (the `false` allows **air** targets).
- Throws `OrcAxeBall1` at up to `t = 3` (**Ⅱ 5**) non-target enemies via `generateWeapon`.

**Base → Ⅱ**
- Normal AoE range/radius 30→35, targets 2→3, mult 0.5→0.7; skill throws 3→5.

**Key values**
| | base | Ⅱ |
|---|---|---|
| normal AoE range / radius | 30 / 30 | 35 / 35 |
| normal AoE maxTargets | 2 | 3 |
| normal AoE damage mult | 0.5 | 0.7 |
| skill throws | 3 | 5 |
| objAtk frame | 78 | 78 |
| skill target query | `getAttackableEnemyList(t+1,false)` (incl. air) | same |

**Formulas**
- Normal forward AoE dmg = atk × 0.5 (base) / × 0.7 (Ⅱ), up to 2/3 extra ground targets. Skill = 1 melee + N thrown axes (3/5).

**✓ Matches description** — "wider AoE" (Ⅱ) = range/radius 30→35, targets 2→3, mult 0.5→0.7. "Hit airborne enemies" = skill's `getAttackableEnemyList(...,false)` includes air units (normal AoE skips air).

---

### Orc Hammerman — `OrcHammer1` (kindNum: 24 · Ⅱ 49)
**TL;DR.** Melee hammer unit whose skill summons a short-lived ice decoy to soak hits; evolved adds a small forward AoE to its normal swing.

**At a glance**
- **Role:** Melee DPS / summoner (decoy)
- **Attack:** melee hammer; **Ⅱ** adds a 1-target forward AoE
- **Skill:** summons an `OrcIcePhantom1` ice decoy (aggro magnet, no attack)
- **Decoy lifetime:** 180t (~3.0s) → **220t (~3.7s)** at Ⅱ

**In-game text**
- Normal: "Attacks enemies in melee with a hammer." (Ⅱ: "Swings a hammer to deal AoE damage to nearby enemies.")
- Skill: "Summons an ice decoy to draw enemy attacks in your place." (Ⅱ: "Summons an ice clone for a longer duration to take hits in your place.")

**Normal attack**
- Base: `doMeleeAttack(target, 1)` on `objAtk={58:1}`.
- **Ⅱ only:** also sweeps for up to **1** extra ground enemy in a 30-unit box centered 30 units ahead (`n = x + direction*30`, radius² = 30² = 900) and hits it with `doMeleeAttack(a, 0.7)` — this is the evolved "AoE".

**Skill — summon ice decoy**
- `summonPhantom(dur)` spawns `OrcIcePhantom1` via `getUnitSync` on frame `objSkill={99:1}`.
- Copies source VO at 0.3 scale (`setData(sourceVo, .3)`), placed at a random angle 40 units away.
- `summonDuration = 180` (**Ⅱ 220**). Phantom just stands and `die()`s when its `summonTimer` hits 0 — draws aggro, never attacks.

**Passive / special**
- Caches `this.sourceVo` in `setData` to clone into the phantom; `this.evolved = this.evolStage>=1`.

**Base → Ⅱ**
- Normal gains a 1-target forward AoE at 0.7×; phantom duration 180t → 220t.

**Key values**
| | base | Ⅱ |
|---|---|---|
| evolved AoE range / radius | — | 30 / 30 (radius²=900) |
| evolved AoE maxTargets | — | 1 |
| evolved AoE damage mult | — | 0.7 |
| phantom duration | 180t (~3.0s) | 220t (~3.7s) |
| phantom setData scale | 0.3 | 0.3 |
| phantom spawn radius | 40 | 40 |
| objAtk / objSkill frame | 58 / 99 | 58 / 99 |

**Formulas**
- Evolved secondary hit dmg = atk × 0.7.

**✓ Matches description** — evolved "AoE normal" = exactly one extra forward ground hit at 0.7×; evolved decoy lasts longer (180→220t). The decoy only soaks aggro then expires; it never attacks.

---

### Wolf Rider — `OrcWolfRider1` (kindNum: 25 · Ⅱ 50)
**TL;DR.** Hybrid melee/summoner/buffer — cleaves nearby enemies, summons ice wolves, periodically taunts, and grants nearby allies an attack/move-speed buff.

**At a glance**
- **Role:** Summoner + melee DPS + buffer
- **Attack:** melee hit + forward AoE (up to 4 → **6** enemies)
- **Skill:** summon Ice Wolf (max 2 → **3**) + ally speed buff; taunt every 3rd use
- **Ally buff:** +25% atk/move-speed → **+40%** (radius 70 → **90**)

**In-game text**
- Normal: "Deals AoE damage to nearby enemies along with a melee attack." (Ⅱ: same.)
- Skill: "Summons a wolf and grants nearby allies a movement speed and attack speed buff. Activates Taunt after a set number of uses." (Ⅱ: "Increases the number of wolves that can be summoned and strengthens the movement speed and attack speed buffs granted to nearby allies. Activates Taunt after a set number of uses.")

**Normal attack**
- `doMeleeAttack(target)` then a forward AoE — box centered `i` units ahead (`i = 40`, **Ⅱ 50**; radius² = i²) hitting up to `e = 4` (**Ⅱ 6**) other enemies at `doDamage(o, 0.65)` (**Ⅱ 0.8**).

**Skill — summon + buff (`objSkill={58:1}`)**
- Increments `skillUseCount`; if current wolf count < `MAX_WOLVES` (2, **Ⅱ 3**), summons `WOLF_KIND_NUM=1003` ("Ice Wolf") via `summonUnitSync`, duration `WOLF_DURATION` (1200, **Ⅱ 1500**), wolf level = `level + enhance + WOLF_LEVEL_BONUS` (6, **Ⅱ 10**), scale `WOLF_SCALE` (1.05, **Ⅱ 1.15**), with `detectRange` set.
- **Every 3rd use** (`skillUseCount%3==0`): `taunt(80)` (80-tick taunt; fires on uses 3, 6, 9…).
- Then `buffNearbyAllies()`.

**Buffs & debuffs**
- Ally atk-speed: +25% (Ⅱ +40%, value 0.25/0.4), 100t (Ⅱ 120t), allies within radius 70 (Ⅱ 90) — id = kindNum (25/50)
- Ally move-speed: +25% (Ⅱ +40%), 100t (Ⅱ 120t), same radius — id = kindNum (25/50)
- Taunt: 80t, every 3rd skill use

**Passive / special**
- `setData` rolls starting mana `250 + 150·random`.
- When `battleController instanceof mii` (hero/own-side context) the wolf gets a smaller `detectRange` (150) and, if on the friendly hero list, full hero treatment (`applyToHero`, hp=maxHp).

**Base → Ⅱ**
- Wolves: max 2→3, duration 1200→1500, level bonus 6→10, scale 1.05→1.15. Normal AoE: range 40→50, targets 4→6, mult 0.65→0.8. Ally buff: value 0.25→0.4, radius 70→90, duration 100→120.

**Key values**
| | base | Ⅱ |
|---|---|---|
| WOLF_KIND_NUM | 1003 (Ice Wolf) | 1003 |
| WOLF_DURATION | 1200t | 1500t |
| MAX_WOLVES | 2 | 3 |
| WOLF_SCALE | 1.05 | 1.15 |
| WOLF_LEVEL_BONUS | 6 | 10 |
| normal AoE range i | 40 | 50 |
| normal AoE maxTargets e | 4 | 6 |
| normal AoE damage mult | 0.65 | 0.8 |
| ally-buff radius | 70 | 90 |
| ally-buff value s | 0.25 (+25%) | 0.4 (+40%) |
| ally-buff duration e | 100t | 120t |
| taunt | every 3rd skill, `taunt(80)` | same |
| starting mana | 250 + 150·rand | same |

**Formulas**
- Ally `atkSpd = orgAtkSpd × (1+0.25)` ⇒ +25% / `×(1+0.4)` ⇒ +40%; same for moveSpd. Normal AoE dmg = atk × 0.65 / × 0.8.
- Both ally buffs keyed by `this.kindNum` (25/50) ⇒ same kindNum doesn't stack, max kept.

**✓ Matches description** — "increases number of wolves" = MAX_WOLVES 2→3 + longer duration; "strengthens buffs" = value/radius/duration up plus stronger wolves (level +6→+10, scale 1.05→1.15). Summoned "wolf" is internally kindNum 1003 = "Ice Wolf".

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

### Fairy — `Fairy1` (kindNum: 53 · Ⅱ 54)
**TL;DR.** Flying support healer that pelts enemies with note bullets and, on skill, heals + restores mana to nearby allies while granting them a move-speed buff.

**At a glance**
- **Role:** Support/healer (air) — HP/mana restore + move-speed buff
- **Attack:** `FairyMusicNote` bullets, `numShot=1.5` (Ⅱ 2)
- **Skill targets:** ≤20 nearest allies within radius 350 (self excluded)
- **Heal:** 6 HP (Ⅱ 12) + 5 mana (Ⅱ 10) per ally; castles get reduced heal, no mana/buff
- **Buff:** +25% move speed (Ⅱ +35%) for 100t (Ⅱ 150t)

**In-game text**
- Normal: "Soars through the sky and attacks from range with music-note bullets."
- Skill: "Grants nearby allies a buff that restores HP and mana, and increases movement speed." (Ⅱ: "Restores more HP and mana to nearby allies, with a stronger movement speed boost.")

**Normal attack**
- Air unit (`isAir`, `airHeight=62`). `attackMain` fires `FairyMusicNote` with `numShot = 1.5` (Ⅱ 2).

**Skill — support aura**
- Gathers alive allies (excluding self) within radius 350 (`SKILL_RADIUS_SQ=122500`), sorts by distance, supports up to 20 nearest.
- Per ally: `heal` 6 HP (Ⅱ 12) for normal allies, or 0.5 (Ⅱ 1) for castles. Non-castle allies also gain +5 mana (Ⅱ +10), a move-speed buff, and the Fairy-wing visual.

**Buffs & debuffs**
- Move speed: +25% (value 0.25, Ⅱ 0.35), 100t (Ⅱ 150t), ≤20 nearest non-castle allies — id = `kindNum` (53 / 54). Plus direct HP heal + mana restore (not buff-system). Self excluded.

**Base → Ⅱ**
- Heal 6 → 12 (castle 0.5 → 1); mana 5 → 10; buff value 0.25 → 0.35; buff dur 100t → 150t; basic numShot 1.5 → 2.

**Key values**
| | base | Ⅱ |
|---|---|---|
| numShot (basic) | 1.5 | 2 |
| ally search radius | 350 (²=122500) | 350 |
| max targets | 20 | 20 |
| heal (ally) | 6 | 12 |
| heal (castle) | 0.5 | 1 |
| mana restore | 5 | 10 |
| movspd buff value | 0.25 | 0.35 |
| movspd buff dur | 100t | 150t |
| airHeight | 62 | 62 |

**Formulas**
- `moveSpd = orgMoveSpd × (1 + value)` → +25% (base) / +35% (evolved). Buff id = `kindNum` (53 or 54), so base & evolved Fairy buffs use different ids and SUM; two Fairies of the same tier share an id and take max (no stack).

**✓ Matches description** — "restores HP and mana + increases movement speed" maps exactly to `heal` + `mana +=` + `addMoveSpeedBuff`; evolved bumps all four (heal 6→12, mana 5→10, buff 0.25→0.35, dur 100→150). Castles get reduced heal and no mana/move buff (an undocumented nuance, not a contradiction).

**Notes**
- Buff-id = kindNum is unusual (most units use a named `fQ.*` enum). Heal/mana are applied directly, not via `addMaxHealthBuff`.

---

### Priest / Priest Ⅱ — `Priest1` (kindNum: 55 · Ⅱ 56)
**TL;DR.** Ranged support healer that fires light bolts and casts an AoE heal plus a hit-negating shield on the team — but the "chance to stun" its normal attack claims doesn't exist in code.

**At a glance**
- **Role:** Healer / support (AoE heal + hit-blocking shields)
- **Attack:** ranged `YellowEnergyBall`, 1.5 shots base / 2 at Ⅱ (NO stun despite text)
- **Skill:** shields nearest ≤20 allies (blocks next 2/3 hits) + heals lowest-HP% ≤20 allies (5%/10% max HP)
- **Type:** RANGE

**In-game text**
- Normal: "Attacks from range with light energy and has a chance to stun enemies."
- Skill: "Restores HP for all allies and grants them a shield."
- Skill (Ⅱ): "Greatly restores HP for all allies and grants them an enhanced shield."

**Normal attack**
- `attackMain()` sets `numShot = 1.5 base / 2 Ⅱ` then base multi-shot.
- objAtk: OBJ_ATK_1 {39,46} (base, 2 hits) / OBJ_ATK_2 {39,44,49} (Ⅱ, 3 hits).
- `YellowEnergyBall` only deals damage (g=0, speed=8) — applies NO stun (see ⚠️).

**Skill — heal + shield**
- Cosmetic `showPriestLight(60)`.
- **Shield pass:** sorts allies by distance, takes nearest ≤20, calls `showPriestStart(shieldDur, shieldHits)` → sets `numPriestShield=shieldDur`, `priestShieldHits=shieldHits` (fully negates the next `shieldHits` hits while the timer lasts).
- **Heal pass:** sorts allies by HP% ascending (lowest first), takes nearest 20, `heal(t, this, true)` with `t = healPct` for normal allies / `castlePct` for castles.

**Buffs & debuffs** (to nearest ≤20 allies)
- Hit-blocking shield: `numPriestShield` dur (90 base / 120 Ⅱ), `priestShieldHits` count (2 base / 3 Ⅱ).
- % heal: 5% base / 10% Ⅱ of max HP (castles get 0.5% / 1%). No enemy debuffs.

**Base → Ⅱ**
- Heal 5% → 10% (castle 0.5% → 1%); shield duration 90t → 120t; shield hits 2 → 3; numShot 1.5 → 2; normal 2-hit → 3-hit.

**Key values**
| metric | base | Ⅱ |
|---|---|---|
| ally heal pct | 5% | 10% |
| castle heal pct | 0.5% | 1% |
| shield duration | 90t | 120t |
| shield hits | 2 | 3 |
| SKILL_MAX_TARGETS | 20 | 20 |
| numShot | 1.5 | 2 |
| objAtk | {39,46} | {39,44,49} |

**Formulas**
- Heal amount `= maxHp * 0.01 * healPct` (evolved 10 ⇒ +10% max HP).
- Shield: while `numPriestShield>0 && priestShieldHits>0`, an incoming hit is fully negated and `priestShieldHits--`; at 0 the shield clears.

**⚠️ Description vs code**
- Heal+shield skill matches ("greatly restores / enhanced shield" = 10% vs 5%, 3 hits/120t vs 2 hits/90t). DELTA on NORMAL: the description says it "has a chance to stun enemies," but `YellowEnergyBall` has NO `onHitMain` and applies NO stun anywhere in `Priest1` or the weapon. The documented normal-attack stun does NOT exist in code (contrast `Bullet1`/Gunner, which does have the hook).

**Notes**
- Heal targets the LOWEST-HP% allies first; shields target the NEAREST allies first — two different sort orders, both capped at 20. Castle heal % is ~10× smaller than ally heal %.

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

### Drums of the Battlefield — `BigDrumer1` (kindNum: 69 · Ⅱ 78)
**TL;DR.** Support drummer — pulses an attack-speed + move-speed buff to the whole team every ~8s; deals no damage.

**At a glance**
- **Role:** Support buffer (no attack)
- **Cadence:** every 500t (~8.3s); first pulse randomized so drummers desync
- **Buffs:** +120% atk-speed & +120% move-speed → **+130%** at Ⅱ
- **Targets:** ≤30 nearest allies (= your whole team)

**In-game text**
- Normal: "Supports allies by beating a drum instead of attacking." (Ⅱ: same.)
- Skill: "Temporarily increases ATK, attack speed, and movement speed for all allied heroes." (Ⅱ: "Further boosts ATK, attack speed, and movement speed of all allied heroes for a limited time.")

**Skill — the drum beat (every 500t)**
- Doesn't attack. `attackMain` is gated by `skillCoolDown` (decremented in `execute`, reset to 500): gathers all alive `allyList`, sorts by squared distance, and buffs the nearest `min(SKILL_MAX_TARGETS=30, n)` allies.
- Both buffs use id 8001, so re-beats refresh rather than stack. Buff strength `s = 1.2` (**Ⅱ 1.3**), duration `dur = 350t` (**Ⅱ 400t**).
- First cooldown is randomized `500*random.next()` so instances desync (constructor seeds `skillCoolDown=300`, overwritten in `setData`). Drum-beat frame `objAtk={48:1}`.

**Buffs & debuffs**
- Attack speed: +120% (Ⅱ +130%), 350t (Ⅱ 400t), ≤30 allies — id 8001
- Move speed: +120% (Ⅱ +130%), 350t (Ⅱ 400t), ≤30 allies — id 8001

**Base → Ⅱ**
- Buff strength +120% → +130%; duration 350t → 400t.

**Key values**
| | base | Ⅱ |
|---|---|---|
| buff strength | +120% (value 1.2) | +130% (value 1.3) |
| buff duration | 350t (~5.8s) | 400t (~6.7s) |
| pulse cooldown | 500t (~8.3s) | 500t |
| max targets | 30 | 30 |
| BUFF_ID | 8001 | 8001 |
| objAtk frame | 48 | 48 |

**Formulas**
- `atkSpd = orgAtkSpd × (1 + value)` → value 1.2 = +120%, value 1.3 = +130%. Same for move speed.

**⚠️ Description vs code**
- Blurb claims an **ATK** boost, but the code calls only `addAttackSpeedBuff` + `addMoveSpeedBuff` — no `addAttackDamageBuff`, so raw ATK is **not** buffed. Confirmed by reading the full `attackMain` (two buff calls only).

**Notes**
- Multiple drummers share id 8001 ⇒ per the max-per-id aggregation rule they don't stack strength, only extend uptime via the `refresh` flag. Static fields verified in bundle: `zt(u0,"BUFF_ID",8001), zt(u0,"SKILL_MAX_TARGETS",30)`.

---

### Pilot / Pilot Ⅱ — `Pilot1` (kindNum: 79 · Ⅱ 80)
**TL;DR.** A flying gunner that strafes multiple enemies from the air, and on its skill fires a volley of missiles while taunting one foe to attack it.

**At a glance**
- **Role:** Air ranged DPS
- **Attack:** `FireBullet` at up to 4 (Ⅱ 7) targets; base 85% single shot, Ⅱ fires a geometric burst
- **Skill:** launches 3 (Ⅱ 5) `PilotMissile1` (1.5× dmg, 25% `stun(10)` + ≤4-enemy 0.5× splash w/ 35% `stun(8)`), then taunts exactly 1 enemy
- **Flying:** `isAir=true`, airHeight 75

**In-game text**
- Normal: "Fires consecutive shots from the air at multiple enemies." (Ⅱ: "...at more enemies.")
- Skill: "Launches a missile and taunts 1 enemy, forcing them to target you." (Ⅱ: "Fires more missiles and taunts 1 enemy...")

**Normal attack**
- Builds a target list (`getEnemiesForDirection` up to `maxAttackTargets`, main target first), then fires.
- Base: 85% chance to fire one shot per call.
- **Ⅱ:** fires one shot, then keeps firing extra shots while `chance(.4)` succeeds (geometric burst), cycling through `attackTargetList`.

**Skill — missile volley + single taunt (mana-gated)**
- Takes the nearest 5 attackable enemies (`getAttackableEnemyList(5)`), launches `skillShotCount` missiles at 1.5× dmg round-robin across them. Each `PilotMissile1` on hit: **25% chance to `stun(10)`** the primary target, and splashes up to 4 nearby enemies (~30px) for **0.5× damage with a 35% `stun(8)`** each.
- Then **taunts exactly 1 enemy**: sets `s.target=this` for the first enemy not already targeting the Pilot, then `break` (a direct retarget, not the radius `taunt()` helper).

**Buffs & debuffs**
- Missile stun (skill): 25% `stun(10)` on the primary target; each splash victim (≤4, ~30px) takes 0.5× damage + 35% `stun(8)`.
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
| missile stun (primary) | 25% → `stun(10)` | same |
| missile splash | ≤4 × 0.5 dmg, 35% → `stun(8)` | same |

**Formulas**
- Ⅱ normal-attack shot count = 1 + Geometric(.4) per call (expected ≈ 1.67), each at a cycled target.

**✓ Matches description** — "fires more missiles" = 3→5; "more enemies" = maxAttackTargets 4→7 plus the evolved burst-firing. Note: the "taunt 1 enemy" is a direct single-target retarget (`s.target=this; break`), not an AoE taunt.

---

### Forest Guardian — `TigerRider1` (kindNum: 81 · Ⅱ 84)
**TL;DR.** Ranged archer that volleys arrows at several enemies at once; its skill is a multi-target barrage with a chance to grant itself a speed buff.

**At a glance**
- **Role:** Ranged DPS (multi-target volley + self speed buff)
- **Attack:** cycles arrows across 3 → **4** nearest enemies
- **Skill:** arrow barrage (1–2 → **1–3** arrows) within radius 220; 50% chance to self-buff
- **Self buff:** +80% atk/move-speed → **+110%** (distinct ids ⇒ both apply)

**In-game text**
- Normal: "Fires magic arrows at enemies within range." (Ⅱ: "Fires magic arrows at more enemies within range.")
- Skill: "Attacks multiple enemies at once with a barrage of arrows, and has a chance to grant itself a Speed Up buff." (Ⅱ: "Attacks multiple enemies at once with a volley of arrows, and has a chance to grant itself an enhanced Speed buff.")

**Normal attack**
- Ranged, `weaponClass=TigerRiderArrow1`. `onAttackStartFrame` builds `targetList = getAttackableEnemyList(NUM_ATK_TARGETS = 3, Ⅱ 4)` with current target forced to front; `attackMain` fires one arrow per call, cycling `attackIndex` through the list (`doRangeAttack`).
- Direction-aware: `selectDirectionFrames` swaps 5 attack/skill frame sets + fire points by firing angle (`atan2`).

**Skill — arrow barrage**
- `gotoSkillState` sets `mana=0` and, with `random.chance(.5)` (50%), self-buffs atk-speed (id 210) + move-speed (id 211) at value `s = 0.8` (**Ⅱ 1.1**) for `dur = 240t` (**Ⅱ 300t**), plus Accelerate FX.
- `onSkillStartFrame` collects `getEnemiesWithin(220, true)` into `skillTargetList`; `skillMain` fires N skill arrows (`fireSkillArrow`, bounceCount=`numBounce`).
- N (base) = `random.chance(.7)?2:1`; N (Ⅱ) = `rand<.3?3 : rand<.75?2 : 1`.

**Buffs & debuffs**
- Self atk-speed (50% per skill): +80% (Ⅱ +110%, value 0.8/1.1), 240t (Ⅱ 300t) — id 210
- Self move-speed (50% per skill): +80% (Ⅱ +110%), 240t (Ⅱ 300t) — id 211

**Base → Ⅱ**
- Normal targets 3→4; skill arrows 1–2→1–3; self-buff value 0.8→1.1, duration 240→300.

**Key values**
| | base | Ⅱ |
|---|---|---|
| NUM_ATK_TARGETS | 3 | 4 |
| BUFF_VALUE | 0.8 (+80%) | 1.1 (+110%) |
| BUFF_DURATION | 240t | 300t |
| self-buff chance | 0.5 | 0.5 |
| skill arrows | 1 or 2 (70%→2) | 1/2/3 (<.3→3, <.75→2) |
| skill target query | `getEnemiesWithin(220,true)` | same |
| atkSpd / moveSpd buff ids | 210 / 211 (distinct ⇒ both apply) | 210 / 211 |
| weaponClass | TigerRiderArrow1 | same |

**Formulas**
- Self `atkSpd = orgAtkSpd × (1+0.8)` ⇒ +80% / `×(1+1.1)` ⇒ +110%; same magnitude moveSpd. atkSpd (210) and moveSpd (211) use distinct ids, so they don't interfere.

**✓ Matches description** — "fires arrows at more enemies" (Ⅱ) = NUM_ATK_TARGETS 3→4; "barrage/volley" = 1–2 (base) / 1–3 (Ⅱ) skill arrows; "chance to grant itself a Speed Up" = 50% self atk+move-speed buff; "enhanced Speed buff" (Ⅱ) = value 0.8→1.1, duration 240→300.

**Notes**
- Structurally near-identical to `Unicorn1`/Unicorn Archer, but Unicorn1 has NO self-buff — that self-buff is the distinguishing Forest-Guardian trait.

---

### Steam Punk — `SteamPunk1` (kindNum: 82 · Ⅱ 85)
**TL;DR.** Ranged gunner whose homing **normal-attack** missiles (2, or 3 evolved) can stun + splash; its skill is a separate **damage-only** missile barrage (no stun).

**At a glance**
- **Role:** Ranged DPS (multi-target homing missiles + stun)
- **Attack:** one homing `SteamFire1` per target across 2 hit-frames → 2 missiles (Ⅱ 3)
- **Targets:** nearest 2 enemies in facing arc (Ⅱ 3)
- **Per-missile:** 30% stun (Ⅱ 40%) + ≤3-enemy splash
- **Skill:** damage-only barrage (`SteamMissile1`, 1.5×, **no stun**) at all enemies within 220 (mana-gated)

**In-game text**
- Normal: "Fires a homing missile that has a chance to stun 2 enemies." (Ⅱ: "…stun 3 enemies.")
- Skill: "Fires multiple missiles at enemies within range." (Ⅱ: "…with a chance to fire additional missiles.")

**Normal attack**
- Builds a `targetList` of the nearest 2 (Ⅱ 3) enemies in its facing arc (`getEnemiesForDirection`).
- Fires one homing `SteamFire1` per target across the hit-frames: `OBJ_ATK_1={90,95}` → 2 missiles; Ⅱ `OBJ_ATK_2={90,93,96}` → 3 missiles.
- Each missile on hit: 30% chance (Ⅱ 40%) to stun its primary target for 40t (Ⅱ 50t), and splashes ≤3 enemies within ~25px (`s²+e²<625`, `|Δ|≤35`) for 0.4× damage.

**Skill — missile barrage (mana-gated)**
- `onSkillStartFrame` gathers up to all enemies within 220, then `skillMain` fires a `SteamMissile1` at each in turn — `SteamMissile1.onHit` deals **1.5× physical damage only, with NO stun** (the stun lives in the normal-attack `SteamFire1.onHitMain`, not here).
- Ⅱ: 20% chance to fire a second missile that cycle.

**Buffs & debuffs**
- Stun on the **normal-attack** `SteamFire1` missile hit: 40t (Ⅱ 50t), 30% chance (Ⅱ 40%), primary target only. **The skill's `SteamMissile1` does not stun.**

**Base → Ⅱ**
- Basic targets 2 → 3 (extra hit-frame, 2 → 3 missiles); stun chance 0.3 → 0.4; stun dur 40t → 50t; skill gains a 20% double-missile roll.

**Key values**
| | base | Ⅱ |
|---|---|---|
| basic hit-frames | {90,95} → 2 missiles | {90,93,96} → 3 missiles |
| basic targets | 2 | 3 |
| missile stun chance | 0.3 | 0.4 |
| missile stun dur | 40t | 50t |
| missile splash | ≤3 × 0.4 dmg (~25px) | same |
| skill gather range | 220 | 220 |
| `SteamMissile1` dmg | 1.5 | 1.5 |
| extra-missile chance | — | 0.2 |

**Formulas**
- Stun rolls per missile independently → "stun 2/3 enemies" = 2/3 missiles each rolling its own stun.

**✓ Matches description** — "stun 2/3 enemies" reflects the 2/3 separate homing missiles; evolved bumps both target count (2→3) and stun chance/dur.

**Notes**
- First skill missile always fires at the locked `target`, then nearest others. `weaponClass=SteamFire1`, skill weapon `SteamMissile1`. `maxMana` not set on basic (skill mana-gated via base class).

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

### Dark Ninja / Dark Ninja Ⅱ — `DarkNinja1` (kindNum: 87 · Ⅱ 88)
**TL;DR.** Teleporting assassin that blinks beside random enemies for rapid lifesteal hits, and on skill yanks far foes in with dark chains before a knock-up spin.

**At a glance**
- **Role:** Melee DPS / assassin (teleporting lifesteal bruiser)
- **Attack:** blinks beside a random nearby enemy, low-damage rapid multi-hit (0.8× each) with lifesteal
- **Skill:** mana-gated (≥500) — Dark Chain pull (×1, ×2 at Ⅱ) + spinning AoE knock-up
- **Stats:** maxHp 150, atkDmg 3, def 10, moveSpd 2.6, atkRange 8, maxMana 250

**In-game text**
- Normal: "Teleports to an enemy at random and unleashes a series of close-range attacks, restoring a small amount of HP with each hit."
- Skill: "Fires a Dark Chain to pull in distant enemies (including airborne units), then attacks nearby enemies with a spinning attack."
- Skill (Ⅱ): "Fires Dark Chain to pull in 2 distant enemies (including aerial units), then strikes nearby enemies with a spinning attack."

**Normal attack**
- 50% chance to scan enemies within 120; for each in-bounds enemy, 30% chance to re-target to it, then **teleport** beside it (±30 px).
- Hits with `doMeleeAttack(target, 0.8)` and lifesteals `+0.005*maxHp` per hit.
- Combo length: 6 hits base (OBJ_ATK_1) → **8 hits at Ⅱ** (OBJ_ATK_2).

**Skill — spin + chain (mana ≥ 500)**
- Mana-gated, not cooldown-gated: triggers when IDLE with `mana>=500` and enemies present.
- Builds a chain-target list (`findChainTargets`, FARTHEST-first within 150 px; air/ranged units down-weighted).
- If nearest chain target has `weight>=4`, teleports to it and `doMeleeAttack(_, 1.5)`; otherwise fires a `DarkChain1` projectile to pull it in. **Ⅱ fires a second DarkChain1** at chain target [1] (if its `weight<=3`).
- Spinning AoE: on each of 9 `whirlAttackFrame` frames, fires `doDamage(_, 0.5)` to up to 2 enemies within `1.5*atkRange` (=12) and `blow()`s them (knock-up).

**Passive / special**
- Lifesteal on every normal hit: `hp = min(maxHp, hp + 0.005*maxHp)`.

**Buffs & debuffs**
- Applies `blow` (knock-up, ±0.2/−4) to enemies during the spin. No ally buffs.

**Base → Ⅱ**
- Normal combo 6 hits → 8 hits; skill fires a second Dark Chain.

**Key values**
| | base | Ⅱ |
|---|---|---|
| normal attack mult | 0.8 | 0.8 |
| lifesteal per hit | 0.005×maxHp | 0.005×maxHp |
| combo hits | 6 (OBJ_ATK_1 {48,54,59,64,69,74}) | 8 (OBJ_ATK_2 {48,51,54,57,61,64,69,74}) |
| chain teleport mult | 1.5 | 1.5 |
| Dark Chains on skill | 1 | 2 |
| whirl AoE mult | 0.5 (≤2 targets) | 0.5 (≤2 targets) |
| whirl radius | 1.5×atkRange (=12) | 12 |
| IDLE_SKILL_MANA | 500 | 500 |
| maxMana | 250 | 250 |
| teleport-scan radius | 120 | 120 |
| teleport offset | 30 px | 30 px |
| blow | (±0.2, −4) | (±0.2, −4) |

**Formulas**
- Lifesteal: `hp = min(maxHp, hp + 0.005*maxHp)`.
- Normal teleport: `x = targetX ∓ 30`.

**✓ Matches description** — chain pull (1 base / 2 evolved) and spin AoE both match; evolved scaling (8-hit combo, second chain) is consistent.

**Notes**
- `maxMana=250` but the auto-cast gate is `mana>=500`, so the threshold can never be reached from `maxMana` alone — the skill must rely on external mana grants/over-cap; the description mentions no mana cost.
- Low per-hit damage (0.8×) but rapid multi-hit + lifesteal makes it a sustain bruiser.

---

### Winged Knight — `WingKnight1` (kindNum: 89 · Ⅱ 93)
**TL;DR.** Melee bruiser with a 3-hit splash combo, a teleport-slam skill, and two passive states — Flash (kill-streak buff + chain-teleport) and Survival (low-HP shield + berserk).

**At a glance**
- **Role:** Melee DPS with kill-streak (Flash) and low-HP (Survival) passives
- **Attack:** 3-hit combo `[.7, .8, 1]×` + one nearby splash victim; 3rd hit knocks back
- **Flash:** at 6 kills → atk/haste/move buffs + chain-teleport on each kill
- **Survival:** ≤20% HP → power shield + +100% atk-spd/atk-dmg (60s cooldown)
- **Skill:** teleport onto nearest enemy ≤500, stun, slam ≤15 enemies for 2.5× (Ⅱ 3×)

**In-game text**
- Normal: "Deals 3 consecutive hits to enemies and also damages nearby enemies. The final hit knocks enemies back. **Flash:** After defeating a set number of enemies, an Attack and Haste buff is triggered, and each kill instantly moves you to the next target. **Survival:** When HP falls below a certain level, a shield is briefly formed and attack speed and attack power greatly increase."
- Skill: "Teleports to an enemy and deals area damage to nearby enemies."

**Normal attack**
- `attackMain` cycles `comboIndex%3`, dealing `ATK_DMG=[.7,.8,1]` per hit, plus one nearby splash victim within 60 (`COMBO_SPLASH_RANGE`) at the same multiplier.
- 3rd hit (`i===2`) knocks back: x-velocity 3 (Ⅱ 4), y-velocity -2, for 30t (Ⅱ 40t).

**Passive — Flash (kill-streak)**
- `onKillEnemy` increments `killCount`; at 6 kills (`KILL_THRESHOLD`) fires `activateFlashBuff()` and enters skill state.
- While active: each kill snaps to a new target within 1200 (`FLASH_DETECT_RANGE`); drains mana per tick; on timer expiry (480t) casts a finishing slam.

**Passive — Survival (low HP)**
- `onHpDroppedBelow20` (≤20% HP): sets HP floor to `max(1, maxHp*0.2)`, casts a power shield for 180t, applies berserk atk-spd/atk-dmg for 600t, forces a skill cast.
- Gated by `SURVIVE_SKILL_COOLDOWN=3600` (~60s). HP-floor logic prevents the killing blow while Survival is available.

**Skill — teleport slam (mana ≥ 900)**
- Teleports onto nearest enemy within 500 (`SKILL_TARGET_RANGE`), stuns it 30t (Ⅱ 45t).
- Ⅱ also stuns enemies within `DASH_STUN_RANGE=60`.
- `doSkillSlam`: 2.5× (Ⅱ 3×) damage to ≤15 enemies within 110 (Ⅱ 150).

**Buffs & debuffs**
- Flash — Move speed: +150% (value 1.5), 480t, self — id `WingKnight1_FLASH_MOVSPD`
- Flash — Attack dmg: +50% (value 0.5), 480t, self — id `WingKnight1_DASH_BUFF`
- Flash — Attack speed: +50% (value 0.5), 480t, self — id `WingKnight1_FLASH_ATKSPD`
- Survival — Attack speed: +100% (value 1), 600t, self — id `WingKnight1_BERSERK_ATKSPD`
- Survival — Attack dmg: +100% (value 1), 600t, self — id `WingKnight1_BERSERK_ATKDMG`
- Survival — power shield: 180t, self
- On enemies: stun (skill teleport), knockback (combo 3rd hit)

**Base → Ⅱ**
- Knockback x-velocity 3 → 4 and duration 30t → 40t; skill stun 30t → 45t (+AoE stun radius 60); slam radius 110 → 150; slam damage 2.5× → 3×.

**Key values**
| | base | Ⅱ |
|---|---|---|
| combo damage | `[.7, .8, 1]×` | same |
| splash range | 60 | 60 |
| 3rd-hit knockback | vx 3, vy -2, 30t | vx 4, vy -2, 40t |
| Flash threshold | 6 kills | 6 kills |
| Flash buff dur | 480t | 480t |
| Flash detect range | 1200 | 1200 |
| Flash move/atk-spd/atk-dmg | 1.5 / 0.5 / 0.5 | same |
| Survival HP threshold | 0.2 (≤20%) | same |
| Survival shield dur | 180t | 180t |
| Survival berserk dur | 600t | 600t |
| Survival atk-spd/atk-dmg | 1 / 1 (+100% each) | same |
| Survival cooldown | 3600t (~60s) | same |
| skill stun | 30t | 45t (+AoE radius 60) |
| skill target range | 500 | 500 |
| slam radius | 110 | 150 |
| slam damage | 2.5× | 3× |
| max targets (slam) | 15 | 15 |
| maxMana | 900 | 900 |

**Formulas**
- `atkSpd = orgAtkSpd × (1 + value)` → 0.5 = +50% (Flash), 1.0 = +100% (Survival). `atkDmg` buffs add +50% (Flash) / +100% (Survival).

**✓ Matches description** — code is richer than the text. "Attack and Haste buff" = the Flash atk-dmg + atk-spd + move-spd buffs; "shield…attack speed and attack power greatly increase" = the Survival branch (verified +100% each). Distinct buff ids per state so Flash and Survival co-exist.

**Notes**
- Flash and Survival are passive (NATK), not the mana skill. `normalSize=.8`, `evolSize=.85`.

---

### Sylphid — `Sylphid1` (kindNum: 90 · Ⅱ 94)
**TL;DR.** Ranged shuriken thrower that ramps its own attack speed with every hit; at max stacks it enters Rage and spews extra shurikens, and its skill rains divergent tornados.

**At a glance**
- **Role:** Ranged DPS (shuriken stacker / rage)
- **Attack:** bouncing shurikens (`numBounce=3`); each hit +4% atk-speed (up to 25 stacks = +100%)
- **Rage:** at 25 stacks → 180t (~3s) window firing bonus shurikens (`doRangeAttack(target,4)`)
- **Skill:** `SylphidTornado1` volley — each tornado vacuums enemies in, roots them (`binding(30)`) and deals 0.6×/30t over 300t, then knocks back on expiry; **Ⅱ** adds a 3rd tornado (count only — per-tick dmg stays 0.6×)

**In-game text**
- Normal: "Fires shurikens in rapid succession, and each hit gradually increases attack speed.\nRage: When attack speed reaches its maximum, additional shurikens are fired with each normal attack."
- Skill: "Fire tornados in succession to deal damage to enemies."

**Normal attack**
- `doRangeAttack(target)`; **while raging** (`rageTimer>0`) also `doRangeAttack(target, 4)` (extra shurikens). Shurikens bounce up to 3× (`numBounce=3`).
- On each shuriken landing, `onShurikenHit` (suppressed during rage) bumps `atkStack` up to `ATKSPD_MAX_STACK=25`, sets `stackResetTimer = STACK_BUFF_DUR = 600`, and applies `addAttackSpeedBuff(id=220, atkStack*0.04, 600, refresh)`.

**Passive / special — stack ramp & Rage**
- At 25 stacks → `activateRage()`: `rageTimer = RAGE_DURATION = 180`, resets stacks, applies the full `25*0.04 = 1.0` atkSpd buff for the rage duration, shows Accelerate FX.
- In `execute`: when not raging, stacks fully reset to 0 after `stackResetTimer` ticks; when rage ends, the atkSpd buff is cleared (`addAttackSpeedBuff(220, 0, 1, refresh)`).
- During rage `onShurikenHit` is skipped, so stacks don't accumulate while raging — rage is a fixed 180t window.

**Skill — tornado volley**
- Fires `SylphidTornado1` (power `i = 1`, **Ⅱ 1.2**): base spawns the tornado on the target plus one "most divergent" (most opposite-direction) target via `findMostDivergentTarget` (gated by `DIVERGE_THRESHOLD=0.7` dot-product), else a random-offset extra.
- **Ⅱ:** adds a 3rd tornado at the next most-divergent target (excluding the first two).
- If no live target, scatters `spawnTornadoAtRandomOffset` tornados (2 base / 3 Ⅱ).
- **Each `SylphidTornado1` lives 300t:** vacuums enemies within r70 toward its center; every 30t it hits enemies within r50 for **0.6× damage + `binding(30)` (root)**; on expiry it **knocks back** everything within r90. (The 0.6× is the weapon's hard-coded `DMG_PER_TICK` — the Ⅱ `1.2` "power" sets `damagePercent` but the tornado ignores it, so Ⅱ only adds tornado **count**, not per-tick damage.)

**Buffs & debuffs**
- Self atk-speed (ramp): +4% per stack (value 0.04·stacks), 600t (~10s), refreshing — id 220
- Self atk-speed (rage): +100% (value 1.0), 180t (~3s) — id 220; cleared to value 0 when rage ends
- Skill tornado debuffs: **root** — `binding(30)` re-applied every 30t over the tornado's 300t life; plus a vacuum-pull (r70) and a knockBack burst on expiry (r90)

**Base → Ⅱ**
- Skill tornado power 1→1.2; max tornados 2→3 (and random-scatter fallback 2→3).

**Key values**
| | base | Ⅱ |
|---|---|---|
| skill "power" (spawn arg) | 1 | 1.2 (per-tick dmg still 0.6×) |
| tornado per-tick dmg | 0.6× (fixed) / 30t | same |
| tornado root | `binding(30)` / 30t | same |
| tornado life | 300t | same |
| max tornados / scatter | 2 | 3 |
| ATKSPD_PER_STACK | 0.04 (+4%) | 0.04 |
| ATKSPD_MAX_STACK | 25 (⇒ +100%, triggers rage) | 25 |
| STACK_BUFF_DUR | 600t (~10s) | 600t |
| RAGE_DURATION | 180t (~3s) | 180t |
| DIVERGE_THRESHOLD | 0.7 | 0.7 |
| numBounce | 3 | 3 |
| maxMana | 600 | 600 |
| rage extra shot | `doRangeAttack(target,4)` | same |
| atkSpd buff id | 220 | 220 |

**Formulas**
- `atkSpd = orgAtkSpd × (1 + 0.04·stacks)`; at 25 stacks ⇒ `×(1+1.0)` = +100% (×2), which fires rage. Rage holds +100% for 180t.

**✓ Matches description** — "each hit increases attack speed" = +0.04/stack (`onShurikenHit`); "max attack speed → additional shurikens" = at 25 stacks rage triggers and normals fire the extra `doRangeAttack(target,4)`. Skill = tornados, evolved fires one more (3 vs 2). ⚠️ The blurb ("deal damage") omits the tornado's **root / vacuum / knockBack**, and the Ⅱ `1.2` "power" arg doesn't actually raise damage (per-tick is the fixed `DMG_PER_TICK=0.6`) — only the tornado count changes.

---

### Abyss Mage / Abyss Mage Ⅱ — `Abyss1` (kindNum: 91 · Ⅱ 95)
**TL;DR.** Ranged chain-lightning mage — basic attacks bounce between enemies for decaying damage and refund mana on kills; skill chains a shock that locks enemies' actions.

**At a glance**
- **Role:** Ranged DPS / mage (chain-lightning)
- **Attack:** lightning chains to 4 enemies (5 at Ⅱ), damage decaying per link; +30 mana on kill
- **Skill:** hits up to 10 enemies in 360 range, ×2 dmg (×3 at Ⅱ) + 60t Shock each
- **Type:** RANGE

**In-game text**
- Normal: "When you attack an enemy, chain lightning jumps to nearby enemies, dealing gradually reduced damage. Restore mana when defeating an enemy."
- Skill: "Strikes multiple enemies in range with lightning in succession, dealing AoE damage and briefly inflicting Shock, disabling their actions."

**Normal attack**
- Builds a chain from the target, repeatedly `findChainTarget` (nearest un-hit enemy within `CHAIN_RANGE=120`) up to 4 links base / **5 at Ⅱ**.
- Each link deals `doDamage(_, CHAIN_DMGS[r], ranged)` with `CHAIN_DMGS=[1, 0.7, 0.5, 0.4, 0.3]` (links past index 4 default to 0.5).
- On a kill: +30 mana.

**Skill — chained shock**
- `onSkillStartFrame` collects up to 10 enemies within 360; `skillMain` fires one per objSkill frame (10 frames).
- Each hit: `doDamage(target, 2 base / 3 Ⅱ, ranged)` + `target.shock(60)` (60-tick action-disable).

**Buffs & debuffs**
- Enemy `shock(60)` on each skill hit (disables actions), ~1s. No ally buffs.

**Base → Ⅱ**
- Chain links 4 → 5; skill mult ×2 → ×3.

**Key values**
| | base | Ⅱ |
|---|---|---|
| chain links | 4 | 5 |
| CHAIN_RANGE | 120 | 120 |
| CHAIN_DMGS | [1, 0.7, 0.5, 0.4, 0.3] | same |
| KILL_MANA_GAIN | 30 | 30 |
| skill dmg mult | 2 | 3 |
| SKILL_RANGE | 360 | 360 |
| SKILL_TARGET_MAX | 10 | 10 |
| shock | 60t | 60t |
| LIGHTNING_DUR / STEP | 58 / 36 | 58 / 36 |

**Formulas**
- Chain damage per link r = `atkDmg * CHAIN_DMGS[r]` (head 1.0× → 0.7 → 0.5 …).

**✓ Matches description** — "gradually reduced damage" = `CHAIN_DMGS` decay; "restore mana when defeating" = +30 on kill; "briefly inflicting Shock" = `shock(60)`. Evolved adds a chain link and raises skill mult; the locale text just doesn't enumerate numbers.

**Notes**
- Skill targets are pre-collected on the start frame, then consumed one-per-frame, so all collected enemies are hit in sequence.

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

### (Elf basic swordsman) — `ElfSwordMan1` (kindNum: no exact-name description)
**TL;DR.** Stripped-down basic melee soldier with a double-hit attack and no skill — likely a spawned/enemy infantry variant.

**At a glance**
- **Role:** Basic melee enemy/soldier (double-hit, no skill)
- **Attack:** 2 hit-frames `{49,53}` → double hit
- **No skill, no buffs** — minimal class (only `initializeData`)

**In-game text**
- No "ElfSwordMan"/"Swordsman" entry in `/tmp/unit_desc.json`. Its double-hit NATK reads identically to Elf Warrior's "Strikes enemies with a melee double hit" but it has no skill. Likely a basic spawned soldier variant (summoned/enemy infantry) rather than a deployable book unit.

**Normal attack**
- `objAtk={49,53}` → melee double-hit. No `hasSkill`, no `skillMain`, no buffs.

**Key values**
| variable | value | meaning |
|---|---|---|
| objAtk | {49,53} | double-hit attack frames |
| skillFrames | == attackFrames QK(36,65) | no separate skill |
| radius / hitHeight | 7 / 27 | hitbox |

**⚠️ Description vs code**
- **No dedicated description** — it shares the "double melee hit" wording of Elf Warrior but lacks any skill. Flagged as an undocumented basic variant.

**Notes**
- Trivial basic attacker. Compare ElfWarrior1 (same family), which adds the 1.5× triple skill.

---


# Summons

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


# Stage bosses

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


# Stage-boss minions

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


# Enemy wave units

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

### Boar1 — `Boar1` (kindNum: none — enemy wave unit, not in unit_desc)
**TL;DR.** A plain melee enemy that shoves whatever it hits a short distance backward.

**At a glance**
- **Role:** Basic enemy (melee, knockback)
- **Attack:** basic melee on the nearest enemy, hit lands on attack-frame 50
- **Signature:** every landed hit knocks the target back (small horizontal shove + slight upward pop)
- **No skill, no buffs, no cooldown logic**

**Normal attack**
- Calls `super.attackMain()` (hit fires on frame 50 per `objAtk={50:1}`); if the target survives, applies `blow(3*direction, -3.5)` — a horizontal shove in its facing direction plus a slight upward pop.

**Key values**
| variable | value | meaning |
|---|---|---|
| objAtk | `{50:1}` | hit fires on attack-anim frame 50 (1 hit) |
| blow vx | `3*direction` | horizontal knockback impulse |
| blow vy | `-3.5` | upward knockback impulse |
| radius / hitHeight / hitWidth | 13 / 22 / 15 | collision box |
| setSize | 0.95 | sprite scale |

**Formulas**
- Knockback magnitude further scaled by target weight: `1 - 0.2*(weight-1)`.

**Description vs code**
- No in-game description exists for this class (see scope note), so there is nothing to compare against.

---

### Boar2 — `Boar2` (kindNum: none — enemy wave unit, not in unit_desc)
**TL;DR.** The elite boar — harder knockback than Boar1 and it lifesteals 3% of its max HP on every hit.

**At a glance**
- **Role:** Basic enemy (melee, knockback, self-heal — the "elite" boar)
- **Attack:** basic melee, hit on frame 50
- **Signature:** stronger knockback `4/-4.5` **plus** self-heal of **3% max HP per landed hit**
- The heal is part of the normal attack — no discrete skill/cooldown

**Normal attack**
- Knocks the target back with `blow(4*direction, -4.5)` (harder than Boar1's 3/-3.5), then calls `heal(3, this, true)`. Because `isPercent=true`, that heals **3% of its own max HP** every time it lands a hit (NOT a flat 3).

**Passive / special**
- On-hit lifesteal: 3% of max HP per landed hit (defining upgrade over Boar1).

**Key values**
| variable | value | meaning |
|---|---|---|
| objAtk | `{50:1}` | hit on frame 50 |
| blow vx / vy | `4*direction` / `-4.5` | knockback (stronger than Boar1) |
| heal amount | `3` (percent) | lifesteal = 3% of max HP per landed hit |
| radius / hitHeight | 13 / 24 | collision |
| setSize | 1.05 | sprite scale |

**Formulas**
- Heal `= maxHp * 0.01 * 3` = 3% max HP per hit; knockback weight-scaled as `1 - 0.2*(weight-1)`.

**Description vs code**
- No in-game description exists; nothing to compare. (vs Boar1: +knockback, +size, and the on-hit 3%-max-HP self-heal.)

---

### Frog1 — `Frog1` (kindNum: none — enemy wave unit, not in unit_desc)
**TL;DR.** A flying jumper that dives at the castle while invulnerable, pokes it for 1 on landing, then fights as an ordinary single-target melee.

**At a glance**
- **Role:** Basic enemy — flying jumper that dives the castle and single-target melees
- **Spawns flying** (`airHeight=55`); invulnerable + stun-immune while airborne
- **Homes the castle**, lands within 40px, deals 1 on touchdown
- **Knock it down:** 2 hits (`airHitCount >= 2`) force an early landing
- **After landing:** ordinary frame-74 single-target melee

**Normal attack (after landing)**
- Ordinary single-target melee, hit on frame 74 (`objAtk={74:1}`).

**Passive / special — flight & dive**
- `doFlying()` finds the castle (`findCastleTarget()` = first alive enemy with `isCastle`) and homes toward it at `moveSpd`.
- Within `landDistance (40)` it calls `startLanding()` and descends over `landingDuration (12)` ticks; on touchdown, if `landedNearCastle`, deals **1** flat damage to the castle (`doDamage(castle,1)`), then drops into normal idle/melee.
- **Airborne invulnerability:** the `health` setter ignores writes while `flying || landingTimer > 0`.
- **Stun-immune** while airborne (`stun()` no-ops).
- **Knockdown:** `onHitted()` increments `airHitCount`; once `airHitCount >= 2` it is forced to land.

**Key values**
| variable | value | meaning |
|---|---|---|
| airHeight (start) | 55 | spawn altitude |
| landDistance | 40 | px from castle at which it starts to land |
| landingDuration | 12 | ticks of descent animation |
| airFrames | `QK(0,12)` | in-air anim loop |
| airHitCount to drop | 2 | hits needed to force it down |
| castle landing damage | 1 | flat dmg on touchdown if near castle |
| objAtk | `{74:1}` | post-landing melee hit frame |

**Formulas**
- Descent: `airHeight = startAirHeight*(1 - t)` where `t = 1 - landingTimer/landingDuration`.

**Description vs code**
- No in-game description exists; nothing to compare. (Only ranged/AoE that registers `onHitted` twice can drop it before it reaches the castle.)

---

### Frog2 — `Frog2` (kindNum: none — enemy wave unit, not in unit_desc)
**TL;DR.** The toad upgrade — flies higher, is harder to knock down, and lands a 5-target AoE swipe with knockback instead of a single-target poke.

**At a glance**
- **Role:** Basic enemy — flying jumper with an AoE ground attack (the "toad" upgrade)
- **Spawns higher** (`airHeight=88` vs 55); invulnerable + stun-immune while airborne
- **Tougher to drop:** 3 hits (`airHitCount >= 3`) vs Frog1's 2
- **Touchdown** still deals 1 to the castle
- **AoE melee:** up to 5 ground enemies in radius 35, 1 dmg each + knockback (hit frame 86)

**Normal attack — AoE swipe (frame 86)**
- `attackMain()` targets a point `35*direction` in front, gathers up to **5** ground enemies within radius **35** via `getEnemiesWithPos` (excludes air units), deals **1** flat damage each and `blow(3*direction, -3.5)` to survivors. Hit fires on frame 86 (`objAtk={86:1}`).

**Passive / special — flight & dive**
- Same fly-to-castle behavior as Frog1 (homes castle, lands within 40px over 12 ticks, deals **1** on touchdown).
- **Flies higher** (`airHeight=88` vs 55) and **tougher to drop** — `onHitted()` needs `airHitCount >= 3` (vs 2).
- Same airborne invulnerability + stun-immunity as Frog1.

**Key values**
| variable | value | meaning |
|---|---|---|
| airHeight (start) | 88 | spawn altitude (higher than Frog1) |
| airHitCount to drop | 3 | hits to force landing (vs 2) |
| landDistance / landingDuration | 40 / 12 | same as Frog1 |
| airFrames | `QK(0,19)` | longer in-air loop |
| AoE offset | `35*direction` | center of the ground swipe |
| AoE radius | 35 | px |
| AoE max targets | 5 | enemies hit per swing |
| AoE damage | 1 | flat each |
| AoE knockback | `3*direction, -3.5` | per survivor |
| castle landing damage | 1 | on touchdown |
| objAtk | `{86:1}` | melee hit frame |

**Formulas**
- Same descent curve as Frog1: `airHeight = startAirHeight*(1 - t)`.

**Description vs code**
- No in-game description exists; nothing to compare. (vs Frog1: higher spawn, +1 hit to knock down, and a 5-target/35-radius AoE swipe with knockback — Frog1 is single-target.)

---

### Orc Spearman — `OrcSpearMan1` (kindNum: none — basic ranged enemy)
**TL;DR.** A fast, low-HP enemy spearman that just throws spears — no skill at all.

**At a glance**
- **Role:** Basic enemy (ranged, no skill)
- **Attack:** throws `OrcSpearmanSpear1` spears (very fast cadence)
- **Stats:** 100 HP, ATK 10, DEF 10, moveSpd 1.6, atkDuration 20, range 150
- **No skill:** `hasSkill` unset, no `skillMain`/`objSkill`/`attackMain` override

**How it works**
- Pure ranged auto-attacker. `unitType=RANGE`, `weaponClass=OrcSpearmanSpear1`, throws a spear on `objAtk={51:1}`, `firePoint=(3,-25)`. Uses base attack only.

**Key values**
| variable | value | meaning |
|---|---|---|
| baseMaxHp | 100 | HP |
| atkDmg / def | 10 / 10 | attack / defense |
| moveSpd | 1.6 | move speed |
| atkDuration | 20 | ticks between shots (~3 shots/s) |
| atkRange | 150 | ranged reach |
| weaponClass | OrcSpearmanSpear1 | spear projectile |

**Formulas**
- atkDuration = 20 ⇒ ~3 shots/s at 1×.

**⚠️ Description vs code**
- No localized description to compare (kindNum absent from `unit_desc.json` 1–96). The playable Orc-faction analog at this slot is the melee line; this is an internal/enemy spearman minion. Documented from code only: a fast, low-HP ranged spear-thrower with no skill. Stated explicitly rather than forcing a wrong kindNum.

---

### RoboBomb1 — `RoboBomb1` (kindNum: none — enemy wave unit, not in unit_desc)
**TL;DR.** A walking suicide bomber that lights a ~1s fuse on reaching a target and explodes for flat AoE damage — kill it first and the blast is cancelled.

**At a glance**
- **Role:** Basic enemy — suicide bomber (explode-on-arrival)
- **No normal attack** — it detonates instead of hitting
- **Fuse:** 60 ticks (~1.0s) in attack range, then self-destructs
- **Blast:** radius 70, 10 flat damage each, survivors knocked back `±7,-7`
- **Kill-before-fuse ⇒ no explosion**

**Passive / special — fuse + detonation**
- Once a target is within attack range, `execute()` sets `fuseStarted=true` and increments `fuseTimer` each tick.
- At `fuseTimer >= fuseDelay (60)` it sets `selfDestruct=true`, calls `die()`, and spawns a `RoboExplode` effect (`start(100)`) at its position.
- `onDie()` (guarded by `selfDestruct`) grabs every enemy within radius **70**, deals **10** flat damage each via `doDamage(i,10)`, and applies `blow(±7, -7)` to survivors (sign depends on whether they're left/right of the bomb).
- If killed before the fuse completes, `onDie()` early-returns ⇒ **no explosion**.

**Key values**
| variable | value | meaning |
|---|---|---|
| fuseDelay | 60 | ticks (~1.0s @1×) in-range before it detonates |
| explosion radius | 70 | px AoE on detonation |
| explosion damage | 10 | flat damage to each enemy in radius |
| knockback | `±7, -7` | survivors blown horizontally/up |
| objAtk | `{14:1}` | unused for damage — it explodes, not attacks |

**Formulas**
- Detonation gated by `fuseTimer >= 60` while target stays in `atkRange`.

**Description vs code**
- No in-game description exists; nothing to compare. (Killing it before the fuse fills cancels the blast entirely — `onDie` early-returns when `!selfDestruct`.)

---

### RoboBomb2 — `RoboBomb2` (kindNum: none — enemy wave unit, not in unit_desc)
**TL;DR.** A cloaked suicide bomber with a bigger blast that blinks red as a fuse warning before it detonates.

**At a glance**
- **Role:** Basic enemy — cloaked suicide bomber (bigger blast, fuse warning)
- **Spawns cloaked** (`cloaking=true`) until engaged
- **Fuse:** warns at 40 ticks (blink red), detonates at 60 ticks
- **Blast:** radius 80, 15 flat damage each, survivors knocked back `±7,-7`
- **Kill-before-fuse ⇒ no explosion**

**Passive / special — fuse, warning blink, detonation**
- Spawns cloaked (`setData` sets `cloaking=true`). Once in range, `fuseTimer++`.
- **Warning phase:** at `fuseTimer >= fuseWarning (40)` it blinks red/white per ~2 ticks: `tint = (fuseTimer>>1 & 1) ? 16724787 : 16777215`.
- At `fuseTimer >= fuseDelay (60)` it forces tint white, sets `selfDestruct`, `die()`s, and spawns `RoboExplode` (`start(100)`).
- `onDie()` (if self-destructed): enemies within radius **80** take **15** flat damage (`doDamage(i,15)`); survivors get `blow(±7, -7)`.

**Base ↔ RoboBomb1 deltas**
- +cloak on spawn, +20-tick red-blink telegraph, radius 80 (vs 70), damage 15 (vs 10).

**Key values**
| variable | value | meaning |
|---|---|---|
| fuseDelay | 60 | ticks in-range to detonate |
| fuseWarning | 40 | tick at which it starts blinking red |
| cloaking | true | starts hidden until engaged |
| explosion radius | 80 | px AoE (bigger than RoboBomb1's 70) |
| explosion damage | 15 | flat damage each (vs RoboBomb1's 10) |
| knockback | `±7, -7` | survivor knockback |
| warn tint | `16724787` red / `16777215` white | blink colors |

**Formulas**
- Blink: `tint = (fuseTimer>>1 & 1) ? red : white`; detonate at `fuseTimer >= 60`.

**Description vs code**
- No in-game description exists; nothing to compare. (Same "no kill ⇒ no boom" rule — `onDie` returns unless `selfDestruct`.)

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


# Raid bosses

### GolemKing — `GolemKing` (kindNum: none — raid boss, not in unit_desc)
**TL;DR.** A teleporting heavy slammer that double-taps its normal, drops pillar and radial slams, charges across the field, then vanishes underground and re-emerges with a massive 480-radius slam.

**At a glance**
- **Role:** Boss (raid) — teleporting heavy slammer
- **Spine boss** (`raids/raid1/Golem`, `spineTimeScale=.8`, wander enabled, `hitHeight=180`, weak point = `Head` bone, offset −25)
- **6 skill slots**, `skillRatio=[.78,.6,.42,.26,.12,0]` (2 forced normals)
- **Signature:** teleport → relocate → emerge-slam (radius 480, the biggest hit in its kit)
- **Heavily damped knockback** `BLOW_SCALE = 0.75*0.6 = 0.45`

**Normal attack — att1 (double-tick slam)**
- AoE at the `R_Arm_01` bone, radius **200**, up to **80** targets, `random.range(1,2.5)` dmg + per-target knockback.
- Queues a **second tick** `ATT1_SECOND_TICK_DELAY=10` ticks later that repeats the slam — so the "normal" attack double-hits.

**Skill — att3 (radial slam)**
- `radialBlow` at self, radius **300**, blow power 3–12.

**Skill — att5 (pillar barrage)**
- For each of **9** `stone_pillar_0X` bones, a radius-**70** blast (up to **10** targets, `random.range(1.4,2.8)` dmg + knockback).

**Skill — att2 (charge)**
- Locks facing toward aggro/centroid and **slides forward** at `ATT2_CHARGE_SPEED=3` for `ATT2_DURATION_FRAMES=120`, doing a radius-**80** hit (≤5 targets, `random.range(1.5,2.5)`) every `ATT2_TICK_INTERVAL=3` frames at an offset point.

**Skill — teleport (skill `SKILL_TELEPORT=5`)**
- Plays `teleport_out`, becomes `attackable=false` + `isUntagetable`, freezes player units in place (`freezeAlliesInPlace`).
- Stays underground `TELEPORT_UNDERGROUND_FRAMES=120` ticks, **relocates randomly** within wander bounds, plays `teleport_in`.
- **Emerges with a huge slam:** `emergeRadialBlow` radius **480**, power **15.2–24.3** (vh 10.6–18.2) — the biggest hit in its kit.
- `escapeSkill()` ⇒ teleport.

**Passive / special**
- Inherits full `BaseRaidUnit` CC-immunity, `weight=5`, raid-stun weak-point system.
- During teleport it is `attackable=false` + untargetable for the 120 underground ticks, and freezes player units' positions.

**Buffs & debuffs (to enemies)**
- Knockback on nearly every hit; teleport freezes player units' positions. No stun/poison.

**Key values** (`zt(O2,…)`)
| variable | value | meaning |
|---|---|---|
| BLOW_SCALE | `0.75*0.6` = 0.45 | knockback multiplier (heavily damped) |
| skillRatio / numForSkillAttack | `[.78,.6,.42,.26,.12,0]` / 2 | 6-slot pick; 2 forced normals |
| ATT1_RADIUS / MAX_TARGETS / DAMAGE | 200 / 80 / `1–2.5` | main slam |
| ATT1_SECOND_TICK_DELAY | 10 | ticks until the repeat slam |
| ATT3_RADIUS / POWER | 300 / `3–12` | radial slam |
| ATT5 pillars | 9 bones, r70, ≤10 tgt, `1.4–2.8` dmg | pillar barrage |
| ATT2 charge | speed 3, 120 frames, r80, ≤5 tgt, `1.5–2.5`, tick 3 | moving charge |
| TELEPORT_UNDERGROUND_FRAMES | 120 | time hidden/untargetable |
| EMERGE_RADIUS / POWER | 480 / `15.2–24.3` (vh 10.6–18.2) | emergence slam (biggest) |

**Formulas**
- `BLOW_SCALE` doubly damped (0.75×0.6) so its knockbacks are short despite large power numbers.
- Emergence uses the same `radialBlow` with the EMERGE_* constants.

**Description vs code**
- No in-game description exists for raid bosses; nothing to compare.

### HarpyKing — `HarpyKing` (kindNum: none — raid boss, not in unit_desc)
**TL;DR.** A flying raid boss that only targets air, divebombs squads, slams down tornadoes, and unleashes feather barrages — pure knockback and lingering AoE, no stun.

**At a glance**
- **Role:** Boss (raid) — flying air-only diver / feather-storm caster
- **Spine boss** (`raids/raid1/Harpy`, `spineTimeScale=.84`, wander enabled, `airTargetOnly=true`, `hitHeight=200`)
- **5 attack slots**, `skillRatio=[.75,.55,.35,.15,0]`; `pickSkill()` remaps skill 1 → 0 (extra dashing normal)
- **Signature:** feather barrage (7 bursts × 20 feathers) + lingering tornadoes
- **Knockback scalar** `BLOW_SCALE=0.75`

**Normal attack — att1 (dive)**
- Dashes to a random alive *corp* (squad) center; during the hover window tracks that corp (`ATT1_HOVER_SPEED 3` from frame 20).
- On each hit event deals up to **7** hits (`ATT1_HITS_PER_EVENT`) of `random.range(1,2)` within radius **100**.

**Skill — att2 (slam + tornadoes)**
- `blow`s every enemy within 300×200, then `spawnSlamTornadoes()` drops **1 tornado** (2 after `TORNADO_TWO_AFTER_FRAMES=5400` battle-frames).
- `HarpyTornado`: ellipse **70×56**, **1200**-tick duration, deals **`TORNADO_DAMAGE_PERCENT=0.5`** (percent-style tornado damage); follows an aggro/random corp center.

**Skill — att4 (cone knockback)**
- Forward cone (radius **300**, half-angle **π/4**): `random.range(1,2)` dmg + `knockBack(power 8–14, dur 12)` to non-immovable enemies in the cone. Facing locked during it.

**Skill — att5 (feather barrage)**
- During the att5 anim fires **7 bursts** (at spine frames 28–40) of **20 feathers** each (`HarpyFeather`, `random.range(1.2,2.5)` dmg) radiating from the `shout` bone at corp/aggro targets.
- First `FEATHER_AGGRO_BURSTS=3` bursts prefer the highest-aggro corp.
- `escapeSkill()` ⇒ skill 4.

**Passive / special**
- Inherits full `BaseRaidUnit` CC-immunity, `weight=5`, raid-stun system.
- `airTargetOnly` + `hitHeight=200` mark it as a true aerial boss; the `pickSkill` 1→0 remap makes slot 1 effectively an extra dashing normal.

**Buffs & debuffs (to enemies)**
- Knockback: att2 slam `blow` and att4 cone (power 8–14, dur 12).
- DoT: lingering tornadoes (0.5 percent-style, 1200t). No stun/freeze.

**Key values** (`zt(T2,…)`)
| variable | value | meaning |
|---|---|---|
| BLOW_SCALE | 0.75 | knockback multiplier |
| ATT1_RADIUS / HITS_PER_EVENT / DAMAGE | 100 / 7 / `1–2` | dive multi-hit |
| ATT1_HOVER_SPEED / START_FRAME | 3 / 20 | corp-tracking hover |
| ATT4_RADIUS / CONE_HALF_ANGLE | 300 / `π/4` | cone sweep |
| ATT4_KNOCKBACK power/dur | `8–14` / 12 | cone knockback |
| FEATHER_PER_BURST / fire frames | 20 / `[28,30,32,34,36,38,40]` | feathers/burst, 7 bursts |
| FEATHER_DAMAGE | `1.2–2.5` | per feather |
| FEATHER_AGGRO_BURSTS | 3 | first bursts target aggro corp |
| TORNADO (radius/dur/dmg%) | 70×56 / 1200 / 0.5 | slam tornado AoE |
| TORNADO_TWO_AFTER_FRAMES | 5400 | battle-frame threshold for 2 tornadoes |

**Formulas**
- Cone test: `dirToEnemy · facing ≥ cos(π/4)`.
- Tornado uses `setMoveTargetProvider` to chase a corp center.

**Description vs code**
- No in-game description exists for raid bosses; nothing to compare.

---

### ScorpionKing — `ScorpionKing` (kindNum: none — raid boss, not in unit_desc)
**TL;DR.** A raid boss that dashes in to slam, then vacuums your team together and drowns them in poison — splash poison, a lingering poison pool, a poison-bullet volley, and a stunning slam.

**At a glance**
- **Role:** Boss (raid) — poison/pull bruiser
- **Spine boss** (`raids/raid1/Scorpion`, `spineTimeScale=.82`, wander enabled)
- **4 moves**, sequenced by `attackOrderList` then `skillRatio=[.78,.55,.3,0]` (2 forced normals)
- **Signature:** pull + poison splash that drops a 1200-tick poison pool
- **Knockback scalar** `BLOW_SCALE=0.7`

**Normal attack — att_01 (dash slam)**
- `startAttackDashTo` the target, then radial AoE at the `target_01` bone — radius **100**, `random.range(1,3)` damage to all in-radius, plus `radialBlow`.

**Skill 1 — att_02 (pull + poison splash)**
- Over the splash window, **pulls** all movable enemies toward the splash center within radius **200** at speed **12**.
- Then once applies a radius-**150** splash: `random.range(1.5,3)` damage + `poison(random 100–150)` to each, a `radialBlow`, and spawns a **lingering poison area** (`ScorpionPoisonArea`, ellipse 112.5×54, **1200**-tick duration, **1 dmg/sec**).

**Skill 2 — att_03 (poison-bullet volley)**
- Dashes to the enemy centroid, then fires up to **7 batches × 16 bullets** (`ScorpionPoisonBullet`, `random.range(1,2)` dmg each, staggered by `delay=floor(n/4)`) from the `tail_ball` bone at random targets.

**Skill 3 — att_04 (impact slam)**
- Radius-**110** impact: `random.range(1,3)` dmg + **stun 240** ticks to each.
- Radius-**200** `radialBlow`.
- On the `baby_att_hit` spine event, a radius-**100** `radialKnockback` (power 6–10, dur 18).
- `escapeSkill()` forces att_04.

**Passive / special**
- Inherits full `BaseRaidUnit` CC-immunity (doubly enforced), `weight=5`, raid-stun "groggy" weak-point system.

**Buffs & debuffs (to enemies)**
- Poison: att_02 splash applies stacks of 100–150; the pool deals 1 dmg/s for 1200t.
- Stun: 240t (att_04 impact).
- Knockback/blow on att_01, att_02, att_04.

**Key values** (all `zt(S2,…)`)
| variable | value | meaning |
|---|---|---|
| BLOW_SCALE | 0.7 | knockback multiplier |
| skillRatio / numForSkillAttack | `[.78,.55,.3,0]` / 2 | skill-pick thresholds; 2 forced normals |
| ATT1_RADIUS / DAMAGE | 100 / `1–3` | normal-attack AoE |
| ATT2_PULL_RADIUS / SPEED | 200 / 12 | vacuum pull |
| ATT2_SPLASH_RADIUS / DAMAGE | 150 / `1.5–3` | splash hit |
| ATT2_POISON_MIN/MAX | 100 / 150 | poison stacks applied |
| ATT2 poison-area | 112.5×54, dur 1200, 1 dmg/s | lingering pool |
| ATT3 bullets | 16/batch × 7 batches, `1–2` dmg | poison-bullet volley |
| ATT4_IMPACT_RADIUS / DAMAGE | 110 / `1–3` | slam core |
| ATT4_STUN_DURATION | 240 | ticks stunned |
| ATT4_BLOW_RADIUS | 200 | slam knockback radius |
| ATT4_KNOCKBACK (radius/power/dur) | 100 / `6–10` / 18 | baby-hit knockback |

**Formulas**
- Pull step `= min(dist, PULL_SPEED*(0.4 + (1 - dist/PULL_RADIUS)))` (closer = stronger pull).
- `radialBlow` impulse `= (min + rand*(max-min)) * BLOW_SCALE`.

**Description vs code**
- No in-game description exists for raid bosses; nothing to compare.

---


# Castle & structures

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

### Castle (base) — `BaseCastle` (`QQ`) — the player's structure
**TL;DR.** The defended HP structure that also auto-fires at enemies — totally CC-immune, immovable, and slowly self-heals.

**At a glance**
- **Role:** Castle (defended HP structure that also auto-fires)
- **Immovable** (`isImmovable=true`) and **immune to every status/CC**
- **Passive regen:** 0.5% max HP every 450 ticks (~7.5s) when not full
- **9-stage "on fire" visual** as HP drops in 10% steps
- Castle0/1/2 all extend this `QQ` base

**Normal attack**
- `doIdle()` finds the nearest enemy and attacks when in range; `numShot` (base 1) raised by upgrades.

**Passive / special**
- **Regen:** `execute()` increments `regenTimer`; every `REGEN_INTERVAL (450)` ticks it `heal(0.5, null, true)` ⇒ **0.5% of max HP** if not full.
- **Total CC-immunity:** `stun/knockBack/onHitted/addDotDamage/shock/freeze/curse/silence/poison/blow/binding` are all no-op overrides; `updateCrowdControl()` only decrements shield counters and returns false.
- **Damage-fire visual:** escalates through **9 levels** as HP drops in 10% steps (`updateDamageFire`: ≤10%→level 9 … ≤90%→level 1), adding/scaling fire at fixed `FIRE_POSITIONS`.
- **Clickable:** `onPointerDown` toggles the attack-range circle and shows the health bar for 225 ticks.

**Key values**
| variable | value | meaning |
|---|---|---|
| numShot (base) | 1 | shots per attack (raised by upgrades) |
| hpRegenPerSec | 0.001 | declared; effective regen below |
| REGEN_INTERVAL | 450 | ticks between regen ticks (~7.5s @1×) |
| regen heal | 0.5 (percent) | 0.5% of max HP each interval |
| damage-fire levels | 9 | fire stages at 10% HP increments |
| health-bar show time | 225 | ticks the bar stays after a click |

**Formulas**
- Regen `= maxHp*0.01*0.5` per 450 ticks.
- Player upgrades feed in via setters: `setPlayerNumShot(t) ⇒ numShot=1+t`; `setPlayerNumBounce(t) ⇒ numBounce=t`; `setPlayerAtkRange(t) ⇒ atkRange=baseAtkRange+t`; `setPlayerAtkDuration(t) ⇒ atkDuration=1e4/(baseAtkDuration+t)`.

**Description vs code**
- No unit description exists. The code matches the upgrade-key intent: `CASTLE_NAME_1 "Castle Durability"`, `_2 "Castle Range"`, `_3 "Castle Atk Speed"`, `_4 "Multi-Shot"`, `_5 "Bounce Shot"`. Total CC-immunity and immovability are the defining structural traits; HP only changes from incoming damage and the slow 0.5%/450-tick self-heal.

---

### Castle0 — `Castle0` (kindNum: none — player castle, not in unit_desc)
**TL;DR.** The starting fixed-loadout ranged tower — the only castle that hard-codes a 3-shot fire instead of relying on the player's Multi-Shot upgrade.

**At a glance**
- **Role:** Castle (the starting / fixed-loadout castle, RANGE)
- **Stationary** (`moveSpd=0`) ranged tower firing `SpeedArrow2`
- **Unique:** hard-codes `numShot=3` in `initializeData` (Castle1/2 leave it at base 1)
- **Fractional multi-shot:** extra shots beyond the integer count rolled by chance
- Hit/fire frame 23

**Normal attack — fractional multi-shot**
- Pulls `ceil(numShot)` attackable enemies; for each successive target rolls `random.chance(s)` with `s` starting at `numShot` and decrementing by 1 — e.g. `numShot=3.4` fires at targets 1/2/3 for sure and the 4th with 40% chance.
- `generateWeapon` spawns the arrow from a point 35px toward the target, carrying `bounceCount = numBounce`. Hit frame 23 (`objAtk={23:1}`).

**Passive / special**
- Inherits all `BaseCastle` traits (CC-immunity, immovable, regen, damage-fire).

**Key values**
| variable | value | meaning |
|---|---|---|
| numShot | 3 | hard-coded shot count (unique to Castle0) |
| moveSpd | 0 | immobile |
| radius / hitHeight | 22 / 67 | collision |
| weaponClass | `SpeedArrow2` | projectile fired |
| objAtk | `{23:1}` | hit/fire frame |
| numBlock | 0 | blocks no enemies |

**Formulas**
- Multi-shot: target `e` fired iff `random.chance(numShot - e)`.
- Weapon offset: `x+35*cos(angle), y-25+35*sin(angle)`.

**Description vs code**
- No unit description exists; nothing to compare. (Identical body to Castle1/Castle2 except for the `numShot=3` literal in `initializeData`.)

---

### Castle1 — `Castle1` (kindNum: none — player castle, not in unit_desc)
**TL;DR.** A mid-tier ranged castle identical to Castle0 except its shot count comes from player upgrades, not a built-in literal.

**At a glance**
- **Role:** Castle (RANGE, upgrade-driven shot count)
- **Stationary** ranged tower firing `SpeedArrow2`
- **Keeps base `numShot=1`** — relies on the player's Multi-Shot upgrade (`setPlayerNumShot`)
- Same fractional-multishot / bounce / fire-frame-23 logic as Castle0

**Normal attack**
- Same as Castle0: fractional-`numShot` multishot via `random.chance`, bounce via `numBounce`, fire frame 23 — but `numShot` is **not** set in `initializeData`, so it stays base 1.

**Passive / special**
- Inherits all `BaseCastle` traits (CC-immunity, immovable, regen, damage-fire).

**Key values**
| variable | value | meaning |
|---|---|---|
| numShot | (inherited 1) | not overridden — driven by upgrades |
| moveSpd / radius / hitHeight | 0 / 22 / 67 | same as Castle0 |
| weaponClass | `SpeedArrow2` | projectile |
| objAtk | `{23:1}` | fire frame |

**Formulas**
- Same multishot/bounce/offset formulas as Castle0.

**Description vs code**
- No unit description exists; nothing to compare. (Only delta vs Castle0 is the absence of the `numShot=3` literal.)

---

### Castle2 — `Castle2` (kindNum: none — player castle, not in unit_desc)
**TL;DR.** The top-tier castle skin — byte-for-byte the same firing code as Castle1, differing only in tier/art, with shot count driven by player upgrades.

**At a glance**
- **Role:** Castle (RANGE, top-tier skin, upgrade-driven)
- **Stationary** ranged tower firing `SpeedArrow2`
- **Keeps base `numShot=1`** (raised by player upgrades)
- Mechanically identical to Castle1 — difference is tier/cosmetic only

**Normal attack**
- Same method bodies as Castle1: fractional-`numShot` multishot, `numBounce` bounce, fire frame 23; `die()` re-shows the sprite. `numShot` not set in `initializeData` (stays base 1).

**Passive / special**
- Inherits all `BaseCastle` traits (CC-immunity, immovable, regen, damage-fire).

**Key values**
| variable | value | meaning |
|---|---|---|
| numShot | (inherited 1) | upgrade-driven |
| moveSpd / radius / hitHeight | 0 / 22 / 67 | identical to Castle1 |
| weaponClass | `SpeedArrow2` | projectile |
| objAtk | `{23:1}` | fire frame |

**Formulas**
- Same as Castle0/Castle1.

**Description vs code**
- No unit description exists; nothing to compare. (No mechanical delta from Castle1 in code; difference is tier/cosmetic.)

---

## Raid-boss base — `BaseRaidUnit` (`E2`/`A2`)
The three "King" bosses below all extend `BaseRaidUnit`. Shared framework (verified):
- **Spine-animated** (`spineKey`, `bossScale=1.3` default, per-boss `spineTimeScale`); state→animation mapping; a **weak-point bone** (head) drives flash/tint feedback.
- **Total CC-immunity**, doubly enforced: constructor sets `blowImmune/stunImmune/freezeImmune/knockImmune=true` AND `stun/freeze/curse/silence/binding/poison/shock/knockBack/blow` are no-op overrides. `weight=5`, `bossType=1`.
- **Raid-stun ("groggy") mechanic**: `applyRaidStun(frames)` is a *separate* system from normal CC — it sets `raidStunFrames`, plays the groggy animation, and freezes attacks for the duration (the intended "hit the weak point to stagger the boss" loop).
- **Skill selection** (`pickSkill`): if a queued `arrAttackTypeList` exists it shifts from that; else it walks a per-battle random **`attackOrderList`** sequence; else the first `numForSkillAttack (=2)` attacks are forced to the normal attack (skill 0), after which it rolls against the descending **`skillRatio`** thresholds to pick a skill index. `skill0` = normal attack; `skillN(i)` = skill `i`.
- **Wander AI** between attacks (`wanderEnabled`, `wanderInterval`, bounded by `wanderMin/MaxX/Y` = 100–540 / 200–950), plus `targetSwapChance` (re-roll target on each attack) and `wanderAfterAttackChance`.
- **Outgoing damage** is multiplied by `getRaidBossDamageMultiplier()` from the battle controller (a raid-difficulty scalar). `radialBlow/radialKnockback` push enemies away from an impact point, scaled by per-boss `BLOW_SCALE`.

---


# Reward / special

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


# Unreleased / cut

### (Druid / vine-controller) — `Druid1` (kindNum: no matching description in `/tmp/unit_desc.json`)
**TL;DR.** Crowd-control summoner that fires seeking tendrils which root enemies in damaging vines, auto-tangles already-CC'd foes, and spreads vines on kill.

**At a glance**
- **Role:** Crowd-control / area-denial summoner (root + DoT + spread)
- **Attack:** 4 seeking tendrils that crawl ≤280 and attach vines on contact (air units immune)
- **Vine:** roots 60t, deals 1.0× DoT every 30t over 150t total life
- **Auto-tangle:** vines any CC'd enemy within 400 each tick
- **On kill:** vines spread to ≤4 enemies within 150
- **Skill:** large `DruidDrill1` whirling projectiles toward two diverging targets

**In-game text**
- No "Druid"/vine/tangle entry in `/tmp/unit_desc.json` (exhaustively searched). Documented from code only.

**Normal attack**
- Spawns 4 seeking tendrils (`TENDRIL_COUNT`) in a `0.6π` fan toward the target; they crawl (speed 7, random-turning) up to 280, leaving trails.
- On contact (radius 24) `attachVine` on ground enemies (air immune). A vine grows for 10t, then roots (`binding(60)`) and deals 1.0× damage every 30t until total life 150t.

**Passive / special**
- `autoTangleCCEnemies()` each tick: any enemy within 400 already under knockback/blow/stun/freeze/shock gets auto-vined.
- `onKillEnemy` → `spreadAtPosition`: vines spread to ≤4 nearby enemies within 150.

**Skill — Druid drills**
- `skillMain` spawns large `DruidDrill1` projectiles (`whirlTotal=90`, scale 3, `setData(0.6)`) toward the main target + a divergent second target (`pickDivergentTarget`), or two random-direction drills if no enemies within 400.
- Each drill hits enemies within r50 for **0.6× damage + knockBack** (`±6, -2`, 24t), re-hitting the same target every 24t over its 90t life — damage + knockback only, no root (the `binding(60)` below is the *normal* vine attack, not the drill).

**Buffs & debuffs**
- `binding(60)` (root/immobilize) on vined enemies + periodic damage; auto-applies to already-CC'd enemies; spreads on kill. Air units exempt throughout.

**Key values**
| variable | value | meaning |
|---|---|---|
| TENDRIL_COUNT | 4 | tendrils per basic attack |
| TENDRIL_SPREAD_ARC | 0.6π | fan width |
| TENDRIL_SPEED / _MAX_DIST | 7 / 280 | crawl speed / max range |
| TENDRIL_HIT_RADIUS | 24 | contact radius to attach a vine |
| TENDRIL_MAX_TURN | 0.15 | per-tick random turn |
| VINE_GROW_FRAMES | 10t | grow time before binding |
| VINE_BIND_FRAMES | 60t | root/bind duration |
| VINE_TOTAL_LIFE | 150t | total vine lifetime |
| VINE_DMG_INTERVAL / _PCT | 30t / 1 | DoT every 30t at 1.0× |
| TANGLE_SEARCH_RANGE | 400 | auto-tangle + skill search range |
| SPREAD_RADIUS / SPREAD_COUNT | 150 / 4 | on-kill vine spread radius / max |
| DruidDrill1 whirlTotal / setData | 90 / 0.6 | skill drill duration / dmg mult |

**Formulas**
- DoT total ≈ `floor((150-grow)/30)` ticks × `VINE_DMG_PCT(1)` per vine while bound.

**⚠️ Description vs code**
- **No in-game description to compare** — kindNum text absent from `/tmp/unit_desc.json`. Behavior is a self-contained vine/root control system; flagged as undocumented.

**Notes**
- Distinct from Druid2 (`v2`, a 5-direction archer) which immediately follows it in the bundle. `normalSize=.75`, `evolSize=.8`. `objAtk={86:1}`, `objSkill={152:1}`. No explicit `evolStage` branch in this class body (evolution via book stats / weapon).

### (Forest-Guardian-slot variant) — `Aladin1` (kindNum: no matching description in `/tmp/unit_desc.json`)
**TL;DR.** Genie that throws gold coins which scatter, persist, and boost his damage; banking enough coins triggers a random wish (Gold / Blessing / Foresight).

**At a glance**
- **Role:** Ranged DPS / area-denial "genie" (buffer hybrid)
- **Attack:** throws 3 coins (Ⅱ 5) every 200t; coins persist 900t, global cap 50
- **Damage scaling:** +3% per nearby coin, cap 25 → up to +75%
- **Skill:** at mana ≥ 400 + ≥3 coins near, lifts coins into orbit and casts a random wish
- **Wishes:** Gold (extra coins + fast attacks) / Blessing (+15% ally ATK) / Foresight (next orbit ×2 dmg, ×1.3 range)

**In-game text**
- No `UNIT_NATK`/`UNIT_SATK` entry exists for an "Aladin"/genie/coin unit in `/tmp/unit_desc.json` (names 1–96 + specials checked exhaustively). Closest by slot order is Forest Guardian 81/84, whose text — "fires magic arrows…self Speed buff" — does NOT match this coin/wish behavior. Documented from code only.

**Normal attack**
- Wanders within a leash (`WANDER_RADIUS=180`); every 200t throws 3 coins (Ⅱ 5) `AladinCoin1` (`damagePercent=0.6`, life 900t) that scatter and persist on the ground. Global cap 50 coins across all Aladins.
- Damage scales with nearby coins: `goldDmgMultiplier = 1 + min(coins,25)×0.03` → up to +75%.

**Skill — coin orbit + wish (mana ≥ 400 & ≥3 coins ≤175)**
- `liftCoins()` then `launchCoinOrbit()` makes nearby coins orbit at radius 155, spawns the `AladinGenie1` effect, then `scheduleWish()`.
- After `WISH_TRIGGER_DELAY=180`, resolves one random wish of three:
  - **Gold:** spawn 8 extra coins + faster attacks for 300t (cooldown halved, ratio 0.5).
  - **Blessing:** +15% ATK to ALL allies for 480t (id `Aladin1_BLESSING_ATKDMG`).
  - **Foresight:** next orbit launch gets ×1.3 range and ×2 coin damage.

**Passive / special**
- `onHitted` re-launches a random idle coin defensively.
- Expired coins have a 10% chance to add 0.5s of rage energy (`COIN_EXPIRE_RAGE_CHANCE=0.1`).

**Buffs & debuffs**
- Blessing wish → Attack dmg +15% (value 0.15), 480t, every alive ally — id `Aladin1_BLESSING_ATKDMG` (removed on death). Gold-wish fast-attack is a direct `goldFastTimer`, no buff id.

**Base → Ⅱ**
- Coins per throw 3 → 5. (No other evolved code branch observed.)

**Key values**
| variable | value | meaning |
|---|---|---|
| ATK_COOLDOWN | 200t | between coin throws |
| ATK_COIN_COUNT | 3 (Ⅱ 5) | coins per throw |
| COIN_LIFE | 900t | coin lifetime |
| GLOBAL_COIN_CAP | 50 | max coins on field (all Aladins) |
| GOLD_DMG_PER_COIN / GOLD_MAX_COINS | 0.03 / 25 | +3% dmg per nearby coin, cap 25 → +75% |
| COLLECT_RADIUS / ORBIT_RADIUS | 175 / 155 | coin gather / orbit radii |
| maxMana | 400 | skill mana gate (also needs ≥3 coins near) |
| WISH_TRIGGER_DELAY | 180t | delay before wish resolves |
| WISH_GOLD_BONUS_COINS | 8 | extra coins on Gold wish |
| WISH_GOLD_FAST_FRAMES / _RATIO | 300t / 0.5 | fast-attack duration / cooldown multiplier |
| WISH_BLESSING_ATKDMG / _FRAMES | 0.15 / 480t | ally ATK buff value / duration |
| WISH_FORESIGHT_DMG_MULT / _RANGE_MULT | 2 / 1.3 | next-orbit dmg / range multipliers |
| AladinCoin1 damagePercent | 0.6 | per-coin damage |
| COIN_EXPIRE_RAGE_CHANCE / _SECONDS | 0.1 / 0.5 | rage energy on coin expiry |

**Formulas**
- `goldDmgMultiplier = 1 + min(coins,25)×0.03`. Blessing: ally `atkDmg` via additive buff value 0.15 → +15%.

**⚠️ Description vs code**
- **No in-game description to compare** — this kindNum's text is absent from `/tmp/unit_desc.json`. The class is a fully self-contained coin/wish system; flagged as undocumented.

**Notes**
- `static allCoins[]` is shared across all Aladin1 instances (global field). `normalSize=.75`, `evolSize=.8`, `weaponClass=AladinCoin1`. `objAtk={}` (no anim-frame hit; coins thrown procedurally in `execute`). `Aladin1_SAND_SLOW` enum id (260) exists but no slow call observed in this class body.

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

### CrowKnight1 — `CrowKnight1` (kindNum: not in desc.json — newer unit, no localized description)
**TL;DR.** Boss-tier flying archer that gains an orbiting crow on every kill — each crow auto-shoots and self-buffs the knight's damage and speed — then sacrifices the whole swarm in a kamikaze burst on skill.

**At a glance**
- **Role:** Boss / ranged DPS with stacking kill-fed pet swarm (self-buffing)
- **Attack:** homing `CrowKnightBullet1` (×1) + orbiting crows auto-fire (×0.4 each)
- **Kill loop:** +1 crow per kill (max 12); sheds 1 crow per 300t with no kill
- **Skill:** tops crows to 6, then launches ALL crows as kamikaze (×3.5) and empties the swarm
- **Stats:** atkRange 350, maxHp 1500, atkDmg 12, maxMana 500, air unit

**In-game text**
- (none — no `UNIT_NAME/NATK/SATK` entry for this class)

**Normal attack**
- Fires a homing `CrowKnightBullet1` (mult 1) at nearest enemy.
- Orbiting crows each auto-fire a bullet (×0.4) every 150 (+0–30 jitter) ticks at enemies within 220.

**Passive / special — the crow swarm**
- Spawns 0 crows at init.
- `onKillEnemy`: spawns one more crow (up to 12) and resets the decay timer.
- If no kill for 300 ticks, sheds one crow (down to base count 0).
- `refreshOrbitBuff` re-applies the self-buff whenever crow count changes.

**Skill — kamikaze swarm**
- objSkill frame 134: collects up to 12 enemies within 400; tops crows up to 6.
- Launches ALL orbit crows as "pending executions" — they arc out (`SKILL_FLY_FRAMES=20`) to enemy positions and fire `CrowKnightBullet1` at ×3.5, speed 14, staggered by 4 ticks.
- Consumes all orbit crows (`orbitCrows.length=0`).

**Buffs & debuffs** (SELF only, refreshed on every crow-count change)
- Attack speed: +6% per crow (value `n*0.06`), dur 9999 — id `CrowKnight1_ORBIT_ATKSPD`
- Attack damage: +4% per crow (value `n*0.04`), dur 9999 — id `CrowKnight1_ORBIT_ATKDMG`
- No enemy debuffs (pure damage).

**Key values**
| variable | value | meaning |
|---|---|---|
| ORBIT_BASE_COUNT / MAX | 0 / 12 | starting / max orbiting crows |
| ORBIT_ATKSPD_PER | 0.06 | +6% atk speed per crow (self) |
| ORBIT_ATKDMG_PER | 0.04 | +4% atk damage per crow (self) |
| ORBIT_BUFF_DUR | 9999 | ~permanent (refreshed each crow change) |
| ORBIT_FIRE_DMG | 0.4 | per orbit-crow auto-shot |
| ORBIT_FIRE_INTERVAL | 150 (+0–30) | ticks between orbit-crow shots |
| ORBIT_FIRE_RANGE | 220 | orbit-crow targeting radius |
| ORBIT_DECAY_FRAMES | 300 | ticks of no-kill before shedding a crow |
| SKILL_TARGET_MAX / RANGE | 12 / 400 | skill targets / radius |
| SKILL_MIN_CROWS | 6 | crows topped-up before skill launch |
| SKILL_DMG / BULLET_SPEED | 3.5 / 14 | kamikaze crow bullet mult / speed |
| SKILL_FLY_FRAMES | 20 | crow arc-out duration |
| SKILL_FIRE_INTERVAL | 4 | ticks between kamikaze shots |
| atkRange/maxHp/atkDmg/maxMana | 350 / 1500 / 12 / 500 | boss-tier base stats |

**Formulas**
- Self atkSpd `= orgAtkSpd*(1 + n*0.06)`; self atkDmg `= orgAtkDmg*(1 + n*0.04)`. With 12 crows ⇒ +72% atk speed, +48% atk damage.

**⚠️ Description vs code**
- No in-game description to compare. Mechanically a snowballing kill-fed swarm that buffs itself and converts into a burst nuke on skill (sacrifices all crows).

**Notes**
- Crow count is the central resource — kills add crows (more dps + bigger skill), idle time sheds them. Skill empties the swarm, so dps drops right after a cast until kills rebuild it.

---

### Druid (Druid2) — `Druid2` (kindNum: none — stub/placeholder)
**TL;DR.** An inert placeholder ranged unit: it fires a default attack but its skill does literally nothing.

**At a glance**
- **Role:** Ranged (stub — no functional skill)
- **Attack:** single default `doRangeAttack` (no `weaponClass` even assigned)
- **Skill:** dead expression — no damage, no buff, no projectile
- **Status:** registered class with `hasSkill=true` but an empty `skillMain`

**How it works**
- Minimal ranged unit: `unitType=RANGE`, `sheetName="Game1"`, `firePoint=(14,-14)`, `objAtk={76:1}`, `objSkill={112:1}`, `hasSkill=true`.
- `attackMain` is just `this.target && this.target.isAlive && this.doRangeAttack(this.target)` — a single default ranged hit, and **no `weaponClass` is assigned** in `initializeData`.
- `skillMain` is the **dead expression** `this.target && this.target.isAlive;` — evaluates truthiness and does nothing else.
- Only referenced in the className→class map (`[fx.Druid2]:v2`); no static constants, no kindNum wiring.

**Key values**
| variable | value | meaning |
|---|---|---|
| objAtk / objSkill frame | 76 / 112 | hit frames (skill frame unused) |
| firePoint | (14, −14) | muzzle offset |
| normalSize | 0.9 | render scale |
| weaponClass | (none set) | no projectile assigned |

**⚠️ Description vs code**
- No localized description to compare (no kindNum). The notable finding: `skillMain` is an **empty/no-op** despite `hasSkill=true` and an allocated skill frame range — effectively an inert placeholder, or a unit whose skill was stripped/never implemented in this build. Stated explicitly rather than inventing a match.

**Notes**
- Sister class `Druid1` (`Q1`) is fully implemented (vine/tendril entangle CC via `DruidTangle1`), so `Druid2` being empty is conspicuous — likely an unfinished evolved/variant or cut content in 1.11.42.

### GriffinRider1 — `GriffinRider1` (kindNum: not in desc.json — newer unit, no localized description)
**TL;DR.** High-flying ranged lancer that spreads its basic attacks across multiple enemies in front of it and fires bouncing super-spears on skill.

**At a glance**
- **Role:** Ranged DPS (flying multi-target lancer, bouncing skill spears)
- **Attack:** `GriffinSpear1`, spread across 2 (base) / 3 (Ⅱ) enemies in the facing direction
- **Skill:** 3 `GriffinSuperSpear1` casts (×1.5) that bounce/chain (`numBounce`); each spear knocks back + `stun(30)` on hit
- **Stats:** air unit, airHeight 75

**In-game text**
- (none — no `UNIT_NAME/NATK/SATK` entry for this class)

**Normal attack**
- `onAttackStartFrame`: gathers enemies in the facing direction within atkRange, up to 2 (base) / 3 (Ⅱ) targets (`getEnemiesForDirection`), front-loading the current target.
- `attackMain()` cycles `attackIndex` through that list, `doRangeAttack`-ing one per objAtk frame — spreading hits across 2/3 enemies.

**Skill — bouncing super-spears**
- objSkill frames {152,170,188} (3 casts): `onSkillStartFrame` collects enemies within 220 (target first).
- `skillMain` fires one `GriffinSuperSpear1` per cast via `fireSkillArrow`, dmg mult 1.5, `bounceCount = this.numBounce`. Each spear's `onHitMain` applies **knockBack (power 10) + `stun(30)`** on hit.
- Spear fire offset randomized `35 + 20*random`.

**Buffs & debuffs**
- The skill spears carry the CC: `GriffinSuperSpear1.onHitMain` applies **knockBack (power 10) + `stun(30)`** on each hit (verified in the weapon, not this class). No freeze; no ally buffs.

**Base → Ⅱ**
- Normal-attack target count 2 → 3. Skill fires 3 bouncing super-spears regardless of tier.

**Key values**
| | base | Ⅱ |
|---|---|---|
| normal targets | 2 | 3 |
| skill collect radius | 220 | 220 |
| skill spear dmg mult | 1.5 | 1.5 |
| skill spear bounces | `numBounce` | `numBounce` |
| objSkill | {152,170,188} | same |
| airHeight | 75 | 75 |

**Formulas**
- Normal attack distributes across `min(targetsInDir, 2|3)` enemies, one per objAtk frame.

**⚠️ Description vs code**
- No in-game description to compare. Behaviorally a Wyvern/Raptor-style multi-target flyer with a bouncing super-spear finisher; evolved adds one more normal-attack target (3 vs 2).

### Succubus1 — `Succubus1` (kindNum: not in desc.json — newer unit, no localized description)
**TL;DR.** Flying ranged attacker whose skill hastes only male allies — code names one of its two speed buffs "attack speed" but actually applies it as a second move-speed buff.

**At a glance**
- **Role:** Support buffer (gender-selective ally hastener) + ranged attacker
- **Attack:** flying ranged unit, fires `SuccubusBlade1` (objAtk frame 56)
- **Skill:** buffs every alive **male** (`sex=="M"`) ally with move speed for 120t (~2s)
- **Quirk:** the "attack speed" buff is wired to move speed; net is +90% move speed, zero atk-speed

**In-game text**
- (none — no `UNIT_NAME/NATK/SATK` entry in en.json or unit_desc.json)

**Skill — love buff (male allies only)**
- objSkill frame 101: iterates `allyList`; for each alive ally with `sex=="M"`, calls `showLoveShield(120)`.
- `showLoveShield(t)` applies NO damage shield (misnomer) — it sets `numLoveShield=t` (120-tick timer) and grants two movement buffs.
- Spawns 20 `SuccubusLove` visual effects (cosmetic).

**Buffs & debuffs** (to male `sex=="M"` allies only — distinct ids ⇒ stack additively)
- Move speed: +50% (value 0.5), 120t (~2s) — id `Succubus1_MOVESPEED_BUFF`
- "Attack speed": +40% (value 0.4), 120t — id `Succubus1_ATTACKSPEED_BUFF`, but applied via `addMoveSpeedBuff` (see ⚠️)

**Key values**
| variable | value | meaning |
|---|---|---|
| love-buff duration | 120 | ticks (~2s @ 1×) |
| MOVESPEED buff value | 0.5 | +50% move speed |
| "ATTACKSPEED" buff value | 0.4 | +40% — but applied as a MOVE-speed buff |
| airHeight | 40 | flying unit |
| love-effect count | 20 | cosmetic SuccubusLove sprites |

**Formulas**
- `moveSpd = orgMoveSpd*(1 + 0.5 + 0.4)` ⇒ effectively +90% move speed (two distinct buff ids ⇒ summed).

**⚠️ Description vs code**
- No in-game description to compare. CODE-INTERNAL quirk: the buff named `Succubus1_ATTACKSPEED_BUFF` is applied via `addMoveSpeedBuff`, not `addAttackSpeedBuff` — it grants movement speed, NOT attack speed. Net = +90% move speed and **zero atk-speed change**. Also `showLoveShield` is a misnomer: no damage mitigation, only the speed buffs.

**Notes**
- Gender-gated: only buffs male allies. Re-cast doesn't stack same-id (max kept) but refreshes uptime.

---

