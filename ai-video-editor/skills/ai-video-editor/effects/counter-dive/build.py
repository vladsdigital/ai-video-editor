#!/usr/bin/env python3
"""COUNTER DIVE: a deep green plaque stands up above the head with a rolling length counter that runs from the raw footage's
real length down to the finished reel's real length. The label swaps, the plaque folds away, and the whole live frame shrinks
into a smaller copy of itself in a thin cream border, again and again inside itself, then the picture pushes in, tips, blurs
and comes out in the next shot.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html   (SAFE=1 safe-zone guide, SFX=0 no sounds, CAPTIONS=0 accepted and ignored)
"""
import json
import os
import shutil
import subprocess

import vgfx as V

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    digit_font='Instrument Serif',  # the counter
    digit_weight=400,
    label_font='JetBrains Mono',    # the small label
    label_weight=500,
    plaque='#17392E',               # deep forest green
    cell='rgba(0,0,0,.2)',
    digit='#F3ECDE',                # cream
    label='#CDB56A',                # gold
    border='#F4EFE3',               # the thin line around the shrinking frame
    radius=16,
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
RAW_SECONDS = None      # the raw length the counter starts from. None = the summed length of the reel's source clips
FINAL_SECONDS = None    # the length it lands on. None = the finished reel's real length
RAW_LABEL = ''          # small label while it rolls, for example 'SIROV SNIMAK'. Required
FINAL_LABEL = ''        # the label it swaps to when it lands, for example 'OVAJ RILS'. Required
T_IN = None             # when the plaque opens: a word of the line (regular expression) or a slot second. None = 85 frames before the exit
PLACE = None            # where the small frame goes: 'above', 'left', 'right'. None = measured
LEVELS = 4              # how many copies inside each other
SOUND = 0.08            # the faint bell when the counter lands. 0 = silent
# ==== END CLIP ====

FR = 1 / V.FPS
SCALE = .355            # each copy, against the one around it


def read_json(path, fallback=None):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return fallback


