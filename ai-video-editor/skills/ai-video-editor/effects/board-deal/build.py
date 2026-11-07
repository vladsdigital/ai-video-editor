#!/usr/bin/env python3
"""BOARD DEAL (proof): cream cards made from real shots of this reel, each with the line that shot says under it, deal
out one by one onto a 4 x 2 board behind the speaker, spinning in edge-on from beside the head. Then they gather into a
deck beside the head, the top card flips over to a note page, and the note underlines itself.

The speaker stays in front through the cutout. No logo, no interface.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html and assets/board/*.jpg   (SAFE=1 safe-zone guide, SFX=0 no sounds)
"""
import json
import os
import shutil
import subprocess

os.environ.setdefault('PREVIEW', '1')     # the cutout goes over the cards, so the footage is part of the page
import vgfx as V  # noqa: E402

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    paper='#F3EEDF',               # the cards and the note (cream)
    ink='#2A2A24',                 # text on paper
    dim='#77735F',                 # small labels
    band='#163127',                # the band at the foot of a card and the top of the note (deep forest green)
    band_ink='#D8D3BC',            # text on the band
    mark='#1F4A38',                # the note's underlines
    serif='Newsreader',            # the line under a card, the note's text
    serif_title='Newsreader',      # the note's title (italic)
    mono='JetBrains Mono',         # the band and the small labels
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
CARDS = None        # None = the reel's own shots, one card each, with the line each one says (segments.json). Or a list of
                    # (frame number of the reel, 'the line under the card'). At most 8 are used
NOTE_TITLE = ''     # the note's title: the speaker's own words. Required
NOTE_LINES = []     # the note's text, line by line, about 26 characters each, in the speaker's words. A line that starts
                    # with * gets an underline
NOTE_ROWS = []      # up to 2 ('label', 'value') rows under the text. True facts of the reel only, e.g. ('length', '10.4 s')
NOTE_PILL = ''      # a short label in a plain outlined pill at the foot of the note. '' = none
NOTE_TAG = None     # text on the note's band. None = the card number and the length of the shot
T_IN = None         # the first card starts to fly (slot seconds). None = 0.1 s
T_GATHER = None     # the cards gather into the deck. None = 0.6 s after the last card lands
T_FLIP = None       # the top card flips to the note. None = 0.75 s after T_GATHER
T_OUT = None        # the deck leaves. None = 0.3 s before the slot ends
DEAL = .3           # how far apart the cards fly out, seconds (the fourth to eighth go a little faster)
SIDE = None         # 'left' or 'right' for the deck. None = the side with more wall
# ==== END CLIP ====

CARD_W, CARD_H = 234, 468
GRID_X, GRID_Y = 36, 232
PITCH_X, PITCH_Y = 252, 480
IMG_H = 376
FOOT_H = 22
TILTS = [-3, 5, 7, -4, -8, 4, 9, -5]
FAN = [(-9, 7, -1.6), (7, -6, 1.4), (-5, -9, -.8), (8, 8, 1.0), (-7, 5, .7), (5, -7, -1.2), (6, 4, .6), (0, 0, 0)]


def plain(s):
    return s.strip().rstrip('.,;:')


