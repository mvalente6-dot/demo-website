import json, html, re as _re
s=json.load(open('script.json')); d=json.load(open('deck.json')); f=json.load(open('figures.json'))
D=f['display']; I=f['inputs']
E=html.escape
WPM=135
def secs(t): return len(t.split())/WPM*60

voices=[
 dict(name="Chris (chosen)", id="vrZ1gMhrsD9LI0gRKrLh", who="Male, American, middle-aged",
      why="Warm, resonant, unhurried, with understated humor. Chosen after the test clips; narrates every scene on eleven_v4 with direction tags.",
      sample="https://storage.googleapis.com/eleven-public-prod/database/workspace/049c8d0ba4094eb5ac02cef3cd05aa4a/voices/vrZ1gMhrsD9LI0gRKrLh/JoyPPfk55u1HDEdz0WLv.mp3"),
 dict(name="Cee Well", id="riqnCDqBJCxuKuDEeenv", who="Male, American (light Southern), middle-aged",
      why="Deep and warm, grounded and calm. The alternative offered alongside Chris.",
      sample="https://storage.googleapis.com/eleven-public-prod/database/workspace/c2320bd857734589a823ddc50220da7d/voices/riqnCDqBJCxuKuDEeenv/481831c2-6928-4fab-979b-9f09191cc2e2.mp3"),
]

total_words=sum(len(_re.sub(r"\[[^\]]+\]\s*", "", sc['narration']).split()) for sc in s['scenes'])
import re as _re
def strip_tags(t): return _re.sub(r"\[[^\]]+\]\s*", "", t)
scene_html=""
for sc in s['scenes']:
    w=len(strip_tags(sc['narration']).split()); t=secs(strip_tags(sc['narration']))
    beats="".join(f'<li><span class="beat">{E(b)}</span><span class="bw">{len(b.split())} words</span></li>' for b in sc['beats'])
    scene_html+=f'''
<article class="scene" id="scene{sc['id']}">
  <header><span class="num">Scene {sc['id']}</span><h3>{E(sc['title'])}</h3><span class="meta">{w} words, about {t:.0f}s, {len(sc['beats'])} beats, about {t/len(sc['beats']):.0f}s each</span></header>
  <div class="cols">
    <div class="narr"><h4>Narration</h4><p>{E(sc['narration'])}</p></div>
    <div><h4>On screen</h4><ol class="beats">{beats}</ol><h4>Picture and motion</h4><p class="vis">{E(sc['visual'])}</p></div>
  </div>
</article>'''

def notes(n): return "".join(f'<p><b>{E(k)}:</b> {E(v)}</p>' for k,v in n.items())
slides=""
for sl in d['main']:
    slides+=f'<article class="slide"><header><span class="num">Slide {sl["id"]}</span><h3>{E(sl["title"])}</h3></header><p class="content">{E(sl["content"])}</p><div class="notes"><h4>Speaker notes</h4>{notes(sl["notes"])}</div></article>'
appx=""
for sl in d['appendix']:
    appx+=f'<article class="slide appendix"><header><span class="num">{sl["id"]}</span><h3>{E(sl["title"])}</h3></header><p class="content">{E(sl["content"])}</p><div class="notes"><h4>Speaker notes</h4>{notes(sl["notes"])}</div></article>'

vhtml="".join(f'''<article class="voice"><h3>{E(v['name'])}</h3><p class="who">{E(v['who'])}</p><p>{E(v['why'])}</p><p><a href="{E(v['sample'])}" target="_blank" rel="noopener">Listen to the library sample</a> (opens in a new tab, this is the voice vendor's own demo, not our script)</p></article>''' for v in voices)

