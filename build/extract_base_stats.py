#!/usr/bin/env python3
"""Extract per-unit base stats from the game's decrypted `UNIT` book into base_stats.json.

The game data dump is NOT in this repo (it's server data, like the bundle). Point this at
the decrypted books file — pass a path, set $EF2_DUMP, or rely on the default location:

    python3 build/extract_base_stats.py [path/to/books-decrypted.json]

Joins by `className` (base row = lowest evolStage, Ⅱ row = next), and keeps only the fields
chosen for the codex: Core combat + Survivability/immunities. Output is consumed by
build_codex.py to render each unit's "Base stats" block. Re-run when the game data updates.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "base_stats.json")
DUMP = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("EF2_DUMP")
        or os.path.expanduser("~/EF2-Browser-Runtime/dump/books-decrypted.json"))

# Core combat + Survivability/immunities (magicShield/physicalShield/numRevive are 0 for every
# unit in the shipped book — in-battle shields come from skills/buffs, not base stats — so dropped).
FIELDS = ["hp", "atkDmg", "atkSpd", "moveSpd", "atkRange", "def", "phyDef", "magDef",
          "recovery", "dmgType", "stunImmune", "freezeImmune", "blowImmune", "knockImmune",
          "cloaking", "detect"]

def main():
    rows = json.load(open(DUMP, encoding="utf-8"))["UNIT"]
    fam = {}
    for r in rows:
        fam.setdefault(r["className"], []).append(r)
    out = {}
    for cls, rs in fam.items():
        rs = sorted(rs, key=lambda r: r.get("evolStage", 0))
        pick = lambda r: {k: r.get(k) for k in FIELDS}
        out[cls] = {"base": pick(rs[0]), "evol": (pick(rs[1]) if len(rs) > 1 else None)}
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
    print(f"wrote {OUT}: {len(out)} classes from {DUMP}")

if __name__ == "__main__":
    main()
