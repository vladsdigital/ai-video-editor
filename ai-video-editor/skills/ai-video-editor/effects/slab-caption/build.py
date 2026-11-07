#!/usr/bin/env python3
"""SLAB CAPTION: the key word springs up from below into a big slab at the top of the frame, a second word in serif
italic opens under it from the right, small tags pop in one by one under the chin, and the payoff lands on a tilted
paper strip. At the end the pieces fold shut one after the other.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html   (SAFE=1 safe-zone guide over the footage, SFX=0 no sounds, CAPTIONS=0 accepted:
                                               the words ARE the effect, so they always draw)
"""
import json
import math
import os
import shutil
import subprocess

from PIL import ImageFont

import vgfx as V

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    font='Inter Tight',            # the slab word and the tags (a heavy sans)
    weight=900,
    tag_weight=800,
    tracking=-0.03,
    serif_font='Instrument Serif', # the second word and the payoff
    serif_weight=400,
    serif_italic=True,
    case='upper',                  # slab word and tags: 'as-said', 'lower' or 'upper'
    serif_case='lower',            # second word and payoff
    card='#163127',                # slab, second box, tags (deep forest green)
    ink='#F6F1E5',                 # cream words
    accent='#CDB062',              # the second word (old gold)
    paper='#F0ECDF',               # the payoff strip (cream paper)
    paper_ink='#163127',
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
SLAB = ''           # the key word, as said. Required
SECOND = ''         # the word under it, as said. '' = none
TAGS = []           # the small words under the chin, in the order said: ['kod', 'poslovanja']. [] = none
PAYOFF = ''         # the last words, as said ("si ti."). Required. Up to about 12 letters
TIMES = {}          # by hand: {'slab': 0.1, 'second': 0.4, 'tags': [0.9, 1.1], 'payoff': 2.5}. Whatever is left out = when it is said
T_OUT = None        # when the last piece has folded shut. None = 0.95 s after the payoff, at most the slot end
TILT = -3.0         # tilt of the payoff strip, degrees
SOUND = 0.0         # volume of a soft tick on each piece. 0 = silent, as the look is meant to be
# ==== END CLIP ====

FR = 1 / V.FPS


def font(family, weight, italic=False):
    name = family.replace(' ', '') + f"-{weight}-{'italic' if italic else 'normal'}.woff2"
    path = os.path.join('assets', 'fonts', name)
    if not os.path.isfile(path):
        V.die(f'{name} is not in assets/fonts: use a face from assets/fonts/fonts.css in the STYLE block')
    f = ImageFont.truetype(path, 1000)
    try:                                              # a variable font opens at its default weight: set the real one
        f.set_variation_by_axes([min(a['maximum'], max(a['minimum'], weight)) if a.get('name') in (b'Weight', 'Weight') else a['default']
                                 for a in f.get_variation_axes()])
    except OSError:
        pass                                          # a static font
    return f


def say(s, text, after):
    """when `text` starts being said, at or after `after`"""
    first = V.bare(str(text).split()[0])
    w = s.find('^' + V.re.escape(first) + '$', after)
    if not w:
        V.die(f'"{first}" is not said in this slot after {after:.2f}s: check the words or set TIMES')
    return w['start']


def keys(sel, at, frames, extra=''):
    """one value per frame: frames = [dict, dict, ...], each reached one frame after the one before"""
    kf = [dict(v, duration=round(FR, 4), ease='none') for v in frames]
    return f"tl.to('{sel}',{{keyframes:{json.dumps(kf)}{extra}}},{V.T(at):.3f});"