def probe(path):
    fp = shutil.which('ffprobe') or 'ffprobe'
    out = subprocess.run([fp, '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path], capture_output=True, text=True).stdout
    try:
        return float(out.strip())
    except ValueError:
        return None


def real_lengths(s):
    """(raw seconds, finished seconds) from the reel project; each one None when it cannot be read"""
    proj = s.clip.get('project')
    if not proj:
        return None, None
    segs = read_json(os.path.join(proj, 'segments.json'), []) or []
    final = (segs[-1]['frame'] + segs[-1]['frames']) / V.FPS if segs else None
    srcs = read_json(os.path.join(proj, 'sources.json'), {}) or {}
    lens = [probe(p) for p in srcs.values() if os.path.isfile(p)]
    raw = sum(x for x in lens if x) if lens and all(lens) else None
    return raw, final


def main():
    s = V.Slot()
    print('words: ' + s.word_list())
    print(s.where())
    if not RAW_LABEL.strip() or not FINAL_LABEL.strip():
        V.die('write RAW_LABEL and FINAL_LABEL in the CLIP block, in the reel\'s language')
    raw_m, final_m = real_lengths(s)
    raw = RAW_SECONDS if RAW_SECONDS is not None else raw_m
    final = FINAL_SECONDS if FINAL_SECONDS is not None else final_m
    if raw is None or final is None:
        V.die('no real lengths: run it in a reel project with its source clips in place, or type RAW_SECONDS and FINAL_SECONDS. Never made-up numbers')
    raw, final = int(round(raw)), int(round(final))
    if raw <= final:
        V.die(f'the raw length ({raw} s) is not longer than the finished one ({final} s): nothing to count down')
    cuts = s.clip.get('cut_frames') or []
    cut = cuts[0] / V.FPS if cuts else s.dur
    head = (s.layout or {}).get('head') or {}
    head_top, chin = s.head_top, s.chin

    # ---------------------------------------------------------------- plaque above the head
    p_bottom = head_top - 12
    p_top = V.SAFE_TOP + 2
    p_h = min(p_bottom - p_top, 342)
    if p_h >= 190:
        p_top = p_bottom - p_h if p_h == 342 else p_top
    else:                                  # a high head: the chest instead, clear of the caption line
        head_ = (s.layout or {}).get('head') or {}
        chin2 = max(s.chin, s.head_top + 1.6 * int(head_.get('width') or 300))   # the measured box can stop at the nose
        p_top = int(chin2 + 36)
        p_h = min(V.SAFE_BOTTOM - 40 - p_top, 300)
        p_bottom = p_top + p_h
        if p_h < 190:
            V.die(f'no room for the plaque: {head_top - 12 - V.SAFE_TOP} px above the head and {max(p_h, 0)} px on the chest, it needs 190. Leave this effect out on this shot')
        print(f'placement: no room above the head, so the plaque sits on the chest. In a reel: fx_add.py ... --caption-y {p_bottom + 12}')
    two_min = raw >= 600
    cells = 4 if two_min else 3
    lab_h = int(p_h * .17)
    cell_h = p_h - lab_h - 22
    cell_w = int(cell_h * .62)
    colon = int(cell_w * .42)
    gap = 10
    p_w = cells * cell_w + (cells - 1) * gap + colon + 72
    p_left = (1080 - p_w) // 2
    fs = int(cell_h * 1.0)

    # ---------------------------------------------------------------- the small frame: above the head, else in the wall beside it
    side_l = int(head.get('side_left') or s.cx - 180)
    side_r = int(head.get('side_right') or s.cx + 180)
    room_above = head_top - 10 - V.SAFE_TOP
    room_left = side_l - 12 - V.SAFE_SIDE
    room_right = (1080 - V.SAFE_SIDE) - (side_r + 12)
    place = PLACE
    if place is None:
        place = 'above' if room_above / 1920 >= .3 else ('left' if room_left >= room_right else 'right')
    if place == 'above':
        k = min(SCALE, room_above / 1920)
        fx, fy = 540 - 540 * k, V.SAFE_TOP + 4
    else:
        room = room_left if place == 'left' else room_right
        k = min(SCALE, room / 1080)
        fx = (V.SAFE_SIDE + 8) if place == 'left' else (1080 - V.SAFE_SIDE - 8 - 1080 * k)
        fy = V.SAFE_TOP + 4
    if k < .2:
        V.die(f'no room for the shrinking frame: {room_above} px above the head, {room_left} left, {room_right} right. Leave this effect out on this shot')
    print(f'  plaque y {p_top} to {p_bottom}, {p_w} px wide; frame {place}: scale {k:.3f} at {fx:.0f},{fy:.0f}; counter {raw // 60}:{raw % 60:02d} to {final // 60}:{final % 60:02d}')

    # ---------------------------------------------------------------- times (frames as in the look this was made to match)
    if not cuts:
        V.die('this effect leaves through a cut: make the slot across one cut of the reel, about 0.4 s into the next shot')
    t_cut = cut
    t_in = float(T_IN) if isinstance(T_IN, (int, float)) else None
    if isinstance(T_IN, str):
        w = s.find(T_IN)
        if not w:
            V.die(f'the word "{T_IN}" is not in this slot. Words: {s.word_list()}')
        t_in = w['start']
    if t_in is None:
        t_in = max(0.0, t_cut - 85 * FR)
    if t_cut - t_in < 62 * FR:
        V.die(f'only {t_cut - t_in:.1f} s from the start to the cut: the whole move needs about 2.1 s, best 2.8 s')
    t = lambda f: t_in + f * FR
    T = V.T
    js = []

    # ---------------------------------------------------------------- the counter
    def strip(n):
        return ''.join(f'<i>{d}</i>' for d in list(range(n)) + [0])

    col = []
    if two_min:
        col.append(('mt', 10))
    col.append(('mu', 10))
    col.append(('st', 6))
    col.append(('su', 10))
    cell_html = []
    for k_, (name, n) in enumerate(col):
        if name == 'st':
            cell_html.append('<b class="cln">:</b>')
        cell_html.append(f'<div class="cel"><div class="str" id="{name}">{strip(n)}</div></div>')
    counter = (f'<div id="pq" style="left:{p_left}px;top:{p_top}px;width:{p_w}px;height:{p_h}px">'
               f'<div id="pqin" style="height:{p_h}px"><div class="lb"><div id="lbs"><span>{V.esc(RAW_LABEL)}</span><span>{V.esc(FINAL_LABEL)}</span></div></div>'
               f'<div class="cls">{"".join(cell_html)}</div></div></div>')
    js.append(f"""var cv={{v:{raw}}},H={cell_h};
function cvp(){{var v=cv.v,u=((v%10)+10)%10,c=Math.max(0,u-9),w=v%60,ts=Math.floor(w/10)+Math.max(0,(w%10)-9),cm=Math.max(0,w-59),m=Math.floor(v/60)+cm;
 gsap.set('#su',{{y:-u*H}});gsap.set('#st',{{y:-(ts%6)*H}});gsap.set('#mu',{{y:-(m%10)*H}});
 {"gsap.set('#mt',{y:-(Math.floor(m/10)+Math.max(0,(m%10)-9))*H});" if two_min else ''}}}
cvp();""")

    # the plaque: a thin line that stands up from its lower edge
    js.append(f"gsap.set('#pq',{{clipPath:'inset(100% 0 0 0 round {STYLE['radius']}px)'}});")
    for f, (l, top_cut, bot_cut) in enumerate(((.03, .98, 0), (0, .53, 0), (0, .26, 0), (0, .10, 0), (0, 0, 0))):
        js.append(f"tl.set('#pq',{{autoAlpha:1,clipPath:'inset({top_cut * 100:.0f}% {l * 100:.0f}% {bot_cut}% {l * 100:.0f}% round {STYLE['radius']}px)'}},{T(t(f)):.3f});")
    # the roll, then a small pop as it lands, then the label swaps
    js.append(f"tl.to(cv,{{v:{final},duration:{19 * FR:.3f},ease:'power2.inOut',onUpdate:cvp}},{T(t(8)):.3f});")
    js.append(f"tl.set('#pq',{{scale:1.025}},{T(t(28)):.3f}); tl.set('#pq',{{scale:1.012}},{T(t(29)):.3f}); tl.set('#pq',{{scale:1}},{T(t(30)):.3f});")
    js.append(f"tl.to('#lbs',{{yPercent:-50,duration:{3 * FR:.3f},ease:'power2.inOut'}},{T(t(30)):.3f});")
    # it folds up into a bar, its lower edge rising
    for f, cutb in enumerate((22, 50, 82)):
        js.append(f"tl.set('#pq',{{clipPath:'inset(0% 0% {cutb}% 0% round {STYLE['radius']}px)'}},{T(t(34 + f)):.3f});")
    js.append(f"tl.set('#pq',{{autoAlpha:0}},{T(t(37)):.3f});")

    # ---------------------------------------------------------------- the frames inside each other
    v = f'muted playsinline data-start="0" data-media-start="0" data-duration="{int(s.dur * 1000) / 1000:.3f}"'
    levels = max(1, min(int(LEVELS), 5))
    nest = ''
    for L in range(levels, 0, -1):
        nest = (f'<div class="lvl" id="lv{L}"><video id="fv{L}" class="lay" src="assets/aroll.mp4" {v} data-track-index="{2 + L}"></video>{nest}'
                f'<div class="bd" id="bd{L}"></div></div>')
    start = 35
    cum = 1.0
    for L in range(1, levels + 1):
        at = t(start) if L == 1 else t(start + 13 + 4 * (L - 2))
        span = 12 if L == 1 else 8
        b0, b1 = 3.0 / cum, 2.8 / (cum * k)
        cum *= k
        js.append(f"gsap.set('#bd{L}',{{borderWidth:{b0:.2f}}});")
        js.append(f"tl.set('#lv{L}',{{autoAlpha:1}},{T(at):.3f});")
        js.append(f"tl.to('#lv{L}',{{x:{fx:.2f},y:{fy:.2f},scale:{k:.4f},duration:{span * FR:.3f},ease:'expo.out'}},{T(at):.3f});")
        js.append(f"tl.to('#bd{L}',{{borderWidth:{b1:.2f},duration:{span * FR:.3f},ease:'expo.out'}},{T(at):.3f});")

    # ---------------------------------------------------------------- the dive and the next shot
    ox, oy = fx + 540 * k, fy
    js.append(f"gsap.set('#stage',{{transformOrigin:'{ox:.0f}px {oy:.0f}px'}});")
    js.append(f"tl.to('#stage',{{scale:1.66,duration:{7 * FR:.3f},ease:'power2.in'}},{T(t_cut - 12 * FR):.3f});")
    for f, (sc, ro, bl) in ((-5, (1.66, 0, 0)), (-4, (1.56, 0, 1)), (-3, (1.46, 2, 3)), (-2, (1.12, 7, 12)), (-1, (1.10, 8, 16))):
        js.append(f"tl.set('#stage',{{scale:{sc},rotation:{ro},filter:'blur({bl}px)'}},{T(t_cut + f * FR):.3f});")
    js.append(f"tl.set('.lvl',{{autoAlpha:0}},{T(t_cut):.3f});")
    js.append(f"gsap.set('#stage',{{transformOrigin:'{ox:.0f}px {oy:.0f}px'}});")
    for f, (sc, bl) in enumerate(((1.20, 22), (1.10, 13), (1.04, 7), (1.01, 2), (1, 0))):
        js.append(f"tl.set('#stage',{{transformOrigin:'540px 960px',scale:{sc},rotation:0,filter:'blur({bl}px)'}},{T(t_cut + f * FR):.3f});")
    if t_cut + 5 * FR > s.dur:
        print('note: the slot ends before the blur has cleared: make it about 0.4 s longer past the cut')

    # ---------------------------------------------------------------- page
    S = STYLE
    audio = ''
    if SOUND and V.SFX_ON and os.path.exists('assets/sfx/chime.mp3'):
        audio = (f'<audio id="sfx0" src="assets/sfx/chime.mp3" data-start="{t(29):.3f}" data-duration="{min(.9, s.dur - t(29)):.3f}" '
                 f'data-track-index="10" data-volume="{SOUND:.3f}"></audio>')
    css = f'''
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:#000}}
#root{{position:relative;width:1080px;height:1920px;overflow:hidden;background:#000}}
#stage{{position:absolute;inset:0}}
.lay{{position:absolute;left:0;top:0;width:1080px;height:1920px;display:block}}
.lvl{{position:absolute;left:0;top:0;width:1080px;height:1920px;overflow:hidden;transform-origin:0 0;visibility:hidden}}
.bd{{position:absolute;inset:0;border:0 solid {S["border"]}}}
#pq{{position:absolute;background:{S["plaque"]};border-radius:{S["radius"]}px;visibility:hidden;overflow:hidden}}
#pqin{{position:absolute;left:0;right:0;top:0}}
.lb{{position:absolute;left:0;right:0;top:{int(lab_h * .22)}px;height:{int(lab_h * .72)}px;overflow:hidden;text-align:center}}
#lbs{{display:flex;flex-direction:column}}
#lbs span{{height:{int(lab_h * .72)}px;line-height:{int(lab_h * .72)}px;font-family:'{S["label_font"]}';font-weight:{S["label_weight"]};font-size:{max(18, int(lab_h * .46))}px;letter-spacing:.22em;color:{S["label"]};white-space:nowrap}}
.cls{{position:absolute;left:0;right:0;top:{lab_h + 6}px;display:flex;justify-content:center;align-items:center;gap:{gap}px;height:{cell_h}px}}
.cel{{width:{cell_w}px;height:{cell_h}px;background:{S["cell"]};overflow:hidden;position:relative;border-radius:3px}}
.str{{position:absolute;left:0;top:0;width:100%}}
.str i{{display:block;height:{cell_h}px;line-height:{cell_h}px;text-align:center;font-style:normal;font-family:'{S["digit_font"]}';font-weight:{S["digit_weight"]};font-size:{fs}px;color:{S["digit"]}}}
.cln{{width:{colon}px;text-align:center;font-family:'{S["digit_font"]}';font-weight:400;font-size:{int(fs * .8)}px;color:{S["digit"]};line-height:1;margin-top:-{int(fs * .08)}px}}
'''
    page = f'''<!doctype html>
<html lang="sr" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<link rel="stylesheet" href="assets/fonts/fonts.css" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{css}</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{int(s.dur * 1000) / 1000:.3f}" data-width="1080" data-height="1920">
  <audio id="bga" src="assets/aroll.mp4" data-start="0" data-media-start="0" data-duration="{int(s.dur * 1000) / 1000:.3f}" data-track-index="2" data-volume="1"></audio>
  {audio}
  <div id="stage">
    <video id="bgv" class="lay" src="assets/aroll.mp4" {v} data-track-index="0"></video>
    {nest}
    {counter}
  </div>
  {V.SAFE_GUIDE if V.SAFE else ''}
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
tl.set({{}}, {{}}, {int(s.dur * 1000) / 1000:.3f});
window.__timelines["main"] = tl;
</script>
</body>
</html>
'''
    with open('index.html', 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(page)
    print(f'index.html written: {s.frames} frames ({s.dur:.2f}s), safe guide {"ON" if V.SAFE else "off"}')
    print(f'  plaque {t_in:.2f}s, rolls {t(8):.2f} to {t(27):.2f}s, frame shrinks {t(35):.2f}s, push in {t_cut - 12 * FR:.2f}s, cut {t_cut:.2f}s')
    print(f'snapshot at: {t(3):.2f},{t(14):.2f},{t(22):.2f},{t(32):.2f},{t(37):.2f},{t(44):.2f},{t(58):.2f},{t_cut - .2:.2f},{t_cut - .05:.2f},{t_cut + .05:.2f}')


if __name__ == '__main__':
    main()