def shots(s):
    """the cards: (reel frame, line under the card, number of frames in that shot)"""
    proj = s.clip.get('project')
    if CARDS:
        return [(int(f), str(t), 0) for f, t in CARDS[:8]]
    if proj:
        try:
            segs = json.load(open(os.path.join(proj, 'segments.json'), encoding='utf-8'))
        except (OSError, ValueError):
            segs = []
        rows = [(g['frame'] + g['frames'] // 2, g.get('line') or '', g['frames']) for g in segs][:8]
        if len(rows) >= 4:
            return rows
    return []


def short(line, n=46):
    line = line.strip()
    if len(line) <= n:
        return line
    cut = line[:n].rsplit(' ', 1)[0].rstrip(',.;:')
    return cut + '...'


def main():
    s = V.Slot()
    print('words: ' + s.word_list())
    print(s.where())
    S = STYLE
    cards = shots(s)
    if not cards:
        V.die('no shots to deal: this slot has no reel project with at least 4 shots. Write CARDS in the CLIP block')
    if not NOTE_TITLE.strip():
        V.die('write NOTE_TITLE in the CLIP block: the speaker\'s own words')
    src = s.clip.get('src')
    if not (src and os.path.isfile(src) and s.clip.get('project')):
        V.die('the cards are the reel\'s own shots: make the slot with fx_new.py --project')
    if not os.path.isfile('assets/subject.webm'):
        V.die('no cutout in this slot (assets/subject.webm): make the slot with the clean cutout')
    # ---- where the deck lands
    head = (s.layout or {}).get('head') or {}
    half = (head.get('width') or 380) / 2 + 12
    room_l, room_r = s.cx - half - V.SAFE_SIDE, 1080 - V.SAFE_SIDE - (s.cx + half)
    side = SIDE or ('left' if room_l >= room_r else 'right')
    room = room_l if side == 'left' else room_r
    deck_w = min(425, room - 8)
    if deck_w < 290:
        V.die(f'{int(room)} px of wall beside the head: the deck needs about 300. This framing does not fit it')
    zoom = deck_w / CARD_W
    deck_h = CARD_H * zoom
    deck_x = V.SAFE_SIDE + 4 if side == 'left' else 1080 - V.SAFE_SIDE - 4 - deck_w
    deck_y = 232
    # ---- the frames
    shutil.rmtree('assets/board', ignore_errors=True)
    os.makedirs('assets/board')
    for k, (f, _, _) in enumerate(cards):
        subprocess.run([shutil.which('ffmpeg') or 'ffmpeg', '-v', 'error', '-y', '-ss', f'{f / V.FPS:.3f}', '-i', src, '-frames:v', '1', '-vf', 'scale=560:-2', '-q:v', '3',
                        f'assets/board/c{k}.jpg'], check=True)
    # ---- when
    n = len(cards)
    t_in = T_IN if T_IN is not None else .1
    starts = []
    t = t_in
    for k in range(n):
        starts.append(t)
        t += DEAL if k < 3 else DEAL * .8
    t_dealt = starts[-1] + .3
    t_gather = T_GATHER if T_GATHER is not None else t_dealt + .6
    t_stack = t_gather + .3
    t_flip = T_FLIP if T_FLIP is not None else t_gather + .75
    t_note = t_flip + .3
    t_out = T_OUT if T_OUT is not None else s.dur - .3
    t_gone = t_out + .24
    if t_gone > s.dur - .02 or t_note + .5 > t_out:
        V.die(f'the slot is too short at {s.dur:.2f} s: the note is up at {t_note:.2f} s and the deck leaves at {t_out:.2f} s. It needs about {t_note + .85:.1f} s')
    p = V.Page(s)
    p.css.append(f"""
#board{{position:absolute;left:0;top:0;width:1080px;height:1920px;z-index:1}}
.cd{{position:absolute;left:0;top:0;width:{CARD_W}px;height:{CARD_H}px;background:{S["paper"]};box-shadow:0 8px 22px rgba(0,0,0,.34);transform-origin:50% 50%;overflow:hidden}}
.cd img{{position:absolute;left:7px;top:7px;width:{CARD_W - 14}px;height:{IMG_H}px;object-fit:cover;display:block}}
.cd p{{position:absolute;left:9px;right:7px;top:{IMG_H + 12}px;font:italic 500 18px/21px '{S["serif"]}';color:{S["ink"]}}}
.cd u{{position:absolute;left:0;right:0;bottom:0;height:{FOOT_H}px;background:{S["band"]};color:{S["band_ink"]};font:500 12px/{FOOT_H}px '{S["mono"]}';display:flex;justify-content:space-between;padding:0 8px;text-decoration:none}}
#subj{{position:absolute;left:0;top:0;width:1080px;height:1920px;object-fit:cover;z-index:3}}
#note{{position:absolute;left:{deck_x:.0f}px;top:{deck_y:.0f}px;width:{deck_w:.0f}px;height:{deck_h:.0f}px;background:{S["paper"]};box-shadow:0 10px 26px rgba(0,0,0,.36);overflow:hidden;z-index:20}}
#note .bd{{height:38px;background:{S["band"]};color:{S["band_ink"]};font:500 17px/38px '{S["mono"]}';padding:0 16px;white-space:nowrap}}
#note h3{{margin:26px 18px 22px;font:italic 500 {int(deck_w * .112)}px/1.14 '{S["serif_title"]}';color:{S["ink"]}}}
#note .ln{{position:relative;margin:0 18px;font:400 {int(deck_w * .082)}px/{int(deck_w * .132)}px '{S["serif"]}';color:{S["ink"]};white-space:nowrap}}
#note .ln i{{position:absolute;left:0;right:0;bottom:2px;height:3px;background:{S["mark"]};transform-origin:0 50%;display:block}}
#note .rw{{margin:26px 18px -8px;display:flex;gap:16px;font:400 {int(deck_w * .066)}px/1.3 '{S["serif"]}';color:{S["ink"]}}}
#note .rw b{{font:500 {int(deck_w * .036)}px/2 '{S["mono"]}';color:{S["dim"]};text-transform:uppercase;min-width:{int(deck_w * .2)}px}}
#note .pl{{position:absolute;left:18px;bottom:24px;padding:0 22px;height:48px;border:2px solid {S["dim"]};border-radius:24px;font:500 {int(deck_w * .052)}px/44px '{S["serif"]}';color:{S["ink"]}}}""")
    html = []
    for k, (f, line, frames) in enumerate(cards):
        clock = f'{int(f / V.FPS // 60)}:{int(f / V.FPS % 60):02d}'
        html.append(f'<div class="cd" id="cd{k}" style="z-index:{k + 1}"><img src="assets/board/c{k}.jpg" alt=""><p>{V.esc(short(line))}</p>'
                    f'<u><span>k{k + 1:02d}</span><span>{clock}</span></u></div>')
    # the note page
    tag = NOTE_TAG or f'k{n:02d}'
    lines = ''
    underlined = []
    for j, ln in enumerate(NOTE_LINES):
        mark = ln.startswith('*')
        txt = ln[1:] if mark else ln
        if mark:
            underlined.append(j)
        lines += f'<div class="ln">{V.esc(txt)}{f"<i id=um{j}></i>" if mark else ""}</div>'
    rows = ''.join(f'<div class="rw"><b>{V.esc(a)}</b><span>{V.esc(b)}</span></div>' for a, b in NOTE_ROWS[:2])
    pill = f'<div class="pl">{V.esc(NOTE_PILL)}</div>' if NOTE_PILL else ''
    note = f'<div id="note"><div class="bd">{V.esc(tag)}</div><h3>{V.esc(NOTE_TITLE)}</h3>{lines}{rows}{pill}</div>'
    dur_sub = t_gone + .05 - t_in
    p.html = [f'<div id="board">{"".join(html)}{note}</div>'
              f'<video id="subj" src="assets/subject.webm" muted playsinline data-start="{t_in:.4f}" data-media-start="{t_in:.4f}" data-duration="{dur_sub:.4f}" data-track-index="3"></video>']
    # the deal
    gx = deck_x + deck_w / 2 - CARD_W / 2
    gy = deck_y + deck_h * .42 - CARD_H / 2
    for k in range(n):
        cx = GRID_X + (k % 4) * PITCH_X
        cy = GRID_Y + (k // 4) * PITCH_Y
        p.hidden.append(f'#cd{k}')
        p.js.append(f"gsap.set('#cd{k}',{{transformPerspective:1300}});")
        tilt = TILTS[k % len(TILTS)]
        p.js.append(f"tl.fromTo('#cd{k}',{{autoAlpha:1,x:{gx:.1f},y:{gy:.1f},rotationY:82,rotation:{tilt * 2},scale:.62}},"
                    f"{{autoAlpha:1,x:{cx},y:{cy},rotationY:0,scale:1,rotation:{tilt},duration:.26,ease:'power3.out',immediateRender:false}},{V.T(starts[k]):.3f});")
        p.js.append(f"tl.to('#cd{k}',{{rotation:0,duration:.14,ease:'power2.out'}},{V.T(starts[k] + .267):.3f});")
        p.sound('click-soft', starts[k] + .2, .26)
    # the gather: they run into a deck beside the head
    for k in range(n):
        fx, fy, fr = FAN[(n - 1 - k) % len(FAN)] if k < n - 1 else (0, 0, 0)
        at = t_gather + (n - 1 - k) * .012
        tx = deck_x + deck_w / 2 - CARD_W / 2 + fx
        ty = deck_y + deck_h / 2 - CARD_H / 2 + fy
        p.js.append(f"tl.to('#cd{k}',{{x:{tx:.1f},y:{ty:.1f},rotation:{fr},scale:{zoom:.4f},duration:{t_stack - t_gather - .1:.3f},ease:'power3.inOut'}},{V.T(at):.3f});")
    p.sound('whoosh-short', t_gather + .08, .35)
    # the flip: the top card goes edge-on, the note comes round
    p.hidden.append('#note')
    p.js.append("gsap.set('#note',{transformPerspective:1300,rotationY:-88});")
    p.js.append(f"tl.to('#cd{n - 1}',{{rotationY:88,duration:.15,ease:'power2.in'}},{V.T(t_flip):.3f});")
    p.js.append(f"tl.set('#cd{n - 1}',{{autoAlpha:0}},{V.T(t_flip + .15):.3f});")
    p.js.append(f"tl.set('#note',{{autoAlpha:1}},{V.T(t_flip + .15):.3f});")
    p.js.append(f"tl.to('#note',{{rotationY:0,duration:.16,ease:'power2.out'}},{V.T(t_flip + .15):.3f});")
    p.sound('click-soft', t_flip + .15, .3)
    # the note takes its marks
    for i, j in enumerate(underlined):
        p.js.append(f"gsap.set('#um{j}',{{scaleX:0}});")
        p.js.append(f"tl.to('#um{j}',{{scaleX:1,duration:.22,ease:'power1.inOut'}},{V.T(t_note + .15 + i * .22):.3f});")
    # out
    off = -deck_w - 120 if side == 'left' else deck_w + 120
    p.js.append(f"tl.to('#board',{{x:{off:.0f},rotation:{-3 if side == 'left' else 3},duration:.24,ease:'power2.in'}},{V.T(t_out):.3f});")
    p.write()
    print(f'  side {side}, deck {deck_w:.0f} x {deck_h:.0f}. {n} cards fly from {t_in:.2f}s, last lands {t_dealt:.2f}s, gather {t_gather:.2f}s, flip {t_flip:.2f}s, note up {t_note:.2f}s, out {t_out:.2f} to {t_gone:.2f}s')
    print(f'snapshot at: {starts[1] + .1:.2f},{starts[n // 2] + .1:.2f},{t_dealt + .3:.2f},{t_gather + .12:.2f},{t_flip + .12:.2f},{t_note + .6:.2f},{t_out + .12:.2f}')


if __name__ == '__main__':
    main()