def lowest_chin(s):
    """The layout's head box can stop above the real chin, and a speaker leans. When the reel has a cutout, the lowest
    neck over this slot's frames (the narrowest row under the head) moves s.chin down. No cutout: the layout stands."""
    sub = os.path.join(s.clip.get('project') or '', 'assets', 'subject.webm')
    if not os.path.isfile(sub):
        return
    try:
        import numpy as np
        w, h = 270, 480
        raw = subprocess.run([shutil.which('ffmpeg') or 'ffmpeg', '-v', 'error', '-c:v', 'libvpx-vp9', '-ss', f'{s.t0:.3f}', '-t', f'{s.dur:.3f}', '-i', sub,
                              '-vf', f"select='not(mod(n\\,{max(1, s.frames // 14)}))',alphaextract,scale={w}:{h}", '-fps_mode', 'passthrough',
                              '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True).stdout
        a = np.frombuffer(raw, dtype=np.uint8)
        n = len(a) // (w * h)
        necks = []
        for fr in a[:n * w * h].reshape(n, h, w):
            rows = (fr > 128).sum(1)
            lit = np.where(rows >= 6)[0]
            if not len(lit):
                continue
            t = lit[0]
            hw = rows[t:t + 45].max()                 # the head's width, from its top part
            lo, hi = t + int(.5 * hw), min(h - 1, t + int(1.9 * hw))
            below = np.where(rows[lo:hi] > 1.7 * hw)[0]   # stop where the shoulders start
            hi = lo + below[0] if len(below) else hi
            if hi > lo:
                necks.append((lo + int(np.argmin(rows[lo:hi]))) * 4 + 40)      # 40 px: the jaw sits over the narrowest row
        if necks and max(necks) > s.chin:
            print(f'placement: chin moved from y {s.chin} to y {max(necks)} (the lowest neck in this slot, from the cutout)')
            s.chin = max(necks)
    except (OSError, ValueError, ImportError):
        pass


def main():
    s = V.Slot()
    s.dur = int(s.frames / V.FPS * 1000) / 1000      # rounded down: a duration rounded up renders one frame too many
    lowest_chin(s)
    print('words: ' + s.word_list())
    print(s.where())
    if not SLAB.strip() or not PAYOFF.strip():
        V.die('write SLAB and PAYOFF in the CLIP block: words the speaker says')
    # ---- when
    t_slab = TIMES.get('slab', None)
    t_slab = t_slab if t_slab is not None else say(s, SLAB, 0)
    t_sec = (TIMES.get('second') if TIMES.get('second') is not None else say(s, SECOND, t_slab)) if SECOND.strip() else None
    t = t_sec if t_sec is not None else t_slab
    t_tags = []
    for k, w in enumerate(TAGS):
        given = (TIMES.get('tags') or [None] * len(TAGS))[k]
        t = given if given is not None else say(s, w, t + .01)
        t_tags.append(t)
    t_pay = TIMES.get('payoff') if TIMES.get('payoff') is not None else say(s, PAYOFF, t + .01)
    t_out = min(s.dur, T_OUT if T_OUT is not None else t_pay + .95)
    if t_out - t_pay < .4:
        V.die(f'the payoff has only {t_out - t_pay:.2f}s on screen: make the slot longer (it may run over a cut)')

    # ---- where: the slab stack between the safe top and the head, the rest between the chin and the safe bottom
    S = STYLE
    fheavy, ftag = font(S['font'], S['weight']), font(S['font'], S['tag_weight'])
    fserif = font(S['serif_font'], S['serif_weight'], S['serif_italic'])
    top = V.SAFE_TOP + 8
    room = s.head_top - 18 - top
    # no room above the head: the whole stack moves to the chest, under the chin
    chest_top = s.chin + 24
    on_chest = room < 110
    if on_chest:
        top = chest_top
        room = V.SAFE_BOTTOM - chest_top - 96 - 190     # the tags and a small payoff still fit under it
        print(f'placement: no room above the head (top at y {s.head_top}), so the slab sits on the chest from y {top:.0f}')
    full = 408                                        # the stack's full height: slab 204 and second box 210, 6 px shared
    if not SECOND.strip():
        full = 204
    k = min(1.0, room / full)
    if room < 110:
        V.die(f'no room for the slab above the head (top at y {s.head_top}) or on the chest (chin at y {s.chin})')
    word = V.cased(V.bare(SLAB.strip()), S['case'])
    fs = 187 * k
    wide = lambda f, t, z, tr=0: f.getlength(t) * z / 1000 + tr * z * (len(t) - 1)
    max_w = 1080 - 2 * V.SAFE_SIDE - 20
    pad_x = 48 * k
    tw = wide(fheavy, word, fs, S['tracking'])
    if tw + 2 * pad_x > max_w:
        fs *= (max_w - 2 * pad_x) / (tw + 2 * pad_x)
    h1 = 204 * k
    w1 = wide(fheavy, word, fs, S['tracking']) + 2 * pad_x
    x1 = 66 if k >= .99 else (1080 - w1) / 2 - 40 * k   # a little left of centre, as the second box hangs to the right
    x1 = max(V.SAFE_SIDE + 8, x1)
    y1 = top
    sec = V.cased(SECOND.strip(), S['serif_case'])
    fs2 = 200 * k
    pad2 = 30 * k
    w2 = wide(fserif, sec, fs2) + 2 * pad2 if sec else 0
    if w2 > max_w:
        fs2 *= max_w / w2
        w2 = max_w
    h2 = 210 * k
    y2 = y1 + h1 - 6 * k
    r2 = min(x1 + w1 + 54 * k, 1080 - V.SAFE_SIDE - 8)
    x2 = max(V.SAFE_SIDE + 8, r2 - w2)
    print(f'  slab "{word}" size {fs:.0f}: x {x1:.0f}..{x1 + w1:.0f} y {y1:.0f}..{y1 + h1:.0f}'
          + (f'; second "{sec}" size {fs2:.0f}: x {x2:.0f}..{x2 + w2:.0f} y {y2:.0f}..{y2 + h2:.0f}' if sec else '') + f'  (head top {s.head_top})')

    tags = [V.cased(V.bare(w), S['case']) for w in TAGS]
    bottom = V.SAFE_BOTTOM - 6
    tag_top = (y2 + h2 if sec else y1 + h1) + 12 if on_chest else s.chin + 16
    right = 1080 - V.SAFE_RIGHT - 6
    left = V.SAFE_SIDE + 10
    tfs, row_h, tag_w = 62.0, 0, []
    if tags:
        gap = 12
        base = [wide(ftag, t, 1) for t in tags]
        tfs = min(62.0, (right - left - gap * (len(tags) - 1)) / (sum(base) + .44 * len(tags)))
        tag_w = [b * tfs + .44 * tfs for b in base]
        row_h = tfs * 1.42
    pay_top = tag_top + row_h - 4 if tags else (tag_top if on_chest else s.chin + 30)
    pay = V.cased(PAYOFF.strip(), S['serif_case'])
    pfs = 190.0
    pw = wide(fserif, pay, pfs) + 72
    pad_rot = lambda w: abs(math.sin(math.radians(TILT))) * w / 2
    ph = pfs * 1.2
    while (pay_top + ph + pad_rot(pw) > bottom or pw > right - left - 10) and pfs > 40:
        pfs -= 2
        pw = wide(fserif, pay, pfs) + 72 * pfs / 190
        ph = pfs * 1.2
    if pfs < 60:
        V.die(f'no room under the chin for the payoff (chin at y {s.chin}): shorter PAYOFF or fewer TAGS')
    px = left + 2
    py = pay_top + pad_rot(pw)
    print(f'  tags size {tfs:.0f} from y {tag_top}; payoff "{pay}" size {pfs:.0f}: x {px:.0f}..{px + pw:.0f} y {py:.0f}..{py + ph:.0f}  (chin {s.chin})')

    # ---- page
    p = V.Page(s)
    italic = 'italic' if S['serif_italic'] else 'normal'
    p.css.append(f"""
.pc{{position:absolute;background:{S['card']};white-space:nowrap}}
.hv{{font-family:'{S['font']}';font-weight:{S['weight']};letter-spacing:{S['tracking']}em;color:{S['ink']};line-height:1}}
.sf{{font-family:'{S['serif_font']}';font-weight:{S['serif_weight']};font-style:{italic};line-height:1}}
#sl{{display:flex;align-items:center;justify-content:center}}
#s2{{overflow:hidden}}
#s2 span{{position:absolute;left:{pad2:.1f}px;top:{(h2 - fs2 * 1.0) / 2:.1f}px;color:{S['accent']}}}
.tg{{font-family:'{S['font']}';font-weight:{S['tag_weight']};color:{S['ink']};line-height:1;display:flex;align-items:center;justify-content:center;
  font-size:{tfs:.1f}px;height:{row_h:.1f}px}}
#po{{background:{S['paper']};color:{S['paper_ink']};display:flex;align-items:center;justify-content:center}}""")
    p.html.append(f'<div id="sl" class="pc hv" style="left:{x1:.1f}px;top:{y1:.1f}px;width:{w1:.1f}px;height:{h1:.1f}px;font-size:{fs:.1f}px">{V.esc(word)}</div>')
    if sec:
        p.html.append(f'<div id="s2" class="pc" style="left:{x2:.1f}px;top:{y2:.1f}px;width:{w2:.1f}px;height:{h2:.1f}px"><span class="sf" style="font-size:{fs2:.1f}px">{V.esc(sec)}</span></div>')
    x = left
    for i, t in enumerate(tags):
        p.html.append(f'<div id="tg{i}" class="pc tg" style="left:{x:.1f}px;top:{tag_top}px;width:{tag_w[i]:.1f}px">{V.esc(t)}</div>')
        x += tag_w[i] + 12
    p.html.append(f'<div id="po" class="sf" style="position:absolute;left:{px:.1f}px;top:{py:.1f}px;width:{pw:.1f}px;height:{ph:.1f}px;font-size:{pfs:.1f}px">{V.esc(pay)}</div>')

    # ---- motion, frame by frame
    p.hidden.append('#sl')
    # the slab starts this far below its place, at most in the hair
    d0 = 480 * k if on_chest else min(480 * k, s.head_top + 150 - y1 - h1)
    p.js.append(f"gsap.set('#sl',{{y:{d0:.0f},scale:.72,rotation:2.4}});")
    p.js.append(f"tl.set('#sl',{{autoAlpha:1}},{V.T(t_slab):.3f});")
    p.js.append(keys('#sl', t_slab, [dict(y=d0 * .38, scale=.86, rotation=2.6), dict(y=d0 * .13, scale=.96, rotation=-1.4),
                                     dict(y=-d0 * .015, scale=1.012, rotation=-.9), dict(y=-d0 * .012, scale=1.006, rotation=-.3),
                                     dict(y=0, scale=1, rotation=0)]))
    if SOUND:
        p.sound('click-soft', t_slab, SOUND)
    if sec:
        p.hidden.append('#s2')
        hh = h2
        p.js.append("gsap.set('#s2',{clipPath:'inset(0% 0% 0% 97%)'});")
        p.js.append(f"gsap.set('#s2 span',{{y:{hh * .62:.1f}}});")
        p.js.append(f"tl.set('#s2',{{autoAlpha:1}},{V.T(t_sec):.3f});")
        p.js.append(keys('#s2', t_sec, [dict(clipPath='inset(0% 0% 0% 62%)'), dict(clipPath='inset(0% 0% 0% 28%)'),
                                        dict(clipPath='inset(0% 0% 0% 8%)'), dict(clipPath='inset(0% 0% 0% 0%)')]))
        p.js.append(keys('#s2 span', t_sec, [dict(y=hh * .42), dict(y=hh * .18), dict(y=hh * .05), dict(y=0)]))
    for i, at in enumerate(t_tags):
        sel = f'#tg{i}'
        p.hidden.append(sel)
        p.js.append(f"gsap.set('{sel}',{{y:{row_h * .42:.1f},scaleY:.12,scaleX:.9}});")
        p.js.append(f"tl.set('{sel}',{{autoAlpha:1}},{V.T(at):.3f});")
        p.js.append(keys(sel, at, [dict(y=row_h * .34, scaleY=.7, scaleX=.88), dict(y=row_h * .12, scaleY=.92, scaleX=.96),
                                   dict(y=-row_h * .05, scaleY=1.04, scaleX=1.01), dict(y=0, scaleY=1, scaleX=1)]))
    p.hidden.append('#po')
    p.js.append(f"gsap.set('#po',{{scale:1.56,rotation:{TILT * 2.1:.2f},x:{pw * .16:.1f}}});")
    p.js.append(f"tl.set('#po',{{autoAlpha:1}},{V.T(t_pay):.3f});")
    p.js.append(keys('#po', t_pay, [dict(scale=1.3, rotation=TILT * 1.7, x=pw * .08), dict(scale=1.12, rotation=TILT * 1.35, x=pw * .03),
                                    dict(scale=1.04, rotation=TILT * 1.12, x=pw * .01), dict(scale=1, rotation=TILT, x=0)]))

    # ---- out: each piece folds shut in two frames, two frames after the one before it
    order = ['#sl'] + (['#s2'] if sec else []) + (['.tg'] if tags else []) + ['#po']
    first_out = t_out - (len(order) * 2 + 1) * FR
    for j, sel in enumerate(order):
        at = first_out + j * 2 * FR
        p.js.append(f"tl.to('{sel}',{{keyframes:{json.dumps([dict(scaleY=.55, duration=round(FR, 4), ease='none'), dict(scaleY=.05, duration=round(FR, 4), ease='none')])}}},{V.T(at):.3f});")
        p.js.append(f"tl.set('{sel}',{{autoAlpha:0}},{V.T(at + 2 * FR):.3f});")
    p.write()
    print(f'snapshot at: {t_slab + .03:.2f},{t_slab + .3:.2f},{(t_sec or t_slab) + .1:.2f},{(t_tags[-1] if t_tags else t_pay) + .1:.2f},{t_pay + .02:.2f},{t_pay + .4:.2f},{first_out + .1:.2f}')
    s.hide_hint([(t_slab, t_out)])


if __name__ == '__main__':
    main()
