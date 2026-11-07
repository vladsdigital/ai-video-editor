#!/usr/bin/env python3
"""FILM GATE (mood): the shot turns into running 35mm film. The look cuts on on the word, sprocket rails snap in from both
sides, the picture rolls one whole frame down into place, then it runs: the holes step past at the film's speed, an
optical soundtrack strip beside them is drawn from the voice in this very clip, with flicker, weave and dust.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html and assets/soundtrack.png   (SAFE=1 safe-zone guide, SFX=0 no sounds)
"""
import os
import random
import subprocess

os.environ.setdefault('PREVIEW', '1')    # a full picture effect: the footage is always in the page
import numpy as np
from PIL import Image

import grade as G
import vgfx as V

# ==== STYLE (the reel's look wins: the rail is film, only the tiny edge print takes a font) ====
STYLE = dict(
    small_font='JetBrains Mono', small_weight=500,
    rail='#111211',                # film base
    hole='#EEEBE2',                # the sprocket holes, cream
    track='#CBCAC5',               # the soundtrack strip
    edge_print='#6E6D66',          # the tiny print along the film's edge
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
ON = None           # the word it starts on (a word from words.json) or seconds. None = the first word after 0.3 s
BACK = 'auto'       # when it cuts back: seconds, a word, 'auto' = 6 frames before the slot ends, None = runs to a cut
LOOK = 'film'       # 'film', 'mood' or 'warm' (grade.py)
GRAIN = 8           # moving grain. 0 = none
EDGE_PRINT = 'BEZBEDNOSNI FILM'   # tiny print along the right edge. '' = none
DUST = 1.0          # how much dust and flicker. 0 = clean
RATTLE = 1.0        # volume of the projector's ticks. 0 = silent
# ==== END CLIP ====

RAIL_L, RAIL_R = 111, 81     # width of the rails, px (left one carries the soundtrack)
PITCH, HOLE_W, HOLE_H = 66, 40, 36
STEP = 24                    # the film moves this many px every second frame
TRACK_X, TRACK_W = 70, 32    # the soundtrack strip inside the left rail
SNAP = (.16, .60, .84, .96, 1)                              # the rails sliding in, frame by frame
ROLL = (.04, .19, .43, .68, .89, .99, 1)                    # the picture rolling one frame down, frame by frame
ROLL_AT = 6                  # frames after the start
BAR = 30                     # the black frame line between two film frames, px


def when(s, what, label):
    if isinstance(what, (int, float)):
        return float(what)
    w = s.find('^' + V.re.escape(what) + '$')
    if not w:
        V.die(f'the word "{what}" ({label}) is not in this slot: pick a word from the list above')
    return w['start']


def soundtrack(dur, speed, y0):
    """the strip as a tall picture: the newest sound at the top. Returns the time at the top of the picture."""
    raw = subprocess.run([G.FF, '-v', 'error', '-i', 'assets/aroll.mp4', '-vn', '-ac', '1', '-ar', '8000', '-f', 'f32le', '-'],
                         capture_output=True).stdout
    a = np.abs(np.frombuffer(raw, np.float32))
    if not a.size:
        V.die('this slot has no sound, and the soundtrack strip is drawn from the voice')
    t_top = dur + y0 / speed
    h = int((t_top + (1920 - y0) / speed) * speed) + 4
    rows = np.zeros(h)
    for y in range(h):
        t = (t_top - y / speed) % dur          # past the slot's own sound the voice starts over, so the strip is never empty
        i, j = int(t * 8000), int((t + 1 / speed) * 8000)
        if j > i and i < a.size:
            rows[y] = a[i:j].max()
    rows = np.convolve(rows, np.ones(5) / 5, 'same')
    peak = max(np.percentile(rows, 90), 1e-4)
    width = 3 + np.clip(rows / peak, 0, 1) ** .55 * (TRACK_W - 3)
    im = np.zeros((h, TRACK_W, 4), np.uint8)
    col = tuple(int(STYLE['track'][k:k + 2], 16) for k in (1, 3, 5))
    for y in range(h):
        half = width[y] / 2
        x0, x1 = TRACK_W / 2 - half, TRACK_W / 2 + half
        im[y, :, :3] = col
        im[y, :, 3] = (np.clip(np.minimum(np.arange(TRACK_W) + 1 - x0, x1 - np.arange(TRACK_W)), 0, 1) * 255).astype(np.uint8)
    Image.fromarray(im).save('assets/soundtrack.png')
    return t_top


def main():
    s = V.Slot()
    s.dur = int(s.frames / V.FPS * 1e4) / 1e4   # cut, not rounded: a duration rounded up renders one frame too many
    print('words: ' + s.word_list())
    print(s.where())
    w0 = next((w for w in s.words if w['start'] >= .3), None)
    if ON is None and not w0:
        V.die('no word starts after 0.3 s in this slot: start the slot earlier')
    t_on = w0['start'] if ON is None else when(s, ON, 'ON')
    f0 = max(2, round(t_on * V.FPS))
    n = s.frames
    fb = None if BACK is None else (n - 6 if BACK == 'auto' else round(when(s, BACK, 'BACK') * V.FPS))
    if (fb or n) < f0 + ROLL_AT + len(ROLL) + 10:
        V.die(f'starts at frame {f0} and ends at frame {fb or n}: it needs {ROLL_AT + len(ROLL) + 10} frames to snap in, roll and run. Start earlier or end later')
    head = (s.layout or {}).get('head') or {}
    hl, hr = int(head.get('left') or s.cx - 180), int(head.get('right') or s.cx + 180)
    if hl < RAIL_L + 6 or hr > 1080 - RAIL_R - 6:
        V.die(f'the head (x {hl} to {hr}) reaches under the film rails on this clip: it needs a more centred shot')

    gain = G.input_gain(LOOK, G.clip_level('assets/aroll.mp4'))
    G.bake('assets/aroll.mp4', 'assets/graded.mp4', LOOK, gain, grain=GRAIN)
    import shutil
    shutil.copy2('assets/graded.mp4', 'assets/graded_b.mp4')   # two videos on one file get merged by the renderer
    speed = STEP / 2 * V.FPS   # px per second
    y0 = 960
    t_top = soundtrack(s.dur, speed, y0)
    tr_h = Image.open('assets/soundtrack.png').size[1]

    rnd = random.Random(4217)
    p = V.Page(s)
    hole_x_l, hole_x_r = 18, 1080 - RAIL_R + 24 - (1080 - RAIL_R)      # holes inside each rail
    p.css.append(f'''
#film{{position:absolute;inset:0;overflow:hidden;background:#040504}}
#pic{{position:absolute;inset:0}}
.pv{{position:absolute;left:0;width:1080px;height:1920px}}
.pv video{{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover}}
#flick{{position:absolute;inset:0;background:#000}}
.rail{{position:absolute;top:0;height:1920px;overflow:hidden;background:{STYLE['rail']}}}
#railL{{left:0;width:{RAIL_L}px}}
#railR{{right:0;width:{RAIL_R}px}}
.holes{{position:absolute;left:0;top:-{PITCH}px;width:100%;height:{1920 + 2 * PITCH}px}}
#strack{{position:absolute;left:{TRACK_X}px;top:0;width:{TRACK_W}px;height:{tr_h}px}}
.print{{position:absolute;font-family:'{STYLE["small_font"]}';font-weight:{STYLE["small_weight"]};font-size:13px;letter-spacing:.14em;color:{STYLE["edge_print"]};
  writing-mode:vertical-rl;white-space:nowrap;line-height:1}}
.dust{{position:absolute;border-radius:50%}}
#scr{{position:absolute;top:0;width:2px;background:#fff}}''')

    def holes(hid, x):
        rects = ''.join(f'<rect x="{x}" y="{k * PITCH + (PITCH - HOLE_H) / 2:.0f}" width="{HOLE_W}" height="{HOLE_H}" rx="7" fill="{STYLE["hole"]}"/>'
                        for k in range(32))
        return f'<svg id="{hid}" class="holes" viewBox="0 0 120 {32 * PITCH}" preserveAspectRatio="xMinYMin slice" style="height:{32 * PITCH}px;width:120px">{rects}</svg>'

    prints = ''
    if EDGE_PRINT:
        prints = ''.join(f'<div class="print pr" style="right:3px;top:{k * 340 - 340}px">{V.esc(EDGE_PRINT)}</div>' for k in range(8))
    marks = ''.join(f'<div class="dust pr" style="left:3px;top:{k * 88 - 340 + 40}px;width:4px;height:4px;background:{STYLE["edge_print"]}"></div>' for k in range(30))
    vid = lambda i, f: (f'<video id="{i}" src="assets/{f}" muted playsinline data-start="0" data-media-start="0" '
                        f'data-duration="{s.dur:.4f}" data-track-index="{1 if f == "graded.mp4" else 3}"></video>')
    # dust and one faint scratch: never on the head
    dust_html, dust_js = [], []
    if DUST:
        for f in range(f0 + 6, (fb or n), 2):
            for _ in range(rnd.choice((0, 1, 1, 2, 3))):
                while True:
                    x, y = rnd.randint(RAIL_L + 8, 1080 - RAIL_R - 8), rnd.randint(30, 1890)
                    if not (hl - 20 < x < hr + 20 and s.head_top - 30 < y < s.chin + 20):
                        break
                sz = rnd.choice((2, 3, 3, 4, 6))
                i = f'd{len(dust_html)}'
                tone = rnd.choice(('#F4F0E6', '#F4F0E6', '#0A0A0A'))
                dust_html.append(f'<div id="{i}" class="dust" style="left:{x}px;top:{y}px;width:{sz}px;height:{int(sz * rnd.uniform(1, 2.4))}px;background:{tone};opacity:{rnd.uniform(.5, .9):.2f}"></div>')
                dust_js.append(f"gsap.set('#{i}',{{autoAlpha:0}});tl.set('#{i}',{{autoAlpha:1}},{V.T(f / V.FPS):.3f});tl.set('#{i}',{{autoAlpha:0}},{V.T((f + 2) / V.FPS):.3f});")
    scr_x = 1080 - RAIL_R - 70 if hr < 1080 - RAIL_R - 100 else RAIL_L + 60
    p.html.append(f'''<div id="film">
  <div id="pic"><div id="pa" class="pv">{vid('gv', 'graded.mp4')}</div><div id="pb" class="pv" style="top:-{1920 + BAR}px">{vid('gvb', 'graded_b.mp4')}</div></div>
  <div id="flick"></div>{''.join(dust_html)}
  <div id="scr" style="left:{scr_x}px;height:760px"></div>
  <div id="railL" class="rail"><div id="tl">{holes('hl', hole_x_l)}{marks}</div><img id="strack" src="assets/soundtrack.png" /></div>
  <div id="railR" class="rail"><div id="tr">{holes('hr', 24)}{prints}</div></div>
</div>''')
    t = lambda f: V.T(f / V.FPS)
    p.js.append("gsap.set('#film',{autoAlpha:0});gsap.set('#flick',{opacity:0});gsap.set('#scr',{autoAlpha:0});")
    p.js.append(f"gsap.set('#railL',{{x:-{RAIL_L}}});gsap.set('#railR',{{x:{RAIL_R}}});")
    p.js.extend(dust_js)
    p.js.append(f"tl.set('#film',{{autoAlpha:1}},{t(f0):.3f});")
    if fb is not None:
        p.js.append(f"tl.set('#film',{{autoAlpha:0}},{t(fb):.3f});")
    for k, u in enumerate(SNAP):
        p.js.append(f"tl.set('#railL',{{x:{-(1 - u) * RAIL_L:.1f}}},{t(f0 + 1 + k):.3f});tl.set('#railR',{{x:{(1 - u) * RAIL_R:.1f}}},{t(f0 + 1 + k):.3f});")
    roll_end = f0 + ROLL_AT + len(ROLL)
    for k, u in enumerate(ROLL):
        y = u * (1920 + BAR)
        p.js.append(f"tl.set('#pic',{{y:{y:.1f}}},{t(f0 + ROLL_AT + k):.3f});")
    wv = random.Random(909)
    end = fb or n
    for f in range(f0, end):
        ft = t(f)
        if (f - f0) % 2 == 0:
            step = (f - f0) / 2 * STEP
            off = step % PITCH
            p.js.append(f"tl.set('#hl,#hr',{{y:{off:.1f}}},{ft:.3f});")
            p.js.append(f"tl.set('.pr',{{y:{step:.1f}}},{ft:.3f});")
            tt = (f - f % 2) / V.FPS
            p.js.append(f"tl.set('#strack',{{y:{y0 + (tt - t_top) * speed:.1f}}},{ft:.3f});")
            if DUST and f >= roll_end:
                p.js.append(f"tl.set('#flick',{{opacity:{wv.uniform(0, .075) * DUST:.3f}}},{ft:.3f});")
                p.js.append(f"tl.set('#pic',{{y:{1920 + BAR + wv.choice((-5, -3, -2, 0, 0, 0, 2, 4)):.1f}}},{ft:.3f});")
                on = wv.random() < .55
                p.js.append(f"tl.set('#scr',{{autoAlpha:{(.22 if on else 0)},x:{wv.randint(-4, 4)},y:{wv.randint(0, 1160)}}},{ft:.3f});")
    if RATTLE:
        f = f0 + 17
        snd = random.Random(31)
        while f < end - 2:
            p.sound('click-soft', f / V.FPS, snd.uniform(.05, .11) * RATTLE)
            f += snd.choice((1, 2, 2, 3, 4))
    p.write()
    print(f'  film from {f0 / V.FPS:.2f}s, rails in by {(f0 + 6) / V.FPS:.2f}s, rolls to {roll_end / V.FPS:.2f}s, ' + (f'cuts back at {fb / V.FPS:.2f}s' if fb else 'runs to the end'))
    print(f'snapshot at: {(f0 + 2) / V.FPS:.2f},{(f0 + 7) / V.FPS:.2f},{(f0 + 9) / V.FPS:.2f},{(f0 + 11) / V.FPS:.2f},{(f0 + 20) / V.FPS:.2f},{(f0 + 22) / V.FPS:.2f}')


if __name__ == '__main__':
    main()
