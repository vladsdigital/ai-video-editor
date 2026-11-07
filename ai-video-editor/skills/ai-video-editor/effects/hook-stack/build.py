#!/usr/bin/env python3
"""HOOK STACK (the whole opening): the first line lands letter by letter in a big serif behind the head, the room flips
to a solid forest green backdrop behind the cutout on the second line, heavy sans lines push through a tight two-line
stack word by word with a small running timecode, then a serif italic line lands with a coloured last word, and the
room cuts back.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html   (SAFE=1 safe-zone guide, SFX=0 no sounds,
                                               CAPTIONS=0 no small plate captions: the reel's own captions run instead)
"""
import os

import vgfx as V

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    serif_font='Instrument Serif',   # the first two lines, and the italic line
    serif_file='InstrumentSerif-400-normal.woff2',
    italic_file='InstrumentSerif-400-italic.woff2',
    serif_stretch=1.24,              # the serif is drawn this much taller than wide, a tall display cut
    heavy_font='Inter Tight',        # the stack
    heavy_file='InterTight-900-normal.woff2',
    heavy_weight=900,
    heavy_tracking=-0.055,           # em
    mono_font='JetBrains Mono',      # the timecode
    plate_font='Instrument Serif',   # the small captions on their plate
    backdrop='#1A3829',              # the solid backdrop behind the cutout (deep forest green)
    ink='#F3EFE2',                   # words (cream paper)
    accent='#0C1C15',                # the last word of the italic line, and the timecode's frames (nearly black, holds on any backdrop)
    dim='#12241B',                   # the words not said yet on the plate, and the timecode's zeros (a dark shade of the backdrop)
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
# Every line is the speaker's own words, in the order said. Each one starts when its first word is said
# (the word is looked up in words.json from the previous line on), or at the second you put in TIMES.
SERIF = ['ELON MUSK', 'NAPRAVIO']          # two lines, capitals. The second one flips the room to the backdrop
STACK = [('LETEĆI', 'AUTOMOBIL'),          # (top line, bottom line) pairs of the heavy stack, 1 to 3 pairs. Capitals
         ('A TI I DALJE', 'IMAŠ')]
ITALIC = ('sajt iz', '2010.')              # the landing line: (first words, last word in the accent colour)
TIMES = {}                                 # optional, slot seconds, by the line's text: {'IMAŠ': 2.80}
KEEP = []                                  # real picture kept behind the speaker on the backdrop (the desk they sit at):
                                           # a list of (x, y) px, closed along the frame's bottom. Still camera only. [] = backdrop everywhere
KEEP_FRONT = []                            # the same, but in front of the speaker (a laptop or a mic stand they sit behind)
T_OUT = None                               # slot second the room cuts back. None = the slot's end (end it on a cut)
PUNCH = 1.12                               # the speaker jumps this much closer on the coloured last word. 1 = off
PLATE_Y = 1360                             # centre of the small caption plate
SOUND = 0.34                               # the low hit under the italic line. 0 = silent
# ==== END CLIP ====

F = 1 / 30
TOP = V.SAFE_TOP + 6          # highest ink
MIN_HEAD_TOP, MAX_SHIFT = 470, 240     # the head has to start this low for the lines; the most the speaker may move down for it


def font_of(fname, size=1000):
    from PIL import ImageFont
    path = os.path.join('assets/fonts', fname)
    if not os.path.exists(path):
        V.die(f'{fname} is not in assets/fonts: set a font of the slot in the STYLE block')
    f = ImageFont.truetype(path, size)
    try:                                       # a variable file measures at its default weight otherwise
        axes = f.get_variation_axes()
        wg = STYLE['heavy_weight'] if fname == STYLE['heavy_file'] else 400
        f.set_variation_by_axes([wg if k == 0 else a['default'] for k, a in enumerate(axes)])
    except OSError:
        pass
    return f


