#!/usr/bin/env python3
"""SCRIPT PAGE: cream paper rises over the shot and the reel becomes a screenplay page in typewriter type, built from
the speaker's own lines. It drifts up slowly while a marker highlights each word as it is said.

An overlay effect: the page is opaque, the reel's own footage comes back when it leaves. Reads the reel's words.json
and segments.json for the lines around this one, or the slot's own words outside a reel.

    build.py      writes index.html   (SAFE=1 safe-zone guide with footage, PREVIEW=1 footage only, SFX=0 no sounds)
"""
import json
import os

import vgfx as V

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    font='Courier Prime',         # typewriter face. A family from assets/fonts/fonts.css: set font_file and bold_file to None
    font_file='fonts/CourierPrime-400-normal.woff2',
    bold_file='fonts/CourierPrime-700-normal.woff2',
    paper='#F0ECDF',
    said='#A5A093',               # lines before and after the current one
    slug='#6C685E',               # scene headings
    ink='#111111',                # the current words
    mark='#B5D6BC',               # the marker (a light shade of the effect colour)
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
NAME = ''               # character name over the dialogue. Required (the buyer's name, as they would write it)
PAREN = '(to camera)'   # direction under the name. '' = none. Write it in the reel's language
SCENE = 'INT. OFFICE - DAY'   # scene heading of the current block, in the reel's language
SCENE_NEXT = 'INT. OFFICE - CONTINUOUS'   # scene heading after it
CUT_LABEL = 'CUT TO:'   # the transition line, in the reel's language
T_IN = None             # slot second the page starts rising. None = 0.1 s before the first word said in the slot
T_OUT = None            # slot second it starts leaving. None = after the last word, or stays to the slot end when that is a cut
SIZE = 41               # type size, px (one character is .6 of it)
COLUMN = 25             # letters per dialogue line
DRIFT = 16              # how fast the page rises, px a second
SOUND = 0.0             # volume of a soft whoosh when the page comes in. 0 = silent
# ==== END CLIP ====

FR = 1 / 30
# how far the paper's top edge still is from the top of the frame, by frame, as a share of the height
RISE = [.47, .2, .07, .02, 0]


def wrap(words, col):
    lines, cur, n = [], [], 0
    for w in words:
        if cur and n + 1 + len(w['text']) > col:
            lines.append(cur)
            cur, n = [], 0
        n += len(w['text']) + (1 if cur else 0)
        cur.append(w)
    return lines + ([cur] if cur else [])


def around(s):
    """from the reel: the last clause of the line before, the words of this line already said when the slot starts,
    the words of this line after the slot ends, the first sentence of the next line"""
    proj = s.clip.get('project')
    if not proj:
        return [], [], [], []
    try:
        all_w = json.load(open(os.path.join(proj, 'words.json'), encoding='utf-8'))
        segs = json.load(open(os.path.join(proj, 'segments.json'), encoding='utf-8'))
    except (OSError, ValueError):
        return [], [], [], []
    t0, t1 = s.t0, s.t0 + s.dur
    def pick(g):
        a, b = g['frame'] / 30, (g['frame'] + g['frames']) / 30
        return [{'text': w['text'], 'start': 0, 'end': 0, 't': w['start']} for w in all_w if a - .12 <= w['start'] < b - .12]      # a word that starts on the cut belongs to the shot after it
    here = next((i for i, g in enumerate(segs) if g['frame'] / 30 <= t0 + .03 < (g['frame'] + g['frames']) / 30), None)
    if here is None:
        return [], [], [], []
    line = pick(segs[here])
    before = [w for w in line if w['t'] < t0 - .02]
    after = [w for w in line if w['t'] >= t1 - .02]
    prev = pick(segs[here - 1]) if here else []
    start = 0
    for i, w in enumerate(prev[:-1]):                    # the last clause, at most 12 words
        if w['text'][-1] in ',.:;!?' and len(prev) - i - 1 >= 2:
            start = i + 1
    prev = prev[max(start, len(prev) - 12):]
    nxt = pick(segs[here + 1]) if here + 1 < len(segs) else []
    for i, w in enumerate(nxt):                          # the first sentence, at most 14 words
        if w['text'][-1] in '.!?':
            nxt = nxt[:i + 1]
            break
    return prev, before, after, nxt[:14]


