#!/usr/bin/env python3
"""COMMENT FLOW (call to action): a dark block wipes white and folds into a comment field at the top, a two-line
headline lands over it, the keyword types itself in and posts, a reply card slides in under it word by word, a like
lands on the comment, the cards lift away, then a follow pill rises at the chest and its button presses.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html   (SAFE=1 safe-zone guide, SFX=0 no sounds, CAPTIONS=0 accepted:
                                               the reel's own captions keep running under it)
"""
import os

import vgfx as V

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    font='Inter Tight',            # headline, keyword, names
    weight=800,
    tracking=-0.02,
    small_font='Inter',            # the small meta line and the reply's words
    small_weight=500,
    plate='#FFFFFF',               # headline plates and cards
    ink='#0F0F0F',                 # words on them
    mute='#9B9B96',                # placeholder and meta line
    green='#1F3D30',               # send and follow button (deep forest green)
    cream='#F4F1E4',               # the pressed button's fill (cream paper)
    sage='#7F9D8B',                # the plain avatar tile
    ring='#8FE3B6',                # the ring of the follow avatar
    heart='#B9506B',               # the like
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
HEADLINE = ['Link se nalazi ovde, a požuri',   # one or two short lines, the speaker's own words
            'dok cena nije skočila.']
KEYWORD = 'LINK'            # what types into the field. Required
PLACEHOLDER = 'Dodaj komentar...'
ME = 'ti'                   # the small name over the posted comment
NOW = 'sada'                # the small "now" after the names
HANDLE = 'vladsdigital'     # the buyer's handle, on the reply and on the follow pill. Required
REPLY = 'Link se nalazi ovde.'   # the reply, comes in word by word
FOLLOW = 'Zaprati'          # the button before the press
FOLLOWING = 'Pratiš'        # after it
SUB = '500+ aktivnih članova'    # small line that fades in under the name. Only something true. '' = none
AVATAR = ''                 # the buyer's own round picture in the slot's assets/, for reply and pill. '' = a plain letter tile
TIMES = {}                  # slot seconds, to overrule any step: type, post, reply, like, out, follow, press, sub
HEAD_Y = None               # top of the headline, screen px. None = the top of the safe zone
FOLLOW_Y = None             # centre of the follow pill. None = under the reel's caption line on the chest
SOUND = 0.3                 # the small ping when the button turns to FOLLOWING. 0 = silent
# ==== END CLIP ====

F = 1 / 30
HEART = ('M12 21s-7.5-4.6-10-9.2C.3 8.5 2.1 4.6 5.8 4.6c2.3 0 3.9 1.3 4.9 2.8.3.5 1.3.5 1.6 0 1-1.5 2.6-2.8 4.9-2.8 '
         '3.7 0 5.5 3.9 3.8 7.2C19.5 16.4 12 21 12 21z')
PERSON = '<circle cx="12" cy="9" r="3.9"/><path d="M4.6 20.4c.9-4 3.8-6 7.4-6s6.5 2 7.4 6c-2 .9-4.5 1.3-7.4 1.3s-5.4-.4-7.4-1.3z"/>'
ARROW = '<path d="M12 19V6M6.5 11.5 12 6l5.5 5.5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>'
CHECK = '<path d="M5 12.5 10 17 19 7.5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>'


