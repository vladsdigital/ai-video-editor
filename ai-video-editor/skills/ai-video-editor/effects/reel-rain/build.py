#!/usr/bin/env python3
"""REEL RAIN (proof): the room dims and eight of the buyer's own videos tumble in out of the dark in 3D, blurred and dim
at first, and settle into a sharp 4 x 2 wall behind the speaker. Then they fall back into the dark and the room returns.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html   (SAFE=1 safe-zone guide, SFX=0 no sounds, CAPTIONS=0 no caption line)
"""
import clipfx as X
import vgfx as V
from clipfx import F

# ==== STYLE (the reel's look wins: match the cap_ lines to the reel's caption style before building) ====
STYLE = dict(
    tile_w=216, tile_h=387,        # one tile, px (9:16)
    gap_x=21, gap_y=18,            # px between tiles
    top=219,                       # top of the wall, px
    radius=14,
    edge='#F2ECDE',                # thin line around a tile (cream)
    edge_px=3,
    dim=.42,                       # how dark the room gets behind the speaker (0 = not at all)
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
CLIPS = 'clips'     # folder (inside the slot, or a full path) with the buyer's own videos, at least 8, each 2 s or
                    # longer. File-name order: the first ones arrive first
SKIP = 1.0          # seconds skipped at the start of each video
WORD = ''           # the word the first tile appears on (a word said in this slot). '' = use T_IN
T_IN = None         # slot seconds. None = 0.2 s into the slot (when WORD is empty)
HOLD = 1.53         # seconds from the first tile to the start of the way out (the wall is full from about 1.0 s on)
# ==== END CLIP ====

COLS, ROWS = 4, 2
# row, column, first frame (from T_IN), tilt: two by two, in two waves
ARRIVE = [(0, 1, 0, -8), (0, 2, 1, 7), (1, 0, 1, -10), (1, 3, 2, 9), (0, 0, 12, -8), (0, 3, 13, 9), (1, 1, 15, 10), (1, 2, 16, -9)]
FLY = [.12, .32, .58, .82, .93, .97, .99, 1]            # size of a tile, frame by frame, as it comes up out of the dark
RESOLVE = 12                                            # frames a tile takes to go from dim and blurred to sharp
FALL = [(.92, 1), (.72, 1), (.52, .9), (.34, .6), (.2, .2)]   # size and opacity, frame by frame, on the way out
FAR = (540, 520)                                        # where "far away" is on screen


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
    f_end = f_out + len(FALL) + 3
    if f_end > s.frames - 1:
        V.die(f'the slot is too short: the wall needs up to frame {f_end + 1} and the slot has {s.frames}. Make the slot longer')
    if not V.os.path.exists('assets/subject.webm'):
        V.die('assets/subject.webm is missing: this effect needs the clean cutout (setup.py --matting, then make the slot again)')
    secs = F(f_end - f_in) + .2
    clips = X.videos(CLIPS, 8, secs, SKIP, 'videos (their reels or clips)')

    p = X.Comp(s, st)
    p.cutout = True
    tw, th = st['tile_w'], st['tile_h']
    p.css.append(f'''
#dim{{position:absolute;inset:0;background:radial-gradient(120% 90% at 50% 45%,rgba(4,10,8,{st["dim"]}) 45%,rgba(4,10,8,{min(1, st["dim"] + .2)}) 100%);opacity:0}}
.rt{{position:absolute;width:{tw}px;height:{th}px;opacity:0;will-change:transform}}
.rt .pic{{position:absolute;inset:0;border-radius:{st["radius"]}px;overflow:hidden;background:#0B120F}}
.rt .pic>div{{position:absolute;inset:0}}
.rt .edge{{position:absolute;inset:0;border-radius:{st["radius"]}px;border:{st["edge_px"]}px solid {st["edge"]};box-shadow:0 8px 26px rgba(0,0,0,.34)}}''')
    p.under.append('<div id="dim"></div>')
    t0 = F(f_in)
    total_w = COLS * tw + (COLS - 1) * st['gap_x']
    left0 = (1080 - total_w) / 2
    n = len(FLY)
    for k, (r, c, delay, tilt) in enumerate(ARRIVE):
        path, start = clips[k]
        x = left0 + c * (tw + st['gap_x'])
        y = st['top'] + r * (th + st['gap_y'])
        i = f'r{k}'
        src = X.tile(path, start, secs, tw * 2, th * 2, f't{k}')
        p.under.append(f'<div id="{i}" class="rt" style="left:{x:.0f}px;top:{y:.0f}px"><div class="pic"><div id="{i}p">{p.video(src, t0, secs)}</div></div><div class="edge"></div></div>')
        cx, cy = x + tw / 2, y + th / 2
        side = 1 if c < COLS / 2 else -1
        rows = []
        for j, sc in enumerate(FLY):
            q = 1 - sc
            rows.append(dict(scale=sc, x=(FAR[0] - cx) * q * .9, y=(FAR[1] - cy) * q * .9, rotation=tilt * q * 1.6, rotationX=34 * q, rotationY=38 * side * q, transformPerspective=1100))
        at = t0 + F(delay)
        p.set(f'#{i}', at, opacity=1)
        p.table(f'#{i}', at, rows)
        # the picture comes up out of the dark more slowly than the tile itself flies in
        p.js.append(f"tl.fromTo('#{i}p',{{opacity:.16,filter:'blur(13px)'}},{{opacity:1,filter:'blur(0px)',duration:{F(RESOLVE):.3f},ease:'sine.inOut',immediateRender:false}},{V.T(at):.3f});")
        # out: the last in leave first
        back = (len(ARRIVE) - 1 - k) // 3
        bat = F(f_out + back)
        p.table(f'#{i}', bat, [dict(scale=sc, opacity=o, x=(FAR[0] - cx) * (1 - sc) * .9, y=(FAR[1] - cy) * (1 - sc) * .9, rotation=tilt * (1 - sc) * .8) for sc, o in FALL])
        p.set(f'#{i}', bat + F(len(FALL)), opacity=0)
    p.to('#dim', t0 - F(1), F(11), 'sine.inOut', opacity=1)
    p.to('#dim', F(f_out), F(5), 'sine.in', opacity=0)
    p.sound('whoosh-short', t0 + F(1), .26)
    p.sound('whoosh-short', t0 + F(13), .2)
    for r, c, delay, tilt in ARRIVE:
        p.sound('click-soft', t0 + F(delay + 5), .08)
    p.sound('whoosh-short', F(f_out + 1), .24)
    if V.env('CAPTIONS', '1') != '0':
        p.captions(0, s.dur)
    p.write()
    print(f'first tile at {t0:.2f}s, all eight sharp at {t0 + F(16 + RESOLVE):.2f}s, way out at {F(f_out):.2f}s, gone at {F(f_end):.2f}s')
    print(f'snapshot at: {t0 + F(4):.2f},{t0 + F(9):.2f},{t0 + F(18):.2f},{t0 + F(32):.2f},{F(f_out + 2):.2f}')


if __name__ == '__main__':
    main()
