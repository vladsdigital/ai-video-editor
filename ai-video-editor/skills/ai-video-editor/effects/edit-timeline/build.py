#!/usr/bin/env python3
"""EDIT TIMELINE (explain): a dark editing panel opens above the head from a thin line and builds THIS reel's own timeline
layer by layer: real shots with real frames and real cut lengths, the real voice waveform, a block for every spoken word,
while a playhead tears across and the time code rolls to the reel's real length. Then the panel flattens to a line,
flipping light for two frames, and is gone.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html and assets/tl_strip.jpg (SAFE=1 safe-zone guide, SFX=0 no sounds,
                          CAPTIONS=0 accepted and ignored: the panel is the effect)
"""
import array
import json
import os
import re
import shutil
import subprocess

import vgfx as V

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    title_font='Inter Tight',      # the panel's title
    title_weight=700,
    mono_font='JetBrains Mono',    # time code, ruler, labels
    mono_weight=500,
    panel='#141C19',               # the panel (deep forest black)
    ink='#EDE8DB',                 # title and icons
    dim='#7E8A82',                 # ruler and row names
    code='#D3B765',                # the time code
    words='#C95F70',               # the row of word blocks
    moments='#D5B25F',             # the row of moments
    phrases='#F4EFE3',             # the row of phrase blocks
    voice='#6F8D7D',               # the voice row
    voice_ink='#CFE0D4',
    bed='#8A7740',                 # the second sound row
    bed_ink='#D9C27B',
    head='#E8697B',                # the playhead
    radius=20,
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
TITLE = 'Montaža'    # the word in the panel's top left corner, in the reel's language
T_IN = None          # when the panel opens: a word of the line (regular expression) or a slot second. None = 0.1 s into the slot
T_OUT = None         # when it starts flattening: a word or a slot second. None = 1.23 s after T_IN
MOMENTS = None       # reel seconds of the gold blocks, for example [3.1, 15.0]. None = the reel's effect slots from plan.json,
                     # or, with none yet, the words that hold a number
SOUND = 0.0          # volume of a soft whoosh when it opens and closes. 0 = silent, as in the look this was made to match
# ==== END CLIP ====

ROWS = ('T1', 'V3', 'V2', 'V1', 'A1', 'A2', 'A3')
NAME_W = 92                    # the row name column
PANEL_W = 978
FR = 1 / V.FPS


def read_json(path, fallback=None):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return fallback


def when(s, cue, fallback):
    if cue is None:
        return fallback
    if isinstance(cue, (int, float)):
        return float(cue)
    w = s.find(cue)
    if not w:
        V.die(f'the word "{cue}" is not in this slot. Words: {s.word_list()}')
    return w['start']


