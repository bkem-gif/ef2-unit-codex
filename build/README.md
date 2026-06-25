# Build pipeline

The codex outputs (`../unit-codex.html` and `../UNIT-MECHANICS.md`) are **generated** from the files here.

## Regenerate the outputs (no game files needed)

```sh
python3 build/build_codex.py
```

It reads `data/units2_part*.md` (the per-unit content), `intro.md` (the combat-framework + key-findings
preamble), and `icon_map.json` (kindNum → icon code), and writes `../unit-codex.html` + `../UNIT-MECHANICS.md`.
Run it after editing a unit's writeup, the intro, or the icon map. (Paths are relative to the script, so the
working directory doesn't matter.) Pure-Python stdlib — no dependencies.

## Files

| Path | What it is |
|---|---|
| `build_codex.py` | the builder (parses the parts, renders the HTML + Markdown) |
| `intro.md` | the framework + key-findings preamble prepended to both outputs |
| `icon_map.json` | kindNum → `EFUnits/` image code (visually verified) |
| `data/units2_part*.md` | the per-unit content the builder reads (8 chunks) |
| `data/units_part*.md` | the raw first-pass extraction (provenance; reformatted into `units2_*`) |
| `data/unit_classmap.json` | className → bundle class-variable (extraction scaffolding) |
| `data/unit_desc.json` | kindNum → in-game NAME / NATK / SATK text |
| `framework.md` | the spec the extraction pass followed (traces the game bundle) |
| `reformat.md` | the spec the reformat pass followed (`units_*` → digestible `units2_*`) |

## Full regeneration for a new game version

The per-unit content was reverse-engineered from the EF2 game bundle
(`runtime/bundles/.../assets/index.js`, v1.11.42) — **not included here** (it's game code). To rebuild
against a newer bundle:

1. Re-extract scaffolding from the new bundle: `unit_classmap.json` (the unit class registry) and
   `unit_desc.json` (`UNIT_NAME/NATK/SATK_*` from the locale JSON).
2. **Extraction pass** — for each chunk of unit classes, trace the bundle per `framework.md` →
   `data/units_part*.md`.
3. **Reformat pass** — restructure each per `reformat.md` → `data/units2_part*.md`.
4. `python3 build/build_codex.py`.

Steps 1–3 need the game bundle plus an agent/LLM to do the tracing; step 4 (the builder) is pure and offline.
