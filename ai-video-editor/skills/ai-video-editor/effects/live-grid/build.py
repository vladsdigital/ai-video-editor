#!/usr/bin/env python3
"""LIVE GRID (proof): six of the buyer's own videos, all playing, drop from above the frame one after another and land
with real weight in a 3 x 2 grid behind the speaker. Then they lift back out, one after another.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html   (SAFE=1 safe-zone guide, SFX=0 no sounds, CAPTIONS=0 no caption line)
"""
import clipfx as X
import vgfx as V
from clipfx import F

# ==== STYLE (the reel's look wins: match the cap_ lines to the reel's caption style before building) ====
STYLE = dict(
    tile_w=294, tile_h=384,        # one tile, px (the videos are cropped to it, from the middle)
    gap=18,                        # px between tiles
    top=240,                       # top of the grid, px
    radius=14,
    edge='#F2ECDE',                # thin line around a tile (cream)
    edge_px=3,
    cap_font='Instrument Serif',   # the caption line (only drawn with CAPTIONS on: no reel captions)
    cap_weight=400,
    cap_size=66,
    cap_y=1356,
    cap_case='as-said',
    cap_ink='#F3EFE2',
    cap_wait='#86A98F',
    cap_plate='#1F3A2C',
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
CLIPS = 'clips'     # folder (inside the slot, or a full path) with the buyer's own videos, at least 6, each 2 s or
                    # longer. File-name order: the first one drops first
SKIP = 1.0          # seconds skipped at the start of each video
WORD = ''           # the word the first tile starts falling on (a word said in this slot). '' = use T_IN
T_IN = None         # slot seconds. None = 0.2 s into the slot (when WORD is empty)
HOLD = 1.43         # seconds from the first tile to the start of the lift out (the grid is full from about 1 s on)
# ==== END CLIP ====

COLS = 3
# row, column, first frame of the fall (from T_IN), tilt in degrees
DROP = [(0, 0, 0, -7), (1, 2, 5, 6), (0, 2, 10, 7), (1, 0, 14, -6), (1, 1, 17, 7), (0, 1, 21, -5)]
FALL_FRAMES = 7     # frames from above the frame to the landing: speeding up all the way, like a weight
BOUNCE = [15, 7, -3, -2, 0]    # px below its place after the landing, frame by frame (it hits, sinks in, comes to rest)
SETTLE = 7          # frames the tilt takes to die away after the landing
LIFT_FRAMES = 6     # frames from its place to out of the frame on the way out


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
    t_in = .2 if t_in is None else t_in
    f_in = round(t_in * V.FPS)
    f_out = f_in + round(HOLD * V.FPS)
    f_end = f_out + 3 + LIFT_FRAMES
    if f_end > s.frames - 1:
        V.die(f'the slot is too short: the grid needs up to frame {f_end + 1} and the slot has {s.frames}. Make the slot longer')
    if not V.os.path.exists('assets/subject.webm'):
        V.die('assets/subject.webm is missing: this effect needs the clean cutout (setup.py --matting, then make the slot again)')
    secs = F(f_end - f_in) + .2
    clips = X.videos(CLIPS, len(DROP), secs, SKIP, 'videos (their reels or clips)')

    p = X.Comp(s, st)
    p.cutout = True
    tw, th, gap = st['tile_w'], st['tile_h'], st['gap']
    left0 = (1080 - (COLS * tw + (COLS - 1) * gap)) / 2
    p.css.append(f'''
.lt{{position:absolute;width:{tw}px;height:{th}px;opacity:0;will-change:transform;transform-origin:50% 40%}}
.lt .pic{{position:absolute;inset:0;border-radius:{st["radius"]}px;overflow:hidden;background:#0B120F}}
.lt .edge{{position:absolute;inset:0;border-radius:{st["radius"]}px;border:{st["edge_px"]}px solid {st["edge"]};box-shadow:0 10px 30px rgba(0,0,0,.38)}}''')
    t0 = F(f_in)
    for k, (r, c, delay, tilt) in enumerate(DROP):
        path, start = clips[k]
        x = left0 + c * (tw + gap)
        y = st['top'] + r * (th + gap)
        i = f'l{k}'
        src = X.tile(path, start, secs, tw * 2, th * 2, f't{k}')
        # all playing from the moment the first tile falls, so nothing starts on a still
        p.under.append(f'<div id="{i}" class="lt" style="left:{x:.0f}px;top:{y:.0f}px"><div class="pic">{p.video(src, t0, secs)}</div><div class="edge"></div></div>')
        above = -(y + th + 50)
        rows = []
        for j in range(FALL_FRAMES):
            q = (j + 1) / FALL_FRAMES
            rows.append(dict(y=above * (1 - q * q), rotation=tilt * (1 - .62 * q), opacity=1))
        for j in range(max(SETTLE, len(BOUNCE))):
            dy = BOUNCE[j] if j < len(BOUNCE) else 0
            rows.append(dict(y=dy, rotation=tilt * .38 * (1 - (j + 1) / SETTLE) * (-1 if j in (1, 2) else 1) if j + 1 < SETTLE else 0))
        at = t0 + F(delay)
        p.set(f'#{i}', at - F(1), y=above, rotation=tilt)
        p.table(f'#{i}', at, rows)
        p.sound('impact-bass-2', at + F(FALL_FRAMES), .1)
        p.sound('click-soft', at + F(FALL_FRAMES), .16)
        # out: the last one in leaves first, speeding up
        lift = F(f_out + round((len(DROP) - 1 - k) * .6))
        p.table(f'#{i}', lift, [dict(y=above * ((j + 1) / LIFT_FRAMES) ** 2.2, rotation=-tilt * .9 * (j + 1) / LIFT_FRAMES) for j in range(LIFT_FRAMES)])
        p.set(f'#{i}', lift + F(LIFT_FRAMES), opacity=0)
    p.sound('whoosh-short', F(f_out + 1), .24)
    if V.env('CAPTIONS', '1') != '0':
        p.captions(0, s.dur)
    p.write()
    print(f'first tile falls at {t0:.2f}s, lands at {t0 + F(FALL_FRAMES):.2f}s, last one lands at {t0 + F(21 + FALL_FRAMES):.2f}s, lift out at {F(f_out):.2f}s, gone at {F(f_end):.2f}s')
    print(f'snapshot at: {t0 + F(4):.2f},{t0 + F(13):.2f},{t0 + F(22):.2f},{t0 + F(36):.2f},{F(f_out + 3):.2f}')


if __name__ == '__main__':
    main()