def ink(fname, text, track=0.0):
    """(width, height above the baseline, height under it) of the text at font size 1"""
    f = font_of(fname)
    box = f.getbbox(text, anchor='ls')
    wide = .12 * text.count(' ') if track else 0.0      # the stack's word gaps are drawn wider than the font's own
    return (f.getlength(text) / 1000 + track * len(text) + wide, -box[1] / 1000, max(0, box[3]) / 1000)


def fit(fname, text, width, track=0.0, max_size=9999):
    return min(max_size, width / ink(fname, text, track)[0])


def letters(text, cls, pid):
    out = []
    for k, c in enumerate(text):
        out.append(f'<span id="{pid}c{k}" class="sp">&nbsp;</span>' if c == ' ' else f'<span id="{pid}c{k}" class="{cls}">{V.esc(c)}</span>')
    return ''.join(out)


def main():
    s = V.Slot()
    print('words: ' + s.word_list())
    print(s.where())
    V.PREVIEW = True          # this effect replaces the room: the slot's footage is always under it
    if len(SERIF) != 2 or not 1 <= len(STACK) <= 3 or len(ITALIC) != 2:
        V.die('SERIF takes 2 lines, STACK 1 to 3 pairs, ITALIC a pair')
    if not os.path.exists('assets/subject.webm'):
        V.die('this effect stands the speaker in front of a backdrop: it needs the clean cutout (setup.py --matting)')
    # little headroom: the speaker is moved down on the backdrop to make it, and the backdrop is up from the first line
    shift = max(0, MIN_HEAD_TOP - s.head_top)
    if shift > MAX_SHIFT:
        V.die(f'the head starts at y {s.head_top}: too high to make room for the lines. It needs a wide or medium shot')
    if shift and KEEP + KEEP_FRONT:
        V.die('KEEP needs the speaker to stay in place, and this clip has too little headroom for that: empty KEEP and KEEP_FRONT')
    head_top, chin = s.head_top + shift, s.chin + shift
    S = STYLE
    plate_on = V.env('CAPTIONS', '1') != '0'

    # ---- when
    cursor = 0.0

    def when(text, gap=.0):
        nonlocal cursor
        if text in TIMES:
            cursor = float(TIMES[text])
            return cursor
        first = V.bare(text.split()[0]).lower()
        w = next((w for w in s.words if w['start'] >= cursor - .01 and V.bare(w['text']).lower() == first), None)
        if not w:
            V.die(f'"{text}": its first word is not said in this slot after {cursor:.2f}s. Fix the line or put it in TIMES')
        cursor = w['start'] + .02
        return max(0.0, w['start'] - gap)

    t_a = when(SERIF[0], .03)
    t_b = when(SERIF[1], .03)
    t_pairs = [(when(a, .03), when(b, .03)) for a, b in STACK]
    t_i1 = when(ITALIC[0], .03)
    t_i2 = when(ITALIC[1], .03)
    t_out = T_OUT if T_OUT is not None else s.dur
    if not t_a < t_b < t_pairs[0][0] < t_i1 < t_i2 < t_out:
        V.die('the lines are out of order in time: check the words and TIMES')

    # ---- sizes, all measured: the heavy stack and the serif sit between the top of the safe zone and the head
    room = head_top + 70
    sy = S['serif_stretch']
    sf, hf, itf = S['serif_file'], S['heavy_file'], S['italic_file']
    tr = S['heavy_tracking']
    fs_a = fit(sf, SERIF[0], 850, max_size=290)
    base_a = TOP + ink(sf, SERIF[0])[1] * fs_a * sy
    fs_b = fit(sf, SERIF[1], 860)
    cap_b = ink(sf, SERIF[1])[1]
    fs_b = min(fs_b, (room + 70 - base_a - 6) / (cap_b * sy))
    base_b = base_a + 6 + cap_b * fs_b * sy
    # heavy: every line fits the width, bottom line a bit bigger, both stopped by the head
    h_up = max(ink(hf, a)[1] for a, _ in STACK)
    h_lo = max(ink(hf, b)[1] for _, b in STACK)
    size_top = [fit(hf, a, 850, tr, 215) for a, _ in STACK]
    size_bot = [fit(hf, b, 960, tr, 250) for _, b in STACK]
    top_h = max(ink(hf, a)[1] * z for (a, _), z in zip(STACK, size_top))
    bot_h = max(ink(hf, b)[1] * z for (_, b), z in zip(STACK, size_bot))
    squeeze = min(1.0, (room - TOP - 12) / (top_h + bot_h))
    size_top = [z * squeeze for z in size_top]
    size_bot = [z * squeeze for z in size_bot]
    base_1 = TOP + top_h * squeeze
    base_2 = base_1 + 12 + bot_h * squeeze
    # italic: rests on top of the head after the punch
    punch_top = chin - (chin - head_top) * PUNCH
    full = ITALIC[0] + ' ' + ITALIC[1]
    fs_i = fit(itf, full, 985, max_size=250)
    i_w0, i_up, i_dn = ink(itf, ITALIC[0])
    base_i = punch_top - 10 - i_dn * fs_i
    if base_i - i_up * fs_i < TOP - 4:
        fs_i *= (punch_top - 10 - TOP) / ((i_up + i_dn) * fs_i)
        base_i = punch_top - 10 - i_dn * fs_i
    i_full = ink(itf, full)[0] * fs_i
    i_w1 = font_of(itf).getlength(ITALIC[0] + ' ') / 1000 * fs_i
    i_w0 = font_of(itf).getlength(ITALIC[0]) / 1000 * fs_i
    x_i0 = 540 - i_full / 2                       # where the whole line starts
    x_solo = 540 - i_w0 / 2                       # the first words alone, centred

    p = V.Page(s)
    p.css.append(f'''
#green{{position:absolute;inset:0;background:{S['backdrop']}}}
.lay{{position:absolute;left:0;top:0;width:1080px}}
.mask{{position:absolute;left:0;width:1080px;overflow:hidden}}
.ln{{position:absolute;white-space:pre;line-height:1;color:{S['ink']}}}
.ln span{{display:inline-block;will-change:transform,opacity}}
.sf{{font-family:'{S['serif_font']}';font-weight:400;letter-spacing:0}}
.hv{{font-family:'{S['heavy_font']}';font-weight:{S['heavy_weight']};letter-spacing:{tr}em}}
.hv .sp{{width:.3em}}
.keep{{position:absolute;left:0;top:0;width:1080px;height:1920px;object-fit:cover}}
.it{{font-family:'{S['serif_font']}';font-style:italic;font-weight:400}}
#fgw{{position:absolute;inset:0;transform-origin:{s.cx}px {s.chin}px}}
#fg{{position:absolute;left:0;top:0;width:1080px;height:1920px;object-fit:cover}}
#tc{{position:absolute;left:60px;font-family:'{S['mono_font']}';font-weight:500;font-size:33px;letter-spacing:.22em;line-height:1;color:{S['dim']};white-space:pre}}
#tc b{{font-weight:500;color:{S['ink']}}}
#tc i{{font-style:normal;color:{S['accent']}}}
.pl{{position:absolute;left:0;width:1080px;text-align:center;top:{PLATE_Y - 41}px}}
.pl div{{display:inline-block;padding:13px 20px 15px;background:{S['backdrop']};border-radius:3px;font-family:'{S['plate_font']}';font-size:47px;line-height:1;color:{S['dim']};white-space:pre}}''')

    def base_box(fname, size, baseline, x, cls, text, pid, stretch=1.0, extra=''):
        """one line of letters with its baseline at screen y `baseline`: top is found from the font's own metrics"""
        asc, dsc = font_of(fname, 1000).getmetrics()
        lh = 1.0 * size
        top = baseline - ((lh - (asc + dsc) / 1000 * size) / 2 + asc / 1000 * size) * 1
        bl = baseline - top
        st = f'left:{x:.1f}px;top:{top:.1f}px;font-size:{size:.1f}px;transform-origin:0 {bl:.1f}px;'
        if stretch != 1.0:
            st += f'transform:scaleY({stretch});'
        return f'<div id="{pid}" class="ln {cls}" style="{st}{extra}">{letters(text, "l", pid)}</div>', bl

    # ---- the layers, back to front: footage, backdrop, words, cutout, plate
    html_words = ['<div id="green"></div>']
    pair_top = base_1 + 8
    mask1 = (TOP - 4, max(base_a, base_1) + 8)            # the top line's window
    mask2 = (max(base_a, base_1) + 8, base_2 + 8)          # the bottom line's window

    def wa(fname, text, size, track=0.0):
        return font_of(fname).getlength(text) / 1000 * size + track * size * len(text)

    # serif lines (their own layer: they land, they do not live in the masks until they leave)
    a_h, _ = base_box(sf, fs_a, base_a - mask1[0], 540 - wa(sf, SERIF[0], fs_a) / 2, 'sf', SERIF[0], 'sa', sy)
    b_h, _ = base_box(sf, fs_b, base_b, 540 - wa(sf, SERIF[1], fs_b) / 2, 'sf', SERIF[1], 'sb', sy)
    # the top line of each pair
    tops, bots = [], []
    m1 = [f'<div id="m1" class="mask" style="top:{mask1[0]:.1f}px;height:{mask1[1] - mask1[0]:.1f}px">', a_h]
    for k, (a, _) in enumerate(STACK):
        h, _x = base_box(hf, size_top[k], base_1 - mask1[0], 60, 'hv', a, f't{k}')
        m1.append(h)
        tops.append(f'#t{k}')
    m1.append('</div>')
    m2 = [f'<div id="m2" class="mask" style="top:{mask2[0]:.1f}px;height:{mask2[1] - mask2[0]:.1f}px">']
    for k, (_, b) in enumerate(STACK):
        h, _x = base_box(hf, size_bot[k], base_2 - mask2[0], 60, 'hv', b, f'b{k}')
        m2.append(h)
        bots.append(f'#b{k}')
    m2.append('</div>')
    html_words += m1 + [b_h] + m2
    # the timecode, under the stack, always behind the head
    html_words.append(f'<div id="tc" style="top:{base_2 + 26:.1f}px">00:00:<b id="tcs">00</b>:<i id="tcf">00</i></div>')
    # the italic line: two separate words, the first moves over when the second lands
    i1, _ = base_box(itf, fs_i, base_i, x_solo, 'it', ITALIC[0], 'i1')
    i2, _ = base_box(itf, fs_i, base_i, x_i0 + i_w1, 'it', ITALIC[1], 'i2', extra=f"color:{S['accent']};")
    html_words += [i1, i2]
    p.html += html_words
    def keep(pts, pid):
        poly = ','.join(f'{x}px {y}px' for x, y in pts)
        return (f'<video id="{pid}" class="keep" src="assets/aroll.mp4" muted playsinline data-start="0" data-media-start="0" '
                f'data-duration="{s.dur:.4f}" data-track-index="{3 if pid == "kb" else 4}" style="clip-path:polygon({poly})"></video>')

    if KEEP:
        p.html.insert(1, keep(KEEP, 'kb'))
        p.hidden.append('#kb')
    p.html.append('<div id="fgw"><video id="fg" src="assets/subject.webm" muted playsinline data-start="0" data-media-start="0" '
                  f'data-duration="{s.dur:.4f}" data-track-index="1"></video></div>')

    if KEEP_FRONT:
        p.html.append(keep(KEEP_FRONT, 'kf'))
        p.hidden.append('#kf')

    # ---- the motion (frame counts read off the look, at 30 fps)
    def set_(sel, vals, at):
        p.js.append(f"tl.set('{sel}',{vals},{V.T(at):.3f});")

    def ft(sel, frm, to, dur, ease, at):
        p.js.append(f"tl.fromTo('{sel}',{frm},{{{to},duration:{dur:.3f},ease:'{ease}',immediateRender:false}},{V.T(at):.3f});")

    def land(pid, text, t0, t_next):
        """letter by letter: each one fades in over 4 frames, settling from a touch bigger; next letter 2 frames on"""
        n = len(text)
        step = min(2 * F, max(F, (t_next - t0 - 2 * F) / max(1, n)))
        k2 = 0
        for k, c in enumerate(text):
            if c == ' ':
                continue
            ft(f'#{pid}c{k}', '{autoAlpha:0,scale:1.12}', 'autoAlpha:1,scale:1', 4 * F, 'power2.out', t0 + k2 * step)
            k2 += 1

    def rise(pid, text, t0, size):
        """letter by letter up from under the window's edge, one frame apart"""
        for k, c in enumerate(text):
            if c != ' ':
                p.js.append(f"gsap.set('#{pid}c{k}',{{y:{size * 1.05:.1f}}});")
                ft(f'#{pid}c{k}', f'{{y:{size * 1.05:.1f}}}', 'y:0', 5 * F, 'power3.out', t0 + k * F)

    for k in range(len(SERIF[0])):
        p.hidden.append(f'#sac{k}')
    for k in range(len(SERIF[1])):
        p.hidden.append(f'#sbc{k}')
    p.hidden += ['#green', '#tc', '#i1', '#i2'] + tops + bots
    t_flip = t_a if shift else t_b
    set_(','.join(['#green'] + (['#kb'] if KEEP else []) + (['#kf'] if KEEP_FRONT else [])), '{autoAlpha:1}', t_flip)
    if shift:
        set_('#fgw', f'{{y:{shift}}}', t_flip)
        print(f'  little headroom: the speaker moves down {shift} px on the backdrop, which is up from the first line')
    land('sa', SERIF[0], t_a, t_b)
    land('sb', SERIF[1], t_b, t_pairs[0][0])
    # the serif leaves: top line rolls up out of its window, bottom line drops away letter by letter
    t0 = t_pairs[0][0]
    ft('#sa', f"{{y:0,scaleY:{sy}}}", f"y:{-(mask1[1] - mask1[0]):.1f},scaleY:{sy}", 3 * F, 'power2.in', t0)
    j, step = 0, min(1.6 * F, 7 * F / max(1, len(SERIF[1])))
    for k, c in enumerate(SERIF[1]):
        if c != ' ':
            ft(f'#sbc{k}', '{autoAlpha:1,y:0}', 'autoAlpha:0,y:60', 4 * F, 'power1.in', t0 + j * step)
            j += 1
    set_('#sb', '{autoAlpha:0}', t0 + j * step + 5 * F)
    # the stack
    for k, ((ta, tb), (a, b)) in enumerate(zip(t_pairs, STACK)):
        h = mask1[1] - mask1[0]
        set_(f'#t{k}', '{autoAlpha:1}', ta)
        ft(f'#t{k}', f'{{y:{h:.1f}}}', 'y:0', 5 * F, 'power3.out', ta)
        if k:
            ft(f'#t{k - 1}', '{y:0}', f'y:{-h:.1f}', 3 * F, 'power2.in', ta)
            set_(f'#t{k - 1}', '{autoAlpha:0}', ta + 3 * F)
        if k == 0:
            set_(f'#b{k}', '{autoAlpha:1}', tb)
            rise(f'b{k}', b, tb, mask2[1] - mask2[0])
            ft('#tc', '{autoAlpha:0}', 'autoAlpha:1', 3 * F, 'none', tb)
        else:
            # the old word's letters leave up one after another, the new one fades in under them, a touch big
            old = STACK[k - 1][1]
            hh = mask2[1] - mask2[0]
            step = min(.7 * F, 2.5 * F / max(1, len(old)))
            for q, c in enumerate(old):
                if c != ' ':
                    ft(f'#b{k - 1}c{q}', '{y:0}', f'y:{-hh * 1.05:.1f}', 3 * F, 'power2.in', tb + q * step)
            ft(f'#b{k}', '{autoAlpha:0,scale:1.07}', 'autoAlpha:1,scale:1', 5 * F, 'power2.out', tb)
    # everything cuts to the italic line
    set_(','.join(tops + bots + ['#tc']), '{autoAlpha:0}', t_i1)
    set_('#i1', '{autoAlpha:1}', t_i1)
    ft('#i1', '{scale:1.55}', 'scale:1', 5 * F, 'expo.out', t_i1)
    # the first words step over, the coloured word lands big and settles; the speaker jumps closer on it
    set_('#i1', f'{{x:{x_i0 - x_solo:.1f}}}', t_i2)
    ft('#i1', '{scale:1.03}', 'scale:1', 5 * F, 'power2.out', t_i2)
    set_('#i2', '{autoAlpha:1}', t_i2)
    ft('#i2', '{scale:1.42}', 'scale:1', 5 * F, 'expo.out', t_i2)
    if PUNCH != 1:
        set_('#fgw', f'{{scale:{PUNCH}}}', t_i2)
    if t_out < s.dur - .02:
        set_('#fx', '{autoAlpha:0}', t_out)
    if SOUND:
        p.sound('impact-bass-1', t_i1, SOUND)

    # ---- the running timecode: the reel's own time
    f0 = round(s.t0 * 30)
    p.js.append(f"""(function(){{const ss=document.getElementById('tcs'),ff=document.getElementById('tcf');let cur=-1;
const o={{v:function(x){{if(x===undefined)return cur;cur=x;const n=Math.floor(x+.001);
ss.textContent=String(Math.floor(n/30)).padStart(2,'0');ff.textContent=String(n%30).padStart(2,'0');}}}};
tl.fromTo(o,{{v:{f0}}},{{v:{f0 + s.frames},duration:{s.dur:.4f},ease:'none',immediateRender:true}},0);}})();""")

    # ---- the small plate captions: 2 to 4 words at a time, said words in the ink colour
    if plate_on:
        groups, g = [], []
        for w in s.words:
            if w['start'] >= t_out:
                break
            if g and (len(' '.join(x['text'] for x in g + [w])) > 18 or len(g) >= 4):
                groups.append(g)
                g = []
            g.append(w)
        if g:
            groups.append(g)
        for gi, g in enumerate(groups):
            pid = f'pl{gi}'
            spans = ' '.join(f'<span id="{pid}w{q}">{V.esc(w["text"])}</span>' for q, w in enumerate(g))
            p.html.append(f'<div id="{pid}" class="pl"><div>{spans}</div></div>')
            start = max(0.0, g[0]['start'] - .05)
            end = groups[gi + 1][0]['start'] - .05 if gi + 1 < len(groups) else t_out
            p.show(f'#{pid}', start, end if end < s.dur - .02 else None)
            for q, w in enumerate(g):
                set_(f'#{pid}w{q}', f"{{color:'{S['ink']}'}}", w['start'])
        s.hide_hint([(0.0, t_out)])
    p.write()
    print(f'  sizes: serif {fs_a:.0f}/{fs_b:.0f}, stack top {[round(z) for z in size_top]} bottom {[round(z) for z in size_bot]}, italic {fs_i:.0f}')
    print(f'  flip {t_b:.2f}s, stack {t_pairs}, italic {t_i1:.2f}s and {t_i2:.2f}s, room back {t_out:.2f}s')
    snaps = [t_a + .3, t_b + .25, t_pairs[0][0] + .2, t_pairs[0][1] + .25, t_pairs[-1][1] + .2, t_i1 + .2, t_i2 + .3]
    print('snapshot at: ' + ','.join(f'{min(x, s.dur - .05):.2f}' for x in snaps))


if __name__ == '__main__':
    main()
