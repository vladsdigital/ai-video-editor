#!/usr/bin/env python3
"""RECEIPT PRINT (explain): a thin forest-green printer bar sits above the head and prints what the speaker says as a
cream paper receipt in mono type: a header, the sentence line by line in step with the words, a total line. The paper
stops, jerks, tears off and is gone in a quarter of a second; the bar stays a moment longer and leaves.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html   (SAFE=1 safe-zone guide, SFX=0 no sounds, CAPTIONS=0 accepted:
                                               the receipt IS the effect, so it always draws)
"""
import random

import vgfx as V

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    font='JetBrains Mono',         # any family assets/fonts/fonts.css provides. Another typeface may need char_width
    weight=500,
    head_weight=700,               # header and total rows
    char_width=.6,                 # letter width in em: used to wrap the lines
    case='upper',                  # 'as-said', 'lower' or 'upper'
    paper='#F3EFE2',
    paper_ink='#141511',
    paper_dim='#7B776B',           # second header row
    bar='#133227',                 # printer bar (deep forest green)
    bar_edge='#1E4436',
    dots='#C9D2B8',                # the row of dots along the slot
    led='#D9B26A',
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
TEXT = ''           # what prints: the speaker's own words. Required. Up to about 70 characters
HEADER = 'INSTRUCTION'         # first header row, left
NUMBER = '01'                  # first header row, right
TO = 'TO THE AI'               # second header row, right (never a real product's name unless the buyer asks)
TOTAL_LABEL = 'TOTAL'          # the total line, left
TOTAL_VALUE = '1 SENTENCE'     # the total line, right
T_START = None      # when the first word of TEXT is said (slot seconds). None = found in words.json
T_DONE = None       # when the total line prints. None = when the last word of TEXT ends
HOLD = .4           # seconds the finished receipt stays before it tears off
Y = None            # y of the top of the printer bar, px. None = just above the head from layout.json
SCALE = None        # size against the full-size receipt (525 px wide). None = as large as the room above the head allows
SOUND = .22         # volume of the paper feed and the tear. 0 = silent
# ==== END CLIP ====

# the receipt at full size, px: everything scales together, so the proportions never change
W, PAD, FS, LH, SMALL, SMALL2 = 525, 39, 45, 63, 23, 18
C_H1, C_H2, RULE1, C_BODY = 33, 65, 92, 138       # centres of the rows from the top of the paper
BAR_W, BAR_H, SLOT = 612, 52, 18                  # the paper leaves the bar SLOT px below the bar's top edge


def wrap(text, cols):
    lines, cur = [], ''
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > cols:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + ' ' + w).strip()
    return lines + [cur] if cur else lines


def teeth(w, h, step):
    """clip-path of a sheet with torn top and bottom edges: uneven pointed waves (the same tear every build)"""
    rnd = random.Random(11)
    n = max(4, int(w / step))
    edge = lambda: [(w * k / n, (0 if k % 2 else rnd.uniform(.5, 1)) * step * .34) for k in range(n + 1)]
    top = [f'{x:.1f}px {d:.1f}px' for x, d in edge()]
    bot = [f'{x:.1f}px {h - d:.1f}px' for x, d in edge()]
    return 'polygon(' + ','.join(top + bot[::-1]) + ')'


def align(tokens, words, t0):
    """(start, end) of each token of TEXT in the spoken words, walking forward. None where it is not found."""
    out, k = [], next((i for i, w in enumerate(words) if w['start'] >= t0 - .01), len(words))
    for tok in tokens:
        b = V.bare(tok).lower()
        j = next((i for i in range(k, min(k + 6, len(words))) if V.bare(words[i]['text']).lower() == b), None)
        if j is None:
            out.append(None)
        else:
            out.append((words[j]['start'], words[j]['end']))
            k = j + 1
    return out


