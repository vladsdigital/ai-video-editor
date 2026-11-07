#!/usr/bin/env python3
"""PENCIL MARK: the shot snaps to black and white, a red grease pencil draws a loose circle round the measured head,
then a short handwritten word and an arrow to the circle write themselves on.

Full picture (the grey is applied to the slot's own footage). Runs from the slot folder.

    build.py      writes index.html   (SAFE=1 safe-zone guide, SFX=0 no sounds)
"""
import math
import random

import headtrack
import vgfx as V

V.PREVIEW = True          # this effect changes the picture, so the footage is always part of it

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    pencil='#1C3729',     # the pencil (the effect colour)
    font='Caveat',        # the handwritten word: a family in assets/fonts/fonts.css
    weight=600,
    word_px=190,
    stroke=9,             # width of the circle and the arrow, px
    contrast=1.14,        # of the black and white
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
WORD = ''          # the short word, one the speaker says, or their own word for themselves. Required
F_SNAP = None      # frame it snaps to black and white. None = on TRIGGER, or 3 frames in
TRIGGER = ''       # the spoken word the snap lands on. '' = F_SNAP
F_BACK = None      # frame it snaps back to colour. None = stays to the slot's last frame (the slot must END ON A CUT)
PLACE = 'auto'     # where the word sits: 'auto' (the emptier side above the head), 'left', 'right'
SOUND = 0.0        # volume of a soft scratch while it draws. 0 = silent
# ==== END CLIP ====

FR = 1 / 30
DRAW_AT, DRAW_FR = 3, 10      # the circle: frames after the snap, frames it takes
WORD_AT, WORD_FR = 26, 9      # the word: frames after the snap, frames it takes
ARROW_FR = 9                  # the arrow runs straight on from the word


