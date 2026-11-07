#!/usr/bin/env python3
"""SPLIT GRADE (reveal): a tilted white divider snaps in from the right with a small overshoot, settles across the
speaker's face with a handle on it and two small tags, then sweeps off to the left on the word, leaving the whole shot
in the new grade. The same frames on both sides of the line.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html   (SAFE=1 safe-zone guide, SFX=0 no sounds)
"""
import math
import os

os.environ.setdefault('PREVIEW', '1')    # a full picture effect: the footage is always in the page
import grade as G
import vgfx as V

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    font='Inter Tight', weight=700, tracking=-0.035, big_weight=800, big_tracking=-0.055, case='as-said',
    small_font='JetBrains Mono',   # the two tags
    small_weight=500,
    serif_font='Newsreader', serif_italic=True,
    ink='#F3EEE3',                 # cream: tag text, and the line stays white
    accent=None,
    card='#16291F',                # forest green: the tag on the plain side
    shadow=False,
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
COMMIT = None        # the word the line sweeps on (a word from words.json) or seconds. None = the first word after 1.0 s
LOOK = 'warm'        # the new grade: 'warm', 'mood' or 'film' (grade.py)
LABELS = ('PRE', 'POSLE')   # the two tags, the plain side first. None = no tags
SPLIT_AT = .22       # where the line crosses the head while it waits: 0 = the centre, .5 = the right edge of the head
TILT = 8.0           # degrees from upright, the top leaning right
HANDLE_Y = None      # screen y of the handle. None = under the reel's caption line
TAG_Y = 285          # centre of the tags, screen px
OUT = 'auto'         # 'auto' = the grade eases off in the last 0.5 s. None = holds to the end (the slot ends on a cut)
SFX_GAIN = 1.0
# ==== END CLIP ====

SLOPE = math.tan(math.radians(TILT))
# The line, frame by frame, counted from the sweep frame. Entry: share of the way from the waiting place out to the right
# edge. Sweep: share of the way from the waiting place to the left edge.
ENTRY = {-12: 1.30, -11: .684, -10: .125, -9: -.103, -8: -.125, -7: -.051, -6: 0, -5: 0, -4: -.007, -3: -.015, -2: -.022, -1: -.029}
SWEEP = {0: .03, 1: .116, 2: .353, 3: .737, 4: .969, 5: 1.08}
TAG_IN = -7         # frames before the sweep the tags start to fade in (2 frames)
TAG_OUT_AFTER = 7   # frames after the sweep the far tag starts to fade out (2 frames)


