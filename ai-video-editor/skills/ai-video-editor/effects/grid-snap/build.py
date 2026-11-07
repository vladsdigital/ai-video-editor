#!/usr/bin/env python3
"""GRID SNAP (proof): on a solid forest green backdrop the speaker shrinks into the middle of a 3x3 grid, eight of the
buyer's own videos pop in around them, all playing, then the grid clears and the speaker snaps back full frame.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html   (SAFE=1 safe-zone guide, SFX=0 no sounds, CAPTIONS=0 no caption line)
"""
import random

import clipfx as X
import vgfx as V
from clipfx import F

# ==== STYLE (the reel's look wins: match the cap_ lines to the reel's caption style before building) ====
STYLE = dict(
    backdrop='#143026',            # solid colour behind the grid (deep forest green)
    tile_w=340, tile_h=606,        # one tile, px. The middle one is the speaker's whole frame at this size
    gap=14,                        # px between tiles
    radius=2,                      # corner of a tile, px
    cap_font='Instrument Serif',   # the caption line (only drawn with CAPTIONS on: no reel captions)
    cap_weight=400,
    cap_size=66,
    cap_y=1356,                    # centre of the caption line, px
    cap_case='as-said',
    cap_ink='#F3EFE2',             # a word once it is said
    cap_wait='#86A98F',            # a word still to come
    cap_plate='#143026',           # plate behind the line
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
CLIPS = 'clips'     # folder (inside the slot, or a full path) with the buyer's own videos, at least 8, each 1.7 s or
                    # longer. File-name order fills the grid: top middle, left, right, bottom middle, then the corners
SKIP = 1.0          # seconds skipped at the start of each video (the first second is often dead air)
WORD = ''           # the word the shrink starts on (a word the speaker says in this slot). '' = use T_IN
T_IN = None         # the shrink starts here, slot seconds. None = 0.3 s into the slot (when WORD is empty)
HOLD = 1.2          # seconds from the start of the shrink to the start of the way back (1.2 is the snappy one)
# ==== END CLIP ====

# Motion, frame by frame from the first shrink frame (30 fps)
SHRINK = [.935, .77, .52, .39, .33, .318, .315]             # size of the speaker on the way in, as part of the full frame
BACK = [.33, .37, .47, .78, .98, 1]                         # and on the way back
POP = [.12, .45, .82, .97, 1.012, 1]                        # size of a tile as it arrives
# (row, column) in arrival order and the frame each one starts, counted from the first shrink frame
ORDER = [(0, 1, 1), (1, 0, 2), (1, 2, 3), (2, 1, 4), (0, 0, 6), (0, 2, 6), (2, 2, 7), (2, 0, 8)]
LEAVE = [.965, .84, .66, .5, .36]                           # size of a tile on the way out


def main():
    s = V.Slot()
    print('words: ' + s.word_list())
    st = STYLE
    t_in = T_IN
    if WORD:
        w = s.find('^' + V.re.escape(V.bare(WORD)) + '$')
        if not w:
            V.die(f'WORD "{WORD}" is not said in this slot. Words: {s.word_list()}')
        t_in = w['start']
    t_in = .3 if t_in is None else t_in
    f_in = round(t_in * V.FPS)
    f_back = f_in + round(HOLD * V.FPS)
    f_end = f_back + len(BACK)
    if f_end > s.frames - 2:
        V.die(f'the slot is too short: the grid needs up to frame {f_end + 2} and the slot has {s.frames}. Make the slot longer or start earlier')
    if f_in < 1:
        V.die('T_IN is on the first frame: start the shrink at least one frame into the slot, so the slot opens on the plain picture')
    secs = (f_end - f_in) / V.FPS + .2
    clips = X.videos(CLIPS, 8, secs, SKIP, 'videos (their reels or clips)')

    p = X.Comp(s, st)
    tw, th, gap = st['tile_w'], st['tile_h'], st['gap']
    p.css.append(f'''
#green{{position:absolute;inset:0;background:{st["backdrop"]}}}
.gt{{position:absolute;width:{tw}px;height:{th}px;overflow:hidden;border-radius:{st["radius"]}px;opacity:0;z-index:30;will-change:transform}}
''')
    p.backdrop.append('<div id="green"></div>')
    rng = random.Random(7)
    t0 = F(f_in)
    for k, (r, c, delay) in enumerate(ORDER):
        path, start = clips[k]
        x = 540 + (c - 1) * (tw + gap) - tw / 2
        y = 960 + (r - 1) * (th + gap) - th / 2
        src = X.tile(path, start, secs, tw * 1.5, th * 1.5, f't{k}')
        vid = p.video(src, t0, secs)
        i = f'g{k}'
        p.top.append(f'<div id="{i}" class="gt" style="left:{x:.0f}px;top:{y:.0f}px">{vid}</div>')
        # each tile grows from its own place, starting a little nearer the middle, with a small tilt that settles
        dx, dy = (540 - (x + tw / 2)) * .1, (960 - (y + th / 2)) * .1
        rot = rng.choice((-1, 1)) * rng.uniform(1.2, 2.4)
        n = len(POP)
        rows = [dict(scale=POP[j], x=dx * (1 - j / (n - 1)), y=dy * (1 - j / (n - 1)), rotation=rot * (1 - j / (n - 1))) for j in range(n)]
        p.set(f'#{i}', t0 + F(delay), opacity=1)
        p.table(f'#{i}', t0 + F(delay), rows)
        # out: every tile shrinks on its place as the speaker grows over them
        p.table(f'#{i}', F(f_back), [dict(scale=v) for v in LEAVE])
        p.set(f'#{i}', F(f_back + len(LEAVE)), opacity=0)
    # the speaker: above the tiles once they are out, and back to full frame on top of everything
    p.css.append('#sw{z-index:35 !important}\n#lay-top{z-index:auto !important}\n#lay-under,#lay-over{display:none}\n')
    p.table('#sw', F(f_in), [dict(scale=v) for v in SHRINK])
    p.table('#sw', F(f_back), [dict(scale=v) for v in BACK])

    p.sound('whoosh-short', F(f_in + 1), .32)
    for r, c, delay in ORDER[:4]:
        p.sound('click-soft', F(f_in + delay + 1), .12)
    p.sound('whoosh-short', F(f_back + 2), .28)
    if V.env('CAPTIONS', '1') != '0':
        p.captions(0, s.dur)
    p.write()
    print(f'shrink at {F(f_in):.2f}s, grid full at {F(f_in + 14):.2f}s, way back at {F(f_back):.2f}s, full frame at {F(f_end):.2f}s')
    print(f'snapshot at: {F(f_in + 2):.2f},{F(f_in + 4):.2f},{F(f_in + 7):.2f},{F(f_in + 16):.2f},{F(f_back + 3):.2f},{F(f_end + 3):.2f}')


if __name__ == '__main__':
    main()
