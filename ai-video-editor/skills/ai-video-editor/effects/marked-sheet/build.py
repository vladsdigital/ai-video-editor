#!/usr/bin/env python3
"""MARKED SHEET (explain): a cream paper sheet with two film strips of real frames from this reel drops in from the top,
tilted, and settles above the speaker. The frames develop from black one after the other, then a red pencil circles and
crosses some of them and writes a short word above them. The sheet flies back off the top.

The shot slides down while the sheet is up, just enough that the sheet stays off the face.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html and assets/strip/*.jpg   (SAFE=1 safe-zone guide, SFX=0 no sounds)
"""
import json
import os
import shutil
import subprocess

os.environ.setdefault('PREVIEW', '1')     # the shot moves: the footage is part of the page
import vgfx as V  # noqa: E402

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    paper='#F4EFE2',               # the sheet (cream)
    film='#121212',                # the film strips
    hole='#EDE8DA',                # the sprocket holes
    hand='#C4525F',                # the pencil: circles, crosses and the handwritten words
    hand_font='Instrument Serif',  # the handwritten words
    hand_italic=True,
    hand_size=64,
    tc='#B05A55',                  # the time under each frame
    foot='#6B675D',                # the line at the foot of the sheet
    mono='JetBrains Mono',         # the times and the foot line
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
MARKS = [           # the pencil, in order. cell = frame number, 0 to 11, left to right, top strip first. kind = 'circle' or
                    # 'cross'. word = what is written above it, in the top strip only ('' = no word). t = slot seconds,
                    # None = spread evenly from T_MARKS on. Use the speaker's own words
    (2, 'circle', '', None),
    (4, 'cross', '', None),
    (6, 'cross', '', None),
    (8, 'cross', '', None),
    (11, 'circle', '', None),
]
TAG = ''            # a word or two in the foot line before the clip's length ('first take'). '' = none
FILE_NAME = None    # the file name in the foot line. None = the real name of the raw clip this slot comes from
T_IN = None         # the sheet starts to drop. None = 0.05 s before the first word from 0.1 s on
T_DEVELOP = None    # the first frame starts to develop. None = 0.55 s after T_IN
T_MARKS = None      # the first pencil mark. None = 0.45 s after the frames are developed
T_OUT = None        # the sheet starts to fly off. None = 0.3 s before the slot ends
DROP = .3           # how long the drop takes, seconds
# ==== END CLIP ====

PAPER_X, PAPER_W, PAPER_Y = 69, 942, 222
HEAD_ROOM = 72                 # paper above the first strip: the words go here
FRAME_W, FRAME_H = 146, 168
BAND = 16                      # the sprocket band above and below the frames
TC_H = 32                      # the line of times under a strip
FOOT_H = 36
PAPER_H = HEAD_ROOM + 2 * (2 * BAND + FRAME_H + TC_H) + FOOT_H
OVER_HAIR = 22                 # how far the paper may lie on the top of the head
CHIN_MAX = 1500                # lowest the chin may go when the shot slides
CAP_GAP = 12


def run(*a):
    return subprocess.run(a, capture_output=True, text=True)


def stamp(sec):
    sec = max(0, sec)
    return f'{int(sec // 60):02d}:{int(sec % 60):02d}:{int((sec % 1) * 30):02d}'


def clock(sec):
    return f'{int(sec // 60)}:{int(round(sec % 60)):02d}'


def raw_file(s):
    """the raw clip this slot was cut from, when the reel knows it: (path or None)"""
    proj = s.clip.get('project')
    if not proj:
        return None
    try:
        segs = json.load(open(os.path.join(proj, 'segments.json'), encoding='utf-8'))
        src = json.load(open(os.path.join(proj, 'sources.json'), encoding='utf-8'))
    except (OSError, ValueError):
        return None
    f0 = s.t0 * V.FPS
    seg = next((g for g in segs if g['frame'] <= f0 + 1 < g['frame'] + g['frames']), None)
    return src.get(seg['clip']) if seg else None