def main():
    s = V.Slot()
    s.dur = int(s.frames / V.FPS * 1e4) / 1e4      # rounded down: a page rounded up to the next 1/10000 s renders one frame too many
    print('words: ' + s.word_list())
    print(s.where())
    if not TEXT.strip():
        V.die('write TEXT in the CLIP block: the sentence the receipt prints')
    tokens = TEXT.split()
    w0 = next((w for w in s.words if V.bare(w['text']).lower() == V.bare(tokens[0]).lower()), None)
    t_start = T_START if T_START is not None else (w0['start'] if w0 else .3)
    times = align(tokens, s.words, t_start)
    found = [t for t in times if t]
    t_done = T_DONE if T_DONE is not None else (found[-1][1] if found else t_start + len(tokens) * .35)

    lines = wrap(V.cased(TEXT, STYLE['case']), int((W - 2 * PAD) / (STYLE['char_width'] * FS)))
    last = C_BODY + LH * (len(lines) - 1)
    rule2 = last + 38
    c_total = rule2 + 34
    H = c_total + 34
    room = (Y + BAR_H if Y is not None else s.head_top - 10) - V.SAFE_TOP - 6
    k = SCALE if SCALE else min(1.0, room / (H + BAR_H - SLOT))
    if k < .58:
        V.die(f'the receipt needs more room above the head than this clip has ({room} px between the safe zone and the '
              'head): shorten TEXT, or pick a wider shot')
    px = lambda v: round(v * k, 1)
    bar_w, bar_h, slot_y = px(BAR_W), px(BAR_H), px(SLOT)
    bar_y = int(Y) if Y is not None else int(s.head_top - 10 - bar_h)
    width = px(W)
    bar_l = int(min(max(V.SAFE_SIDE, s.cx - bar_w / 2), 1080 - V.SAFE_SIDE - bar_w))
    left = bar_l + (bar_w - width) / 2
    print(f'  receipt: scale {k:.2f} ({width:.0f} x {px(H):.0f} px), {len(lines)} lines, bar top at y {bar_y}, room {room} px')

    # when each row comes out: the header just before the first word, each line as its first word is said
    stops = [(max(.03, t_start - .2), px(RULE1 + 14), .24, 'power2.out')]
    t_prev, tok_k = stops[0][0], 0
    for i, line in enumerate(lines):
        t = times[tok_k] if tok_k < len(times) else None
        at = max(t[0] if t else t_start + (t_done - t_start) * i / len(lines), t_prev + (.27 if i == 0 else .2))
        stops.append((at, px(C_BODY + LH * i + 31), .11, 'power3.out'))
        t_prev = at
        tok_k += len(line.split())
    t_total = max(t_done - .1, t_prev + .25)
    stops.append((t_total, px(H), .11, 'power3.out'))
    t_tear = t_total + .11 + HOLD
    t_gone = t_tear + .25
    t_bar_out = t_gone + .3
    if t_bar_out + .12 > s.dur:
        print(f'  note: the slot ends at {s.dur:.2f}s and the effect needs until {t_bar_out + .12:.2f}s: make the slot longer (--to) or lower HOLD')

    p = V.Page(s)
    I = STYLE['paper_ink']
    p.css.append(f'''
.rc-bar{{position:absolute;left:{bar_l}px;top:{bar_y}px;width:{bar_w}px;height:{bar_h}px;border-radius:{px(14)}px;background:{STYLE["bar"]};
  box-shadow:inset 0 0 0 {px(2)}px {STYLE["bar_edge"]},0 {px(6)}px {px(16)}px rgba(0,0,0,.42)}}
.rc-bar i{{position:absolute;left:{px(26)}px;right:{px(26)}px;top:{px(22)}px;height:0;border-top:{px(4)}px dotted {STYLE["dots"]}}}
.rc-bar u{{position:absolute;left:{px(26)}px;top:{px(36)}px;width:{px(70)}px;height:{px(3)}px;border-radius:2px;background:{STYLE["dots"]};opacity:.42}}
.rc-bar b{{position:absolute;right:{px(20)}px;top:{px(32)}px;width:{px(11)}px;height:{px(11)}px;border-radius:50%;background:{STYLE["led"]}}}
.rc-clip{{position:absolute;left:0;top:0;width:1080px;height:{bar_y + slot_y}px;overflow:hidden;filter:drop-shadow(0 {px(3)}px {px(7)}px rgba(0,0,0,.22))}}
.rc-paper{{position:absolute;left:{left}px;top:{bar_y + slot_y}px;width:{width}px;height:{px(H)}px;background:{STYLE["paper"]};color:{I};
  clip-path:{teeth(width, px(H), px(35))};font-family:'{STYLE["font"]}';font-weight:{STYLE["weight"]};transform-origin:50% 100%}}
.rc-row{{position:absolute;left:{px(PAD)}px;right:{px(PAD)}px;display:flex;justify-content:space-between;align-items:center;white-space:pre;transform:translateY(-50%);line-height:1}}
.rc-rule{{position:absolute;left:{px(PAD)}px;right:{px(PAD)}px;height:0;border-top:{max(1.5, px(2))}px dashed {I}77}}''')
    stamp = s.t0 + t_start
    rows = [f'<div class="rc-row" style="top:{px(C_H1)}px;font-size:{px(SMALL)}px;font-weight:{STYLE["head_weight"]};letter-spacing:.13em">'
            f'<span>{V.esc(HEADER)}</span><span>{V.esc(NUMBER)}</span></div>',
            f'<div class="rc-row" style="top:{px(C_H2)}px;font-size:{px(SMALL2)}px;color:{STYLE["paper_dim"]};letter-spacing:.09em">'
            f'<span>{int(stamp // 60):02d}:{stamp % 60:05.2f}</span><span>{V.esc(TO)}</span></div>',
            f'<div class="rc-rule" style="top:{px(RULE1)}px"></div>']
    for i, line in enumerate(lines):
        rows.append(f'<div class="rc-row" style="top:{px(C_BODY + LH * i)}px;font-size:{px(FS)}px"><span>{V.esc(line)}</span></div>')
    rows.append(f'<div class="rc-rule" style="top:{px(rule2)}px"></div>')
    rows.append(f'<div class="rc-row" style="top:{px(c_total)}px;font-size:{px(SMALL + 1)}px;font-weight:{STYLE["head_weight"]};letter-spacing:.07em">'
                f'<span>{V.esc(TOTAL_LABEL)}</span><span>{V.esc(TOTAL_VALUE)}</span></div>')
    p.html.append('<div id="rcb" class="rc-bar"><i></i><u></u><b></b></div>')
    p.html.append(f'<div id="rcc" class="rc-clip"><div id="rcp" class="rc-paper">{"".join(rows)}</div></div>')

    p.enter('#rcb', max(0.0, stops[0][0] - .07), {}, {}, .1, ease='none')
    for at, shown, dur, ease in stops:
        p.js.append(f"tl.to('#rcp',{{y:{-shown},duration:{dur},ease:'{ease}'}},{V.T(at):.3f});")
        if SOUND:
            p.sound('click-soft', at, SOUND)
    # the tear, a quarter of a second in all: a tilt, a lift with the tilt swung back, then away up and to the right
    full = px(H)
    p.js.append(f"tl.to('#rcp',{{y:{-full - px(14)},rotation:-2.6,duration:.05,ease:'power2.out'}},{V.T(t_tear):.3f});")
    p.js.append(f"tl.to('#rcp',{{y:{-full - px(120)},x:{px(30)},rotation:1,duration:.07,ease:'sine.in'}},{V.T(t_tear) + .05:.3f});")
    p.js.append(f"tl.to('#rcp',{{y:{-bar_y - full - 120},x:{px(420)},rotation:7,duration:.14,ease:'power1.in'}},{V.T(t_tear) + .12:.3f});")
    p.js.append(f"tl.to('#rcb',{{autoAlpha:0,duration:.12,ease:'none'}},{V.T(t_bar_out):.3f});")
    if SOUND:
        p.sound('click', t_tear, SOUND)
        p.sound('whoosh-short', t_tear + .06, SOUND * .7)
    print(f'  prints {t_start:.2f}s to {t_total:.2f}s, tears at {t_tear:.2f}s, gone at {t_gone:.2f}s, bar out at {t_bar_out + .12:.2f}s')
    p.write()
    print(f'snapshot at: {stops[0][0] + .25:.2f},{stops[1][0] + .15:.2f},{t_total + .2:.2f},{t_tear + .04:.2f},{t_tear + .1:.2f},{t_tear + .17:.2f},{t_gone + .1:.2f}')


if __name__ == '__main__':
    main()
