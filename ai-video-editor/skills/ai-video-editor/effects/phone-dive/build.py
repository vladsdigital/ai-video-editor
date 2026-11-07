#!/usr/bin/env python3
"""PHONE DIVE (transition): a dark title card with a small running timecode and a big serif line that rises in word by
word. It cuts to the shot, full frame. The shot then shrinks into a plain phone on the same flat colour, plays there
with a small time bar and the spoken words under it, and dives back until it fills the frame again.

Everything is drawn in the page. No logo, no real device, no real app.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html   (SAFE=1 safe-zone guide, SFX=0 no sounds, CAPTIONS=0 no words under the phone)
"""
import os
import shutil
import subprocess

os.environ.setdefault('PREVIEW', '1')     # the footage is what shrinks into the phone
import vgfx as V  # noqa: E402

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    ground='#163127',              # the card and the room behind the phone (deep forest green)
    title_font='Instrument Serif', # the big line on the card
    title_weight=400,
    title_size=118,
    title_case='upper',            # 'as-typed', 'lower' or 'upper'
    title_line=153,                # line height of the card's lines, px
    ink='#F4EFE2',                 # the big line (cream)
    tc='#F3EFE2',                  # the small timecode
    rule='#F3EFE2',                # the short line under the last word
    mono='JetBrains Mono',         # timecode and the phone's time bar
    body='#F4EFE2',                # the phone's frame (cream)
    cap_font='Newsreader',         # the words under the phone: set these to the reel's caption style
    cap_weight=400,
    cap_size=56,
    cap_case='as-said',            # 'as-said', 'lower' or 'upper'
    cap_on='#FFFFFF',              # a word that has been said
    cap_off='#7E9288',             # a word still to come
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
TITLE = None        # the card's lines: ['first', 'second', 'third']. Each line rises in as its first word is said (a line
                    # whose word is not said comes 0.45 s after the one before). None = one line per word said on the card
T_SHOT = None       # the card cuts to the shot (slot seconds). None = 35% of the slot
T_SHRINK = None     # the shot starts to shrink into the phone. None = 0.35 s after T_SHOT
T_GROW = None       # the phone starts to dive back. None = 0.35 s before the slot ends
SHRINK = .27        # the shrink, seconds
GROW = .27          # the dive back, seconds
PHONE = .48         # the phone's size against the screen when it lands
PHONE_END = .525    # and when the dive starts: it creeps up while it holds
PHONE_Y = 797       # where the middle of the phone sits, y
CAP_Y = 1361        # where the middle of the words under the phone sits, y
# ==== END CLIP ====

RADIUS = 165        # the corners of the screen at phone size, px before scaling
RING = 8            # the dark line round the screen, px before scaling
BEZEL = 52          # the frame's thickness, px before scaling
TC_Y = 659
LINE_0_Y = 787


