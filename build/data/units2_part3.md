# EF2 unit mechanics — Part 3 (12 Elf/allied-faction units)

Source bundle: `runtime/bundles/mounted/1.11.42/assets/index.js`.
Constants below are quoted verbatim from the bundle (`zt(Class,"NAME",value)` static defs). Times are game ticks (~60/s at 1× game speed). "evolved" = `evolStage>=1`.

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
- **Tornado:** whirls 70t (Ⅱ 100t), 0.3× per-tick DoT

**In-game text**
- Normal: "Launches an energy ball to attack enemies from range."
- Skill: "Summons a tornado at the enemy's location, dealing sustained damage." (Ⅱ: "Summons a tornado for longer, hitting more enemies and dealing sustained damage.")

**Normal attack**
- Fires `GreenEnergyBall` with `numShot = 1.5` (Ⅱ 2.5).

**Skill — tornadoes**
- `skillMain` picks `t = 2·evolStage+2` targets → 2 base, 4 evolved: the locked target plus nearest enemies within 200.
- Spawns a `Twist` (tornado) on each via `spawnTwist`, each whirling for 70t (Ⅱ 100t), dealing 0.3× per-tick DoT.

**Base → Ⅱ**
- Basic numShot 1.5 → 2.5; skill targets 2 → 4; tornado whirl 70t → 100t ("for longer, hitting more enemies").

**Key values**
| | base | Ⅱ |
|---|---|---|
| numShot (basic) | 1.5 | 2.5 |
| skill target count | 2 (`2·0+2`) | 4 (`2·1+2`) |
| skill gather range | 200 | 200 |
| tornado whirl dur | 70t | 100t |
| Twist per-tick dmg | 0.3× | 0.3× |

**Formulas**
- Evolved skill targets `2·1+2 = 4` vs base `2·0+2 = 2`.

**✓ Matches description** — "for longer, hitting more enemies" = whirl 70→100 and targets 2→4 when evolved. (`OBJ_ATK` `{57:1}` and `OBJ_SKL` `{101:1}` frame sets identical base/evolved; only counts/durations differ.)

**Notes**
- `weaponClass=GreenEnergyBall` (`MagicalHitEffect`, speed 9). Tornado is weapon class `Twist`, spawned procedurally; drifts toward target then whirls in place. Twist deals sustained DoT, no stat debuff.

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
