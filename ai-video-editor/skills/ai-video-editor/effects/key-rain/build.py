#!/usr/bin/env python3
"""KEY RAIN (explain): keyboard keycaps with shortcut glyphs rain down, land with weight on the speaker's head and on an
invisible shelf level with it, and stack up row on row with real physics. The pile rides the head as it moves. On the
sweep word a gold ruler bar crosses the frame and shoves the whole pile tumbling out of the side.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html   (SAFE=1 safe-zone guide, SFX=0 no sounds, CAPTIONS=0 accepted:
                                               the keys ARE the effect, so they always draw)
"""
import os
import random
import shutil
import subprocess

import numpy as np

import pile_sim
import vgfx as V

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    font='Inter Tight',            # the big letter on a key
    weight=700,
    label_font='JetBrains Mono',   # the tiny word under it
    label_weight=500,
    key='#F3EFE2',                 # light key: top face
    key_lip='#BDB6A4',             # light key: lower edge
    key_ink='#14241C',
    key_dim='#7B776B',
    dark='#1F4033',                # dark key (deep forest green)
    dark_lip='#122A20',
    dark_ink='#F3EFE2',
    dark_dim='#A8BDAE',
    ruler='#C9A95C',               # the sweeping bar
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
# Rows of keys, bottom row first: (what the key shows, tiny word under it, width in key units, dark key?).
# In what the key shows, the characters of the modifier keys draw as shapes, so they look the same on any machine:
# ⌘ ⌥ ⇧ ⌫. Everything else is plain text. None = this default set in English.
KEYS = None
T_RAIN = None       # when the first key leaves the top (a word, seconds). None = 0.1 s into the slot
RAIN_DUR = 1.15     # seconds from the first key to the last
T_SWEEP = None      # when the bar crosses (a word, seconds). Required
SWEEP_DIR = 'right' # 'right' or 'left'
KEY_H = None        # key height, px. None = the rows fit the room above the head (at most 120 px)
FLOOR_Y = None      # y the bottom row rests on, px. None = measured: a little below the top of the head
SOUND = .3          # volume of the landings and the sweep. 0 = silent
# ==== END CLIP ====

DEFAULT_KEYS = [
    [('⌘C', 'copy', 1.5, False), ('X', 'cut', 1, False), ('V', 'paste', 1, False), ('A', 'all', 1, False), ('⌥', 'option', 1, True), ('Z', 'back', 1, False), ('⌘S', 'save', 1.5, False)],
    [('F', 'find', 1, False), ('space', 'play', 2.2, False), ('⌘Z', 'undo', 1.5, False), ('⇧', 'shift', 1, True)],
    [('⌘', 'command', 1, True), ('⌘B', 'bold', 1.5, False), ('R', 'redo', 1, False), ('⇧⌘D', 'copy', 1.7, False), ('Q', 'quit', 1, False)],
    [('=', 'zoom', 1, False), ('⇧⌘Z', 'again', 1.7, False), ('⇧⌫', 'delete', 1.7, True)],
]
GLYPHS = {  # drawn shapes for the modifier keys, on a 24 x 24 box
    '⌘': 'M9 9h6v6H9zM9 9V6.5A2.5 2.5 0 1 0 6.5 9H9zM15 9h2.5A2.5 2.5 0 1 0 15 6.5V9zM9 15H6.5A2.5 2.5 0 1 0 9 17.5V15zM15 15v2.5a2.5 2.5 0 1 0 2.5-2.5H15z',
    '⌥': 'M3 6h6l6 12h6M14 6h7',
    '⇧': 'M12 4 3.5 13H8v7h8v-7h4.5z',
    '⌫': 'M8 5h13v14H8l-6-7zM11.5 9.5l5 5M16.5 9.5l-5 5',
}
PITCH_GAP = .08


def when(s, spec, default=None):
    if spec is None:
        return default
    if isinstance(spec, (int, float)):
        return float(spec)
    hit = s.find('^' + V.re.escape(V.bare(str(spec))) + '$')
    return hit['start'] if hit else None


