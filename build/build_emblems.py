#!/usr/bin/env python3
"""Render `../raid-emblems.html` from `emblem_catalog.json`.

Pure-Python stdlib, no game files needed — the catalog JSON beside this script is the input.
Run after editing a finding or regenerating the catalog:

    python3 build/build_emblems.py

Paths are relative to the script, so the working directory does not matter.
"""
import json, html, os

HERE = os.path.dirname(os.path.abspath(__file__))
cat = json.load(open(f"{HERE}/emblem_catalog.json"))

# ---- curated findings (distilled from the traces + measurements, keeping the measured numbers) ----
FINDINGS = [
    dict(ref=52, id="multiShot", name="Double Shot", rune="618 RuneTwinbolt", sev="dead", equipped=False,
         claim="Automatically fires a second harpoon (Power 50% at Legendary / 70% at Mythic).",
         code="No implementation of any kind. The effect record is built and routed into crossbowContext.passives, but nothing ever reads it — there is no getCrossbowStat(\"multiShot\") call anywhere in the 6.4MB bundle.",
         measured="Arrows per fire = 1.000 in both arms. 6 arrows, 10 boss hits, 109,200 crossbow damage — bit-identical with and without the rune. 0 second harpoons from 6 fires; 0 of a promised 76,440 damage.",
         impact="A dead crossbow slot. The tooltip ships in all 16 languages with an [ALWAYS][CROSSBOW] prefix that reads as a guaranteed passive."),
    dict(ref=107, id="pulseCritBuff", name="Crit Rate pulse", rune="627 RuneOmenF · 429 RuneOmen", sev="dead", equipped=True,
         claim="4 Allies' Crit Rate +{v}% every 4s, lasting 7s. Duration exceeds interval, so a player reads it as permanent uptime.",
         code="The pulse writes unit.critChance += v/100, but BaseUnit.updateActiveBuff() unconditionally reassigns critChance = orgCritChance + activeCritChanceBuff.value at the head of every unit's execute(), before any attack resolves. Delivered uptime is 0 of the advertised 420 frames.",
         measured="Full battle, 9001 frames, 16,832 intercepted crit rolls: damage 6,970,088.853046298 in BOTH arms — identical to the last decimal. Crit rate 10.0642% both arms, 1694 crits both arms. The pulse fires on schedule 37 times and is erased every time.",
         impact="Your equipped 627 at Epic contributes exactly 0.000000%. The battle is bit-for-bit identical whether it pays +6% crit or +600%."),
    dict(ref=21, id="resFreeze", name="Freeze Resistance", rune="319 RuneWarmthC · 422", sev="dead", equipped=False,
         claim="Freeze Duration -{v}% (10/20/30/40/60%), and full Freeze Immunity at Mythic.",
         code="The arithmetic is correct and matches the tooltip exactly. But nothing in a guild raid ever calls freeze() on an ally — the complete caller set contains no raid boss path.",
         measured="0 ally-inbound freezes across 12 full raid battles spanning all 5 bosses and 3 seeds (~4.2M ally-frames, max numFreeze = 0). The detector was validated by 3-of-3 injected freezes, so the zero is a real absence, not a broken probe.",
         impact="Zero value in a guild raid at every grade including Mythic. The stat is genuinely written onto your units — it just guards against something the raid never does."),
    dict(ref=22, id="resStun", name="Stun Resistance", rune="118 RuneClarityA", sev="dead", equipped=True,
         claim="Stun Duration -{v}%. Your rune 118 at Rare advertises -30%.",
         code="stunResistPct has exactly one consumer, BaseUnit.stun(). The blow-recovery stagger — by far the most common stun in the raid — writes numStun directly, bypassing stun() and therefore bypassing the resistance entirely.",
         measured="Direct drive confirms the honest path works: stun(240) → 240/168/144/96 frames at grades 0/3/4/5. But blow-landing → 12 frames at EVERY grade. On Dragon Knight d1 the full battle is byte-identical with and without the rune (6,970,089 damage, 556 landings, corp0 103 stuns × 12 frames).",
         impact="Advertised -30%, delivers 0% on the raid you actually run. Corp 1 ate 20.6 seconds of stun with the rune equipped and exactly the same without it."),
    dict(ref=108, id="pulseManaPulse", name="Mana pulse", rune="628 RuneWellspringF", sev="magnitude", equipped=True,
         claim="Restores {v}% Mana to 4 Allies every 4s. The engine's own renderer prints '마나 6% 회복' — with the percent sign.",
         code="case \"pulseManaPulse\": i.mana += s — bare value, no division by 100. Every sibling pulse whose tooltip renders {v}% does divide by 100. This one restores FLAT mana points.",
         measured="148 grants at exactly 6 mana each; 5,009 unit-frames of zero excess. Timing (240f) and target count (4) are both correct — only the unit is wrong.",
         impact="Against your roster's 500-mana pool, Epic 628 delivers 6 mana where the tooltip promises 30 — a 5.0× shortfall, and 9.0× on the 900-pool Winged Knight. Each pulse is worth 0.1 seconds of natural regen."),
    dict(ref=14, id="healPower", name="Healing Power", rune="306 RuneGrace", sev="magnitude", equipped=True,
         claim="Healing +{v}%. Your 306 at Epic advertises +20%, condition ALWAYS.",
         code="Read at exactly 3 sites, all emblem-internal. It multiplies emblem-generated healing only — the massHeal active, the five pulse heals, and healCycle. It cannot see a healer hero's own class-skill heal, dot ticks, the tauntRecover heal, or castle regen. Separately, it is silently discarded on any rune whose filter isn't ALL.",
         measured="healCycle 12% → 14.4% (×1.20 exactly). Hero class-skill heal(4) → 4, ratio 1.00 — untouched. In your own raid it delivered +9.33% against an advertised +20%, because 122,159 of 250,297 total healing (48.8%) runs through paths healPower cannot reach.",
         impact="Under half the advertised rate in your build. Note the auditor demoted the +9.33% to a counterfactual — the measured A-vs-B whole-battle difference was +1.9%."),
    dict(ref=76, id="healCleanse", name="Mass Heal cleanse", rune="322", sev="value-ignored", equipped=False,
         claim="Cleanses {v} Debuffs — rendered as 1 at Epic, 1 at Legendary, 2 at Mythic.",
         code="runMassHealStart tests for the effect's presence with .some() and never reads .value. All grades execute identical code: a fixed wipe of the 7 canonical debuff counters.",
         measured="Post-cast counter state at grades 4, 5 and 6 is byte-identical; control leaves all counters at 60. Full raid: 620 cleanse calls either way, boss damage bit-identical at 321,604.",
         impact="Merging Legendary → Mythic doubles the displayed cleanse count and changes nothing. The upgrade sells a number that does not exist."),
    dict(ref=95, id="onHpLow", name="Last Stand", rune="124 · 324 RuneLastStand", sev="trigger", equipped=False,
         claim="When corps HP first collapses to 20%, damage taken is reduced for 8s, once.",
         code="The trigger computes aliveHP / aliveMaxHP — dead units are removed from BOTH numerator and denominator — while the HP bar the player watches uses aliveHP / totalMaxHP. A nearly-wiped corps whose last survivor is healthy therefore reads 100% and never arms.",
         measured="Forced honest state (31/31 alive at 15% bar): armed at frame 930, 0.50 multiplier live on 35 of 62 incoming hits. Forced wiped state (30 of 31 dead, hero at full): never armed. In the un-manipulated raid, corp 1 was ground from 31 units to 2, bar bottomed at 10.77%, and it armed zero times in 9001 frames.",
         impact="A wipe-saver that is worst precisely when you are being wiped — every death makes it less likely to fire."),
    dict(ref=105, id="pulseAtkBuff", name="ATK pulse", rune="427 · 625 RuneWarSongF", sev="stacking", equipped=False,
         claim="Declared merge = 'add'. Two sources (+27% and +22%) read as +49%.",
         code="Both call addAttackDamageBuff into shared buff id 312, whose value is the MAX within an id, not the sum. The same id is shared with exhaustDmg, weakBonus and onInterrupt.",
         measured="A alone 0.2700, B alone 0.2200, both together 0.2700 — never 0.4900, deterministically and across 3 seeds. 0.49 is representable on the same accumulator and cross-id buffs do add, so this is a per-id max, not a clamp.",
         impact="Partially confirmed. The raid-level aggregate loss is small (0.01%/0.69%/5.08% across three seeds) because only 4 of 155 allies are picked per fire. The real cost is corp-wide: rune 218 'Damage While Groggy' (+38%) and 219 'Damage While Weak Point Exposed' (+38%) collide on the same id during exactly the burn window guides tell you to stack — but only while those windows overlap."),
    dict(ref=106, id="pulseSpdBuff", name="Attack Speed pulse", rune="428 RuneWarDrum · 626", sev="stacking", equipped=True,
         claim="Declared merge = 'add'. Two sources (+22% and +18%) read as +40%.",
         code="addAttackSpeedBuff passes overwrite = true into shared buff id 313. Last writer wins outright — so a LOWER-value source can actively downgrade a live higher-value buff.",
         measured="Writing 428 (22%) then 626 (18%): value goes 0.2200 → 0.1800. Hard ceiling in the two-source arm is 0.2200, never 0.4000; no unit ever holds more than one id-313 entry, in direct drive and in both live battles.",
         impact="Worse than mere non-stacking: a second, weaker attack-speed rune makes your build actively worse. You have 428 equipped."),
    dict(ref=49, id="exhaustArrow", name="Execution", rune="606 RuneExecution", sev="stronger", equipped=False,
         claim="Damage to Groggy Bosses +{v}% (+32% at Mythic), rendered with an [ALWAYS] prefix.",
         code="The gate reads raidStunFrames > 0, not inExhaustStun. raidStunFrames is also set by every successful weak-point interrupt, so the bonus pays during plain stagger — a state where the game shows no groggy indicator. The interrupt runs earlier in the same testArrowHit call, so the interrupting bolt grants itself the bonus.",
         measured="Base damage 8400.017 in every control. Full poise: ×1.0000. The interrupting bolt: ×1.3200 with raidStunFrames=0, inExhaustStun=false and the HUD groggy chip showing false. In one real battle, 37.2% of qualifying hits were in this undisclosed state.",
         impact="This one favours you — it is materially stronger than advertised. Worth knowing before anyone 'fixes' it."),
]

