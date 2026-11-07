#!/usr/bin/env python3
"""PICTURE LOOP (proof): a thin frame comes in from the edges of the screen, and the whole shot shrinks inside it into a
framed picture on the wall, while the speaker stays in front at full size. The picture holds the same live shot with
the same picture in it, several levels deep. Then the picture bursts back out, the speaker pushing past the camera, and
the frame lands on the plain shot.

It is a real recursion of the live frame: every level is the frame of that moment, composed in this script.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes assets/loop.mp4 (about 1 min, kept while nothing changes) and index.html
                          (SAFE=1 safe-zone guide, SFX=0 no sounds)
"""
import hashlib
import json
import os
import shutil
import subprocess

os.environ.setdefault('PREVIEW', '1')     # the picture is made from the footage, so the footage is part of the page
import cv2  # noqa: E402
import numpy as np  # noqa: E402
import vgfx as V  # noqa: E402

# ==== STYLE (the reel's look wins) ====
STYLE = dict(
    line='#F1EBDD',                # the frame of the picture (cream)
    line_px=5,                     # its thickness on the first level, px
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
T_IN = None         # the frame appears and the shot starts to shrink (slot seconds). None = 0.1 s
T_BURST = None      # the picture starts to burst back out. None = 0.48 s before the slot ends
SHRINK = .26        # the shrink, seconds
BURST = .23         # the burst, seconds
SCALE = .55         # size of the picture against the screen. Each level is this much smaller than the one around it
LEVELS = 4          # how many pictures deep
SIDE = None         # 'left' or 'right' side of the screen. None = the side with more wall beside the head
TOP = .258          # height of the point the levels run into, 0 = top of the screen, 1 = bottom
PUSH = 1.9          # how large the speaker gets at the end of the burst
# ==== END CLIP ====

W, H = 1080, 1920


def ease_out3(u):
    return 1 - (1 - u) ** 3


def ease_in2(u):
    return u * u


def params(s):
    t_in = T_IN if T_IN is not None else .1
    t_burst = T_BURST if T_BURST is not None else s.dur - .48
    t_end = t_burst + BURST
    if t_in < .03 or t_end > s.dur - .05:
        V.die(f'the burst ends at {t_end:.2f} s and the slot at {s.dur:.2f} s: set T_BURST earlier, the last frames must be the plain shot')
    if t_burst - (t_in + SHRINK) < .4:
        V.die(f'the slot is too short: the picture only holds for {t_burst - t_in - SHRINK:.2f} s. It needs about 1.2 s or more')
    side = SIDE
    if side is None:
        side = 'left' if s.cx >= W / 2 else 'right'
    return t_in, t_burst, t_end, side


def frames_of(path, n0, n1, decoder=None, pix='bgr24', channels=3):
    """frames n0 .. n1-1 as arrays"""
    cmd = [shutil.which('ffmpeg') or 'ffmpeg', '-v', 'error']
    if decoder:
        cmd += ['-c:v', decoder]
    cmd += ['-i', path, '-vf', f"select='between(n\\,{n0}\\,{n1 - 1})'", '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', pix, '-']
    pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    size = W * H * channels
    try:
        while True:
            raw = pipe.stdout.read(size)
            if len(raw) < size:
                return
            yield np.frombuffer(raw, np.uint8).reshape(H, W, channels)
    finally:
        pipe.stdout.close()
        pipe.wait()


def place(frame, inner, s_now, fx, fy, line, thick):
    """inner (the frame with its deeper pictures) shrunk to s_now around the fixed point, on top of the frame"""
    w, h = max(2, round(W * s_now)), max(2, round(H * s_now))
    x, y = round(fx * W * (1 - s_now)), round(fy * H * (1 - s_now))
    pic = cv2.resize(inner, (w, h), interpolation=cv2.INTER_AREA)
    if thick > 0:
        cv2.rectangle(pic, (0, 0), (w - 1, h - 1), line, thick, cv2.LINE_AA)
    out = frame.copy()
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    out[y0:y1, x0:x1] = pic[y0 - y:y1 - y, x0 - x:x1 - x]
    return out


def over(under, top, alpha):
    a = alpha[..., None].astype(np.float32) / 255
    return (top * a + under * (1 - a)).astype(np.uint8)


def compose(frame, alpha, s_now, fx, fy, line, push, head_xy):
    """one frame: the picture recursion on the wall, and the speaker in front"""
    inner = frame
    for k in range(LEVELS - 1, -1, -1):        # deepest first
        thick = max(2, round(STYLE['line_px'] * s_now ** (k * .55))) if s_now < .999 else STYLE['line_px']
        wall = place(frame, inner, s_now, fx, fy, line, thick)
        inner = over(wall, frame, alpha) if k > 0 else wall
    if push <= 1.0001:
        return over(inner, frame, alpha)
    M = np.float32([[push, 0, head_xy[0] * (1 - push)], [0, push, head_xy[1] * (1 - push)]])
    big = cv2.warpAffine(frame, M, (W, H), flags=cv2.INTER_LINEAR)
    big_a = cv2.warpAffine(alpha, M, (W, H), flags=cv2.INTER_LINEAR)
    return over(inner, big, big_a)


def make(s, t_in, t_burst, t_end, side):
    if not os.path.isfile('assets/subject.webm'):
        V.die('no cutout in this slot (assets/subject.webm): make the slot with the clean cutout')
    n0, n1 = round(t_in * V.FPS), round(t_end * V.FPS)
    key = hashlib.md5(json.dumps([n0, n1, side, SHRINK, BURST, SCALE, LEVELS, TOP, PUSH, STYLE, s.frames]).encode()).hexdigest()
    os.makedirs('work', exist_ok=True)
    stamp = 'work/loop.key'
    if os.path.isfile('assets/loop.mp4') and os.path.isfile(stamp) and open(stamp).read() == key:
        print('  assets/loop.mp4: kept, nothing changed')
        return
    h = STYLE['line'].lstrip('#')
    line = (int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16))
    fx = .985 if side == 'right' else .015
    head_xy = (s.cx, (s.head_top + s.chin) / 2)
    enc = subprocess.Popen([shutil.which('ffmpeg') or 'ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(V.FPS),
                            '-i', '-', '-an', '-c:v', 'libx264', '-crf', '13', '-preset', 'medium', '-pix_fmt', 'yuv420p', 'assets/loop.mp4'], stdin=subprocess.PIPE)
    done, seen = 0, 0.0
    subj = frames_of('assets/subject.webm', n0, n1, decoder='libvpx-vp9', pix='rgba', channels=4)
    for k, frame in enumerate(frames_of('assets/aroll.mp4', n0, n1)):
        rgba = next(subj, None)
        if rgba is None:
            V.die('the cutout has fewer frames than the shot: make the slot again')
        alpha = rgba[..., 3]
        seen += float((alpha > 128).mean())
        t = (n0 + k) / V.FPS
        if t < t_in + SHRINK:
            s_now = 1 + (SCALE - 1) * ease_out3((t - t_in) / SHRINK)
            push = 1.0
        elif t < t_burst:
            s_now, push = SCALE, 1.0
        else:
            u = ease_in2(min(1.0, (t - t_burst) / (BURST - 1 / V.FPS)))
            s_now, push = SCALE + (1 - SCALE) * u, 1 + (PUSH - 1) * u
        enc.stdin.write(compose(frame, alpha, s_now, fx, TOP, line, push, head_xy).tobytes())
        done += 1
    enc.stdin.close()
    enc.wait()
    if done != n1 - n0:
        V.die(f'made {done} frames of {n1 - n0}: make the slot again')
    if seen / done < .03:
        V.die('the cutout holds almost nothing on this shot: there is no speaker to keep in front of the picture')
    if seen / done > .75:
        V.die('the speaker fills most of the frame on this shot: the picture on the wall would not show')
    with open(stamp, 'w') as fh:
        fh.write(key)
    print(f'  assets/loop.mp4: {done} frames')


def main():
    s = V.Slot()
    print(s.where())
    t_in, t_burst, t_end, side = params(s)
    make(s, t_in, t_burst, t_end, side)
    p = V.Page(s)
    p.css.append('#loop{position:absolute;left:0;top:0;width:1080px;height:1920px;object-fit:cover}')
    n0, n1 = round(t_in * V.FPS), round(t_end * V.FPS)
    p.html.append(f'<video id="loop" src="assets/loop.mp4" muted playsinline data-start="{n0 / V.FPS:.4f}" data-media-start="0" '
                  f'data-duration="{(n1 - n0) / V.FPS:.4f}" data-track-index="3"></video>')
    p.sound('whoosh-short', t_in + .05, .3)
    p.sound('whoosh-short', t_burst + BURST * .5, .45)
    p.write()
    print(f'  side {side}. frame in at {t_in:.2f}s, picture holds from {t_in + SHRINK:.2f}s, bursts {t_burst:.2f} to {t_end:.2f}s')
    print(f'snapshot at: {t_in + .07:.2f},{t_in + SHRINK + .1:.2f},{(t_in + t_burst) / 2 + .1:.2f},{t_burst + BURST * .7:.2f},{t_end + .03:.2f}')


if __name__ == '__main__':
    main()