def head_tops(s):
    """top of the head per frame, measured on the cutout in a band around the head's x. None with no cutout."""
    if not os.path.isfile('assets/subject.webm'):
        return None
    ff = shutil.which('ffmpeg') or 'ffmpeg'
    q = 4
    w, h = 1080 // q, 1920 // q
    raw = subprocess.run([ff, '-v', 'error', '-c:v', 'libvpx-vp9', '-i', 'assets/subject.webm', '-vf', f'alphaextract,scale={w}:{h}:flags=area',
                          '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True).stdout
    if not raw:
        return None
    a = np.frombuffer(raw, np.uint8).reshape(-1, h, w) > 128
    x0, x1 = max(0, (s.cx - 110) // q), min(w, (s.cx + 110) // q)
    tops = np.array([int(np.argmax(m[:, x0:x1].any(axis=1))) * q if m[:, x0:x1].any() else -1 for m in a], float)
    if (tops < 0).mean() > .3:
        return None
    med = np.median(tops[tops >= 0])
    tops = np.where((tops < 0) | (tops < med - 70), med, tops)      # a hand raised over the head does not count
    # a slow follow: the pile has weight, it does not twitch with every nod
    kernel = np.ones(9) / 9
    smooth = np.convolve(np.pad(tops, 4, mode='edge'), kernel, 'valid')
    return smooth


def glyph_html(text, font_px):
    out = []
    for ch in text:
        d = GLYPHS.get(ch)
        if d:
            size = font_px * .94
            out.append(f'<svg viewBox="0 0 24 24" style="width:{size:.1f}px;height:{size:.1f}px;margin:0 {font_px * .03:.1f}px;overflow:visible"><path d="{d}" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"/></svg>')
        else:
            out.append(V.esc(ch))
    return ''.join(out)


def main():
    s = V.Slot()
    s.dur = int(s.frames / V.FPS * 1e4) / 1e4      # rounded down: a page rounded up to the next 1/10000 s renders one frame too many
    print('words: ' + s.word_list())
    print(s.where())
    rows = KEYS or DEFAULT_KEYS
    t_rain = when(s, T_RAIN, .1)
    t_sweep = when(s, T_SWEEP)
    if t_sweep is None:
        V.die('set T_SWEEP in the CLIP block: the word (or the seconds) the bar crosses on')
    if t_rain is None:
        V.die(f'the word "{T_RAIN}" is not in the words of this slot')
    if t_sweep - t_rain < RAIN_DUR + .5:
        V.die(f'the keys need {RAIN_DUR + .5:.1f} s from the first key to the sweep: move T_RAIN earlier or T_SWEEP later')

    tops = head_tops(s)
    if tops is None:
        print('placement: no cutout in this slot, so the head top comes from layout.json and the pile does not ride the head')
        top_min = s.head_top
    else:
        top_min = int(tops.min())
    floor_y = int(FLOOR_Y) if FLOOR_Y is not None else top_min + 16
    room = floor_y - V.SAFE_TOP - 4
    use = len(rows)
    key_h = KEY_H
    if key_h is None:
        while use > 2 and room / use < 66:
            use -= 1
        key_h = min(120, room / use)
    if key_h < 54:
        V.die(f'there is no room above the head on this clip for the keys ({room} px between the safe zone and the head)')
    rows = rows[:use]
    k = key_h / 120
    px = lambda v: round(v * k, 1)
    unit = px(126)
    print(f'  keys: {key_h:.0f} px tall, {use} rows, {sum(len(r) for r in rows)} keys, shelf at y {floor_y}, room {room} px')

    # ---- every key's place: rows spread across the safe width, dropped in row order so each row lands on the last
    left_x, right_x = V.SAFE_SIDE + 8.0, 1080 - V.SAFE_SIDE - 8.0
    span = right_x - left_x
    rnd = random.Random(23)
    keys = []
    for r, row in enumerate(rows):
        widths = [unit * max(1, w) for _, _, w, _ in row]
        spare = span - sum(widths) * 1.0
        if spare < 0:
            V.die(f'row {r + 1} of KEYS is wider than the frame: fewer keys or narrower ones')
        gap = min(spare / max(1, len(row) - 1), unit * .9) if len(row) > 1 else 0
        total = sum(widths) + gap * (len(row) - 1)
        x = left_x + (span - total) / 2 + (-1) ** r * min(unit * .25, (span - total) / 2)
        slots = []
        for w in widths:
            slots.append((x + w / 2, w))
            x += w + gap
        for (cx, w), (txt, sub, _, dark) in zip(slots, row):
            keys.append(dict(row=r, x=cx + rnd.uniform(-6, 6), w=w, txt=txt, sub=sub, dark=dark))
    # batches of two or three within a row, shuffled so it does not read as left to right
    order = []
    for r in range(use):
        ids = [i for i, q in enumerate(keys) if q['row'] == r]
        rnd.shuffle(ids)
        order += ids
    n = len(keys)
    bodies = [None] * n
    for pos, i in enumerate(order):
        q = keys[i]
        bodies[i] = dict(w=q['w'], h=key_h, x=q['x'], y=-key_h, ang=rnd.uniform(-5, 5), spin=rnd.uniform(-.5, .5),
                         vx=rnd.uniform(-10, 10), vy=1500.0, t_spawn=t_rain + RAIN_DUR * pos / max(1, n - 1), weight=1.0)
    # ---- the physics: the same small solver as Word Pile, with the shelf as its floor and the ruler as a moving wall
    sign = 1 if SWEEP_DIR == 'right' else -1
    t_end_bar = t_sweep + .36
    x_from, x_to = (-60.0, 1220.0) if sign > 0 else (1140.0, -140.0)
    bar_x = lambda t: x_from + (x_to - x_from) * min(1.0, max(0.0, (t - t_sweep) / (t_end_bar - t_sweep)))
    speed = abs(x_to - x_from) / (t_end_bar - t_sweep)
    cfg = dict(fps=V.FPS, sub=4, n=s.frames, floor_y=float(floor_y), wall_l=left_x - 6, wall_r=right_x + 6, wall_top=-400.0,
               t_sweep=None, mid_x=540.0, sweep_dir=sign)
    world = pile_sim.World(cfg, bodies)
    spun = random.Random(5)

    def push(w):
        t = w.t
        if t < t_sweep:
            # keycaps are squat and heavy: while they fall and settle they right themselves instead of tumbling
            for b in w.bodies:
                if b.spawned and not b.asleep:
                    b.om += (-b.ang * 90.0 - b.om * 16.0) * w.dt
            return
        w.walls_on = False
        bx = bar_x(t)
        for b in w.bodies:
            if not b.spawned:
                continue
            behind = (b.x - b.w / 2 < bx) if sign > 0 else (b.x + b.w / 2 > bx)
            if behind:
                b.asleep, b.sleep_t = False, 0.0
                b.x = bx + sign * b.w / 2
                if sign * b.vx < speed:
                    b.vx = sign * speed * spun.uniform(.98, 1.08)
                    b.vy = min(b.vy, 0.0) - spun.uniform(80, 900)
                    b.om += spun.uniform(-9, 9)

    world.run(s.frames, hook=push)
    ev = world.events()
    tr = world.track
    settled = [b for b in world.bodies if b.asleep or True]
    at_sweep = int((t_sweep - .02) * V.FPS) * 4
    tops_of = [tr[b.i, min(at_sweep, tr.shape[1] - 1), 1] - key_h / 2 for b in world.bodies]
    pile_top = float(np.nanmin(tops_of))
    print(f'  pile top at y {pile_top:.0f} before the sweep (safe zone starts at {V.SAFE_TOP})')
    if pile_top < V.SAFE_TOP - 8:
        print('  !! the pile reaches above the safe zone: lower KEY_H or take a row out of KEYS')

    # ---- the page
    S = STYLE
    p = V.Page(s)
    p.css.append(f'''
#krp{{position:absolute;left:0;top:0;width:1080px;height:1920px}}
.kr{{position:absolute;left:0;top:0;border-radius:{px(26)}px;display:flex;flex-direction:column;align-items:center;justify-content:center;transform-origin:50% 50%;will-change:transform}}
.kr .mn{{display:flex;align-items:center;justify-content:center;font-family:'{S["font"]}';font-weight:{S["weight"]};font-size:{px(52)}px;line-height:1;white-space:nowrap}}
.kr .sb{{font-family:'{S["label_font"]}';font-weight:{S["label_weight"]};font-size:{max(11.5, px(17))}px;line-height:1;letter-spacing:.08em;margin-top:{px(11)}px;white-space:nowrap}}
.kr.l{{background:linear-gradient(180deg,#FAF7EE,{S["key"]} 60%);color:{S["key_ink"]};box-shadow:inset 0 {-px(7)}px 0 {S["key_lip"]},inset 0 0 0 {px(2)}px rgba(255,255,255,.55),0 {px(8)}px {px(14)}px rgba(0,0,0,.34)}}
.kr.l .sb{{color:{S["key_dim"]}}}
.kr.d{{background:{S["dark"]};color:{S["dark_ink"]};box-shadow:inset 0 {-px(7)}px 0 {S["dark_lip"]},inset 0 0 0 {px(2)}px rgba(255,255,255,.08),0 {px(8)}px {px(14)}px rgba(0,0,0,.34)}}
.kr.d .sb{{color:{S["dark_dim"]}}}
#krb{{position:absolute;left:0;top:0;z-index:9}}
#krb .pole{{position:absolute;left:0;top:0;width:{px(26)}px;height:{px(420)}px;background:repeating-linear-gradient(180deg,{S["ruler"]} 0 {px(10)}px,#8E7639 {px(10)}px {px(12)}px);box-shadow:0 0 {px(10)}px rgba(0,0,0,.4)}}
#krb .arm{{position:absolute;left:{px(10)}px;top:0;width:{px(6)}px;height:{px(540)}px;background:{S["ruler"]};transform-origin:50% 0;transform:rotate(142deg) translateY(0)}}''')
    html = []
    for i, q in enumerate(keys):
        html.append(f'<div id="kr{i}" class="kr {"d" if q["dark"] else "l"}" style="width:{q["w"]:.1f}px;height:{key_h:.1f}px"><div class="mn">{glyph_html(q["txt"], px(52))}</div>'
                    + (f'<div class="sb">{V.esc(q["sub"])}</div>' if q['sub'] else '') + '</div>')
    p.html.append(f'<div id="krp">{"".join(html)}</div>')
    pole_h = px(420)
    p.html.append('<div id="krb"><div class="pole"></div><div class="arm"></div></div>')
    # poses, frame by frame: only the frames in which a key really moved
    for b in world.bodies:
        i = b.i
        first = None
        last = None
        for f in range(s.frames):
            x, y, a = tr[i, f * 4]
            if np.isnan(x):
                continue
            deg = float(np.degrees(a))
            pose = (x - b.w / 2, y - key_h / 2, deg)
            if first is None:
                first = f
                p.js.append(f"gsap.set('#kr{i}',{{x:{pose[0]:.1f},y:{pose[1]:.1f},rotation:{deg:.2f}}});")
                p.hidden.append(f'#kr{i}')
                p.js.append(f"tl.set('#kr{i}',{{autoAlpha:1}},{V.T(f / V.FPS):.3f});")
            elif last is None or abs(pose[0] - last[0]) > .25 or abs(pose[1] - last[1]) > .25 or abs(deg - last[2]) > .08:
                p.js.append(f"tl.to('#kr{i}',{{x:{pose[0]:.1f},y:{pose[1]:.1f},rotation:{deg:.2f},duration:.03,ease:'none'}},{(f - 1) / V.FPS + .002:.3f});")
            else:
                continue
            last = pose
        event = ev[i]
        hit = min([v for v in (event['floor_t'], event['slab_t']) if v is not None], default=None)
        if SOUND and hit is not None and hit < t_sweep:
            p.sound('key-press', hit, SOUND * rnd.uniform(.7, 1.0))
    # the pile rides the head: slow follow of how far the head sits below its highest point in the slot
    if tops is not None and FLOOR_Y is None:
        last_dy = None
        for f in range(0, s.frames - 3, 3):
            dy = float(tops[min(f, len(tops) - 1)] - top_min)
            if last_dy is None or abs(dy - last_dy) > .6:
                p.js.append(f"tl.to('#krp',{{y:{dy:.1f},duration:.095,ease:'none'}},{f / V.FPS + .002:.3f});")
                last_dy = dy
    bar_top = floor_y + 16 - pole_h
    p.js.append(f"gsap.set('#krb',{{x:{x_from:.0f},y:{bar_top:.0f}}});")
    p.hidden.append('#krb')
    p.js.append(f"tl.set('#krb',{{autoAlpha:1}},{V.T(t_sweep):.3f});")
    p.js.append(f"tl.to('#krb',{{x:{x_to:.0f},duration:{t_end_bar - t_sweep:.3f},ease:'none'}},{V.T(t_sweep):.3f});")
    p.js.append(f"tl.set('#krb',{{autoAlpha:0}},{V.T(t_end_bar):.3f});")
    if SOUND:
        p.sound('whoosh-short', t_sweep + .05, SOUND * 1.4)
    p.write()
    print(f'  rain {t_rain:.2f}s to {t_rain + RAIN_DUR:.2f}s, sweep {t_sweep:.2f}s to {t_end_bar:.2f}s')
    print('snapshot at: ' + ','.join(f'{m:.2f}' for m in (t_rain + .3, t_rain + .7, t_rain + RAIN_DUR + .4, t_sweep - .05, t_sweep + .08, t_sweep + .17, t_sweep + .26, t_end_bar + .05)))


if __name__ == '__main__':
    main()