def main():
    s = V.Slot()
    print('words: ' + s.word_list())
    print(s.where())
    if not KEYWORD.strip() or not HANDLE.strip() or not HEADLINE:
        V.die('write HEADLINE, KEYWORD and HANDLE in the CLIP block')
    if len(HEADLINE) > 2:
        V.die('HEADLINE takes one or two short lines')
    S = STYLE

    # ---- when: the keyword types as it is said, the rest keeps the look's rhythm, tightened to fit the slot
    w = s.find('^' + V.bare(KEYWORD) + '$')
    t_head = 8 * F
    t_type = float(TIMES.get('type', max(t_head + 4 * F, w['start'] if w else t_head + 7 * F)))
    n = len(KEYWORD)
    fixed = t_type + n * 2 * F + 16 * F
    gaps = [12, 22, 14, 16, 32, 9, 16]             # last letter>post, post>reply, reply>like, like>out, out>follow, follow>press, press>sub, in frames
    k = min(1.0, max(.35, (s.dur - fixed) / (sum(gaps) * F)))
    if s.dur - fixed < .35 * sum(gaps) * F:
        V.die(f'{s.dur:.1f} s is too short for the whole flow from the keyword on: it needs about {fixed + .35 * sum(gaps) * F:.1f} s')
    t, times = t_type + n * 2 * F, {}
    for name, g in zip(['post', 'reply', 'like', 'out', 'follow', 'press', 'sub'], gaps):
        t += g * F * k
        times[name] = float(TIMES.get(name, t))
    print(f'  pace {k:.2f} of the full rhythm: ' + ', '.join(f'{a} {b:.2f}' for a, b in times.items()))

    # ---- where: the whole top stack ends on the hair at most, and scales with the room over the head
    top = HEAD_Y if HEAD_Y is not None else V.SAFE_TOP + 8
    lines = len(HEADLINE)
    need = (80 * lines + 34 + 112 + 15 + 112)
    u = min(1.0, (s.head_top + 52 - top) / need)
    if u < .62:
        V.die(f'the head starts at y {s.head_top}: no room for the cards above it. It needs a wide or medium shot')
    hl_h, gap1, box_h, gap2 = 80 * u, 34 * u, 112 * u, 15 * u
    y_box = top + hl_h * lines + gap1
    y_rep = y_box + box_h + gap2
    box_x, box_w = 90, 900
    rep_x, rep_w = 90 + 80, 900 - 80
    pill_h = 114
    fy = FOLLOW_Y if FOLLOW_Y is not None else min(s.chest + 150, V.SAFE_BOTTOM - 10 - pill_h / 2)
    if fy - pill_h / 2 < s.chin - 30:
        V.die('no room for the follow pill under the chin on this clip')

    p = V.Page(s)
    fs = lambda v: f'{v * u:.1f}px'
    p.css.append(f'''
.pf{{position:absolute}}
#hl{{left:0;width:1080px;text-align:center;top:{top}px}}
.hp{{display:table;margin:0 auto;height:{hl_h:.1f}px;line-height:{hl_h:.1f}px;padding:0 {24 * u:.0f}px;background:{S['plate']};border-radius:{13 * u:.0f}px;
  font-family:'{S['font']}';font-weight:{S['weight']};letter-spacing:{S['tracking']}em;color:{S['ink']};font-size:{fs(52)};white-space:pre}}
.hp+.hp{{margin-top:-1px}}
#box{{left:{box_x}px;top:{y_box:.1f}px;width:{box_w}px;height:{box_h:.1f}px;background:{S['plate']};border-radius:{box_h / 2:.1f}px;overflow:hidden;box-shadow:0 8px 26px rgba(0,0,0,.13)}}
#wipe{{position:absolute;inset:0;background:{S['green']}}}
.av{{position:absolute;border-radius:50%;background:{S['sage']};overflow:hidden;display:flex;align-items:center;justify-content:center;color:#fff}}
.av svg{{width:72%;height:72%;fill:#fff}}
.av img{{width:100%;height:100%;object-fit:cover}}
.tile{{font-family:'{S['font']}';font-weight:800;line-height:1}}
#ty{{position:absolute;left:{112 * u:.1f}px;top:0;height:100%;display:flex;align-items:center;font-family:'{S['font']}';font-weight:700;font-size:{fs(35)};color:{S['ink']};white-space:pre}}
#ty span{{display:none}}
#cr{{display:inline-block;width:{2.6 * u:.1f}px;height:{fs(42)};background:{S['ink']};margin-left:2px}}
#ph{{position:absolute;left:{118 * u:.1f}px;top:0;height:100%;display:flex;align-items:center;font-family:'{S['small_font']}';font-weight:{S['small_weight']};font-size:{fs(30)};color:{S['mute']};white-space:pre}}
.meta{{font-family:'{S['small_font']}';font-weight:{S['small_weight']};font-size:{fs(25)};color:{S['mute']};white-space:pre;line-height:1}}
#me{{position:absolute;left:{112 * u:.1f}px;top:{24 * u:.1f}px}}
#send{{position:absolute;right:{22 * u:.1f}px;top:{(box_h - 68 * u) / 2:.1f}px;width:{68 * u:.1f}px;height:{68 * u:.1f}px;border-radius:50%;background:#D6DBD6;color:#fff;display:flex;align-items:center;justify-content:center}}
#send svg{{width:62%;height:62%}}
#sgo{{position:absolute;inset:0;border-radius:50%;background:{S['green']};opacity:0}}
#heart,#hfill{{position:absolute;right:{34 * u:.1f}px;top:{(box_h - 44 * u) / 2:.1f}px;width:{44 * u:.1f}px;height:{44 * u:.1f}px;overflow:visible}}
#rep{{left:{rep_x}px;top:{y_rep:.1f}px;width:{rep_w}px;height:{box_h:.1f}px;background:{S['plate']};border-radius:{30 * u:.1f}px;box-shadow:0 8px 26px rgba(0,0,0,.13);overflow:hidden}}
#rep .nm,#fo .nm{{font-family:'{S['font']}';font-weight:700;color:{S['ink']};white-space:pre;line-height:1}}
#rep .rl{{position:absolute;left:{112 * u:.1f}px;top:{22 * u:.1f}px;font-size:{fs(25)};display:flex;gap:.25em;align-items:baseline}}
#rt{{position:absolute;left:{112 * u:.1f}px;top:{56 * u:.1f}px;font-family:'{S['small_font']}';font-weight:{S['small_weight']};font-size:{fs(33)};line-height:1;color:{S['ink']};white-space:pre}}
#fo{{left:{(1080 - 700) / 2}px;top:{fy - pill_h / 2:.1f}px;width:700px;height:{pill_h}px;border-radius:{pill_h / 2}px;background:{S['plate']};box-shadow:0 8px 26px rgba(0,0,0,.16)}}
#fo .nm{{position:absolute;left:112px;top:0;line-height:{pill_h}px;font-size:33px}}
#fsub{{position:absolute;left:112px;top:62px;font-size:24px}}
#btn{{position:absolute;right:20px;top:{(pill_h - 70) / 2}px;width:232px;height:70px;border-radius:35px;overflow:hidden;background:{S['green']};font-family:'{S['font']}';font-weight:700;font-size:28px}}
#b1,#b2{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;gap:8px;white-space:pre}}
#b1{{color:{S['cream']}}}
#b2{{color:{S['ink']}}}
#b2 svg{{width:26px;height:26px}}
#bb{{position:absolute;inset:0;border-radius:35px;background:{S['cream']};border:2.5px solid {S['ink']}}}''')

    use_avatar = None
    if AVATAR:
        use_avatar = 'assets/' + AVATAR
        if not os.path.exists(use_avatar):
            V.die(f'AVATAR: {use_avatar} is not in the slot. Copy the buyer\'s picture there, or leave AVATAR empty')

    def avatar(size, left, top, ring=False):
        st = f'width:{size:.1f}px;height:{size:.1f}px;left:{left:.1f}px;top:{top:.1f}px;'
        if ring:
            st += f'box-shadow:0 0 0 {size * .07:.1f}px {S["ring"]};'
        if use_avatar:
            inner = f'<img src="{use_avatar}" alt="">'
        else:
            st += f'background:{S["green"]};font-size:{size * .5:.1f}px;'
            inner = f'<span class="tile">{V.esc(HANDLE[:1].upper())}</span>'
        return f'<div class="av" style="{st}">{inner}</div>'

    head = ''.join(f'<div class="hp">{V.esc(x)}</div>' for x in HEADLINE)
    p.html.append(f'<div id="hl" class="pf">{head}</div>')
    typed = ''.join(f'<span id="k{i}">{V.esc(c)}</span>' for i, c in enumerate(KEYWORD))
    a = 68 * u
    p.html.append(f'''<div id="box" class="pf">
<div id="av0" class="av" style="width:{a:.1f}px;height:{a:.1f}px;left:{24 * u:.1f}px;top:{(box_h - a) / 2:.1f}px"><svg viewBox="0 0 24 24">{PERSON}</svg></div>
<div id="ph">{V.esc(PLACEHOLDER)}</div>
<div id="me" class="meta">{V.esc(ME)} · {V.esc(NOW)}</div>
<div id="ty">{typed}<i id="cr"></i></div>
<div id="send"><div id="sgo"></div><svg viewBox="0 0 24 24" style="position:relative">{ARROW}</svg></div>
<svg id="heart" viewBox="0 0 24 24"><path d="{HEART}" fill="none" stroke="{S['ink']}" stroke-width="2"/></svg>
<svg id="hfill" viewBox="0 0 24 24"><path d="{HEART}" fill="{S['heart']}"/></svg>
<div id="wipe"></div>
</div>''')
    rw = REPLY.split()
    rwords = ' '.join(f'<span id="r{i}">{V.esc(x)}</span>' for i, x in enumerate(rw))
    p.html.append(f'''<div id="rep" class="pf">
{avatar(68 * u, 22 * u, (box_h - 68 * u) / 2)}
<div class="rl"><span class="nm">{V.esc(HANDLE)}</span><span class="meta">· {V.esc(NOW)}</span></div>
<div id="rt">{rwords}</div>
</div>''')
    p.html.append(f'''<div id="fo" class="pf">
{avatar(70, 22, (pill_h - 70) / 2, ring=True)}
<div id="fn" class="nm">{V.esc(HANDLE)}</div>
{'<div id="fsub" class="meta">' + V.esc(SUB) + '</div>' if SUB else ''}
<div id="btn"><div id="bb"></div><div id="b1">{V.esc(FOLLOW)}</div><div id="b2"><svg viewBox="0 0 24 24">{CHECK}</svg>{V.esc(FOLLOWING)}</div></div>
</div>''')
    def ft(sel, frm, to, dur, ease, at):
        p.js.append(f"tl.fromTo('{sel}',{frm},{{{to},duration:{dur:.3f},ease:'{ease}',immediateRender:false}},{V.T(at):.3f});")

    def set_(sel, vals, at):
        p.js.append(f"tl.set('{sel}',{vals},{V.T(at):.3f});")

    p.hidden += ['#hl', '#me', '#heart', '#hfill', '#rep', '#fo', '#ph', '#av0', '#sgo', '#cr', '#send', '#bb', '#b2', '#box'] + (['#fsub'] if SUB else [])

    # ---- the opening: a dark block wipes white from the left while it folds into the field, 7 frames
    t0 = float(TIMES.get('in', .0))
    bt0, bh0 = max(top, y_box - 186 * u), 380 * u
    set_('#box', '{autoAlpha:1}', t0)
    ft('#box', f'{{x:{135 - box_x},width:810,y:{bt0 - y_box:.1f},height:{bh0:.1f},borderRadius:{34 * u:.1f}}}',
       f'x:0,width:{box_w},y:0,height:{box_h:.1f},borderRadius:{box_h / 2:.1f}', 7 * F, 'power2.inOut', t0)
    ft('#wipe', "{clipPath:'inset(0 0 0 0%)'}", "clipPath:'inset(0 0 0 100%)'", 5 * F, 'power1.inOut', t0 + F)
    set_('#wipe', '{autoAlpha:0}', t0 + 6 * F)
    # the headline lands, a touch small, as the field settles
    ft('#hl', "{autoAlpha:0,scale:.93}", 'autoAlpha:1,scale:1', 3 * F, 'power2.out', t0 + t_head)
    set_('#av0,#ph,#send', '{autoAlpha:1}', t0 + t_head + F)
    set_('#cr', '{autoAlpha:1}', t0 + t_head)
    # typing, 2 frames a letter, the send button wakes on the first
    set_('#ph', '{autoAlpha:0}', t_type)
    for i in range(n):
        p.js.append(f"tl.set('#k{i}',{{display:'inline'}},{V.T(t_type + i * 2 * F):.3f});")
    ft('#sgo', '{autoAlpha:0}', 'autoAlpha:1', 2 * F, 'none', t_type + F)
    tp = times['post']
    # blink while waiting
    b = t_type + n * 2 * F + .3
    while b < tp - .1:
        set_('#cr', '{opacity:0}', b)
        set_('#cr', '{opacity:1}', b + .25)
        b += .5
    # post: button presses, the pill becomes a card, the small name appears, the button gives way to a heart
    ft('#send', '{scale:1}', 'scale:.86', 2 * F, 'power2.out', tp - 2 * F)
    ft('#send', '{scale:.86}', 'scale:1', 2 * F, 'power2.out', tp)
    set_('#cr', '{autoAlpha:0}', tp)
    ft('#box', f'{{borderRadius:{box_h / 2:.1f}}}', f'borderRadius:{30 * u:.1f}', 4 * F, 'power2.out', tp)
    ft('#me', '{autoAlpha:0}', 'autoAlpha:1', 3 * F, 'none', tp)
    ft('#ty', '{y:0}', f'y:{15 * u:.1f}', 3 * F, 'power2.out', tp)
    ft('#sgo', '{autoAlpha:1}', 'autoAlpha:0', 2 * F, 'none', tp + F)
    ft('#send', '{autoAlpha:1}', 'autoAlpha:0', 2 * F, 'none', tp + 2 * F)
    ft('#heart', '{autoAlpha:0,scale:.6}', 'autoAlpha:1,scale:1', 3 * F, 'back.out(2)', tp + 3 * F)
    # the reply fades up glassy under the comment, its words come in as a group, then one by one
    tr = times['reply']
    ft('#rep', '{autoAlpha:0,y:14,scale:.985}', 'autoAlpha:1,y:0,scale:1', 4 * F, 'power2.out', tr)
    tl_ = times['like']
    for i in range(len(rw)):
        at = tr + 3 * F + i * max(F, (tl_ - tr - 3 * F) / len(rw))
        p.hidden.append(f'#r{i}')
        set_(f'#r{i}', '{autoAlpha:1}', at if i else tr + 3 * F)
    # the like lands big and settles
    set_('#heart', '{autoAlpha:0}', tl_)
    ft('#hfill', '{autoAlpha:1,scale:1.5}', 'autoAlpha:1,scale:1', 6 * F, 'power3.out', tl_)
    # out: reply first, up and into the comment, then the comment, narrowing and blurring away
    to_ = times['out']
    ft('#rep', "{y:0,scale:1,opacity:1,filter:'blur(0px)'}", f"y:{-70 * u:.1f},scale:.9,opacity:0,filter:'blur(5px)'", 4 * F, 'power2.in', to_)
    ft('#box', "{y:0,x:0,scale:1,opacity:1,filter:'blur(0px)'}", f"y:{-46 * u:.1f},x:10,scale:.88,opacity:0,filter:'blur(6px)'", 5 * F, 'power2.in', to_ + F)
    # the follow pill rises, overshoots, settles
    tf = times['follow']
    ft('#fo', "{autoAlpha:0,y:46,scale:.96,filter:'blur(5px)'}", "autoAlpha:1,y:0,scale:1,filter:'blur(0px)'", 6 * F, 'back.out(1.5)', tf)
    # the press: the button squeezes, pales, the new label rolls up with its check
    tb = times['press']
    ft('#btn', '{scale:1}', 'scale:.9', 2 * F, 'power2.out', tb)
    ft('#btn', '{scale:.9}', 'scale:1', 4 * F, 'back.out(2)', tb + 2 * F)
    ft('#b1', '{autoAlpha:1,y:0}', 'autoAlpha:0,y:-14', 2 * F, 'none', tb + F)
    ft('#bb', '{autoAlpha:0}', 'autoAlpha:1', 2 * F, 'none', tb + F)
    ft('#b2', '{autoAlpha:0,y:26}', 'autoAlpha:1,y:0', 4 * F, 'power3.out', tb + 2 * F)
    if SOUND:
        p.sound('ping', tb + 2 * F, SOUND)
    if SUB:
        ts = times['sub']
        ft('#fn', '{y:0}', 'y:-16', 4 * F, 'power2.out', ts)
        ft('#fsub', '{autoAlpha:0}', 'autoAlpha:1', 4 * F, 'none', ts)
    p.write()
    print(f'  top stack {top} to {y_rep + box_h:.0f} (head top {s.head_top}), scale {u:.2f}; follow pill centre {fy}')
    sn = [t_type + n * F, tp + 6 * F, times['like'] + 5 * F, times['out'] + 3 * F, times['press'] - F, s.dur - .1]
    print('snapshot at: ' + ','.join(f'{min(x, s.dur - .05):.2f}' for x in sn))


if __name__ == '__main__':
    main()
