#!/usr/bin/env python3
"""STRIKE TILES (explain / proof): plain tiles pop up above the head on their names, a red pen line strikes through each
one and the tile dulls. On the last word they hop and fall out of frame beside the head, and one italic word rises in
their place, holds and fades.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html   (SAFE=1 safe-zone guide, SFX=0 no sounds, CAPTIONS=0 accepted:
                                               the tiles ARE the effect, so they always draw)
"""
import os

import vgfx as V

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    word_font='Instrument Serif',  # the one word at the end
    word_italic=True,
    word_weight=400,
    word_case='as-said',           # 'as-said', 'lower' or 'upper'
    ink='#F3EFE2',                 # the word and the names under the tiles
    label_font='Inter',
    label_weight=500,
    letter_font='Instrument Serif',  # the letter on a tile with no image
    letter_italic=True,
    pen='#D93A5C',                 # the strike
    pen_tip='#FFF3E6',             # the bright head of the line while it draws
    tiles=[('#FFFFFF', '#14241C'), ('#1F4033', '#F3EFE2'), ('#1B1B1E', '#E9C46A'), ('#C9A95C', '#14241C')],  # (fill, letter)
    shadow=True,
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
# One row per tile, left to right: (name under the tile, the word it pops up on, image file or None).
# word: a word the speaker says ('faktura', 'faktura#2' for its second time), or seconds.
# Image: a file the buyer gave, in the slot's tiles/ folder. None = a plain coloured square with the name's first letter.
# Never a real product's logo unless it is the buyer's own.
TILES = []
WORD = ''           # the italic word that rises in their place. Required
T_WORD = None       # when it lands (a word, seconds). None = when WORD is said
T_OUT = None        # when the word starts to fade. None = 0.55 s after it lands
STRIKE_AFTER = .24  # seconds from a tile popping up to its strike starting
Y = None            # y of the top of the tiles, px. None = as close to the top of the safe zone as the room allows
SCALE = None        # size against full size (tiles 225 px). None = as large as the room above the head allows
SOUND = .3          # volume of the pops, the pen and the fall. 0 = silent
# ==== END CLIP ====

# full size, px: everything scales together
TILE, PITCH, RAD, LABEL_GAP, LABEL_PX, WORD_PX, PEN = 225, 270, 50, 26, 28, 125, 15


def when(s, spec, after=0.0):
    if isinstance(spec, (int, float)):
        return float(spec)
    name, _, nth = str(spec).partition('#')
    t, hit = after, None
    for _ in range(int(nth or 1)):
        hit = s.find('^' + V.re.escape(V.bare(name)) + '$', t)
        if not hit:
            return None
        t = hit['start'] + .01
    return hit['start']


