#!/usr/bin/env python3
"""COLOR PICKER (mood): a small cream palette card slides in at the side, an eyedropper cursor taps five real colours
measured off this clip, each one flying into the card with its hex code typing in. Then the shot steps down three times,
darker and more drained each time, and the swatches and codes step with it: they show what the grade does to those colours.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html   (SAFE=1 safe-zone guide, SFX=0 no sounds)
"""
import itertools
import os
import subprocess

os.environ.setdefault('PREVIEW', '1')    # a full picture effect: the footage is always in the page
import numpy as np

import grade as G
import vgfx as V

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    small_font='JetBrains Mono',   # hex codes, title and labels
    small_weight=500,
    paper='#F3EEE3',               # the card, cream paper
    ink='#1C2A23',                 # text on the card, near-black forest
    faint='#8C877B',               # title and labels
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
ON = None           # the word the grade takes its first step on (a word from words.json) or seconds.
                    # None = the first word at least 0.7 s into the slot
TITLE = 'UZORCI'    # the card's title
LABELS = dict(dark='TAMNA', light='SVETLA', neutral='SIVA', red='CRVENA', orange='NARANDŽASTA', yellow='ŽUTA', green='ZELENA',
              blue='PLAVA', purple='LJUBIČASTA')   # the name under each swatch, in the reel's language
OUT = 'auto'        # 'auto' = card and grade leave in the last 0.4 s. None = they stay to the end (the slot ends on a cut)
SFX_GAIN = 1.0
# ==== END CLIP ====

W, H = 216, 429         # the card, px
SW, PITCH, SW_TOP = 54, 75, 52   # the swatches
PICKS = (2, 5, 8, 11, 14)        # frames after the card starts: a tap every 3 frames
STAGES = (18, 26, 31)            # frames after the card starts: the three steps of the grade
LOOKS = ('drain1', 'drain2', 'drain3')
SLIDE = (.0, .70, .97, 1)        # the card sliding in, frame by frame
FLY = 5                          # frames a swatch takes to reach the card
BLOCK = 30


def grab(path, frame, alpha=False, extra=()):
    fmt = 'rgba' if alpha else 'rgb24'
    raw = subprocess.run([G.FF, '-v', 'error', *extra, '-i', path, '-vf', f"select='eq(n\\,{frame})',scale=1080:1920", '-frames:v', '1',
                          '-f', 'rawvideo', '-pix_fmt', fmt, '-'], capture_output=True).stdout
    c = 4 if alpha else 3
    if len(raw) < 1080 * 1920 * c:
        V.die(f'could not read frame {frame} of {path}')
    return np.frombuffer(raw, np.uint8).reshape(1920, 1080, c).astype(float)


def colour_name(c):
    """which entry of LABELS a measured colour (0-255) belongs to"""
    r, g, b = c / 255
    hi, lo = max(r, g, b), min(r, g, b)
    if hi < .16:
        return 'dark'
    if hi - lo < .12 or (hi - lo) / hi < .18:
        return 'light' if hi > .75 else 'neutral'
    h = ((g - b) / (hi - lo) % 6 if hi == r else (b - r) / (hi - lo) + 2 if hi == g else (r - g) / (hi - lo) + 4) * 60
    return ('red' if h < 15 or h >= 335 else 'orange' if h < 42 else 'yellow' if h < 70 else 'green' if h < 170
            else 'blue' if h < 255 else 'purple')


def crosses(a, b, box):
    """does the straight line a to b touch the box (x0, y0, x1, y1)?"""
    for u in np.linspace(0, 1, 40):
        x, y = a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
        if box[0] < x < box[2] and box[1] < y < box[3]:
            return True
    return False


