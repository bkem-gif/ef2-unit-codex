#!/usr/bin/env python3
import re, glob, json, os, html as _html
"""Regenerate the codex (../unit-codex.html + ../UNIT-MECHANICS.md) from build/ inputs.
Run: python3 build/build_codex.py  (paths are relative to this file, so cwd doesn't matter)."""

HERE  = os.path.dirname(os.path.abspath(__file__))   # build/ dir
REPO  = os.path.dirname(HERE)                         # repo root
PARTS = os.path.join(HERE, "data")
INTRO = os.path.join(HERE, "intro.md")
ICON  = os.path.join(HERE, "icon_map.json")
BS    = os.path.join(HERE, "base_stats.json")
OUT   = os.path.join(REPO, "unit-codex.html")
MD    = os.path.join(REPO, "UNIT-MECHANICS.md")

# ---------- markdown -> html ----------
def esc(s): return _html.escape(s, quote=True)
def inline(s):
    s = esc(s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    return s
def render_table(tbl):
    rows = [[c.strip() for c in r.strip().strip('|').split('|')] for r in tbl]
    if len(rows) < 2: return ''
    head = rows[0]; is_sep = set(''.join(rows[1])) <= set('-: ')
    body = rows[2:] if is_sep else rows[1:]
    out = ['<table><thead><tr>'] + [f'<th>{inline(h)}</th>' for h in head] + ['</tr></thead><tbody>']
    for r in body:
        while len(r) < len(head): r.append('')
        out.append('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>')
    out.append('</tbody></table>'); return ''.join(out)
def md2html(md):
    if not md: return ''
    lines = md.split('\n'); out = []; i = 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip(): i += 1; continue
        if ln.lstrip().startswith('|'):
            tbl = []
            while i < len(lines) and lines[i].lstrip().startswith('|'): tbl.append(lines[i]); i += 1
            out.append(render_table(tbl)); continue
        if re.match(r'^\s*[-*]\s', ln):
            out.append('<ul>')
            while i < len(lines) and re.match(r'^\s*[-*]\s', lines[i]):
                out.append(f'<li>{inline(re.sub(r"^\s*[-*]\s","",lines[i]))}</li>'); i += 1
            out.append('</ul>'); continue
        if re.match(r'^\s*\d+\.\s', ln):
            out.append('<ol>')
            while i < len(lines) and re.match(r'^\s*\d+\.\s', lines[i]):
                out.append(f'<li>{inline(re.sub(r"^\s*\d+\.\s","",lines[i]))}</li>'); i += 1
            out.append('</ol>'); continue
        para = [ln]; i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r'^\s*(\||[-*]\s|\d+\.\s)', lines[i]):
            para.append(lines[i]); i += 1
        out.append(f'<p>{inline(" ".join(para))}</p>')
    return '\n'.join(out)
def strip_md(s): return re.sub(r'[`*_|]', ' ', s or '').strip()

# ---------- base stats (from the captured UNIT book) ----------
BSTATS = json.load(open(BS, encoding='utf-8')) if os.path.exists(BS) else {}
BS_DESC = "From the game's `UNIT` book (server base values; `atkSpd` drives `atkDuration = 1e4/atkSpd`)."
def _yn(v): return 'Y' if str(v) in ('Y', '1', 'true', 'True') else '—'
def _imm(d):
    on = [lbl for k, lbl in (('stunImmune','stun'),('freezeImmune','freeze'),
          ('blowImmune','blow'),('knockImmune','knockback')) if str((d or {}).get(k)) in ('Y','1')]
    return ', '.join(on) if on else '—'
def _spd(a):
    try: t = round(1e4/float(a)); return f'{a} → ~{t}t (~{t/60:.1f}s)'
    except Exception: return '—' if a is None else str(a)
def _g(d, k):
    x = (d or {}).get(k); return '—' if x is None else x
