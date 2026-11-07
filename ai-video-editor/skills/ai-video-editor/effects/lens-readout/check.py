#!/usr/bin/env python3
"""Check the slot render (run from the slot folder, after hf render). Plain python, ffmpeg only.
Prints size and frame count against clip.json, says if the red guide was left in, writes work/check/sheet.jpg
(8 frames spread over the slot) and work/check/landing.jpg (every frame from the first letter on), and a phone copy."""
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
FF = shutil.which('ffmpeg') or 'ffmpeg'
FP = shutil.which('ffprobe') or 'ffprobe'


def main():
    name = os.path.basename(HERE)
    out = f'renders/{name}.mp4'
    if not os.path.exists(out):
        sys.exit(f'{out} is missing: render first')
    page = open('index.html', encoding='utf-8').read()
    if 'rgba(255,0,0,.28)' in page:
        print('!! index.html still has the red safe-zone guide: run build.py without SAFE=1 and render again')
    nfr = int(json.load(open('clip.json', encoding='utf-8'))['frames'])
    info = subprocess.run([FP, '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries',
                           'stream=width,height,nb_read_frames', '-of', 'csv=p=0', out], capture_output=True, text=True).stdout.strip().strip(',')
    ok = info == f'1080,1920,{nfr}'
    print(f'render: {info}  (want 1080,1920,{nfr})  {"OK" if ok else "!! WRONG"}')
    os.makedirs('work/check', exist_ok=True)
    picks = sorted({min(nfr - 1, round(k * (nfr - 1) / 7)) for k in range(8)})
    sel = '+'.join(f'eq(n\\,{f})' for f in picks)
    subprocess.run([FF, '-v', 'error', '-y', '-i', out, '-vf', f"select='{sel}',scale=270:480,tile={len(picks)}x1", '-frames:v', '1',
                    'work/check/sheet.jpg'], check=False)
    m = re.search(r"tl\.(?:fromTo|set)\('\.l0'.*?,([\d.]+)\);", page)
    f0 = round(float(m.group(1)) * 30) if m else 0
    subprocess.run([FF, '-v', 'error', '-y', '-i', out, '-vf', f"select='between(n\\,{f0}\\,{f0 + 19})',crop=1080:900:0:100,scale=360:-1,tile=5x4",
                    '-fps_mode', 'passthrough', '-frames:v', '1', 'work/check/landing.jpg'], check=False)
    print('LOOK at work/check/sheet.jpg and work/check/landing.jpg: the word behind the head, no letter in the red area, clean cutout edge')
    subprocess.run([FF, '-v', 'error', '-y', '-i', out, '-vf', 'scale=720:1280', '-c:v', 'libx264', '-crf', '27', '-preset', 'veryfast',
                    '-c:a', 'aac', '-b:a', '96k', f'renders/{name}-phone.mp4'], check=False)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
