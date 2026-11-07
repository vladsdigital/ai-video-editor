#!/usr/bin/env python3
"""PLATE WORD: the words before the payoff stack up under the chin in small dark boxes, each box bigger than the last,
each new one popping in at the bottom and pushing the stack up. On the payoff word the picture cuts to a paper plate
with that one word cut out of it, slamming down from huge, and the live video plays through the letters.

An overlay: the plate is transparent inside the letters, so the reel's own footage and grade are what shows through.
Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html   (SAFE=1 safe-zone guide over the footage, SFX=0 no sounds,
                                               CAPTIONS=0 no stack: the plate alone)
"""
import os
import shutil
import subprocess

from PIL import ImageFont

import vgfx as V

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    font='Instrument Serif',       # the stack's words and the cut-out word
    weight=400,
    italic=False,
    word_case='upper',             # the cut-out word: 'as-said', 'lower' or 'upper'
    stack_case='as-said',
    tracking=-0.012,
    box='#1E4032',                 # the stack's boxes (deep forest green)
    box_ink='#F3EEE1',             # the stack's words (cream)
    paper='#F0ECDF',               # the plate (cream paper)
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
WORD = ''           # the payoff word, as said. Required. Short is best: the shorter, the bigger the letters
STACK = None        # the boxes: a list of [text, slot second] rows. None = the words said before WORD, one box each,
                    # a short word joined to the next, the last MAX_BOXES boxes
MAX_BOXES = 4
LINES = None        # the word on one or two lines. None = two from 4 letters up. Or a list: ['ČLAN', 'OVA']
T_WORD = None       # the cut to the plate. None = when WORD is said
HOLD = 0.70         # seconds the plate stays
WIDTH = 0.88        # share of the frame width the widest line takes
STRETCH = None      # letter height against width. 1 = as drawn. None = 1 on two lines, 1.3 on one (fills the plate higher)
SOUND = 0.0         # volume of a low hit on the plate. 0 = silent, as the look is meant to be
# ==== END CLIP ====

RATIOS = [1, 1.35, 1.9, 2.6]            # box sizes from the first to the last
CARD_TOP, CARD_BOTTOM = V.SAFE_TOP + 8, V.SAFE_BOTTOM - 6


def font_file():
    name = STYLE['font'].replace(' ', '') + f"-{STYLE['weight']}-{'italic' if STYLE['italic'] else 'normal'}.woff2"
    path = os.path.join('assets', 'fonts', name)
    if not os.path.isfile(path):
        V.die(f'{name} is not in assets/fonts: use a face from assets/fonts/fonts.css in the STYLE block')
    return path


