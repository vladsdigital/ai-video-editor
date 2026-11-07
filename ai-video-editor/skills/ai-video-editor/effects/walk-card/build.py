#!/usr/bin/env python3
"""WALK CARD (explain): a card unfolds in the free space above the head (or beside it on a tighter shot): a 16:9 picture on
top, a deep green panel with a serif title under it. A play button presses on a word, the buyer's own walkthrough
video plays inside, and titled chapters skip by with a thin progress line. Then it folds away.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html   (SAFE=1 safe-zone guide + footage, SFX=0 no sounds, CAPTIONS=0 no caption line)
"""
import os
import subprocess

import clipfx as X
import vgfx as V
from clipfx import F

# ==== STYLE (the reel's look wins: match this block to the reel's style before building) ====
STYLE = dict(
    panel='#1F3F2E',               # the panel under the picture (deep forest green)
    title_font='Instrument Serif', # the card's title
    title_weight=400,
    title_px=52,                   # at full card width; a smaller card scales it, down to 38
    sub_font='Inter',              # chapter names
    sub_weight=500,
    sub_px=25,
    mono_font='JetBrains Mono',    # chapter numbers and the small word in capitals
    num_color='#B9C98A',
    ink='#F3EFE2',                 # text on the panel and the filled part of the line (cream)
    track='#FFFFFF40',             # the empty part of the line
    radius=18,
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
CLIPS = 'clips'     # folder (inside the slot, or a full path): the buyer's own walkthrough video. One video = chapters
                    # jump through it. One video per chapter also works (file-name order)
TITLE = ''          # the card's title, the buyer's words. Up to about 30 characters on a wide shot, 16 on a tight one
KICKER = ''         # small word in capitals under the title before play ("vodič"). '' = none
COUNT = ''          # small words beside it ("3 poglavlja"). '' = none
CHAPTERS = []       # [('chapter name', 'word it starts on'), ...]: 2 to 5. The word is one the speaker says in this slot
                    # (None = spread evenly up to T_END). Example: [('Fakture', 'faktura,'), ('Ponude', 'ponuda,')]
PRESS_WORD = ''     # the word the play button presses on. The card starts unfolding 7 frames before it. '' = 0.25 s into the slot
T_END = None        # slot seconds the card starts to close. None = 0.9 s after the last chapter starts
SOURCE_AT = None    # one video: seconds in it where each chapter starts, [12, 40, ...]. None = spread through the video
FOCUS = .3          # which part of a tall video the 16:9 picture keeps (0 = top, .5 = middle, 1 = bottom)
PLACE = 'auto'      # 'auto' = above the head if it fits, else beside it. 'above' or 'side' forces it (still never on the face)
HEAD_TOP = None     # top of the head, px, when layout.json has it wrong. None = measured
# ==== END CLIP ====

CARD_W, VIDEO_H, PANEL_H, TOP = 764, 430, 143, 227        # the card at its full size, px
POP = [.14, .46, .76, .88, .94, .98, 1]                   # size, frame by frame, as it comes up
OPEN = [0, .07, .28, .49, .73, .87, .98, 1]               # how far the panel has opened under the picture, frame by frame
TEXT_IN = [24, 17, 11, 6, 3, 1, 0]                        # px under its place, frame by frame, as a line of text slides in


def main():
    s = V.Slot()
    print('words: ' + s.word_list())
    print(s.where())
    st = STYLE
    if not TITLE.strip():
        V.die('write TITLE in the CLIP block: the name of the walkthrough, in the buyer\'s words')
    if not 2 <= len(CHAPTERS) <= 5:
        V.die('write CHAPTERS in the CLIP block: 2 to 5 chapter names, each with the word it starts on')
    # ---- when
    t_press = .25
    if PRESS_WORD:
        w = s.find('^' + V.re.escape(V.bare(PRESS_WORD)) + '$')
        if not w:
            V.die(f'PRESS_WORD "{PRESS_WORD}" is not said in this slot. Words: {s.word_list()}')
        t_press = w['start']
    f_press = round(t_press * V.FPS)
    f_in = f_press - 7
    if f_in < 1:
        V.die(f'the card needs 7 frames before the press and the slot has {f_press}: start the slot about {(8 - f_press) / V.FPS:.2f} s earlier')
    starts, after = [], F(f_press + 9)
    for name, word in CHAPTERS:
        if word:
            w = s.find('^' + V.re.escape(V.bare(word)) + '$', after)
            if not w:
                V.die(f'chapter "{name}": the word "{word}" is not said in this slot after {after:.2f} s. Words: {s.word_list()}')
            after = w['start'] + .15
            starts.append(round(w['start'] * V.FPS))
        else:
            starts.append(None)
    last_end = round(T_END * V.FPS) if T_END else None
    known = [x for x in starts if x is not None]
    if None in starts:
        f0 = starts[0] if starts[0] is not None else f_press + 9
        end = last_end or s.frames - 12
        starts = [f0 + round((end - f0) * k / len(CHAPTERS)) for k in range(len(CHAPTERS))]
    f_end = last_end or starts[-1] + 27
    f_gone = f_end + 10
    if f_gone > s.frames:
        V.die(f'the card closes at frame {f_gone} and the slot has {s.frames}: make the slot longer or set T_END earlier')
    # ---- the buyer's video
    lens = [(starts[k + 1] if k + 1 < len(starts) else f_end + 6) - starts[k] for k in range(len(starts))]
    folder_videos = sorted(f for f in os.listdir(CLIPS) if f.lower().endswith(X.VIDEO_EXT)) if os.path.isdir(CLIPS) else []
    one = len(folder_videos) < len(CHAPTERS)
    if one:
        clip = X.videos(CLIPS, 1, F(sum(lens)) + 1, 0, 'walkthrough video')[0][0]
        total = X.probe(clip)[2]
        at = list(SOURCE_AT) if SOURCE_AT else [total * (.08 + .84 * k / len(CHAPTERS)) for k in range(len(CHAPTERS))]
        if len(at) != len(CHAPTERS):
            V.die('SOURCE_AT needs one time for each chapter')
        parts = []
        for k, a in enumerate(at):
            if a + F(lens[k]) + .1 > total:
                V.die(f'the walkthrough video is {total:.1f} s and chapter {k + 1} needs {F(lens[k]):.1f} s from {a:.1f} s: give a longer video or earlier SOURCE_AT')
            parts.append((clip, a))
    else:
        got = X.videos(CLIPS, len(CHAPTERS), F(max(lens)) + .1, 1.0, 'walkthrough videos')
        parts = list(got)
    # ---- where: above the head when it fits, else in the free side beside it
    head_top = HEAD_TOP if HEAD_TOP else s.head_top
    head = (s.layout or {}).get('head') or {}
    full_h = VIDEO_H + PANEL_H
    fits_above = TOP + full_h + 20 <= head_top
    place = PLACE if PLACE != 'auto' else ('above' if fits_above else 'side')
    if place == 'above':
        if not fits_above and not HEAD_TOP:
            V.die(f'the card is {full_h} px tall and there are only {head_top - TOP} px above the head on this clip. Use PLACE = \'side\' or a wider shot')
        w, cx, cy = CARD_W, 540, TOP + full_h // 2
        k = 1.0
    else:
        left_room = int(head.get('side_left') or head.get('left') or s.cx - 200) - V.SAFE_SIDE - 20
        right_room = 1080 - V.SAFE_SIDE - int(head.get('side_right') or head.get('right') or s.cx + 200) - 20
        room = max(left_room, right_room)
        if room < 360:
            V.die(f'there is no room for the card on this clip: {head_top - TOP} px above the head and {room} px beside it. Leave Walk Card out on this shot')
        w = min(CARD_W, room)
        k = w / CARD_W
        cx = (V.SAFE_SIDE + 8 + w / 2) if left_room >= right_room else (1080 - V.SAFE_SIDE - 8 - w / 2)
        cy = None
        print(f'placement: no room above the head ({head_top - TOP} px), so the card sits beside it, {w} px wide')
    vh = round(w * 9 / 16)
    tpx = max(38, round(st['title_px'] * k))
    spx = max(23, round(st['sub_px'] * k))
    pad = max(20, round(36 * k))
    ph = round(tpx * 1.32 + spx * 1.5 + pad * .95)
    h = vh + ph
    if cy is None:
        cy = max(V.SAFE_TOP + 16, min(TOP, head_top - 200)) + h // 2
    # ---- the card
    p = X.Comp(s, st, overlay=True)
    bar_y = vh - max(16, round(30 * k))
    p.css.append(f'''
#wc{{position:absolute;left:{cx - w / 2:.0f}px;top:0;width:{w}px;height:{vh}px;border-radius:{st["radius"]}px;overflow:hidden;background:{st["panel"]};opacity:0;box-shadow:0 18px 44px rgba(0,0,0,.28);transform-origin:50% 0;will-change:transform}}
#wc .vid{{position:absolute;left:0;top:0;width:{w}px;height:{vh}px;background:#0A0F0C;overflow:hidden}}
#wc .vid img,#wc .vid video{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
#wc .play{{position:absolute;left:50%;top:{vh / 2:.0f}px;width:{round(116 * k)}px;height:{round(116 * k)}px;margin:-{round(58 * k)}px 0 0 -{round(58 * k)}px;border-radius:50%;background:#F7F5EE;box-shadow:0 4px 18px rgba(0,0,0,.3)}}
#wc .play i{{position:absolute;left:41%;top:32%;width:0;height:0;border-style:solid;border-width:{round(18 * k)}px 0 {round(18 * k)}px {round(28 * k)}px;border-color:transparent transparent transparent #1B2A22}}
#wc .track{{position:absolute;left:{pad / 2:.0f}px;width:{w - pad}px;top:{bar_y}px;height:{max(3, round(4 * k))}px;background:{st["track"]};border-radius:2px;opacity:0}}
#wc .fill{{position:absolute;left:0;top:0;bottom:0;width:100%;background:{st["ink"]};border-radius:2px;transform-origin:0 50%;transform:scaleX(0)}}
#wc .knob{{position:absolute;top:50%;left:0;width:{max(10, round(15 * k))}px;height:{max(10, round(15 * k))}px;margin:-{max(5, round(7.5 * k))}px 0 0 -{max(5, round(7.5 * k))}px;border-radius:50%;background:{st["num_color"]}}}
#wc .pan{{position:absolute;left:0;right:0;top:{vh}px;height:{ph}px;overflow:hidden;background:{st["panel"]}}}
#wc .ttl{{position:absolute;left:{pad}px;right:{pad}px;top:{round(pad * .34)}px;font-family:'{st["title_font"]}';font-weight:{st["title_weight"]};font-size:{tpx}px;line-height:1.2;color:{st["ink"]};white-space:nowrap;letter-spacing:-.008em;opacity:0}}
#wc .row{{position:absolute;left:{pad}px;right:{pad}px;top:{round(pad * .34 + tpx * 1.24)}px;height:{round(spx * 1.4)}px;font-family:'{st["sub_font"]}';font-weight:{st["sub_weight"]};font-size:{spx}px;line-height:{round(spx * 1.4)}px;color:{st["ink"]};white-space:nowrap;opacity:0}}
#wc .row b{{font-family:'{st["mono_font"]}';font-weight:500;font-size:{round(spx * .82)}px;color:{st["num_color"]};margin-right:{round(spx * .7)}px;letter-spacing:.03em}}
#wc .row em{{font-style:normal;margin-left:{round(spx * .3)}px;opacity:.7}}
#wc .veil{{position:absolute;inset:0;background:{st["panel"]};opacity:0}}''')
    still = 'assets/tiles/still.jpg'
    tiles = []
    for k2, (path, a) in enumerate(parts):
        tiles.append(X.tile(path, a, F(lens[k2]) + .1, w * 1.5, vh * 1.5, f'c{k2}', FOCUS))
    subprocess.run([X.FF, '-v', 'error', '-y', '-i', tiles[0], '-frames:v', '1', '-q:v', '2', still], check=True)
    vids = ''.join(p.video(t, F(starts[k2]), F(lens[k2]), cls='') for k2, t in enumerate(tiles))
    rows = []
    if KICKER or COUNT:
        rows.append(f'<div id="rk" class="row"><b style="letter-spacing:.14em">{V.esc(KICKER.upper())}</b><em>{V.esc(COUNT)}</em></div>')
    for k2, (name, _) in enumerate(CHAPTERS):
        rows.append(f'<div id="r{k2}" class="row"><b>{k2 + 1:02d}</b>{V.esc(name)}</div>')
    p.top.append(f'''<div id="wc"><div class="vid"><img src="{still}" alt="">{vids}<div id="pb" class="play"><i></i></div><div id="tr" class="track"><div id="fi" class="fill"></div><div id="kn" class="knob"></div></div></div>
<div id="pan" class="pan"><div id="tt" class="ttl">{V.esc(TITLE)}</div>{''.join(rows)}</div><div id="ve" class="veil"></div></div>''')
    # up and open: the middle of the card stays where it is while the panel grows
    n = max(len(POP), len(OPEN))
    t0 = F(f_in)
    tbl = []
    for j in range(n):
        sc = POP[min(j, len(POP) - 1)]
        op = OPEN[min(j, len(OPEN) - 1)]
        cur = vh + ph * op
        tbl.append(dict(scale=sc, height=round(cur), y=round(cy - cur * sc / 2), opacity=1))
    p.table('#wc', t0, tbl)
    p.table('#tt', t0 + F(6), [dict(y=v, opacity=1) for v in TEXT_IN])
    if KICKER or COUNT:
        p.table('#rk', t0 + F(9), [dict(y=v, opacity=1) for v in TEXT_IN])
    # the press lands on the word: down and grey for two frames, back up, gone when the video starts
    p.table('#pb', F(f_press), [dict(scale=.86, opacity=.45), dict(scale=.84, opacity=.45), dict(scale=.9, opacity=.72), dict(scale=.94, opacity=.95), dict(scale=.96, opacity=1)])
    p.table('#pb', F(starts[0] - 2), [dict(scale=.9, opacity=.7), dict(scale=.8, opacity=.3), dict(scale=.7, opacity=0)])
    p.sound('pop', t0 + F(1), .2)
    p.sound('click', F(f_press), .34)
    # chapters: a hard skip in the picture, the name slides up a frame later, the line jumps with them
    p.set('#tr', F(starts[0]), opacity=1)
    span = f_end - starts[0]
    p.js.append(f"tl.fromTo('#fi',{{scaleX:0}},{{scaleX:1,duration:{F(span):.3f},ease:'none',immediateRender:false}},{V.T(F(starts[0])):.3f});")
    p.js.append(f"tl.fromTo('#kn',{{x:0}},{{x:{w - pad},duration:{F(span):.3f},ease:'none',immediateRender:false}},{V.T(F(starts[0])):.3f});")
    prev = '#rk' if (KICKER or COUNT) else None
    for k2, f in enumerate(starts):
        if prev:
            p.table(prev, F(f), [dict(y=-8, opacity=.8), dict(y=-20, opacity=.35), dict(y=-30, opacity=0)])
        p.table(f'#r{k2}', F(f), [dict(y=v, opacity=1) for v in TEXT_IN])
        prev = f'#r{k2}'
        p.sound('click-soft', F(f), .22)
    # out: the picture goes under the green, then the card folds up
    p.to('#ve', F(f_end), F(4), 'sine.inOut', opacity=1)
    tb2 = []
    for sc, op in ((.98, .9), (.9, .66), (.72, .36), (.42, .12), (.14, 0)):
        cur = vh + ph * op
        tb2.append(dict(scale=sc, height=round(cur), y=round(cy - cur * sc / 2)))
    p.table('#wc', F(f_end + 4), tb2)
    p.set('#wc', F(f_end + 9), opacity=0)
    p.sound('whoosh-short', F(f_end + 4), .16)
    if V.env('CAPTIONS', '1') != '0':
        p.captions(0, s.dur)
    p.write()
    print(f'card {w} x {h} at centre ({cx:.0f},{cy}), up at {t0:.2f}s, press at {F(f_press):.2f}s, chapters at ' + ', '.join(f'{F(f):.2f}' for f in starts) + f', closes at {F(f_end):.2f}s, gone at {F(f_gone):.2f}s')
    print(f'snapshot at: {t0 + F(2):.2f},{F(f_press):.2f},{F(starts[0] + 8):.2f},{F(starts[-1] + 8):.2f},{F(f_end + 5):.2f}')


if __name__ == '__main__':
    main()
