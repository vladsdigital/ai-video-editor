#!/usr/bin/env python3
"""COMMENT LETTERS (call to action): a comment box appears above the head, the keyword's big letters drop in one by one
in 3D above it, in dark or cream depending on what is behind each part of them, then each letter falls into the box and
becomes typed text, the comment posts and lifts up, and reply cards stack under it on a thread line, with a like.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html and assets/lightmask.png   (SAFE=1 safe-zone guide, SFX=0 no sounds,
                          CAPTIONS=0 accepted: the reel's own captions keep running under it)
"""
import os

import vgfx as V

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    font='Inter Tight',            # the big letters, keyword, names
    font_file='InterTight-900-normal.woff2',
    weight=900,
    tracking=-0.03,
    small_font='Inter',
    small_weight=500,
    plate='#FFFFFF',               # cards
    ink='#0F0F0F',                 # words on cards
    mute='#9B9B96',
    green='#1B3C2E',               # the big letters over a light background, the Post button (deep forest green)
    cream='#F4F1E4',               # the big letters over a dark background (cream paper)
    sage='#7F9D8B',                # the plain avatar tile
    ring='#8FE3B6',
    heart='#B9506B',
    thread='#FFFFFF',              # the line from comment to replies
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
KEYWORD = 'LINK'            # the big word that drops in and types itself: 2 to 8 letters. Required
PLACEHOLDER = 'Dodaj komentar...'
POST = 'Objavi'             # the button
ME, NOW = 'ti', 'sada'      # the small name over the posted comment, and "now"
HANDLE = 'vladsdigital'     # the buyer's handle on the replies. Required
REPLIES = ['Link se nalazi ovde.',          # 1 or 2 short replies, they stack, words come in one by one
           'Požuri dok cena nije skočila.']
AVATAR = ''                 # the buyer's own round picture in the slot's assets/. '' = a plain letter tile
TWO_TONE = True             # True = dark letters over light parts of the picture, cream over dark. False = cream only
TIMES = {}                  # slot seconds, to overrule a step: box, drop, fall, post, reply, like, out
SOUND = 0.26                # the low hit when the first letter reaches the box. 0 = silent
# ==== END CLIP ====

F = 1 / 30
HEART = ('M12 21s-7.5-4.6-10-9.2C.3 8.5 2.1 4.6 5.8 4.6c2.3 0 3.9 1.3 4.9 2.8.3.5 1.3.5 1.6 0 1-1.5 2.6-2.8 4.9-2.8 '
         '3.7 0 5.5 3.9 3.8 7.2C19.5 16.4 12 21 12 21z')
PERSON = '<circle cx="12" cy="9" r="3.9"/><path d="M4.6 20.4c.9-4 3.8-6 7.4-6s6.5 2 7.4 6c-2 .9-4.5 1.3-7.4 1.3s-5.4-.4-7.4-1.3z"/>'


def face(path, weight):
    """the font at the weight the page draws: a variable file measures at its default weight otherwise"""
    from PIL import ImageFont
    f = ImageFont.truetype(path, 1000)
    try:
        axes = f.get_variation_axes()
        f.set_variation_by_axes([weight if k == 0 else a['default'] for k, a in enumerate(axes)])
    except OSError:
        pass
    return f


