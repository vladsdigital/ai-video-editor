#!/usr/bin/env python3
"""APP DELETE (explain / proof): a cream panel of plain tiles with labels sits above the head and starts to jiggle.
Each tile is deleted on its name: its small badge flushes pink and swells, the tile shrinks away, the rest close the
gap and the count in the corner drops. On the last word the tiles still there hop and fall out of frame beside the
head, one big italic word rises in the panel, and the panel fades.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html   (SAFE=1 safe-zone guide, SFX=0 no sounds, CAPTIONS=0 accepted:
                                               the panel IS the effect, so it always draws)
"""
import os

import vgfx as V

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    word_font='Instrument Serif',  # the one word at the end
    word_italic=True,
    word_weight=400,
    word_case='as-said',           # 'as-said', 'lower' or 'upper'
    label_font='Inter',            # names under the tiles
    label_weight=500,
    mono_font='JetBrains Mono',    # the two corner labels
    letter_font='Instrument Serif',  # the letter on a tile with no image
    letter_italic=True,
    panel='#F3EFE2',
    ink='#14241C',                 # the word and the names
    mode='#C6577F',                # corner label, left, and the badge when it is about to delete
    dim='#7B776B',                 # corner label, right
    badge='#111111',
    tiles=[('#1F4033', '#F3EFE2'), ('#FFFFFF', '#14241C'), ('#1B1B1E', '#E9C46A'), ('#C9A95C', '#14241C')],  # (fill, letter)
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
# One row per tile, left to right: (name under the tile, the word it is deleted on, image file or None).
# word: a word the speaker says ('faktura', or 'faktura#2' for its second time), seconds, or None = it stays to the end
# and falls out on T_WORD. Image: a file the buyer gave, in the slot's tiles/ folder. None = a plain coloured square
# with the name's first letter. Never a real product's logo unless it is the buyer's own.
TILES = []
WORD = ''           # the word that takes the panel's place. Required
T_WORD = None       # when it lands (a word, seconds). None = when WORD is said
T_IN = None         # when the panel appears (slot seconds). None = 0.55 s before the first delete
T_OUT = None        # when the panel starts to fade. None = 0.72 s after the word lands
MODE = 'EDIT MODE'  # corner label, left
COUNT = '{n} items' # corner label, right: '{n} items', or a dict for languages with more plural forms {0: '...', 2: '...'}
BADGE = 'minus'     # the small mark on each tile: 'minus' or 'x'
Y = None            # y of the bottom of the panel, px. None = just above the head from layout.json, or on the chest with no room there
SCALE = None        # size against the full-size panel (882 x 330 px). None = as large as the room above the head allows
SOUND = .3          # volume of the pops, the fall and the word. 0 = silent
# ==== END CLIP ====

# the panel at full size, px: everything scales together
PW, PH, RAD = 882, 330, 30
TILE, PITCH, TX, TY, TRAD = 170, 200, 54, 75, 42
LABEL_C, HEAD_C, MONO = 273, 36, 21
BADGE_D, LABEL_PX, WORD_PX = 42, 27, 132


def when(s, spec, after=0.0):
    """a word ('name' or 'name#2'), or seconds -> slot seconds, or None"""
    if spec is None:
        return None
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


def count_text(n):
    if isinstance(COUNT, dict):
        return COUNT.get(n) or COUNT.get(max(COUNT)) or str(n)
    return COUNT.format(n=n)