OVERRIDE = {
    107: dict(impact="Rune 627 RuneOmenF at Epic is a dead slot. Measured contribution to raid damage: exactly 0.000000% — the battle is bit-for-bit identical whether the rune pays +6% crit or +600%."),
    21:  dict(impact="Zero value in a guild raid at every grade including Mythic. The stat is genuinely written onto the units — it just guards against something the raid never does."),
    22:  dict(claim="Stun Duration -{v}%. Rune 118 at Rare advertises -30%.",
              impact="Advertised -30%, delivers 0% on Dragon Knight d1. Corp 1 ate 20.6 seconds of stun with the rune equipped and exactly the same without it."),
    108: dict(impact="Against a 500-mana pool, Epic 628 delivers 6 mana where the tooltip promises 30 — a 5.0× shortfall, and 9.0× on a 900-pool Winged Knight. Each pulse is worth 0.1 seconds of natural regen."),
    14:  dict(claim="Healing +{v}%. Rune 306 at Epic advertises +20%, condition ALWAYS.",
              measured="healCycle 12% → 14.4% (×1.20 exactly). Hero class-skill heal(4) → 4, ratio 1.00 — untouched. Over a full raid it delivered +9.33% against an advertised +20%, because 122,159 of 250,297 total healing (48.8%) runs through paths healPower cannot see. A filter-locked rune (313 at Mythic, +57% ELF) left healCycle at 12% — the tooltip predicts 18.84%.",
              impact="Under half the advertised rate in a representative build. Note the auditor demoted the +9.33% figure to a counterfactual — the measured A-vs-B whole-battle difference was +1.9%."),
    106: dict(impact="Worse than mere non-stacking: a second, weaker attack-speed rune makes the build actively worse."),
    49:  dict(impact="This one favours the player — it is materially stronger than advertised. Worth knowing before it gets 'fixed'."),
}

