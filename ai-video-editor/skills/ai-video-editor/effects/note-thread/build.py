#!/usr/bin/env python3
"""NOTE THREAD (explain / proof): at the top of the frame a small forest-green card fades in with two stills of the clip
and a line quoted from it, and a round name badge pops on its edge. A cream card rises over it, a note types itself out
under a name, the time stamp lands, and the card grows to let a reply line slide in. Then it all fades.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html   (SAFE=1 safe-zone guide, SFX=0 no sounds, CAPTIONS=0 accepted:
                                               the note IS the effect, so it always draws)
"""
import os
import shutil
import subprocess

import vgfx as V

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    font='Inter',                  # the note and the reply
    weight=500,
    name_weight=600,
    quote_font='Instrument Serif', # the quoted line on the green card
    quote_italic=True,
    mono_font='JetBrains Mono',    # time code on the green card
    card='#F7F3E8',                # the cream card
    ink='#1A1F1B',
    dim='#A29D8F',                 # the time stamp
    back='#133227',                # the green card (deep forest green)
    back_ink='#F3EFE2',
    badge='#6FE3B0',               # name badge of the note
    badge_ink='#14241C',
    reply_badge='#C9A95C',         # name badge of the reply
    reply_ink='#14241C',
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
NAME = ''           # who writes the note. Required
NOTE = ''           # the note that types out. Required. Up to about 60 characters (one line), 110 (two lines)
REPLY_NAME = ''     # who answers. Required. Never a real product's name unless the buyer asks
REPLY = ''          # the reply line. Required. Same length limits as NOTE
QUOTE = ''          # the line quoted on the green card. '' = NOTE
STAMP = 'now'       # the small word beside the name when the note is done
AVATAR = None       # a picture for the note's badge, in the slot's avatars/ folder. None = the name's first letter
REPLY_AVATAR = None # the same for the reply's badge
T_IN = None         # when the green card appears (slot seconds). None = 0.45 s before typing
T_TYPE = None       # when the note starts to type (a word or seconds). None = 0.35 s into the slot
T_REPLY = None      # when the reply slides in (a word or seconds). None = 0.25 s after the note is done
T_OUT = None        # when it all fades. None = 1.0 s after the reply, or the slot end
TYPE_RATE = .024    # seconds per letter
Y = None            # y of the bottom of the grown card, px. None = just above the head from layout.json
SCALE = None        # size against full size (cream card 1000 px wide). None = as large as the room above the head allows
SOUND = .3          # volume of the keys and the card. 0 = silent
# ==== END CLIP ====

# full size, px: everything scales together
CW, BACK_W, BACK_H, ROW_H, PAD, FS, AV, RAD = 1000, 690, 104, 66, 38, 29, 46, 24


def when(s, spec, default=None):
    if spec is None:
        return default
    if isinstance(spec, (int, float)):
        return float(spec)
    hit = s.find('^' + V.re.escape(V.bare(str(spec))) + '$')
    if not hit:
        V.die(f'the word "{spec}" is not in the words of this slot')
    return hit['start']


def wrap(text, cols):
    lines, cur = [], ''
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > cols:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + ' ' + w).strip()
    return lines + [cur] if cur else lines


def stills(s):
    """two stills of the slot's own clip for the green card, written into the slot's assets"""
    ff = shutil.which('ffmpeg') or 'ffmpeg'
    out = []
    for k, at in enumerate((s.dur * .25, s.dur * .7)):
        path = f'assets/note_still{k}.jpg'
        subprocess.run([ff, '-v', 'error', '-y', '-ss', f'{at:.3f}', '-i', 'assets/aroll.mp4', '-frames:v', '1', '-vf', 'scale=320:-2', '-q:v', '4', path], check=False)
        out.append(path if os.path.isfile(path) else None)
    return out


def badge(cls, name, image, fill, ink, size, font_px):
    face = f'<img src="avatars/{V.esc(image)}" alt="" style="width:100%;height:100%;object-fit:cover;display:block">' if image else V.esc(name.strip()[:1].upper())
    return (f'<div class="{cls}" style="width:{size}px;height:{size}px;background:{fill};color:{ink};font-size:{font_px}px">{face}</div>')