def circle_path(rx, ry, seed=11, turns=1.32, tilt=-9):
    """a loose hand-drawn loop from the top right, going round a little more than once, each pass off by a few px"""
    r = random.Random(seed)
    ph = [r.uniform(0, 6.28) for _ in range(4)]
    pts = []
    n = int(72 * turns)
    t0 = -math.pi * .36
    for k in range(n + 1):
        u = k / n
        a = t0 - u * turns * 2 * math.pi                     # counter-clockwise from the top right
        wob = 1 + .018 * math.sin(a * 2 + ph[0]) + .012 * math.sin(a * 5 + ph[1]) + .055 * u * math.sin(a * 1 + ph[2])
        x, y = rx * wob * math.cos(a), ry * wob * math.sin(a)
        c, s = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
        pts.append((x * c - y * s, x * s + y * c))
    d = f'M{pts[0][0]:.1f} {pts[0][1]:.1f}'
    for i in range(1, len(pts) - 1):                         # smooth through the midpoints
        mx, my = (pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2
        d += f'Q{pts[i][0]:.1f} {pts[i][1]:.1f} {mx:.1f} {my:.1f}'
    return d


def main():
    s = V.Slot()
    s.dur = int(s.frames / 30 * 10000) / 10000     # rounded down: a duration rounded up renders one frame too many
    print('words: ' + s.word_list())
    if not WORD.strip():
        V.die('write WORD in the CLIP block: a short word for the mark')
    if len(WORD) > 10:
        V.die(f'"{WORD}" is too long for the mark: one short word, up to 10 letters')
    head = headtrack.track(s)
    n = s.frames
    f_snap = F_SNAP
    if TRIGGER:
        w = s.find('^' + TRIGGER + '$')
        if not w:
            V.die(f'"{TRIGGER}" is not said in this slot. Words here: {s.word_list()}')
        f_snap = round(w['start'] * 30)
    f_snap = 3 if f_snap is None else f_snap
    need = f_snap + WORD_AT + WORD_FR + ARROW_FR + 8
    if need > (F_BACK or n):
        V.die(f'the slot is too short: the mark needs {need} frames from the start, this has {F_BACK or n}. Make --to later')
    i0, i1 = f_snap, min(n - 1, F_BACK or n - 1)
    cxs, cys, tops, chins = (head[k][i0:i1 + 1] for k in ('cx', 'cy', 'top', 'chin'))
    cx0, cy0 = sum(cxs) / len(cxs), sum(cys) / len(cys)
    hw = head['width']
    hh = head['height']
    rx = max(hw * .68, hh * .36)
    ry = hh * .56
    # the circle stays inside the frame, and the word needs room above and beside it
    if cx0 - rx < 12 or cx0 + rx > 1068:
        rx = min(cx0 - 12, 1068 - cx0)
    side = PLACE if PLACE in ('left', 'right') else ('left' if cx0 > 540 else 'right')
    top_edge = cy0 - ry
    S = STYLE
    word_px = S['word_px']
    w_est = len(WORD) * word_px * .42
    word_y = max(V.SAFE_TOP + word_px * .72, min(top_edge - 80, 420))
    if side == 'left':
        word_x = max(V.SAFE_SIDE + 40, min(330, cx0 - rx - w_est - 10)) if cx0 - rx - w_est > 60 else V.SAFE_SIDE + 40
    else:
        word_x = 1080 - V.SAFE_RIGHT - 40 - w_est
    beside = top_edge - 80 < V.SAFE_TOP + word_px * .72      # no wall above the head: the word goes level with the eyes, beside it
    if beside:
        word_y = cy0 - ry * .3
        room = cx0 - rx - V.SAFE_SIDE - 30 if side == 'left' else 1080 - V.SAFE_SIDE - 30 - cx0 - rx
        if room < w_est + 50:
            V.die('the head fills the frame on this clip: there is no room for the word beside the circle')
        word_x = max(V.SAFE_SIDE + 30, cx0 - rx - w_est - 90) if side == 'left' else min(1080 - V.SAFE_SIDE - 30 - w_est, cx0 + rx + 90)
    # the arrow: from the end of the word (or its start, on the right) curving down into the top of the circle
    a0 = (word_x + w_est * .9, word_y - word_px * .16) if side == 'left' else (word_x - 16, word_y - word_px * .16)
    a1 = (cx0 - rx * .34 if side == 'left' else cx0 + rx * .34, top_edge - 24)
    mid = ((a0[0] + a1[0]) / 2 + (40 if side == 'left' else -40), a0[1] - 26)
    if beside:                                                # a short arc across into the circle's side
        a1 = (cx0 - rx * 1.06 if side == 'left' else cx0 + rx * 1.06, cy0 - ry * .08)
        mid = ((a0[0] + a1[0]) / 2, a0[1] - 44)
    tip = math.atan2(a1[1] - mid[1], a1[0] - mid[0])
    def barb(ang, ln=44):
        return f'M{a1[0] + ln * math.cos(tip + ang):.1f} {a1[1] + ln * math.sin(tip + ang):.1f}L{a1[0]:.1f} {a1[1]:.1f}'
    p = V.Page(s)
    p.css.append(f'''
#mk{{position:absolute;inset:0;overflow:visible}}
#mk .pen{{fill:none;stroke:{S['pencil']};stroke-width:{S['stroke']};stroke-linecap:round;stroke-linejoin:round}}
#mk text{{font-family:'{S['font']}';font-weight:{S['weight']};font-size:{word_px}px;fill:{S['pencil']}}}''')
    # the letters are revealed by a thick pen going up and down across each one, so the word looks written, not wiped
    defs, letters, js = '', '', p.js
    x = word_x
    step = w_est / len(WORD)
    letter_at = []
    for k, ch in enumerate(WORD):
        lw = step * 1.2
        x0 = word_x + k * step - step * .12
        pts, zig = [], 5
        for z in range(zig + 1):
            pts.append((x0 + lw * z / zig, word_y + word_px * .3 if z % 2 == 0 else word_y - word_px * .86))
        d = 'M' + 'L'.join(f'{a:.1f} {b:.1f}' for a, b in pts)
        ln = sum(math.dist(pts[i], pts[i + 1]) for i in range(zig))
        defs += (f'<mask id="m{k}" maskUnits="userSpaceOnUse" x="0" y="0" width="1080" height="1920"><path id="z{k}" d="{d}" fill="none" stroke="#fff" '
                 f'stroke-width="{lw / zig * 2.4:.1f}" stroke-linecap="round" stroke-dasharray="{ln:.0f}" stroke-dashoffset="{ln:.0f}"/></mask>')
        letters += f'<text mask="url(#m{k})" x="{word_x + k * step:.1f}" y="{word_y:.1f}">{V.esc(ch)}</text>'
        letter_at.append((k, ln))
    path = circle_path(rx, ry)
    p.html.append(f'''<svg id="mk" width="1080" height="1920" viewBox="0 0 1080 1920"><defs>{defs}
<filter id="gr" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency=".55" numOctaves="2" seed="4"/>
<feDisplacementMap in="SourceGraphic" scale="3.2"/></filter></defs>
<g id="ring" style="visibility:hidden" transform="translate({cx0:.1f} {cy0:.1f})"><path id="ci" class="pen" pathLength="1000" d="{path}" stroke-dasharray="1000" stroke-dashoffset="1000" filter="url(#gr)"/></g>
<g id="wd" style="visibility:hidden">{letters}</g>
<path id="ar" class="pen" pathLength="1000" d="M{a0[0]:.1f} {a0[1]:.1f}Q{mid[0]:.1f} {mid[1]:.1f} {a1[0]:.1f} {a1[1]:.1f}" stroke-dasharray="1000" stroke-dashoffset="1000" filter="url(#gr)" style="visibility:hidden"/>
<path id="b1" class="pen" pathLength="1000" d="{barb(math.pi - .55)}" stroke-dasharray="1000" stroke-dashoffset="1000" style="visibility:hidden"/>
<path id="b2" class="pen" pathLength="1000" d="{barb(math.pi + .55)}" stroke-dasharray="1000" stroke-dashoffset="1000" style="visibility:hidden"/>
</svg>''')
    grey = f"grayscale(1) contrast({S['contrast']})"
    js.append(f"tl.set('#bgv',{{filter:'{grey}'}},{V.T(f_snap * FR):.3f});")
    end = F_BACK if F_BACK else n
    if F_BACK:
        js.append(f"tl.set('#bgv',{{filter:'none'}},{V.T(F_BACK * FR):.3f});")
        js.append(f"tl.set('#mk',{{autoAlpha:0}},{V.T(F_BACK * FR):.3f});")
    # the circle: on at DRAW_AT, drawn with an ease that starts quick and settles, and it stays with the head slowly
    fd = f_snap + DRAW_AT
    js.append(f"tl.set('#ring',{{visibility:'visible'}},{V.T(fd * FR):.3f});")
    for k in range(DRAW_FR + 1):
        u = k / DRAW_FR
        e = 1 - (1 - u) ** 1.7
        js.append(f"tl.set('#ci',{{attr:{{'stroke-dashoffset':{1000 * (1 - e):.1f}}}}},{V.T((fd + k) * FR):.3f});")
    for f in range(fd, end):
        i = min(n - 1, f)
        a, b = max(i0, i - 7), min(i1, i + 7)
        mx = sum(head['cx'][a:b + 1]) / (b - a + 1)
        my = sum(head['cy'][a:b + 1]) / (b - a + 1)
        js.append(f"tl.set('#ring',{{attr:{{transform:'translate({mx:.1f} {my:.1f})'}}}},{V.T(f * FR):.3f});")
    # the word, letter after letter, then the arrow's line and its head
    fw = f_snap + WORD_AT
    js.append(f"tl.set('#wd',{{visibility:'visible'}},{V.T(fw * FR):.3f});")
    per = WORD_FR / len(WORD)
    for k, ln in letter_at:
        steps = max(2, round(per))
        for j in range(steps + 1):
            js.append(f"tl.set('#z{k}',{{attr:{{'stroke-dashoffset':{ln * (1 - j / steps):.1f}}}}},{V.T((fw + k * per + j) * FR):.3f});")
    fa = fw + WORD_FR
    for sel, a, b in (('#ar', fa, fa + ARROW_FR - 3), ('#b1', fa + ARROW_FR - 3, fa + ARROW_FR - 1), ('#b2', fa + ARROW_FR - 1, fa + ARROW_FR + 1)):
        js.append(f"tl.set('{sel}',{{visibility:'visible'}},{V.T(a * FR):.3f});")
        for f in range(a, b + 1):
            u = (f - a) / max(1, b - a)
            js.append(f"tl.set('{sel}',{{attr:{{'stroke-dashoffset':{1000 * (1 - u):.1f}}}}},{V.T(f * FR):.3f});")
    if SOUND:
        p.sound('whoosh-short', fd * FR, SOUND)
    print(f'head {hw:.0f} x {hh:.0f} px at ({cx0:.0f},{cy0:.0f}), circle {rx:.0f} x {ry:.0f}. Snap f{f_snap}, circle f{fd} to f{fd + DRAW_FR}, word f{fw}, arrow f{fa} to f{fa + ARROW_FR + 1}. Word at x {word_x:.0f}, y {word_y:.0f}')
    p.write()
    print('snapshot at: ' + ','.join(f'{(f + .5) * FR:.3f}' for f in (f_snap + 1, fd + 5, fd + DRAW_FR + 3, fw + 5, fa + 4, fa + ARROW_FR + 3)))


if __name__ == '__main__':
    main()
