"""Where the speaker's head is on every frame of the slot, measured from the slot's cutout (assets/subject.webm).

    track(slot) -> {'cx': [...], 'cy': [...], 'top': [...], 'chin': [...], 'width': median px, 'height': median px,
                    'measured': True when it came from the cutout, False when only layout.json's per-shot numbers}

Each shot is smoothed on its own (a cut never blends two head positions). The result is saved in work/head.json.
"""
import json
import os
import shutil
import subprocess

import numpy as np
from scipy import ndimage

W, H, Q = 1080, 1920, 4
FF = shutil.which('ffmpeg') or 'ffmpeg'


def shots(slot):
    """first frame of every shot inside the slot, from the reel's segments.json (or clip.json's cut_frames)"""
    cuts = set(int(k) for k in slot.clip.get('cut_frames') or [])
    proj, f0 = slot.clip.get('project'), int(slot.clip.get('frame') or 0)
    try:
        for g in json.load(open(os.path.join(proj, 'segments.json'), encoding='utf-8')):
            if f0 < g['frame'] < f0 + slot.frames:
                cuts.add(g['frame'] - f0)
    except (OSError, ValueError, TypeError, KeyError):
        pass
    return [0] + sorted(cuts) + [slot.frames]


def seg_size(slot, frame):
    """head height the reel's layout.json measured for the shot this frame is in, or None"""
    t = slot.t0 + frame / 30
    for g in (slot.layout or {}).get('segments') or []:
        if g.get('t0', 0) <= t + .02 < g.get('t1', 0) and g.get('chin') and g.get('head_top'):
            return float(g['chin'] - g['head_top']), g
    return None, None


def run_at(row, x):
    """the unbroken run of True around column x (or the nearest one) in one row -> (start, end) or None"""
    xs = np.where(row)[0]
    if not len(xs):
        return None
    cuts = np.where(np.diff(xs) > 2)[0]
    a, b = np.r_[xs[0], xs[cuts + 1]], np.r_[xs[cuts], xs[-1]]
    k = int(np.argmin(np.where((a <= x) & (b >= x), 0, np.minimum(abs(a - x), abs(b - x)))))
    return int(a[k]), int(b[k])


def one_frame(m, hint):
    rows = m.sum(1)
    ys = np.where(rows > 8)[0]
    if not len(ys):
        return None
    top = int(ys[0])
    cx = hint if hint is not None else float(np.where(m[top + 2])[0].mean())
    widths, mids = [], []
    for y in range(top, min(m.shape[0], top + 160)):
        r = run_at(m[y], cx)
        if r is None:
            break
        widths.append(r[1] - r[0] + 1)
        mids.append((r[0] + r[1]) / 2)
        if len(mids) < 24:                       # the crown steers the run search, the shoulders never do
            cx = .7 * cx + .3 * mids[-1]
    if len(widths) < 10:
        return None
    w = float(np.percentile(widths[: min(60, len(widths))], 60))
    return top * Q, float(np.median(mids[: min(60, len(mids))])) * Q, w * Q


def read_mattes(n):
    cmd = [FF, '-v', 'error', '-c:v', 'libvpx-vp9', '-i', 'assets/subject.webm', '-vf',
           f'alphaextract,scale={W // Q}:{H // Q}:flags=area', '-f', 'rawvideo', '-pix_fmt', 'gray', '-']
    raw = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H // Q, W // Q)[:n] > 127


def track(slot):
    n, bounds = slot.frames, shots(slot)
    if not os.path.exists('assets/subject.webm'):
        out = {'cx': [], 'cy': [], 'top': [], 'chin': [], 'measured': False}
        for f in range(n):
            size, g = seg_size(slot, f)
            if size is None:
                size, g = slot.chin - slot.head_top, {'cx': slot.cx, 'head_top': slot.head_top, 'chin': slot.chin}
            out['cx'].append(float(g['cx']))
            out['top'].append(float(g['head_top']))
            out['chin'].append(float(g['chin']))
            out['cy'].append((g['head_top'] + g['chin']) / 2)
        out.update(width=float(np.median(out['chin'])) * .5, height=float(np.median(np.array(out['chin']) - out['top'])))
        return out
    mattes = read_mattes(n)
    if len(mattes) < n:
        raise SystemExit(f'DECLINED: assets/subject.webm has {len(mattes)} frames, the slot {n}: make the slot again')
    t, x, w = np.zeros(n), np.zeros(n), np.zeros(n)
    hit = np.zeros(n, bool)
    for a, b in zip(bounds, bounds[1:]):
        hint = None
        for f in range(a, b):
            r = one_frame(mattes[f], hint)
            if r:
                t[f], x[f], w[f], hit[f] = r[0], r[1], r[2], True
                hint = r[1] / Q
    if hit.mean() < .9:
        raise SystemExit('DECLINED: the speaker is missing from the cutout on too many frames of this slot, so the head cannot be followed')
    size = np.zeros(n)
    for a, b in zip(bounds, bounds[1:]):
        idx = np.arange(a, b)
        ok = idx[hit[a:b]]
        if not len(ok):
            raise SystemExit(f'DECLINED: no speaker in the cutout on frames {a} to {b - 1}')
        for arr in (t, x, w):
            arr[a:b] = np.interp(idx, ok, arr[ok])
            arr[a:b] = ndimage.gaussian_filter1d(ndimage.median_filter(arr[a:b], 5, mode='nearest'), 1.6, mode='nearest')
        s, _ = seg_size(slot, a)
        wm = float(np.median(w[a:b]))
        # layout.json's chin is the better measure of the head's length. Without it: a head is about 1.45 widths tall
        size[a:b] = s if s and .9 * wm < s < 2.4 * wm else 1.45 * wm
    out = {'cx': x.round(1).tolist(), 'top': t.round(1).tolist(), 'chin': (t + size).round(1).tolist(),
           'cy': (t + size / 2).round(1).tolist(), 'width': float(np.median(w)), 'height': float(np.median(size)), 'measured': True}
    os.makedirs('work', exist_ok=True)
    json.dump(out, open('work/head.json', 'w'))
    return out