def base_stats_table(cls):
    e = BSTATS.get(cls)
    if not e or not e.get('base'): return ''
    b = e['base']; v = e.get('evol'); two = v is not None
    def row(lbl, fb, fv): return f'| {lbl} | {fb} | {fv} |' if two else f'| {lbl} | {fb} |'
    dt = {'P': 'Physical', 'M': 'Magic'}
    L = (['| stat | base | Ⅱ |', '|---|---|---|'] if two else ['| stat | value |', '|---|---|'])
    L.append(row('HP', _g(b,'hp'), _g(v,'hp')))
    L.append(row('ATK (`atkDmg`)', _g(b,'atkDmg'), _g(v,'atkDmg')))
    L.append(row('atk speed (`atkSpd`)', _spd(b.get('atkSpd')), _spd((v or {}).get('atkSpd'))))
    L.append(row('move speed', _g(b,'moveSpd'), _g(v,'moveSpd')))
    L.append(row('range (`atkRange`)', _g(b,'atkRange'), _g(v,'atkRange')))
    L.append(row('defense (def/phy/mag)', f"{_g(b,'def')} / {_g(b,'phyDef')} / {_g(b,'magDef')}",
                 f"{_g(v,'def')} / {_g(v,'phyDef')} / {_g(v,'magDef')}"))
    L.append(row('recovery', _g(b,'recovery'), _g(v,'recovery')))
    L.append(row('dmg type', dt.get(b.get('dmgType'), _g(b,'dmgType')), dt.get((v or {}).get('dmgType'), _g(v,'dmgType'))))
    L.append(row('immunities', _imm(b), _imm(v)))
    L.append(row('cloaking / detect', f"{_yn(b.get('cloaking'))} / {_yn(b.get('detect'))}",
                 f"{_yn((v or {}).get('cloaking'))} / {_yn((v or {}).get('detect'))}"))
    return '\n'.join(L)
def base_stats_block(cls):
    t = base_stats_table(cls)
    return {'k': 'basestats', 'label': 'Base stats', 'html': md2html(BS_DESC + '\n' + t)} if t else None
def base_stats_md(cls):
    t = base_stats_table(cls)
    return f"**Base stats** — {BS_DESC}\n{t}\n" if t else ''

# ---------- categories ----------
SUMMONS={'NWolf','SkeletonX1','IceWolf','OrcIcePhantom1'}
STAGE_BOSS={'KingSlime','OrcFlower','HammerMole','DarkHermit'}
STAGE_MIN={'SlimeRed','SlimeBlue','SlimeYellow','FlowerSoldier1','FlowerSoldier2','MoleSoldier1','MoleSoldier2','StarFish','Crab','SSlime1','SSlime2','SSlime3'}
WAVE={'Boar1','Boar2','RoboBomb1','RoboBomb2','Frog1','Frog2','Spider1','Spider2','OrcSpearMan1','SkeletonMan2'}
RAID={'ScorpionKing','HarpyKing','GolemKing','BaseRaidUnit'}
CASTLE={'Castle0','Castle1','Castle2','BaseCastle','ElfTown5'}
REWARD={'GoldGoblin','AdsGoblin'}
CUT={'Druid2','Artillery1','CrowKnight1','Succubus1','GriffinRider1','BladeMaster1','Druid1','Aladin1'}
def category(cls):
    if cls in SUMMONS: return 'Summons'
    if cls in STAGE_BOSS: return 'Stage bosses'
    if cls in STAGE_MIN: return 'Stage-boss minions'
    if cls in WAVE: return 'Enemy wave units'
    if cls in RAID: return 'Raid bosses'
    if cls in CASTLE: return 'Castle & structures'
    if cls in REWARD: return 'Reward / special'
    if cls in CUT: return 'Unreleased / cut'
    return 'Player heroes'
CAT_ORDER = ['Player heroes','Summons','Stage bosses','Stage-boss minions','Enemy wave units','Raid bosses','Castle & structures','Reward / special','Unreleased / cut']
def role_bucket(role):
    r = (role or '').lower()
    if 'support' in r or 'buffer' in r: return 'Support'
    if 'heal' in r: return 'Healer'
    if 'tank' in r: return 'Tank'
    if 'summon' in r: return 'Summoner'
    if 'boss' in r: return 'Boss'
    if 'mage' in r or 'caster' in r: return 'Mage'
    if 'assassin' in r: return 'Assassin'
    if 'ranged' in r or 'archer' in r or 'gunner' in r: return 'Ranged'
    if 'melee' in r: return 'Melee'
    if 'castle' in r or 'structure' in r or 'turret' in r: return 'Structure'
    if 'reward' in r or 'piñata' in r or 'pinata' in r: return 'Special'
    if 'enemy' in r or 'minion' in r or 'wave' in r: return 'Enemy'
    return 'Other'

