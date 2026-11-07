#!/usr/bin/env python3
"""LETTER STAMP: one huge serif word lands letter by letter BEHIND the speaker's head, across the top of the frame.
MODE 'stamp': each letter fades up a touch too big and settles, two frames after the one before it, with an optional
thin rule running through the tops of the letters. MODE 'drop': each letter hits the line squashed flat, springs up
past its height and settles. Where the word crosses a bright part of the room it turns dark, so it stays readable.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html   (SAFE=1 safe-zone guide, SFX=0 no sounds, CAPTIONS=0 = no word, nothing to show)
"""
import os
import shutil
import subprocess

import numpy as np
from PIL import Image, ImageFilter, ImageFont

import vgfx as V

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    font='Instrument Serif',       # the word: a face from assets/fonts/fonts.css
    weight=400,
    italic=False,
    case='upper',                  # 'as-said', 'lower' or 'upper'
    tracking=-0.012,               # letter spacing, em
    ink='#F3EEE1',                 # cream, on the dark parts of the room
    ink_dark='#163127',            # deep forest green, where the word crosses a bright part of the room
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
WORD = ''           # the word, as the speaker says it. Required. Best 4 to 7 letters: longer means smaller
MODE = 'stamp'      # 'stamp' or 'drop'
RULE = False        # stamp only: a thin rule through the tops of the letters, drawn while they land
T_IN = None         # slot second the first letter lands. None = when WORD is said
T_OUT = None        # when the word goes. None = stays to the end of the slot if the slot ends on a cut of the reel,
                    # else fades 0.8 s after the word was said plus the rest of its line (at most the slot end)
STAGGER = 2         # frames between two letters
WIDTH = 0.90        # width of the word, share of the frame width (it shrinks when there is no height for it)
TUCK = None         # share of the letter height behind the head. None = 0.14 for stamp, 0.26 for drop, up to 0.5 when the room is short
LEAD = ''           # optional first line, stamped above WORD a beat earlier ("ima preko" over "500"). '' = one word only
T_LEAD = None       # slot second LEAD starts. None = when its first word is said
GROUND = None       # a colour: on the first letter of WORD the whole room cuts to this flat colour, the speaker stays.
                    # '#163127' = deep forest green. None = the room stays
TWO_TONE = True     # False = one colour for the whole word
LIGHT = 172         # how bright (0-255) the room must be for the word to turn dark there
SOUND = 0.0         # volume of a soft tick per letter. 0 = silent, as the look is meant to be
# ==== END CLIP ====

FF = shutil.which('ffmpeg') or 'ffmpeg'
SIDE = 40           # px kept free left and right


def font_file():
    name = STYLE['font'].replace(' ', '') + f"-{STYLE['weight']}-{'italic' if STYLE['italic'] else 'normal'}.woff2"
    path = os.path.join('assets', 'fonts', name)
    if not os.path.isfile(path):
        V.die(f'{name} is not in assets/fonts: use a face from assets/fonts/fonts.css in the STYLE block')
    return path