def measure(frame, head_box, card_box, slot_xy):
    """five sample places, off the face and off the card, whose flight to the card clears the face.
    -> [(kind, x, y)] in tap order, with the cursor's path clear of the face wherever that is possible"""
    if not os.path.exists('assets/subject.webm'):
        V.die('assets/subject.webm is missing: this effect reads the speaker\'s cutout to tell clothes from the wall. Make the slot again with the cutout')
    rgb = grab('assets/aroll.mp4', frame)
    rgb0, rgb1 = grab('assets/aroll.mp4', max(0, frame - 6)), grab('assets/aroll.mp4', frame + 6)
    alpha = grab('assets/subject.webm', frame, alpha=True, extra=('-c:v', 'libvpx-vp9'))[..., 3] / 255
    cells = []
    for y in range(V.SAFE_TOP + 20, V.SAFE_BOTTOM - BLOCK, BLOCK):
        for x in range(V.SAFE_SIDE + 10, 1080 - V.SAFE_SIDE - 40, BLOCK):
            cx, cy = x + BLOCK / 2, y + BLOCK / 2
            if head_box[0] < cx < head_box[2] and cy < head_box[3] + 180:    # the face, above it, and far enough below it for the cursor's body
                continue
            if card_box[0] - 30 < cx < card_box[2] + 30 and card_box[1] - 30 < cy < card_box[3] + 30:
                continue
            if crosses((cx, cy), slot_xy, head_box):
                continue
            b = rgb[y:y + BLOCK, x:x + BLOCK].reshape(-1, 3)
            a = alpha[y:y + BLOCK, x:x + BLOCK]
            if b.std(0).mean() > 16 or (.05 < a.mean() < .95):
                continue
            m = b.mean(0)
            if max(np.abs(r[y:y + BLOCK, x:x + BLOCK].reshape(-1, 3).mean(0) - m).max() for r in (rgb0, rgb1)) > 12:
                continue                     # a hand passing through: the code would not match what is there at the tap
            cells.append(dict(x=cx, y=cy, c=m, luma=float(m @ (.2126, .7152, .0722)), sat=float(m.max() - m.min()), sub=a.mean() >= .95))
    bg, sub = [c for c in cells if not c['sub']], [c for c in cells if c['sub']]
    if len(bg) < 3 or len(cells) < 12:
        V.die('there is not enough calm picture off the face on this clip to sample five colours')

    # five colours as far apart as the picture offers, starting from the clothes (or the wall on a clip with no clothes in reach)
    pool = sub or bg
    first = min(pool, key=lambda c: float(np.abs(c['c'] - np.median([o['c'] for o in pool], 0)).sum()))
    chosen = [first]
    while len(chosen) < 5:
        chosen.append(max(cells, key=lambda c: min(float(np.abs(c['c'] - o['c']).sum()) for o in chosen)
                          if all(abs(c['x'] - o['x']) + abs(c['y'] - o['y']) > 120 for o in chosen) else -1))
    kinds = [colour_name(c['c']) for c in chosen]
    pts = [(k, c['x'], c['y']) for k, c in zip(kinds, chosen)]
    start = (slot_xy[0] + 500, slot_xy[1] + 500)
    best = min(itertools.permutations(pts), key=lambda order: sum(crosses(a[1:], b[1:], head_box) for a, b in zip(order, order[1:])) * 10000
               + sum(abs(a[1] - b[1]) + abs(a[2] - b[2]) for a, b in zip(order, order[1:])))
    n_cross = sum(crosses(a[1:], b[1:], head_box) for a, b in zip(best, best[1:]))
    if n_cross:
        print(f'  note: the cursor has to pass the face {n_cross} time(s) on its way between samples: check the snapshots')
    return list(best), start


