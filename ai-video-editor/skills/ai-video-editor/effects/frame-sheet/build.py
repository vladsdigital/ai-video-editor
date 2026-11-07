#!/usr/bin/env python3
"""FRAME SHEET (hook): the shot shrinks into cell 01 of a solid colour contact sheet, the numbered empty cells fill one
real frame of this clip at a time while the line above builds word by word, and the camera snaps into the last cell and
out as the live shot, full frame. About 1.3 to 1.6 s from the shrink to the snap.

Every thumbnail is the frame of the clip at the moment its cell fills. Nothing is pre-made, no logo, no interface.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html and assets/sheet/*.jpg
                          (SAFE=1 safe-zone guide, SFX=0 no sounds, CAPTIONS=0 no words above the grid)
"""
import os
import shutil
import subprocess

os.environ.setdefault('PREVIEW', '1')     # a full-frame effect: the footage is always part of the page
import vgfx as V  # noqa: E402

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    font='Instrument Serif',       # the words above the grid
    weight=400,
    tracking=-0.01,                # em
    case='upper',                  # 'as-said', 'lower' or 'upper'
    ink='#F4EFE2',                 # the words (cream)
    ground='#163127',              # the solid colour of the sheet (deep forest green). Any flat colour of the reel's look
    cell='#2A5A44',                # an empty cell
    number='#668375',              # the number in an empty cell
    mark='#E6DFC6',                # the thin line round the cell that just filled
    mono='JetBrains Mono',         # the cell numbers
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
LINES = None        # the words above the grid, split into lines: ['first line', 'second line']. The words must be said
                    # inside the sheet's window. None = the reel's own words of that window, split by themselves
T_IN = None         # when the shot starts to shrink into cell 01 (slot seconds). None = just after the first word from 0.4 s on
T_DIVE = None       # when the dive into the last cell starts. None = when the last word of the window ends, at most 0.9 s
                    # before the slot ends
SHRINK = .2         # the shot shrinking into cell 01, seconds
DIVE = .12          # the dive into the last cell, seconds. It is meant to be nearly a cut
COLS = 6            # cells across. COLS x ROWS = 30 reads as "one second of this video" at 30 frames a second
ROWS = 5
CURVE = .87         # how the filling runs: 1 = even, under 1 = a slow first few cells, then steady
LINE_SIZE = 112     # the largest size of the words, px. Long lines get smaller by themselves
# ==== END CLIP ====

GRID_X, GRID_Y = 51, 399       # the grid's top left. The bottom right cells reach under the app's buttons: pictures only
CELL_W, CELL_H = 158, 210
PITCH_X, PITCH_Y = 164, 213
LINE_MID = 302                 # middle of the line of words
LINE_MAX = 936                 # widest a line may be
FACE_AT = .44                  # where the face sits inside a cell, top to bottom
SAID_FROM = .4


def chunks(words):
    """the spoken words as lines of up to about 16 characters: a line this size holds no more"""
    out, cur = [], []
    for w in words:
        if cur and len(' '.join(x['text'] for x in cur + [w])) > 16:
            out.append(cur)
            cur = []
        cur.append(w)
        if w['text'][-1] in ',.;:!?' and len(cur) > 1:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def typed_lines(words):
    """LINES laid onto the spoken times: every typed word takes the time of the next spoken word that matches"""
    out, at = [], 0
    for line in LINES:
        row = []
        for tok in line.split():
            hit = next((j for j in range(at, len(words)) if V.bare(words[j]['text']).lower() == V.bare(tok).lower()), None)
            if hit is None:
                V.die(f'LINES has "{tok}" and the speaker does not say it inside the sheet\'s window: '
                      + ' '.join(w['text'] for w in words))
            row.append(dict(words[hit], text=tok))
            at = hit + 1
        out.append(row)
    return out


def grab(frames):
    """the frames of the clip, one small jpg each: they are real frames, nothing else goes in the cells"""
    shutil.rmtree('assets/sheet', ignore_errors=True)
    os.makedirs('assets/sheet')
    sel = '+'.join(f'eq(n\\,{f})' for f in sorted(set(frames)))
    subprocess.run([shutil.which('ffmpeg') or 'ffmpeg', '-v', 'error', '-y', '-i', 'assets/aroll.mp4', '-vf',
                    f"select='{sel}',scale=360:-2", '-fps_mode', 'vfr', '-q:v', '4', 'assets/sheet/t%03d.jpg'], check=True)
    have = len(os.listdir('assets/sheet'))
    if have != len(set(frames)):
        V.die(f'got {have} frames out of the clip, wanted {len(set(frames))}: make the slot again')
    order = {f: k + 1 for k, f in enumerate(sorted(set(frames)))}
    return {f: f'assets/sheet/t{order[f]:03d}.jpg' for f in frames}