def main():
    s = V.Slot()
    s.dur = int(s.frames / V.FPS * 1e4) / 1e4      # rounded down: a page rounded up to the next 1/10000 s renders one frame too many
    print('words: ' + s.word_list())
    print(s.where())
    if not TILES or not WORD.strip():
        V.die('fill TILES and WORD in the CLIP block: the things the speaker names, and the word they end on')
    if len(TILES) > 4:
        V.die('at most 4 tiles fit one row')
    t_word = when(s, T_WORD if T_WORD is not None else V.bare(WORD))
    if t_word is None:
        V.die(f'"{WORD}" is not in the words of this slot: set T_WORD to the word or the seconds it lands on')
    pops = []
    for row in TILES:
        t = when(s, row[1])
        if t is None:
            V.die(f'the word "{row[1]}" for the tile "{row[0]}" is not in the words of this slot')
        pops.append(t)
    if max(pops) + STRIKE_AFTER + .25 >= t_word:
        V.die('the last tile needs about half a second before the last word, to be struck through')
    t_out = T_OUT if T_OUT is not None else t_word + .55
    if t_out + .2 > s.dur:
        print(f'  note: the slot ends at {s.dur:.2f}s and the word fades at {t_out:.2f}s: make the slot longer (--to)')

    n = len(TILES)
    stack = TILE + LABEL_GAP + LABEL_PX
    bottom_max = s.head_top - 12
    room = bottom_max - V.SAFE_TOP - 16
    k = SCALE if SCALE else min(1.0, room / stack, (1080 - 2 * V.SAFE_SIDE - 20) / (TILE + (n - 1) * PITCH))
    if k < .55:
        V.die(f'the tiles need more room above the head than this clip has ({room} px between the safe zone and the head)')
    px = lambda v: round(v * k, 1)
    tw, pitch = px(TILE), px(PITCH)
    row_w = tw + (n - 1) * pitch
    left = min(max(V.SAFE_SIDE + 10, s.cx - row_w / 2), 1080 - V.SAFE_SIDE - 10 - row_w)
    top = int(Y) if Y is not None else max(V.SAFE_TOP + 16, bottom_max - px(stack))
    print(f'  tiles: scale {k:.2f} ({tw:.0f} px), row from x {left:.0f}, top y {top}, room {room} px')

    # where they fall: the side of the head with room, so nothing crosses the face
    head = (s.layout or {}).get('head') or {}
    side_l, side_r = int(head.get('side_left') or s.cx - 220), int(head.get('side_right') or s.cx + 220)
    room_l, room_r = side_l - V.SAFE_SIDE, 1080 - V.SAFE_SIDE - side_r
    fall_left = room_l >= room_r
    can_fall = max(room_l, room_r) >= tw + 20
    if not can_fall:
        print('  note: no open side beside the head on this clip, so the tiles drop back and fade above the head instead of falling past the face')

    S = STYLE
    p = V.Page(s)
    shade = 'text-shadow:0 2px 18px rgba(0,0,0,.42);' if S['shadow'] else ''
    p.css.append(f'''
.st-tile{{position:absolute;top:{top}px;width:{tw}px;height:{tw}px;z-index:3}}
.st-face{{position:absolute;inset:0;border-radius:{px(RAD)}px;overflow:hidden;display:flex;align-items:center;justify-content:center;
  box-shadow:0 {px(6)}px {px(18)}px rgba(0,0,0,.3),inset 0 0 0 {px(2)}px rgba(255,255,255,.16);filter:saturate(1) brightness(1);font-family:'{S["letter_font"]}';font-style:{'italic' if S["letter_italic"] else 'normal'};font-size:{px(136)}px;line-height:1}}
.st-face img{{width:100%;height:100%;object-fit:cover;display:block}}
.st-name{{position:absolute;left:{px(-30)}px;right:{px(-30)}px;top:{tw + px(LABEL_GAP) - px(LABEL_PX) / 2:.1f}px;text-align:center;font-family:'{S["label_font"]}';font-weight:{S["label_weight"]};font-size:{px(LABEL_PX)}px;line-height:1;color:{S["ink"]};white-space:nowrap;{shade}}}
.st-pen{{position:absolute;left:0;top:0;width:{tw}px;height:{tw}px;overflow:visible;z-index:2}}
.st-pen path{{fill:none;stroke-linecap:round;stroke-linejoin:round}}
.st-word{{position:absolute;left:0;right:0;display:flex;justify-content:center;font-family:'{S["word_font"]}';font-style:{'italic' if S["word_italic"] else 'normal'};font-weight:{S["word_weight"]};color:{S["ink"]};line-height:1;white-space:nowrap;{shade}}}''')
    for i, row in enumerate(TILES):
        fill, ink = S['tiles'][i % len(S['tiles'])]
        image = row[2] if len(row) > 2 else None
        if image and not os.path.isfile(os.path.join('tiles', image)):
            V.die(f'tiles/{image} is missing: put the buyer\'s file in the slot\'s tiles/ folder, or use None')
        face = f'<img src="tiles/{V.esc(image)}" alt="">' if image else V.esc(row[0].strip()[:1].upper())
        # a hand-drawn line past both edges with a slight bow; odd tiles go the other way across
        o, a = px(-14), tw + px(14)
        if i % 2 == 0:
            d = f'M{o} {tw * .16:.1f} C{tw * .28:.1f} {tw * .22:.1f} {tw * .55:.1f} {tw * .6:.1f} {a} {tw * .86:.1f}'
        else:
            d = f'M{o} {tw * .84:.1f} C{tw * .26:.1f} {tw * .74:.1f} {tw * .72:.1f} {tw * .34:.1f} {a} {tw * .14:.1f}'
        pen = (f'<svg class="st-pen" viewBox="0 0 {tw} {tw}"><path id="stl{i}" d="{d}" pathLength="1" stroke="{S["pen"]}" stroke-width="{px(PEN)}" stroke-dasharray="1 1.2" stroke-dashoffset="1"/>'
               f'<path id="stq{i}" d="{d}" pathLength="1" stroke="{S["pen_tip"]}" stroke-width="{px(PEN) * .8:.1f}" stroke-dasharray=".05 1.2" stroke-dashoffset=".05"/></svg>')
        p.html.append(f'<div id="st{i}" class="st-tile" style="left:{left + i * pitch:.1f}px"><div id="stw{i}" style="position:absolute;inset:0">'
                      f'<div id="stf{i}" class="st-face" style="background:{fill};color:{ink}">{face}</div>{pen}'
                      f'<div id="stn{i}" class="st-name">{V.esc(row[0])}</div></div></div>')
    shown = V.cased(WORD, S['word_case'])
    wpx = min(px(WORD_PX), 900 / max(1, len(shown) * .4))
    word_y = top + tw / 2 - wpx / 2
    word_y = max(V.SAFE_TOP + 10, word_y)
    p.html.append(f'<div id="stx" class="st-word" style="top:{word_y:.0f}px;left:{max(V.SAFE_SIDE, s.cx - 480):.0f}px;right:auto;width:960px;font-size:{wpx:.0f}px">{V.esc(shown)}</div>')

    t_hop = t_word - .13
    for i, t in enumerate(pops):
        p.enter(f'#st{i}', t, {'scale': .62}, {'scale': 1}, .2, ease='back.out(2.2)')
        at = t + STRIKE_AFTER
        p.js.append(f"tl.to('#stl{i}',{{attr:{{'stroke-dashoffset':0}},duration:.15,ease:'power1.inOut'}},{V.T(at):.3f});")
        p.js.append(f"tl.to('#stq{i}',{{attr:{{'stroke-dashoffset':-.95}},duration:.15,ease:'power1.inOut'}},{V.T(at):.3f});")
        p.js.append(f"tl.to('#stq{i}',{{opacity:0,duration:.03,ease:'none'}},{V.T(at) + .15:.3f});")
        p.js.append(f"tl.to('#stf{i}',{{filter:'saturate(.75) brightness(.9)',duration:.15,ease:'none'}},{V.T(at):.3f});")
        p.sound('pop', t, SOUND)
        p.sound('click-soft', at + .03, SOUND)
    # the last word: they hop with a small tilt, then fall one after another; the word rises in their place
    for i in range(n):
        lag = i * .07
        tilt = -3 if i % 2 else 3
        p.js.append(f"tl.to('#stw{i}',{{y:{px(-24)},rotation:{tilt},duration:.11,ease:'power2.out'}},{V.T(t_hop):.3f});")
        here = left + i * pitch
        if can_fall:
            if fall_left:
                span = side_l - V.SAFE_SIDE - 22 - tw
                dest = V.SAFE_SIDE + 6 + (span * i / (n - 1) if n > 1 else span / 2)
            else:
                span = 1080 - V.SAFE_SIDE - 22 - tw - side_r
                dest = side_r + 16 + (span * i / (n - 1) if n > 1 else span / 2)
            p.js.append(f"tl.to('#st{i}',{{x:{dest - here:.1f},duration:.13,ease:'power2.out'}},{V.T(t_word + lag):.3f});")
            p.js.append(f"tl.to('#st{i}',{{y:{1980 - top},duration:.5,ease:'power2.in'}},{V.T(t_word + lag):.3f});")
            p.js.append(f"tl.to('#stw{i}',{{rotation:{-12 - 6 * i if fall_left else 12 + 6 * i},duration:.5,ease:'power1.in'}},{V.T(t_word + lag) + .01:.3f});")
        else:
            p.js.append(f"tl.to('#st{i}',{{scale:.6,autoAlpha:0,duration:.16,ease:'power2.in'}},{V.T(t_word + lag):.3f});")
    p.enter('#stx', t_word + .05, {'y': px(36)}, {'y': 0}, .15, ease='power2.out')
    p.js.append(f"tl.to('#stx',{{autoAlpha:0,duration:.17,ease:'none'}},{V.T(t_out):.3f});")
    p.sound('whoosh-short', t_word + .1, SOUND * .6)
    print(f'  pops at ' + ', '.join(f'{t:.2f}' for t in pops) + f', word at {t_word:.2f}s, fades at {t_out:.2f}s, the tiles fall on the {"left" if fall_left else "right"}')
    p.write()
    moments = [pops[0] + .03, pops[0] + STRIKE_AFTER + .08, pops[-1] + STRIKE_AFTER + .3, t_hop + .1, t_word + .1, t_word + .3, t_out + .08]
    print('snapshot at: ' + ','.join(f'{m:.2f}' for m in moments))


if __name__ == '__main__':
    main()
