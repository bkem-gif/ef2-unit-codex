#!/usr/bin/env python3
"""Regenerate `emblem_catalog.json` from the game's decrypted books.

Needs the game data dump and a mounted bundle — neither is in this repo. Mirrors
`extract_base_stats.py`: run it only when moving to a new game version, then commit the JSON so
`build_emblems.py` can render the page with no game files present.

Sources, in order of authority:
  - books-latest.json  : EMBLEM (6), EMBLEM_SKILL (76), RUNE (137) — live server books,
                         captured read-only by the `book-capture` plugin.
  - RUNE_GRADE / RUNE_SUB : NOT sourced from the server. The server never ships these two books;
                         EmblemDataManager.ensureLoaded() falls back to tables baked into the app
                         bundle, so those baked-in values ARE the live values. Verified by seeding
                         a sentinel book into the cache and watching it override the fallback.
  - locales/en.json    : the player-facing English tooltips.

The player's own equipped loadout and rune inventory are deliberately NOT emitted — this is
reference material, not a personal build.

Usage:  python3 build/extract_emblem_catalog.py [books-latest.json] [bundle-assets-dir]
"""
import json, os, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
BOOKS = sys.argv[1] if len(sys.argv) > 1 else \
    "/Users/briankemery/ef2-clan-war-simulator/data/live/books-latest.json"
BUNDLE = sys.argv[2] if len(sys.argv) > 2 else \
    "/Users/briankemery/EF2-Browser-Runtime/EF2-Browser-Runtime-main/runtime/bundles/mounted/1.12.80/assets"

books = json.load(open(BOOKS))
C = books["collections"]
LOC = json.load(open(f"{BUNDLE}/locales/en.json"))

# --- grades: engine-resolved (bundle fallback pQt), English names from the locale ---------------
GRADE_ROWS = [(1, 5, 100), (2, 5, 300), (3, 5, 900), (4, 5, 2500), (5, 5, 7000), (6, 0, 0)]
grades = [{"grade": g, "name": LOC.get(f"EmblemGradeName{g}"), "mergeCount": mc,
           "mergeCoin": coin, "subOption": g >= 5} for g, mc, coin in GRADE_ROWS]

# --- sub-options: engine-resolved (bundle fallback gQt) -----------------------------------------
SUB_ROWS = [(1, 1, [2, 5], 4, 7), (2, 2, [1, 2, 3, 4, 5], 5, 8), (3, 3, [1, 3, 4], 4, 7),
            (4, 4, [2, 4, 5], 3, 5), (5, 9, [1, 3], -3, -5), (6, 35, [1, 2, 3, 4, 5, 6], 3, 5),
            (7, 13, [1, 3], 2, 4), (8, 31, [4, 5], 0.0025, 0.005), (9, 41, [6], 4, 7),
            (10, 43, [6], 3, 5)]

ES = {r["kindNum"]: r for r in C["EMBLEM_SKILL"]["rows"]}
EM = {r["kindNum"]: r for r in C["EMBLEM"]["rows"]}
RU = C["RUNE"]["rows"]


def endesc(k):
    return LOC.get(f"EmblemDesc{k}")


def parse_emblems(v):
    return [v] if isinstance(v, int) else [int(x) for x in str(v).split("|") if x]


subs = [{"subId": sid, "skillRef": sr, "emblems": emb, "value5": v5, "value6": v6,
         "mech_id": ES.get(sr, {}).get("id"), "desc_en": endesc(sr)}
        for sid, sr, emb, v5, v6 in SUB_ROWS]

emblems = []
for k in sorted(EM):
    e, p, a = EM[k], ES.get(EM[k]["pSkill"], {}), ES.get(EM[k]["aSkill"], {})
    emblems.append({
        "kindNum": k, "name_en": LOC.get(f"EmblemName{k}"), "className": e["className"],
        "name_ko": e["name"], "role": e["role"], "slot": e["slot"], "runeType": e["runeType"],
        "passive": {"skillRef": e["pSkill"], "id": p.get("id"), "value": e["pValue"],
                    "desc_en": endesc(e["pSkill"]), "category": p.get("category"),
                    "target": p.get("target")},
        "active": {"skillRef": e["aSkill"], "id": a.get("id"), "value": e["aValue"],
                   "cooldown_s": e["aCool"], "duration_s": e["aDur"],
                   "desc_en": endesc(e["aSkill"]), "target": a.get("target")},
    })

