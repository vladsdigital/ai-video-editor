#!/usr/bin/env python3
"""IRIS CARD: an iris closes on the speaker's face to black, a framed title card opens out of the black and sets the
line word by word as it is said, then the iris reopens through the card onto the speaker.

The iris follows the head measured on every frame (headtrack.py, from the cutout; layout.json's numbers without one).
An overlay effect: the reel's own footage stays under the transparent parts.

    build.py      writes index.html   (SAFE=1 safe-zone guide with footage, PREVIEW=1 footage only, SFX=0 no sounds)
"""
import random

import headtrack
import vgfx as V

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    font='EB Garamond',       # the upper lines. Set to a family in assets/fonts/fonts.css, and font_file to None
    font_file='fonts/EBGaramond-400-normal.woff2',
    weight=400,
    big_font='EB Garamond',   # the last words, large
    big_file='fonts/EBGaramond-400-italic.woff2',
    big_italic=True,
    case='as-said',           # 'as-said', 'lower' or 'upper'
    ink='#EDEEDF',            # the words
    line='#CFDCCE',           # the frame and its ornaments
    ground='#1C3729',         # the card
    black='#101010',          # what the iris closes to
    dust=True,                # specks and hairline scratches flickering on the card
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
LINE = ''           # the words the card sets, exactly as spoken, in order. Required.
BIG = 2             # how many of the last words go large on their own line under the rule. 0 = no large line
T_CLOSE = None      # slot second the iris starts closing. None = so the card is open when the first word of LINE is said
T_OPEN = None       # slot second the iris starts reopening. None = just after the last word of LINE, or as late as still fits
LINE_PX = 100       # size of the upper lines (longer lines get smaller by themselves)
BIG_PX = 138        # size of the large line
SOUND = 0.0         # volume of a soft whoosh on the close. 0 = silent
# ==== END CLIP ====

W, H = 1080, 1920
# the frame: x 99 to 981, y 336 to 1401
BOX = (99, 336, 882, 1065)
CARD_ORIGIN = (540, 874)         # where the card opens from
# iris radius by frame from the start of the close, as a multiple of the radius that holds on the head
CLOSE = [None, 2.7, 2.0, 1.3, 1.0, 1.0, .98, .96, .57, 0]
# the card opening out of the black, then the iris reopening, by frame, as a share of the frame width
CARD_OPEN = [.075, .23, .5, .85, 1.4]
REOPEN = [.045, .1, .22, .36, .5, .73, 1.4]
FR = 1 / 30


def match(s, line):
    """the slot's words that make up LINE, in order, or stop with the reason"""
    said, out, at = line.split(), [], 0
    for tok in said:
        key = V.bare(tok).lower()
        for i in range(at, len(s.words)):
            if V.bare(s.words[i]['text']).lower() == key:
                out.append(s.words[i])
                at = i + 1
                break
        else:
            V.die(f'"{tok}" of LINE is not said in this slot. Words here: {s.word_list()}')
    return out


def wrap(words, px, width):
    """greedy lines, near even, for a serif about .44 em a letter"""
    size = px
    while size > 58:
        total = sum((len(w) + 1) * .44 * size for w in words)
        lines = max(1, round(total / width + .35))
        if max(len(w) * .44 * size for w in words) <= width and lines <= 4:
            break
        size -= 4
    goal = sum(len(w) + 1 for w in words) / lines
    out, cur, n = [], [], 0
    for w in words:
        if cur and n + len(w) * .5 > goal and len(out) < lines - 1:
            out.append(cur)
            cur, n = [], 0
        cur.append(w)
        n += len(w) + 1
    return out + [cur], size