def main():
    s = V.Slot()
    s.dur = int(s.frames / V.FPS * 1e4) / 1e4      # rounded down: a page rounded up to the next 1/10000 s renders one frame too many
    print('words: ' + s.word_list())
    print(s.where())
    if not (NAME.strip() and NOTE.strip() and REPLY_NAME.strip() and REPLY.strip()):
        V.die('fill NAME, NOTE, REPLY_NAME and REPLY in the CLIP block')
    for image in (AVATAR, REPLY_AVATAR):
        if image and not os.path.isfile(os.path.join('avatars', image)):
            V.die(f'avatars/{image} is missing: put the buyer\'s picture in the slot\'s avatars/ folder, or use None')
    cols = int((CW - 2 * PAD) / (FS * .5))
    note_lines, reply_lines = wrap(NOTE, cols), wrap(REPLY, cols)
    if len(note_lines) > 2 or len(reply_lines) > 2:
        V.die('NOTE and REPLY each fit two lines, about 110 characters: shorten them')
    line_h = FS * 1.3
    first_h = PAD * .62 + ROW_H * .72 + line_h * len(note_lines) + PAD * .62
    full_h = first_h + ROW_H * .62 + line_h * len(reply_lines) + PAD * .55
    stack = BACK_H * .78 + full_h
    bottom = int(Y) if Y is not None else s.head_top - 12
    room = bottom - V.SAFE_TOP - 6
    k = SCALE if SCALE else min(1.0, room / stack, (1080 - 2 * V.SAFE_SIDE - 16) / CW)
    if k < .62:
        V.die(f'the note needs more room above the head than this clip has ({room} px between the safe zone and the head)')
    px = lambda v: round(v * k, 1)
    cw = px(CW)
    left = round((1080 - cw) / 2)
    top_full = bottom - px(full_h)
    back_top = top_full - px(BACK_H * .78)
    print(f'  note: scale {k:.2f} ({cw:.0f} px wide), green card from y {back_top:.0f}, cream card y {top_full:.0f} to {bottom}, room {room} px')

    t_type = when(s, T_TYPE, .35)
    t_in = T_IN if T_IN is not None else max(.02, t_type - .45)
    t_type = max(t_type, t_in + .38)      # the cream card is up before the first letter
    t_done = t_type + len(NOTE) * TYPE_RATE
    t_reply = when(s, T_REPLY, t_done + .25)
    if t_reply < t_done + .05:
        print(f'  note: the reply at {t_reply:.2f}s comes before the note is done at {t_done:.2f}s: moved it to just after')
        t_reply = t_done + .1
    t_out = T_OUT if T_OUT is not None else min(s.dur - .16, t_reply + 1.0)
    if t_out < t_reply + .4:
        print(f'  note: the reply is up only {t_out - t_reply:.2f}s: make the slot longer (--to)')

    S = STYLE
    p = V.Page(s)
    p.css.append(f'''
.nt-back{{position:absolute;left:{left + px(10)}px;top:{back_top:.1f}px;width:{px(BACK_W)}px;height:{px(BACK_H) + px(RAD)}px;border-radius:{px(10)}px {px(10)}px 0 0;background:{S["back"]};overflow:visible;box-shadow:0 {px(4)}px {px(14)}px rgba(0,0,0,.28)}}
.nt-still{{position:absolute;top:{px(10)}px;height:{px(BACK_H) + px(RAD) - px(10)}px;width:{px(150)}px;object-fit:cover;object-position:50% 25%;background:#0c0f0d}}
.nt-tc{{position:absolute;left:{px(360)}px;top:{px(16)}px;font-family:'{S["mono_font"]}';font-weight:500;font-size:{max(10, px(13))}px;letter-spacing:.14em;color:{S["back_ink"]};opacity:.75;white-space:nowrap}}
.nt-q{{position:absolute;left:{px(360)}px;top:{px(38)}px;right:{px(18)}px;font-family:'{S["quote_font"]}';font-style:{'italic' if S["quote_italic"] else 'normal'};font-size:{px(24)}px;line-height:1.1;color:{S["back_ink"]};white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.nt-pin{{position:absolute;left:{px(BACK_W - 118)}px;top:{px(-16)}px;border-radius:50%;overflow:hidden;display:flex;align-items:center;justify-content:center;font-family:'{S["font"]}';font-weight:{S["name_weight"]};line-height:1;box-shadow:0 {px(3)}px {px(8)}px rgba(0,0,0,.35)}}
.nt-card{{position:absolute;left:{left}px;top:{bottom - px(full_h) + px(0):.1f}px;width:{cw}px;height:{px(first_h)}px;border-radius:{px(RAD)}px;background:{S["card"]};color:{S["ink"]};overflow:hidden;box-shadow:0 {px(8)}px {px(26)}px rgba(0,0,0,.28)}}
.nt-row{{position:absolute;left:{px(PAD)}px;right:{px(PAD)}px;display:flex;align-items:center;gap:{px(14)}px;height:{px(ROW_H * .72)}px}}
.nt-av{{flex:none;border-radius:50%;overflow:hidden;display:flex;align-items:center;justify-content:center;font-family:'{S["font"]}';font-weight:{S["name_weight"]};line-height:1}}
.nt-name{{font-family:'{S["font"]}';font-weight:{S["name_weight"]};font-size:{px(FS)}px;line-height:1;white-space:nowrap}}
.nt-stamp{{font-family:'{S["font"]}';font-weight:{S["weight"]};font-size:{px(FS * .82)}px;line-height:1;color:{S["dim"]};white-space:nowrap}}
.nt-tx{{position:absolute;left:{px(PAD)}px;right:{px(PAD)}px;font-family:'{S["font"]}';font-weight:{S["weight"]};font-size:{px(FS)}px;line-height:{px(line_h)}px;white-space:pre-wrap}}
.nt-tx .ch{{display:none}}
.nt-caret{{display:inline-block;width:{max(2, px(3))}px;height:{px(FS * 1.04)}px;background:{S["ink"]};vertical-align:{px(-4)}px;margin-left:{px(2)}px}}''')
    a, b = stills(s)
    imgs = ''.join(f'<img class="nt-still" src="{src}" style="left:{px(10 + i * 165)}px" alt="">' for i, src in enumerate((a, b)) if src)
    stamp_at = s.t0 + t_type
    quote = QUOTE or NOTE
    pin = badge('nt-pin', NAME, AVATAR, S['badge'], S['badge_ink'], px(58), px(28))
    p.html.append(f'<div id="ntb" class="nt-back">{imgs}<div class="nt-tc">{int(stamp_at // 60):02d}:{stamp_at % 60:05.2f}</div>'
                  f'<div class="nt-q">{V.esc("„" + quote + "“")}</div><div id="ntn">{pin}</div></div>')
    note_text = '\n'.join(note_lines)
    chars = ''.join(f'<span id="ntk{i}" class="ch">{V.esc(c)}</span>' for i, c in enumerate(note_text))
    reply_top = px(first_h)
    reply_text = V.esc('\n'.join(reply_lines))
    p.html.append(
        f'<div id="ntc" class="nt-card">'
        f'<div class="nt-row" style="top:{px(PAD * .62)}px">{badge("nt-av", NAME, AVATAR, S["badge"], S["badge_ink"], px(AV), px(22))}<span class="nt-name">{V.esc(NAME)}</span><span id="nts" class="nt-stamp">{V.esc(STAMP)}</span></div>'
        f'<div class="nt-tx" style="top:{px(PAD * .62 + ROW_H * .72)}px">{chars}<span id="ntr" class="nt-caret"></span></div>'
        f'<div id="ntp" style="position:absolute;left:0;right:0;top:{reply_top - px(PAD * .1):.1f}px">'
        f'<div class="nt-row" style="top:0">{badge("nt-av", REPLY_NAME, REPLY_AVATAR, S["reply_badge"], S["reply_ink"], px(AV), px(22))}<span class="nt-name">{V.esc(REPLY_NAME)}</span></div>'
        f'<div class="nt-tx" style="top:{px(ROW_H * .62)}px">{reply_text}</div></div></div>')

    p.enter('#ntb', t_in, {'y': px(10)}, {'y': 0}, .14, ease='power2.out')
    p.enter('#ntn', t_in + .16, {'scale': .2}, {'scale': 1}, .17, ease='back.out(2.4)')
    t_card = t_type - .12
    p.enter('#ntc', t_card, {'y': px(30)}, {'y': 0}, .18, ease='power2.out')
    p.js.append(f"gsap.set('#nts,#ntp',{{autoAlpha:0}});")
    p.hidden.append('#nts')
    step = TYPE_RATE
    for i, ch in enumerate(note_text):
        p.js.append(f"tl.set('#ntk{i}',{{display:'inline'}},{V.T(t_type + i * step):.3f});")
    p.js.append(f"tl.set('#ntr',{{autoAlpha:0}},{V.T(t_done + .1):.3f});")
    p.js.append(f"tl.to('#nts',{{autoAlpha:1,duration:.1,ease:'none'}},{V.T(t_done + .06):.3f});")
    # the card grows, the reply slides in under the note
    p.js.append(f"tl.to('#ntc',{{height:{px(full_h)},duration:.22,ease:'power3.out'}},{V.T(t_reply):.3f});")
    p.js.append(f"tl.fromTo('#ntp',{{autoAlpha:0,y:{px(18)}}},{{autoAlpha:1,y:0,duration:.22,ease:'power2.out',immediateRender:false}},{V.T(t_reply + .04):.3f});")
    p.js.append(f"tl.to('#ntb,#ntc',{{autoAlpha:0,duration:.13,ease:'none'}},{V.T(t_out):.3f});")
    if SOUND:
        p.sound('click-soft', t_in + .16, SOUND)
        p.sound('pop', t_card, SOUND)
        p.sound('typing', t_type, SOUND * .8)
        p.sound('pop', t_reply, SOUND)
    print(f'  green card {t_in:.2f}s, cream card {t_card:.2f}s, types {t_type:.2f}s to {t_done:.2f}s, reply {t_reply:.2f}s, fades {t_out:.2f}s')
    p.write()
    print('snapshot at: ' + ','.join(f'{m:.2f}' for m in (t_in + .08, t_card + .08, (t_type + t_done) / 2, t_done + .2, t_reply + .1, t_reply + .4, t_out + .06)))


if __name__ == '__main__':
    main()
