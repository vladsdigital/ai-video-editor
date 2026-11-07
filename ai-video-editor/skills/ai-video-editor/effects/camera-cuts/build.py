#!/usr/bin/env python3
"""CAMERA CUTS: a hard cut becomes one camera move across it, chosen by name, with real motion blur: every frame of the
move is the average of many camera positions inside that frame's shutter, summed in linear light.

    whip   the picture tears sideways out of shot A and shot B arrives moving the same way
    zoom   a fast push into shot A that carries on through into shot B (for a dive through the speaker's clothes with
           the passage kept dark, use the zoom-through-cut effect: that one needs dark fabric, this one needs nothing)
    spin   a roll round the head that carries on through the cut
    push   shot B pushes shot A up and out of the frame, the two joined at the edge
    drop   the picture drops out of frame and shot B falls in from above, landing with a small bounce

Run from the slot folder. Bakes assets/plate.mp4 (a few seconds), writes index.html.
    build.py      (SAFE=1 safe-zone guide, SFX=0 no whoosh)
"""
import math
import os

import numpy as np
from PIL import Image

import plate as P

# ==== CLIP (edit this) ====
MOVE = 'whip'       # 'whip', 'zoom', 'spin', 'push', 'drop'
HALF = 4            # frames of the move on each side of the cut
STRENGTH = 1.0      # 1 = as designed. .6 is gentler
SHUTTER = 1.0       # 1 = the whole frame's time is blurred. .5 = a sharper, more stroby look
DIRECTION = 1       # whip: 1 tears to the left, -1 to the right. push: 1 up, -1 down
CENTRE = None       # (x, y) of zoom and spin. None = the measured face in each shot
WHOOSH = .3         # volume of one whoosh, its peak just before the cut. 0 = silent
# ==== END CLIP ====

MOVES = ('whip', 'zoom', 'spin', 'push', 'drop')
GAMMA = 2.2
LUT = (np.arange(256, dtype=np.float32) / 255) ** GAMMA
CURVE = 2.6               # how sharply the speed peaks on the cut


def pad(fr, px, py):
    return np.pad(fr, ((py, py), (px, px), (0, 0)), mode='reflect')


def warp(src, w, h, pxy, cx, cy, scale, angle, dx, dy):
    """the picture scaled and turned about (cx, cy), then moved by (dx, dy). w, h = output size; src is padded by pxy"""
    c, s = math.cos(angle) / scale, math.sin(angle) / scale
    a, b = c, s
    d, e = -s, c
    ox, oy = cx + dx, cy + dy
    co = (a, b, cx - a * ox - b * oy + pxy[0], d, e, cy - d * ox - e * oy + pxy[1])
    return np.asarray(src.transform((w, h), Image.AFFINE, co, Image.BILINEAR), np.uint8)


def camera(tau, cut, half):
    """(side, scale, angle, dx, dy) at time tau, in full-size px. side 'a' before the cut, 'b' after it"""
    side = 'a' if tau < cut - .5 else 'b'
    x = min(1.0, abs(tau - (cut - .5)) / half)
    k = (1 - x) ** CURVE * STRENGTH
    sg = 1 if side == 'a' else -1
    if MOVE == 'whip':
        return side, 1.0, 0.0, -sg * DIRECTION * k * P.W * .85, 0.0
    if MOVE == 'zoom':
        return side, math.exp(sg * k * (.85 if side == 'a' else .55)), 0.0, 0.0, 0.0
    if MOVE == 'spin':
        return side, 1 + .32 * k * STRENGTH, math.radians(sg * k * 34), 0.0, 0.0
    if MOVE == 'drop':
        return side, 1.0, 0.0, 0.0, sg * k * P.H * .9
    return side, 1.0, 0.0, 0.0, 0.0


def landing(tau, cut, half):
    """drop: a small damped bounce once shot B has landed"""
    t = tau - (cut - .5) - half
    if MOVE != 'drop' or t <= 0:
        return 0.0
    return -46 * STRENGTH * math.exp(-t / 3.2) * math.sin(t / 7 * 2 * math.pi)


def pad_for():
    return {'whip': (.88, .0), 'zoom': (.4, .4), 'spin': (.5, .3), 'drop': (.0, .92)}.get(MOVE, (0, 0))