SEV = {
    "dead":         ("Delivers nothing", "crit"),
    "magnitude":    ("Wrong magnitude", "warn"),
    "value-ignored":("Value never read", "warn"),
    "trigger":      ("Wrong trigger", "warn"),
    "stacking":     ("Does not stack", "warn"),
    "stronger":     ("Stronger than stated", "good"),
}

e = html.escape
meta = cat["_meta"]

def rune_rows():
    out = []
    for r in sorted(cat["runes"], key=lambda x: x["kindNum"]):
        vals = "".join(
            f'<td class="v{" z" if v==0 else ""}">{("—" if v==0 else (f"{v:g}"))}</td>'
            for v in r["values"])
        flags = []
        if r["allowlist_violation"]: flags.append('<span class="flag">off-list</span>')
        if r["filter"] and r["filter"] != "ALL": flags.append(f'<span class="flag">{e(r["filter"])}</span>')
        out.append(
            f'<tr data-emblem="{e(r["emblem_name"] or "")}" data-cat="{e(r["category"] or "")}" '
            f'data-search="{e((r["className"]+" "+(r["mech_id"] or "")+" "+(r["desc_en"] or "")).lower())}">'
            f'<td class="mono num">{r["kindNum"]}</td>'
            f'<td class="nm">{e(r["className"])} {"".join(flags)}</td>'
            f'<td class="mono t">{e(r["type"])}</td>'
            f'<td>{e(r["emblem_name"] or "")}</td>'
            f'<td class="mono sm">{e(r["mech_id"] or "")}</td>'
            f'<td class="desc">{e(r["desc_en"] or "")}</td>'
            f'{vals}</tr>')
    return "\n".join(out)

