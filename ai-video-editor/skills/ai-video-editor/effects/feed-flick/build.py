#!/usr/bin/env python3
"""FEED FLICK (hook / proof): a phone feed with plain generic buttons flicks past the buyer's own videos, faster and
faster with heavy vertical motion blur, then brakes hard on the speaker.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      cuts assets/feed.mp4 from the buyer's videos, writes index.html
                          (SAFE=1 safe-zone guide, SFX=0 no sounds, CAPTIONS=0 no caption line)
"""
import hashlib
import os
import subprocess

import numpy as np

import clipfx as X
import vgfx as V
from clipfx import F

# ==== STYLE (the reel's look wins: match the cap_ lines to the reel's caption style before building) ====
STYLE = dict(
    ui='#FFFFFF',                  # buttons and the small words of the feed
    ui_font='Inter',
    ui_weight=500,
    cap_font='Instrument Serif',   # the caption line (only drawn with CAPTIONS on: no reel captions)
    cap_weight=400,
    cap_size=66,
    cap_y=1356,
    cap_case='as-said',
    cap_ink='#F3EFE2',
    cap_wait='#86A98F',
    cap_plate='#1F3A2C',
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
CLIPS = 'clips'     # folder (inside the slot, or a full path) with the buyer's own videos, at least as many as HOLDS.
                    # File-name order is feed order. Each one needs about 0.3 s after SKIP
SKIP = 1.0          # seconds skipped at the start of each video
HOLDS = [2, 3, 3, 3, 2, 2, 2, 2]  # frames each video stays still between two flicks. Short = faster
WORD = ''           # the word the feed brakes on: the speaker is back on this word. '' = use T_LAND
T_LAND = None       # slot seconds of the braking frame. None = as early as the slot allows
HANDLE = ''         # the account name beside the small circle, the buyer's own. '' = the circle alone
FOLLOW = ''         # the word in the small pill, in the reel's language. '' = no pill
# ==== END CLIP ====

BLUR = .3           # length of the smear on a flick frame, as part of the frame height (one frame only)
LAND = 66           # px of smear left on the braking frame
ICONS = {           # plain line drawings, no real product's buttons. Drawn on a 48 x 48 box
    'heart': '<path d="M24 41 C10 30 5 23 5 16 C5 10 10 6 15 6 C19 6 22 8 24 12 C26 8 29 6 33 6 C38 6 43 10 43 16 C43 23 38 30 24 41Z"/>',
    'note': '<path d="M24 5 C13 5 5 13 5 23 C5 28 7 32 10 36 L8 43 L16 40 C18.500 41 21 42 24 42 C35 42 43 34 43 23 C43 13 35 5 24 5Z"/>',
    'swap': '<path d="M9 21 V16 C9 13 11 11 14 11 H38 M31 4 L38 11 L31 18 M39 27 V32 C39 35 37 37 34 37 H10 M17 44 L10 37 L17 30"/>',
    'send': '<path d="M5 7 H43 L25 43 L21 22 Z M21 22 L43 7"/>',
    'mark': '<path d="M11 5 H37 V43 L24 33 L11 43 Z"/>',
    'back': '<path d="M30 8 L14 24 L30 40"/>',
    'find': '<circle cx="21" cy="21" r="15"/><path d="M32 32 L43 43"/>',
}


def icon(name, x, y, size, col, stroke=3.4):
    return (f'<svg style="position:absolute;left:{x - size / 2:.0f}px;top:{y - size / 2:.0f}px" width="{size}" height="{size}" viewBox="0 0 48 48" '
            f'fill="none" stroke="{col}" stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>')


def frames_of(path, start, n, size=(1080, 1920)):
    """n frames from `start` seconds of a video, as an array [n, 1920, 1080, 3]"""
    w, h = size
    vf = f'fps=30,scale={w}:{h}:force_original_aspect_ratio=increase:flags=bicubic,crop={w}:{h}'
    raw = subprocess.run([X.FF, '-v', 'error', '-ss', f'{start:.3f}', '-i', path, '-an', '-vf', vf, '-frames:v', str(n), '-f', 'rawvideo',
                          '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    got = len(raw) // (w * h * 3)
    if got < n:
        V.die(f'{os.path.basename(path)} gave {got} frames from {start:.1f} s and {n} are needed: give a longer video or lower SKIP')
    return np.frombuffer(raw, 'u1').reshape(n, h, w, 3)


def smear(strip, centre, length):
    """vertical motion blur: the mean of `length` rows around each row of the frame that starts at row `centre`"""
    length = max(2, int(length))
    c = np.cumsum(strip.astype(np.float32), axis=0)
    c = np.concatenate([np.zeros((1,) + strip.shape[1:], np.float32), c])
    top = np.arange(1920) + centre - length // 2
    a = np.clip(top, 0, len(strip))
    b = np.clip(top + length, 0, len(strip))
    out = (c[b] - c[a]) / np.maximum(b - a, 1)[:, None, None]
    return out.clip(0, 255).astype('u1')


def soft(img, length):
    """the same smear on one frame, a second pass makes the ends of it fade instead of stopping dead"""
    return smear(np.concatenate([img[:1].repeat(length, 0), img, img[-1:].repeat(length, 0)]), length, length)


def main():
    s = V.Slot()
    print('words: ' + s.word_list())
    n_flick = len(HOLDS)
    total = 1 + sum(h + 1 for h in HOLDS)         # first flick, then each video and the flick after it
    f_land = None
    if WORD:
        w = s.find('^' + V.re.escape(V.bare(WORD)) + '$')
        if not w:
            V.die(f'WORD "{WORD}" is not said in this slot. Words: {s.word_list()}')
        f_land = round(w['start'] * V.FPS)
    elif T_LAND is not None:
        f_land = round(T_LAND * V.FPS)
    f0 = (f_land - total) if f_land is not None else 3
    f_land = f0 + total
    if f0 < 2:
        V.die(f'the feed needs {total} frames ({total / V.FPS:.1f} s) before it brakes and the slot only has {f_land - total + total} there: start the slot about {(2 - f0) / V.FPS + .1:.1f} s earlier')
    if f_land + 6 > s.frames:
        V.die(f'the slot ends too soon: it needs at least {f_land + 6} frames and has {s.frames}')
    clips = X.videos(CLIPS, n_flick, .35, SKIP, 'videos (their reels or clips)')

    # ---- the feed picture, frame by frame, with real motion blur on the flick frames
    sig = hashlib.sha1(repr((clips, HOLDS, BLUR, LAND, f0, s.frames, os.path.getmtime('assets/aroll.mp4'))).encode()).hexdigest()[:10]
    os.makedirs('assets/tiles', exist_ok=True)
    feed = f'assets/tiles/feed-{sig}.mp4'
    if not os.path.exists(feed):
        for old in os.listdir('assets/tiles'):
            os.remove(os.path.join('assets/tiles', old))
        enc = subprocess.Popen([X.FF, '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920', '-r', '30', '-i', '-', '-c:v', 'libx264',
                                '-crf', '15', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', feed], stdin=subprocess.PIPE)
        speaker = frames_of('assets/aroll.mp4', 0, f_land + 2)
        L = int(1920 * BLUR)
        prev = speaker[f0]
        for k, hold in enumerate(HOLDS):
            frames = frames_of(clips[k][0], clips[k][1], hold + 2)
            enc.stdin.write(smear(np.concatenate([prev, frames[0]]), 960, L).tobytes())
            for j in range(hold):
                enc.stdin.write(frames[j + 1].tobytes())
            prev = frames[hold + 1]
        arrive = speaker[f_land]
        enc.stdin.write(smear(np.concatenate([prev, arrive]), 960, L).tobytes())
        rows = np.arange(1920) + int(LAND * .6)
        enc.stdin.write(soft(arrive, LAND)[np.where(rows > 1919, 2 * 1919 - rows, rows)].tobytes())
        enc.stdin.close()
        if enc.wait() != 0:
            V.die('could not write the feed picture')

    # ---- the page
    st = STYLE
    p = X.Comp(s, st)
    ui, col = 'ui', st['ui']
    p.css.append(f'''
#feedw{{position:absolute;inset:0;opacity:0}}
#{ui}{{position:absolute;inset:0;opacity:0;filter:drop-shadow(0 1px 5px rgba(0,0,0,.6))}}
#{ui} .who{{position:absolute;left:138px;top:1832px;font-family:'{st["ui_font"]}';font-weight:{st["ui_weight"]};font-size:30px;color:{col};white-space:nowrap;line-height:44px}}
#{ui} .pill{{display:inline-block;margin-left:20px;padding:0 20px;border:2px solid {col}B0;border-radius:12px;font-size:27px;line-height:40px}}
#{ui} .dot{{position:absolute;left:44px;top:1822px;width:66px;height:66px;border-radius:50%;background:{col}38;border:3px solid {col}}}
#bar{{position:absolute;left:1048px;width:4px;height:150px;border-radius:2px;background:{col};opacity:0}}''')
    p.under.append(f'<div id="feedw">{p.video(feed, F(f0), F(total + 1))}</div>')
    bits = [icon('back', 90, 84, 62, col), icon('find', 1000, 84, 62, col)]
    for name, y in (('heart', 1080), ('note', 1248), ('swap', 1416), ('send', 1596), ('mark', 1770)):
        bits.append(icon(name, 1005, y, 66, col))
    bits.append('<div class="dot"></div>')
    if HANDLE or FOLLOW:
        pill = f'<span class="pill">{V.esc(FOLLOW)}</span>' if FOLLOW else ''
        bits.append(f'<div class="who">{V.esc(HANDLE)}{pill}</div>')
    p.over.append(f'<div id="{ui}">{"".join(bits)}</div><div id="bar"></div>')

    p.set('#feedw', F(f0), opacity=1)
    p.set('#feedw', F(f_land + 1), opacity=0)
    f = f0
    p.sound('whoosh-short', F(f0), .3)
    for k, hold in enumerate(HOLDS):
        p.set('#ui', F(f + 1), opacity=1)
        p.set('#ui', F(f + 1 + hold), opacity=0)
        if k:
            p.sound('click-soft', F(f), .1 + .012 * k)
        f += hold + 1
    p.sound('whoosh-short', F(f_land - 1), .26)
    p.sound('click-soft', F(f_land), .22)
    for j in range(total):             # the thin scroll mark walks down the side, the one thing that stays through the blur
        p.set('#bar', F(f0 + j), top=int(228 + 40 * j), opacity=.9)
    p.set('#bar', F(f_land), opacity=0)
    if V.env('CAPTIONS', '1') != '0':
        p.captions(0, s.dur)
    p.write()
    print(f'first flick at {F(f0):.2f}s, {n_flick} videos, brakes at {F(f_land):.2f}s, sharp at {F(f_land + 1):.2f}s')
    print(f'snapshot at: {F(f0):.2f},{F(f0 + 1):.2f},{F(f0 + 3):.2f},{F(f0 + 12):.2f},{F(f_land):.2f},{F(f_land + 2):.2f}')


if __name__ == '__main__':
    main()