def light_mask(y0, y1):
    """a picture of where the slot's background is light (median of a few frames): the big letters go dark there.
    The line between light and dark is found in the band the letters fly through; None = that band is all one tone"""
    import cv2
    import numpy as np
    cap = cv2.VideoCapture('assets/aroll.mp4')
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    frames = []
    for k in range(5):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(k * n / 5))
        ok, fr = cap.read()
        if ok:
            frames.append(cv2.cvtColor(cv2.resize(fr, (540, 960)), cv2.COLOR_BGR2GRAY))
    cap.release()
    if not frames:
        V.die('could not read assets/aroll.mp4 for the two-tone letters: set TWO_TONE = False')
    g = cv2.GaussianBlur(np.median(np.stack(frames), axis=0).astype('uint8'), (0, 0), 3)
    band = g[int(y0 / 2):int(y1 / 2), :]
    level, _ = cv2.threshold(band, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    lo, hi = band[band <= level], band[band > level]
    if not len(lo) or not len(hi) or hi.mean() - lo.mean() < 26 or min(len(lo), len(hi)) < .04 * band.size:
        return None
    m = (g > level).astype('uint8') * 255
    m = cv2.GaussianBlur(m, (0, 0), .8)
    out = np.dstack([np.full_like(m, 255)] * 3 + [m])
    cv2.imwrite('assets/lightmask.png', cv2.resize(out, (1080, 1920), interpolation=cv2.INTER_LINEAR))
    return float((m[int(y0 / 2):int(y1 / 2), :] > 127).mean())


def main():
    s = V.Slot()
    print('words: ' + s.word_list())
    print(s.where())
    S = STYLE
    word = KEYWORD.strip()
    if not 2 <= len(word) <= 8 or not HANDLE.strip():
        V.die('KEYWORD takes 2 to 8 letters, and HANDLE is required')
    if not 1 <= len(REPLIES) <= 2:
        V.die('REPLIES takes 1 or 2 short replies')
    path = os.path.join('assets/fonts', S['font_file'])
    if not os.path.exists(path):
        V.die(f'{S["font_file"]} is not in assets/fonts: set a font of the slot in the STYLE block')
    ff = face(path, S['weight'])

    # ---- where: the box sits just above the head; the posted stack ends on the hair at most; the word above the box
    top = V.SAFE_TOP + 10
    nr = len(REPLIES)
    room = s.head_top + 45 - top
    u = min(1.0, room / ((nr + 1) * 116 + nr * 15))
    if u < .6:
        V.die(f'the head starts at y {s.head_top}: no room for the cards above it. It needs a wide or medium shot')
    box_h, gap = 116 * u, 15 * u
    y_pre = s.head_top - box_h - 8
    y_post = s.head_top + 45 - (nr + 1) * box_h - nr * gap
    if y_post < top:
        y_post = top
    cap_room = y_pre - 24 - top
    box_x, box_w = 90, 900
    # the big word: as wide as the demo's look, stopped by the room over the box
    cap_ratio = -ff.getbbox('H', anchor='ls')[1] / 1000
    ink_up = -ff.getbbox(word, anchor='ls')[1] / 1000
    width1 = ff.getlength(word) / 1000 + S['tracking'] * len(word)
    size = min(262 * (1 if len(word) <= 5 else 5 / len(word)), 900 / width1, cap_room / ink_up)
    if size * cap_ratio < 70:
        V.die(f'only {cap_room:.0f} px over the box for the big letters on this clip: it needs more headroom')
    base = y_pre - 24 - (cap_room - ink_up * size) * .35
    wx = 540 - width1 * size / 2

    # ---- when
    w = s.find('^' + V.bare(word) + '$')
    n = len(word)
    t_drop = float(TIMES.get('drop', w['start'] if w else .4))
    t_box = float(TIMES.get('box', max(0.0, t_drop - 12 * F)))
    t_fall = float(TIMES.get('fall', t_drop + (n * 2 + 3) * F))
    t_typed = t_fall + (n - 1) * 2 * F + 6 * F
    t_post = float(TIMES.get('post', t_typed + 7 * F))
    t_reply = float(TIMES.get('reply', t_post + 7 * F))
    t_out = float(TIMES.get('out', s.dur - 7 * F))
    rw = [r.split() for r in REPLIES]
    each = max(.32, min(.8, (t_out - .55 - t_reply) / nr))
    t_rep = [t_reply + k * each for k in range(nr)]
    t_like = float(TIMES.get('like', t_rep[-1] + each - .05))
    if t_like > t_out - .2:
        V.die(f'{s.dur:.1f} s is too short for this flow from the keyword on: use a longer slot or one reply')
    print(f'  box {t_box:.2f}, letters {t_drop:.2f}, fall {t_fall:.2f}, typed {t_typed:.2f}, post {t_post:.2f}, replies {[round(x, 2) for x in t_rep]}, like {t_like:.2f}, out {t_out:.2f}')

    use_avatar = None
    if AVATAR:
        use_avatar = 'assets/' + AVATAR
        if not os.path.exists(use_avatar):
            V.die(f'AVATAR: {use_avatar} is not in the slot. Copy the buyer\'s picture there, or leave AVATAR empty')
    two = TWO_TONE
    if two:
        share = light_mask(top, y_pre + box_h)
        two = share is not None
        print(f'  two-tone: {share:.0%} of the band over the head is light' if two else '  two-tone off: the background over the head is all one tone')

    p = V.Page(s)
    fs = lambda v: f'{v * u:.1f}px'
    ty_px = 37 * u
    p.css.append(f'''
.card{{position:absolute;left:{box_x}px;width:{box_w}px;height:{box_h:.1f}px;background:{S['plate']};border-radius:{30 * u:.1f}px;box-shadow:0 8px 26px rgba(0,0,0,.13)}}
.card.rp{{left:{box_x + 80}px;width:{box_w - 80}px;overflow:hidden}}
.bl{{position:absolute;left:0;top:0;width:1080px;height:1920px;perspective:1000px;perspective-origin:540px {y_pre:.0f}px;font-family:'{S['font']}';font-weight:{S['weight']};font-size:{size:.1f}px;line-height:1}}
.bl span{{position:absolute;white-space:pre;will-change:transform,opacity}}
#lc{{color:{S['cream']}}}
#ld{{color:{S['green']};-webkit-mask-image:url(assets/lightmask.png);mask-image:url(assets/lightmask.png);-webkit-mask-size:1080px 1920px;mask-size:1080px 1920px}}
.av{{position:absolute;border-radius:50%;background:{S['sage']};overflow:hidden;display:flex;align-items:center;justify-content:center;color:#fff}}
.av svg{{width:72%;height:72%;fill:#fff}}
.av img{{width:100%;height:100%;object-fit:cover}}
.tile{{font-family:'{S['font']}';font-weight:800;line-height:1}}
#ty{{position:absolute;left:{118 * u:.1f}px;top:0;height:100%;display:flex;align-items:center;font-family:'{S['font']}';font-weight:800;font-size:{ty_px:.1f}px;color:{S['ink']};white-space:pre}}
#ty span{{display:none}}
#cr{{display:inline-block;width:{2.6 * u:.1f}px;height:{fs(44)};background:{S['ink']};margin-left:2px}}
#ph{{position:absolute;left:{118 * u:.1f}px;top:0;height:100%;display:flex;align-items:center;font-family:'{S['small_font']}';font-weight:{S['small_weight']};font-size:{fs(33)};color:{S['mute']};white-space:pre}}
#phc{{display:inline-block;width:{2.6 * u:.1f}px;height:{fs(44)};background:{S['ink']};margin-right:2px}}
.meta{{font-family:'{S['small_font']}';font-weight:{S['small_weight']};font-size:{fs(25)};color:{S['mute']};white-space:pre;line-height:1}}
#me{{position:absolute;left:{118 * u:.1f}px;top:{25 * u:.1f}px}}
#me b{{font-family:'{S['font']}';font-weight:700;color:{S['ink']}}}
#send{{position:absolute;right:{22 * u:.1f}px;top:{(box_h - 66 * u) / 2:.1f}px;height:{66 * u:.1f}px;padding:0 {28 * u:.1f}px;border-radius:{33 * u:.1f}px;background:#E9E7DF;color:{S['mute']};display:flex;align-items:center;justify-content:center;font-family:'{S['font']}';font-weight:700;font-size:{fs(28)}}}
#sgo{{position:absolute;inset:0;border-radius:{33 * u:.1f}px;background:{S['green']};color:{S['cream']};display:flex;align-items:center;justify-content:center;opacity:0}}
#heart,#hfill{{position:absolute;right:{34 * u:.1f}px;top:{(box_h - 46 * u) / 2:.1f}px;width:{46 * u:.1f}px;height:{46 * u:.1f}px;overflow:visible}}
.nm{{font-family:'{S['font']}';font-weight:700;color:{S['ink']};white-space:pre;line-height:1}}
.rl{{position:absolute;left:{112 * u:.1f}px;top:{24 * u:.1f}px;font-size:{fs(25)};display:flex;gap:.25em;align-items:baseline}}
.rt{{position:absolute;left:{112 * u:.1f}px;top:{60 * u:.1f}px;font-family:'{S['small_font']}';font-weight:{S['small_weight']};font-size:{fs(33)};line-height:1;color:{S['ink']};white-space:pre}}
.th{{position:absolute;overflow:visible;left:0;top:0;width:1080px;height:1920px}}''')

    def avatar(sz, left, top_):
        st = f'width:{sz:.1f}px;height:{sz:.1f}px;left:{left:.1f}px;top:{top_:.1f}px;box-shadow:0 0 0 {sz * .07:.1f}px {S["ring"]};'
        if use_avatar:
            return f'<div class="av" style="{st}"><img src="{use_avatar}" alt=""></div>'
        return (f'<div class="av" style="{st}background:{S["green"]};font-size:{sz * .5:.1f}px"><span class="tile">{V.esc(HANDLE[:1].upper())}</span></div>')

    # letters, measured one at a time so each can fly alone; a dark copy lives under the light-area mask
    x = wx
    pos = []
    for k, c in enumerate(word):
        adv = ff.getlength(word[:k + 1]) / 1000 * size - ff.getlength(word[:k]) / 1000 * size + S['tracking'] * size
        pos.append((x, adv))
        x += adv
    asc, dsc = ff.getmetrics()
    top_l = base - ((size - (asc + dsc) / 1000 * size) / 2 + asc / 1000 * size)
    spans = ''.join(f'<span class="a{k}" style="left:{px:.1f}px;top:{top_l:.1f}px;transform-origin:{adv / 2:.1f}px {base - top_l - cap_ratio * size / 2:.1f}px">{V.esc(c)}</span>'
                    for k, ((px, adv), c) in enumerate(zip(pos, word)))
    big = f'<div id="lc" class="bl">{spans}</div>' + (f'<div id="ld" class="bl">{spans}</div>' if two else '')

    # thread line, comment, replies
    a = 68 * u
    y_cards = [y_post + k * (box_h + gap) for k in range(nr + 1)]
    ax = box_x + 26 * u + a / 2
    for k in range(nr):
        ry = y_cards[k + 1] + box_h / 2
        d = f'M{ax:.1f} {y_post + box_h:.1f} L{ax:.1f} {ry - 16:.1f} Q{ax:.1f} {ry:.1f} {ax + 16:.1f} {ry:.1f} L{box_x + 80:.1f} {ry:.1f}'
        p.html.append(f'<svg class="th" id="th{k}"><path d="{d}" fill="none" stroke="{S["thread"]}" stroke-width="3.5" stroke-linecap="round"/></svg>')
    typed = ''.join(f'<span id="k{i}">{V.esc(c)}</span>' for i, c in enumerate(word))
    p.html.append(f'''<div id="box" class="card" style="top:{y_post:.1f}px">
<div id="av0" class="av" style="width:{a:.1f}px;height:{a:.1f}px;left:{26 * u:.1f}px;top:{(box_h - a) / 2:.1f}px"><svg viewBox="0 0 24 24">{PERSON}</svg></div>
<div id="ph"><i id="phc"></i>{V.esc(PLACEHOLDER)}</div>
<div id="me" class="meta"><b>{V.esc(ME)}</b> · {V.esc(NOW)}</div>
<div id="ty">{typed}<i id="cr"></i></div>
<div id="send">{V.esc(POST)}<div id="sgo">{V.esc(POST)}</div></div>
<svg id="heart" viewBox="0 0 24 24"><path d="{HEART}" fill="none" stroke="{S['ink']}" stroke-width="2"/></svg>
<svg id="hfill" viewBox="0 0 24 24"><path d="{HEART}" fill="{S['heart']}"/></svg>
</div>''')
    for k, words in enumerate(rw):
        rt = ' '.join(f'<span id="r{k}w{i}">{V.esc(x_)}</span>' for i, x_ in enumerate(words))
        p.html.append(f'''<div id="rc{k}" class="card rp" style="top:{y_cards[k + 1]:.1f}px">
{avatar(68 * u, 22 * u, (box_h - 68 * u) / 2)}
<div class="rl"><span class="nm">{V.esc(HANDLE)}</span><span class="meta">· {V.esc(NOW)}</span></div>
<div class="rt">{rt}</div>
</div>''')
    p.html.append(big)

    def ft(sel, frm, to, dur, ease, at):
        p.js.append(f"tl.fromTo('{sel}',{frm},{{{to},duration:{dur:.3f},ease:'{ease}',immediateRender:false}},{V.T(at):.3f});")

    def set_(sel, vals, at):
        p.js.append(f"tl.set('{sel}',{vals},{V.T(at):.3f});")

    move = y_pre - y_post
    p.hidden += ['#box', '#me', '#heart', '#hfill', '#cr'] + [f'#th{k}' for k in range(nr)] + [f'.a{k}' for k in range(n)] + [f'#rc{k}' for k in range(nr)]
    # the box is already at its low place when it fades up
    p.js.append(f"gsap.set('#box',{{y:{move:.1f}}});")
    ft('#box', f'{{autoAlpha:0,y:{move + 12 * u:.1f}}}', f'autoAlpha:1,y:{move:.1f}', 5 * F, 'power2.out', t_box)
    t = t_box + 6 * F
    while t < t_typed - .1 and t < t_fall:              # the caret blinks in the empty field
        set_('#phc', '{opacity:0}', t + .25)
        set_('#phc', '{opacity:1}', t + .5)
        t += .5
    # letters arrive from far away, one every 2 frames
    for k in range(n):
        ft(f'.a{k}', '{autoAlpha:0,scale:.32,y:-46,rotateX:38}', 'autoAlpha:1,scale:1,y:0,rotateX:0', 4 * F, 'expo.out', t_drop + k * 2 * F)
    # then each one falls into the box and turns into a typed letter
    ty_y = y_pre + box_h / 2
    tx = box_x + 118 * u
    bbox_mid = base - cap_ratio * size / 2
    from_ty = face(os.path.join('assets/fonts', 'InterTight-800-normal.woff2'), 800) if os.path.exists('assets/fonts/InterTight-800-normal.woff2') else ff
    land_last = t_fall
    for k, c in enumerate(word):
        cw = from_ty.getlength(word[:k]) / 1000 * ty_px + from_ty.getlength(c) / 2000 * ty_px
        lx = tx + cw - (pos[k][0] + pos[k][1] / 2)
        ly = ty_y - bbox_mid
        at = t_fall + k * 2 * F
        tilt = -10 + 20 * k / max(1, n - 1)
        ft(f'.a{k}', '{x:0,y:0,scale:1,rotateX:0,rotationZ:0}', f'x:{lx:.1f},y:{ly:.1f},scale:{ty_px / size * 1.2:.3f},rotateX:-32,rotationZ:{tilt:.1f}', 6 * F, 'power2.in', at)
        land = at + 6 * F
        set_(f'.a{k}', '{autoAlpha:0}', land)
        p.js.append(f"tl.set('#k{k}',{{display:'inline'}},{V.T(land):.3f});")
        land_last = land
        if k == 0:
            set_('#ph', '{autoAlpha:0}', land)
            set_('#cr', '{autoAlpha:1}', land)
            ft('#sgo', '{opacity:0}', 'opacity:1', 2 * F, 'none', land + F)
            if SOUND:
                p.sound('impact-bass-1', land, SOUND)
    # post: the comment lifts up and the button gives way to a heart
    set_('#cr', '{autoAlpha:0}', t_post)
    ft('#box', f'{{y:{move:.1f}}}', 'y:0', 5 * F, 'power3.out', t_post)
    ft('#me', '{autoAlpha:0}', 'autoAlpha:1', 3 * F, 'none', t_post + F)
    ft('#ty', '{y:0}', f'y:{16 * u:.1f}', 3 * F, 'power2.out', t_post)
    ft('#send', '{autoAlpha:1}', 'autoAlpha:0', 3 * F, 'none', t_post + F)
    ft('#heart', '{autoAlpha:0,scale:.7}', 'autoAlpha:1,scale:1', 3 * F, 'power2.out', t_post + 3 * F)
    # replies stack, each fades up glassy; the thread line draws to them; words come in one by one
    for k, words in enumerate(rw):
        tr = t_rep[k]
        ft(f'#rc{k}', '{autoAlpha:0,y:16,scale:.985}', 'autoAlpha:1,y:0,scale:1', 4 * F, 'power2.out', tr)
        ft(f'#th{k}', '{autoAlpha:0}', 'autoAlpha:1', 3 * F, 'none', tr + 3 * F)
        for i in range(len(words)):
            p.hidden.append(f'#r{k}w{i}')
            at = tr + 3 * F + i * max(F, (each - .15) / len(words))
            set_(f'#r{k}w{i}', '{autoAlpha:1}', at)
    # the like
    set_('#heart', '{autoAlpha:0}', t_like)
    ft('#hfill', '{autoAlpha:1,scale:1.5}', 'autoAlpha:1,scale:1', 6 * F, 'power3.out', t_like)
    # out: the comment lifts away first, the replies after it
    if t_out < s.dur:
        set_(','.join(f'#th{k}' for k in range(nr)), '{autoAlpha:0}', t_out)
        ft('#box', "{y:0,opacity:1,filter:'blur(0px)'}", f"y:{-40 * u:.1f},opacity:0,filter:'blur(5px)'", 4 * F, 'power2.in', t_out)
        for k in range(nr):
            ft(f'#rc{k}', "{y:0,opacity:1,filter:'blur(0px)'}", f"y:{-46 * u:.1f},opacity:0,filter:'blur(5px)'", 4 * F, 'power2.in', t_out + (k + 1) * 2 * F)
    p.write()
    print(f'  big letters {size:.0f} px, baseline y {base:.0f}; box {y_pre:.0f} then {y_post:.0f}; cards end {y_cards[-1] + box_h:.0f} (head top {s.head_top}), scale {u:.2f}')
    sn = [t_box + .12, t_drop + (n * 2 + 2) * F, t_fall + 5 * F, t_typed, t_rep[0] + .25, t_like + .2]
    print('snapshot at: ' + ','.join(f'{min(x_, s.dur - .05):.2f}' for x_ in sn))


if __name__ == '__main__':
    main()
