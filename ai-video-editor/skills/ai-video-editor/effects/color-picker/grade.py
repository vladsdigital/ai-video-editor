"""The colour looks of the grade effects, as a small helper each pack carries its own copy of (a pack stands alone).

A look is a set of tone curves per channel plus saturation, written as a .cube and baked onto the slot's own footage with
ffmpeg, so the page can lay the graded picture over the plain one and reveal it however the effect wants.
apply() gives the same result on single colours, so a palette on screen can show exactly what the grade does.

Needs numpy and ffmpeg. No footage, no outside files.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

import numpy as np

FF = shutil.which('ffmpeg') or 'ffmpeg'
FP = shutil.which('ffprobe') or 'ffprobe'
SPACE = ['-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv']

# Each curve: (in, out) points on 0-255, straight between points. sat: 1 = as is. tint: added after saturation, 0-255 scale.
# fit: how far the look's inputs may be lifted so a dark clip lands on the part of the curve the look was made for.
LOOKS = {
    # warm, glowing, more colour: reds and skin lift, blues hold
    'warm': dict(R=[(0, 0), (40, 53), (51, 66), (90, 104), (188, 217), (209, 245), (242, 255), (255, 255)],
                 G=[(0, 0), (37, 44), (49, 56), (77, 81), (165, 167), (185, 197), (236, 237), (255, 255)],
                 B=[(0, 0), (27, 30), (39, 40), (61, 60), (138, 134), (159, 155), (224, 212), (255, 235)],
                 sat=1.12, fit=205),
    # moody: half the light, most of the colour gone, a little green left in the greys
    'mood': dict(R=[(0, 0), (45, 16), (88, 37), (123, 60), (169, 83), (240, 113), (255, 159)],
                 G=[(0, 0), (35, 11), (76, 37), (109, 59), (157, 82), (224, 107), (255, 151)],
                 B=[(0, 0), (25, 9), (59, 31), (86, 53), (133, 77), (192, 103), (255, 138)],
                 sat=.42),
    # film: blacks crushed, shadows teal-green, highlights warm and rolled
    'film': dict(R=[(0, 0), (32, 4), (56, 19), (76, 39), (185, 154), (205, 195), (225, 238), (255, 255)],
                 G=[(0, 0), (32, 5), (55, 25), (77, 49), (167, 137), (188, 171), (225, 228), (255, 252)],
                 B=[(0, 2), (23, 6), (40, 22), (76, 50), (138, 103), (175, 150), (225, 203), (255, 235)],
                 sat=1.0, fit=205),
    # three steps down to dark and drained, ending blue-grey
    'drain1': dict(gain=.80, sat=.52, tint=(-2, 0, 3)),
    'drain2': dict(gain=.72, sat=.32, tint=(-3, 0, 4)),
    'drain3': dict(gain=.64, sat=.26, tint=(-4, 0, 6), toe=10),
}


def clip_level(src, frames=12):
    """where the clip's bright end sits (0-255), measured on frames spread over it"""
    cmd = [FF, '-v', 'error', '-i', src, '-vf', f'select=not(mod(n\\,{max(1, frames)})),scale=135:240,format=gray',
           '-fps_mode', 'passthrough', '-f', 'rawvideo', '-']
    raw = subprocess.run(cmd, capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8)
    if not a.size:
        sys.exit(f'could not read {src}')
    return float(np.percentile(a, 92))


def input_gain(look, level):
    """lift a dark clip into the look's range, never by more than 1.25 times, never darken a bright one"""
    ref = LOOKS[look].get('fit')
    return float(np.clip(ref / max(level, 1), 1.0, 1.25)) if ref else 1.0


def apply(rgb, look, gain_in=1.0):
    """rgb: array (..., 3) of 0-1 values -> the same colours through the look"""
    L = LOOKS[look]
    x = np.clip(np.asarray(rgb, float) * gain_in, 0, 1)
    if 'R' in L:
        out = np.stack([np.interp(x[..., i] * 255, *zip(*L[c])) / 255 for i, c in enumerate('RGB')], -1)
    else:
        out = x * L.get('gain', 1.0)
    grey = (out * (.2126, .7152, .0722)).sum(-1, keepdims=True)
    out = grey + (out - grey) * L.get('sat', 1.0)
    if 'toe' in L:
        t = L['toe'] / 255
        out = np.clip(out - t * np.clip(1 - out / .28, 0, 1), 0, 1)
    return np.clip(out + np.array(L.get('tint', (0, 0, 0))) / 255, 0, 1)


def write_cube(path, look, gain_in=1.0, size=33):
    g = np.linspace(0, 1, size)
    b, gg, r = np.meshgrid(g, g, g, indexing='ij')
    v = apply(np.stack([r, gg, b], -1).reshape(-1, 3), look, gain_in)
    with open(path, 'w', encoding='ascii', newline='\n') as fh:
        fh.write(f'LUT_3D_SIZE {size}\n')
        fh.writelines(f'{a:.5f} {c:.5f} {d:.5f}\n' for a, c, d in v)


def bake(src, dst, look, gain_in=1.0, grain=0, vignette=None):
    """src -> dst through the look, same frames, same colour tags. grain: moving film grain strength (0 = none).
    vignette: darkening at the corners, as an angle in radians (pi/5 is gentle, pi/3.4 is heavy). Done again only when asked differently."""
    key = json.dumps([LOOKS[look], gain_in, grain, vignette, os.path.getmtime(src)], sort_keys=True)
    stamp = 'work/bake_' + os.path.basename(dst) + '.txt'
    tag = hashlib.sha1(key.encode()).hexdigest()
    if os.path.exists(dst) and os.path.exists(stamp) and open(stamp).read() == tag:
        return dst
    os.makedirs('work', exist_ok=True)
    cube = f'work/{look}.cube'
    write_cube(cube, look, gain_in)
    vf = [f'scale=in_color_matrix=bt709:in_range=tv:out_range=pc:flags=accurate_rnd+full_chroma_int,format=gbrp',
          f'lut3d=file={cube}:interp=tetrahedral',
          'scale=out_color_matrix=bt709:in_range=pc:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuv420p']
    if vignette:
        vf.append(f'vignette=angle={vignette:.4f}')
    if grain:
        vf.append(f'noise=c0s={int(grain)}:c0f=t+u')
    r = subprocess.run([FF, '-v', 'error', '-y', '-i', src, '-an', '-vf', ','.join(vf), '-c:v', 'libx264', '-crf', '14',
                        '-preset', 'medium', '-pix_fmt', 'yuv420p'] + SPACE + [dst], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f'could not bake the {look} look: {r.stderr.strip()[-300:]}')
    with open(stamp, 'w') as fh:
        fh.write(tag)
    return dst


def hex_of(rgb):
    return '#' + ''.join(f'{int(round(float(c) * 255)):02X}' for c in np.clip(rgb, 0, 1))