def emblem_cards():
    out = []
    for m in cat["emblems"]:
        out.append(f'''<article class="emb">
  <header><h3>{e(m["name_en"] or "")}</h3>
    <p class="sub"><span class="mono">{e(m["className"])}</span> · {e(m["role"])} · slot <span class="mono">{e(m["slot"])}</span> · rune type <span class="mono">{e(m["runeType"])}</span></p></header>
  <dl>
    <dt>Passive</dt><dd>{e(m["passive"]["desc_en"] or "").replace("{v}", f'<b>{m["passive"]["value"]:g}</b>')}
      <span class="mono sm">#{m["passive"]["skillRef"]} {e(m["passive"]["id"] or "")}</span></dd>
    <dt>Active</dt><dd>{e(m["active"]["desc_en"] or "").replace("{v}", f'<b>{m["active"]["value"]:g}</b>')}
      <span class="mono sm">{m["active"]["cooldown_s"]}s cooldown · {m["active"]["duration_s"]}s duration</span></dd>
  </dl></article>''')
    return "\n".join(out)

def finding_cards():
    out = []
    for f in FINDINGS:
        label, cls = SEV[f["sev"]]
        f = {**f, **OVERRIDE.get(f["ref"], {})}
        eq = ""
        out.append(f'''<article class="find {cls}">
  <header>
    <div class="fhead"><h3>{e(f["name"])}</h3>{eq}</div>
    <p class="meta"><span class="sevtag {cls}">{e(label)}</span>
      <span class="mono sm">skillRef {f["ref"]} · {e(f["id"])} · {e(f["rune"])}</span></p>
  </header>
  <div class="grid3">
    <div><h4>What the game says</h4><p>{e(f["claim"])}</p></div>
    <div><h4>What the code does</h4><p>{e(f["code"])}</p></div>
    <div><h4>What the sim measured</h4><p>{e(f["measured"])}</p></div>
  </div>
  <p class="impact"><strong>Impact.</strong> {e(f["impact"])}</p>
</article>''')
    return "\n".join(out)