def main():
    s = V.Slot()
    print('words: ' + s.word_list())
    print(s.where())
    n = COLS * ROWS
    words_on = V.env('CAPTIONS', '1') != '0'
    t_in = T_IN
    if t_in is None:
        w0 = next((w for w in s.words if w['start'] >= SAID_FROM), None)
        t_in = (w0['start'] + .05) if w0 else SAID_FROM
    t_in = max(.1, t_in)
    t_dive = T_DIVE
    if t_dive is None:
        said = [w for w in s.words if w['start'] >= t_in - .1 and w['end'] <= s.dur - .9]
        t_dive = said[-1]['end'] if said else s.dur - .9
    t_land = t_in + SHRINK
    t_end = t_dive + DIVE
    if t_end > s.dur - .1:
        V.die(f'the dive ends at {t_end:.2f} s and the slot at {s.dur:.2f} s: move T_DIVE earlier, the last frames must be the plain shot')
    if t_dive - t_land < .7:
        V.die(f'only {t_dive - t_land:.2f} s for {n} cells: the sheet needs 0.9 s or more, make the slot longer or set T_DIVE later')
    fill = [t_land + (t_dive - .03 - t_land) * (k / (n - 1)) ** CURVE for k in range(n)]
    frames = [min(s.frames - 1, round(t * V.FPS)) for t in fill]
    thumbs = grab(frames)

    p = V.Page(s)
    S = STYLE
    cw, ch = CELL_W, CELL_H
    box_h = cw * 16 / 9                    # the whole frame at cell width: a cell shows a slice of it, the dive opens it
    head = (s.head_top + s.chin) / 2
    full_crop = ch / box_h * 1920
    top_px = max(0.0, min(1920 - full_crop, head - FACE_AT * full_crop))
    ins_t, ins_b = top_px / 1920 * box_h, box_h - ch - top_px / 1920 * box_h
    clip_small = f'inset({ins_t:.2f}px 0px {ins_b:.2f}px 0px round 2px)'
    p.css.append(f"""
#sheet{{position:absolute;left:0;top:0;width:1080px;height:1920px;background:{S["ground"]};transform-origin:0 0;overflow:hidden}}
.c{{position:absolute;width:{cw}px;height:{ch}px;background:{S["cell"]};overflow:hidden;border-radius:2px}}
.c>b{{position:absolute;left:0;right:0;top:{ch / 2 - 18:.1f}px;text-align:center;font:500 30px/36px '{S["mono"]}';color:{S["number"]}}}
.c>.t{{position:absolute;inset:0}}
.c img{{position:absolute;left:0;top:{-ins_t:.2f}px;width:{cw}px;height:{box_h:.2f}px;display:block}}
.c>.t>i{{position:absolute;left:6px;top:{ch - 25}px;font:500 16px/20px '{S["mono"]}';font-style:normal;color:{S["ink"]}}}
.c>.t>u{{position:absolute;inset:0;border:3px solid {S["mark"]};border-radius:2px;display:block}}
#clast{{height:{box_h:.2f}px;overflow:visible;border-radius:0;clip-path:{clip_small}}}
#clast>b{{top:{ins_t + ch / 2 - 18:.1f}px}}
#clast img{{top:0}}
#clast>.t>i{{top:{ins_t + ch - 25:.1f}px}}
#clast>.t>u{{inset:auto;left:0;right:0;top:{ins_t:.1f}px;height:{ch}px}}
#live{{position:absolute;left:0;top:0;width:100%;height:100%;object-fit:cover}}
#fly{{position:absolute;left:0;top:0;width:1080px;height:1920px;transform-origin:0 0;z-index:60}}
#fly video{{position:absolute;left:0;top:0;width:1080px;height:1920px;object-fit:cover}}
#lines{{position:absolute;left:0;top:{LINE_MID - 82}px;width:1080px;height:164px;overflow:hidden;z-index:70}}
.ln{{position:absolute;left:0;width:1080px;top:0;height:164px;line-height:164px;text-align:center;white-space:nowrap;font-family:'{S["font"]}';font-weight:{S["weight"]};letter-spacing:{S["tracking"]}em;color:{S["ink"]}}}
.ln span{{display:inline-block;margin:0 .11em}}
#grid{{position:absolute;inset:0}}""")
    cells, frag = [], []
    for k in range(n):
        r, c = k // COLS, k % COLS
        x, y = GRID_X + c * PITCH_X, GRID_Y + r * PITCH_Y
        last = k == n - 1
        cells.append((x, y - ins_t))
        live = (f'<video id="live" src="assets/aroll.mp4" muted playsinline data-start="{t_dive:.4f}" data-media-start="{t_dive:.4f}" '
                f'data-duration="{DIVE + .04:.4f}" data-track-index="3"></video>') if k == n - 1 else ''
        frag.append(f'<div class="c" id="{"clast" if last else f"c{k}"}" style="left:{x}px;top:{y - ins_t if last else y:.2f}px;z-index:{k + 2}"><b>{k + 1:02d}</b>'
                    f'<div class="t" id="t{k}"><img src="{thumbs[frames[k]]}" alt=""><i>{k + 1:02d}</i><u id="u{k}"></u>{live}</div></div>')
    # the line of words: every word has its place in the finished line and rises into it when it is said
    lines_html = []
    if words_on:
        said = [w for w in s.words if t_in - .15 <= w['start'] < t_dive]
        rows = typed_lines(said) if LINES else chunks(said)
        rows = [[dict(w, text=V.cased(w['text'], S['case'])) for w in row] for row in rows]
        for j, row in enumerate(rows):
            text = ' '.join(w['text'] for w in row)
            upper = text.upper() == text
            size = min(LINE_SIZE, int(LINE_MAX / max(1, len(text) * (.5 if upper else .42))))
            spans = ''.join(f'<span id="l{j}w{m}">{V.esc(w["text"])}</span>' for m, w in enumerate(row))
            lines_html.append(f'<div class="ln" id="l{j}" style="font-size:{size}px">{spans}</div>')
            for m, w in enumerate(row):
                p.hidden.append(f'#l{j}w{m}')
                p.js.append(f"tl.fromTo('#l{j}w{m}',{{autoAlpha:0,y:120}},{{autoAlpha:1,y:0,duration:.2,ease:'power3.out',immediateRender:false}},{V.T(w['start']):.3f});")
            if j + 1 < len(rows):
                p.js.append(f"tl.to('#l{j}',{{y:-150,duration:.14,ease:'power2.in'}},{V.T(rows[j + 1][0]['start'] - .12):.3f});")
        print('line: ' + ' / '.join(' '.join(w['text'] for w in row) for row in rows))
    # the shot shrinks into cell 01, the cells fill, the camera goes into the last one
    x0, y0 = cells[0]
    p.html = [f'<div id="sheet"><div id="grid">{"".join(frag)}</div>'
              f'<div id="fly"><video id="flyv" src="assets/aroll.mp4" muted playsinline data-start="{t_in:.4f}" data-media-start="{t_in:.4f}" '
              f'data-duration="{SHRINK + .04:.4f}" data-track-index="4"></video></div>'
              f'<div id="lines">{"".join(lines_html)}</div></div>']
    p.show('#sheet', t_in, t_end)
    p.hidden.append('#grid')
    p.js.append(f"tl.fromTo('#grid',{{autoAlpha:0}},{{autoAlpha:1,duration:.1,immediateRender:false}},{V.T(t_in + SHRINK * .4):.3f});")
    crop_b = 1920 - top_px - full_crop
    p.js.append(f"tl.fromTo('#fly',{{clipPath:'inset(0px 0px 0px 0px)'}},{{clipPath:'inset({top_px:.1f}px 0px {crop_b:.1f}px 0px)',x:{x0},y:{y0:.2f},scale:{cw / 1080:.5f},duration:{SHRINK},ease:'power2.inOut',immediateRender:false}},{V.T(t_in):.3f});")
    p.js.append(f"tl.set('#fly',{{autoAlpha:0}},{V.T(t_land + .01):.3f});")
    for k, t in enumerate(fill):
        p.hidden.append(f'#t{k}')
        at = V.T(t)
        p.js.append(f"tl.set('#t{k}',{{autoAlpha:1}},{at:.3f});")
        p.js.append(f"tl.set('#u{k}',{{autoAlpha:0}},{V.T(fill[k + 1] if k + 1 < n else t_dive):.3f});")
        if k % 2 == 0:
            p.sound('click-soft', t, .14)
    x, y = cells[-1]
    z = 1080 / cw
    p.js.append(f"tl.to('#clast',{{clipPath:'inset(0px 0px 0px 0px round 0px)',duration:{DIVE},ease:'power2.in'}},{V.T(t_dive):.3f});")
    p.js.append(f"tl.to('#sheet',{{x:{-x * z:.2f},y:{-y * z:.2f},scale:{z:.4f},duration:{DIVE},ease:'power2.in'}},{V.T(t_dive):.3f});")
    p.write()
    print(f'  shot shrinks at {t_in:.2f}s, in cell 01 at {t_land:.2f}s, {n} cells fill to {fill[-1]:.2f}s, dive {t_dive:.2f} to {t_end:.2f}s, plain shot after that')
    print(f'snapshot at: {t_in + SHRINK * .4:.2f},{t_land + .1:.2f},{(t_land + t_dive) / 2:.2f},{t_dive - .05:.2f},{t_dive + DIVE * .5:.2f},{min(s.dur - .03, t_end + .05):.2f}')
    s.hide_hint([(t_in, t_end)])


if __name__ == '__main__':
    main()