def main():
    s = V.Slot()
    s.dur = int(s.frames / V.FPS * 1e4) / 1e4   # cut, not rounded: a duration rounded up renders one frame too many
    print('words: ' + s.word_list())
    print(s.where())
    if ON is None:
        w = next((w for w in s.words if w['start'] >= .7), None)
        if not w:
            V.die('no word starts 0.7 s or later in this slot: end the slot later')
        t_on = w['start']
    elif isinstance(ON, (int, float)):
        t_on = float(ON)
    else:
        w = s.find('^' + V.re.escape(ON) + '$')
        if not w:
            V.die(f'the word "{ON}" is not in this slot: pick a word from the list above')
        t_on = w['start']
    f_on = round(t_on * V.FPS)
    f0 = f_on - STAGES[0]
    n = s.frames
    if f0 < 1:
        V.die(f'the grade word is {f_on} frames into the slot and the picks need {STAGES[0] + 1} frames before it: start the slot earlier or pick a later word')
    if f0 + STAGES[2] + 12 > n:
        V.die('the slot ends before the last step of the grade has been seen: end it later')
    head = (s.layout or {}).get('head') or {}
    hl, hr = int(head.get('side_left') or s.cx - 200), int(head.get('side_right') or s.cx + 200)
    head_box = (hl - 40, s.head_top - 50, hr + 40, s.chin + 30)
    if hl - 40 >= V.SAFE_SIDE + W:
        card_x = max(39, V.SAFE_SIDE + 4)
    elif hr + 40 + W <= 1080 - V.SAFE_SIDE:
        card_x = 1080 - V.SAFE_SIDE - W - 4
    else:
        V.die('there is no room beside the face for the palette card on this clip')
    side = -1 if card_x < 540 else 1
    card_y = 561
    card_box = (card_x, card_y, card_x + W, card_y + H)
    slot_mid = (card_x + 15 + SW / 2, card_y + SW_TOP + SW / 2 + 2 * PITCH)
    picks, start = measure(f0 + PICKS[2], head_box, card_box, slot_mid)

    # the colours are read at the very frame each one is tapped
    rows = []
    for i, (kind, x, y) in enumerate(picks):
        rgb = grab('assets/aroll.mp4', f0 + PICKS[i])
        b = rgb[int(y) - 10:int(y) + 10, int(x) - 10:int(x) + 10].reshape(-1, 3).mean(0) / 255
        steps = [b] + [G.apply(b, lk) for lk in LOOKS]
        rows.append(dict(kind=kind, x=x, y=y, steps=steps, hexes=[G.hex_of(c) for c in steps]))
        print(f'  sample {i + 1}: {LABELS.get(kind, kind)} at ({x:.0f},{y:.0f})  ' + ' > '.join(r for r in rows[-1]['hexes']))
    for lk, name in zip(LOOKS, ('assets/grade1.mp4', 'assets/grade2.mp4', 'assets/grade3.mp4')):
        G.bake('assets/aroll.mp4', name, lk)

    t = lambda f: V.T(f / V.FPS)
    p = V.Page(s)
    paper, ink, faint = STYLE['paper'], STYLE['ink'], STYLE['faint']
    p.css.append(f'''
#grades{{position:absolute;inset:0}}
#grades video{{position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover}}
#card{{position:absolute;left:{card_x}px;top:{card_y}px;width:{W}px;height:{H}px;border-radius:21px;background:{paper};box-shadow:0 8px 28px rgba(0,0,0,.3);
  font-family:'{STYLE["small_font"]}';font-weight:{STYLE["small_weight"]};color:{ink}}}
#card .ttl{{position:absolute;left:18px;top:15px;font-size:15px;letter-spacing:.16em;color:{faint};line-height:1}}
#card .dot{{position:absolute;top:18px;width:15px;height:7px;border-radius:3px;border:1.5px solid {faint}}}
#card .well{{position:absolute;left:15px;width:{SW}px;height:{SW}px;border-radius:13px;border:1.5px solid rgba(0,0,0,.05)}}
#card .hx{{position:absolute;left:{15 + SW + 12}px;font-size:24px;line-height:1;height:26px;overflow:hidden;white-space:nowrap;letter-spacing:.01em}}
#card .hx span{{position:absolute;left:0;top:0}}
#card .lb{{position:absolute;left:{15 + SW + 12}px;font-size:15px;line-height:1;letter-spacing:.12em;color:{faint}}}
.sw{{position:absolute;width:{SW}px;height:{SW}px;border-radius:13px;box-shadow:0 1px 3px rgba(0,0,0,.18)}}
#ring{{position:absolute;left:-30px;top:-30px;width:60px;height:60px;border-radius:50%;border:3px solid #fff}}
#drop{{position:absolute;left:0;top:0;width:78px;height:78px;transform-origin:0 100%}}''')
    vid = lambda k: (f'<video id="g{k}" src="assets/grade{k}.mp4" muted playsinline data-start="0" data-media-start="0" '
                     f'data-duration="{s.dur:.4f}" data-track-index="{2 + k}"></video>')
    p.html.append(f'<div id="grades">{vid(1)}{vid(2)}{vid(3)}</div>')
    card = [f'<div class="ttl">{V.esc(TITLE)}</div>']
    for i in range(3):
        card.append(f'<div id="dot{i}" class="dot" style="left:{W - 66 + i * 18}px"></div>')
    fly = []
    for i, r in enumerate(rows):
        y = SW_TOP + i * PITCH
        hexes = ''.join(f'<span id="h{i}s{k}">{h}</span>' for k, h in enumerate(r['hexes']))
        card.append(f'<div class="well" style="top:{y}px"></div><div id="hx{i}" class="hx" style="top:{y + 5}px;width:0">{hexes}</div>'
                    f'<div id="lb{i}" class="lb" style="top:{y + 36}px">{V.esc(LABELS.get(r["kind"], r["kind"]))}</div>')
        fly.append(f'<div id="sw{i}" class="sw" style="left:{card_x + 15}px;top:{card_y + y}px;background:{r["hexes"][0]}"></div>')
    p.html.append('<div id="card">' + ''.join(card) + '</div>')
    p.html.append(''.join(fly))
    # a plain eyedropper, tip at the bottom left of its box
    p.html.append('<div id="ring"></div><svg id="drop" viewBox="0 0 78 78"><g fill="none" stroke-linecap="round" stroke-linejoin="round">'
                  '<path d="M6 72 L10 58 L42 26 L52 36 L20 68 Z M38 20 L58 40 M48 22 L58 12 Q64 8 69 13 Q74 18 68 24 L58 34 Z" fill="#fff" stroke="#fff" stroke-width="8"/>'
                  '<path d="M6 72 L10 58 L42 26 L52 36 L20 68 Z" fill="#fff" stroke="#111" stroke-width="3.5"/>'
                  '<path d="M38 20 L58 40" stroke="#111" stroke-width="9"/>'
                  '<path d="M48 22 L58 12 Q64 8 69 13 Q74 18 68 24 L58 34 Z" fill="#111" stroke="#111" stroke-width="2"/></g></svg>')

    js = p.js
    js.append(f"gsap.set('#grades video,#ring',{{autoAlpha:0}});gsap.set('#card',{{x:{side * (W + 80)}}});gsap.set('.sw',{{autoAlpha:0}});"
              "gsap.set('.lb',{autoAlpha:0});gsap.set('.hx span',{autoAlpha:0});")
    for k, u in enumerate(SLIDE):
        js.append(f"tl.set('#card',{{x:{side * (W + 80) * (1 - u):.1f}}},{t(f0 + k):.3f});")
    # the cursor: comes in from the far side, three frames between taps, leaves after the last one
    path = [(start[0], start[1], f0)]
    for i, r in enumerate(rows):
        path.append((r['x'], r['y'], f0 + PICKS[i]))
    leave = f0 + PICKS[4] + 8
    path.append((1180 if rows[4]['x'] > s.cx else -100, rows[4]['y'] - 120, leave))    # out on its own side, never over the face
    js.append(f"gsap.set('#drop',{{autoAlpha:0,x:{start[0]:.0f},y:{start[1] - 78:.0f}}});tl.set('#drop',{{autoAlpha:1}},{t(f0):.3f});tl.set('#drop',{{autoAlpha:0}},{t(leave):.3f});")
    for (x0, y0, a), (x1, y1, b) in zip(path, path[1:]):
        for f in range(a + 1, b + 1):
            u = (f - a) / (b - a)
            e = 1 - (1 - u) ** 3
            js.append(f"tl.set('#drop',{{x:{x0 + (x1 - x0) * e:.1f},y:{y0 + (y1 - y0) * e - 78:.1f}}},{t(f):.3f});")
    for i, r in enumerate(rows):
        fp = f0 + PICKS[i]
        # the tap: a ring opens at the tip
        js.append(f"tl.set('#ring',{{autoAlpha:1,x:{r['x']:.0f},y:{r['y']:.0f},scale:.5,opacity:1}},{t(fp):.3f});"
                  f"tl.to('#ring',{{scale:1.15,opacity:0,duration:.09,ease:'power2.out'}},{t(fp):.3f});")
        # the swatch flies from the tip to its place
        sx = card_x + 15 + SW / 2
        sy = card_y + SW_TOP + i * PITCH + SW / 2
        dx, dy = r['x'] - sx, r['y'] - sy
        js.append(f"tl.set('#sw{i}',{{autoAlpha:1,x:{dx:.1f},y:{dy:.1f},scale:.62}},{t(fp):.3f});")
        for k in range(1, FLY + 1):
            u = k / FLY
            e = 3 * u * u - 2 * u * u * u
            js.append(f"tl.set('#sw{i}',{{x:{dx * (1 - e):.1f},y:{dy * (1 - e):.1f},scale:{.62 + .38 * e:.3f}}},{t(fp + k):.3f});")
        land = fp + FLY
        # the hex types itself in, then the label
        js.append(f"tl.set('#h{i}s0',{{autoAlpha:1}},{t(land - 1):.3f});")
        for k, chars in enumerate((2, 4, 6, 7)):
            js.append(f"tl.set('#hx{i}',{{width:{chars * 14.6 + 2:.1f}}},{t(land - 1 + k):.3f});")
        js.append(f"tl.to('#lb{i}',{{autoAlpha:1,duration:.067,ease:'none'}},{t(land + 3):.3f});")
        p.sound('click-soft', fp / V.FPS, .42 * SFX_GAIN)
    # the steps of the grade: picture, swatches and codes change on the same frame
    for k, st in enumerate(STAGES):
        f = f0 + st
        js.append(f"tl.set('#g{k + 1}',{{autoAlpha:1}},{t(f):.3f});" + (f"tl.set('#g{k}',{{autoAlpha:0}},{t(f + 1):.3f});" if k else ''))
        js.append(f"tl.set('#dot{k}',{{backgroundColor:'{ink}',borderColor:'{ink}'}},{t(f):.3f});")
        for i, r in enumerate(rows):
            js.append(f"tl.set('#sw{i}',{{backgroundColor:'{r['hexes'][k + 1]}'}},{t(f):.3f});"
                      f"tl.set('#h{i}s{k}',{{autoAlpha:0}},{t(f):.3f});tl.set('#h{i}s{k + 1}',{{autoAlpha:1}},{t(f):.3f});")
    p.sound('whoosh-short', (f0 + STAGES[0]) / V.FPS, .24 * SFX_GAIN)
    if OUT == 'auto':
        fo = n - 12
        js.append(f"tl.to('#grades',{{autoAlpha:0,duration:.33,ease:'power1.inOut'}},{t(fo):.3f});")
        js.append(f"tl.to('#card,.sw',{{x:'+={side * (W + 80)}',duration:.23,ease:'power2.in'}},{t(fo):.3f});")
    p.write()
    print(f'  card in at {f0 / V.FPS:.2f}s, taps {", ".join(f"{(f0 + x) / V.FPS:.2f}" for x in PICKS)}, grade steps {", ".join(f"{(f0 + x) / V.FPS:.2f}" for x in STAGES)}, card on the {"left" if side < 0 else "right"}')
    print(f'snapshot at: {(f0 + 3) / V.FPS:.2f},{(f0 + 9) / V.FPS:.2f},{(f0 + 15) / V.FPS:.2f},{(f0 + 22) / V.FPS:.2f},{(f0 + 34) / V.FPS:.2f},{max(0, s.dur - .05):.2f}')


if __name__ == '__main__':
    main()