TYPE2EMB = {e["runeType"]: e["kindNum"] for e in EM.values()}

runes = []
for r in RU:
    s = ES.get(r["skillRef"], {})
    vals = [float(x) for x in str(r["value"]).split("|")]
    allowed = parse_emblems(s.get("emblems", "")) if s else []
    emb = TYPE2EMB.get(r["type"])
    runes.append({
        "kindNum": r["kindNum"], "className": r["className"], "name_ko": r["name"],
        "type": r["type"], "emblem": emb, "emblem_name": EM[emb]["className"] if emb else None,
        "skillRef": r["skillRef"], "mech_id": s.get("id"), "category": s.get("category"),
        "target": s.get("target"), "merge": s.get("merge"), "condition": s.get("condition"),
        "minGrade": s.get("minGrade"), "filter": r.get("filter"), "param": r.get("param", 0),
        "values": vals, "desc_en": endesc(r["skillRef"]),
        # the allowlist the engine does NOT enforce at apply time (verified against the engine)
        "allowlist": allowed, "allowlist_violation": bool(emb and allowed and emb not in allowed),
        # a grade whose value is 0 is a hard skip in resolve(): `if (c && 0 !== s)`
        "dead_grades": [i + 1 for i, v in enumerate(vals) if v == 0],
    })

mechanics = [{"skillRef": k, "id": r["id"], "category": r["category"], "type": r["type"],
              "target": r["target"], "merge": r["merge"], "condition": r["condition"],
              "minGrade": r["minGrade"], "sigFor": r["sigFor"],
              "emblems": parse_emblems(r["emblems"]), "desc_en": endesc(k),
              "desc6_ko": r.get("desc6", ""),
              "carrier_runes": [x["kindNum"] for x in runes if x["skillRef"] == k]}
             for k, r in sorted(ES.items())]

cat = {
    "_meta": {
        "captured_at": books.get("_captured_at"),
        "bundle": "1.12.80 (mounted)",
        "grade_source": "engine-resolved from the bundle's baked-in tables — the server ships no "
                        "RUNE_GRADE/RUNE_SUB (verified by sentinel-book control)",
        "engine_constants": {"FPS": 60, "COOL_CUT_MAX": 0.8},
        "resolver_facts": [
            "RuneLoadout.resolve() dedupes by rune kindNum — duplicate copies of the same rune do not stack",
            "the ONLY equip gate is rune.type !== emblem.runeType; EMBLEM_SKILL.emblems is never checked at apply time",
            "a grade whose value is 0 is a hard skip, which also suppresses that rune's sub-option",
            "EMBLEM_SKILL.minGrade is never read by any code; availability is isRuneAvailableAtGrade = (value !== 0)",
            "activeCool/activeDur/activePower (target SELF) are siphoned out before routing and never appear as effects",
        ],
    },
    "grades": grades, "subs": subs, "emblems": emblems, "runes": runes, "mechanics": mechanics,
}
json.dump(cat, open(f"{HERE}/emblem_catalog.json", "w"), ensure_ascii=False, indent=1)

print(f"wrote emblem_catalog.json — grades={len(grades)} subs={len(subs)} "
      f"emblems={len(emblems)} runes={len(runes)} mechanics={len(mechanics)}")
print(f"  allowlist violations: {sum(1 for r in runes if r['allowlist_violation'])}")
print(f"  runes with >=1 zero-value grade: {sum(1 for r in runes if r['dead_grades'])}")
print(f"  runes by emblem: {dict(Counter(r['emblem_name'] for r in runes))}")