def auto_stack(s, t_word):
    rows, cur, t0 = [], '', None
    for w in s.words:
        if w['start'] >= t_word - .02:
            break
        txt = V.bare(w['text'])
        cur, t0 = (cur + ' ' + txt).strip(), (t0 if t0 is not None else w['start'])
        if len(cur) >= 5:
            rows.append([cur, t0])
            cur, t0 = '', None
    if cur:
        rows.append([cur, t0])
    return rows[-MAX_BOXES:]


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
    if not WORD.strip():
        V.die('write WORD in the CLIP block: the payoff word the speaker says')
    said = s.find('^' + V.re.escape(V.bare(WORD.strip())) + '$')
    t_word = T_WORD if T_WORD is not None else (said['start'] if said else None)
    if t_word is None:
        V.die(f'"{WORD}" is not in this slot\'s words: move the slot or set T_WORD')
    t_out = min(s.dur, t_word + HOLD)
    word = V.cased(V.bare(WORD.strip()), STYLE['word_case'])
    lines = LINES or ([word[:(len(word) + 1) // 2], word[(len(word) + 1) // 2:]] if len(word) >= 4 else [word])

    stretch = STRETCH if STRETCH is not None else (1.0 if len(lines) > 1 else 1.3)
    # the plate: every line the same size, the widest one fills WIDTH
    f = ImageFont.truetype(font_file(), 1000)
    track = STYLE['tracking']
    wide = lambda t: f.getlength(t) / 1000 + track * (len(t) - 1)
    cap = -f.getbbox('H', anchor='ls')[1] / 1000
    size = WIDTH * 1080 / max(wide(t) for t in lines)
    tallest = max(-f.getbbox(t, anchor='ls')[1] for t in lines) / 1000
    leading = 1.16 * cap * stretch
    total = (tallest * stretch + (len(lines) - 1) * leading) * size
    if total > CARD_BOTTOM - CARD_TOP:
        size *= (CARD_BOTTOM - CARD_TOP) / total
        total = CARD_BOTTOM - CARD_TOP
    mid = (CARD_TOP + CARD_BOTTOM) / 2
    y0 = mid - total / 2 + tallest * stretch * size          # first baseline
    p = V.Page(s)
    ital = 'italic' if STYLE['italic'] else 'normal'
    texts = ''.join(f'<text transform="translate(540 {y0 + k * leading * size:.1f}) scale(1 {stretch})" text-anchor="middle" fill="#000" '
                    f'font-family="{STYLE["font"]}" font-weight="{STYLE["weight"]}" font-style="{ital}" font-size="{size:.1f}" '
                    f'style="letter-spacing:{track * size:.2f}px">{V.esc(t)}</text>' for k, t in enumerate(lines))
    p.html.append(f'<svg id="plate" width="1080" height="1920" viewBox="0 0 1080 1920" style="position:absolute;left:0;top:0">'
                  f'<defs><mask id="pm" maskUnits="userSpaceOnUse" x="0" y="0" width="1080" height="1920">'
                  f'<rect width="1080" height="1920" fill="#fff"/><g id="pg">{texts}</g></mask></defs>'
                  f'<rect width="1080" height="1920" fill="{STYLE["paper"]}" mask="url(#pm)"/></svg>')
    p.show('#plate', t_word, t_out)
    fr = 1 / V.FPS
    # the slam, frame by frame: about three times too big on its first frame, home on its fifth
    p.js.append(f"gsap.set('#pg',{{svgOrigin:'540 {mid:.0f}',scale:3.2}});")
    p.js.append(f"tl.to('#pg',{{keyframes:[{{scale:1.75,duration:{fr:.4f},ease:'none'}},{{scale:1.18,duration:{fr:.4f},ease:'none'}},"
                f"{{scale:1.04,duration:{fr:.4f},ease:'none'}},{{scale:1,duration:{fr:.4f},ease:'none'}}]}},{V.T(t_word):.3f});")
    print(f'  plate {t_word:.2f}s to {t_out:.2f}s: {" / ".join(lines)}, size {size:.0f}, letters {cap * stretch * size:.0f} px tall')
    if SOUND:
        V.SFX_LEN['impact-bass-1'] = .7
        p.sound('impact-bass-1', t_word, SOUND)

    # the stack, under the chin: bottom fixed, each new box pushes the others up
    t_first = t_word
    rows = []
    if V.env('CAPTIONS') != '0':
        rows = [[V.cased(str(a), STYLE['stack_case']), float(b)] for a, b in (STACK if STACK is not None else auto_stack(s, t_word))]
    if rows:
        t_first = rows[0][1]
        if len(rows) > len(RATIOS):
            V.die(f'at most {len(RATIOS)} boxes fit: shorten STACK')
        ratios = RATIOS[:len(rows)]
        bottom = V.SAFE_BOTTOM - 8
        top_limit = s.chin + 22
        room = bottom - top_limit
        if room < 120:
            V.die('no room under the chin on this clip for the stack: build with CAPTIONS=0 for the plate alone')
        pad_y = .13
        unit = min(room / (sum(ratios) * (1 + 2 * pad_y)), 92)
        fs = [unit * r for r in ratios]
        hs = [z * (1 + 2 * pad_y) for z in fs]
        cx_lim = V.SAFE_RIGHT_FROM <= bottom
        right = 1080 - (V.SAFE_RIGHT if cx_lim else V.SAFE_SIDE)
        for k, (t, _) in enumerate(rows):            # a long word shrinks to fit the safe width
            w = f.getlength(t) * fs[k] / 1000 + fs[k] * .6
            if w > right - V.SAFE_SIDE - 8:
                fs[k] *= (right - V.SAFE_SIDE - 8) / w
        half = max(f.getlength(t) * fs[k] / 2000 + fs[k] * .3 for k, (t, _) in enumerate(rows))
        cx = min(max(s.cx, V.SAFE_SIDE + 8 + half), right - 8 - half)
        p.css.append(f"""
.bx{{position:absolute;left:{cx:.0f}px;top:0;background:{STYLE['box']};color:{STYLE['box_ink']};font-family:'{STYLE['font']}';font-weight:{STYLE['weight']};
  font-style:{ital};white-space:nowrap;line-height:1;transform-origin:50% 0}}""")
        for k, (t, _) in enumerate(rows):
            p.html.append(f'<div id="bx{k}" class="bx" style="font-size:{fs[k]:.1f}px;padding:{fs[k] * pad_y:.1f}px {fs[k] * .3:.1f}px">{V.esc(t)}</div>')
            p.hidden.append(f'#bx{k}')
            p.js.append(f"gsap.set('#bx{k}',{{xPercent:-50}});")
        ease = "back.out(1.5)"
        for st, (_, at) in enumerate(rows):          # state st: boxes 0..st are up
            y = bottom - sum(hs[:st + 1])
            for k in range(st + 1):
                if k == st:
                    p.js.append(f"tl.fromTo('#bx{k}',{{autoAlpha:1,y:{y + hs[k] * .45:.1f},scale:.42}},{{autoAlpha:1,y:{y:.1f},scale:1,duration:{4 * fr:.4f},ease:'{ease}',immediateRender:false}},{V.T(at):.3f});")
                else:
                    p.js.append(f"tl.to('#bx{k}',{{y:{y:.1f},duration:{4 * fr:.4f},ease:'{ease}'}},{V.T(at):.3f});")
                y += hs[k]
        p.js.append(f"tl.set('.bx',{{autoAlpha:0}},{V.T(t_word):.3f});")
        print(f'  stack: ' + ', '.join(f'"{t}" {at:.2f}s {z:.0f}px' for (t, at), z in zip(rows, fs)) + f'  top y {bottom - sum(hs):.0f}, chin {s.chin}')
    p.write()
    print(f'snapshot at: {t_first + .2:.2f},{t_word - .05:.2f},{t_word + .02:.2f},{t_word + .1:.2f},{t_word + .4:.2f},{min(s.dur - .02, t_out + .05):.2f}')
    s.hide_hint([(t_first, t_out)])


if __name__ == '__main__':
    main()
