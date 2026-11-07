#!/usr/bin/env python3
"""COVER BUILD: a whole magazine page builds behind the speaker's head on one line. A thin gold frame draws itself
from the top left corner, the masthead drops letter by letter (the letters flip dark over anything bright behind them),
a small line of type runs across above it, a barcode lands, coverlines rise on the words, a round sticker slaps on,
and the picture leaves through the next cut in a short zoom blur.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html   (SAFE=1 safe-zone guide, SFX=0 no sounds, CAPTIONS=0 accepted and ignored:
                                               the page is the effect)
"""
import json
import os

import vgfx as V

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
# Families must be ones assets/fonts/fonts.css provides.
STYLE = dict(
    mast_font='DM Serif Display',  # the masthead
    mast_weight=400,
    mast_blend='difference',       # letters flip dark over bright things behind them. 'normal' = solid letters
    small_font='JetBrains Mono',   # the small lines (top line, labels, barcode number)
    small_weight=500,
    line_font='Inter Tight',       # the coverlines
    line_weight=700,
    script_font='Pacifico',        # the big word on the sticker
    ink='#F3ECDE',                 # masthead (cream paper)
    line_ink='#F8F4EA',            # coverlines
    gold='#C4AA5E',                # frame and small labels
    paper='#F6F2E8',               # barcode ticket
    paper_ink='#1B1B16',
    sticker='#C6B562',             # the sticker
    sticker_ink='#2C2710',
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
MASTHEAD = ''           # the big word, in capitals. A word of the line, 4 to 8 letters. Required
TOP_LINE = ''           # the small line above it, for example 'BR. 01 · NOVEMBAR 2026 · MONTIRAO AI AGENT'. Required
LEFT = ('', [''])       # coverline: (small label, [one or two lines]). Words from the line. ('', []) = none
RIGHT = ('', [''])      # the same on the right
TICKET = ''             # the number line under the barcode, for example 'BR. 01 NOV 2026'. '' = no barcode
STICKER = ('', '', '')  # (small top word, script word, small bottom word). ('', '', '') = no sticker
# When each part lands: a word of the line (first word from there on that matches, a regular expression), or a slot
# second as a number, or None = the same rhythm as the default (spread over the time before the exit).
AT_START = None         # the frame starts drawing. None = 0.08 s before the first word
AT_BARCODE = None
AT_LEFT = None
AT_RIGHT = None
AT_STICKER = None
BOTTOM = None           # lower edge of the frame, screen px. None = just under the chin
STICKER_SIDE = None     # 'left' / 'right'. None = the side with more wall
SOUND = 0.30            # the sticker's tap. 0 = silent
# ==== END CLIP ====

SIDE = 40                      # frame inset from the left and right of the picture
EXIT_FRAMES = 4                # frames of zoom blur on each side of the cut


def text_width(font_file, text, size):
    """width of `text` in px without kerning, from the font file. None when the file cannot be read here."""
    try:
        from PIL import ImageFont
        f = ImageFont.truetype(font_file, 200)
        return sum(f.getlength(c) for c in text) * size / 200
    except Exception:
        return None


def face_metrics(font_file):
    """(cap height, baseline inside a line-height:1 box), both in em, from the font file. Fallback: the default face."""
    try:
        from PIL import ImageFont
        f = ImageFont.truetype(font_file, 1000)
        a, d = f.getmetrics()
        box = f.getbbox('H', anchor='ls')
        return -box[1] / 1000, ((1000 - (a + d)) / 2 + a) / 1000
    except Exception:
        return .66, .825


def when(s, cue, fallback, after):
    if cue is None:
        return fallback
    if isinstance(cue, (int, float)):
        return float(cue)
    w = s.find(cue, after)
    if not w:
        V.die(f'the word "{cue}" is not in this slot after {after:.2f}s. Words: {s.word_list()}')
    return w['start']


def bars(text, w, h):
    """plain made-up bars from the ticket text: never a real code"""
    x, out, k = 0.0, [], 7
    seed = [ord(c) for c in (text or 'x')]
    i = 0
    while x < w - 2:
        k = (k * 31 + seed[i % len(seed)]) % 97
        bw = 2 + k % 3 * 2
        if x + bw > w:
            break
        out.append(f'<rect x="{x:.0f}" y="0" width="{bw}" height="{h}"/>')
        x += bw + 2 + (k >> 3) % 3 * 2
        i += 1
    return ''.join(out)


def main():
    s = V.Slot()
    print('words: ' + s.word_list())
    print(s.where())
    if not MASTHEAD.strip() or not TOP_LINE.strip():
        V.die('write MASTHEAD and TOP_LINE in the CLIP block: words from the line this cover goes on')
    cuts = s.clip.get('cut_frames') or []
    cut = cuts[0] / V.FPS if cuts else s.dur
    first = s.words[0]['start'] if s.words else .1

    # ---------------------------------------------------------------- times (the rhythm: 23, 34, 42, 51 frames of 55)
    t0 = when(s, AT_START, max(.0, first - .08), 0)
    t_exit = cut - EXIT_FRAMES / V.FPS
    if t_exit - t0 < 1.5:
        V.die(f'only {t_exit - t0:.1f} s before the exit: the page needs about 1.8 s. Start the slot earlier or use a longer line')
    span = t_exit - t0
    t_bar = when(s, AT_BARCODE, t0 + span * .42, t0)
    t_left = when(s, AT_LEFT, t0 + span * .62, t0)
    t_right = when(s, AT_RIGHT, t0 + span * .76, t0)
    t_stick = when(s, AT_STICKER, t0 + span * .93, t0)
    t_stick = min(t_stick, t_exit - 3 / V.FPS)

    # ---------------------------------------------------------------- places, from the head
    top_safe = V.SAFE_TOP + 2
    has_lines = bool(LEFT[1] or RIGHT[1])
    n_lines = max(len(LEFT[1]), len(RIGHT[1]), 1)
    block = (24 + n_lines * 47 + 10) if has_lines else 0        # labels and coverlines
    mast_top_min = top_safe + 18 + block + 44                  # small line sits 34 px above the caps
    head_top, chin = s.head_top, s.chin
    room = head_top + 48 - mast_top_min                         # the letters reach 48 px down behind the head
    if room < 110:
        V.die(f'the head starts at y {head_top}: there is no room for a masthead under the safe zone. Leave this effect out on this shot')
    font_file = 'assets/fonts/DMSerifDisplay-400-normal.woff2'
    CAP, BASE = face_metrics(font_file)
    unit = text_width(font_file, MASTHEAD, 100)
    if unit is None:
        unit = 62.0 * len(MASTHEAD)
        print('note: could not measure the masthead font here, width is estimated: look at a snapshot')
    fs = min((1080 - 2 * SIDE - 85) / unit * 100, 196 / CAP, room / CAP)
    cap_h = fs * CAP
    mast_base = head_top + 48
    mast_cap_top = mast_base - cap_h
    if mast_cap_top < mast_top_min:
        mast_cap_top = mast_top_min
        mast_base = mast_cap_top + cap_h
    width = text_width(font_file, MASTHEAD, fs) or unit * fs / 100
    mast_left = (1080 - width) / 2
    top_y = mast_cap_top - 40
    L, T = SIDE, top_safe
    R = 1080 - SIDE
    B = int(BOTTOM if BOTTOM is not None else min(chin + 44, V.SAFE_RIGHT_FROM - 5))
    lab_y = T + 18
    head = (s.layout or {}).get('head') or {}
    room_r = R - int(head.get('side_right') or s.cx + 170)
    room_l = int(head.get('side_left') or s.cx - 170) - L
    side = STICKER_SIDE or ('right' if room_r >= 124 or room_r >= room_l else 'left')
    r_stick = min(84, max(room_r if side == 'right' else room_l, 0) / 2 - 2)
    if STICKER[1] and r_stick < 58:
        print(f'note: only {max(room_r, room_l)} px of wall beside the head: no sticker on this shot')
    stick_on = bool(STICKER[1]) and r_stick >= 58
    stick_x = (R - 12 - r_stick) if side == 'right' else (L + 12 + r_stick)
    stick_y = max(mast_base + r_stick + 40, chin - 232)
    tick_x, tick_y, tick_w = L + 26, mast_base + 108, 159
    if side == 'left' and stick_on:
        tick_x = R - 26 - tick_w
    print(f'  page: frame {L},{T} to {R},{B}; masthead {fs:.0f}px, caps y {mast_cap_top:.0f} to {mast_base:.0f}, {width:.0f} px wide; head top {head_top}, chin {chin}')
    if mast_left < V.SAFE_SIDE or mast_left + width > 1080 - V.SAFE_SIDE:
        V.die(f'the masthead "{MASTHEAD}" is too wide for the safe zone: pick a shorter word')

    # ---------------------------------------------------------------- the page
    S = STYLE
    w_page, h_page = R - L, B - T
    per = w_page + h_page
    letters = ''.join(f'<span class="ml" id="ml{k}">{V.esc(c) if c != " " else "&nbsp;"}</span>' for k, c in enumerate(MASTHEAD))
    frame = (f'<svg id="frame" width="1080" height="1920" viewBox="0 0 1080 1920" fill="none" stroke="{S["gold"]}" stroke-width="2.6">'
             f'<path id="fa" d="M{L} {T}H{R}V{B}" stroke-dasharray="{per}" stroke-dashoffset="{per}"/>'
             f'<path id="fb" d="M{L} {T}V{B}H{R}" stroke-dasharray="{per}" stroke-dashoffset="{per}"/></svg>')
    html = [frame, f'<div id="top" style="top:{top_y:.0f}px">{V.esc(TOP_LINE)}</div>',
            f'<div id="mast" style="left:{mast_left:.1f}px;top:{mast_base - fs * BASE:.1f}px;font-size:{fs:.1f}px">{letters}</div>']
    js = []
    tick_on = bool(TICKET)
    if tick_on:
        html.append(f'<div id="tick" style="left:{tick_x:.0f}px;top:{tick_y:.0f}px;width:{tick_w}px">'
                    f'<svg id="barsv" width="{tick_w - 18}" height="74" fill="{S["paper_ink"]}">{bars(TICKET, tick_w - 18, 74)}</svg>'
                    f'<div class="tn">{V.esc(TICKET)}</div></div>')

    def coverline(name, cl, right):
        label, lines = cl
        if not lines:
            return ''
        al = f'right:{1080 - R + 28}px;text-align:right' if right else f'left:{L + 28}px'
        rows = ''.join(f'<div class="clm"><div class="cl" id="{name}{k}">{V.esc(t)}</div></div>' for k, t in enumerate(lines))
        return f'<div class="cov" style="{al};top:{lab_y}px"><div class="lab" id="{name}L">{V.esc(label)}</div>{rows}</div>'

    html += [coverline('cvl', LEFT, False), coverline('cvr', RIGHT, True)]
    if stick_on:
        d = int(r_stick * 2)
        top_w, script, low = STICKER
        html.append(f'<div id="stick" style="left:{stick_x - r_stick:.0f}px;top:{stick_y - r_stick:.0f}px;width:{d}px;height:{d}px">'
                    f'<svg class="stx" width="{d}" height="{d}"><filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" seed="7"/>'
                    f'<feColorMatrix values="0 0 0 0 .16  0 0 0 0 .14  0 0 0 0 .05  0 0 0 -1.5 1"/></filter>'
                    f'<circle cx="{d / 2}" cy="{d / 2}" r="{d / 2}" filter="url(#grain)" opacity=".42"/></svg>'
                    f'<div class="st1" style="top:{d * .19:.0f}px;font-size:{d * .105:.0f}px">{V.esc(top_w)}</div>'
                    f'<div class="st2" style="top:{d * .285:.0f}px;font-size:{d * .205:.0f}px">{V.esc(script)}</div>'
                    f'<div class="st1" style="top:{d * .70:.0f}px;font-size:{d * .095:.0f}px">{V.esc(low)}</div></div>')

    # ---------------------------------------------------------------- the moves
    T = V.T
    fr = 1 / V.FPS
    js.append(f"tl.to('#fa,#fb',{{strokeDashoffset:0,duration:{11 * fr:.3f},ease:'power1.out'}},{T(t0):.3f});")
    t_mast = t0 + 2 * fr
    n = len(MASTHEAD)
    gap = 1.65 * fr if n <= 6 else 10 * fr / n
    for k in range(n):
        at = t_mast + k * gap
        js.append(f"tl.fromTo('#ml{k}',{{y:-{.36 * fs:.0f},autoAlpha:0}},{{y:0,duration:{7 * fr:.3f},ease:'power3.out',immediateRender:false}},{T(at):.3f});")
        js.append(f"tl.to('#ml{k}',{{autoAlpha:1,duration:{5 * fr:.3f},ease:'none'}},{T(at):.3f});")
    js.append(f"gsap.set('#top',{{clipPath:'inset(0 100% 0 0)'}}); tl.set('#top',{{autoAlpha:1}},{T(t0 + 5 * fr):.3f});")
    js.append(f"tl.to('#top',{{clipPath:'inset(0 0% 0 0)',duration:{10 * fr:.3f},ease:'none'}},{T(t0 + 5 * fr):.3f});")
    if tick_on:
        js.append(f"tl.set('#tick',{{autoAlpha:1}},{T(t_bar):.3f});")
        js.append(f"tl.fromTo('#barsv,#tick .tn',{{clipPath:'inset(0 100% 0 0)'}},{{clipPath:'inset(0 0% 0 0)',duration:{5 * fr:.3f},ease:'power1.out',immediateRender:false}},{T(t_bar + fr):.3f});")

    def rise(name, cl, at):
        if not cl[1]:
            return
        js.append(f"gsap.set('#{name}L',{{clipPath:'inset(0 100% 0 0)'}}); tl.set('#{name}L',{{autoAlpha:1}},{T(at):.3f});")
        js.append(f"tl.to('#{name}L',{{clipPath:'inset(0 0% 0 0)',duration:{6 * fr:.3f},ease:'none'}},{T(at):.3f});")
        for k in range(len(cl[1])):
            js.append(f"gsap.set('#{name}{k}',{{yPercent:105}}); tl.to('#{name}{k}',{{yPercent:0,duration:{7 * fr:.3f},ease:'power3.out'}},{T(at + (2 + 2 * k) * fr):.3f});")

    rise('cvl', LEFT, t_left)
    rise('cvr', RIGHT, t_right)
    if stick_on:
        js.append(f"tl.set('#stick',{{autoAlpha:1}},{T(t_stick):.3f});")
        js.append(f"tl.fromTo('#stick',{{scale:1.36,rotation:-3}},{{scale:1,rotation:-8,duration:{4 * fr:.3f},ease:'power3.out',immediateRender:false}},{T(t_stick):.3f});")
    # the exit: a zoom blur that peaks on the cut and clears on the next shot. Nothing of the page is left after the cut
    if cuts:
        js.append(f"tl.fromTo('#stage',{{scale:1,filter:'blur(0px)'}},{{scale:1.42,filter:'blur(30px)',duration:{EXIT_FRAMES * fr:.3f},ease:'power2.in',immediateRender:false}},{T(cut - EXIT_FRAMES * fr):.3f});")
        js.append(f"tl.set('#page',{{autoAlpha:0}},{T(cut):.3f});")
        js.append(f"tl.fromTo('#stage',{{scale:1.26,filter:'blur(24px)'}},{{scale:1,filter:'blur(0px)',duration:{EXIT_FRAMES * fr:.3f},ease:'power2.out',immediateRender:false}},{T(cut):.3f});")
    else:
        js.append(f"tl.fromTo('#stage',{{scale:1,filter:'blur(0px)'}},{{scale:1.42,filter:'blur(30px)',duration:{EXIT_FRAMES * fr:.3f},ease:'power2.in',immediateRender:false}},{T(s.dur - EXIT_FRAMES * fr):.3f});")
        print('note: this slot holds no cut, so the exit ends blurred on the last frame: the next shot has to follow it directly')

    # ---------------------------------------------------------------- sound, page
    audio = ''
    if SOUND and V.SFX_ON and stick_on and os.path.exists('assets/sfx/click-soft.mp3'):
        audio = (f'<audio id="sfx0" src="assets/sfx/click-soft.mp3" data-start="{max(0, t_stick - .01):.3f}" data-duration=".25" '
                 f'data-track-index="10" data-volume="{SOUND:.3f}"></audio>')
    dur = s.dur
    v = f'muted playsinline data-start="0" data-media-start="0" data-duration="{dur:.4f}"'
    blend = f"mix-blend-mode:{S['mast_blend']};" if S['mast_blend'] != 'normal' else ''
    css = f'''
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:#000}}
#root{{position:relative;width:1080px;height:1920px;overflow:hidden;background:#000}}
#stage{{position:absolute;inset:0;transform-origin:{s.cx}px {(head_top + chin) / 2:.0f}px}}
.lay{{position:absolute;left:0;top:0;width:1080px;height:1920px;display:block}}
#bgv{{z-index:0}}
#page{{position:absolute;inset:0;z-index:1}}
#subjw{{z-index:2}}
#frame{{position:absolute;left:0;top:0}}
#mast{{position:absolute;white-space:pre;font-family:'{S["mast_font"]}';font-weight:{S["mast_weight"]};color:{S["ink"]};line-height:1;font-kerning:none;{blend}}}
.ml{{display:inline-block;visibility:hidden}}
#top{{position:absolute;left:0;width:1080px;text-align:center;font-family:'{S["small_font"]}';font-weight:{S["small_weight"]};font-size:21px;letter-spacing:.2em;color:{S["ink"]};white-space:nowrap;visibility:hidden}}
#tick{{position:absolute;background:{S["paper"]};padding:9px 9px 7px;visibility:hidden}}
#tick svg{{display:block}}
#tick .tn{{font-family:'{S["small_font"]}';font-weight:700;font-size:13px;letter-spacing:.09em;color:{S["paper_ink"]};margin-top:6px;white-space:nowrap}}
.cov{{position:absolute}}
.lab{{font-family:'{S["small_font"]}';font-weight:{S["small_weight"]};font-size:19px;letter-spacing:.18em;color:{S["gold"]};line-height:24px;margin-bottom:6px;visibility:hidden;white-space:nowrap}}
.clm{{overflow:hidden;height:47px}}
.cl{{font-family:'{S["line_font"]}';font-weight:{S["line_weight"]};font-size:42px;line-height:47px;letter-spacing:-.022em;color:{S["line_ink"]};white-space:nowrap}}
#stick{{position:absolute;border-radius:50%;background:{S["sticker"]};color:{S["sticker_ink"]};visibility:hidden;overflow:hidden;box-shadow:0 3px 10px rgba(0,0,0,.28)}}
.stx{{position:absolute;left:0;top:0;mix-blend-mode:multiply}}
.st1,.st2{{position:absolute;left:0;width:100%;text-align:center;white-space:nowrap}}
.st1{{font-family:'{S["small_font"]}';font-weight:700;letter-spacing:.14em}}
.st2{{font-family:'{S["script_font"]}';line-height:1.2}}
'''
    page = f'''<!doctype html>
<html lang="sr" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<link rel="stylesheet" href="assets/fonts/fonts.css" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>{css}</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{dur:.4f}" data-width="1080" data-height="1920">
  <audio id="bga" src="assets/aroll.mp4" data-start="0" data-media-start="0" data-duration="{dur:.4f}" data-track-index="2" data-volume="1"></audio>
  {audio}
  <div id="stage">
    <video id="bgv" class="lay" src="assets/aroll.mp4" {v} data-track-index="0"></video>
    <div id="page">
    {chr(10).join(x for x in html if x)}
    </div>
    <div id="subjw" class="lay"><video id="subj" class="lay" src="assets/subject.webm" {v} data-track-index="1"></video></div>
  </div>
  {V.SAFE_GUIDE if V.SAFE else ''}
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
tl.set({{}}, {{}}, {dur:.3f});
window.__timelines["main"] = tl;
</script>
</body>
</html>
'''
    with open('index.html', 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(page)
    print(f'index.html written: {s.frames} frames ({dur:.2f}s), safe guide {"ON" if V.SAFE else "off"}')
    print(f'  frame starts {t0:.2f}s, barcode {t_bar:.2f}s, left {t_left:.2f}s, right {t_right:.2f}s, sticker {t_stick:.2f}s, exit {t_exit:.2f}s, cut {cut:.2f}s')
    print(f'snapshot at: {t0 + .2:.2f},{t0 + .5:.2f},{t_bar + .2:.2f},{t_left + .3:.2f},{t_stick + .15:.2f},{cut - .06:.2f},{cut + .04:.2f}')


if __name__ == '__main__':
    main()
