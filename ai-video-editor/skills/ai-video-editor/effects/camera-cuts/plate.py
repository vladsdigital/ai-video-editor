"""What a transition across a cut needs: the slot's frames, the cut, where the head is in each shot, a plate writer and
the page around the plate. Skill's Python only (numpy, Pillow)."""
import json
import os
import shutil
import subprocess
import sys

import numpy as np

W, H, FPS = 1080, 1920, 30
FF = shutil.which('ffmpeg') or 'ffmpeg'


def die(msg):
    print('DECLINED: ' + msg)
    sys.exit(2)


def clip():
    try:
        return json.load(open('clip.json', encoding='utf-8'))
    except (OSError, ValueError):
        die('clip.json is missing: make the slot with fx_new.py across one cut of the reel')


def cut_of(c, need):
    """the first frame of shot B. `need` frames have to exist on each side"""
    cuts = c.get('cut_frames') or []
    if len(cuts) != 1:
        die('this slot needs exactly one cut inside it: give fx_new.py a span about 0.5 s each side of one cut')
    k, n = int(cuts[0]), int(c['frames'])
    if k < need or n - k < need:
        die(f'the cut has {k} frames before it and {n - k} after it, and this move needs {need} on each side: widen --from / --to')
    return k


def frames(n):
    """every frame of the slot's a-roll as uint8 RGB, read as bt709"""
    raw = subprocess.run([FF, '-v', 'error', '-i', 'assets/aroll.mp4', '-vf', 'scale=in_color_matrix=bt709,format=rgb24',
                          '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    if len(a) < n:
        die(f'assets/aroll.mp4 has {len(a)} frames, the slot {n}: make the slot again')
    return a[:n]


class PlateWriter:
    """assets/plate.mp4: same frame count, tagged bt709 so the browser shows it exactly like the a-roll"""

    def __init__(self):
        self.p = subprocess.Popen([FF, '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                   '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p', '-c:v', 'libx264', '-crf', '12', '-preset', 'medium',
                                   '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-movflags', '+faststart', 'assets/plate.mp4'],
                                  stdin=subprocess.PIPE)

    def add(self, fr):
        self.p.stdin.write(np.asarray(fr, np.uint8).tobytes())

    def close(self):
        self.p.stdin.close()
        self.p.wait()


def head_at(c, frame):
    """(x, y) of the face at this slot frame, from the reel's layout.json; the frame's upper middle on a loose clip"""
    try:
        lay = json.load(open(os.path.join(c.get('project') or '.', 'layout.json'), encoding='utf-8'))
    except (OSError, ValueError):
        return W / 2, H * .42
    t = float(c.get('in') or 0) + frame / FPS
    for g in lay.get('segments') or []:
        if g.get('t0', 0) <= t + .02 < g.get('t1', 0) and g.get('chin'):
            return float(g.get('cx', W / 2)), (float(g.get('head_top', 500)) + float(g['chin'])) / 2
    h = lay.get('head') or {}
    if h.get('chin'):
        return float(h.get('cx', W / 2)), (float(h.get('top', 500)) + float(h['chin'])) / 2
    return W / 2, H * .42


GUIDE = ('<div style="position:absolute;inset:0;z-index:99;pointer-events:none">'
         '<div style="position:absolute;left:0;right:0;top:0;height:220px;background:rgba(255,0,0,.28)"></div>'
         '<div style="position:absolute;left:0;right:0;top:1470px;bottom:0;background:rgba(255,0,0,.28)"></div>'
         '<div style="position:absolute;left:0;width:35px;top:220px;height:1250px;background:rgba(255,0,0,.28)"></div>'
         '<div style="position:absolute;right:0;width:35px;top:220px;height:935px;background:rgba(255,0,0,.28)"></div>'
         '<div style="position:absolute;right:0;width:100px;top:1155px;height:315px;background:rgba(255,0,0,.28)"></div></div>')


def page(n, sound=None, safe=False, sfx_on=True):
    """index.html: the plate, the slot's own audio and at most one sound. sound = (name, second, length, volume)"""
    dur = int(n / FPS * 10000) / 10000     # rounded down: a duration rounded up renders one frame too many
    fx = ''
    if sound and sfx_on and os.path.exists(f'assets/sfx/{sound[0]}.mp3'):
        at = max(0.0, sound[1])
        fx = (f'<audio id="sfx0" src="assets/sfx/{sound[0]}.mp3" data-start="{at:.3f}" data-duration="{min(sound[2], dur - at):.3f}" '
              f'data-track-index="10" data-volume="{sound[3]:.3f}"></audio>')
    html = f'''<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:1080px;height:1920px;overflow:hidden;background:#000}}
#root{{position:relative;width:1080px;height:1920px;overflow:hidden}}.full{{position:absolute;left:0;top:0;width:1080px;height:1920px;object-fit:cover}}</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{dur:.4f}" data-width="1080" data-height="1920">
  <audio id="bga" src="assets/aroll.mp4" data-start="0" data-media-start="0" data-duration="{dur:.4f}" data-track-index="2" data-volume="1"></audio>
  {fx}
  <video id="bgv" class="full" src="assets/plate.mp4" muted playsinline data-start="0" data-media-start="0" data-duration="{dur:.4f}" data-track-index="0"></video>
  {GUIDE if safe else ''}
</div>
<script>
window.__timelines = window.__timelines || {{}};
window.__timelines["main"] = gsap.timeline({{ paused: true }});
</script>
</body>
</html>
'''
    with open('index.html', 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(html)
