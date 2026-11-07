#!/usr/bin/env python3
"""PAGE ROLL (explain): a dark page panel slides up and the picture drops under it, so the face stays in view. The page scrolls
like a screen recording through rows made of the reel's real frames and lines (or the buyer's own long screenshot), flicks
back to one row, zooms in on it, dims everything else, and its lines light up one by one as the speaker names them. Then it
drops away and the picture comes back.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html and assets/pr_*.jpg   (SAFE=1 safe-zone guide, SFX=0 no sounds,
                          CAPTIONS=0 accepted and ignored: the page is the effect)
"""
import json
import os
import re
import shutil
import subprocess

import vgfx as V

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    serif_font='Newsreader',       # the title and the quoted lines, italic
    serif_weight=500,
    sans_font='Inter',             # bullets and lit lines
    sans_weight=500,
    mono_font='JetBrains Mono',    # bars, labels, times
    mono_weight=500,
    page='#17372C',                # deep forest green
    page_dim='#0E2219',            # the page once it is dimmed
    bar='#F3ECDE',                 # cream bar on top of the panel
    bar_ink='#23261E',
    ink='#EFEADC',
    soft='#9FB1A3',                # small print
    gold='#D1B15F',                # the lit line's rule, and the lit values
    lit_bg='#21483A',              # the band behind a lit line
    radius=14,
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
BAR_LEFT = ''         # text on the cream bar, for example 'rils / plan kadrova'. Required
TITLE = ''            # the page's big italic title. Required
LIT = []              # the lines that light up: (word that lights it, regular expression; small label; the line)
                      # Example: [('faktur', 'DOSADNO', 'Pravljenje faktura'), ('ponud', 'DOSADNO', 'Ponude')]. 1 to 4. Required
T_IN = None           # when the panel starts up: a word (regular expression) or slot second. None = 0.1 s into the slot
T_OUT = None          # when it starts down: a word or slot second. None = 0.5 s after the last line lights
PAGE_FILE = None      # a long screenshot from the buyer, in the slot's page/ folder. None = the first picture in page/, if any.
                      # Without one, the page is built from the reel's own frames and lines
PANEL_BOTTOM = None   # lower edge of the panel, screen px. None = measured from the face
SOUND = 0.0           # soft whoosh up and down. 0 = silent
# ==== END CLIP ====

FR = 1 / V.FPS
PANEL_W = 960
BAR_H = 45
ROW_H = 300
HERO_H = 356
TEXT_X = 400
ZOOM = 1.9
MAX_ROWS = 15


def read_json(path, fallback=None):
    try:
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return fallback


def when(s, cue, fallback, after=0.0):
    if cue is None:
        return fallback
    if isinstance(cue, (int, float)):
        return float(cue)
    w = s.find(cue, after)
    if not w:
        V.die(f'the word "{cue}" is not in this slot after {after:.2f}s. Words: {s.word_list()}')
    return w['start']


def grab(aroll, sec, out, vf):
    ff = shutil.which('ffmpeg') or 'ffmpeg'
    r = subprocess.run([ff, '-v', 'error', '-y', '-ss', f'{sec:.3f}', '-i', aroll, '-frames:v', '1', '-update', '1', '-vf', vf, '-q:v', '4', out],
                       capture_output=True, text=True)
    if r.returncode or not os.path.exists(out):
        V.die('could not cut a frame out of the reel: ' + r.stderr.strip()[-160:])


def clock(sec):
    return f'{int(sec // 60)}:{sec % 60:04.1f}'


def phrases_of(words):
    out, run = [], []
    for w in words:
        run.append(w)
        if re.search(r'[,.;:!?]$', w['text'].strip()):
            out.append(run)
            run = []
    if run:
        out.append(run)
    return out