def main():
    s = V.Slot()
    s.dur = int(s.frames / V.FPS * 1e4) / 1e4      # rounded down: a page rounded up to the next 1/10000 s renders one frame too many
    print('words: ' + s.word_list())
    print(s.where())
    if not TILES or not WORD.strip():
        V.die('fill TILES and WORD in the CLIP block: the things the speaker names, and the word they end on')
    if len(TILES) > 6:
        V.die('at most 6 tiles fit one row')
    t_word = when(s, T_WORD if T_WORD is not None else V.bare(WORD))
    if t_word is None:
        V.die(f'"{WORD}" is not in the words of this slot: set T_WORD to the word or the seconds it lands on')
    dels = []
    for i, row in enumerate(TILES):
        t = when(s, row[1])
        if row[1] is not None and t is None:
            V.die(f'the word "{row[1]}" for the tile "{row[0]}" is not in the words of this slot')
        if t is not None:
            dels.append((t, i))
    dels.sort()
    if any(t >= t_word for t, _ in dels):
        V.die('every tile has to be deleted before the last word lands')
    first = dels[0][0] if dels else t_word
    t_in = T_IN if T_IN is not None else max(.03, first - .55)
    t_out = T_OUT if T_OUT is not None else t_word + .72
    if t_out + .14 > s.dur:
        print(f'  note: the slot ends at {s.dur:.2f}s and the panel fades at {t_out:.2f}s: make the slot longer (--to)')

    bottom = int(Y) if Y is not None else s.head_top - 14
    room = bottom - V.SAFE_TOP - 6
    n = len(TILES)
    k = SCALE if SCALE else min(1.0, room / PH, (1080 - 2 * V.SAFE_SIDE - 20) / PW, (PW - 2 * TX) / (n * PITCH))
    # no room above the head: the panel sits on the chest, under the chin
    below = (Y > s.chin) if Y is not None else k < .58
    if below:
        limit = (Y if Y is not None else V.SAFE_BOTTOM - 6) - s.chin - 24
        k = SCALE if SCALE else min(1.0, limit / PH, (1080 - 2 * V.SAFE_SIDE - 20) / PW, (PW - 2 * TX) / (n * PITCH))
        if Y is None:
            bottom = int(s.chin + 24 + PH * k)
        print('placement: no room above the head, so the panel sits on the chest')
    if k < .58:
        V.die(f'the panel needs more room above the head than this clip has ({room} px between the safe zone and the head)')
    px = lambda v: round(v * k, 1)
    pw, ph = px(PW), px(PH)
    left, top = round((1080 - pw) / 2), bottom - ph
    print(f'  panel: scale {k:.2f} ({pw:.0f} x {ph:.0f} px), top y {top:.0f}, bottom y {bottom}, room {room} px')

    # where the falling tiles go: the side of the head with room, so nothing crosses the face
    head = (s.layout or {}).get('head') or {}
    side_l, side_r = int(head.get('side_left') or s.cx - 220), int(head.get('side_right') or s.cx + 220)
    tw = px(TILE)
    room_l, room_r = side_l - V.SAFE_SIDE, 1080 - V.SAFE_SIDE - side_r
    fall_side = 'left' if room_l >= room_r else 'right'
    can_fall = max(room_l, room_r) >= tw + 24
    if not can_fall:
        print('  note: no open side beside the head on this clip, so the last tiles shrink away in the panel instead of falling past the face')

    S = STYLE
    p = V.Page(s)
    ital = 'italic' if S['word_italic'] else 'normal'
    p.css.append(f'''
.ad-panel{{position:absolute;left:{left}px;top:{top}px;width:{pw}px;height:{ph}px;border-radius:{px(RAD)}px;background:{S["panel"]};
  box-shadow:0 {px(10)}px {px(30)}px rgba(0,0,0,.26)}}
.ad-mono{{position:absolute;top:{px(HEAD_C)}px;transform:translateY(-50%);font-family:'{S["mono_font"]}';font-weight:500;font-size:{px(MONO)}px;letter-spacing:.12em;line-height:1;white-space:nowrap}}
.ad-slot{{position:absolute;top:{px(TY)}px;width:{tw}px;height:{px(LABEL_C - TY + 20)}px;z-index:3}}
.ad-wig{{position:absolute;left:0;top:0;width:{tw}px;height:{tw}px;transform-origin:50% 50%}}
.ad-tile{{position:absolute;inset:0;border-radius:{px(TRAD)}px;overflow:hidden;display:flex;align-items:center;justify-content:center;
  box-shadow:0 {px(4)}px {px(12)}px rgba(0,0,0,.2);font-family:'{S["letter_font"]}';font-style:{'italic' if S["letter_italic"] else 'normal'};font-size:{px(104)}px;line-height:1}}
.ad-tile img{{width:100%;height:100%;object-fit:cover;display:block}}
.ad-badge{{position:absolute;left:{px(-11)}px;top:{px(-11)}px;width:{px(BADGE_D)}px;height:{px(BADGE_D)}px;border-radius:50%;background:{S["badge"]};display:flex;align-items:center;justify-content:center;z-index:2}}
.ad-badge i{{display:block;width:{px(20)}px;height:{px(4)}px;border-radius:{px(2)}px;background:#fff}}
.ad-badge.x i{{position:absolute;transform:rotate(45deg)}}
.ad-badge.x i+i{{transform:rotate(-45deg)}}
.ad-name{{position:absolute;left:{px(-20)}px;right:{px(-20)}px;top:{px(LABEL_C - TY)}px;transform:translateY(-50%);text-align:center;font-family:'{S["label_font"]}';font-weight:{S["label_weight"]};font-size:{px(LABEL_PX)}px;color:{S["ink"]};line-height:1;white-space:nowrap}}
.ad-word{{position:absolute;left:0;right:0;top:{px(HEAD_C + 18)}px;bottom:0;display:flex;align-items:center;justify-content:center;font-family:'{S["word_font"]}';font-style:{ital};font-weight:{S["word_weight"]};color:{S["ink"]};line-height:1;white-space:nowrap}}''')
    shown_word = V.cased(WORD, S['word_case'])
    wpx = min(px(WORD_PX), (pw * .84) / max(1, len(shown_word) * .4))
    x_of = lambda pos: px(TX) + pos * px(PITCH)
    rows = []
    for i, row in enumerate(TILES):
        fill, ink = S['tiles'][i % len(S['tiles'])]
        image = row[2] if len(row) > 2 else None
        if image and not os.path.isfile(os.path.join('tiles', image)):
            V.die(f'tiles/{image} is missing: put the buyer\'s file in the slot\'s tiles/ folder, or use None')
        face = f'<img src="tiles/{V.esc(image)}" alt="">' if image else V.esc(row[0].strip()[:1].upper())
        mark = '<i></i><i></i>' if BADGE == 'x' else '<i></i>'
        rows.append(f'<div id="ads{i}" class="ad-slot" style="left:{x_of(i)}px">'
                    f'<div id="adw{i}" class="ad-wig"><div id="adt{i}" class="ad-tile" style="background:{fill};color:{ink}">{face}</div>'
                    f'<div id="adb{i}" class="ad-badge{" x" if BADGE == "x" else ""}">{mark}</div></div>'
                    f'<div id="adn{i}" class="ad-name">{V.esc(row[0])}</div></div>')
    counts = ''.join(f'<span id="adc{c}" style="position:absolute;right:0;top:0;opacity:{1 if c == n else 0}">{V.esc(count_text(c))}</span>'
                     for c in sorted({n - j for j in range(len(dels) + 1)} | {0}))
    p.html.append(f'<div id="adp" class="ad-panel">'
                  f'<div class="ad-mono" style="left:{px(TX - 14)}px;color:{S["mode"]}">{V.esc(MODE)}</div>'
                  f'<div class="ad-mono" style="right:{px(TX - 14)}px;width:{px(300)}px;height:{px(MONO)}px;color:{S["dim"]};transform:translateY(-50%);text-align:right">{counts}</div>'
                  f'<div id="adx" class="ad-word" style="font-size:{wpx}px">{V.esc(shown_word)}</div>'
                  f'{"".join(rows)}</div>')

    # ---- in: the panel fades down a touch, the tiles and their badges come in one after another
    p.enter('#adp', t_in, {'y': px(-15)}, {'y': 0}, .13, ease='power2.out')
    for i in range(n):
        p.enter(f'#ads{i}', t_in + .02 + i * .045, {}, {}, .1, ease='none')
        p.enter(f'#adb{i}', t_in + .14 + i * .05, {'scale': .3}, {'scale': 1}, .1, ease='back.out(2)')
    # ---- the jiggle: each tile rocks on its own beat, about 6 times a second
    t_lift = t_word - .1
    start = t_in + .16
    for i in range(n):
        t, sign = start + i * .03, 1 if i % 2 else -1
        end = next((d for d, j in dels if j == i), t_lift)
        while t < end - .08:
            p.js.append(f"tl.to('#adw{i}',{{rotation:{sign * (1.5 + (i % 2) * .3):.2f},y:{sign * px(1.6):.1f},duration:.075,ease:'sine.inOut'}},{t:.3f});")
            t += .08
            sign = -sign
    # ---- each delete: the badge flushes and swells, the tile shrinks, the rest slide over, the count drops
    alive = list(range(n))
    count = n
    for t, i in dels:
        p.js.append(f"tl.to('#adb{i}',{{backgroundColor:'{S['mode']}',scale:1.42,duration:.12,ease:'power2.out'}},{V.T(t - .14):.3f});")
        p.js.append(f"tl.to('#adw{i}',{{scale:.28,autoAlpha:0,duration:.11,ease:'power2.in'}},{V.T(t):.3f});")
        p.js.append(f"tl.to('#adn{i}',{{autoAlpha:0,duration:.09,ease:'none'}},{V.T(t):.3f});")
        alive.remove(i)
        for pos, j in enumerate(alive):
            if j > i:
                p.js.append(f"tl.to('#ads{j}',{{x:{x_of(pos) - x_of(j):.1f},duration:.17,ease:'power2.out'}},{V.T(t + .03):.3f});")
        p.js.append(f"tl.set('#adc{count}',{{opacity:0}},{V.T(t + .05):.3f});")
        count -= 1
        p.js.append(f"tl.set('#adc{count}',{{opacity:1}},{V.T(t + .05):.3f});")
        p.sound('pop', t, SOUND)
    # ---- the last word: what is left hops, then falls out of frame beside the head; the word rises in the panel
    if count:
        p.js.append(f"tl.set('#adc{count}',{{opacity:0}},{V.T(t_lift):.3f});tl.set('#adc0',{{opacity:1}},{V.T(t_lift):.3f});")
    pos_of = {j: pos for pos, j in enumerate(alive)}
    for j in alive:
        seat = x_of(pos_of[j]) - x_of(j)
        lag = pos_of[j] * .07
        rot = (-14 - 8 * pos_of[j]) if fall_side == 'left' else (14 + 8 * pos_of[j])
        p.js.append(f"tl.to('#ads{j}',{{y:{px(-26)},duration:.1,ease:'power2.out'}},{V.T(t_lift):.3f});")
        p.js.append(f"tl.set('#adn{j}',{{autoAlpha:0}},{V.T(t_word + .05):.3f});")
        if can_fall:
            # spread over the open side, so they fall apart from each other
            edge, span = (V.SAFE_SIDE + 6, side_l - V.SAFE_SIDE - 22 - tw) if fall_side == 'left' else (side_r + 16, 1080 - V.SAFE_SIDE - 22 - tw - side_r)
            dest = edge + (span * pos_of[j] / (len(alive) - 1) if len(alive) > 1 else span / 2)
            dx = 0 if below else dest - (left + px(TX) + pos_of[j] * px(PITCH))      # on the chest they just drop
            p.js.append(f"tl.to('#ads{j}',{{x:{seat + dx:.1f},duration:.14,ease:'power2.out'}},{V.T(t_word + lag):.3f});")
            p.js.append(f"tl.to('#ads{j}',{{y:{1980 - top:.0f},duration:.52,ease:'power2.in'}},{V.T(t_word + lag):.3f});")
            p.js.append(f"tl.to('#adw{j}',{{rotation:{rot},duration:.52,ease:'power1.in'}},{V.T(t_word + lag):.3f});")
        else:
            p.js.append(f"tl.to('#ads{j}',{{scale:.25,autoAlpha:0,duration:.16,ease:'power2.in'}},{V.T(t_word):.3f});")
    p.enter('#adx', t_word + .04, {'y': px(26)}, {'y': 0}, .15, ease='power2.out')
    p.js.append(f"tl.to('#adp',{{autoAlpha:0,y:{px(-8)},duration:.13,ease:'power1.in'}},{V.T(t_out):.3f});")
    p.sound('whoosh-short', t_word + .1, SOUND * .6)
    p.sound('click-soft', t_word + .04, SOUND)
    print(f'  in at {t_in:.2f}s, deletes at ' + ', '.join(f'{t:.2f}' for t, _ in dels) + f', word at {t_word:.2f}s, fades at {t_out:.2f}s; the tiles fall on the {fall_side}')
    p.write()
    moments = [t_in + .05, t_in + .3] + [t - .05 for t, _ in dels[:1]] + [dels[0][0] + .06 if dels else t_lift] + [t_lift + .08, t_word + .12, t_word + .3, t_out + .05]
    print('snapshot at: ' + ','.join(f'{m:.2f}' for m in moments))


if __name__ == '__main__':
    main()
