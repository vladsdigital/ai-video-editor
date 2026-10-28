#!/usr/bin/env python3
"""Frame-exact QA of a render: the last frame before and first frame after every cut, in one strip, plus a phone copy.

Usage:  PY check_cuts.py <project_dir> <render.mp4> [--phone] [--loud]
Writes work/cut_check.jpg (pairs left->right: before|after for each cut). LOOK at it: every 'after' frame must show the
new shot with that section's look and no leftovers (room plates, cutout of the previous shot, stale captions).
Snapshots from `hyperframes snapshot` seek approximately at cuts; only frames pulled from the final render are proof.
--phone also writes <render>-phone.mp4 (720p, crf 26; SendUserFile uploads over ~5MB often fail, drop to crf 28).
<render.mp4> may be written the short way, "renders/<file>.mp4": it is looked up inside the project folder.
The last line is the loudness of the render (LUFS, as Instagram/TikTok/YouTube measure it) and what to do about it.
--loud writes <render>-loud.mp4 at -14 LUFS (two-pass, one linear gain, true peak under -1 dB; video copied untouched).
"""
import json
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True   # no __pycache__ next to the scripts (a plugin's folder is not ours to write in)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skillenv  # noqa: E402

skillenv.utf8_stdio()
FF = skillenv.tool('ffmpeg')
if len(sys.argv) < 3:
    sys.exit(__doc__)
proj = skillenv.path_arg(sys.argv[1])
render = skillenv.project_file(proj, sys.argv[2])            # "renders/x.mp4" is read inside the project
if not os.path.isfile(render):
    sys.exit(f'render not found: {render}')
with open(os.path.join(proj, 'segments.json'), encoding='utf-8') as fh:
    segs = json.load(fh)
cf = os.path.join(proj, 'work', 'cf')
sheet = os.path.join(proj, 'work', 'cut_check.jpg')
os.makedirs(cf, exist_ok=True)
pngs = []
for s in segs[1:]:
    for n in (s['frame'] - 1, s['frame']):
        p = os.path.join(cf, f'f{n}.png')
        subprocess.run([FF, '-loglevel', 'error', '-y', '-i', render, '-vf', f'select=eq(n\\,{n}),scale=150:-2', '-frames:v', '1', p], check=True)
        pngs.append(p)
if pngs:
    ins = sum((['-i', p] for p in pngs), [])
    subprocess.run([FF, '-loglevel', 'error', '-y', *ins, '-filter_complex', f'hstack={len(pngs)}', sheet], check=True)
    print('cuts at frames', [s['frame'] for s in segs[1:]], '->', sheet)
else:
    print('one continuous take: there are no cuts to check')
if '--phone' in sys.argv:
    out = os.path.splitext(render)[0] + '-phone.mp4'
    subprocess.run([FF, '-loglevel', 'error', '-y', '-i', render, '-vf', 'scale=720:-2', '-c:v', 'libx264', '-crf', '26', '-preset', 'slow',
                    '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', out], check=True)
    print('phone copy', out, f'{os.path.getsize(out) / 1e6:.1f} MB')

# how loud the voice is, as the platforms measure it (integrated loudness, LUFS). Instagram, TikTok and YouTube play
# talking-head reels at about -14 LUFS: much quieter sounds weak next to other reels, louder gets turned down.
TARGET, TRUE_PEAK = -14.0, -1.0


def loudness(path, extra_af=''):
    af = (extra_af + ',' if extra_af else '') + f'loudnorm=I={TARGET}:TP={TRUE_PEAK}:LRA=11:print_format=json'
    r = subprocess.run([FF, '-hide_banner', '-nostats', '-i', path, '-vn', '-af', af, '-f', 'null', '-'], **skillenv.TEXT)
    m = re.search(r'\{[^{}]*"input_i"[^{}]*\}', r.stderr or '', re.S)
    return json.loads(m.group(0)) if m else None


lv = loudness(render)
if not lv or lv.get('input_i') in (None, '-inf'):
    print('audio: NO SOUND found in the render. Check that the clip has a voice track before delivering.')
else:
    lufs, tp = float(lv['input_i']), float(lv['input_tp'])
    if '--loud' in sys.argv:
        # two-pass, linear: the whole reel moves by one gain, so the voice keeps its natural dynamics
        out = os.path.splitext(render)[0] + '-loud.mp4'
        meas = (f"loudnorm=I={TARGET}:TP={TRUE_PEAK}:LRA=11:measured_I={lv['input_i']}:measured_TP={lv['input_tp']}:"
                f"measured_LRA={lv['input_lra']}:measured_thresh={lv['input_thresh']}:offset={lv['target_offset']}:linear=true")
        subprocess.run([FF, '-loglevel', 'error', '-y', '-i', render, '-c:v', 'copy', '-af', meas, '-ar', '48000',
                        '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out], check=True)
        after = loudness(out) or {}
        print(f"loud copy {out}: {float(after.get('input_i', lufs)):.1f} LUFS (was {lufs:.1f})")
    if lufs < TARGET - 2.5:
        note = (f'quieter than other reels: offer the louder copy (run again with --loud: {TARGET:.0f} LUFS, '
                f'peaks kept under {TRUE_PEAK:.0f} dB) and deliver that one when they say yes')
    elif lufs > TARGET + 2:
        note = 'louder than the platforms play: fine, they turn it down by themselves'
    else:
        note = 'fine'
    print(f'audio: {lufs:.1f} LUFS, true peak {tp:.1f} dB -> {note}')
