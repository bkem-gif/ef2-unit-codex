# EF2 Unit Mechanics Codex

A code-derived reference for **how every unit in Endless Frontier 2 works** — combat behaviour,
hard-coded values, formulas, and buffs — each paired with its in-game description and a **validated
delta** wherever the two disagree. Reverse-engineered (read-only) from the EF2 game bundle (v1.11.42);
covers **96 unit classes across 116 `kindNum`s**.

## Open it

Open **`unit-codex.html`** in any browser. It's self-contained — live search, category/role filters, a
**"deltas only"** toggle, and collapsible per-unit cards with art. Keep the **`EFUnits/`** folder beside it
so the icons load.

## Contents

| File | What it is |
|---|---|
| `unit-codex.html` | the interactive browser (search / filter / expand) |
| `UNIT-MECHANICS.md` | the same content as Markdown — the readable source |
| `EFUnits/` | unit icons + [`ICON-MAP.md`](EFUnits/ICON-MAP.md) (which icon is which unit) |

## What each unit card shows

A plain-English one-liner, an **at-a-glance** box (role + the numbers that matter), then only the sections
that apply — **Normal attack / Skill / Passive / Buffs / Base → Ⅱ / Key values / Formulas** — and a
**✓ Matches** or **⚠️ Description vs code** verdict.

The codex flags **15 units whose in-game blurb doesn't match the code**, e.g.:
- **Drums of the Battlefield** claims it buffs **ATK** — the code only buffs attack speed + move speed.
- **Priest's** "chance to stun" on its basic attack isn't implemented; **Gunner's** stun (undocumented) is.
- **Green Eagle** has an undocumented poison; **Unicorn Archer's** evolved bonus shot is dead code.
- A batch of internal-name vs display-name mismatches (`TigerRider1` = Forest Guardian, `GreatMage1` = Fire Mage, …).

## How the buff system works (quick reference)

Buffs are `add<Stat>Buff(id, value, durationTicks)`. Attack-speed / move-speed / damage are **multiplicative**
(`stat = base × (1 + value)`, so `value 1.2` = +120%); crit & range-evade are **additive**. Same buff-id
doesn't stack (max kept); different ids sum. Time is in game ticks (~60/sec at 1× speed). The full framework
is in the codex's "Combat framework & formulas" panel.

## License & provenance

The documentation in this repo (`UNIT-MECHANICS.md`, `unit-codex.html`) is **MIT** (see [LICENSE](LICENSE)).
The images in `EFUnits/` are **Endless Frontier 2 game art © its developer**, bundled for convenience and
**not** covered by the MIT license. The mechanics documented here are facts derived from observing the game;
the game and its runtime are not included.