def measure_head(s):
    """head top and centre from the cutout itself, over the whole slot"""
    if not os.path.isfile('assets/subject.webm'):
        V.die('assets/subject.webm is missing: this effect needs the clean cutout (setup.py --matting, then fx_new.py)')
    w, h = 270, 480
    step = max(1, s.frames // 14)
    raw = subprocess.run([FF, '-v', 'error', '-c:v', 'libvpx-vp9', '-i', 'assets/subject.webm', '-vf',
                          f"select='not(mod(n\\,{step}))',alphaextract,scale={w}:{h}", '-fps_mode', 'passthrough',
                          '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True).stdout
    a = np.frombuffer(raw, dtype=np.uint8)
    n = len(a) // (w * h)
    if not n:
        V.die('could not read the cutout (assets/subject.webm): make the slot again with fx_new.py')
    tops, xs, widths, ends = [], [], [], []
    for fr in a[:n * w * h].reshape(n, h, w):
        rows = np.where((fr > 128).sum(1) >= 6)[0]
        if len(rows):
            t = rows[0]
            tops.append(t * 4)
            ends.append(rows[-1] * 4)
            band = fr[t:t + 40] > 128
            cols = np.where(band.any(0))[0]
            xs.append((cols[0] + cols[-1]) * 2)
            widths.append((cols[-1] - cols[0]) * 4)
    if not tops:
        V.die('nobody in the cutout on this clip: the word has no head to go behind')
    return int(np.median(tops)), int(min(tops)), int(np.median(xs)), int(np.median(widths)), int(np.median(ends))


def light_mask(s, box):
    """Where the room is bright behind the word: a soft white-on-transparent picture from the slot's own footage.
    Returns the share of the word's box that is bright."""
    step = max(1, s.frames // 9)
    raw = subprocess.run([FF, '-v', 'error', '-i', 'assets/aroll.mp4', '-vf', f"select='not(mod(n\\,{step}))'", '-fps_mode', 'passthrough',
                          '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True).stdout
    a = np.frombuffer(raw, dtype=np.uint8)
    n = len(a) // (1080 * 1920)
    if not n:
        return 0.0
    med = np.median(a[:n * 1080 * 1920].reshape(n, 1920, 1080), axis=0).astype(np.uint8)
    soft = np.asarray(Image.fromarray(med).filter(ImageFilter.GaussianBlur(3)), dtype=np.float32)
    alpha = np.clip((soft - LIGHT) / 14 + .5, 0, 1)
    x0, y0, x1, y1 = [int(v) for v in box]
    share = float(alpha[max(0, y0):y1, max(0, x0):x1].mean())
    img = np.zeros((1920, 1080, 4), dtype=np.uint8)
    img[..., :3] = 255
    img[..., 3] = (alpha * 255).astype(np.uint8)
    Image.fromarray(img).save(os.path.join('assets', 'lightmask.png'))
    return share


def ends_on_cut(s):
    proj = s.clip.get('project')
    if not proj:
        return False
    segs = V._json(os.path.join(proj, 'segments.json'), []) or []
    end = int(s.clip.get('frame') or 0) + s.frames
    last = max((g['frame'] + g['frames'] for g in segs), default=-1)
    return any(abs(g['frame'] - end) <= 1 for g in segs) or abs(last - end) <= 1


def letter_svg(ch, x, base, size, fill):
    ital = 'italic' if STYLE['italic'] else 'normal'
    return (f'<svg width="1080" height="1920" viewBox="0 0 1080 1920" style="position:absolute;left:0;top:0;overflow:visible">'
            f'<text x="{x:.1f}" y="{base:.1f}" font-family="{STYLE["font"]}" font-weight="{STYLE["weight"]}" font-style="{ital}" '
            f'font-size="{size:.1f}" fill="{fill}">{V.esc(ch)}</text></svg>')


def main():
    s = V.Slot()
    s.dur = int(s.frames / V.FPS * 1000) / 1000      # rounded down: a duration rounded up renders one frame too many
    V.PREVIEW = True                 # a cutout effect: the render holds the footage, the word and the speaker
    V.SFX_LEN.update({'click': .2})
    print('words: ' + s.word_list())
    if MODE not in ('stamp', 'drop'):
        V.die("MODE is 'stamp' or 'drop'")
    if not WORD.strip():
        V.die('write WORD in the CLIP block: one word the speaker says')
    word = V.cased(WORD.strip(), STYLE['case'])
    said = s.find('^' + V.re.escape(V.bare(WORD.strip())) + '$')
    t_in = T_IN if T_IN is not None else (said['start'] if said else .3)
    top, top_min, hx, hw, body_end = measure_head(s)
    print(f'head from the cutout: top y {top} (highest {top_min}), centre x {hx}, width near the top {hw}')

    # size: as wide as asked, as tall as the room above the head allows
    f = ImageFont.truetype(font_file(), 1000)
    track = STYLE['tracking']
    tuck = TUCK if TUCK is not None else (.26 if MODE == 'drop' else .14)
    adv = lambda txt, k: f.getlength(txt[:k]) / 1000 + track * k
    wide = lambda txt: adv(txt, len(txt)) - track
    tall = lambda txt: -f.getbbox(txt, anchor='ls')[1] / 1000      # tallest ink above the line per px of size (hačeks too)
    cap1 = -f.getbbox('H', anchor='ls')[1] / 1000
    lead = V.cased(LEAD.strip(), STYLE['case'])
    width = min(WIDTH * 1080, 1080 - 2 * SIDE)
    box_top = V.SAFE_TOP + 8
    if lead:                                          # the word is about a third bigger than the line above it
        s_lead = width / wide(lead)
        size = min(width / wide(word), s_lead * 1.35)
        s_lead = min(s_lead, size / 1.15)               # a long word is never smaller than the line above it
    else:
        s_lead, size = 0, width / wide(word)
    if TUCK is None and not lead:                     # a tall head: the word goes further behind it before it gets small
        while tuck < .5 and (tall(word) - tuck * cap1) * size > top - box_top:
            tuck += .02
    gap = .03 * s_lead
    need = (tall(word) - tuck * cap1) * size + (tall(lead) * s_lead + gap if lead else 0)
    if need > top - box_top:
        k = (top - box_top) / need
        size, s_lead, gap = size * k, s_lead * k, gap * k
    if cap1 * size < 110:
        V.die(f'no room above the head on this clip: the head top is at y {top} and the safe zone starts at {V.SAFE_TOP}')
    base = top + tuck * cap1 * size
    wpx = wide(word) * size

    def place(txt, sz, line_base):
        x0 = (1080 - wide(txt) * sz) / 2
        return [(c, x0 + adv(txt, k) * sz, x0 + adv(txt, k) * sz + f.getlength(c) * sz / 2000, line_base, sz) for k, c in enumerate(txt)]

    letters = place(word, size, base)
    box = [(1080 - wpx) / 2, base - tall(word) * size, (1080 + wpx) / 2, base]
    lead_base = base - tall(word) * size - gap
    first_lead = []
    if lead:
        first_lead = place(lead, s_lead, lead_base)
        box = [min(box[0], (1080 - wide(lead) * s_lead) / 2), lead_base - tall(lead) * s_lead,
               max(box[2], (1080 + wide(lead) * s_lead) / 2), base]
        print(f'  lead "{lead}": size {s_lead:.0f}, line at y {lead_base:.0f}')
    print(f'  "{word}" {MODE}: size {size:.0f}, letters {cap1 * size:.0f} px tall, ink x {box[0]:.0f}..{box[2]:.0f} y {box[1]:.0f}..{box[3]:.0f}')

    p = V.Page(s)
    p.css.append(f"""
.ws{{position:absolute;inset:0}}
.lt{{position:absolute;inset:0}}
.ws.dk{{-webkit-mask-image:url(assets/lightmask.png);mask-image:url(assets/lightmask.png);-webkit-mask-size:1080px 1920px;mask-size:1080px 1920px}}
.rule{{position:absolute;height:3px;transform-origin:0 50%}}
#gnd{{position:absolute;inset:0}}
#subj{{position:absolute;left:0;top:0;width:1080px;height:1920px}}""")
    share = light_mask(s, box) if TWO_TONE else 0.0
    two = share > .005
    print(f'  bright room behind {share * 100:.0f}% of the word: ' + ('it turns dark there' if two else 'one colour'))
    if GROUND:
        # a cutout that stops above the frame edge (a desk, a laptop) would leave hands floating on the flat colour:
        # the real picture comes back under the body
        fade = '' if body_end >= 1880 else (f'-webkit-mask-image:linear-gradient(#000 {body_end - 300}px,transparent {body_end - 110}px);'
                                            f'mask-image:linear-gradient(#000 {body_end - 300}px,transparent {body_end - 110}px);')
        p.html.append(f'<div id="gnd" style="background:{GROUND};{fade}"></div>')
        p.show('#gnd', t_in)
    layers = [('', STYLE['ink'])] + ([(' dk', STYLE['ink_dark'])] if two else [])
    rule_y = base - cap1 * size * .94
    every = first_lead + letters
    for cls, col in layers:
        inner = ''.join(f'<div class="lt l{k}" style="transform-origin:{c[2]:.1f}px {c[3]:.1f}px">{letter_svg(c[0], c[1], c[3], c[4], col)}</div>'
                        for k, c in enumerate(every))
        if RULE and MODE == 'stamp':
            inner += (f'<div class="rule rl" style="left:{SIDE}px;width:{1080 - 2 * SIDE}px;top:{rule_y:.0f}px;background:{col}"></div>')
        p.html.append(f'<div class="ws{cls}">{inner}</div>')
    dur = s.dur
    v = f'muted playsinline data-start="0" data-media-start="0" data-duration="{dur:.4f}"'
    p.html.append(f'<video id="subj" src="assets/subject.webm" {v} data-track-index="1"></video>')
    if GROUND and two:
        p.js.append(f"tl.set('.ws.dk',{{autoAlpha:0}},{V.T(t_in):.3f});")   # on the flat colour the whole word is one ink

    fr = 1 / V.FPS
    n = len(word)
    t_lead = 0.0
    if lead:
        w0 = s.find('^' + V.re.escape(V.bare(LEAD.split()[0])) + '$')
        t_lead = T_LEAD if T_LEAD is not None else (w0['start'] if w0 else max(0.0, t_in - len(lead) * STAGGER * fr - .1))
    times = [t_lead + k * STAGGER * fr for k in range(len(first_lead))] + [t_in + k * STAGGER * fr for k in range(n)]
    for k, at in enumerate(times):
        sel = f'.l{k}'
        p.hidden.append(sel)
        if MODE == 'stamp':
            # up a touch too big and see-through, settled four frames later
            p.js.append(f"tl.fromTo('{sel}',{{autoAlpha:.06,scale:1.11}},{{autoAlpha:1,scale:1,duration:{4 * fr:.4f},ease:'power1.out',immediateRender:false}},{V.T(at):.3f});")
        else:
            # hits the line squashed (each letter a bit flatter than the last), holds two frames, springs past its height, settles
            sq = max(.45, .82 - .09 * k)
            p.js.append(f"tl.set('{sel}',{{autoAlpha:1,scaleY:{sq:.2f},scaleX:1.02}},{V.T(at):.3f});")
            p.js.append(f"tl.to('{sel}',{{keyframes:[{{scaleY:{sq + .05:.2f},scaleX:1.015,duration:{fr:.4f},ease:'none'}},"
                        f"{{scaleY:1.08,scaleX:.985,duration:{2 * fr:.4f},ease:'power2.out'}},"
                        f"{{scaleY:.985,scaleX:1.005,duration:{2 * fr:.4f},ease:'sine.inOut'}},"
                        f"{{scaleY:1,scaleX:1,duration:{2 * fr:.4f},ease:'sine.out'}}]}},{V.T(at + fr):.3f});")
        if SOUND:
            p.sound('click-soft', at, SOUND)
    t_done = t_in + (n - 1) * STAGGER * fr + 4 * fr
    if RULE and MODE == 'stamp':
        p.hidden.append('.rl')
        p.js.append(f"tl.fromTo('.rl',{{autoAlpha:1,scaleX:0}},{{autoAlpha:1,scaleX:1,duration:{t_done - t_in:.3f},ease:'power2.out',immediateRender:false}},{V.T(t_in):.3f});")
    if T_OUT is not None:
        t_out = T_OUT
    elif ends_on_cut(s):
        t_out = dur
    else:
        t_out = min(dur - .02, t_done + 1.4)
    if t_out < dur - .02:
        p.js.append(f"tl.to('.ws',{{autoAlpha:0,duration:{4 * fr:.4f},ease:'none'}},{V.T(t_out - 4 * fr):.3f});")
    print(f'  letters {t_in:.2f}s to {t_done:.2f}s, ' + ('stays to the cut at the slot end' if t_out >= dur - .02 else f'gone at {t_out:.2f}s'))
    p.write()
    print(f'snapshot at: {max(0, t_in - .05):.2f},{t_in + 3 * fr:.2f},{(t_in + t_done) / 2:.2f},{t_done + .1:.2f},{max(0, dur - .1):.2f}')


if __name__ == '__main__':
    main()
