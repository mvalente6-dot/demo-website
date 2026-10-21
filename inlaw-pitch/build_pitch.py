"""Build the single-file pitch page (video + deck) from figures.json, script.json, deck.json
and any narration clips in audio/scene-N.mp3.

Outputs:
  pitch.html          full standalone document (offline, no external references)
  pitch-artifact.html same content without the document wrapper, for the Artifact tool
"""
import json, base64, os, re, html, sys

HERE = os.path.dirname(os.path.abspath(__file__))
def load(n): return json.load(open(os.path.join(HERE, n)))
F = load('figures.json'); S = load('script.json'); D = load('deck.json')
DISP = F['display']; INP = F['inputs']

# ---------- numbers to words (narration only) ----------
ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "zero ten twenty thirty forty fifty sixty seventy eighty ninety".split()
def words(n):
    n = int(round(n))
    if n < 20: return ONES[n]
    if n < 100: return TENS[n//10] + ("" if n % 10 == 0 else " " + ONES[n % 10])
    if n < 1000: return ONES[n//100] + " hundred" + ("" if n % 100 == 0 else " " + words(n % 100))
    if n < 1_000_000: return words(n//1000) + " thousand" + ("" if n % 1000 == 0 else " " + words(n % 1000))
    return words(n//1_000_000) + " million" + ("" if n % 1_000_000 == 0 else " " + words(n % 1_000_000))
def dollars(n): return words(n) + " dollars"
def pct(x):
    s = f"{x*100:.2f}".rstrip('0').rstrip('.')
    if '.' in s:
        a, b = s.split('.'); return words(int(a)) + " point " + " ".join(ONES[int(c)] for c in b) + " percent"
    return words(int(s)) + " percent"

W = {
    'home_cost': dollars(INP['home_cost']),
    'from_home_sale': dollars(INP['from_home_sale']),
    'loan_amount': dollars(INP['loan_amount']),
    'loan_amount_adj': words(INP['loan_amount']) + " dollar",
    'today_payment': dollars(INP['today_payment']),
    'market_rate_pct': pct(INP['market_rate']),
    'monthly_market': dollars(F['monthly_payment_market']),
    'monthly_family': dollars(F['monthly_payment_family']),
    'interest_gap_rounded': dollars(round(F['interest_gap'] / 1000) * 1000),
    'extra_tax': dollars(F['extra_tax_estimate_per_year']),
    'change_family': dollars(F['change_vs_today_family']),
    'change_market': dollars(F['change_vs_today_market']),
}
def fill(t):
    t = re.sub(r"\{w:(\w+)\}", lambda m: W[m.group(1)], t)
    return re.sub(r"\{(\w+)\}", lambda m: DISP[m.group(1)], t)

# ---------- audio ----------
def audio_for(scene_id):
    p = os.path.join(HERE, 'audio', f'scene-{scene_id}.mp3')
    if not os.path.exists(p): return None, None
    b = open(p, 'rb').read()
    dur = None
    try:
        from mutagen.mp3 import MP3
        dur = MP3(p).info.length
    except Exception:
        pass
    return "data:audio/mpeg;base64," + base64.b64encode(b).decode(), dur

WPM = 135
scenes = []
for sc in S['scenes']:
    narr = fill(sc['narration'])
    sents = re.split(r'(?<=[.!?])\s+', narr)
    starts = []; acc = 0
    for s_ in sents: starts.append(acc); acc += len(s_.split())
    total = acc
    audio, dur = audio_for(sc['id'])
    scenes.append({
        'id': sc['id'], 'title': sc['title'], 'narration': narr, 'sentences': sents,
        'beats': [fill(b) for b in sc['beats']],
        'cue_frac': [starts[c] / total for c in sc['cues']],
        'sent_frac': [st / total for st in starts],
        'est': total / WPM * 60, 'audio': audio, 'dur': dur,
    })
deck = {
    'main': [{**sl, 'content': fill(sl['content']), 'notes': {k: fill(v) for k, v in sl['notes'].items()}} for sl in D['main']],
    'appendix': [{**sl, 'content': fill(sl['content']), 'notes': {k: fill(v) for k, v in sl['notes'].items()}} for sl in D['appendix']],
}
E = html.escape

# ---------- scene markup ----------
def beat_div(i, text, cls=""):
    return f'<div class="beat {cls}" data-beat="{i}"><span class="measure">{E(text)}</span></div>'

def street_svg(with_house=False, lit=False, faint=False):
    """Flat street: Papa and Grandee's house left, lot right."""
    house_r = ""
    if with_house:
        house_r = f'''
    <g id="newhome">
      <rect x="1180" y="560" width="420" height="260" fill="#F2E6D3" stroke="#1F2A30" stroke-width="6"/>
      <polygon points="1160,560 1390,400 1620,560" fill="#B86B28" stroke="#1F2A30" stroke-width="6" stroke-linejoin="round"/>
      <rect x="1600" y="620" width="230" height="200" fill="#E7D9BF" stroke="#1F2A30" stroke-width="6"/>
      <polygon points="1600,620 1715,520 1830,620" fill="#9E5A22" stroke="#1F2A30" stroke-width="6" stroke-linejoin="round"/>
      <rect x="1340" y="700" width="90" height="120" fill="#1F2A30"/>
      <rect x="1230" y="620" width="80" height="70" fill="{'#FFD98A' if lit else '#FFF9EE'}" stroke="#1F2A30" stroke-width="5"/>
      <rect x="1470" y="620" width="80" height="70" fill="{'#FFD98A' if lit else '#FFF9EE'}" stroke="#1F2A30" stroke-width="5"/>
      <rect x="1680" y="680" width="70" height="60" fill="{'#FFD98A' if lit else '#FFF9EE'}" stroke="#1F2A30" stroke-width="5"/>
    </g>'''
    return f'''<svg class="art {'faint' if faint else ''}" viewBox="0 0 1920 1080" aria-hidden="true">
    <rect width="1920" height="1080" fill="#FAF8F4"/>
    <g class="clouds">
      <ellipse cx="300" cy="150" rx="120" ry="40" fill="#F1ECE3"/><ellipse cx="380" cy="130" rx="90" ry="34" fill="#F1ECE3"/>
      <ellipse cx="1500" cy="200" rx="140" ry="44" fill="#F1ECE3"/><ellipse cx="1600" cy="180" rx="100" ry="36" fill="#F1ECE3"/>
    </g>
    <circle cx="1700" cy="130" r="54" fill="#F3C96B"/>
    <rect x="0" y="820" width="1920" height="260" fill="#CFE3B4"/>
    <rect x="0" y="840" width="1920" height="110" fill="#8C8B86"/>
    <g stroke="#FAF8F4" stroke-width="6" stroke-dasharray="60 50"><line x1="0" y1="895" x2="1920" y2="895"/></g>
    <!-- Papa and Grandee's house -->
    <g id="pg">
      <rect x="280" y="540" width="440" height="280" fill="#EFE3CF" stroke="#1F2A30" stroke-width="6"/>
      <polygon points="260,540 500,380 740,540" fill="#7F8C7A" stroke="#1F2A30" stroke-width="6" stroke-linejoin="round"/>
      <rect x="300" y="700" width="400" height="120" fill="#E2D2B5" stroke="#1F2A30" stroke-width="6"/>
      <rect x="320" y="700" width="12" height="120" fill="#1F2A30"/><rect x="668" y="700" width="12" height="120" fill="#1F2A30"/>
      <rect x="460" y="710" width="80" height="110" fill="#1F2A30"/>
      <rect x="330" y="590" width="80" height="80" fill="#FFD98A" stroke="#1F2A30" stroke-width="5"/>
      <rect x="590" y="590" width="80" height="80" fill="#FFD98A" stroke="#1F2A30" stroke-width="5"/>
      <circle cx="500" cy="690" r="12" fill="#F3C96B"/>
      <text x="500" y="1030" text-anchor="middle" font-size="44" font-family="inherit" fill="#1F2A30" font-weight="700">Papa and Grandee</text>
    </g>
    <!-- the lot -->
    <g id="lot"><rect x="1120" y="600" width="760" height="220" rx="20" fill="#D9E8C2"/>
      <text x="1500" y="1030" text-anchor="middle" font-size="44" font-family="inherit" fill="#1F2A30" font-weight="700">{'The home they hope to build' if with_house else 'The land'}</text></g>
    {house_r}
    <g id="tree1"><rect x="1000" y="700" width="24" height="120" fill="#8B5E34"/><circle cx="1012" cy="690" r="70" fill="#A9C98B"/></g>
    </svg>'''

def kids_svg():
    return '''<svg class="art" viewBox="0 0 1920 1080" aria-hidden="true">
    <rect width="1920" height="1080" fill="#FAF8F4"/>
    <ellipse cx="960" cy="1000" rx="1300" ry="300" fill="#CFE3B4"/>
    <circle cx="1760" cy="340" r="54" fill="#F3C96B"/>
    <g class="kid k1" fill="#B86B28"><circle cx="620" cy="560" r="46" fill="#F2D2B6"/><rect x="580" y="610" width="80" height="120" rx="30"/><rect x="590" y="730" width="24" height="90" rx="12" fill="#1F2A30"/><rect x="646" y="730" width="24" height="90" rx="12" fill="#1F2A30"/></g>
    <g class="kid k2" fill="#7F8C7A"><circle cx="900" cy="600" r="40" fill="#F2D2B6"/><rect x="866" y="644" width="68" height="104" rx="28"/><rect x="874" y="748" width="22" height="80" rx="11" fill="#1F2A30"/><rect x="922" y="748" width="22" height="80" rx="11" fill="#1F2A30"/></g>
    <g class="kid k3" fill="#D99A4E"><circle cx="1140" cy="660" r="32" fill="#F2D2B6"/><rect x="1112" y="696" width="56" height="80" rx="24"/><rect x="1118" y="776" width="18" height="60" rx="9" fill="#1F2A30"/><rect x="1156" y="776" width="18" height="60" rx="9" fill="#1F2A30"/></g>
    <g class="ball"><circle cx="760" cy="420" r="34" fill="#FAF8F4" stroke="#1F2A30" stroke-width="6"/><path d="M740 396 Q760 420 740 444 M780 396 Q760 420 780 444" stroke="#1F2A30" stroke-width="5" fill="none"/></g>
    <g><rect x="1380" y="700" width="24" height="160" fill="#8B5E34"/><circle cx="1392" cy="680" r="90" fill="#A9C98B"/></g>
    <g><rect x="360" y="720" width="24" height="140" fill="#8B5E34"/><circle cx="372" cy="700" r="80" fill="#A9C98B"/></g>
    </svg>'''

def barn_svg(rain=False):
    rain_g = '''<g class="rain" stroke="#9FB3C8" stroke-width="5" stroke-linecap="round">''' + "".join(
        f'<line x1="{x}" y1="{60 + (x*7)%200}" x2="{x-18}" y2="{120 + (x*7)%200}"/>' for x in range(40, 1920, 70)) + '</g>' if rain else ''
    return f'''<svg class="art" viewBox="0 0 1920 1080" aria-hidden="true">
    <rect width="1920" height="1080" fill="{'#EEF0F2' if rain else '#FAF8F4'}"/>
    {rain_g}
    <g transform="translate(0,70)">
    <rect x="0" y="880" width="1920" height="200" fill="#CFE3B4"/>
    <!-- main house, side view -->
    <rect x="160" y="520" width="420" height="360" fill="#F2E6D3" stroke="#1F2A30" stroke-width="6"/>
    <polygon points="140,520 370,360 600,520" fill="#B86B28" stroke="#1F2A30" stroke-width="6" stroke-linejoin="round"/>
    <rect x="220" y="600" width="90" height="80" fill="{'#FFD98A' if rain else '#FFF9EE'}" stroke="#1F2A30" stroke-width="5"/>
    <rect x="420" y="600" width="90" height="80" fill="{'#FFD98A' if rain else '#FFF9EE'}" stroke="#1F2A30" stroke-width="5"/>
    <rect x="330" y="760" width="80" height="120" fill="#1F2A30"/>
    <!-- attached barn, cutaway -->
    <rect x="580" y="440" width="1180" height="440" fill="{'#FFF3DD' if rain else '#FBF4E8'}" stroke="#1F2A30" stroke-width="6"/>
    <polygon points="560,440 1170,260 1780,440" fill="#9E5A22" stroke="#1F2A30" stroke-width="6" stroke-linejoin="round"/>
    <text x="1170" y="420" text-anchor="middle" font-size="40" font-family="inherit" fill="#1F2A30" font-weight="700" letter-spacing="4">SPORTS BARN</text>
    <!-- hoop -->
    <g><rect x="660" y="520" width="14" height="360" fill="#1F2A30"/><rect x="640" y="500" width="150" height="100" fill="#FAF8F4" stroke="#1F2A30" stroke-width="6"/><ellipse cx="760" cy="600" rx="40" ry="14" fill="none" stroke="#B86B28" stroke-width="8"/><path d="M724 606 L740 660 M796 606 L780 660 M740 660 L780 660 M750 620 L770 620" stroke="#1F2A30" stroke-width="3" fill="none"/></g>
    <!-- soccer goal -->
    <g><rect x="880" y="700" width="260" height="180" fill="none" stroke="#1F2A30" stroke-width="8"/>{"".join(f'<line x1="{x}" y1="700" x2="{x}" y2="880" stroke="#9FA8A3" stroke-width="2"/>' for x in range(900,1140,26))}{"".join(f'<line x1="880" y1="{y}" x2="1140" y2="{y}" stroke="#9FA8A3" stroke-width="2"/>' for y in range(720,880,26))}<circle cx="1010" cy="850" r="26" fill="#FAF8F4" stroke="#1F2A30" stroke-width="5"/></g>
    <!-- climbing wall -->
    <g><rect x="1200" y="480" width="200" height="400" fill="#E7D9BF" stroke="#1F2A30" stroke-width="6"/>{"".join(f'<circle cx="{1230+ (i*53)%150}" cy="{520+i*38}" r="12" fill="{c}"/>' for i,c in enumerate(['#B86B28','#7F8C7A','#D99A4E','#B86B28','#7F8C7A','#D99A4E','#B86B28','#7F8C7A','#D99A4E']))}</g>
    <!-- jungle gym -->
    <g stroke="#1F2A30" stroke-width="8" fill="none"><rect x="1460" y="600" width="240" height="280"/><line x1="1460" y1="670" x2="1700" y2="670"/><line x1="1460" y1="740" x2="1700" y2="740"/><line x1="1460" y1="810" x2="1700" y2="810"/><line x1="1580" y1="600" x2="1580" y2="880"/></g>
    <!-- home gym corner -->
    <g><rect x="700" y="820" width="120" height="14" fill="#1F2A30"/><rect x="690" y="800" width="30" height="54" rx="6" fill="#5B6166"/><rect x="800" y="800" width="30" height="54" rx="6" fill="#5B6166"/><text x="760" y="790" text-anchor="middle" font-size="26" font-family="inherit" fill="#5B6166">home gym</text></g>
    </g></svg>'''

def table_svg():
    chairs = ""
    pts = [(760, 420), (960, 400), (1160, 420), (1260, 560), (1160, 700), (960, 720), (760, 700), (660, 560)]
    for i, (x, y) in enumerate(pts[:7]):
        chairs += f'<rect x="{x-36}" y="{y-36}" width="72" height="72" rx="18" fill="#B86B28" stroke="#1F2A30" stroke-width="5"/>'
    return f'''<svg class="art" viewBox="0 0 1920 1080" aria-hidden="true">
    <rect width="1920" height="1080" fill="#FAF8F4"/>
    <rect x="0" y="0" width="1920" height="1080" fill="#F6EFE3"/>
    <!-- window with the two houses -->
    <rect x="1380" y="140" width="420" height="320" rx="12" fill="#DCEBF6" stroke="#1F2A30" stroke-width="8"/>
    <line x1="1590" y1="140" x2="1590" y2="460" stroke="#1F2A30" stroke-width="8"/><line x1="1380" y1="300" x2="1800" y2="300" stroke="#1F2A30" stroke-width="8"/>
    <rect x="1380" y="400" width="420" height="60" fill="#CFE3B4"/>
    <rect x="1430" y="370" width="80" height="40" fill="#EFE3CF"/><polygon points="1420,372 1470,330 1520,372" fill="#7F8C7A"/>
    <rect x="1670" y="370" width="80" height="40" fill="#F2E6D3"/><polygon points="1660,372 1710,330 1760,372" fill="#B86B28"/>
    <!-- table -->
    <ellipse cx="960" cy="560" rx="360" ry="190" fill="#D9A86A" stroke="#1F2A30" stroke-width="8"/>
    <ellipse cx="960" cy="560" rx="300" ry="140" fill="none" stroke="#C48E4E" stroke-width="4"/>
    {chairs}
    </svg>'''

def scene_markup(sc):
    sid = sc['id']; B = sc['beats']
    if sid == 1:
        body = street_svg() + beat_div(0, B[0], 'top') + beat_div(1, B[1], 'top')
    elif sid == 2:
        body = (f'<div class="layer l0">{street_svg(with_house=True)}</div>'
                f'<div class="layer l1">{kids_svg()}</div>'
                f'<div class="layer l2">{barn_svg()}</div>'
                f'<div class="layer l3">{barn_svg(rain=True)}</div>'
                f'<div class="layer l4">{table_svg()}</div>'
                + "".join(beat_div(i, b, "top" if i < 4 else "") for i, b in enumerate(B)))
    elif sid == 3:
        body = ('<div class="center"><div class="thanks measure">Thank you</div><div class="rule"></div></div>'
                + beat_div(1, B[1], "low"))
    elif sid == 4:
        body = f'''<div class="plan">
          <div class="bar"><div class="seg sale"><span class="measure">{E(DISP['from_home_sale_k'])}</span></div><div class="seg loan"><span class="measure">{E(DISP['loan_amount_k'])}</span></div></div>
          <div class="bartotal measure">{E(DISP['home_cost_k'])} to build</div>
        </div>''' + "".join(beat_div(i, b, "low") for i, b in enumerate(B))
    elif sid == 5:
        body = f'''<div class="cards">
          <div class="card c0"><div class="k">Today</div><div class="v measure">{E(DISP['monthly_today'])}</div><div class="s">a month, about 2.5%</div></div>
          <div class="card c1"><div class="k">Bank rate, {E(DISP['market_rate_pct'])}</div><div class="v measure">{E(DISP['monthly_market'])}</div><div class="s">{E(DISP['change_market'])} vs today</div></div>
          <div class="card c2"><div class="k">Family rate, about 3%</div><div class="v measure">{E(DISP['monthly_family'])}</div><div class="s">{E(DISP['change_family'])} vs today</div></div>
        </div>
        <div class="wide">
          <div class="k">Total interest over 30 years</div>
          <div class="pair"><div><div class="v measure">{E(DISP['total_interest_market_rounded'])}</div><div class="s">at the bank rate</div></div><div class="vs">vs</div><div><div class="v measure">{E(DISP['total_interest_family_rounded'])}</div><div class="s">at about 3%</div></div></div>
          <div class="gap"><span class="measure">The gap a family rate closes: about {E(DISP['interest_gap_rounded'])}</span></div>
        </div>'''
    elif sid == 6:
        body = street_svg(with_house=True, faint=True) + '<div class="askcard">' + "".join(f'<div class="line" data-beat="{i}"><span class="measure">{E(b)}</span></div>' for i, b in enumerate(B)) + '</div>'
    elif sid == 7:
        icons = ['<svg viewBox="0 0 80 80"><rect x="14" y="8" width="52" height="64" rx="6" fill="#FFF" stroke="#1F2A30" stroke-width="5"/><line x1="26" y1="28" x2="54" y2="28" stroke="#1F2A30" stroke-width="5"/><line x1="26" y1="42" x2="54" y2="42" stroke="#1F2A30" stroke-width="5"/><path d="M26 58 q10 -10 20 0" stroke="#B86B28" stroke-width="5" fill="none"/></svg>',
                 '<svg viewBox="0 0 80 80"><polygon points="10,40 40,12 70,40" fill="#B86B28" stroke="#1F2A30" stroke-width="5" stroke-linejoin="round"/><rect x="18" y="40" width="44" height="30" fill="#FFF" stroke="#1F2A30" stroke-width="5"/><circle cx="56" cy="60" r="12" fill="#F3C96B" stroke="#1F2A30" stroke-width="4"/></svg>',
                 '<svg viewBox="0 0 80 80"><rect x="12" y="10" width="56" height="60" rx="6" fill="#FFF" stroke="#1F2A30" stroke-width="5"/><line x1="22" y1="28" x2="58" y2="28" stroke="#1F2A30" stroke-width="4"/><line x1="22" y1="42" x2="58" y2="42" stroke="#1F2A30" stroke-width="4"/><line x1="22" y1="56" x2="46" y2="56" stroke="#1F2A30" stroke-width="4"/></svg>',
                 '<svg viewBox="0 0 80 80"><rect x="18" y="8" width="44" height="64" fill="#FFF" stroke="#1F2A30" stroke-width="5"/><polyline points="18,72 26,64 34,72 42,64 50,72 58,64 62,72" fill="none" stroke="#1F2A30" stroke-width="4"/><text x="40" y="48" text-anchor="middle" font-size="26" font-weight="700" fill="#B86B28">$</text></svg>']
        body = '<div class="checklist">' + "".join(f'<div class="item" data-beat="{i}"><div class="ico">{icons[i]}</div><div class="txt measure">{E(b)}</div><div class="tick">✓</div></div>' for i, b in enumerate(B)) + '</div>'
    elif sid == 8:
        body = street_svg(with_house=True, lit=True) + '<div class="askcard end">' + "".join(f'<div class="line" data-beat="{i}"><span class="measure">{E(b)}</span></div>' for i, b in enumerate(B)) + '</div>'
    else:
        body = ""
    return f'<section class="scene s{sid}" data-scene="{sid}" aria-label="Scene {sid}: {E(sc["title"])}">{body}<div class="caption" aria-live="polite"></div></section>'

scenes_html = "".join(scene_markup(sc) for sc in scenes)

# ---------- deck markup ----------
def slide_markup(sl, idx, appendix=False):
    sid = sl['id']
    if not appendix and sid == 1:
        body = f'''<h2>The ask, in one view</h2>
        <div class="big4">
          <div><div class="k">Amount</div><div class="v">{E(DISP['loan_amount_k'])}</div><div class="s">about</div></div>
          <div><div class="k">Term</div><div class="v">30 yrs</div><div class="s">paid monthly</div></div>
          <div><div class="k">Rate</div><div class="v">below market</div><div class="s">{E(DISP['family_rate_pct'])} is the example, not a fixed number</div></div>
          <div><div class="k">Monthly, at {E(DISP['family_rate_pct'])}</div><div class="v">{E(DISP['monthly_family'])}</div><div class="s">vs {E(DISP['monthly_today'])} today</div></div>
        </div>
        <p class="foot">Fully documented, recorded against the home, paid through a servicer. We cover every cost.</p>'''
    elif not appendix and sid == 2:
        body = f'''<h2>Bank rate vs family rate</h2>
        <div class="compare">
          <div class="col"><div class="h">Bank rate, {E(DISP['market_rate_pct'])}</div>
            <div class="row"><span>Monthly payment</span><b>{E(DISP['monthly_market'])}</b></div>
            <div class="row"><span>Change vs today</span><b>{E(DISP['change_market'])}</b></div>
            <div class="row"><span>Interest over 30 years</span><b>{E(DISP['total_interest_market'])}</b></div></div>
          <div class="col fam"><div class="h">Family rate, about 3%</div>
            <div class="row"><span>Monthly payment</span><b>{E(DISP['monthly_family'])}</b></div>
            <div class="row"><span>Change vs today</span><b>{E(DISP['change_family'])}</b></div>
            <div class="row"><span>Interest over 30 years</span><b>{E(DISP['total_interest_family'])}</b></div></div>
        </div>
        <p class="foot">The gap a family rate closes: <b>{E(DISP['interest_gap'])}</b> of interest over 30 years. Our payment still rises by {E(DISP['change_family'])} a month.</p>'''
    elif not appendix and sid == 3:
        body = f'''<h2>Try the numbers</h2>
        <div class="sliders">
          <div class="ctl"><label for="loanAmt">Loan amount <output id="loanOut">$400,000</output></label><input type="range" id="loanAmt" min="300000" max="450000" step="5000" value="400000"></div>
          <div class="ctl"><label for="rate">Family rate <output id="rateOut">3.00%</output></label><input type="range" id="rate" min="2.5" max="{INP['market_rate']*100:.2f}" step="0.05" value="3"></div>
        </div>
        <div class="big4 live">
          <div><div class="k">Our monthly payment</div><div class="v" id="liveMonthly"></div><div class="s" id="liveChange"></div></div>
          <div><div class="k">Bank loan, {E(DISP['market_rate_pct'])}</div><div class="v" id="liveBank"></div><div class="s" id="liveDiff"></div></div>
          <div><div class="k">Interest over 30 years</div><div class="v" id="liveInt"></div><div class="s" id="liveIntBank"></div></div>
        </div>
        <p class="foot">Move the sliders with the mouse or arrow keys. Press Tab to switch between them.</p>'''
    elif not appendix and sid == 4:
        items = ["A written loan agreement, drawn up by an attorney",
                 "Recorded against the home, like a bank mortgage, so the loan is fully secured",
                 "Payments through an independent loan servicer, so there are always clear records",
                 "We pay every cost of setting it up",
                 f"We cover any extra tax from the below-market rate, every year (about {DISP['extra_tax']} in year one, an estimate, shrinking over time)"]
        body = '<h2>Done properly</h2><ul class="checks">' + "".join(f'<li><span class="tick">✓</span><span>{E(t)}</span></li>' for t in items) + '</ul>'
    elif not appendix and sid == 5:
        body = '''<h2>What we're asking of you</h2>
        <ol class="steps">
          <li><b>Take the time you need.</b> No answer tonight.</li>
          <li><b>Ask us anything,</b> tonight or later.</li>
          <li><b>If you want to go further,</b> we bring in an attorney and a CPA to confirm every detail.</li>
          <li><b>Then we build</b> in 2027, across the street.</li>
        </ol>
        <p class="foot">Thank you for the land, and for listening.</p>'''
    elif appendix and sid == 'A1':
        body = '''<h2>Fair to Amber's siblings</h2>
        <p class="lead">If the loan is not fully repaid by the time of inheritance, the unpaid balance comes out of Amber's share.</p>
        <ul class="checks"><li><span class="tick">✓</span><span>The loan is a debt owed to you, not a gift</span></li>
        <li><span class="tick">✓</span><span>Any unpaid balance reduces Amber's share only</span></li>
        <li><span class="tick">✓</span><span>The attorney writes this into the agreement</span></li></ul>'''
    elif appendix and sid == 'A2':
        body = f'''<h2>Sources for the rates</h2>
        <ul class="src">
          <li><b>Bank rate, {E(DISP['market_rate_pct'])}.</b> Freddie Mac Primary Mortgage Market Survey, 30-year fixed, week of {E(DISP['market_date'])}. freddiemac.com/pmms</li>
          <li><b>Construction loans.</b> Residential construction loans were quoted around 7% to 9% in October 2026 (lender and guide pages, no single official figure). The 30-year rate is used for the comparison.</li>
          <li><b>IRS minimum rate for family loans, {E(DISP['afr_pct'])}.</b> Rev. Rul. 2026-19, October 2026, long-term rate, semiannual compounding. irs.gov/pub/irs-drop/rr-26-19.pdf</li>
          <li><b>Tax estimate.</b> ({E(DISP['afr_pct'])} minus 3%) on {E(DISP['loan_amount_k'])}, times an assumed 30% tax rate, about {E(DISP['extra_tax'])} in year one. We will confirm every detail with an attorney and CPA.</li>
        </ul>'''
    else:
        body = ""
    notes = json.dumps(sl['notes'])
    return f'<section class="slide" data-slide="{idx}" data-id="{sid}" data-title="{E(sl["title"])}" data-notes=\'{E(notes)}\'><div class="slidebody">{body}</div><div class="slidefoot"><span>{"Appendix" if appendix else "Discussion"}</span><span>{E(str(sid))}</span></div></section>'

all_slides = [(sl, False) for sl in deck['main']] + [(sl, True) for sl in deck['appendix']]
slides_html = "".join(slide_markup(sl, i, ap) for i, (sl, ap) in enumerate(all_slides))
appendix_start = len(deck['main'])

data_js = json.dumps({
    'figures': F,
    'scenes': [{k: v for k, v in sc.items() if k != 'audio'} for sc in scenes],
    'audio': {sc['id']: sc['audio'] for sc in scenes if sc['audio']},
    'appendixStart': appendix_start,
}).replace('</', '<\\/')

CSS = r'''
:root { --bg:#FAF8F4; --fg:#1F2A30; --muted:#5B6166; --accent:#B86B28; --accent-soft:#F4E6D6; --card:#FFFDF9; --line:#E4DDD1; --bars:#EFE9DF;
  --ui:"Avenir Next","Segoe UI","Helvetica Neue",Helvetica,Arial,sans-serif; color-scheme: light; }
html, body { height:100%; margin:0; }
body { background:var(--bars); color:var(--fg); font-family:var(--ui); overflow:hidden; }
#viewport { position:fixed; inset:0; background:var(--bars); overflow:hidden; }
#stage { position:absolute; left:50%; top:50%; width:1920px; height:1080px; background:var(--bg); overflow:hidden; transform-origin:center center; box-shadow:0 20px 60px rgba(31,42,48,.12); }
.screen { position:absolute; inset:0; opacity:0; transition:opacity 1.1s ease; pointer-events:none; }
.screen.on { opacity:1; pointer-events:auto; }
/* start */
#start { display:grid; place-items:center; text-align:center; }
#start h1 { font-size:88px; font-weight:700; margin:0 0 18px; letter-spacing:-.01em; text-wrap:balance; }
#start p { font-size:40px; color:var(--muted); margin:0 0 56px; }
#begin { font:inherit; font-size:44px; font-weight:700; padding:24px 72px; border-radius:999px; border:0; background:var(--accent); color:#fff; cursor:pointer; box-shadow:0 10px 30px rgba(184,107,40,.3); }
#begin:focus-visible { outline:6px solid var(--fg); outline-offset:6px; }
.hint { position:absolute; bottom:40px; left:0; right:0; font-size:28px; color:var(--muted); text-align:center; }
/* scenes */
.scene { position:absolute; inset:0; opacity:0; transition:opacity 1.2s ease; }
.scene.on { opacity:1; }
.art { position:absolute; inset:0; width:100%; height:100%; }
.art.faint { opacity:.22; }
.layer { position:absolute; inset:0; opacity:0; transition:opacity 1.2s ease; }
.beat { position:absolute; left:120px; right:120px; bottom:90px; text-align:center; font-size:72px; font-weight:700; line-height:1.18; opacity:0; transition:opacity .9s ease; text-wrap:balance; }
.beat.on { opacity:1; }
.beat .measure { display:inline-block; background:rgba(250,248,244,.9); padding:14px 40px; border-radius:18px; }
.beat.low { bottom:70px; }
.beat.top { top:60px; bottom:auto; }
body.captions .beat.top { top:60px; }
.caption { position:absolute; left:160px; right:160px; bottom:20px; text-align:center; font-size:38px; color:var(--muted); display:none; }
body.captions .caption { display:block; }
body.captions .beat { bottom:150px; }
/* scene 2 layers */
.s2.b0 .l0, .s2.b1 .l1, .s2.b2 .l2, .s2.b3 .l3, .s2.b4 .l4 { opacity:1; }
.kid { transform-origin:center bottom; animation: sway 4s ease-in-out infinite alternate; }
.k2 { animation-delay:-1.3s; } .k3 { animation-delay:-2.4s; }
.ball { animation: bounce 2.6s ease-in-out infinite alternate; }
.clouds { animation: drift 40s linear infinite alternate; }
.rain { animation: rainfall 1.2s linear infinite; }
@keyframes sway { from { transform:translateY(0) } to { transform:translateY(-10px) } }
@keyframes bounce { from { transform:translateY(0) } to { transform:translateY(60px) } }
@keyframes drift { from { transform:translateX(0) } to { transform:translateX(90px) } }
@keyframes rainfall { from { transform:translateY(-60px) } to { transform:translateY(60px) } }
/* scene 3 */
.center { position:absolute; inset:0; display:grid; place-items:center; align-content:center; }
.thanks { font-size:200px; font-weight:700; letter-spacing:-.02em; }
.rule { width:0; height:12px; background:var(--accent); border-radius:6px; transition:width 2.2s ease; margin-top:10px; }
.s3.on .rule { width:560px; }
.s3 .beat.low { bottom:140px; font-size:64px; }
/* scene 4 */
.plan { position:absolute; left:160px; right:160px; top:280px; }
.bar { height:200px; border:8px solid var(--fg); border-radius:28px; display:flex; overflow:hidden; background:var(--card); }
.seg { display:flex; align-items:center; justify-content:center; font-size:96px; font-weight:700; color:#fff; width:0; transition:width 1.8s ease; white-space:nowrap; overflow:hidden; }
.seg.sale { background:#7F8C7A; } .seg.loan { background:var(--accent); }
.s4.b1 .seg.sale, .s4.b2 .seg.sale { width:33.333%; } .s4.b2 .seg.loan { width:70%; }
.bartotal { text-align:center; font-size:72px; font-weight:700; margin-top:36px; }
/* scene 5 */
.cards { position:absolute; left:100px; right:100px; top:200px; display:grid; grid-template-columns:repeat(3,1fr); gap:40px; transition:transform 1.2s ease, opacity 1s ease; }
.card { background:var(--card); border:4px solid var(--line); border-radius:28px; padding:40px 30px; text-align:center; opacity:0; transform:translateY(16px); transition:opacity 1s ease, transform 1s ease; }
.card .k { font-size:40px; color:var(--muted); font-weight:700; }
.card .v { font-size:130px; font-weight:700; line-height:1.05; margin:18px 0 10px; font-variant-numeric:tabular-nums; letter-spacing:-.02em; }
.card .s { font-size:38px; color:var(--muted); }
.s5.b0 .c0, .s5.b1 .c0, .s5.b1 .c1, .s5.b2 .c0, .s5.b2 .c1, .s5.b2 .c2 { opacity:1; transform:none; }
.s5.b3 .cards, .s5.b4 .cards { transform:translateY(-120px) scale(.62); opacity:.5; }
.s5.b3 .c0, .s5.b3 .c1, .s5.b3 .c2, .s5.b4 .c0, .s5.b4 .c1, .s5.b4 .c2 { opacity:1; transform:none; }
.card.c1 { border-color:#C9CFD2; } .card.c2 { border-color:var(--accent); }
.wide { position:absolute; left:160px; right:160px; top:560px; background:var(--card); border:4px solid var(--accent); border-radius:28px; padding:36px 40px; text-align:center; opacity:0; transform:translateY(20px); transition:opacity 1s ease, transform 1s ease; }
.s5.b3 .wide, .s5.b4 .wide { opacity:1; transform:none; }
.wide .k { font-size:40px; color:var(--muted); font-weight:700; }
.pair { display:grid; grid-template-columns:1fr auto 1fr; align-items:center; gap:40px; margin:12px 0 8px; }
.pair .v { font-size:116px; font-weight:700; font-variant-numeric:tabular-nums; letter-spacing:-.02em; line-height:1.05; }
.pair .s { font-size:34px; color:var(--muted); } .vs { font-size:48px; color:var(--muted); }
.gap { font-size:52px; font-weight:700; color:var(--accent); opacity:0; transition:opacity 1s ease; margin-top:6px; }
.s5.b4 .gap { opacity:1; }
/* scene 6 and 8 */
.askcard { position:absolute; left:220px; right:220px; top:300px; height:480px; background:rgba(255,253,249,.96); border:4px solid var(--line); border-radius:32px; display:grid; place-items:center; text-align:center; }
.askcard .line { grid-area:1/1; font-size:84px; font-weight:700; line-height:1.2; padding:0 80px; opacity:0; transition:opacity 1s ease; text-wrap:balance; }
.askcard .line.on { opacity:1; }
.askcard.end { top:40px; height:300px; }
/* scene 7 */
.checklist { position:absolute; left:220px; right:220px; top:110px; display:grid; gap:22px; }
.item { display:grid; grid-template-columns:110px 1fr 80px; align-items:center; gap:26px; background:var(--card); border:4px solid var(--line); border-radius:24px; padding:18px 36px; opacity:0; transform:translateX(-14px); transition:opacity .9s ease, transform .9s ease; }
.item.on { opacity:1; transform:none; }
.item .ico svg { width:100px; height:100px; }
.item .txt { font-size:58px; font-weight:700; line-height:1.12; }
.item .tick { font-size:76px; color:var(--accent); font-weight:700; opacity:0; transition:opacity .6s ease .6s; }
.item.on .tick { opacity:1; }
/* controls overlay */
#controls { position:absolute; left:0; right:0; bottom:0; padding:14px 40px; display:flex; justify-content:space-between; font-size:26px; color:var(--muted); opacity:0; transition:opacity .4s; pointer-events:none; }
#video:hover #controls, body.paused #controls { opacity:1; }
#pausebadge { position:absolute; top:40px; right:40px; font-size:34px; font-weight:700; color:var(--accent); background:var(--card); border:3px solid var(--accent); border-radius:999px; padding:10px 28px; display:none; }
body.paused #pausebadge { display:block; }
/* deck */
.slide { position:absolute; inset:0; opacity:0; transition:opacity .7s ease; padding:90px 140px 80px; box-sizing:border-box; display:flex; flex-direction:column; }
.slide.on { opacity:1; }
.slidebody { flex:1; min-height:0; }
.slide h2 { font-size:84px; margin:0 0 40px; letter-spacing:-.01em; }
.slidefoot { display:flex; justify-content:space-between; font-size:26px; color:var(--muted); letter-spacing:.08em; text-transform:uppercase; }
.big4 { display:grid; grid-template-columns:repeat(4,1fr); gap:32px; }
.big4 > div { background:var(--card); border:4px solid var(--line); border-radius:24px; padding:36px 30px; min-width:0; }
.big4 .k { font-size:30px; color:var(--muted); font-weight:700; }
.big4 .v { font-size:88px; font-weight:700; line-height:1.05; margin:14px 0 10px; font-variant-numeric:tabular-nums; letter-spacing:-.02em; text-wrap:balance; }
.big4 .s { font-size:30px; color:var(--muted); }
.big4.live { grid-template-columns:repeat(3,1fr); margin-top:40px; }
.foot { font-size:40px; color:var(--muted); margin:48px 0 0; text-wrap:balance; }
.compare { display:grid; grid-template-columns:1fr 1fr; gap:40px; }
.col { background:var(--card); border:4px solid var(--line); border-radius:24px; padding:30px 40px; }
.col.fam { border-color:var(--accent); }
.col .h { font-size:40px; font-weight:700; margin-bottom:18px; }
.col .row { display:flex; justify-content:space-between; align-items:baseline; font-size:40px; padding:18px 0; border-top:2px solid var(--line); }
.col .row b { font-size:64px; font-variant-numeric:tabular-nums; letter-spacing:-.01em; }
.sliders { display:grid; grid-template-columns:1fr 1fr; gap:60px; }
.ctl label { display:flex; justify-content:space-between; font-size:40px; font-weight:700; margin-bottom:12px; }
.ctl output { font-variant-numeric:tabular-nums; color:var(--accent); }
input[type=range] { width:100%; height:48px; accent-color:var(--accent); cursor:pointer; }
input[type=range]:focus-visible { outline:5px solid var(--fg); outline-offset:8px; border-radius:8px; }
.checks { list-style:none; padding:0; margin:0; display:grid; gap:26px; }
.checks li { display:flex; gap:28px; align-items:flex-start; font-size:50px; line-height:1.2; }
.checks .tick { color:var(--accent); font-weight:700; }
.steps { font-size:54px; line-height:1.25; padding-left:70px; margin:0; display:grid; gap:26px; }
.lead { font-size:56px; line-height:1.2; margin:0 0 40px; text-wrap:balance; }
.src { list-style:none; padding:0; margin:0; display:grid; gap:22px; font-size:34px; line-height:1.3; color:var(--muted); }
.src b { color:var(--fg); }
/* presenter panel (fallback when a popup is blocked) */
#notes { position:fixed; top:0; right:0; bottom:0; width:min(520px,90vw); background:#1F2A30; color:#FAF8F4; padding:24px 28px; overflow:auto; font-size:17px; line-height:1.5; transform:translateX(100%); transition:transform .3s; z-index:20; box-sizing:border-box; }
body.notes #notes { transform:none; }
#notes h3 { margin:0 0 6px; font-size:14px; letter-spacing:.1em; text-transform:uppercase; color:#D99A4E; }
#notes .t { font-size:22px; font-weight:700; margin-bottom:14px; }
#notes p { margin:0 0 12px; } #notes b { color:#F3C96B; }
#notes .next { margin-top:22px; color:#B9C2C6; }
#diag { position:fixed; left:0; bottom:0; max-height:50vh; width:min(720px,100vw); overflow:auto; background:#1F2A30; color:#FAF8F4; font:14px/1.4 ui-monospace,Menlo,monospace; padding:12px 16px; display:none; z-index:30; box-sizing:border-box; white-space:pre-wrap; }
body.diag #diag { display:block; }
@media (prefers-reduced-motion: reduce) { .kid, .ball, .clouds, .rain { animation:none !important; } .screen, .scene, .beat, .layer, .card, .wide, .item, .seg, .rule, .askcard .line, .slide { transition-duration:.01s !important; } }
'''

JS = r'''
const DATA = __DATA__;
const WPM = 135;
const $ = s => document.querySelector(s), $$ = s => Array.from(document.querySelectorAll(s));
const stage = $('#stage'), body = document.body;
let scale = 1;
function fit() { const w = innerWidth, h = innerHeight; scale = Math.min(w / 1920, h / 1080); stage.style.transform = `translate(-50%,-50%) scale(${scale})`; }
addEventListener('resize', fit); fit();

// ---------- mode ----------
let mode = 'start';
function show(id) { $$('.screen').forEach(s => s.classList.toggle('on', s.id === id)); mode = id; body.classList.toggle('paused', false); }

// ---------- video ----------
const scenes = DATA.scenes; const audioEls = {};
for (const sc of scenes) { if (DATA.audio[sc.id]) { const a = new Audio(DATA.audio[sc.id]); a.preload = 'auto'; audioEls[sc.id] = a; } }
let si = -1, clock = null, raf = null, endTimer = null, paused = false, manualT0 = 0, manualAcc = 0;
function sceneEl(i) { return $(`.scene[data-scene="${scenes[i].id}"]`); }
function duration(i) { const sc = scenes[i]; const a = audioEls[sc.id]; return (a && isFinite(a.duration) && a.duration > 0) ? a.duration : (sc.dur || sc.est); }
function now(i) { const a = audioEls[scenes[i].id]; if (a) return a.currentTime; return manualAcc + (paused ? 0 : (performance.now() - manualT0) / 1000); }
function setBeat(i, b) {
  const el = sceneEl(i); const sc = scenes[i];
  for (let k = 0; k < 6; k++) el.classList.toggle('b' + k, k === b);
  el.querySelectorAll('[data-beat]').forEach(x => { const n = +x.dataset.beat; x.classList.toggle('on', n === b || (x.classList.contains('item') && n <= b)); });
}
function setCaption(i, t) {
  const sc = scenes[i]; const d = duration(i); let idx = 0;
  for (let k = 0; k < sc.sent_frac.length; k++) if (t / d >= sc.sent_frac[k] - 0.02) idx = k;
  const c = sceneEl(i).querySelector('.caption'); if (c.textContent !== sc.sentences[idx]) c.textContent = sc.sentences[idx];
}
function tick() {
  if (si < 0 || mode !== 'video') return;
  const sc = scenes[si], d = duration(si), t = now(si);
  let b = -1; for (let k = 0; k < sc.cue_frac.length; k++) if (t / d >= sc.cue_frac[k] - 0.015) b = k;
  const el = sceneEl(si); if (+el.dataset.beat !== b) { el.dataset.beat = b; setBeat(si, b); }
  setCaption(si, t);
  if (!audioEls[sc.id] && !paused && t >= d) { onEnded(); return; }
  raf = requestAnimationFrame(tick);
}
function onEnded() {
  cancelAnimationFrame(raf);
  if (si === scenes.length - 1) { $('#hintEnd').style.opacity = 1; return; }  // hold on the last card
  endTimer = setTimeout(() => startScene(si + 1), 1400);
}
function stopScene() {
  cancelAnimationFrame(raf); clearTimeout(endTimer);
  if (si >= 0) { const a = audioEls[scenes[si].id]; if (a) { a.pause(); a.currentTime = 0; a.onended = null; } sceneEl(si).classList.remove('on'); }
}
function startScene(i, fromUser) {
  stopScene(); si = i; paused = false; body.classList.remove('paused'); $('#hintEnd').style.opacity = 0;
  const sc = scenes[i], el = sceneEl(i); el.dataset.beat = -1; setBeat(i, -1); el.classList.add('on');
  $('#sceneNo').textContent = `Scene ${sc.id} of ${scenes.length}: ${sc.title}`;
  const a = audioEls[sc.id]; manualAcc = 0; manualT0 = performance.now();
  if (a) { a.currentTime = 0; a.onended = onEnded; a.play().catch(() => {}); }
  raf = requestAnimationFrame(tick);
}
function togglePause() {
  if (mode !== 'video' || si < 0) return;
  const a = audioEls[scenes[si].id];
  if (!paused) { paused = true; if (a) a.pause(); else manualAcc += (performance.now() - manualT0) / 1000; clearTimeout(endTimer); }
  else { paused = false; if (a) a.play().catch(() => {}); else manualT0 = performance.now(); if (now(si) >= duration(si)) onEnded(); }
  body.classList.toggle('paused', paused);
}
function beginVideo() { show('video'); for (const k in audioEls) { try { audioEls[k].load(); } catch (e) {} } startScene(0); }
function enterDeck() { stopScene(); show('deck'); gotoSlide(0); }

// ---------- deck ----------
const slides = $$('.slide'); let cur = 0; const chan = ('BroadcastChannel' in window) ? new BroadcastChannel('pitch-notes') : null; let popup = null;
function gotoSlide(n) {
  cur = Math.max(0, Math.min(slides.length - 1, n));
  slides.forEach((s, i) => s.classList.toggle('on', i === cur));
  const s = slides[cur]; const msg = { title: s.dataset.title, id: s.dataset.id, notes: JSON.parse(s.dataset.notes), next: slides[cur + 1] ? slides[cur + 1].dataset.title : 'End', n: cur + 1, total: slides.length };
  renderNotes(msg); if (chan) chan.postMessage(msg); try { localStorage.setItem('pitch-notes', JSON.stringify(msg)); } catch (e) {}
  if (popup && !popup.closed) { try { popup.postMessage(msg, '*'); } catch (e) {} }
  if (cur === 2) recompute();
}
function notesHTML(m) { return `<h3>Slide ${m.n} of ${m.total}</h3><div class="t">${m.title}</div>` + Object.entries(m.notes).map(([k, v]) => `<p><b>${k}:</b> ${v}</p>`).join('') + `<div class="next">Next: ${m.next}</div>`; }
function renderNotes(m) { $('#notes').innerHTML = notesHTML(m); }
function openNotes() {
  const html = `<!doctype html><meta charset="utf-8"><title>Presenter notes</title><style>body{margin:0;background:#1F2A30;color:#FAF8F4;font:20px/1.5 "Avenir Next","Segoe UI",Helvetica,Arial,sans-serif;padding:28px}h3{margin:0 0 6px;font-size:14px;letter-spacing:.1em;text-transform:uppercase;color:#D99A4E}.t{font-size:28px;font-weight:700;margin-bottom:16px}p{margin:0 0 14px}b{color:#F3C96B}.next{margin-top:26px;color:#B9C2C6}#clock{position:fixed;top:14px;right:20px;color:#B9C2C6;font-variant-numeric:tabular-nums}</style><div id="clock"></div><div id="n">Waiting for the deck…</div><script>
    function r(m){document.getElementById('n').innerHTML='<h3>Slide '+m.n+' of '+m.total+'</h3><div class="t">'+m.title+'</div>'+Object.entries(m.notes).map(([k,v])=>'<p><b>'+k+':</b> '+v+'</p>').join('')+'<div class="next">Next: '+m.next+'</div>'}
    addEventListener('message',e=>{if(e.data&&e.data.notes)r(e.data)});
    if('BroadcastChannel' in window){new BroadcastChannel('pitch-notes').onmessage=e=>r(e.data)}
    try{const m=JSON.parse(localStorage.getItem('pitch-notes'));if(m)r(m)}catch(e){}
    setInterval(()=>{document.getElementById('clock').textContent=new Date().toLocaleTimeString([],{hour:'numeric',minute:'2-digit'})},1000);
  <\/script>`;
  try { popup = window.open('', 'pitchNotes', 'width=620,height=760'); } catch (e) { popup = null; }
  if (popup) { popup.document.open(); popup.document.write(html); popup.document.close(); gotoSlide(cur); }
  else { body.classList.toggle('notes'); }
}
// slider math: identical formula to compute_figures.py
const INP = DATA.figures.inputs;
function pmt(P, r, n) { const m = r / 12; return P * m / (1 - Math.pow(1 + m, -n)); }
const usd = v => '$' + Math.round(v).toLocaleString('en-US');
function recompute() {
  const P = +$('#loanAmt').value, r = +$('#rate').value / 100, n = INP.term_years * 12;
  const ours = pmt(P, r, n), bank = pmt(P, INP.market_rate, n);
  $('#loanOut').textContent = usd(P); $('#rateOut').textContent = (r * 100).toFixed(2) + '%';
  $('#liveMonthly').textContent = usd(ours); $('#liveChange').textContent = (ours >= INP.today_payment ? '+' : '') + usd(ours - INP.today_payment) + ' vs ' + usd(INP.today_payment) + ' today';
  $('#liveBank').textContent = usd(bank); $('#liveDiff').textContent = 'same amount, ' + usd(bank - ours) + ' a month more';
  $('#liveInt').textContent = usd(ours * n - P); $('#liveIntBank').textContent = usd(bank * n - P) + ' at the bank rate';
}
$('#loanAmt').addEventListener('input', recompute); $('#rate').addEventListener('input', recompute); recompute();

// ---------- keys ----------
function onKey(e) {
  const k = e.key; const tag = (e.target.tagName || '').toLowerCase();
  if (k === 'd' || k === 'D') { body.classList.toggle('diag'); return; }
  if (k === 'c' || k === 'C') { body.classList.toggle('captions'); return; }
  if (mode === 'start') { if (k === 'Enter' || k === ' ' || k === 'ArrowRight' || k === 'PageDown') { e.preventDefault(); beginVideo(); } return; }
  if (mode === 'video') {
    if (k === ' ') { e.preventDefault(); if (si === scenes.length - 1 && now(si) >= duration(si)) enterDeck(); else togglePause(); }
    else if (k === 'ArrowRight' || k === 'PageDown') { e.preventDefault(); if (si === scenes.length - 1) enterDeck(); else startScene(si + 1, true); }
    else if (k === 'ArrowLeft' || k === 'PageUp') { e.preventDefault(); if (now(si) > 2.5 || si === 0) startScene(si, true); else startScene(si - 1, true); }
    else if (k === 'Enter') { if (si === scenes.length - 1) enterDeck(); }
    else if (k === 'Escape') { stopScene(); show('start'); }
    return;
  }
  if (mode === 'deck') {
    if (tag === 'input' && (k === 'ArrowLeft' || k === 'ArrowRight')) return;  // sliders own the arrows
    if (k === 'ArrowRight' || k === 'PageDown' || k === ' ' || k === 'Enter') { e.preventDefault(); gotoSlide(cur + 1); }
    else if (k === 'ArrowLeft' || k === 'PageUp' || k === 'Backspace') { e.preventDefault(); gotoSlide(cur - 1); }
    else if (k === 'a' || k === 'A') { gotoSlide(DATA.appendixStart); }
    else if (k === 'n' || k === 'N') { openNotes(); }
    else if (k === 'Home') { gotoSlide(0); }
    else if (k === 'v' || k === 'V') { show('video'); startScene(0); }
    else if (k === 'Escape') { body.classList.remove('notes'); }
  }
}
addEventListener('keydown', onKey);
$('#begin').addEventListener('click', beginVideo);
$('#video').addEventListener('click', e => { if (si === scenes.length - 1 && now(si) >= duration(si)) enterDeck(); else togglePause(); });
$('#deck').addEventListener('click', e => { if (['input', 'label', 'output'].includes((e.target.tagName || '').toLowerCase())) return; gotoSlide(cur + 1); });

// ---------- self test (layout + wording), results in the D panel and window.__selftest ----------
function selfTest() {
  const out = []; const sr = stage.getBoundingClientRect();
  const inside = (r) => r.left >= sr.left - 1 && r.top >= sr.top - 1 && r.right <= sr.right + 1 && r.bottom <= sr.bottom + 1;
  const check = (label, root) => root.querySelectorAll('.measure, .beat.on, h2, .v, .row, .foot, .checks li, .steps li, .src li, .lead, .ctl').forEach(el => {
    if (!el.offsetParent && getComputedStyle(el).position !== 'absolute') return;
    const r = el.getBoundingClientRect(); if (r.width === 0) return;
    if (!inside(r)) out.push(`OVERFLOW ${label}: "${el.textContent.trim().slice(0, 40)}" ${Math.round(r.right - sr.right)}px right, ${Math.round(r.bottom - sr.bottom)}px bottom`);
    if (el.scrollWidth > el.clientWidth + 2 && getComputedStyle(el).overflowX !== 'visible') out.push(`CLIP ${label}: "${el.textContent.trim().slice(0, 40)}"`);
  });
  const prev = { mode, si, cur };
  // scenes: every beat state
  show('video');
  scenes.forEach((sc, i) => { const el = sceneEl(i); el.classList.add('on'); for (let b = 0; b < sc.beats.length; b++) { setBeat(i, b); el.offsetHeight; check(`scene ${sc.id} beat ${b + 1}`, el); } setBeat(i, -1); el.classList.remove('on'); });
  show('deck'); slides.forEach((s, i) => { s.classList.add('on'); s.offsetHeight; check(`slide ${s.dataset.id}`, s); s.classList.remove('on'); });
  // wording
  const banned = [/—/, /–/, /guarantee/i, /\bAFR\b/, /security deed/i, /Form 709/i, /imputed/i, /amortiz/i, /when we move in/i, /savings/i];
  const vidText = scenes.map(sc => sc.narration + ' ' + sc.beats.join(' ')).join(' ');
  const mainText = slides.slice(0, DATA.appendixStart).map(s => s.textContent + ' ' + s.dataset.notes).join(' ');
  banned.forEach(re => { if (re.test(vidText)) out.push(`WORDING video: ${re}`); if (re.test(mainText)) out.push(`WORDING main slides: ${re}`); });
  if (/sibling|inheritance/i.test(vidText + mainText)) out.push('WORDING: sibling topic outside the appendix');
  // figures trace
  const f = DATA.figures; const n = f.inputs.term_years * 12;
  const chk = (name, a, b) => { if (Math.abs(a - b) > 0.5) out.push(`FIGURE ${name}: page ${a} vs figures.json ${b}`); };
  chk('monthly_market', pmt(f.inputs.loan_amount, f.inputs.market_rate, n), f.monthly_payment_market);
  chk('monthly_family', pmt(f.inputs.loan_amount, f.inputs.family_rate_example, n), f.monthly_payment_family);
  chk('interest_gap', (pmt(f.inputs.loan_amount, f.inputs.market_rate, n) - pmt(f.inputs.loan_amount, f.inputs.family_rate_example, n)) * n, f.interest_gap);
  // audio
  const missing = scenes.filter(sc => !DATA.audio[sc.id]).map(sc => sc.id); if (missing.length) out.push(`AUDIO missing for scenes ${missing.join(', ')} (timed by estimate)`);
  if (document.querySelector('link[href^="http"], script[src^="http"], img[src^="http"], audio[src^="http"], source[src^="http"]')) out.push('EXTERNAL reference found');
  // restore
  show(prev.mode); if (prev.mode === 'deck') gotoSlide(prev.cur);
  const summary = (out.length ? out.join('\n') : 'All layout, wording, figure and audio checks passed.') + `\nStage scale ${scale.toFixed(3)} at ${innerWidth}x${innerHeight}. Audio clips: ${Object.keys(DATA.audio).length} of ${scenes.length}. Press D to hide.`;
  $('#diag').textContent = summary; window.__selftest = { issues: out, summary }; return out;
}
window.__show = (i, b) => { show('video'); stopScene(); si = i; const el = sceneEl(i); el.classList.add('on'); setBeat(i, b); if (b === scenes[i].beats.length - 1 && i === scenes.length - 1) $('#hintEnd').style.opacity = 1; };
window.__slide = (n) => { show('deck'); gotoSlide(n); };
window.__selfTest = selfTest;
addEventListener('load', () => { setTimeout(() => { try { selfTest(); } catch (e) { $('#diag').textContent = 'self test error: ' + e; } }, 300); });
'''

BODY = f'''<title>Across the Street</title>
<style>{CSS}</style>
<div id="viewport"><div id="stage">
  <section id="start" class="screen on" aria-label="Start">
    <div><p style="font-size:34px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:700;margin:0 0 26px">For Papa and Grandee</p>
    <h1>Across the Street</h1><p>A short film, then a conversation.</p>
    <button id="begin" type="button">Begin</button></div>
    <div class="hint">Space pauses. Arrow keys replay or skip a scene. C shows captions.</div>
  </section>
  <section id="video" class="screen" aria-label="Video">
    {scenes_html}
    <div id="pausebadge">Paused</div>
    <div id="controls"><span id="sceneNo"></span><span>Space: pause. Left: replay. Right: next.</span></div>
    <div class="hint" id="hintEnd" style="opacity:0;transition:opacity 1s;bottom:auto;top:352px">Press any key or click to continue to the discussion.</div>
  </section>
  <section id="deck" class="screen" aria-label="Discussion deck">
    {slides_html}
  </section>
</div></div>
<aside id="notes" aria-label="Presenter notes"></aside>
<pre id="diag" aria-label="Self test results"></pre>
<script>{JS.replace('__DATA__', data_js)}</script>'''

open(os.path.join(HERE, 'pitch-artifact.html'), 'w').write(BODY)
full = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
{BODY.replace('<title>Across the Street</title>', '<title>Across the Street</title>', 1)}
</head>
<body></body>
</html>'''
# The content above includes body-level elements; restructure so markup sits inside <body>.
head_part, _, rest = BODY.partition('</style>')
full = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
{head_part}</style>
</head>
<body>{rest}</body>
</html>'''
open(os.path.join(HERE, 'pitch.html'), 'w').write(full)
print(f"pitch.html {len(full)/1024:.0f} KB, audio clips: {sum(1 for s in scenes if s['audio'])}/{len(scenes)}")