def main():
    s = V.Slot()
    s.dur = int(s.frames / 30 * 10000) / 10000     # rounded down: a duration rounded up renders one frame too many
    print('words: ' + s.word_list())
    if not LINE.strip():
        V.die('write LINE in the CLIP block: the words the card sets, as spoken')
    said = match(s, LINE)
    head = headtrack.track(s)
    print(('head: measured on every frame' if head['measured'] else 'head: no cutout, so the per-shot numbers of layout.json')
          + f", {head['width']:.0f} x {head['height']:.0f} px")
    hold = min(470.0, max(110.0, head['height'] / 2 * 1.24))
    open_at = said[0]['start'] - (len(CARD_OPEN) - 2) * FR       # the card's circle is most of the way open on the first word
    t_close = T_CLOSE if T_CLOSE is not None else open_at - (len(CLOSE) + 1) * FR
    if t_close < 0:
        V.die(f'the slot starts too late: make --from at least {-t_close + .05:.2f}s earlier, the iris needs that time to close')
    f_close = round(t_close * 30)
    f_black = f_close + len(CLOSE) - 1
    f_card = f_black + 2
    last_end = said[-1]['end']
    t_open = T_OPEN if T_OPEN is not None else min(last_end + .02, s.dur - (len(REOPEN) + .5) * FR)
    if t_open < said[-1]['start'] + .1:
        V.die(f'the slot ends too soon: the iris needs {len(REOPEN) / 30:.2f}s after the last word. Make --to later')
    f_open = round(t_open * 30)
    f_clear = f_open + len(REOPEN)

    upper = [w['text'] for w in said[:len(said) - BIG]] if BIG else [w['text'] for w in said]
    lower = [w['text'] for w in said[len(said) - BIG:]] if BIG else []
    last = lower if lower else upper                  # a line cut from a longer sentence does not end on a comma
    last[-1] = last[-1].rstrip(',;:')
    lines, px = wrap(upper, LINE_PX, 730)
    big_px = BIG_PX
    n_big = sum(len(w) + 1 for w in lower)
    if lower and n_big * .4 * big_px > 790:
        big_px = int(790 / (n_big * .4))
    p = V.Page(s)
    S = STYLE
    faces = ''
    if S.get('font_file'):
        faces += f"@font-face{{font-family:'{S['font']}';font-weight:{S['weight']};src:url('{S['font_file']}') format('woff2');font-display:block}}\n"
    if S.get('big_file'):
        faces += (f"@font-face{{font-family:'{S['big_font']}';font-style:{'italic' if S['big_italic'] else 'normal'};font-weight:{S['weight']};"
                  f"src:url('{S['big_file']}') format('woff2');font-display:block}}\n")
    top = 650 - max(0, len(lines) - 2) * 72 + (72 if not lower else 0)
    p.css.append(faces + f'''
#cov{{position:absolute;inset:0;--x:0px;--y:0px;--r:0px;
  -webkit-mask-image:radial-gradient(circle at var(--x) var(--y),transparent calc(var(--r) - 1px),#000 var(--r));
  mask-image:radial-gradient(circle at var(--x) var(--y),transparent calc(var(--r) - 1px),#000 var(--r))}}
#blk{{position:absolute;inset:0;background:{S['black']}}}
#card{{position:absolute;inset:0;background:{S['ground']};--c:0px;
  -webkit-mask-image:radial-gradient(circle at {CARD_ORIGIN[0]}px {CARD_ORIGIN[1]}px,#000 calc(var(--c) - 1px),transparent var(--c));
  mask-image:radial-gradient(circle at {CARD_ORIGIN[0]}px {CARD_ORIGIN[1]}px,#000 calc(var(--c) - 1px),transparent var(--c))}}
#card svg{{position:absolute;left:0;top:0}}
.ln{{position:absolute;left:0;width:1080px;text-align:center;color:{S['ink']};white-space:pre;font-family:'{S['font']}';font-weight:{S['weight']};
  font-size:{px}px;line-height:1;letter-spacing:-.005em}}
.bg{{position:absolute;left:0;width:1080px;text-align:center;color:{S['ink']};white-space:pre;font-family:'{S['big_font']}';font-weight:{S['weight']};
  font-style:{'italic' if S['big_italic'] else 'normal'};font-size:{big_px}px;line-height:1}}
.ch{{opacity:0}}
.dust{{position:absolute;inset:0;visibility:hidden}}
.dust i{{position:absolute;display:block;background:{S['ink']}}}''')
    # ---- card contents
    x, y, w, h = BOX
    i_x, i_y, i_w, i_h = x + 15, y + 15, w - 30, h - 30
    notch = 26
    inner = (f'M{i_x + notch} {i_y}H{i_x + i_w - notch}A{notch} {notch} 0 0 0 {i_x + i_w} {i_y + notch}V{i_y + i_h - notch}'
             f'A{notch} {notch} 0 0 0 {i_x + i_w - notch} {i_y + i_h}H{i_x + notch}A{notch} {notch} 0 0 0 {i_x} {i_y + i_h - notch}'
             f'V{i_y + notch}A{notch} {notch} 0 0 0 {i_x + notch} {i_y}Z')
    dots = [(x + w / 2, y), (x + w / 2, y + h)] + [(a, b) for a in (i_x + 15, i_x + i_w - 15) for b in (i_y + 15, i_y + i_h - 15)]
    def diamond(cx, cy, r=6):
        return f'<path d="M{cx} {cy - r}L{cx + r} {cy}L{cx} {cy + r}L{cx - r} {cy}Z" fill="{S["line"]}"/>'
    per = 2 * (w + h)
    svg = (f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect id="fo" x="{x}" y="{y}" width="{w}" height="{h}" fill="none" '
           f'stroke="{S["line"]}" stroke-width="2.6" stroke-dasharray="{per}" stroke-dashoffset="{per}"/>'
           f'<g id="fi" style="opacity:0"><path d="{inner}" fill="none" stroke="{S["line"]}" stroke-width="2"/>'
           + ''.join(diamond(a, b) for a, b in dots) + '</g>')
    # ---- the words, laid out with every letter in place from the start so nothing reflows
    t = top
    html, words_at = [], []
    k = 0
    for ln in lines:
        spans = []
        for word in ln:
            chars = ''.join(f'<span class="ch" id="c{k}x{j}">{V.esc(c)}</span>' for j, c in enumerate(V.cased(word, S['case'])))
            spans.append(chars)
            words_at.append((k, len(word), said[k]['start']))
            k += 1
        html.append(f'<div class="ln" style="top:{t - px // 2}px">{" ".join(spans)}</div>')
        t += int(px * 1.29)
    rule_y = t - int(px * 1.29) + int(px * .98)
    if lower:
        svg += (f'<g id="ru" style="opacity:0"><path d="M{540 - 150} {rule_y}H{540 - 18}M{540 + 18} {rule_y}H{540 + 150}" stroke="{S["line"]}" stroke-width="2"/>'
                + diamond(540, rule_y) + '</g>')
        spans = []
        for word in lower:
            spans.append(''.join(f'<span class="ch" id="c{k}x{j}">{V.esc(c)}</span>' for j, c in enumerate(V.cased(word, S['case']))))
            words_at.append((k, len(word), said[k]['start']))
            k += 1
        html.append(f'<div class="bg" style="top:{rule_y + 156 - big_px // 2}px">{" ".join(spans)}</div>')
    svg += '</svg>'
    dust = ''
    rng = random.Random(7)
    groups = 6
    if S.get('dust'):
        for g in range(groups):
            bits = ''
            for _ in range(9):
                a, b = rng.randrange(20, 1060), rng.randrange(20, 1900)
                d = rng.choice((2, 2, 3, 4))
                bits += f'<i style="left:{a}px;top:{b}px;width:{d}px;height:{d}px;opacity:{rng.uniform(.18, .5):.2f};border-radius:50%"></i>'
            if g % 2 == 0:
                a, b = rng.randrange(40, 1040), rng.randrange(0, 900)
                bits += f'<i style="left:{a}px;top:{b}px;width:1px;height:{rng.randrange(300, 900)}px;opacity:.1"></i>'
            dust += f'<div class="dust" id="du{g}">{bits}</div>'
    p.html.append(f'<div id="cov"><div id="blk"></div><div id="card">{dust}{svg}{"".join(html)}</div></div>')
    # ---- the timeline: everything is set frame by frame, so the render is exact and the iris stays on the head
    js = p.js
    js.append("gsap.set('#cov',{autoAlpha:0});")
    far = 2300
    def setcov(f, r):
        fi = min(s.frames - 1, max(0, f))
        js.append(f"tl.set('#cov',{{'--x':'{head['cx'][fi]:.1f}px','--y':'{head['cy'][fi]:.1f}px','--r':'{r:.1f}px'}},{V.T(f * FR):.3f});")
    js.append(f"tl.set('#cov',{{autoAlpha:1}},{V.T(f_close * FR):.3f});")
    for n, m in enumerate(CLOSE):
        setcov(f_close + n, far if m is None else m * hold)
    for n, r in enumerate(CARD_OPEN):
        js.append(f"tl.set('#card',{{'--c':'{r * W:.1f}px'}},{V.T((f_card + n) * FR):.3f});")
    js.append(f"tl.set('#card',{{'-webkit-mask-image':'none','mask-image':'none'}},{V.T((f_card + len(CARD_OPEN)) * FR):.3f});")
    # the frame runs clockwise round the card from its top left in 10 frames, the inner line and ornaments come after
    f_draw = f_card + 2
    for n in range(11):
        js.append(f"tl.set('#fo',{{attr:{{'stroke-dashoffset':{per * (1 - n / 10):.1f}}}}},{V.T((f_draw + n) * FR):.3f});")
    js.append(f"tl.to('#fi',{{opacity:1,duration:{4 * FR:.3f},ease:'none'}},{V.T((f_draw + 10) * FR):.3f});")
    if lower:
        t_rule = max(said[len(said) - BIG - 1]['end'] - .02, (f_draw + 6) * FR)
        js.append(f"tl.to('#ru',{{opacity:1,duration:{5 * FR:.3f},ease:'none'}},{V.T(t_rule):.3f});")
    # each word comes in letter by letter, from a dim grey to full, over 8 frames for a short word
    for idx, n, at in words_at:
        step = min(.03, .28 / max(1, n))
        at = max(at, f_card * FR)
        for j in range(n):
            js.append(f"tl.to('#c{idx}x{j}',{{opacity:1,duration:.14,ease:'none'}},{at + j * step:.3f});")
    if S.get('dust'):
        f = f_card
        while f < f_clear:
            g = f // 2 % groups
            js.append(f"tl.set('#du{g}',{{visibility:'visible'}},{V.T(f * FR):.3f});tl.set('#du{g}',{{visibility:'hidden'}},{V.T((f + 2) * FR):.3f});")
            f += 2
    setcov(f_black, 0)
    for n, r in enumerate(REOPEN):
        setcov(f_open + n, r * W)
    if f_clear < s.frames:
        js.append(f"tl.set('#cov',{{autoAlpha:0}},{V.T(f_clear * FR):.3f});")
    js.append(f"tl.set('#blk',{{autoAlpha:0}},{V.T((f_card + len(CARD_OPEN)) * FR):.3f});")
    if SOUND:
        p.sound('whoosh-short', (f_close + 3) * FR, SOUND)
    print(f'  iris closes {f_close * FR:.2f}s, black {f_black * FR:.2f}s, card from {f_card * FR:.2f}s, reopens {f_open * FR:.2f}s, clear {f_clear * FR:.2f}s; hold radius {hold:.0f}px')
    if f_clear > s.frames:
        print(f'  !! the iris is still opening at the slot end ({f_clear} of {s.frames} frames): make --to later or T_OPEN earlier')
    p.write()
    picks = [f_close + 1, f_close + 5, f_card + 2, f_card + 9, (f_card + f_open) // 2, f_open - 2, f_open + 3]
    print('snapshot at: ' + ','.join(f'{(f + .5) * FR:.3f}' for f in picks))
    s.hide_hint([(f_close * FR, min(s.dur, f_clear * FR))])


if __name__ == '__main__':
    main()