def envelope(aroll, n):
    """n peak values (0 to 1) over the reel's audio"""
    ff = shutil.which('ffmpeg') or 'ffmpeg'
    raw = subprocess.run([ff, '-v', 'error', '-i', aroll, '-vn', '-ac', '1', '-ar', '8000', '-f', 's16le', '-'],
                         capture_output=True).stdout
    a = array.array('h')
    a.frombytes(raw[:len(raw) // 2 * 2])
    if not a:
        return [0.0] * n
    step = max(1, len(a) // n)
    out = [max(abs(x) for x in a[i * step:(i + 1) * step] or [0]) for i in range(n)]
    top = max(out) or 1
    return [x / top for x in out]


def wave_svg(values, w, h, color):
    mid, d = h / 2, []
    for i, v in enumerate(values):
        hh = max(1.0, v * (h - 2))
        d.append(f'M{i * 2 + .5:.1f} {mid - hh / 2:.1f}v{hh:.1f}')
    return f'<svg width="{w}" height="{h}" style="position:absolute;left:0;top:0"><path d="{"".join(d)}" stroke="{color}" stroke-width="1.4" fill="none"/></svg>'


def filmstrip(aroll, total, n, tw, th):
    """one strip of n real frames of the reel, evenly spaced"""
    ff = shutil.which('ffmpeg') or 'ffmpeg'
    os.makedirs('assets', exist_ok=True)
    r = subprocess.run([ff, '-v', 'error', '-y', '-i', aroll, '-an', '-vf',
                        f'fps={n / total:.5f},scale={tw * 2}:{th * 2}:force_original_aspect_ratio=increase,crop={tw * 2}:{th * 2},eq=brightness=.07:saturation=1.12,tile={n}x1',
                        '-frames:v', '1', '-q:v', '4', 'assets/tl_strip.jpg'], capture_output=True, text=True)
    if r.returncode or not os.path.exists('assets/tl_strip.jpg'):
        V.die('could not cut frames out of the reel for the shots row: ' + r.stderr.strip()[-160:])


def main():
    s = V.Slot()
    print('words: ' + s.word_list())
    print(s.where())
    proj = s.clip.get('project')
    if not proj or not os.path.isfile(os.path.join(proj, 'segments.json')):
        V.die('this effect shows the reel\'s own timeline, so it needs a reel project (make the slot with fx_new.py --project)')
    aroll = os.path.join(proj, 'assets', 'aroll.mp4')
    segs = read_json(os.path.join(proj, 'segments.json'), [])
    if not segs or not os.path.isfile(aroll):
        V.die('segments.json or assets/aroll.mp4 is missing in the project: run assemble.py first')
    total = (segs[-1]['frame'] + segs[-1]['frames']) / V.FPS
    words = read_json(os.path.join(proj, 'words.json'), [])
    words = words.get('words', words) if isinstance(words, dict) else words
    plan = read_json(os.path.join(proj, 'plan.json'), {}) or {}

    # ---------------------------------------------------------------- room: above the head, inside the safe zone
    top = V.SAFE_TOP + 2
    bottom = s.head_top - 8
    height = bottom - top
    if height < 250:
        V.die(f'the head starts at y {s.head_top}: only {max(height, 0)} px above it inside the safe zone, the panel needs 250. Leave this effect out on this shot')
    height = min(height, 593)
    top = bottom - height
    head_h = max(42, int(height * .135))
    rule_h = max(30, int(height * .10))
    row_h = (height - head_h - rule_h - 8) // len(ROWS)
    box_h = row_h - 7
    left = (1080 - PANEL_W) // 2
    tw_all = PANEL_W - NAME_W - 22
    print(f'  panel: y {top} to {bottom} (head top {s.head_top}), rows {row_h} px, reel {total:.2f} s in {len(segs)} shots, {len(words)} words')

    def X(sec):
        return sec / total * tw_all

    # ---------------------------------------------------------------- the reel's own data
    n_thumb = max(8, int(tw_all / max(box_h * .58, 12)))
    th_w = tw_all / n_thumb
    filmstrip(aroll, total, n_thumb, int(round(th_w)) or 1, box_h)
    env = envelope(aroll, tw_all // 2 + 1)
    smooth = [sum(env[max(0, i - 3):i + 4]) / len(env[max(0, i - 3):i + 4]) for i in range(len(env))]
    top_s = max(smooth) or 1
    smooth = [min(1.0, .18 + .82 * v / top_s) for v in smooth]

    phrases, run = [], []
    for w in words:
        run.append(w)
        if re.search(r'[,.;:!?]$', w.get('text', '').strip()):
            phrases.append((run[0]['start'], run[-1]['end']))
            run = []
    if run:
        phrases.append((run[0]['start'], run[-1]['end']))
    if MOMENTS is not None:
        moments = [(float(a), float(a) + 1.1) for a in MOMENTS]
    elif plan.get('slots'):
        moments = [(float(x['from']), float(x['to'])) for x in plan['slots']]
    else:
        moments = [(w['start'], w['start'] + 1.1) for w in words if re.search(r'\d', w.get('text', ''))]

    S = STYLE
    p = V.Page(s)
    js = p.js
    html = []

    # ---------------------------------------------------------------- rows
    def block(row, a, b, cls, label='', inner='', radius=5):
        x, w = X(a), max(3.0, X(b) - X(a))
        i = p.nid('c')
        tag = f'<span>{V.esc(label)}</span>' if label and w > 34 else ''
        rows[row].append((i, x))
        return (f'<div id="{i}" class="blk {cls}" style="left:{x:.1f}px;width:{w:.1f}px;border-radius:{radius}px">{tag}{inner}</div>')

    rows = {r: [] for r in ROWS}
    lane = {r: [] for r in ROWS}
    for w in words:
        lane['T1'].append(block('T1', w['start'], max(w['end'] - .02, w['start'] + .05), 'w', radius=2))
    for k, (a, b) in enumerate(moments):
        lane['V3'].append(block('V3', a, b, 'm', f'fx{k + 1:02d}', radius=6))
    for k, (a, b) in enumerate(phrases):
        lane['V2'].append(block('V2', a, b, 'ph', f'fx{k + 1:02d}', radius=6))
    for g in segs:
        a, b = g['frame'] / V.FPS, (g['frame'] + g['frames']) / V.FPS
        x = X(a)
        bg = f'background-image:url(assets/tl_strip.jpg);background-size:{tw_all:.1f}px {box_h}px;background-position:-{x + 1:.1f}px 0'
        lane['V1'].append(block('V1', a, b - .12, 'sh', inner=f'<div style="position:absolute;inset:0;{bg}"></div>', radius=4))
        i0, i1 = int(x / 2), int(X(b) / 2)
        lane['A1'].append(block('A1', a, b - .12, 'vo', inner=wave_svg(env[i0:i1], int(X(b) - x), box_h, S['voice_ink']), radius=4))
    mid = len(segs) // 2
    for part in (segs[:mid + 1], segs[mid + 1:]):
        if not part:
            continue
        a, b = part[0]['frame'] / V.FPS, (part[-1]['frame'] + part[-1]['frames']) / V.FPS
        i0, i1 = int(X(a) / 2), int(X(b) / 2)
        lane['A2'].append(block('A2', a, b - .12, 'bd', inner=wave_svg(smooth[i0:i1], int(X(b) - X(a)), box_h, S['bed_ink']), radius=4))
    for w in words:
        lane['A3'].append(block('A3', w['start'], w['start'] + .06, 'tk', radius=1))

    row_html = ''
    for k, r in enumerate(ROWS):
        row_html += (f'<div class="row" style="top:{head_h + rule_h + k * row_h}px;height:{row_h}px"><b>{r}</b><i></i>'
                     f'<div class="lane" style="height:{box_h}px;top:{(row_h - box_h) // 2}px">{"".join(lane[r])}</div></div>')

    # ---------------------------------------------------------------- ruler and header
    step = 5 if total <= 25 else 10 if total <= 70 else 30
    rule = ''
    t = 0
    while t <= total + .01:
        rule += f'<u style="left:{X(t):.1f}px">{t // 60}:{t % 60:02d}</u>'
        t += step
    t = 0.0
    while t <= total:
        rule += f'<s style="left:{X(t):.1f}px;height:{10 if abs(t / step - round(t / step)) < .01 else 6}px"></s>'
        t += step / 5
    for g in segs[1:]:
        rule += f'<em style="left:{X(g["frame"] / V.FPS) - 5:.1f}px"></em>'
    icons = (f'<svg width="96" height="24" viewBox="0 0 96 24" fill="{S["ink"]}"><path d="M3 2l13 9-6 1 3 7-3 1-3-7-4 4z"/>'
             f'<circle cx="42" cy="6" r="4"/><rect x="40" y="9" width="4" height="12"/>'
             f'<path d="M66 12a5 5 0 0 1 5-5h4a5 5 0 0 1 0 10h-4a5 5 0 0 1-5-5zm3 0a2 2 0 0 0 2 2h4a2 2 0 0 0 0-4h-4a2 2 0 0 0-2 2z"/>'
             f'<path d="M77 12a5 5 0 0 1 5-5h4a5 5 0 0 1 0 10h-4a5 5 0 0 1-5-5zm3 0a2 2 0 0 0 2 2h4a2 2 0 0 0 0-4h-4a2 2 0 0 0-2 2z"/></svg>')
    html.append(f'''<div id="tlp" style="left:{left}px;top:{top}px;width:{PANEL_W}px;height:{height}px">
<div id="tlin">
<div id="thead" style="height:{head_h}px"><span class="tt">{V.esc(TITLE)}</span><span class="tc" id="tc">00:00:00:00</span>
<span class="ic">{icons}</span><span class="zm"><i></i><b id="zk"></b></span></div>
<div id="rule" style="top:{head_h}px;height:{rule_h}px;left:{NAME_W}px;width:{tw_all}px">{rule}</div>
{row_html}
<div id="ph" style="left:{NAME_W}px;top:{head_h + 2}px;height:{height - head_h - 4}px"><b></b></div>
</div></div>''')
    p.html += html

    p.css.append(f'''
#tlp{{position:absolute;background:{S["panel"]};border-radius:{S["radius"]}px;overflow:hidden;box-shadow:0 10px 34px rgba(0,0,0,.34);visibility:hidden}}
#tlin{{position:absolute;inset:0}}
#thead{{position:absolute;left:0;right:0;top:0;display:flex;align-items:center;padding:0 28px}}
.tt{{font-family:'{S["title_font"]}';font-weight:{S["title_weight"]};font-size:{int(head_h * .52)}px;color:{S["ink"]};letter-spacing:-.01em}}
.tc{{position:absolute;left:0;right:0;text-align:center;font-family:'{S["mono_font"]}';font-weight:{S["mono_weight"]};font-size:{int(head_h * .58)}px;color:{S["code"]};letter-spacing:.03em}}
.ic{{position:absolute;right:178px;top:50%;margin-top:-12px;height:24px;transform:scale(.86)}}
.zm{{position:absolute;right:30px;top:50%;width:128px;height:2px;background:rgba(237,232,219,.34)}}
.zm b{{position:absolute;left:0;top:-6px;width:14px;height:14px;border-radius:50%;background:{S["ink"]}}}
#rule{{position:absolute;font-family:'{S["mono_font"]}';font-size:{max(12, int(rule_h * .42))}px;color:{S["dim"]}}}
#rule u{{position:absolute;top:1px;text-decoration:none;margin-left:2px}}
#rule s{{position:absolute;bottom:2px;width:1.4px;background:{S["dim"]};text-decoration:none;opacity:.8}}
#rule em{{position:absolute;top:0;width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-top:7px solid {S["dim"]}}}
.row{{position:absolute;left:0;right:0}}
.row>b{{position:absolute;left:26px;top:50%;transform:translateY(-50%);font-family:'{S["mono_font"]}';font-weight:{S["mono_weight"]};font-size:{max(14, int(row_h * .46))}px;color:{S["dim"]}}}
.row>i{{position:absolute;left:66px;top:50%;width:5px;height:5px;margin-top:-2px;border-radius:50%;background:{S["dim"]}}}
.lane{{position:absolute;left:{NAME_W}px;width:{tw_all}px}}
.blk{{position:absolute;top:0;height:100%;overflow:hidden;visibility:hidden}}
.blk span{{position:absolute;left:5px;top:2px;font-family:'{S["mono_font"]}';font-weight:700;font-size:{max(10, min(14, int(box_h * .44)))}px;line-height:1.1;color:#2A261A;white-space:nowrap}}
.w{{background:{S["words"]};height:70%;top:15%}}
.m{{background:{S["moments"]}}}
.ph{{background:{S["phrases"]}}}
.sh{{background:#000}}
.vo{{background:{S["voice"]}}}
.bd{{background:{S["bed"]}}}
.tk{{background:{S["phrases"]}}}
#ph{{position:absolute;width:2.4px;background:{S["head"]};visibility:hidden}}
#ph b{{position:absolute;left:-7px;top:0;width:16px;height:18px;background:{S["head"]};border-radius:3px 3px 8px 8px}}''')

    # ---------------------------------------------------------------- the moves
    t_in = when(s, T_IN, .1)
    t_out = when(s, T_OUT, t_in + 41 * FR)
    if t_out - t_in < 34 * FR:
        t_out = t_in + 34 * FR
    end_at = t_out + 6 * FR
    if end_at > s.dur:
        V.die(f'the panel needs {end_at:.2f} s and the slot is {s.dur:.2f} s: make the slot longer or start earlier')
    T = V.T
    js.append("gsap.set('#tlp',{transformOrigin:'50% 50%'});")
    # opening, frame by frame: a thin line that stands up into the panel
    for f, (sx, sy) in enumerate(((.905, .05), (.966, .70), (.985, .87), (.995, .97), (1, 1))):
        js.append(f"tl.set('#tlp',{{autoAlpha:1,scaleX:{sx},scaleY:{sy}}},{T(t_in + f * FR):.3f});")
    js.append("gsap.set('#tlin',{autoAlpha:0});")
    js.append(f"tl.to('#tlin',{{autoAlpha:1,duration:{2 * FR:.3f},ease:'none'}},{T(t_in + 1.5 * FR):.3f});")

    def build(row, start, span):
        for i, x in rows[row]:
            at = start + span * x / tw_all
            js.append(f"tl.set('#{i}',{{visibility:'visible'}},{T(at):.3f});")

    t = lambda f: t_in + f * FR       # frames after the panel starts opening, as in the look this was made to match
    build('V1', t(4), 7 * FR)
    build('A1', t(5), 7 * FR)
    build('V2', t(8), 13 * FR)
    build('A2', t(14), 9 * FR)
    build('V3', t(19), 9 * FR)
    build('T1', t(20), 8 * FR)
    build('A3', t(22), 9 * FR)
    # the playhead: fast start, settles at the far end
    js.append(f"tl.set('#ph',{{visibility:'visible'}},{T(t(7)):.3f});")
    js.append(f"tl.to('#ph',{{x:{tw_all},duration:{24 * FR:.3f},ease:'power2.inOut'}},{T(t(7)):.3f});")
    js.append(f"tl.to('#zk',{{x:112,duration:{18 * FR:.3f},ease:'power2.inOut'}},{T(t(14)):.3f});")
    # the time code rolls with the playhead to the reel's real length
    n = int(round(total * V.FPS))
    js.append(f"(function(){{var o={{v:0}},e=document.getElementById('tc'),p=function(x){{return (x<10?'0':'')+x}};"
              f"tl.to(o,{{v:{n},duration:{24 * FR:.3f},ease:'power2.inOut',onUpdate:function(){{var f=Math.round(o.v),"
              f"ss=Math.floor(f/30);e.textContent='00:'+p(Math.floor(ss/60))+':'+p(ss%60)+':'+p(f%30)}}}},{T(t(7)):.3f});}})();")
    # the exit, frame by frame: head and top rows go, it flattens, flips light for two frames, gone
    js.append(f"tl.to('#thead,#rule',{{autoAlpha:0,duration:{FR:.3f},ease:'none'}},{T(t_out):.3f});")
    js.append(f"tl.set('#ph',{{autoAlpha:0}},{T(t_out + FR):.3f});")
    for f, (sy, flip) in enumerate(((.97, 0), (.84, 0), (.46, 1), (.012, 1))):
        ff = 'invert(1) sepia(.12)' if flip else 'none'
        js.append(f"tl.set('#tlp',{{scaleY:{sy},filter:'{ff}'}},{T(t_out + (f + 1) * FR):.3f});")
    js.append(f"tl.set('#tlp',{{autoAlpha:0}},{T(end_at - .5 * FR + FR):.3f});")
    if SOUND:
        p.sound('whoosh-short', t_in, SOUND)
        p.sound('whoosh-short', t_out, SOUND * .7)
    p.write()
    print(f'  opens {t_in:.2f}s, built by {t(34):.2f}s, flattens {t_out:.2f}s, gone {end_at + .03:.2f}s')
    print(f'snapshot at: {t_in + .07:.2f},{t(8):.2f},{t(14):.2f},{t(22):.2f},{t(30):.2f},{t_out + 2 * FR:.2f},{t_out + 3 * FR:.2f}')


if __name__ == '__main__':
    main()
