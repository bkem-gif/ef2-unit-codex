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