def probe_len(path):
    out = subprocess.run([shutil.which('ffprobe') or 'ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                         capture_output=True, text=True).stdout.strip()
    try:
        return float(out)
    except ValueError:
        return 0.0


def clock(sec):
    return f'{int(sec // 60)}:{int(sec % 60):02d}'


def timecode(sec):
    return f'{int(sec // 3600):02d}:{int(sec // 60) % 60:02d}:{int(sec % 60):02d}:{int((sec % 1) * 30):02d}'


def title_case(s):
    m = STYLE['title_case']
    return s.upper() if m == 'upper' else s.lower() if m == 'lower' else s


def main():
    s = V.Slot()
    print('words: ' + s.word_list())
    print(s.where())
    S = STYLE
    t_shot = T_SHOT if T_SHOT is not None else s.dur * .35
    t_shr = T_SHRINK if T_SHRINK is not None else t_shot + .35
    t_grow = T_GROW if T_GROW is not None else s.dur - .35
    t_back = t_grow + GROW
    if t_back > s.dur - .02:
        V.die(f'the dive ends at {t_back:.2f} s and the slot at {s.dur:.2f} s: set T_GROW earlier')
    if t_grow - (t_shr + SHRINK) < .4 or t_shot < .5:
        V.die(f'the slot is too short at {s.dur:.2f} s: the card needs 0.5 s, the phone needs 0.4 s of hold. About 2.6 s or more')
    # ---- the card
    said = [w for w in s.words if w['start'] < t_shot - .1]
    if TITLE:
        rows = []
        prev = .1
        for line in TITLE:
            first = V.bare(line.split()[0]).lower()
            w = next((x for x in said if V.bare(x['text']).lower() == first and x['start'] >= prev - .01), None)
            at = w['start'] if w else prev + .45
            rows.append((line, at))
            prev = at
    else:
        rows = [(w['text'], w['start']) for w in said]
    if not rows:
        V.die('nothing is said on the card: write TITLE in the CLIP block or make T_SHOT later')
    if len(rows) > 4:
        V.die(f'the card holds 4 lines and it would get {len(rows)}: write TITLE with fewer lines')
    p = V.Page(s)
    ital = ''
    p.css.append(f"""
#card,#room{{position:absolute;left:0;top:0;width:1080px;height:1920px;background:{S["ground"]}}}
#tc{{position:absolute;left:0;right:0;top:{TC_Y - 16}px;height:32px;text-align:center;font:500 25px/32px '{S["mono"]}';letter-spacing:.09em;color:{S["tc"]}}}
.tl{{position:absolute;left:0;right:0;height:{S["title_line"]}px;overflow:hidden;text-align:center}}
.tl>span{{display:block;font-family:'{S["title_font"]}';font-weight:{S["title_weight"]};font-size:{S["title_size"]}px;line-height:{S["title_line"]}px;color:{S["ink"]};white-space:nowrap}}
#rule{{position:absolute;left:{540 - 118}px;width:236px;height:3px;background:{S["rule"]};transform-origin:50% 50%}}
#ph{{position:absolute;left:0;top:0;width:1080px;height:1920px;transform-origin:50% 50%}}
#body{{position:absolute;inset:0;border-radius:{RADIUS}px;box-shadow:0 0 0 {RING}px #0B0B0B,0 0 0 {RING + BEZEL}px {S["body"]},0 40px 90px {RING + BEZEL}px rgba(0,0,0,.34)}}
#scr{{position:absolute;inset:0;overflow:hidden;background:#000;border-radius:{RADIUS}px}}
#scr video{{position:absolute;left:0;top:0;width:1080px;height:1920px;object-fit:cover}}
.nub{{position:absolute;width:26px;background:{S["body"]};border-radius:8px}}
#hud{{position:absolute;left:70px;right:70px;top:1740px}}
#hudt{{font:500 38px/46px '{S["mono"]}';color:#fff;text-shadow:0 1px 8px rgba(0,0,0,.6)}}
#hudb{{margin-top:14px;height:7px;background:rgba(255,255,255,.3);border-radius:4px}}
#hudf{{width:100%;height:100%;background:#fff;border-radius:4px;transform-origin:0 50%}}
.cp{{position:absolute;left:0;right:0;top:{CAP_Y - 40}px;height:80px;line-height:80px;text-align:center;white-space:nowrap;font-family:'{S["cap_font"]}';font-weight:{S["cap_weight"]};font-size:{S["cap_size"]}px;color:{S["cap_off"]}}}
.cp span{{display:inline-block;margin:0 .13em}}""")
    # the card's words
    card = [f'<div id="tc">{timecode(s.t0)}</div>']
    for k, (line, at) in enumerate(rows):
        y = LINE_0_Y - S['title_line'] / 2 + k * S['title_line']
        card.append(f'<div class="tl" style="top:{y:.0f}px"><span id="tl{k}">{V.esc(title_case(V.bare(line) if not TITLE else line))}</span></div>')
        p.hidden.append(f'#tl{k}')
        p.js.append(f"tl.fromTo('#tl{k}',{{autoAlpha:1,y:{S['title_line']}}},{{autoAlpha:1,y:0,duration:.28,ease:'power3.out',immediateRender:false}},{V.T(at):.3f});")
    ry = LINE_0_Y - S['title_line'] / 2 + len(rows) * S['title_line'] + 14
    card.append(f'<div id="rule" style="top:{ry:.0f}px"></div>')
    p.hidden.append('#rule')
    p.js.append(f"tl.fromTo('#rule',{{autoAlpha:1,scaleX:0}},{{autoAlpha:1,scaleX:1,duration:.26,ease:'power2.out',immediateRender:false}},{V.T(rows[-1][1] + .14):.3f});")
    n_card = round(t_shot * V.FPS)
    for f in range(1, n_card):
        p.js.append(f"tl.set('#tc',{{textContent:'{timecode(s.t0 + f / V.FPS)}'}},{f / V.FPS - .002:.3f});")
    p.show('#card', 0.0, t_shot)
    # the phone: 1080 x 1920 scaled as a whole, so at scale 1 it IS the shot and its frame lies outside the screen
    reel_len = probe_len(s.clip.get('src') or '') if s.clip.get('project') else 0.0
    reel_len = reel_len or s.t0 + s.dur
    secs = sorted({int(s.t0 + t_shr + i * .1) for i in range(int((t_back - t_shr) * 10) + 1)})
    hud_txt = f'{clock(s.t0 + t_shr)} / {clock(reel_len)}'
    nubs = ''.join(f'<div class="nub" style="{side}:{-(RING + BEZEL + 22)}px;top:{y}px;height:{h}px"></div>'
                   for side, y, h in (('left', 420, 150), ('left', 610, 150), ('right', 500, 220)))
    p.html = [f'<div id="room"><div id="ph">{nubs}<div id="body"></div><div id="scr"><video id="phv" src="assets/aroll.mp4" muted playsinline '
              f'data-start="{t_shr:.4f}" data-media-start="{t_shr:.4f}" data-duration="{t_back - t_shr + .04:.4f}" data-track-index="3"></video>'
              f'<div id="hud"><div id="hudt">{hud_txt}</div><div id="hudb"><div id="hudf"></div></div></div></div></div></div>']
    for sec in secs[1:]:
        t = sec - s.t0
        if t_shr < t < t_back:
            p.js.append(f"tl.set('#hudt',{{textContent:'{clock(sec)} / {clock(reel_len)}'}},{V.T(t):.3f});")
    p.js.append(f"gsap.set('#hudf',{{scaleX:{(s.t0 + t_shr) / reel_len:.4f}}});")
    p.js.append(f"tl.to('#hudf',{{scaleX:{(s.t0 + t_back) / reel_len:.4f},duration:{t_back - t_shr:.3f},ease:'none'}},{V.T(t_shr):.3f});")
    p.show('#room', t_shr, t_back)
    dy0 = PHONE_Y - 960
    p.js.append(f"gsap.set('#ph',{{scale:1,y:0}});")
    p.js.append(f"tl.to('#ph',{{scale:{PHONE},y:{dy0},duration:{SHRINK - .012:.3f},ease:'power3.out'}},{V.T(t_shr):.3f});")
    p.js.append(f"tl.to('#ph',{{scale:{PHONE_END},duration:{t_grow - t_shr - SHRINK:.3f},ease:'sine.inOut'}},{V.T(t_shr + SHRINK):.3f});")
    p.js.append(f"tl.to('#ph',{{scale:1,y:0,duration:{GROW},ease:'power2.in'}},{V.T(t_grow):.3f});")
    for el in ('#body', '#scr'):
        p.js.append(f"gsap.set('{el}',{{borderRadius:0}});")
        p.js.append(f"tl.to('{el}',{{borderRadius:{RADIUS},duration:{SHRINK * .5:.3f},ease:'power2.out'}},{V.T(t_shr):.3f});")
        p.js.append(f"tl.to('{el}',{{borderRadius:0,duration:{GROW * .5:.3f},ease:'power2.in'}},{V.T(t_back - GROW * .5):.3f});")
    # the words under the phone
    caps_on = V.env('CAPTIONS', '1') != '0'
    if caps_on:
        ws = [w for w in s.words if t_shr - .3 <= w['start'] < t_grow + .05]
        lines, cur = [], []
        for w in ws:
            if cur and len(' '.join(x['text'] for x in cur + [w])) > 26:
                lines.append(cur)
                cur = []
            cur.append(w)
        if cur:
            lines.append(cur)
        html = []
        for j, row in enumerate(lines):
            spans = ''.join(f'<span id="c{j}w{m}">{V.esc(V.cased(w["text"], S["cap_case"]))}</span>' for m, w in enumerate(row))
            html.append(f'<div class="cp" id="c{j}">{spans}</div>')
            start = max(t_shr + SHRINK * .6, row[0]['start'])
            end = lines[j + 1][0]['start'] if j + 1 < len(lines) else t_grow + .04
            p.show(f'#c{j}', start, end)
            for m, w in enumerate(row):
                p.js.append(f"tl.to('#c{j}w{m}',{{color:'{S['cap_on']}',duration:.1,ease:'none'}},{V.T(max(start, w['start'])):.3f});")
        p.html.append(''.join(html))
        print('under the phone: ' + ' / '.join(' '.join(w['text'] for w in row) for row in lines))
    p.html.append(f'<div id="card">{"".join(card)}</div>')
    p.sound('whoosh-short', t_shr + .05, .3)
    p.sound('whoosh-short', t_back - .1, .4)
    p.write()
    print(f'  card to {t_shot:.2f}s, shot full, shrinks {t_shr:.2f}s, phone holds to {t_grow:.2f}s, back in full frame at {t_back:.2f}s')
    print(f'snapshot at: {rows[-1][1] + .3:.2f},{t_shot + .1:.2f},{t_shr + .06:.2f},{t_shr + SHRINK + .2:.2f},{t_grow + GROW * .6:.2f},{min(s.dur - .02, t_back + .02):.2f}')
    s.hide_hint([(0.0, t_shot)] + ([(t_shr, t_back)] if caps_on else []))


if __name__ == '__main__':
    main()