def main():
    s = V.Slot()
    s.dur = int(s.frames / V.FPS * 1e4) / 1e4   # cut, not rounded: a duration rounded up renders one frame too many
    print('words: ' + s.word_list())
    print(s.where())
    if isinstance(COMMIT, (int, float)):
        t_c = float(COMMIT)
    elif COMMIT:
        w = s.find('^' + V.re.escape(COMMIT) + '$')
        if not w:
            V.die(f'the word "{COMMIT}" is not in this slot: pick a word from the list above')
        t_c = w['start']
    else:
        w = next((w for w in s.words if w['start'] >= 1.0), None)
        if not w:
            V.die('no word starts after 1.0 s in this slot: start the slot earlier')
        t_c = w['start']
    fc = round(t_c * V.FPS)
    if fc < 13:
        V.die(f'the sweep word is {fc} frames into the slot: the line needs 13 frames before it. Start the slot earlier')
    n = s.frames
    if fc + 6 >= n:
        V.die('the slot ends before the sweep is over: end it later')

    head = (s.layout or {}).get('head') or {}
    hw = int(head.get('width') or 350)
    head_mid = (s.head_top + s.chin) / 2
    x_mid = s.cx + SPLIT_AT * hw                 # where the line crosses the middle of the head while it waits
    top_rest = x_mid + head_mid * SLOPE          # x of the line at the top of the frame while it waits
    if top_rest > 1040 or top_rest - 1920 * SLOPE < 20:
        print('  !! the head sits so far to one side that the line leaves the frame while it waits: lower SPLIT_AT or TILT')
    hy = HANDLE_Y if HANDLE_Y is not None else min(V.SAFE_BOTTOM - 50, max(1245, s.chest + 170))
    t_out = None if OUT is None else max(fc + 8, n - 15) / V.FPS

    level = G.clip_level('assets/aroll.mp4')
    gain = G.input_gain(LOOK, level)
    G.bake('assets/aroll.mp4', 'assets/graded.mp4', LOOK, gain)
    print(f'  look {LOOK}: clip level {level:.0f}, lift {gain:.2f}')

    p = V.Page(s)
    ink, card = STYLE['ink'], STYLE['card']
    p.css.append(V.style_css(STYLE) + f'''
#after{{position:absolute;inset:0;overflow:hidden}}
#line{{position:absolute;left:-2px;top:-60px;width:4px;height:2040px;background:#fff;box-shadow:0 0 6px rgba(255,255,255,.35)}}
#hand{{position:absolute;left:-36px;width:72px;height:72px;top:{hy - 36}px;border-radius:50%;background:#fff;box-shadow:0 2px 10px rgba(0,0,0,.28)}}
#hand svg{{position:absolute;inset:0}}
.tag{{position:absolute;top:{TAG_Y - 25}px;height:50px;padding:0 20px;display:flex;align-items:center;border-radius:6px;
  font-size:24px;letter-spacing:.2em;color:{ink}}}
#tagA{{left:66px;background:{card}E6}}
#tagB{{right:54px;background:rgba(52,44,38,.62)}}''')
    vid = (f'<video id="gv" class="full" src="assets/graded.mp4" muted playsinline data-start="0" data-media-start="0" '
           f'data-duration="{s.dur:.4f}" data-track-index="1"></video>')
    p.html.append(f'<div id="after"><div id="afade" style="position:absolute;inset:0">{vid}</div></div>')
    p.html.append('<div id="line"></div>')
    p.html.append('<div id="hand"><svg viewBox="0 0 72 72"><path d="M31 25 L20 36 L31 47 M41 25 L52 36 L41 47" fill="none" '
                  'stroke="#16291F" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>')
    if LABELS:
        p.html.append(f'<div id="tagA" class="tag vg-small" style="line-height:1">{V.esc(LABELS[0])}</div>')
        p.html.append(f'<div id="tagB" class="tag vg-small" style="line-height:1">{V.esc(LABELS[1])}</div>')

    def top_x(f):
        k = f - fc
        if k < -12:
            return 1500.0
        if k in ENTRY:
            return top_rest + ENTRY[k] * (1080 + 60 - top_rest)
        if k in SWEEP:
            return top_rest + SWEEP[k] * (-60 - top_rest)
        return -400.0

    def poly(x):
        return f'polygon({x:.1f}px 0px,1200px 0px,1200px 1920px,{x - 1920 * SLOPE:.1f}px 1920px)'

    p.js.append(f"gsap.set('#line',{{rotation:{TILT},autoAlpha:0}});gsap.set('#hand',{{autoAlpha:0}});")
    p.js.append(f"gsap.set('#after',{{clipPath:'{poly(1500)}'}});")
    gone = fc + max(SWEEP) + 1
    for f in range(max(0, fc - 12), gone + 1):
        x = top_x(f)
        t = V.T(f / V.FPS)
        p.js.append(f"tl.set('#after',{{clipPath:'{poly(x)}'}},{t:.3f});"
                    f"tl.set('#line',{{x:{x - 960 * SLOPE:.1f}}},{t:.3f});"
                    f"tl.set('#hand',{{x:{x - hy * SLOPE:.1f}}},{t:.3f});")
    p.js.append(f"tl.set('#line,#hand',{{autoAlpha:1}},{V.T((fc - 11) / V.FPS):.3f});"
                f"tl.set('#line,#hand',{{autoAlpha:0}},{V.T(gone / V.FPS):.3f});")
    p.js.append(f"tl.set('#after',{{clipPath:'none'}},{V.T(gone / V.FPS):.3f});")
    if LABELS:
        t_in = V.T((fc + TAG_IN) / V.FPS)
        p.js.append(f"gsap.set('#tagA,#tagB',{{autoAlpha:0}});tl.to('#tagA,#tagB',{{autoAlpha:1,duration:.067,ease:'none'}},{t_in:.3f});")
        # the plain side's tag goes the moment the line reaches it
        fa = next((f for f in range(fc, gone + 1) if top_x(f) - TAG_Y * SLOPE < 66 + 150), gone)
        p.js.append(f"tl.set('#tagA',{{autoAlpha:0}},{V.T(fa / V.FPS):.3f});")
        p.js.append(f"tl.to('#tagB',{{autoAlpha:0,duration:.067,ease:'none'}},{V.T((fc + TAG_OUT_AFTER) / V.FPS):.3f});")
    if t_out is not None:
        p.js.append(f"tl.to('#afade',{{autoAlpha:0,duration:{s.dur - t_out - 1 / V.FPS:.3f},ease:'power1.inOut'}},{t_out:.3f});")
    p.sound('click-soft', (fc - 8) / V.FPS, .30 * SFX_GAIN)
    p.sound('whoosh-short', fc / V.FPS + .04, .20 * SFX_GAIN)
    p.write()
    print(f'  line in at {(fc - 11) / V.FPS:.2f}s, waits with its top at x {top_rest:.0f}, sweeps at {t_c:.2f}s, handle y {hy}, '
          + ('holds to the end' if t_out is None else f'grade off from {t_out:.2f}s'))
    print(f'snapshot at: {(fc - 10) / V.FPS:.2f},{(fc - 3) / V.FPS:.2f},{(fc + 2) / V.FPS:.2f},{(fc + 10) / V.FPS:.2f},{max(0, s.dur - .05):.2f}')


if __name__ == '__main__':
    main()