def strip_frames(s):
    """12 real frames spread over the reel (over the slot on a loose clip), and their reel times"""
    src = s.clip.get('src') if s.clip.get('project') and os.path.isfile(s.clip.get('src') or '') else 'assets/aroll.mp4'
    out = run(shutil.which('ffprobe') or 'ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src).stdout
    try:
        dur = float(out.strip())
    except ValueError:
        V.die(f'could not read the length of {src}')
    times = [(k + .5) / 12 * dur for k in range(12)]
    shutil.rmtree('assets/strip', ignore_errors=True)
    os.makedirs('assets/strip')
    for k, t in enumerate(times):
        run(shutil.which('ffmpeg') or 'ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.3f}', '-i', src, '-frames:v', '1', '-vf', 'scale=320:-2',
            '-q:v', '4', f'assets/strip/f{k:02d}.jpg')
        if not os.path.isfile(f'assets/strip/f{k:02d}.jpg'):
            V.die(f'could not pull a frame at {t:.2f} s from {src}')
    start = 0.0 if src != 'assets/aroll.mp4' else s.t0
    return [start + t for t in times]


def foot_line(s):
    raw = raw_file(s)
    src = raw if raw and os.path.isfile(raw) else 'assets/aroll.mp4'
    name = FILE_NAME or os.path.basename(raw or s.clip.get('src') or src)
    bits = [TAG] if TAG else []
    out = run(shutil.which('ffprobe') or 'ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src).stdout.strip()
    if out:
        bits.append(clock(float(out)))
    bits.append(f'{os.path.getsize(src) / 1048576:.1f} MB')
    return name, ' · '.join(bits)


def loop_path(cx, cy, rx, ry):
    """a pencil loop drawn by hand: it goes round once and runs a little past its own start"""
    return (f'M{cx - rx * .35:.1f},{cy - ry * .96:.1f} C{cx + rx * .6:.1f},{cy - ry * 1.12:.1f} {cx + rx * 1.06:.1f},{cy - ry * .45:.1f} '
            f'{cx + rx:.1f},{cy + ry * .1:.1f} C{cx + rx * .95:.1f},{cy + ry * .72:.1f} {cx + rx * .4:.1f},{cy + ry * 1.04:.1f} '
            f'{cx - rx * .12:.1f},{cy + ry:.1f} C{cx - rx * .72:.1f},{cy + ry * .95:.1f} {cx - rx * 1.04:.1f},{cy + ry * .35:.1f} '
            f'{cx - rx:.1f},{cy - ry * .2:.1f} C{cx - rx * .97:.1f},{cy - ry * .78:.1f} {cx - rx * .45:.1f},{cy - ry * 1.04:.1f} '
            f'{cx + rx * .3:.1f},{cy - ry * .98:.1f}')


def main():
    s = V.Slot()
    print('words: ' + s.word_list())
    print(s.where())
    S = STYLE
    t_in = T_IN
    if t_in is None:
        w0 = next((w for w in s.words if w['start'] >= .1), None)
        t_in = max(.1, w0['start'] - .05) if w0 else .15
    t_land = t_in + DROP
    t_dev = T_DEVELOP if T_DEVELOP is not None else t_in + .55
    stag, each = .036, .24
    t_dev_end = t_dev + 11 * stag + each
    t_out = T_OUT if T_OUT is not None else s.dur - .3
    t_gone = t_out + .2
    t_marks = T_MARKS if T_MARKS is not None else t_dev_end + .45
    if t_gone > s.dur - .03:
        V.die(f'the sheet is gone at {t_gone:.2f} s and the slot ends at {s.dur:.2f} s: set T_OUT earlier, the last frame must be the plain shot')
    if t_marks > t_out - .3:
        V.die(f'the slot is too short: the pencil starts at {t_marks:.2f} s and the sheet leaves at {t_out:.2f} s. It needs about 2.7 s or more')
    for m in MARKS:
        if not 0 <= m[0] <= 11 or m[1] not in ('circle', 'cross'):
            V.die(f'MARKS row {m}: cell is 0 to 11 and kind is circle or cross')
    free = [k for k, m in enumerate(MARKS) if m[3] is None]
    mark_t = {}
    for j, k in enumerate(free):
        mark_t[k] = t_marks + (t_out - .22 - t_marks) * j / max(1, len(free) - 1)
    # the shot slides down until the head is under the sheet
    bottom = PAPER_Y + PAPER_H
    slide = max(0, bottom - OVER_HAIR - s.head_top)
    if s.chin + slide > CHIN_MAX:
        V.die(f'the chin would land at y {s.chin + slide} under the sheet: this framing is too tight for it (a medium or wide shot fits)')
    cap_y = int(s.chin + slide + CAP_GAP)
    times = strip_frames(s)
    fname, fright = foot_line(s)
    print(f'  foot line: {fname}  |  {fright}')

    p = V.Page(s)
    ital = 'italic' if S['hand_italic'] else 'normal'
    fy = max(0.0, min(100.0, ((s.head_top + s.chin) / 2 - .42 * FRAME_H / FRAME_W * 1080) / max(1, 1920 - FRAME_H / FRAME_W * 1080) * 100))
    strip_w = PAPER_W - 2 * 22
    gap = (strip_w - 6 * FRAME_W) / 7
    p.css.append(f"""
#cam{{position:absolute;left:0;top:0;width:1080px;height:1920px}}
#cam video{{position:absolute;left:0;width:1080px;height:1920px;object-fit:cover}}
#camv{{top:0}}
#camm{{top:-1920px;transform:scaleY(-1);filter:blur(14px)}}
#paper{{position:absolute;left:{PAPER_X}px;top:{PAPER_Y}px;width:{PAPER_W}px;height:{PAPER_H}px;background:{S["paper"]};box-shadow:0 14px 34px rgba(0,0,0,.42);transform-origin:50% 40%}}
.st{{position:absolute;left:22px;width:{strip_w}px;height:{FRAME_H + 2 * BAND}px;background:{S["film"]}}}
.st>s{{position:absolute;left:4px;right:4px;height:8px;display:block;background:repeating-linear-gradient(90deg,{S["hole"]} 0 9px,transparent 9px 21px)}}
.fr{{position:absolute;top:{BAND}px;width:{FRAME_W}px;height:{FRAME_H}px;overflow:hidden;background:#000}}
.fr img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:50% {fy:.1f}%;display:block}}
.fr em{{position:absolute;inset:0;background:#0C0C0C;display:block}}
.tc{{position:absolute;width:{FRAME_W}px;text-align:center;font:500 19px/24px '{S["mono"]}';color:{S["tc"]}}}
.ft{{position:absolute;left:24px;right:24px;font:500 16px/22px '{S["mono"]}';color:{S["foot"]};display:flex;justify-content:space-between;white-space:nowrap;text-transform:uppercase}}
.hw{{position:absolute;font-family:'{S["hand_font"]}';font-style:{ital};font-size:{S["hand_size"]}px;line-height:{HEAD_ROOM}px;height:{HEAD_ROOM}px;color:{S["hand"]};white-space:nowrap;text-align:center;transform:translateX(-50%)}}
#pencil{{position:absolute;left:0;top:0;width:{PAPER_W}px;height:{PAPER_H}px;overflow:visible}}""")
    # the paper
    rows = [HEAD_ROOM, HEAD_ROOM + 2 * BAND + FRAME_H + TC_H]
    h = []
    for r, y in enumerate(rows):
        inner = f'<s style="top:4px"></s><s style="bottom:4px"></s>'
        for c in range(6):
            k = r * 6 + c
            x = gap + c * (FRAME_W + gap)
            inner += f'<div class="fr" style="left:{x:.1f}px"><img src="assets/strip/f{k:02d}.jpg" alt=""><em id="ev{k}"></em></div>'
        h.append(f'<div class="st" style="top:{y}px">{inner}</div>')
        for c in range(6):
            k = r * 6 + c
            x = 22 + gap + c * (FRAME_W + gap)
            h.append(f'<div class="tc" style="left:{x:.1f}px;top:{y + 2 * BAND + FRAME_H + 3}px">{stamp(times[k])}</div>')
    h.append(f'<div class="ft" style="top:{PAPER_H - FOOT_H + 6}px"><span>{V.esc(fname)}</span><span>{V.esc(fright)}</span></div>')
    # the pencil
    svg, js = [], []
    for j, (k, kind, word, t) in enumerate(MARKS):
        at = t if t is not None else mark_t[j]
        r, c = k // 6, k % 6
        cx = 22 + gap + c * (FRAME_W + gap) + FRAME_W / 2
        cy = rows[r] + BAND + FRAME_H / 2
        if kind == 'circle':
            d = loop_path(cx, cy, FRAME_W * .52, (FRAME_H + 2 * BAND) * .54)
            svg.append(f'<path id="m{j}" d="{d}" pathLength="100" fill="none" stroke="{S["hand"]}" stroke-width="6" stroke-linecap="round" stroke-dasharray="100" stroke-dashoffset="100"/>')
            js.append(f"tl.to('#m{j}',{{strokeDashoffset:0,duration:.2,ease:'power1.inOut'}},{V.T(at):.3f});")
        else:
            a, b = FRAME_W * .42, FRAME_H * .42
            svg.append(f'<path id="m{j}a" d="M{cx - a:.1f},{cy - b:.1f} L{cx + a:.1f},{cy + b:.1f}" pathLength="100" fill="none" stroke="{S["hand"]}" stroke-opacity=".82" stroke-width="10" stroke-linecap="round" stroke-dasharray="100" stroke-dashoffset="100"/>')
            svg.append(f'<path id="m{j}b" d="M{cx + a:.1f},{cy - b:.1f} L{cx - a:.1f},{cy + b:.1f}" pathLength="100" fill="none" stroke="{S["hand"]}" stroke-opacity=".82" stroke-width="10" stroke-linecap="round" stroke-dasharray="100" stroke-dashoffset="100"/>')
            js.append(f"tl.to('#m{j}a',{{strokeDashoffset:0,duration:.07,ease:'none'}},{V.T(at):.3f});")
            js.append(f"tl.to('#m{j}b',{{strokeDashoffset:0,duration:.07,ease:'none'}},{V.T(at + .08):.3f});")
        if word:
            if r != 0:
                V.die(f'MARKS: a word only fits above the top strip, and cell {k} is in the bottom strip')
            h.append(f'<div class="hw" id="w{j}" style="left:{cx:.1f}px;top:2px">{V.esc(word)}</div>')
            js.append(f"tl.fromTo('#w{j}',{{clipPath:'inset(-20% 100% -20% 0%)'}},{{clipPath:'inset(-20% -10% -20% 0%)',duration:{min(.34, .07 * len(word) + .06):.2f},ease:'none',immediateRender:false}},{V.T(at + .08):.3f});")
            p.hidden.append(f'#w{j}')
            js.append(f"tl.set('#w{j}',{{autoAlpha:1}},{V.T(at + .08):.3f});")
    h.append(f'<svg id="pencil" viewBox="0 0 {PAPER_W} {PAPER_H}">{"".join(svg)}</svg>')
    p.html = [f'<div id="cam"><video id="camm" src="assets/aroll.mp4" muted playsinline data-start="{t_in:.4f}" data-media-start="{t_in:.4f}" '
              f'data-duration="{t_gone + .09 - t_in:.4f}" data-track-index="3"></video><video id="camv" src="assets/aroll.mp4" muted playsinline data-start="{t_in:.4f}" '
              f'data-media-start="{t_in:.4f}" data-duration="{t_gone + .05 - t_in:.4f}" data-track-index="4"></video></div>'
              f'<div id="paper">{"".join(h)}</div>']
    # the moves
    p.hidden.append('#paper')
    p.js.append(f"tl.fromTo('#cam',{{y:0}},{{y:{slide},duration:{DROP},ease:'power3.out',immediateRender:false}},{V.T(t_in):.3f});")
    p.js.append(f"tl.fromTo('#paper',{{autoAlpha:1,y:{-(PAPER_Y + PAPER_H + 120)},rotation:-4.5}},{{autoAlpha:1,y:0,rotation:0,duration:{DROP},ease:'back.out(1.15)',immediateRender:false}},{V.T(t_in):.3f});")
    for k in range(12):
        p.js.append(f"tl.to('#ev{k}',{{opacity:0,duration:{each},ease:'power1.in'}},{V.T(t_dev + k * stag):.3f});")
    p.js.extend(js)
    p.js.append(f"tl.to('#paper',{{y:{-(PAPER_Y + PAPER_H + 140)},rotation:2.5,duration:.2,ease:'power2.in'}},{V.T(t_out):.3f});")
    p.js.append(f"tl.to('#cam',{{y:0,duration:.2,ease:'power2.inOut'}},{V.T(t_out):.3f});")
    p.sound('whoosh-short', t_in + .06, .4)
    p.sound('whoosh-short', t_out + .08, .3)
    p.write()
    print(f'  drop {t_in:.2f}s, develop {t_dev:.2f} to {t_dev_end:.2f}s, pencil from {t_marks:.2f}s, off at {t_out:.2f} to {t_gone:.2f}s')
    print(f'  the shot slides down {slide} px: head top y {s.head_top + slide}, chin y {s.chin + slide}. In a reel: fx_add.py --caption-y {cap_y}')
    print(f'snapshot at: {t_in + DROP * .4:.2f},{t_land + .05:.2f},{t_dev + 8 * stag:.2f},{t_marks + .3:.2f},{t_out - .03:.2f},{min(s.dur - .02, t_gone + .02):.2f}')


if __name__ == '__main__':
    main()
