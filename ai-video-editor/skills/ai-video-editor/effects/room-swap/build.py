#!/usr/bin/env python3
"""ROOM SWAP (explain): the buyer's own walkthrough video slides in from the right and replaces the room behind the cutout.
Chapter labels change on a green plate with a segmented progress row, each new chapter slides in over the last one, large
captions run under it, and at the end the real room slides back.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html   (SAFE=1 safe-zone guide, SFX=0 no sounds, CAPTIONS=0 no caption line)
"""
import os

import clipfx as X
import vgfx as V
from clipfx import F

# ==== STYLE (the reel's look wins: match the plate and the cap_ lines to the reel's style before building) ====
STYLE = dict(
    plate='#2A4132',               # the chapter plate (forest green)
    plate_w=497, plate_h=115,      # its size, px
    plate_x=65,                    # its left edge, px
    plate_y=1153,                  # its top, px (moved down by itself when the chin is lower)
    name_font='Inter',             # chapter name
    name_weight=600,
    name_px=33,
    num_font='JetBrains Mono',     # chapter number
    num_color='#B9C98A',
    ink='#F3EFE2',                 # names, and the filled part of the progress row
    track='#FFFFFF38',             # the empty part of the row
    cap_font='Instrument Serif',   # the large captions: the effect's own words. The reel's caption style wins here
    cap_weight=400,
    cap_size=72,
    cap_y=1358,
    cap_case='as-said',
    cap_ink='#F3EFE2',
    cap_wait='#88AB91',
    cap_plate='#2A4132',
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
CLIPS = 'clips'     # folder (inside the slot, or a full path): the buyer's own walkthrough video. One video = chapters
                    # jump through it. One video per chapter also works (file-name order)
CHAPTERS = []       # [('chapter name', 'word it starts on'), ...]: 2 to 5, the word is one said in this slot
                    # (None = spread evenly up to END_WORD). The first one's word is when the room starts to change
END_WORD = ''       # the word the real room starts to slide back on. '' = 1.4 s after the last chapter starts
SOURCE_AT = None    # one video: seconds in it where each chapter starts, [12, 40, ...]. None = spread through the video
SKIP = 1.0          # one video per chapter: seconds skipped at the start of each
FOCUS = .5          # which part of a video that is not 9:16 the frame keeps (0 = top or left, 1 = bottom or right)
# ==== END CLIP ====

SLIDE = [.96, .72, .27, .05, 0]        # left edge of an incoming picture, as part of the frame width, frame by frame
OPEN = [.42, .70, .86, .95, 1]         # how much of the plate is showing, from its left edge, frame by frame
SHUT = [.3, .62, .86, 1]               # how much of it is wiped away from the left at the end
TEXT_IN = [20, 13, 7, 3, 1, 0]         # px under its place as a chapter name slides up
LEAD = 2                               # frames before the word that a slide starts, so it lands on the word


def main():
    s = V.Slot()
    print('words: ' + s.word_list())
    print(s.where())
    st = STYLE
    if not 2 <= len(CHAPTERS) <= 5:
        V.die('write CHAPTERS in the CLIP block: 2 to 5 chapter names, each with the word it starts on')
    if not os.path.exists('assets/subject.webm'):
        V.die('assets/subject.webm is missing: this effect needs the clean cutout (setup.py --matting, then make the slot again)')
    # ---- when
    starts, after = [], 0.0
    for name, word in CHAPTERS:
        if word:
            w = s.find('^' + V.re.escape(V.bare(word)) + '$', after)
            if not w:
                V.die(f'chapter "{name}": the word "{word}" is not said in this slot after {after:.2f} s. Words: {s.word_list()}')
            after = w['start'] + .15
            starts.append(round(w['start'] * V.FPS) - LEAD)
        else:
            starts.append(None)
    f_end = None
    if END_WORD:
        w = s.find('^' + V.re.escape(V.bare(END_WORD)) + '$', after)
        if not w:
            V.die(f'END_WORD "{END_WORD}" is not said in this slot after the last chapter. Words: {s.word_list()}')
        f_end = round(w['start'] * V.FPS) - LEAD
    if None in starts:
        f0 = starts[0] if starts[0] is not None else 6
        end = f_end or s.frames - 12
        starts = [f0 + round((end - f0) * k / len(CHAPTERS)) for k in range(len(CHAPTERS))]
    f_end = f_end or starts[-1] + 42
    if starts[0] < 1:
        V.die(f'the first chapter starts too near the slot start: start the slot about {(LEAD + 2) / V.FPS:.2f} s earlier')
    if f_end + len(SLIDE) + 2 > s.frames:
        V.die(f'the room is back at frame {f_end + len(SLIDE) + 2} and the slot has {s.frames}: make the slot longer or set END_WORD earlier')
    # ---- the buyer's video
    lens = [(starts[k + 1] if k + 1 < len(starts) else f_end) - starts[k] + len(SLIDE) for k in range(len(starts))]
    found = sorted(f for f in os.listdir(CLIPS) if f.lower().endswith(X.VIDEO_EXT)) if os.path.isdir(CLIPS) else []
    if len(found) < len(CHAPTERS):
        clip = X.videos(CLIPS, 1, F(sum(lens)) + 1, 0, 'walkthrough video')[0][0]
        total = X.probe(clip)[2]
        at = list(SOURCE_AT) if SOURCE_AT else [total * (.06 + .86 * k / len(CHAPTERS)) for k in range(len(CHAPTERS))]
        if len(at) != len(CHAPTERS):
            V.die('SOURCE_AT needs one time for each chapter')
        parts = []
        for k, a in enumerate(at):
            if a + F(lens[k]) + .1 > total:
                V.die(f'the walkthrough video is {total:.1f} s and chapter {k + 1} needs {F(lens[k]):.1f} s from {a:.1f} s: give a longer video or earlier SOURCE_AT')
            parts.append((clip, a))
    else:
        parts = X.videos(CLIPS, len(CHAPTERS), F(max(lens)) + .1, SKIP, 'walkthrough videos')
    # ---- the plate clears the chin
    plate_y = max(st['plate_y'], s.chin + 22)
    cap_top = st['cap_y'] - st['cap_size'] * .7
    if plate_y + st['plate_h'] > cap_top - 4:
        V.die(f'no room for the chapter plate between the chin (y {s.chin}) and the captions (y {cap_top:.0f}) on this clip: use a wider shot or leave Room Swap out')

    p = X.Comp(s, st)
    p.cutout = True
    n = len(CHAPTERS)
    pw, ph = st['plate_w'], st['plate_h']
    seg_gap = 8
    seg_w = (pw - 54 - (n - 1) * seg_gap) / n
    p.css.append(f'''
.rs{{position:absolute;inset:0;overflow:hidden;opacity:0;will-change:transform}}
#plate{{position:absolute;left:{st["plate_x"]}px;top:{plate_y}px;width:{pw}px;height:{ph}px;border-radius:14px;background:{st["plate"]};overflow:hidden;clip-path:inset(0 100% 0 0 round 14px)}}
#plate .nm{{position:absolute;left:36px;right:18px;top:{round(ph * .13)}px;height:50px;line-height:50px;white-space:nowrap;font-family:'{st["name_font"]}';font-weight:{st["name_weight"]};font-size:{st["name_px"]}px;color:{st["ink"]};letter-spacing:-.01em;opacity:0}}
#plate .nm b{{font-family:'{st["num_font"]}';font-weight:500;font-size:{round(st["name_px"] * .74)}px;color:{st["num_color"]};margin-right:32px}}
#plate .sg{{position:absolute;top:{ph - 30}px;height:5px;width:{seg_w:.1f}px;background:{st["track"]};border-radius:3px;overflow:hidden}}
#plate .sg i{{position:absolute;inset:0;background:{st["ink"]};transform-origin:0 50%;transform:scaleX(0)}}''')
    bits = []
    for k, (name, _) in enumerate(CHAPTERS):
        bits.append(f'<div id="nm{k}" class="nm"><b>{k + 1:02d}</b>{V.esc(name)}</div>')
        bits.append(f'<div class="sg" style="left:{27 + k * (seg_w + seg_gap):.1f}px"><i id="sg{k}"></i></div>')
    p.over.append(f'<div id="plate">{"".join(bits)}</div>')
    for k, (path, a) in enumerate(parts):
        src = X.tile(path, a, F(lens[k]) + .1, 1080, 1920, f'c{k}', FOCUS)
        i = f'rs{k}'
        p.under.append(f'<div id="{i}" class="rs">{p.video(src, F(starts[k]), F(lens[k]))}</div>')
        p.set(f'#{i}', F(starts[k]), opacity=1)
        p.table(f'#{i}', F(starts[k]), [dict(x=round(v * 1080)) for v in SLIDE])
        p.sound('whoosh-short', F(starts[k]), .2 if k else .3)
        # name and segment
        p.table(f'#nm{k}', F(starts[k] + (3 if k == 0 else 1)), [dict(y=v, opacity=1) for v in TEXT_IN])
        if k:
            p.table(f'#nm{k - 1}', F(starts[k]), [dict(y=-10, opacity=.7), dict(y=-22, opacity=.3), dict(y=-34, opacity=0)])
        stop = starts[k + 1] if k + 1 < n else f_end
        p.js.append(f"tl.fromTo('#sg{k}',{{scaleX:0}},{{scaleX:1,duration:{F(stop - starts[k]):.3f},ease:'none',immediateRender:false}},{V.T(F(starts[k])):.3f});")
    # the real room comes back the same way, over the last chapter
    back = f_end
    p.under.append(f'<div id="rsb" class="rs">{p.video("assets/aroll.mp4", F(back), s.dur - F(back), media=F(back))}</div>')
    p.set('#rsb', F(back), opacity=1)
    p.table('#rsb', F(back), [dict(x=round(v * 1080)) for v in SLIDE])
    p.sound('whoosh-short', F(back), .24)
    # plate: opens from its left edge as the first picture arrives, wiped away from the left at the end
    p.table('#plate', F(starts[0]), [dict(clipPath=f'inset(0 {round(100 * (1 - v))}% 0 0 round 14px)') for v in OPEN])
    p.table('#plate', F(back), [dict(clipPath=f'inset(0 0% 0 {round(100 * v)}% round 14px)') for v in SHUT])
    p.set('#plate', F(back + len(SHUT)), opacity=0)
    # the large captions are this effect's own: the reel's are hidden while they run
    if V.env('CAPTIONS', '1') != '0':
        p.captions(0, s.dur, size=st['cap_size'], chars=22)
        s.hide_hint([(0, s.dur)])
    p.write()
    print('chapters slide in at ' + ', '.join(f'{F(f):.2f}' for f in starts) + f', room back at {F(back):.2f} to {F(back + len(SLIDE)):.2f}s')
    print(f'snapshot at: {F(starts[0] + 1):.2f},{F(starts[0] + 7):.2f},{F(starts[1] + 2):.2f},{F(starts[-1] + 9):.2f},{F(back + 2):.2f},{F(back + 7):.2f}')


if __name__ == '__main__':
    main()