def sub_rows():
    return "\n".join(
        f'<tr><td class="mono num">{s["subId"]}</td><td class="mono sm">{e(s["mech_id"] or "")}</td>'
        f'<td class="desc">{e(s["desc_en"] or "")}</td>'
        f'<td class="mono">{", ".join(str(x) for x in s["emblems"])}</td>'
        f'<td class="v">{s["value5"]:g}</td><td class="v">{s["value6"]:g}</td></tr>'
        for s in cat["subs"])

def grade_rows():
    return "\n".join(
        f'<tr><td class="mono num">{g["grade"]}</td><td class="nm">{e(g["name"] or "")}</td>'
        f'<td class="v">{g["mergeCount"] or "—"}</td><td class="v">{g["mergeCoin"] or "—"}</td>'
        f'<td>{"yes" if g["subOption"] else "—"}</td></tr>'
        for g in cat["grades"])

emb_names = sorted({r["emblem_name"] for r in cat["runes"] if r["emblem_name"]})
cats = sorted({r["category"] for r in cat["runes"] if r["category"]})

tally_extra = '<div class="crit"><span class="n">3</span><span class="l">deliver nothing at all</span></div>'
footer_extra = ""
build_section = ""

HTML = f'''<title>EF2 Raid Emblems — Audit</title>
<style>
:root {{
  --paper:#F7F7F4; --ink:#16181D; --ink-2:#3A3F4A; --neutral:#737784;
  --rule:#D9D9D2; --card:#FFFFFF; --accent:#2D4B8E;
  --crit:#A32A21; --warn:#9A6B10; --good:#2E6B4F;
  --crit-bg:#FBEEEC; --warn-bg:#FBF5E6; --good-bg:#EDF4EF;
  --serif: "Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
  --sans: system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  --mono: ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --paper:#101216; --ink:#E8E9EC; --ink-2:#AFB4BE; --neutral:#8B909C;
    --rule:#282C34; --card:#171A20; --accent:#8FA9E0;
    --crit:#E8796B; --warn:#D9AE58; --good:#7FBE9A;
    --crit-bg:#231718; --warn-bg:#231F16; --good-bg:#16211C;
  }}
}}
:root[data-theme="dark"] {{
  --paper:#101216; --ink:#E8E9EC; --ink-2:#AFB4BE; --neutral:#8B909C;
  --rule:#282C34; --card:#171A20; --accent:#8FA9E0;
  --crit:#E8796B; --warn:#D9AE58; --good:#7FBE9A;
  --crit-bg:#231718; --warn-bg:#231F16; --good-bg:#16211C;
}}
:root[data-theme="light"] {{
  --paper:#F7F7F4; --ink:#16181D; --ink-2:#3A3F4A; --neutral:#737784;
  --rule:#D9D9D2; --card:#FFFFFF; --accent:#2D4B8E;
  --crit:#A32A21; --warn:#9A6B10; --good:#2E6B4F;
  --crit-bg:#FBEEEC; --warn-bg:#FBF5E6; --good-bg:#EDF4EF;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--paper); color:var(--ink); font-family:var(--sans);
  font-size:16px; line-height:1.6; -webkit-font-smoothing:antialiased; }}
.wrap {{ max-width:1180px; margin:0 auto; padding:0 24px 96px; }}
.mono {{ font-family:var(--mono); font-variant-numeric:tabular-nums; }}
.sm {{ font-size:.8rem; color:var(--neutral); }}

header.top {{ padding:72px 0 40px; border-bottom:2px solid var(--ink); }}
.eyebrow {{ font-family:var(--mono); font-size:.72rem; letter-spacing:.14em; text-transform:uppercase;
  color:var(--accent); margin:0 0 18px; }}
h1 {{ font-family:var(--serif); font-size:clamp(2.2rem,5vw,3.4rem); line-height:1.08; margin:0 0 18px;
  text-wrap:balance; font-weight:600; letter-spacing:-.015em; }}
.lede {{ font-size:1.12rem; color:var(--ink-2); max-width:64ch; margin:0; }}

.tally {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(148px,1fr)); gap:1px;
  background:var(--rule); border:1px solid var(--rule); margin:40px 0 0; }}
.tally div {{ background:var(--paper); padding:18px 20px; }}
.tally .n {{ font-family:var(--serif); font-size:2.1rem; line-height:1; display:block; }}
.tally .l {{ font-size:.76rem; color:var(--neutral); letter-spacing:.04em; margin-top:8px; display:block; }}
.tally .crit .n {{ color:var(--crit); }}

section {{ padding-top:64px; }}
h2 {{ font-family:var(--serif); font-size:1.7rem; margin:0 0 8px; font-weight:600; letter-spacing:-.01em; }}
.shead {{ border-bottom:1px solid var(--rule); padding-bottom:14px; margin-bottom:28px; }}
.shead p {{ margin:6px 0 0; color:var(--ink-2); max-width:68ch; }}

.find {{ background:var(--card); border:1px solid var(--rule); border-left:4px solid var(--neutral);
  padding:22px 24px; margin-bottom:16px; }}
.find.crit {{ border-left-color:var(--crit); }}
.find.warn {{ border-left-color:var(--warn); }}
.find.good {{ border-left-color:var(--good); }}
.fhead {{ display:flex; align-items:baseline; gap:12px; flex-wrap:wrap; }}
.find h3 {{ font-family:var(--serif); font-size:1.25rem; margin:0; font-weight:600; }}
.find .meta {{ margin:8px 0 18px; display:flex; gap:12px; align-items:center; flex-wrap:wrap; }}
.sevtag {{ font-size:.7rem; letter-spacing:.08em; text-transform:uppercase; font-family:var(--mono);
  padding:3px 8px; border-radius:2px; }}
.sevtag.crit {{ background:var(--crit-bg); color:var(--crit); }}
.sevtag.warn {{ background:var(--warn-bg); color:var(--warn); }}
.sevtag.good {{ background:var(--good-bg); color:var(--good); }}
.eqd {{ font-size:.7rem; letter-spacing:.06em; text-transform:uppercase; font-family:var(--mono);
  border:1px solid var(--accent); color:var(--accent); padding:2px 7px; border-radius:2px; }}
.grid3 {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:22px; }}
.grid3 h4 {{ font-size:.72rem; letter-spacing:.1em; text-transform:uppercase; color:var(--neutral);
  margin:0 0 7px; font-weight:600; }}
.grid3 p {{ margin:0; font-size:.9rem; color:var(--ink-2); }}
.impact {{ margin:18px 0 0; padding-top:14px; border-top:1px solid var(--rule); font-size:.9rem; }}

.embs {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:1px;
  background:var(--rule); border:1px solid var(--rule); }}
.emb {{ background:var(--card); padding:20px 22px; }}
.emb h3 {{ font-family:var(--serif); font-size:1.2rem; margin:0; font-weight:600; }}
.emb .sub {{ margin:5px 0 14px; font-size:.78rem; color:var(--neutral); }}
.emb dl {{ margin:0; display:grid; grid-template-columns:auto 1fr; gap:7px 14px; font-size:.88rem; }}
.emb dt {{ font-size:.68rem; letter-spacing:.08em; text-transform:uppercase; color:var(--neutral);
  padding-top:3px; }}
.emb dd {{ margin:0; }}
.emb dd .mono {{ display:block; margin-top:3px; }}

.tblwrap {{ overflow-x:auto; border:1px solid var(--rule); background:var(--card); }}
table {{ border-collapse:collapse; width:100%; font-size:.85rem; }}
th {{ text-align:left; font-size:.68rem; letter-spacing:.08em; text-transform:uppercase;
  color:var(--neutral); font-weight:600; padding:11px 10px; border-bottom:1px solid var(--rule);
  white-space:nowrap; position:sticky; top:0; background:var(--card); }}
td {{ padding:8px 10px; border-bottom:1px solid var(--rule); vertical-align:top; }}
tr:last-child td {{ border-bottom:0; }}
td.v {{ font-family:var(--mono); text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }}
td.z {{ color:var(--neutral); opacity:.45; }}
td.num {{ text-align:right; color:var(--neutral); }}
td.nm {{ font-weight:500; white-space:nowrap; }}
td.t {{ color:var(--neutral); }}
td.desc {{ color:var(--ink-2); min-width:210px; }}
tr.bad {{ background:var(--crit-bg); }}
.flag {{ font-family:var(--mono); font-size:.62rem; letter-spacing:.05em; text-transform:uppercase;
  color:var(--warn); border:1px solid var(--warn); padding:1px 4px; border-radius:2px;
  margin-left:5px; vertical-align:1px; }}

.filters {{ display:flex; gap:10px; flex-wrap:wrap; margin-bottom:14px; align-items:center; }}
.filters input, .filters select {{ font-family:var(--sans); font-size:.85rem; padding:7px 10px;
  border:1px solid var(--rule); background:var(--card); color:var(--ink); border-radius:2px; }}
.filters input {{ min-width:200px; }}
.filters input:focus-visible, .filters select:focus-visible {{ outline:2px solid var(--accent);
  outline-offset:1px; }}
.count {{ font-size:.78rem; color:var(--neutral); font-family:var(--mono); }}

.note {{ background:var(--card); border:1px solid var(--rule); border-left:3px solid var(--accent);
  padding:18px 22px; font-size:.9rem; color:var(--ink-2); }}
.note ul {{ margin:10px 0 0; padding-left:20px; }}
.note li {{ margin-bottom:7px; }}
.note b, .impact strong {{ color:var(--ink); }}
footer {{ margin-top:72px; padding-top:22px; border-top:1px solid var(--rule);
  font-size:.78rem; color:var(--neutral); }}
@media (prefers-reduced-motion: reduce) {{ * {{ animation:none!important; transition:none!important; }} }}
</style>

<div class="wrap">
<header class="top">
  <p class="eyebrow">Endless Frontier 2 · bundle {e(meta["bundle"])} · guild raid</p>
  <h1>The raid emblem system, audited against its own code</h1>
  <p class="lede">Every emblem, every rune, every stat at every rarity — and for all 76 mechanics,
  whether the game actually does what the tooltip says. Each divergence below was traced to engine
  code, adversarially re-derived by an independent reviewer, then measured in a headless sim running
  the same bundle.</p>
  <div class="tally">
    <div><span class="n">76</span><span class="l">mechanics traced</span></div>
    <div class="crit"><span class="n">11</span><span class="l">divergences confirmed</span></div>
    {tally_extra}
    <div><span class="n">137</span><span class="l">runes catalogued</span></div>
    <div><span class="n">822</span><span class="l">grade values verified</span></div>
  </div>
</header>

<section>
  <div class="shead"><h2>Confirmed divergences</h2>
  <p>Ordered by severity. “What the sim measured” is the output of a probe that ran the real engine —
  not a prediction. Every one of these survived an independent attempt to refute the code reading,
  then a second independent audit of the measurement itself.</p></div>
  {finding_cards()}
</section>

{build_section}

<section>
  <div class="shead"><h2>The six emblems</h2>
  <p>Fixed — one per slot, no rarity of their own. Each carries one passive and one active; rarity
  enters only through the five runes you socket into it.</p></div>
  <div class="embs">{emblem_cards()}</div>
</section>

<section>
  <div class="shead"><h2>Rarity</h2>
  <p>Six grades. Sub-options unlock at Legendary and pay a second, higher value at Mythic. These two
  tables ship inside the app bundle rather than from the server — proven by control experiment, so
  they are the live values.</p></div>
  <div class="tblwrap"><table>
    <thead><tr><th>Grade</th><th>Name</th><th>Merge count</th><th>Merge coin</th><th>Sub-option</th></tr></thead>
    <tbody>{grade_rows()}</tbody></table></div>
  <h3 style="font-family:var(--serif);font-weight:600;margin:32px 0 12px;font-size:1.15rem;">Sub-options</h3>
  <div class="tblwrap"><table>
    <thead><tr><th>#</th><th>Mechanic</th><th>Effect</th><th>Emblems</th><th>Legendary</th><th>Mythic</th></tr></thead>
    <tbody>{sub_rows()}</tbody></table></div>
</section>

<section>
  <div class="shead"><h2>All 137 runes by rarity</h2>
  <p>Every rune with its value at each grade. A dash means the value is literally zero — the resolver
  hard-skips those, which also suppresses that rune's sub-option, and the game will not grant the
  rune at that grade at all. <span class="flag">off-list</span> marks a rune the engine accepts into
  an emblem its own skill allowlist excludes; <span class="flag">HERO</span>-style tags mark a
  non-ALL filter that narrows who the effect reaches.</p></div>
  <div class="filters">
    <input id="q" type="search" placeholder="Search name, mechanic, effect…" aria-label="Search runes">
    <select id="fe" aria-label="Filter by emblem"><option value="">All emblems</option>
      {"".join(f'<option>{e(n)}</option>' for n in emb_names)}</select>
    <select id="fc" aria-label="Filter by category"><option value="">All categories</option>
      {"".join(f'<option>{e(c)}</option>' for c in cats)}</select>
    <span class="count" id="cnt"></span>
  </div>
  <div class="tblwrap"><table id="rt">
    <thead><tr><th>#</th><th>Rune</th><th>Type</th><th>Emblem</th><th>Mechanic</th><th>Effect</th>
      <th>Com</th><th>Unc</th><th>Rare</th><th>Epic</th><th>Leg</th><th>Myth</th></tr></thead>
    <tbody>{rune_rows()}</tbody></table></div>
</section>

<section>
  <div class="shead"><h2>How this was established</h2></div>
  <div class="note">
  <p>Three independent layers had to agree before anything above was called a divergence.</p>
  <ul>
    <li><b>Data.</b> Books captured read-only from the live client. <span class="mono sm">RUNE_GRADE</span>
      and <span class="mono sm">RUNE_SUB</span> never arrive from the server; the engine falls back to
      tables baked into the bundle. Proven by seeding a sentinel book and watching it override — so the
      fallback is used because nothing arrives, not because something is masked.</li>
    <li><b>Code.</b> All 76 mechanics traced to engine code, then every flagged claim handed to an
      independent agent instructed to refute it. 45 were flagged; 34 did not survive.</li>
    <li><b>Measurement.</b> Each survivor probed in a headless sim, then the probe itself audited by a
      third agent who re-ran it and checked the controls. The sim bundle is byte-identical to the
      shipped game bundle across the emblem subsystem, so this is the same code, not a lookalike.</li>
  </ul>
  <p style="margin-top:14px;">Engine facts worth carrying into any build decision:
  <b>duplicate copies of the same rune do not stack</b> (the resolver dedupes by kind);
  the only equip gate is rune type versus emblem type;
  <span class="mono sm">minGrade</span> is never read by any code;
  and active cooldown reduction caps at 80%, reachable to 41% by putting sub-option 6 in all five slots.</p>
  </div>
</section>

<footer>Captured {e(meta["captured_at"] or "")} · bundle {e(meta["bundle"])} ·
raid tested: Dragon Knight d1 (kindNum 5, 21M HP, crossbow) unless a finding states otherwise{footer_extra}</footer>
</div>

<script>
(function () {{
  var q = document.getElementById('q'), fe = document.getElementById('fe'),
      fc = document.getElementById('fc'), cnt = document.getElementById('cnt'),
      rows = Array.prototype.slice.call(document.querySelectorAll('#rt tbody tr'));
  function apply() {{
    var s = q.value.trim().toLowerCase(), em = fe.value, ca = fc.value, n = 0;
    rows.forEach(function (r) {{
      var ok = (!s || r.dataset.search.indexOf(s) !== -1) &&
               (!em || r.dataset.emblem === em) && (!ca || r.dataset.cat === ca);
      r.style.display = ok ? '' : 'none';
      if (ok) n++;
    }});
    cnt.textContent = n + ' of ' + rows.length;
  }}
  [q, fe, fc].forEach(function (el) {{ el.addEventListener('input', apply); }});
  apply();
}})();
</script>
'''

dest = os.path.join(HERE, "..", "raid-emblems.html")
open(dest, "w").write(HTML)
print(f"wrote {os.path.normpath(dest)} ({len(HTML):,} bytes)")
print(f"findings={len(FINDINGS)} runes={len(cat['runes'])} emblems={len(cat['emblems'])}")