page=f'''<title>Papa and Grandee Pitch, Phase A</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
/* Layout: one reading column; the pitch's own warm light palette, committed single-theme so Matteo previews the real look. */
:root {{ --bg:#FAF8F4; --fg:#1F2A30; --muted:#5B6166; --line:#E4DDD1; --card:#FFFDF9; --accent:#B86B28; --accent-soft:#F4E6D6; --ok:#2E7D4F;
  --display:'Literata', Georgia, 'Times New Roman', serif; --body:'Nunito Sans', 'Segoe UI', Helvetica, Arial, sans-serif; color-scheme: light; }}
body {{ background:var(--bg); color:var(--fg); font-family:var(--body); font-size:17px; line-height:1.55; padding-block:32px 64px; padding-left:max(16px, env(safe-area-inset-left,0px)); padding-right:max(16px, env(safe-area-inset-right,0px)); }}
main {{ max-width:960px; margin:0 auto; }}
h1,h2,h3 {{ font-family:var(--display); font-weight:600; text-wrap:balance; line-height:1.15; margin:0; }}
h1 {{ font-size:clamp(30px,5vw,44px); }} h2 {{ font-size:clamp(24px,3.5vw,30px); margin-top:56px; padding-bottom:8px; border-bottom:2px solid var(--accent); }}
h3 {{ font-size:22px; }} h4 {{ font-size:12px; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); margin:14px 0 6px; font-weight:700; }}
p {{ margin:0 0 10px; max-width:70ch; }} .lead {{ font-size:19px; color:var(--muted); max-width:62ch; }}
.eyebrow {{ font-size:12px; letter-spacing:.1em; text-transform:uppercase; color:var(--accent); font-weight:700; }}
.grid {{ display:grid; gap:14px; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); margin-top:16px; }}
.tile {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:16px 18px; min-width:0; }}
.tile .k {{ font-size:12px; letter-spacing:.06em; text-transform:uppercase; color:var(--muted); }}
.tile .v {{ font-family:var(--display); font-size:34px; font-variant-numeric:tabular-nums; margin-top:2px; }}
.tile .s {{ font-size:14px; color:var(--muted); }}
table {{ border-collapse:collapse; width:100%; font-variant-numeric:tabular-nums; margin-top:14px; }}
th,td {{ text-align:left; padding:10px 12px; border-bottom:1px solid var(--line); vertical-align:top; }} th {{ font-size:12px; letter-spacing:.06em; text-transform:uppercase; color:var(--muted); }}
td.n {{ text-align:right; }} .tw {{ overflow-x:auto; }}
.scene, .slide, .voice {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:20px 22px; margin-top:18px; min-width:0; }}
.scene header, .slide header {{ display:flex; flex-wrap:wrap; align-items:baseline; gap:8px 14px; margin-bottom:10px; }}
.num {{ font-size:12px; letter-spacing:.08em; text-transform:uppercase; color:var(--accent); font-weight:700; }}
.meta {{ font-size:14px; color:var(--muted); }}
.cols {{ display:grid; gap:12px 28px; grid-template-columns:1.2fr 1fr; }} @media (max-width:700px) {{ .cols {{ grid-template-columns:1fr; }} }}
.cols > div {{ min-width:0; }}
.narr p {{ font-size:18px; line-height:1.6; }}
.beats {{ margin:0; padding-left:20px; }} .beats li {{ margin:4px 0; display:flex; gap:10px; align-items:baseline; }} .beat {{ font-weight:700; }} .bw {{ font-size:12px; color:var(--muted); white-space:nowrap; }}
.vis {{ font-size:15px; color:var(--muted); }}
.slide .content {{ font-size:17px; }} .notes {{ background:var(--accent-soft); border-radius:8px; padding:10px 14px; margin-top:8px; }} .notes p {{ font-size:15px; }}
.appendix {{ border-style:dashed; }}
.voice .who {{ color:var(--muted); font-size:14px; margin-bottom:6px; }}
ul.plain {{ padding-left:20px; }} ul.plain li {{ margin:6px 0; }}
.check {{ display:grid; gap:10px; margin-top:14px; }} .check div {{ display:flex; gap:12px; align-items:flex-start; background:var(--card); border:1px solid var(--line); border-radius:8px; padding:12px 14px; }}
.check b {{ color:var(--accent); font-family:var(--display); font-size:20px; line-height:1; }}
.pill {{ display:inline-block; font-size:12px; font-weight:700; letter-spacing:.06em; text-transform:uppercase; padding:3px 9px; border-radius:999px; background:var(--accent-soft); color:var(--accent); }}
.pill.ok {{ background:#E3F1E8; color:var(--ok); }}
a {{ color:var(--accent); }} a:focus-visible {{ outline:2px solid var(--accent); outline-offset:2px; }}
@media (prefers-reduced-motion: reduce) {{ * {{ animation:none !important; transition:none !important; }} }}
</style>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Literata:wght@400;600&family=Nunito+Sans:wght@400;700&display=swap">
<main>
<p class="eyebrow">Phase A review, for Matteo's approval</p>
<h1>Family loan pitch to Steve and Dawn</h1>
<p class="lead">Everything below is content, not build. Read it as Steve and Dawn would hear it. Nothing has been recorded yet; the voice test clips wait for your OK.</p>

<h2>What I need from you</h2>
<div class="check">
  <div><b>1</b><div><p><b>Approve or edit the script and storyboard.</b> Eight scenes, {total_words} words, about {total_words/WPM:.1f} minutes at 135 words per minute. Beats hold 6 to 11 seconds each.</p></div></div>
  <div><b>2</b><div><p><b>Approve or edit the deck speaker notes</b> (five main slides, two appendix slides).</p></div></div>
  <div><b>3</b><div><p><b>OK the two voice test clips.</b> Cost about 4 cents each. The clip is scene 1, so you hear how each voice says Grandee, Matteo, Lucas, Owen and Wyatt. The full narration is about 56 cents in the voice you pick.</p></div></div>
  <div><b>4</b><div><p><b>Answer the open questions</b> at the bottom, or accept my recommendations.</p></div></div>
</div>

<h2>The numbers (from figures.json)</h2>
<p>A $400,000 loan over 30 years. Bank rate is Freddie Mac's 30-year average for the week of October 15, 2026. The family rate is the 3% example only.</p>
<div class="grid">
  <div class="tile"><div class="k">Today</div><div class="v">{D['monthly_today']}</div><div class="s">per month, about 2.5%</div></div>
  <div class="tile"><div class="k">Bank rate, {D['market_rate_pct']}</div><div class="v">{D['monthly_market']}</div><div class="s">{D['change_market']} vs today</div></div>
  <div class="tile"><div class="k">Family rate, about 3%</div><div class="v">{D['monthly_family']}</div><div class="s">{D['change_family']} vs today</div></div>
</div>
<div class="tw"><table>
<tr><th>Figure</th><th class="n">Bank rate {D['market_rate_pct']}</th><th class="n">Family rate 3%</th><th>Where it appears</th></tr>
<tr><td>Monthly payment</td><td class="n">{D['monthly_market']}</td><td class="n">{D['monthly_family']}</td><td>Video scene 5, slides 1 to 3</td></tr>
<tr><td>Change vs today's $1,000</td><td class="n">{D['change_market']}</td><td class="n">{D['change_family']}</td><td>Slide 2, slider</td></tr>
<tr><td>Total interest, 30 years</td><td class="n">{D['total_interest_market']}</td><td class="n">{D['total_interest_family']}</td><td>Scene 5 (rounded to thousands on the TV), slide 2</td></tr>
<tr><td>The gap a family rate closes</td><td class="n" colspan="2">{D['interest_gap']}</td><td>Scene 5 (as "about $390,000"), slide 2</td></tr>
<tr><td>Their estimated extra tax, year one (we cover it)</td><td class="n" colspan="2">about {D['extra_tax']}</td><td>Slide 4 notes only. (5.15% IRS minimum minus 3%, on $400,000, times 30%.) Shrinks each year.</td></tr>
</table></div>
<p style="margin-top:12px"><span class="pill ok">Sanity check passed</span> 3% over 30 years on $400,000 computes to $1,686.42 a month and $207,110 total interest, matching the brief.</p>
<p><b>Sources.</b> Freddie Mac Primary Mortgage Market Survey, 30-year fixed, 7.40% as of October 15, 2026 (confirmed against FRED series MORTGAGE30US). IRS Rev. Rul. 2026-19, October 2026, long-term rate, semiannual compounding, 5.15%. Residential construction loans were quoted at roughly 7% to 9% in October 2026 across lender and guide pages; there is no single authoritative figure, so the 30-year rate is used for the comparison and the construction range is noted in the appendix only.</p>

<h2>Part 1: the video, scene by scene</h2>
<p>Narration is third person throughout. On-screen text is at most 12 words per beat. Timing below assumes 135 words per minute; the build uses the real clip lengths.</p>
{scene_html}

<h2>Part 2: the discussion deck</h2>
<p>Five main slides, presenter advanced. Speaker notes are split between Matteo and Amber. Slide 3 is the live slider.</p>
{slides}
<h3 style="margin-top:28px">Appendix (only if the conversation goes there)</h3>
{appx}

<h2>Voice candidates</h2>
<p>Alexander and Kimberly were the first candidates; Matteo found Alexander nasal and asked for two more male options. Chris was chosen. All clips use the eleven_v4 model with direction tags such as [warmly], [softly] and [chuckles], per the ElevenLabs model guide.</p>
{vhtml}
<div class="tw"><table>
<tr><th>Item</th><th class="n">Credits</th><th class="n">Approx. cost</th></tr>
<tr><td>One test clip (scene 1), per candidate</td><td class="n">226</td><td class="n">$0.04</td></tr>
<tr><td>Full narration, 8 clips, one voice</td><td class="n">3,062</td><td class="n">$0.56</td></tr>
<tr><td>Everything, if both test clips are made</td><td class="n">3,514</td><td class="n">$0.64</td></tr>
</table></div>

<h2>Self-review</h2>
<ul class="plain">
<li><b>Sales-pitch check.</b> Cut "savings" everywhere; the interest difference is always "the gap a family rate closes." Removed any line that framed the loan as good for Steve and Dawn financially. The only benefit named for them is family across the street.</li>
<li><b>Honesty check.</b> Scene 5 and slide 2 both say the payment still rises by about $686 a month at the family rate. Scene 6 says plainly that they could earn more elsewhere.</li>
<li><b>Easy to say no.</b> "The home they hope to build" throughout, never "when we move in." Scene 8 and slide 5 say no answer is needed tonight, and Amber's note on slide 5 says "not yet" is okay.</li>
<li><b>Rate never fixed.</b> 3% is called the example in scenes 5 and 6 and on slide 1; scene 6 says the actual rate is theirs to decide.</li>
<li><b>Banned words.</b> Automated search of the script and deck found no em or en dashes, no "guarantee," and none of AFR, security deed, Form 709, imputed interest, or amortization. "Attorney and CPA" appears once in the video and once in the deck.</li>
<li><b>Siblings.</b> Appear only in appendix A1.</li>
<li><b>Nothing invented about the home.</b> The house is only ever "the home," plus the sports barn as the brief describes it. The illustrations show a house outline, the barn with the listed equipment, a family table, and the street.</li>
<li><b>Pace.</b> Scene 5 is the longest at about 60 seconds and carries five numbers. I kept it because it is the whole argument; everything else is under 50 seconds.</li>
</ul>

<h2>Open questions</h2>
<ul class="plain">
<li><b>Bank rate refresh.</b> Freddie Mac publishes a new number tomorrow, Thursday October 22. I recommend building on 7.40% now and refreshing figures.json the week you present; every figure, the scene 5 narration and the slider ceiling flow from that one file. The only manual step is re-recording scene 5 if the rate moves. Agree?</li>
<li><b>Voice.</b> OK to generate the two scene 1 test clips (about 8 cents total)?</li>
<li><b>Construction loan rate.</b> No single citable number exists. I recommend naming only the 30-year rate in the video and deck, with the 7% to 9% construction range in the appendix sources. Agree?</li>
<li><b>Who reads the number.</b> Scene 5 narration reads the dollar figures out loud in words. If you'd rather the narrator say "about twenty seven hundred" instead of "two thousand seven hundred seventy," say so.</li>
<li><b>Anything in the script that doesn't sound like you two?</b> Edit freely; I will carry every change into the build.</li>
</ul>
</main>'''
open('phase-a-review.html','w').write(page)
print(len(page))
