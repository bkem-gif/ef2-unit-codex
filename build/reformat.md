# Per-unit reformat — make each section digestible (READ FIRST)

You are REFORMATTING already-extracted unit writeups into a cleaner, scannable shape. The data is
already correct in the source file — your job is **restructure for readability, losing NO quantitative
detail**. Do not re-research from scratch; work from the source section text. You MAY open the bundle
(`runtime/bundles/mounted/1.11.42/assets/index.js`, Python byte-slicing) only to disambiguate a confusing
sentence — but every hard value, formula, id, duration, multiplier, target count, and the validated delta
from the source MUST survive into your output.

## Goal
Replace dense run-on "How it works" paragraphs with a layered, skimmable structure: a one-line summary,
3–5 at-a-glance facts, then short labelled sections (only the ones that apply). Simple units stay SHORT;
complex units get more sections. Adapt the shape to the unit.

## EXACT template — use these bold labels at the START of their own line (parser depends on it)
Omit any section that doesn't apply to a given unit. Keep bullets tight (one fact each).

```
### <Display name> — `<ClassName>` (kindNum: <n>[ · Ⅱ <n2>])     ← keep the header line as-is from source (you may tidy "69, 78 evolved" → "69 · Ⅱ 78")
**TL;DR.** <ONE plain-English sentence: what the unit is + its signature mechanic. No code identifiers.>

**At a glance**
- **Role:** <short role, e.g. Support buffer | Melee DPS | Ranged mage | Tank | Summoner | Boss | Basic enemy | Castle>
- <2–4 more compact facts that matter most: attack type, cadence/trigger, headline numbers (e.g. "+120% atk-speed → +130% Ⅱ", "every ~8.3s", "≤30 allies")>

**In-game text**
- Normal: "<verbatim UNIT_NATK>"
- Skill: "<verbatim UNIT_SATK>"   ← omit line if none

**Normal attack**          ← include only if it does something beyond a plain basic hit
- <bullets>

**Skill — <short name / trigger>**   ← e.g. "Skill — heavy strike (mana ≥ X)" or "Skill — the drum beat (every 500t)"
- <bullets: effect, targets, values; note evolved deltas inline as "(Ⅱ: …)">

**Passive / special**      ← only if present (on-kill effects, stacks, split-on-death, CC immunity, summons, telegraphs…)
- <bullets>

**Buffs & debuffs**        ← only if it applies any buff (self/ally) or debuff/CC (enemy)
- <stat>: <+X% or value>, <duration>t, <target scope> — id <N>

**Base → Ⅱ**               ← only if evolvable (two kindNums sharing the class)
- <what changes: value 1.2→1.3, duration 350→400, +1 target, extra hit-frame, etc.>

**Key values**
| variable | value | meaning |        ← for NON-evolvable units
|---|---|---|
   …OR, for EVOLVABLE units use base/Ⅱ columns:
| | base | Ⅱ |
|---|---|---|
| <metric> | <base> | <evolved> |
(Keep every meaningful gameplay constant. DROP pure noise: sprite scale, sound names, animation frame ranges — unless a frame index is the actual mechanic, e.g. an objAtk multi-hit.)

**Formulas**               ← only if non-obvious (e.g. the buff formula, a damage scaling). Skip "n/a".
- <formula, with what the number means, e.g. `atkSpd = orgAtkSpd × (1 + value)` → 1.2 = +120%>

**⚠️ Description vs code**  ← if there IS a validated mismatch: state it crisply (what the text says vs what the code does).
   …OR, if it matches:
**✓ Matches description**   ← one short line (you may note the evolved scaling if relevant).

**Notes**                  ← optional; only genuinely interesting extras (stacking quirks, dead code, name mismatches). Keep short.
```

## Rules
- **TL;DR** is mandatory and must be plain English (a player could read it) — this becomes the card's subtitle.
- The first **At a glance** bullet MUST be `- **Role:** <role>` (used for filtering).
- Prefer **% and seconds** in prose where helpful (ticks ≈ /60 s at 1×), but keep the raw tick/value in **Key values**.
- Express durations/cooldowns as `Nt (~Ns)` where useful.
- Convert buff `value` to a percent in prose (value 1.2 = +120%) but keep the raw value in the table.
- Every unit ends with either **⚠️ Description vs code** or **✓ Matches description** (never omit both).
- Don't invent. If the source flagged "no kindNum / no description", carry that forward (skip the In-game text section, and the delta line becomes a short note like "No localized description to compare").

## Worked example A — complex (drummer)
```
### Drums of the Battlefield — `BigDrumer1` (kindNum: 69 · Ⅱ 78)
**TL;DR.** Support drummer — pulses an attack-speed + move-speed buff to the whole team every ~8s; deals no damage.

**At a glance**
- **Role:** Support buffer (no attack)
- **Cadence:** every 500t (~8.3s); first pulse randomized so drummers desync
- **Buffs:** +120% atk-speed & +120% move-speed → **+130%** at Ⅱ
- **Targets:** ≤30 nearest allies (= your whole team)

**In-game text**
- Normal: "Supports allies by beating a drum instead of attacking."
- Skill: "Temporarily increases ATK, attack speed, and movement speed for all allied heroes."

**Skill — the drum beat (every 500t)**
- Buffs the nearest ≤30 allies with atk-speed + move-speed for 350t (~5.8s); **Ⅱ → 400t**.
- Both buffs use id 8001, so re-beats refresh rather than stack.

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

**Formulas**
- `atkSpd = orgAtkSpd × (1 + value)` → value 1.2 = +120%. Same for move speed.

**⚠️ Description vs code**
- Blurb claims an **ATK** boost, but the code calls only `addAttackSpeedBuff` + `addMoveSpeedBuff` — no `addAttackDamageBuff`, so raw ATK is **not** buffed.

**Notes**
- Multiple drummers share id 8001 ⇒ they don't stack strength (max-per-id rule), only extend uptime.
```

## Worked example B — simple (Infantry)
```
### Infantry — `FootMan1` (kindNum: 1 · Ⅱ 26)
**TL;DR.** Basic melee swordsman; its skill is a heavy strike with a chance to stun.

**At a glance**
- **Role:** Melee DPS
- **Attack:** basic sword on the nearest enemy
- **Skill:** heavy strike + chance to stun

**In-game text**
- Normal: "Strikes nearby enemies with a sword."
- Skill: "Delivers a powerful strike that damages enemies and has a chance to stun them."

**Skill — heavy strike**
- Deals ×1.5 damage (**Ⅱ ×2.5**), then 30% chance (**Ⅱ 50%**) to stun for 50t (**Ⅱ 60t**).

**Base → Ⅱ**
- Damage ×1.5 → ×2.5; stun chance 30% → 50%; stun 50t → 60t.

**Key values**
| | base | Ⅱ |
|---|---|---|
| skill damage | ×1.5 | ×2.5 |
| stun chance | 30% | 50% |
| stun duration | 50t | 60t |

**✓ Matches description** — evolved scales damage, stun chance, and stun duration exactly as "greater damage / higher chance" implies.
```

Now reformat every section in your assigned source file into this template.