def main():
    s = V.Slot()
    s.dur = int(s.frames / 30 * 10000) / 10000     # rounded down: a duration rounded up renders one frame too many
    print('words: ' + s.word_list())
    if not NAME.strip():
        V.die('write NAME in the CLIP block: the character name over the dialogue')
    if not s.words:
        V.die('no words in this slot: the page is made of what the speaker says')
    S = STYLE
    prev, before, after, nxt = around(s)
    s.words = [w for w in s.words if w['start'] < s.dur - .12]      # a word starting on the slot's end belongs to the next shot
    first = next((w for w in s.words if w['start'] > .02), s.words[0])
    s.words = s.words[s.words.index(first):]
    t_in = T_IN if T_IN is not None else max(0.0, s.words[0]['start'] - .1)
    t_out = T_OUT if T_OUT is not None else (s.words[-1]['end'] + .05 if s.words[-1]['end'] + .05 + 6 * FR < s.dur - FR else None)
    f_in = round(t_in * 30)
    line_h = round(SIZE * 1.03)
    ch = SIZE * .6
    faces = ''
    if S.get('font_file'):
        faces = (f"@font-face{{font-family:'{S['font']}';font-weight:400;src:url('{S['font_file']}') format('woff2');font-display:block}}\n"
                 f"@font-face{{font-family:'{S['font']}';font-weight:700;src:url('{S['bold_file']}') format('woff2');font-display:block}}\n")
    d_left = 240                                    # dialogue column; headings further left, the transition right
    p = V.Page(s)
    p.css.append(faces + f'''
#pg{{position:absolute;inset:0;background:{S['paper']};overflow:hidden;will-change:transform}}
#tx{{position:absolute;left:0;top:0;width:1080px;font-family:'{S['font']}';font-size:{SIZE}px;line-height:{line_h}px;white-space:pre;color:{S['said']}}}
.r{{position:absolute;white-space:pre}}
.w{{position:relative;display:inline-block}}
.w .m{{position:absolute;left:-2px;top:0;height:{line_h}px;width:calc(100% + 4px);background:{S['mark']};transform-origin:0 50%;transform:scaleX(0)}}
.w .t{{position:relative}}
.g{{color:{S['ink']}}}''')
    rows, y = [], 0
    def row(text, x, colour=None, center=False, right=False):
        nonlocal y
        st = f'top:{y}px;'
        if center:
            st += 'left:0;width:1080px;text-align:center;'
        elif right:
            st += f'right:{1080 - 840}px;'
        else:
            st += f'left:{x}px;'
        if colour:
            st += f'color:{colour};'
        rows.append(f'<div class="r" style="{st}">{text}</div>')
        y += line_h
    def gap(n=1):
        nonlocal y
        y += round(line_h * n)
    # the line before
    for ln in wrap(prev, COLUMN):
        row(V.esc(' '.join(w['text'] for w in ln)), d_left)
    if prev:
        gap(.72)
        row(V.esc(CUT_LABEL), 0, right=True)
        gap(.5)
    row(V.esc(SCENE), 138, S['slug'])
    gap(.68)
    y0_dialog = y
    row(V.esc(NAME.upper()), 0, S['ink'], center=True)
    if PAREN:
        row(V.esc(PAREN), 0, S['ink'], center=True)
    # the current words: every one a span with its marker behind it
    spoken = wrap(before + s.words + after, COLUMN)
    k = 0
    current_y = y
    live = set(id(w) for w in s.words)
    for ln in spoken:
        parts = []
        for j, w in enumerate(ln):
            if id(w) in live:
                wide = '' if j == len(ln) - 1 else ' style="width:calc(100% + .6em)"'      # the marker bridges the space to the next word
                parts.append(f'<span class="w" id="w{k}"><span class="m" id="m{k}"{wide}></span><span class="t g">{V.esc(w["text"])}</span></span>')
                w['_k'] = k
                k += 1
            elif w in after:
                parts.append(f'<span class="g">{V.esc(w["text"])}</span>')
            else:
                parts.append(V.esc(w['text']))
        row(' '.join(parts), d_left)
    y_mid = (current_y + y) / 2
    gap(.72)
    row(V.esc(CUT_LABEL), 0, S['ink'], right=True)
    gap(.5)
    row(V.esc(SCENE_NEXT), 138, S['slug'])
    gap(.68)
    row(V.esc(NAME.upper()), 0, center=True)
    for ln in wrap(nxt, COLUMN):
        row(V.esc(' '.join(w['text'] for w in ln)), d_left)
    # the current lines sit a little above the middle of the safe zone when the words start
    end_f = s.frames if t_out is None else round(t_out * 30) + 6
    y_top = 880 - y_mid
    p.html.append(f'<div id="pg"><div id="tx" style="height:{y}px">{"".join(rows)}</div></div>')
    if y_top + current_y < 230 + 40:
        print(f'  note: {len(spoken)} dialogue lines start high on the page; a shorter slot keeps them centred')
    if y_top + (current_y + line_h * len(spoken)) > 1460:
        V.die(f'{len(spoken)} dialogue lines do not fit the safe zone at this size: make the slot shorter or SIZE smaller')
    # ---- the timeline, frame by frame
    js = p.js
    js.append("gsap.set('#pg',{autoAlpha:0});")
    js.append(f"tl.set('#pg',{{autoAlpha:1}},{V.T(f_in * FR):.3f});")
    for n, r in enumerate(RISE):
        js.append(f"tl.set('#pg',{{y:{r * 1920:.1f}}},{V.T((f_in + n) * FR):.3f});")
    js.append(f"tl.set('#tx',{{y:{y_top:.1f}}},{V.T(f_in * FR):.3f});")
    js.append(f"tl.to('#tx',{{y:{y_top - DRIFT * (s.dur - f_in * FR):.1f},duration:{s.dur - f_in * FR - FR:.3f},ease:'none'}},{f_in * FR:.3f});")
    for w in s.words:
        i, a, b = w['_k'], w['start'], max(w['end'], w['start'] + .1)
        js.append(f"tl.fromTo('#m{i}',{{scaleX:0}},{{scaleX:1,duration:{b - a:.3f},ease:'none',immediateRender:false}},{a:.3f});")
    if t_out is not None:
        f_out = round(t_out * 30)
        for n, r in enumerate((.02, .07, .2, .47, .8, 1.0)):      # it leaves the way it came, out at the top
            js.append(f"tl.set('#pg',{{y:{-r * 1920:.1f}}},{V.T((f_out + n) * FR):.3f});")
        js.append(f"tl.set('#pg',{{autoAlpha:0}},{V.T((f_out + 6) * FR):.3f});")
    if SOUND:
        p.sound('whoosh-short', f_in * FR, SOUND)
    print(f'  page in {f_in * FR:.2f}s, ' + (f'out {t_out:.2f}s' if t_out is not None else 'stays to the slot end (keep that a cut)') + f', {len(spoken)} dialogue lines')
    p.write()
    a, b = s.words[0]['start'], s.words[-1]['end']
    print('snapshot at: ' + ','.join(f'{t:.3f}' for t in ((f_in + 1.5) * FR, a + .25, (a + b) / 2, b - .1)))
    s.hide_hint([(f_in * FR, min(s.dur, end_f * FR))])


if __name__ == '__main__':
    main()
