#!/usr/bin/env python3
"""Check the slot render (run from the slot folder, after hf render). Reads renders/<slot folder>.mp4 and prints / writes:
  - size and frame count against clip.json
  - whether the red safe-zone guide was left in index.html
  - how far the first frame is from the plain footage (a slot must start on the plain picture)
  - work/check/sheet.jpg: 12 frames spread over the slot, to LOOK at
  - renders/<slot folder>-phone.mp4 (720 x 1280 preview)
"""
import json
import os
import shutil
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
FF = shutil.which('ffmpeg') or 'ffmpeg'
FP = shutil.which('ffprobe') or 'ffprobe'


def grab(path, f):
    raw = subprocess.run([FF, '-v', 'error', '-i', path, '-vf', f"select='eq(n\\,{f})',scale=270:480", '-frames:v', '1',
                          '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(480, 270, 3).astype(float)


def main():
    name = os.path.basename(HERE)
    out = f'renders/{name}.mp4'
    if not os.path.exists(out):
        sys.exit(f'{out} is missing: render first')
    if 'rgba(255,0,0,.28)' in open('index.html', encoding='utf-8').read():
        print('!! index.html still has the red safe-zone guide: run build.py without SAFE=1 and render again')
    nfr = int(json.load(open('clip.json', encoding='utf-8'))['frames'])
    info = subprocess.run([FP, '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries',
                           'stream=width,height,nb_read_frames', '-of', 'csv=p=0', out], capture_output=True, text=True).stdout.strip().strip(',')
    ok = info == f'1080,1920,{nfr}'
    print(f'render: {info}  (want 1080,1920,{nfr})  {"OK" if ok else "!! WRONG"}')
    d = float(np.abs(grab(out, 0) - grab('assets/aroll.mp4', 0)).mean())
    print(f'first frame against the plain footage: difference {d:.2f}  ' + ('ok' if d < 6 else '!! not the plain picture'))
    ok &= d < 6
    os.makedirs('work/check', exist_ok=True)
    picks = sorted({min(nfr - 1, round(k * (nfr - 1) / 11)) for k in range(12)})
    sel = '+'.join(f'eq(n\\,{f})' for f in picks)
    subprocess.run([FF, '-v', 'error', '-y', '-i', out, '-vf', f"select='{sel}',scale=270:480,tile={len(picks)}x1",
                    '-fps_mode', 'passthrough', '-frames:v', '1', 'work/check/sheet.jpg'], check=False)
    print('sheet: work/check/sheet.jpg  frames ' + ', '.join(str(f) for f in picks) + '  LOOK at it')
    subprocess.run([FF, '-v', 'error', '-y', '-i', out, '-vf', 'scale=720:1280', '-c:v', 'libx264', '-crf', '27', '-preset',
                    'veryfast', '-c:a', 'aac', '-b:a', '96k', f'renders/{name}-phone.mp4'], check=False)
    print(f'phone copy: renders/{name}-phone.mp4')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
