# EF2 unit-mechanics extraction — framework reference (READ FIRST)

You are reverse-engineering one chunk of EF2's combat units from the game bundle to document
**how each unit works** — mechanics, formulas, and hard-coded values — and the delta vs the
in-game description. Be rigorous: quote ACTUAL constants from the code, never guess.

## Files
- Bundle (minified, ~6MB): `runtime/bundles/mounted/1.11.42/assets/index.js`  (relative to repo root `<EF2-Browser-Runtime>`)
- English locale: `runtime/bundles/mounted/1.11.42/assets/locales/en.json`
- className → classVar map: `build/data/unit_classmap.json`
- kindNum → {NAME, NATK, SATK} descriptions: `build/data/unit_desc.json`

## How to locate a class
Each unit is an ES class registered with `Kt(<classVar>,"<ClassName>")`. To find one, grep the bundle
(byte offsets) for `this.className=fx.<ClassName>` (inside its `initializeData`) AND `Kt(...,"<ClassName>")`
(the end of the class). Read the whole class body between them.
IMPORTANT: `grep -aob` byte offsets must be read with Python byte-slicing, NOT char-slicing, because of
multi-byte chars: `data=open(F,'rb').read(); print(data[a:b].decode('utf-8','replace'))`.

## The combat framework (already established)
- **Units extend base class `qQ`.** Each class typically defines: `initializeData()` (sets `className`,
  `radius`, `hitHeight`, animation frame ranges `idleFrames/moveFrames/attackFrames/skillFrames/dieFrames`
  as `new QK(start,end)`, `objAtk` = `{frameIndex: hitCount}` i.e. which attack-anim frame fires the hit,
  sounds, `hasSkill`), `setData(t,i,s,e)` (sets `evolStage`; many do `this.evolved=this.evolStage>=1`),
  `execute()` (runs every game tick; often decrements a cooldown), and `attackMain()` (the attack/skill action).
  Some override `skill()`, `onDie()`, `generateWeapon()` (spawn a projectile), etc.
- **Time is in game ticks** (~60/sec at 1× game speed; everything scales with the live game-speed multiplier).
  Cooldowns/durations are tick counts. `skillCoolDown` is decremented in `execute()` and gates the skill;
  many units randomize the FIRST cooldown (`this.skillCoolDown = N*this.random.next()`) so instances desync.
- **Attacking:** a unit attacks the nearest enemy in range; `atkDuration = 1e4 / atkSpd` is the attack
  interval; hits land on the `objAtk` frame(s). `generateWeapon(target, WeaponType)` spawns projectiles.
- **Buff system** — methods called on a unit (self or an ally), signature `(id, value, durationTicks[, refreshFlag])`:
  `addAttackSpeedBuff`, `addMoveSpeedBuff`, `addAttackDamageBuff`, `addDefenseBuff`, `addMaxHealthBuff`,
  `addCritMultiplierBuff`, `addCritChanceBuff`, `addRangeEvadeChanceBuff`.
  - **Stat formulas** (recomputed each tick): `atkSpd = orgAtkSpd*(1 + activeAttackSpeedBuff.value)`,
    `moveSpd = orgMoveSpd*(1 + activeMoveSpeedBuff.value)`, `critDmg = orgCritDmg + activeCritMultiplierBuff.value`
    (ADDITIVE), `critChance = orgCritChance + activeCritChanceBuff.value` (ADDITIVE),
    `rangeEvadeChange = orgRangeEvadeChange + activeRangeEavdeBuff.value` (ADDITIVE), `atkDuration = 1e4/atkSpd`.
    Damage/defense/maxHealth buffs follow the same `value` convention — VERIFY the exact formula for any you cite.
  - A buff `value` is the magnitude; for the multiplicative stats `value 1.2` ⇒ **+120%** (×2.2), `0.5` ⇒ +50%.
    `durationTicks` is the buff's `count`, decremented each tick, expires at <0.
  - **Aggregation (class `WQ`):** `.value = sum over DISTINCT buff-ids of the MAX value for that id`
    (positive buffs). So same id ⇒ NO stacking (max kept); the refreshFlag overwrites value+count; different
    ids ⇒ summed. Clamped to [min,max] (default [-1,10]).
- **Status effects on enemy targets:** `freeze(durationTicks)`, `stun(durationTicks)`, `stunAll(...)`,
  `knockBack(...)`. Also taunt/provoke, shields, and summons exist — read the actual call.
- **Targeting:** `this.allyList` (allies incl. self), enemy list; many skills gather a list, sort by squared
  distance, and affect the nearest `Math.min(MAX, n)` (e.g. drummer `SKILL_MAX_TARGETS=30`).
- **Localization:** `UNIT_NAME_<kindNum>` (display name), `UNIT_NATK_<kindNum>` (normal-attack text),
  `UNIT_SATK_<kindNum>` (skill text) — all in `build/data/unit_desc.json`. Match a class to its kindNum(s) by
  **behavior** (the description describes the code) + name. A class can map to MULTIPLE kindNums via evolution
  (e.g. `BigDrumer1` = kindNum 69 base + 78 evolved); list each and note base vs evolved values.

## Worked example (the quality bar) — `BigDrumer1` (kindNum 69/78, "Drums of the Battlefield")
Support unit; doesn't deal damage. `attackMain()` gated by `skillCoolDown` (reset to 500): gathers all alive
allies, sorts by distance, buffs the nearest `min(SKILL_MAX_TARGETS=30, n)` with `addAttackSpeedBuff(BUFF_ID=8001, s, dur, true)`
and `addMoveSpeedBuff(8001, s, dur, true)` where `s=1.2`(base)/`1.3`(evolved), `dur=350`(base)/`400`(evolved).
First cooldown randomized `500*random`. **Delta found & validated:** description says it buffs "ATK, attack
speed, movement speed" but the code calls ONLY `addAttackSpeedBuff`+`addMoveSpeedBuff` — there is NO
`addAttackDamageBuff`, so no raw-ATK buff. Multiple drummers share id 8001 ⇒ don't stack (max), only improve uptime.

## Output — write a markdown file with one section PER class, this exact template:

```
### <Display name(s)> — `<ClassName>` (kindNum: <n>[, <n2> evolved])
**Role:** <melee dps | ranged dps | mage | support/buffer | healer | tank | summoner | assassin | boss | basic enemy | castle | …>
**Description (in-game):**
- Normal (`UNIT_NATK_<k>`): "<verbatim>"
- Skill (`UNIT_SATK_<k>`): "<verbatim>"  (omit if none/empty)
**How it works (code):** <2–6 sentences: attack pattern, skill, targeting, projectiles/summons/status effects, conditions, evolved differences>
**Hard values:**
| variable | value | meaning |
|---|---|---|
| skillCoolDown | <n> | ticks between skill (≈ n/60 s at 1×) |
| <buff/dmg/range/count/etc.> | <n> | <meaning> |
**Formulas:** <only those relevant to this unit, e.g. `atkSpd=orgAtkSpd*(1+1.2)` ⇒ +120%; or "n/a">
**Buffs/debuffs applied:** <each: stat, id, value(+how it maps to %), durationTicks, target scope/count — or "none">
**Δ description vs code:** <"none — matches" OR the specific mismatch, with what the code actually does. Be exhaustive and validate it.>
**Notes:** <evolved vs base deltas, randomized cooldowns, anything noteworthy. Omit if nothing.>
```

Rules: quote real constants only; if a class is a trivial basic attacker (no skill/buff), keep it brief but
still fill Role + how-it-works + any values. If you truly cannot find a class or its description match, say so
explicitly rather than inventing. Note `evolStage`-gated differences wherever present.