# ---------- parse new template ----------
def classify(lbl):
    l = lbl.strip(); low = l.lower()
    if low.startswith('tl;dr'): return 'tldr'
    if low.startswith('at a glance'): return 'glance'
    if low.startswith('in-game text'): return 'ingame'
    if low.startswith('normal'): return 'normal'
    if low.startswith('skill'): return 'skill'
    if low.startswith('passive'): return 'passive'
    if low.startswith('buffs'): return 'buffs'
    if low.startswith('base') or low.startswith('evolved'): return 'evolved'
    if low.startswith('key values'): return 'keyvalues'
    if low.startswith('formula'): return 'formulas'
    if l.startswith('✓') or low.startswith('matches'): return 'matches'
    if l.startswith('⚠') or low.startswith('description vs code') or low.startswith('δ'): return 'delta'
    if low.startswith('notes'): return 'notes'
    if low.startswith('how it works'): return 'normal'
    if 'numshot' in low: return 'notes'
    return None

def parse_section(sec):
    lines = sec.split('\n'); header = lines[0]
    m = re.match(r'###\s*(.+?)\s*—\s*`([^`]+)`\s*(.*)', header)
    if not m: return None
    name, cls, rest = m.group(1).strip(), m.group(2), m.group(3)
    km = re.search(r'kindNum:\s*([^)]*)', rest); kind = (km.group(1).strip() if km else '')
    body = '\n'.join(lines[1:])
    fields = []  # [key, rawlabel, content]
    cur = None
    for ln in body.split('\n'):
        mm = re.match(r'^\*\*(.+?)\*\*\s*(.*)$', ln)
        if mm and classify(mm.group(1)) is not None:
            if cur: fields.append(cur)
            inline_c = mm.group(2)
            cur = [classify(mm.group(1)), mm.group(1).strip(), ([inline_c] if inline_c.strip() else [])]
        elif cur is not None:
            cur[2].append(ln)
    if cur: fields.append(cur)
    fields = [[k, l, '\n'.join(c).strip()] for k, l, c in fields]
    return name, cls, kind, fields

units = []
for f in sorted(glob.glob(os.path.join(PARTS,'units2_part*.md'))):
    txt = open(f, encoding='utf-8').read()
    for sec in re.split(r'(?m)^(?=### )', txt):
        if not sec.strip().startswith('### '): continue
        p = parse_section(sec)
        if not p: continue
        name, cls, kind, fields = p
        fmap = {}
        for k, l, c in fields: fmap.setdefault(k, []).append((l, c))
        tldr = fmap.get('tldr', [('','')])[0][1]
        glance = fmap.get('glance', [('','')])[0][1]
        rolem = re.search(r'(?im)^\s*[-*]\s*\*\*Role:\*\*\s*(.+)$', glance) or re.search(r'(?i)Role:\s*(.+)', glance)
        role = rolem.group(1).strip() if rolem else ''
        rb = role_bucket(role)
        # has-delta: a real mismatch (not a "no description" note, not a ✓ match)
        has_delta = False
        for l, c in fmap.get('delta', []):
            txt2 = (l + ' ' + strip_md(c)).lower()
            if not re.search(r'no (localized |in-game )?description|nothing to compare|no .*to compare', txt2):
                has_delta = True
        kn = re.findall(r'\d+', kind); primary = int(kn[0]) if kn else 999999
        evolved = len(kn) >= 2 and kn[1] != kn[0]
        cat = category(cls)
        # ordered render blocks (skip tldr -> header)
        blocks = []
        for k, l, c in fields:
            if k == 'tldr': continue
            blocks.append({'k': k, 'label': l, 'html': md2html(c)})
        search = strip_md(' '.join([name, cls, kind, tldr, role] + [c for _,_,c in fields])).lower()
        units.append({'name':name,'cls':cls,'kind':kind,'primary':primary,'evolved':evolved,'cat':cat,
                      'roleBucket':rb,'tldr':tldr,'hasDelta':has_delta,'blocks':blocks,'search':search})
units.sort(key=lambda u: (CAT_ORDER.index(u['cat']) if u['cat'] in CAT_ORDER else 99, u['primary'], u['name']))
icon = json.load(open(ICON))   # {kindNum(str): image-code}
for u in units:
    code = icon.get(str(u['primary']))
    u['img'] = ('EFUnits/' + code + '.png') if code else ''
    bs = base_stats_block(u['cls'])          # inject "Base stats" right after the at-a-glance
    if bs:
        gi = next((i for i, b in enumerate(u['blocks']) if b['k'] == 'glance'), -1)
        u['blocks'].insert(gi + 1, bs)