def frame_push(a, k, f, half):
    """push: A and B joined at the edge, with one ease across the whole move; samples straddle the shutter"""
    out = np.zeros((P.H, P.W, 3), np.float32)
    n = 24
    for j in range(n):
        tau = f + (j + .5) / n * SHUTTER - SHUTTER / 2
        u = min(1.0, max(0.0, (tau - (k - .5 - half)) / (2 * half)))
        e = u * u * u * (u * (6 * u - 15) + 10)
        off = int(round(e * P.H)) * DIRECTION
        fa, fb = a[min(f, k - 1)], a[max(f, k)]
        if DIRECTION > 0:
            sample = np.vstack((fa[off:], fb[:off])) if off else fa
        else:
            off = -off
            sample = np.vstack((fb[P.H - off:], fa[:P.H - off])) if off else fa
        out += LUT[sample]
    return out / n


def frame_move(a, k, f, half, centres, cache, extra):
    samples = []
    speed = 0.0
    pv = None
    probe = 7
    for j in range(probe):
        tau = f + (j + .5) / probe * SHUTTER - SHUTTER / 2
        sd, sc, an, dx, dy = camera(tau, k, half)
        dy += landing(tau, k, half)
        point = (dx + (sc - 1) * 500 + an * 500, dy + (sc - 1) * 900 + an * 900)
        if pv is not None:
            speed += math.hypot(point[0] - pv[0], point[1] - pv[1])
        pv = point
    half_res = speed > 70
    q = 2 if half_res else 1
    n = int(min(40, max(1, math.ceil(speed / (5 * q)))))
    w, h = P.W // q, P.H // q
    out = np.zeros((h, w, 3), np.float32)
    fx, fy = pad_for()
    for j in range(n):
        tau = f + (j + .5) / n * SHUTTER - SHUTTER / 2
        sd, sc, an, dx, dy = camera(tau, k, half)
        dy += landing(tau, k, half)
        src_f = min(f, k - 1) if sd == 'a' else max(f, k)
        key = (src_f, q)
        if key not in cache:
            small = a[src_f] if q == 1 else np.asarray(Image.fromarray(a[src_f]).resize((w, h), Image.BOX))
            cache[key] = (Image.fromarray(pad(small, int(w * fx), int(h * fy))), (int(w * fx), int(h * fy)))
        img, pxy = cache[key]
        cx, cy = centres[sd]
        out += LUT[warp(img, w, h, pxy, cx / q, cy / q, sc, an, dx / q, dy / q)]
    out /= n
    if half_res:
        out = np.dstack([np.asarray(Image.fromarray(out[..., c]).resize((P.W, P.H), Image.BICUBIC)) for c in range(3)])
    return out


def main():
    if MOVE not in MOVES:
        P.die(f'MOVE "{MOVE}" is not one of: ' + ', '.join(MOVES))
    c = P.clip()
    n = int(c['frames'])
    tail = 7 if MOVE == 'drop' else 0
    k = P.cut_of(c, HALF + 2 + tail)
    a = P.frames(n)
    centres = {'a': tuple(CENTRE) if CENTRE else P.head_at(c, k - 1), 'b': tuple(CENTRE) if CENTRE else P.head_at(c, k)}
    if MOVE not in ('zoom', 'spin'):
        centres = {'a': (P.W / 2, P.H / 2), 'b': (P.W / 2, P.H / 2)}
    out = P.PlateWriter()
    f0, f1 = k - HALF, k + HALF + tail
    cache = {}
    os.makedirs('work', exist_ok=True)
    for f in range(n):
        if not (f0 <= f < f1):
            out.add(a[f])
            continue
        lin = frame_push(a, k, f, HALF) if MOVE == 'push' else frame_move(a, k, f, HALF, centres, cache, tail)
        fr = np.clip(lin, 0, 1) ** (1 / GAMMA) * 255 + .5
        out.add(fr)
    out.close()
    P.page(n, ('whoosh-short', (k - 1.5) / P.FPS - .12, .8, WHOOSH * .75) if WHOOSH else None, os.environ.get('SAFE') == '1', os.environ.get('SFX') != '0')
    print(f'{MOVE}: frames {f0} to {f1 - 1} of {n}, cut on frame {k}. assets/plate.mp4 and index.html written')
    print('snapshot at: ' + ','.join(f'{(f + .5) / P.FPS:.3f}' for f in range(f0, f1)))


if __name__ == '__main__':
    main()
