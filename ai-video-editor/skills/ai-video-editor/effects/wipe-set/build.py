#!/usr/bin/env python3
"""WIPE SET: a shape wipe across one cut of the reel, chosen by name, with a thin light line on its edge.
Shot A plays up to the cut with shot B's first frame held in the shape; from the cut shot B plays and shot A's last
frame is held outside it. So both shots stay in sync with their sound, and the sound stays a straight cut.

Run from the slot folder. Bakes assets/plate.mp4 (a few seconds), writes index.html.
    build.py      (SAFE=1 safe-zone guide, SFX=0 no sound)
"""
import math
import os

import numpy as np

import plate as P

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    edge='#F4F1E6',     # the line on the wipe's edge
    edge_px=4.5,        # its width. 0 = no line
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
WIPE = 'iris'       # 'iris' (a circle opens from the face of the next shot), 'blinds', 'barn doors', 'clock wipe'
FRAMES = None       # frames the wipe takes, half before the cut, half after. None = the shape's own default
BLINDS = 9          # how many slats 'blinds' has
CENTRE = None       # (x, y) centre of 'iris' and 'clock wipe'. None = the measured face in the next shot
SOUND = 0.0         # volume of one soft whoosh on the cut. 0 = silent
# ==== END CLIP ====

SHAPES = {'iris': 6, 'blinds': 10, 'barn doors': 8, 'clock wipe': 12}     # frames each one takes by default
FR = 1 / P.FPS
YY, XX = np.mgrid[0:P.H, 0:P.W].astype(np.float32)


def rgb(hexcol):
    return np.array([int(hexcol[i:i + 2], 16) for i in (1, 3, 5)], np.float32)


def distance(u, centre):
    """px inside the shape (positive = shot B shows there) at progress u"""
    if WIPE == 'iris':
        far = max(math.hypot(x - centre[0], y - centre[1]) for x in (0, P.W) for y in (0, P.H)) + 12
        return far * u ** 2.1 - np.hypot(XX - centre[0], YY - centre[1])
    if WIPE == 'blinds':
        bar = P.H / BLINDS
        e = u * u * (3 - 2 * u)
        return e * (bar + 8) - (YY % bar)
    if WIPE == 'barn doors':
        e = u * u * (3 - 2 * u)
        return e * (P.W / 2 + 12) - np.abs(XX - P.W / 2)
    e = u * u * (3 - 2 * u)                      # clock: a hand sweeping clockwise from 12
    dx, dy = XX - centre[0], YY - centre[1]
    ang = np.mod(np.arctan2(dx, -dy), 2 * math.pi)
    rad = np.hypot(dx, dy)
    sweep = e * (2 * math.pi + .02)
    d = np.minimum(ang, sweep - ang) * rad
    return np.where(ang <= sweep, np.maximum(d, .75), -np.minimum(ang - sweep, 2 * math.pi - ang) * rad)


def bake(k, a, count, centre):
    edge, ew = rgb(STYLE['edge']), float(STYLE['edge_px'])
    out = P.PlateWriter()
    half = count // 2
    f0, f1 = k - half, k + count - half
    for f in range(len(a)):
        if not (f0 <= f < f1):
            out.add(a[f])
            continue
        u = (f - f0 + 1) / (count + 1)
        d = distance(u, centre)
        m = np.clip(d / 1.5 + .5, 0, 1)[..., None]
        sa = a[f] if f < k else a[k - 1]
        sb = a[k] if f < k else a[f]
        fr = sa * (1 - m) + sb * m
        if ew > 0:
            line = np.clip(ew / 2 + .75 - np.abs(d), 0, 1)[..., None]
            fr = fr * (1 - line) + edge * line
        out.add(np.clip(fr + .5, 0, 255))
    out.close()
    return f0, f1


def main():
    if WIPE not in SHAPES:
        P.die(f'WIPE "{WIPE}" is not one of: ' + ', '.join(SHAPES))
    c = P.clip()
    n = int(c['frames'])
    count = int(FRAMES or SHAPES[WIPE])
    k = P.cut_of(c, count // 2 + 2)
    centre = tuple(CENTRE) if CENTRE else P.head_at(c, k)
    a = P.frames(n)
    f0, f1 = bake(k, a, count, centre)
    P.page(n, ('whoosh-short', k * FR - .12, .8, SOUND) if SOUND else None, os.environ.get('SAFE') == '1', os.environ.get('SFX') != '0')
    print(f'{WIPE}: frames {f0} to {f1 - 1} of {n}, cut on frame {k}, centre ({centre[0]:.0f},{centre[1]:.0f}). assets/plate.mp4 and index.html written')
    print('snapshot at: ' + ','.join(f'{(f + .5) * FR:.3f}' for f in range(f0, f1, max(1, count // 6))))


if __name__ == '__main__':
    main()