# intro panels from prior codex md (reuse framework + findings text)
codex = open(INTRO, encoding='utf-8').read()
def between(md, start, ends):
    s = re.search(start, md)
    if not s: return ''
    rest = md[s.end():]; cuts = [e.start() for e in (re.search(p, rest) for p in ends) if e]
    return rest[:min(cuts)] if cuts else rest
FRAMEWORK_HTML = md2html(between(codex, r'(?m)^## How the combat engine works.*$', [r'(?m)^## Key findings', r'(?m)^## Index']))
FINDINGS_HTML  = md2html(between(codex, r'(?m)^## Key findings.*$', [r'(?m)^## Index', r'(?m)^# Player heroes']))

roles = sorted({u['roleBucket'] for u in units})
n_delta = sum(1 for u in units if u['hasDelta'])
DATA = json.dumps(units, ensure_ascii=False)
CATS = json.dumps([c for c in CAT_ORDER if any(u['cat']==c for u in units)], ensure_ascii=False)
ROLES = json.dumps(roles, ensure_ascii=False)

# ---------- regenerate the markdown codex (digestible) ----------
def build_md():
    head = codex[:codex.find('\n## Index')] if '\n## Index' in codex else codex.split('\n# Player heroes')[0]
    parts = [head.rstrip(), '']
    bycat = {}
    for u in units: bycat.setdefault(u['cat'], []).append(u)
    for cat in CAT_ORDER:
        if cat not in bycat: continue
        parts.append(f"\n# {cat}\n")
        for u in bycat[cat]:
            sec = [f"### {u['name']} — `{u['cls']}` (kindNum: {u['kind']})", f"**TL;DR.** {u['tldr']}", '']
            # re-emit raw blocks from source order is lossy after md2html; instead pull original section text
            parts.append('')  # placeholder; full md below
    # simpler: just concatenate the raw reformatted sources under category headers
    out = [head.rstrip(), '']
    secs = {}
    for f in sorted(glob.glob(os.path.join(PARTS,'units2_part*.md'))):
        for sec in re.split(r'(?m)^(?=### )', open(f, encoding='utf-8').read()):
            if sec.strip().startswith('### '):
                mm = re.search(r'`([^`]+)`', sec.split('\n')[0]); secs[mm.group(1)] = sec.rstrip()
    for cat in CAT_ORDER:
        cu = [u for u in units if u['cat'] == cat]
        if not cu: continue
        out.append(f"\n# {cat}\n")
        for u in cu:
            if u['cls'] not in secs: continue
            sec = secs[u['cls']]; bs = base_stats_md(u['cls'])
            if bs:                                # splice the Base-stats block in before the trailing '---'
                s2 = sec.rstrip(); idx = s2.rfind('\n---')
                sec = (s2[:idx] + '\n\n' + bs + s2[idx:]) if (s2.endswith('---') and idx != -1) else (s2 + '\n\n' + bs)
            out.append(sec); out.append('')
    return '\n'.join(out) + '\n'
open(MD, 'w', encoding='utf-8').write(build_md())