def main():
    s = V.Slot()
    print('words: ' + s.word_list())
    print(s.where())
    if not BAR_LEFT.strip() or not TITLE.strip():
        V.die('write BAR_LEFT and TITLE in the CLIP block, in the reel\'s language')
    page_dir = 'page'
    pics = sorted(f for f in os.listdir(page_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))) if os.path.isdir(page_dir) else []
    shot = PAGE_FILE or (pics[0] if pics else None)
    if shot and not os.path.isfile(os.path.join(page_dir, shot)):
        V.die(f'{shot} is not in the slot\'s page/ folder')
    if not shot and not (1 <= len(LIT) <= 4):
        V.die('write 1 to 4 LIT lines in the CLIP block: the things the speaker names')
    proj = s.clip.get('project')

    # ---------------------------------------------------------------- places: the panel on top, the face under it
    top = V.SAFE_TOP + 2
    head_top, chin = s.head_top, s.chin
    face = chin - head_top
    if PANEL_BOTTOM is not None:
        bottom = int(PANEL_BOTTOM)
    else:
        bottom = max(top + 480, min(top + 1044, V.SAFE_BOTTOM + 90 - face - 8))
    if chin + 40 < V.SAFE_BOTTOM - 480 and head_top > bottom:
        V.die('unexpected layout: type PANEL_BOTTOM')
    if bottom - top < 480:
        V.die(f'only {bottom - top} px for the panel with the face under it: the face is too large on this shot')
    push = max(0, bottom + 8 - head_top)
    if chin + push > 1920 - 10:
        V.die(f'the face would leave the bottom of the frame ({chin + push} px): the shot is too tight for this effect')
    height = bottom - top
    left = (1080 - PANEL_W) // 2
    print(f'  panel y {top} to {bottom}; the picture drops {push} px, so the face sits at y {head_top + push} to {chin + push}')
    print(f'  in a reel: add the slot with  fx_add.py ... --caption-y {bottom - 38}  so the captions ride the panel\'s lower edge')

    # ---------------------------------------------------------------- times
    t_in = when(s, T_IN, .1)
    lit_times = []
    after = t_in
    for row in LIT:
        at = when(s, row[0], None, after)
        lit_times.append(at)
        after = at
    t_ready = t_in + 47 * FR
    if lit_times and lit_times[0] < t_ready:
        print(f'note: the first line lights at {lit_times[0]:.2f}s, before the zoom has settled ({t_ready:.2f}s): start the panel earlier for the full scroll')
    t_out = when(s, T_OUT, (lit_times[-1] + .5) if lit_times else t_in + 96 * FR, t_in)
    t_end = t_out + 5 * FR
    if t_end > s.dur + .001:
        V.die(f'the panel leaves at {t_end:.2f}s and the slot is {s.dur:.2f}s long: make the slot longer')

    S = STYLE
    T = V.T
    js = []
    inner = ''
    target_y = HERO_H
    page_h = HERO_H

    if shot:
        # ------------------------------------------------------------ the buyer's own long screenshot
        inner = f'<img id="shot" src="{page_dir}/{shot}" style="display:block;width:{PANEL_W}px">'
        ff = shutil.which('ffprobe') or 'ffprobe'
        size = subprocess.run([ff, '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0',
                               os.path.join(page_dir, shot)], capture_output=True, text=True).stdout.strip().split(',')
        try:
            page_h = int(int(size[1]) * PANEL_W / int(size[0]))
        except (ValueError, IndexError):
            V.die(f'could not read the size of {shot}')
        if page_h < height * 1.5:
            V.die(f'{shot} is only {page_h} px tall at the panel\'s width: it needs to be a long page to scroll')
    else:
        # ------------------------------------------------------------ a page from the reel's own frames and lines
        if not proj or not os.path.isfile(os.path.join(proj, 'words.json')):
            V.die('without a screenshot in page/ the page is built from the reel: make the slot with fx_new.py --project')
        aroll = os.path.join(proj, 'assets', 'aroll.mp4')
        words = read_json(os.path.join(proj, 'words.json'), [])
        words = words.get('words', words) if isinstance(words, dict) else words
        words = [dict(w, text=w.get('text', w.get('word', ''))) for w in words]
        segs = read_json(os.path.join(proj, 'segments.json'), []) or []
        total = (segs[-1]['frame'] + segs[-1]['frames']) / V.FPS if segs else words[-1]['end']
        rows = phrases_of(words)

        def where_in(sec):
            k = next((n for n, g in enumerate(segs) if g['frame'] / V.FPS <= sec < (g['frame'] + g['frames']) / V.FPS), 0)
            return f'Kadar {k + 1} od {len(segs)}, {sec:.1f} s u rilu'

        # the row that gets the zoom: the phrase the first named thing falls in
        t0 = s.t0 + (lit_times[0] if lit_times else t_in)
        hit = next((i for i, r in enumerate(rows) if r[-1]['end'] >= t0 - .05), 0)
        first = max(0, min(hit - 6, len(rows) - MAX_ROWS))
        rows = rows[first:first + MAX_ROWS]
        hit -= first
        if len(rows) < 4:
            V.die('this reel has too few spoken phrases to fill a page')
        target_y = HERO_H + hit * ROW_H
        page_h = HERO_H + len(rows) * ROW_H
        os.makedirs('assets', exist_ok=True)
        bars = ''
        if segs:
            shades = ('#3E6F5B', '#2C5545', '#5C8C77', '#35604F', '#7FA893', '#2A4F40')
            bars = ''.join(f'<i style="width:{g["frames"] / V.FPS / total * 100:.2f}%;background:{shades[k % 6]}"></i>' for k, g in enumerate(segs))
        inner = (f'<div class="hero" style="height:{HERO_H}px"><div class="hm">PLAN · {len(segs)} KADROVA · {total:.1f} S · {len(words)} REČI</div>'
                 f'<div class="ht">{V.esc(TITLE)}</div><div class="hb">{bars}</div></div>')
        crop_top = max(0, head_top - 120)
        for i, r in enumerate(rows):
            a, b = r[0]['start'], r[-1]['end']
            line = ' '.join(w['text'] for w in r)
            for k, (when_, kind) in enumerate(((a + .05, 'p'), ((a + b) / 2, 'p'), (max(a, b - .1), 'w'))):
                out = f'assets/pr_{i:02d}_{k}.jpg'
                vf = 'scale=234:-2' if kind == 'p' else f'crop=1080:608:0:{crop_top},scale=530:-2'
                grab(aroll, when_, out, vf)
            thumbs = (f'<img class="tp" src="assets/pr_{i:02d}_0.jpg" style="left:36px"><img class="tp" src="assets/pr_{i:02d}_1.jpg" style="left:160px">'
                      f'<img class="tw" src="assets/pr_{i:02d}_2.jpg" style="left:284px;width:96px;height:170px;object-fit:cover">')
            meta = f'{first + i + 1:02d} &nbsp;{clock(a)}-{clock(b)} &nbsp;{b - a:.1f}s &nbsp;<u></u> Kadar'
            if i == hit and LIT:
                lines = ''.join(f'<div class="lr" id="lr{k}"><b>{V.esc(lab)}</b><span>{V.esc(txt)}</span><em id="ul{k}"></em></div>'
                                for k, (_, lab, txt) in enumerate(LIT))
                body = f'<div class="q" style="font-size:26px">&ldquo;{V.esc(line)}&rdquo;</div>{lines}'
                cls = ' hit'
            else:
                dots = ''.join(f'<div class="kv"><b>{k_}</b><span>{V.esc(v_)}</span></div>' for k_, v_ in
                               (('TRAJANJE', f'{b - a:.1f} s'), ('REČI', str(len(r)))))
                body = f'<div class="q">&ldquo;{V.esc(line)}&rdquo;</div><div class="bl">{V.esc(where_in(a))}</div>{dots}'
                cls = ''
            inner += (f'<div class="rw{cls}" id="rw{i}" style="top:{HERO_H + i * ROW_H}px">{thumbs}<div class="tx"><div class="mt">{meta}</div>{body}</div></div>')

    # ---------------------------------------------------------------- the moves
    view = height - BAR_H
    max_scroll = max(0, page_h - view)
    Y = lambda y: -min(max_scroll, max(0.0, y))
    t = lambda f: t_in + f * FR
    js.append(f"gsap.set('#panel',{{y:{1920 - top}}});")
    js.append(f"tl.set('#panel',{{autoAlpha:1}},{T(t_in):.3f});")
    js.append(f"tl.to('#panel',{{y:0,duration:{10 * FR:.3f},ease:'expo.out'}},{T(t_in):.3f});")
    js.append(f"tl.to('#drop',{{y:{push},duration:{10 * FR:.3f},ease:'expo.out'}},{T(t_in):.3f});")
    if shot:
        y1, y2, y3 = page_h * .22, page_h * .5, page_h * .85
    else:
        y1, y2 = HERO_H + ROW_H * 2.4, HERO_H + ROW_H * 5.1
        y3 = None
    F = "force3D:false"
    js.append(f"tl.to('#pg',{{y:{Y(y1):.0f},duration:{7 * FR:.3f},ease:'power3.inOut',{F}}},{T(t(12)):.3f});")
    js.append(f"tl.to('#pg',{{y:{Y(y1 + 26):.0f},duration:{8 * FR:.3f},ease:'none',{F}}},{T(t(19)):.3f});")
    js.append(f"tl.to('#pg',{{y:{Y(y2):.0f},duration:{7 * FR:.3f},ease:'power3.inOut',{F}}},{T(t(27)):.3f});")
    if shot:
        js.append(f"tl.to('#pg',{{y:{Y(y3):.0f},duration:{9 * FR:.3f},ease:'power3.inOut',{F}}},{T(t(38)):.3f});")
    else:
        zy = -(target_y + 24) * ZOOM + 18
        zx = -TEXT_X * ZOOM + 26
        js.append(f"tl.to('#pg',{{x:{zx:.0f},y:{zy:.0f},scale:{ZOOM},duration:{9 * FR:.3f},ease:'power3.inOut',{F}}},{T(t(38)):.3f});")
        js.append(f"tl.to('#pgw',{{backgroundColor:'{S['page_dim']}',duration:{4 * FR:.3f},ease:'none'}},{T(t(44)):.3f});")
        js.append(f"tl.to('.rw:not(.hit),.hero',{{opacity:.28,duration:{4 * FR:.3f},ease:'none'}},{T(t(44)):.3f});")
        if LIT:
            js.append(f"tl.to('.hit .q,.hit .mt,.lr',{{opacity:.5,duration:{4 * FR:.3f},ease:'none'}},{T(t(44)):.3f});")
        for k, at in enumerate(lit_times):
            js.append(f"tl.to('#lr{k}',{{opacity:1,backgroundColor:'{S['lit_bg']}',duration:{3 * FR:.3f},ease:'none'}},{T(at):.3f});")
            js.append(f"tl.fromTo('#ul{k}',{{scaleX:0}},{{scaleX:1,duration:{6 * FR:.3f},ease:'power2.out',immediateRender:false}},{T(at):.3f});")
    js.append(f"tl.to('#panel',{{y:{1920 - top},duration:{5 * FR:.3f},ease:'power2.in'}},{T(t_out):.3f});")
    js.append(f"tl.to('#drop',{{y:0,duration:{5 * FR:.3f},ease:'power2.in'}},{T(t_out):.3f});")
    js.append(f"tl.set('#panel',{{autoAlpha:0}},{T(t_end):.3f});")

    # ---------------------------------------------------------------- page
    audio = ''
    if SOUND and V.SFX_ON and os.path.exists('assets/sfx/whoosh-short.mp3'):
        audio = (f'<audio id="sfx0" src="assets/sfx/whoosh-short.mp3" data-start="{t_in:.3f}" data-duration=".6" data-track-index="10" data-volume="{SOUND:.3f}"></audio>'
                 f'<audio id="sfx1" src="assets/sfx/whoosh-short.mp3" data-start="{max(0, t_out - .1):.3f}" data-duration=".6" data-track-index="11" data-volume="{SOUND * .7:.3f}"></audio>')
    n_cuts = len(read_json(os.path.join(proj, 'segments.json'), []) or []) if proj else 0
    bar_right = f'{n_cuts} kadrova' if n_cuts else ''
    v = f'muted playsinline data-start="0" data-media-start="0" data-duration="{s.dur:.4f}"'
    css = f'''
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:#000}}
#root{{position:relative;width:1080px;height:1920px;overflow:hidden;background:#000}}
.lay{{position:absolute;left:0;top:0;width:1080px;height:1920px;display:block}}
#drop{{position:absolute;left:0;top:0;width:1080px;height:1920px;overflow:hidden;-webkit-mask-image:linear-gradient(180deg,transparent 0,#000 150px);mask-image:linear-gradient(180deg,transparent 0,#000 150px)}}
#panel{{position:absolute;left:{left}px;top:{top}px;width:{PANEL_W}px;height:{height}px;border-radius:{S["radius"]}px;overflow:hidden;background:{S["page"]};box-shadow:0 14px 44px rgba(0,0,0,.4);visibility:hidden}}
#pbar{{position:absolute;left:0;right:0;top:0;height:{BAR_H}px;background:{S["bar"]};display:flex;align-items:center;justify-content:space-between;padding:0 22px;font-family:'{S["mono_font"]}';font-weight:700;font-size:17px;color:{S["bar_ink"]};z-index:3}}
#pbar i{{font-style:normal;font-weight:{S["mono_weight"]};opacity:.62;font-size:15px}}
#pgw{{position:absolute;left:0;right:0;top:{BAR_H}px;bottom:0;overflow:hidden;background:{S["page"]}}}
#pg{{position:absolute;left:0;top:0;width:{PANEL_W}px;height:{page_h}px;transform-origin:0 0}}
.hero{{position:absolute;left:0;right:0;top:0;padding:26px 36px}}
.hm{{font-family:'{S["mono_font"]}';font-size:14px;letter-spacing:.14em;color:{S["soft"]}}}
.ht{{font-family:'{S["serif_font"]}';font-style:italic;font-weight:{S["serif_weight"]};font-size:66px;line-height:1.1;color:{S["ink"]};margin-top:14px;white-space:nowrap}}
.hb{{display:flex;height:28px;gap:2px;margin-top:44px}}
.hb i{{display:block;height:100%}}
.rw{{position:absolute;left:0;right:0;height:{ROW_H}px;border-top:1.5px solid rgba(239,234,220,.1)}}
.tp,.tw{{position:absolute;top:24px;width:116px;height:206px;object-fit:cover;background:#000}}
.tx{{position:absolute;left:{TEXT_X}px;top:24px;width:{PANEL_W - TEXT_X - 34}px;font-family:'{S["sans_font"]}';font-weight:{S["sans_weight"]};color:{S["ink"]}}}
.hit .tx{{width:{int((PANEL_W - 52) / ZOOM)}px}}
.mt{{font-family:'{S["mono_font"]}';font-size:13px;color:{S["soft"]};white-space:nowrap;display:flex;align-items:center;gap:0}}
.mt u{{display:inline-block;width:10px;height:10px;background:{S["soft"]};margin:0 6px 0 0;opacity:.7;text-decoration:none}}
.q{{font-family:'{S["serif_font"]}';font-style:italic;font-weight:{S["serif_weight"]};font-size:25px;line-height:1.22;color:{S["ink"]};margin-top:10px}}
.bl{{font-size:15px;line-height:1.3;margin-top:10px;padding-left:16px;position:relative;white-space:nowrap;overflow:hidden}}
.bl:before{{content:'';position:absolute;left:2px;top:7px;width:6px;height:6px;border-radius:50%;background:{S["ink"]}}}
.kv{{display:flex;gap:14px;font-size:14px;margin-top:6px}}
.kv b{{font-family:'{S["mono_font"]}';font-weight:{S["mono_weight"]};color:{S["soft"]};width:82px;font-size:12px;letter-spacing:.06em}}
.lr{{position:relative;display:flex;gap:14px;align-items:baseline;padding:7px 8px 8px;margin-top:6px;font-size:17px;white-space:nowrap}}
.lr b{{font-family:'{S["mono_font"]}';font-weight:700;color:{S["soft"]};font-size:12px;letter-spacing:.08em;flex:none}}
.lr span{{color:{S["ink"]}}}
.lr em{{position:absolute;left:8px;right:8px;bottom:2px;height:2px;background:{S["gold"]};transform-origin:0 50%;transform:scaleX(0)}}
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
<div id="root" data-composition-id="main" data-start="0" data-duration="{s.dur:.4f}" data-width="1080" data-height="1920">
  <audio id="bga" src="assets/aroll.mp4" data-start="0" data-media-start="0" data-duration="{s.dur:.4f}" data-track-index="2" data-volume="1"></audio>
  {audio}
  <video id="bgv" class="lay" src="assets/aroll.mp4" {v} data-track-index="0"></video>
  <div id="drop"><video id="drv" class="lay" src="assets/aroll.mp4" {v} data-track-index="1"></video></div>
  <div id="panel">
    <div id="pbar"><span>{V.esc(BAR_LEFT)}</span><i>{V.esc(bar_right)}</i></div>
    <div id="pgw"><div id="pg">{inner}</div></div>
  </div>
  {V.SAFE_GUIDE if V.SAFE else ''}
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
tl.set({{}}, {{}}, {s.dur:.3f});
window.__timelines["main"] = tl;
</script>
</body>
</html>
'''
    with open('index.html', 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(page)
    print(f'index.html written: {s.frames} frames ({s.dur:.2f}s), safe guide {"ON" if V.SAFE else "off"}')
    print('  panel up {:.2f}s, zoom done {:.2f}s, lines {}, down {:.2f}s'.format(t_in, t_ready, ', '.join(f'{x:.2f}' for x in lit_times), t_out))
    snaps = [t(4), t(10), t(16), t(24), t(32), t(44), t(50)] + [x + .25 for x in lit_times] + [t_out + 2 * FR, t_out + 4 * FR]
    print('snapshot at: ' + ','.join(f'{x:.2f}' for x in snaps))


if __name__ == '__main__':
    main()
