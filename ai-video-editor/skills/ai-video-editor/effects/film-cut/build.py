#!/usr/bin/env python3
"""FILM CUT (mood): a hard vertical wipe runs across the frame in six frames, left to right, with a thin white edge, and
leaves the shot in a film look: deep blacks, teal shadows, warm highlights, some grain. It holds for one line, then the
picture cuts straight back.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html   (SAFE=1 safe-zone guide, SFX=0 no sounds)
"""
import os

os.environ.setdefault('PREVIEW', '1')    # a full picture effect: the footage is always in the page
import grade as G
import vgfx as V

# ==== STYLE (the reel's look wins; this effect draws no words) ====
STYLE = dict(edge='#FFFFFF')    # colour of the wipe's thin edge
# ==== END STYLE ====

# ==== CLIP (edit this) ====
ON = None           # the word the wipe runs on (a word from words.json) or seconds. None = the first word after 0.3 s
BACK = 'auto'       # when it cuts back: seconds, a word, 'auto' = 6 frames before the slot ends, None = holds to a cut
LOOK = 'film'       # 'film', 'mood' or 'warm' (grade.py)
GRAIN = 7           # moving grain in the look. 0 = none
SOUND = 0.0         # volume of a soft whoosh on the wipe. 0 = silent, the look is a clean cut
# ==== END CLIP ====

# share of the frame the wipe has covered, frame by frame
WIPE = (.056, .222, .5, .778, .944, 1.02)


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
    if ON is None and not w0:
        V.die('no word starts after 0.3 s in this slot: start the slot earlier')
    t_on = w0['start'] if ON is None else when(s, ON, 'ON')
    fw = max(2, round(t_on * V.FPS))
    n = s.frames
    fb = None if BACK is None else (n - 6 if BACK == 'auto' else round(when(s, BACK, 'BACK') * V.FPS))
    if fb is not None and fb < fw + len(WIPE) + 12:
        V.die(f'the wipe runs at frame {fw} and the look ends at frame {fb}: it needs at least 18 frames to be seen. Pick an earlier word or end the slot later')
    if fw + len(WIPE) >= n:
        V.die('the slot ends before the wipe is over: end it later')

    G.bake('assets/aroll.mp4', 'assets/graded.mp4', LOOK, G.input_gain(LOOK, G.clip_level('assets/aroll.mp4')), grain=GRAIN)
    p = V.Page(s)
    p.css.append(f'''
#film{{position:absolute;inset:0;overflow:hidden}}
#edge{{position:absolute;top:0;bottom:0;left:-1px;width:3px;background:{STYLE['edge']};box-shadow:0 0 4px rgba(255,255,255,.3)}}''')
    p.html.append(f'<div id="film"><video id="gv" class="full" src="assets/graded.mp4" muted playsinline data-start="0" '
                  f'data-media-start="0" data-duration="{s.dur:.4f}" data-track-index="1"></video></div><div id="edge"></div>')
    p.js.append("gsap.set('#film',{clipPath:'inset(0px 1080px 0px 0px)'});gsap.set('#edge',{autoAlpha:0});")
    p.js.append(f"tl.set('#edge',{{autoAlpha:1}},{V.T(fw / V.FPS):.3f});")
    for k, u in enumerate(WIPE):
        x = 1080 * u
        t = V.T((fw + k) / V.FPS)
        p.js.append(f"tl.set('#film',{{clipPath:'inset(0px {max(0, 1080 - x):.1f}px 0px 0px)'}},{t:.3f});tl.set('#edge',{{x:{x:.1f}}},{t:.3f});")
    p.js.append(f"tl.set('#edge',{{autoAlpha:0}},{V.T((fw + len(WIPE) - 1) / V.FPS):.3f});")
    if fb is not None:
        p.js.append(f"tl.set('#film',{{autoAlpha:0}},{V.T(fb / V.FPS):.3f});")
    if SOUND:
        p.sound('whoosh-short', fw / V.FPS, SOUND)
    p.write()
    print(f'  wipe {fw / V.FPS:.2f}s to {(fw + len(WIPE)) / V.FPS:.2f}s, ' + (f'cuts back at {fb / V.FPS:.2f}s' if fb else 'holds to the end'))
    last = (fb - 1) if fb else n - 1
    print(f'snapshot at: {(fw + 1) / V.FPS:.2f},{(fw + 2) / V.FPS:.2f},{(fw + 4) / V.FPS:.2f},{(fw + 14) / V.FPS:.2f},{last / V.FPS:.2f},{(n - 1) / V.FPS:.2f}')


if __name__ == '__main__':
    main()