HTML = r'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>EF2 Unit Mechanics Codex</title>
<style>
:root{--bg:#0f1115;--panel:#161a21;--panel2:#1d222b;--bd:#2a313c;--tx:#e6e9ef;--mut:#9aa4b2;--acc:#5b9dff;--delta:#ff6b6b;--ok:#3ad29f;--chip:#222936;--code:#0b0d11;--glance:#172033;--warn:#2a1d22;--okbg:#16271f}
@media(prefers-color-scheme:light){:root{--bg:#f6f7f9;--panel:#fff;--panel2:#f0f2f5;--bd:#e1e4ea;--tx:#1b2330;--mut:#5d6b7e;--acc:#1f6feb;--delta:#d83b3b;--ok:#0a8f63;--chip:#eef1f5;--code:#f1f3f7;--glance:#eaf1fb;--warn:#fcecec;--okbg:#e9f6ef}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--acc)}code{background:var(--code);padding:.05em .35em;border-radius:4px;font:12.5px/1.4 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.wrap{max-width:1060px;margin:0 auto;padding:22px 18px 80px}
header h1{margin:0 0 4px;font-size:24px;font-weight:600}.sub{color:var(--mut);margin:0 0 14px}
.stats{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}.stat{background:var(--panel);border:1px solid var(--bd);border-radius:10px;padding:8px 12px}.stat b{font-size:18px}.stat span{color:var(--mut);font-size:12px;display:block}
details.panel{background:var(--panel);border:1px solid var(--bd);border-radius:12px;margin:0 0 12px;padding:0 14px}
details.panel>summary{cursor:pointer;padding:12px 0;font-weight:600;list-style:none}details.panel>summary::-webkit-details-marker{display:none}
details.panel>summary::before{content:"▸ ";color:var(--mut)}details.panel[open]>summary::before{content:"▾ "}
.panel .body{padding:0 0 10px}.panel table{border-collapse:collapse;width:100%;margin:8px 0}.panel th,.panel td{border:1px solid var(--bd);padding:5px 9px;text-align:left;font-size:13.5px}.panel th{background:var(--panel2)}
.toolbar{position:sticky;top:0;z-index:5;background:var(--bg);padding:10px 0;display:flex;gap:8px;flex-wrap:wrap;align-items:center;border-bottom:1px solid var(--bd);margin-bottom:6px}
.toolbar input[type=search]{flex:1;min-width:200px;background:var(--panel);border:1px solid var(--bd);color:var(--tx);border-radius:9px;padding:9px 12px;font-size:14px}
.toolbar select{background:var(--panel);border:1px solid var(--bd);color:var(--tx);border-radius:9px;padding:9px 10px;font-size:13px}
.tgl{display:flex;align-items:center;gap:6px;background:var(--panel);border:1px solid var(--bd);border-radius:9px;padding:8px 11px;font-size:13px;cursor:pointer;user-select:none}.tgl input{accent-color:var(--delta)}
.btn{background:var(--panel);border:1px solid var(--bd);color:var(--tx);border-radius:9px;padding:8px 11px;font-size:13px;cursor:pointer}
.count{color:var(--mut);font-size:13px;margin:6px 2px 10px}
.catnav{display:flex;gap:6px;flex-wrap:wrap;margin:2px 0 12px}.catchip{background:var(--chip);border:1px solid var(--bd);border-radius:20px;padding:4px 11px;font-size:12.5px;cursor:pointer;color:var(--mut)}.catchip.active{background:var(--acc);color:#fff;border-color:var(--acc)}
.cathead{font-size:13px;color:var(--mut);text-transform:uppercase;letter-spacing:.06em;margin:18px 2px 8px;font-weight:600}
.card{background:var(--panel);border:1px solid var(--bd);border-radius:12px;margin:0 0 8px;overflow:hidden}.card.delta{border-left:3px solid var(--delta)}
.chead{padding:11px 14px;cursor:pointer}.chead:hover{background:var(--panel2)}
.crow{display:flex;align-items:center;gap:10px}
.arrow{color:var(--mut);transition:transform .12s;font-size:12px;flex:0 0 auto}.card.open .arrow{transform:rotate(90deg)}
.thumb{width:38px;height:38px;border-radius:8px;background:var(--panel2);border:1px solid var(--bd);overflow:hidden;display:flex;align-items:center;justify-content:center;flex:0 0 38px}
.thumb.empty{background:transparent;border:0}.thumb img{max-width:100%;max-height:100%;object-fit:contain}
.namecol{flex:1;min-width:0}.nameline{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.cname{font-weight:600;font-size:15px}
.tldr{color:var(--mut);font-size:13px;margin:3px 0 0}
.top{display:flex;gap:12px;align-items:flex-start;margin-top:10px}
.hero{width:96px;height:96px;object-fit:contain;border-radius:10px;background:var(--panel2);border:1px solid var(--bd);padding:4px;flex:0 0 96px}
.topglance{flex:1;min-width:0;background:var(--glance);border:1px solid var(--bd);border-radius:9px;padding:8px 12px}.topglance ul{margin:0;padding-left:1.1em}
@media(max-width:560px){.top{flex-direction:column}.hero{width:84px;flex-basis:auto}}
.chip{font-size:11.5px;padding:2px 8px;border-radius:20px;background:var(--chip);color:var(--mut);border:1px solid var(--bd);white-space:nowrap}
.chip.cls{font-family:ui-monospace,Menlo,monospace}.chip.kind{color:var(--acc)}.chip.evo{color:var(--ok);border-color:var(--ok)}.chip.role{background:transparent}
.badge-d{margin-left:auto;color:var(--delta);font-weight:700;font-size:12px;border:1px solid var(--delta);border-radius:20px;padding:2px 9px}
.cbody{display:none;padding:4px 14px 14px;border-top:1px solid var(--bd)}.card.open .cbody{display:block}
.blk{margin:12px 0 0}.blk h5{margin:0 0 4px;font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut);font-weight:600}
.cbody p{margin:.3em 0}.cbody ul,.cbody ol{margin:.2em 0;padding-left:1.25em}.cbody li{margin:.18em 0}
.cbody table{border-collapse:collapse;width:100%;margin:4px 0}.cbody th,.cbody td{border:1px solid var(--bd);padding:4px 8px;font-size:12.8px;text-align:left}.cbody th{background:var(--panel2)}
.glance{background:var(--glance);border:1px solid var(--bd);border-radius:9px;padding:8px 12px;margin-top:12px}.glance ul{margin:0;padding-left:1.1em}
.ingame{background:var(--panel2);border-radius:8px;padding:7px 11px;font-size:13px;color:var(--mut)}.ingame ul{margin:0}
.callout{border-radius:9px;padding:9px 12px;margin-top:12px;border:1px solid}
.callout.warn{background:var(--warn);border-color:var(--delta)}.callout.warn h5{color:var(--delta)}
.callout.ok{background:var(--okbg);border-color:var(--ok)}.callout.ok h5{color:var(--ok)}
.notes{color:var(--mut);font-size:13px}
.nohit{color:var(--mut);text-align:center;padding:40px}
</style></head><body><div class="wrap">
<header><h1>EF2 Unit Mechanics Codex</h1>
<p class="sub">Code-derived mechanics, formulas &amp; hard values for every unit — bundle <code>1.11.42</code>. Each card opens with a plain-English summary; click to expand the detail.</p>
<div class="stats"><div class="stat"><b id="s-total">0</b><span>unit classes</span></div><div class="stat"><b id="s-delta">0</b><span>description↔code deltas</span></div><div class="stat"><b id="s-cat">0</b><span>categories</span></div></div>
<details class="panel"><summary>Combat framework &amp; formulas</summary><div class="body">__FRAMEWORK__</div></details>
<details class="panel"><summary>Key findings &amp; validated deltas</summary><div class="body">__FINDINGS__</div></details></header>
<div class="toolbar">
 <input type="search" id="q" placeholder="Search units, classes, kindNum, mechanics…" autocomplete="off">
 <select id="role"><option value="">All roles</option></select>
 <label class="tgl"><input type="checkbox" id="deltaOnly"> Deltas only</label>
 <button class="btn" id="expand">Expand all</button><button class="btn" id="collapse">Collapse all</button>
</div>
<div class="catnav" id="catnav"></div><div class="count" id="count"></div><div id="list"></div>
</div>
<script>
const UNITS=__DATA__, CATS=__CATS__, ROLES=__ROLES__;
const $=s=>document.querySelector(s), list=$('#list');
$('#s-total').textContent=UNITS.length;$('#s-delta').textContent=UNITS.filter(u=>u.hasDelta).length;$('#s-cat').textContent=CATS.length;
const roleSel=$('#role');ROLES.forEach(r=>{const o=document.createElement('option');o.value=r;o.textContent=r;roleSel.appendChild(o);});
let activeCat='';const catnav=$('#catnav');
function mkChip(label,val){const c=document.createElement('div');c.className='catchip'+(val===activeCat?' active':'');c.textContent=label;c.onclick=()=>{activeCat=(activeCat===val?'':val);render();};return c;}
function buildNav(){catnav.innerHTML='';catnav.appendChild(mkChip('All ('+UNITS.length+')',''));CATS.forEach(c=>{catnav.appendChild(mkChip(c+' ('+UNITS.filter(u=>u.cat===c).length+')',c));});}
function esc(s){return s.replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));}
function blockHtml(b){
 const k=b.k;
 if(k==='glance') return '<div class="glance">'+b.html+'</div>';
 if(k==='ingame') return '<div class="blk"><h5>In-game text</h5><div class="ingame">'+b.html+'</div></div>';
 if(k==='matches') return '<div class="callout ok"><h5>✓ Matches description</h5>'+(b.html||'')+'</div>';
 if(k==='delta'){const real=!/no (localized |in-game )?description|nothing to compare|no .*to compare/i.test(b.label+' '+b.html);
   if(real) return '<div class="callout warn"><h5>⚠️ '+esc(b.label.replace(/^⚠️?\s*/,''))+'</h5>'+b.html+'</div>';
   return '<div class="blk notes"><h5>Description</h5>'+b.html+'</div>';}
 if(k==='notes') return '<div class="blk notes"><h5>'+esc(b.label)+'</h5>'+b.html+'</div>';
 return '<div class="blk"><h5>'+esc(b.label)+'</h5>'+b.html+'</div>';
}
function card(u){
 const d=document.createElement('div');d.className='card'+(u.hasDelta?' delta':'');
 let chips='<span class="chip cls">'+esc(u.cls)+'</span>';
 if(u.kind&&/\d/.test(u.kind)) chips+='<span class="chip kind">#'+esc(u.kind)+'</span>';
 if(u.evolved) chips+='<span class="chip evo">Ⅱ</span>';
 if(u.roleBucket) chips+='<span class="chip role">'+esc(u.roleBucket)+'</span>';
 const badge=u.hasDelta?'<span class="badge-d">Δ</span>':'';
 const thumb='<span class="thumb'+(u.img?'':' empty')+'">'+(u.img?'<img src="'+u.img+'" alt="" loading="lazy">':'')+'</span>';
 const gl=u.blocks.find(b=>b.k==='glance'), rest=u.blocks.filter(b=>b.k!=='glance');
 let top='';
 if(u.img||gl) top='<div class="top">'+(u.img?'<img class="hero" src="'+u.img+'" alt="'+esc(u.name)+'" loading="lazy">':'')+'<div class="topglance">'+(gl?gl.html:'')+'</div></div>';
 const body=top+rest.map(blockHtml).join('');
 d.innerHTML='<div class="chead"><div class="crow"><span class="arrow">▸</span>'+thumb+'<div class="namecol"><div class="nameline"><span class="cname">'+esc(u.name)+'</span>'+chips+badge+'</div>'+(u.tldr?'<div class="tldr">'+esc(u.tldr)+'</div>':'')+'</div></div></div><div class="cbody">'+body+'</div>';
 d.querySelector('.chead').onclick=()=>d.classList.toggle('open');
 return d;
}
function render(){
 const q=$('#q').value.trim().toLowerCase(),role=roleSel.value,dOnly=$('#deltaOnly').checked,terms=q.split(/\s+/).filter(Boolean);
 buildNav();
 const sel=UNITS.filter(u=>(!activeCat||u.cat===activeCat)&&(!role||u.roleBucket===role)&&(!dOnly||u.hasDelta)&&terms.every(t=>u.search.includes(t)));
 list.innerHTML='';
 if(!sel.length){list.innerHTML='<div class="nohit">No units match.</div>';$('#count').textContent='0 units';return;}
 let cur=null;
 sel.forEach(u=>{if(u.cat!==cur){cur=u.cat;const h=document.createElement('div');h.className='cathead';h.textContent=cur+' · '+sel.filter(x=>x.cat===cur).length;list.appendChild(h);}list.appendChild(card(u));});
 $('#count').textContent=sel.length+' unit'+(sel.length>1?'s':'')+(dOnly?' with deltas':'')+(q?' matching “'+q+'”':'');
}
$('#q').oninput=render;roleSel.onchange=render;$('#deltaOnly').onchange=render;
$('#expand').onclick=()=>document.querySelectorAll('.card').forEach(c=>c.classList.add('open'));
$('#collapse').onclick=()=>document.querySelectorAll('.card').forEach(c=>c.classList.remove('open'));
render();
</script></body></html>'''
HTML=(HTML.replace('__FRAMEWORK__',FRAMEWORK_HTML).replace('__FINDINGS__',FINDINGS_HTML)
          .replace('__DATA__',DATA).replace('__CATS__',CATS).replace('__ROLES__',ROLES))
open(OUT,'w',encoding='utf-8').write(HTML)
print("wrote",OUT,"and",MD)
print("units:",len(units)," deltas:",n_delta," roles:",roles)
print("no-tldr:",[u['cls'] for u in units if not u['tldr']][:8]," no-glance:",[u['cls'] for u in units if not any(b['k']=='glance' for b in u['blocks'])][:8])
