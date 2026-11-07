#!/usr/bin/env python3
"""GRADE CURTAIN (mood): on the word a thin light edge drops from the top of the frame and pulls a moody grade down
behind it like a curtain, fast then slowing. Grain and a vignette hold while it is dark, and at the end the edge rises
back and the plain picture returns.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html   (SAFE=1 safe-zone guide, SFX=0 no sounds)
"""
import os

os.environ.setdefault('PREVIEW', '1')    # a full picture effect: the footage is always in the page
import grade as G
import vgfx as V

# ==== STYLE (the reel's look wins; this effect draws no words) ====
STYLE = dict(edge='#EEF2EA')    # colour of the thin edge of the curtain
# ==== END STYLE ====

# ==== CLIP (edit this) ====
DROP = None         # the word it falls on (a word from words.json) or seconds. None = the first word after 0.3 s
LIFT = 'auto'       # when it starts to rise: seconds, a word, 'auto' = 14 frames before the slot ends, None = stays dark to a cut
LOOK = 'mood'       # 'mood', 'film' or 'warm' (grade.py)
GRAIN = 8           # moving grain while it is dark. 0 = none
VIGNETTE = .5       # corner darkening while it is dark (radians, .5 gentle, .9 heavy). 0 = none
SFX_GAIN = 1.0
# ==== END CLIP ====

MOVE = 10           # frames the fall takes
POWER = 2.7         # how hard it slows down as it lands


def when(s, what, label):
    if isinstance(what, (int, float)):
        return float(what)
    w = s.find('^' + V.re.escape(what) + '$')
    if not w:
        V.die(f'the word "{what}" ({label}) is not in this slot: pick a word from the list above')
    return w['start']


def main():
    s = V.Slot()
    s.dur = int(s.frames / V.FPS * 1e4) / 1e4   # cut, not rounded: a duration rounded up renders one frame too many
    print('words: ' + s.word_list())
    w0 = next((w for w in s.words if w['start'] >= .3), None)
    if DROP is None and not w0:
        V.die('no word starts after 0.3 s in this slot: start the slot earlier')
    t_d = w0['start'] if DROP is None else when(s, DROP, 'DROP')
    fd = max(2, round(t_d * V.FPS))
    n = s.frames
    if LIFT is None:
        fl = None
    elif LIFT == 'auto':
        fl = n - 14
    else:
        fl = round(when(s, LIFT, 'LIFT') * V.FPS)
    if fl is not None and (fl < fd + MOVE + 8 or fl + MOVE > n - 1):
        V.die(f'the curtain falls at frame {fd} and rises at frame {fl} of {n}: it needs {MOVE} frames to fall, a hold, and {MOVE} to rise inside the slot')
    if fl is None and fd + MOVE >= n:
        V.die('the slot ends before the curtain has landed: end it later')

    G.bake('assets/aroll.mp4', 'assets/graded.mp4', LOOK, G.input_gain(LOOK, G.clip_level('assets/aroll.mp4')),
           grain=GRAIN, vignette=VIGNETTE or None)
    p = V.Page(s)
    p.css.append(f'''
#dark{{position:absolute;inset:0;overflow:hidden}}
#edge{{position:absolute;left:0;right:0;top:-2px;height:4px;background:{STYLE['edge']};opacity:.9}}''')
    p.html.append(f'<div id="dark"><video id="gv" class="full" src="assets/graded.mp4" muted playsinline data-start="0" '
                  f'data-media-start="0" data-duration="{s.dur:.4f}" data-track-index="1"></video></div><div id="edge"></div>')
    p.js.append("gsap.set('#dark',{clipPath:'inset(0px 0px 1920px 0px)'});gsap.set('#edge',{autoAlpha:0});")

    def place(f, y):
        t = V.T(f / V.FPS)
        return (f"tl.set('#dark',{{clipPath:'inset(0px 0px {1920 - y:.1f}px 0px)'}},{t:.3f});"
                f"tl.set('#edge',{{y:{y:.1f}}},{t:.3f});")

    p.js.append(f"tl.set('#edge',{{autoAlpha:1}},{V.T((fd + 1) / V.FPS):.3f});")
    for k in range(1, MOVE + 1):
        p.js.append(place(fd + k, 1920 * (1 - (1 - k / MOVE) ** POWER)))
    p.js.append(f"tl.set('#edge',{{autoAlpha:0}},{V.T((fd + MOVE) / V.FPS):.3f});")
    p.sound('whoosh-short', (fd - 4) / V.FPS + .12, .30 * SFX_GAIN)
    if fl is not None:
        p.js.append(f"tl.set('#edge',{{autoAlpha:1}},{V.T((fl + 1) / V.FPS):.3f});")
        for k in range(1, MOVE + 1):
            p.js.append(place(fl + k, 1920 * (1 - k / MOVE) ** POWER))
        p.js.append(f"tl.set('#edge',{{autoAlpha:0}},{V.T((fl + MOVE) / V.FPS):.3f});")
        p.sound('whoosh-short', (fl - 2) / V.FPS + .12, .18 * SFX_GAIN)
    p.write()
    print(f'  falls from {fd / V.FPS:.2f}s, dark at {(fd + MOVE) / V.FPS:.2f}s, ' + (f'rises from {fl / V.FPS:.2f}s' if fl else 'stays dark to the end'))
    print(f'snapshot at: {(fd + 2) / V.FPS:.2f},{(fd + 4) / V.FPS:.2f},{(fd + 7) / V.FPS:.2f},{(fd + 14) / V.FPS:.2f}' + (f',{(fl + 2) / V.FPS:.2f},{(fl + 5) / V.FPS:.2f}' if fl else ''))


if __name__ == '__main__':
    main()
