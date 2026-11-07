#!/usr/bin/env python3
"""FILE DROP (explain): a forest green drop-zone card with a dashed line appears above the head. A file card with the raw
clip's real name and length falls in from the top, tilted, and lands in it. The card and the zone go glassy and open into
a small player of the real raw clip, sped up, with its length on a pill. Red rubber stamps slam on. Then it fades.

Graphics only (an overlay): the reel lays them over its own footage. A plain generic card, no real app's screen, no logo.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes assets/raw.mp4, assets/raw_thumb.jpg and index.html  (SAFE=1 guide + footage, SFX=0 no sounds)
"""
import json
import os
import shutil
import subprocess

import vgfx as V

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    zone='#163127',                # the drop zone (deep forest green)
    dash='#D8D3BC',                # its dashed line, icon and text
    zone_font='Inter',             # the text in the zone
    zone_weight=500,
    file_bg='#FBFAF6',             # the file card
    file_ink='#161616',            # its name
    file_dim='#6A675C',            # its small line
    name_font='Inter Tight',       # the file name and the pill
    name_weight=800,
    mono='JetBrains Mono',         # the file's small line, the speed badge, the stamps
    pill_bg='#FBFAF6',             # the pill under the player
    pill_ink='#161616',
    pill_num='#C23A46',            # the length on the pill
    stamp_bg='#F4E4DA',            # the stamp's paper
    stamp_ink='#B8323F',           # the stamp's line and word (red)
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
DROP_TEXT = 'Drop your clip here'     # the line in the drop zone, in the buyer's language
PILL_TEXT = 'of footage'       # after the length on the pill, in the buyer's language
STAMPS = ['WRONG TAKE', 'WRONG TAKE']  # one or two stamps, the buyer's words, up to about 12 letters
RAW_FILE = None     # the raw clip. None = the one this slot was cut from in the reel, else the slot's own clip
FILE_NAME = None    # the name on the card. None = the raw clip's real name
SPEED = 2.3         # how fast the player runs the clip
T_IN = None         # the zone appears (slot seconds). None = 0.1 s
T_FILE = None       # the file card starts to fall. None = 0.55 s after T_IN
T_OPEN = None       # the file opens into the player. None = 0.5 s after T_FILE
T_STAMP = None      # the first stamp. None = 0.45 s after T_OPEN
T_OUT = None        # it fades. None = 0.2 s before the slot ends
# ==== END CLIP ====

ZONE_W, ZONE_H_MAX = 798, 495
ZONE_TOP = 228
HEAD_GAP = 14
CHIN_PAD = .35                 # room left under the measured chin on the chest, against the head's height
ZONE_H_MIN = 240
PLAYER_W_MAX = 336
FILE_W = 585


def run(*a):
    return subprocess.run(a, capture_output=True, text=True)


def probe(path, entries):
    return run(shutil.which('ffprobe') or 'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', entries, '-of', 'csv=p=0', path).stdout.strip()


def clock(sec):
    return f'{int(sec // 60)}:{int(round(sec % 60)):02d}'


def raw_source(s):
    """the raw clip and where this slot starts in it: (path, seconds)"""
    if RAW_FILE:
        return RAW_FILE, 0.0
    proj = s.clip.get('project')
    if proj:
        try:
            segs = json.load(open(os.path.join(proj, 'segments.json'), encoding='utf-8'))
            src = json.load(open(os.path.join(proj, 'sources.json'), encoding='utf-8'))
        except (OSError, ValueError):
            segs, src = [], {}
        f0 = s.t0 * V.FPS
        seg = next((g for g in segs if g['frame'] <= f0 + 1 < g['frame'] + g['frames']), None)
        if seg and os.path.isfile(src.get(seg['clip']) or ''):
            return src[seg['clip']], float(seg.get('src_in') or 0) + (f0 - seg['frame']) / V.FPS
    return 'assets/aroll.mp4', 0.0


def short_name(name, n=21):
    if len(name) <= n:
        return name
    stem, ext = os.path.splitext(name)
    keep = n - len(ext) - 3
    return stem[:keep - keep // 3] + '...' + stem[-(keep // 3):] + ext


def main():
    s = V.Slot()
    print('words: ' + s.word_list())
    print(s.where())
    S = STYLE
    if not 1 <= len(STAMPS) <= 2:
        V.die('STAMPS holds one or two stamps')
    # ---- where things go
    ZONE_Y = ZONE_TOP
    zone_h = min(ZONE_H_MAX, s.head_top - HEAD_GAP - ZONE_TOP)
    chest = zone_h < ZONE_H_MIN            # no wall above the head: the whole thing goes on the chest, under the chin
    if chest:
        ZONE_Y = int(s.chin + max(24, (s.chin - s.head_top) * CHIN_PAD))   # the measured chin can stop short of the beard
        zone_h = min(ZONE_H_MAX, V.SAFE_BOTTOM - 6 - ZONE_Y)
        if zone_h < ZONE_H_MIN:
            V.die(f'no room for the drop zone: {s.head_top - HEAD_GAP - ZONE_TOP} px above the head and {V.SAFE_BOTTOM - 6 - ZONE_Y} px under the chin, it needs about {ZONE_H_MIN}')
    zone_x = int((1080 - ZONE_W) / 2)
    head = (s.layout or {}).get('head') or {}
    half = (head.get('width') or 380) / 2 + 12
    room_l, room_r = s.cx - half - V.SAFE_SIDE - 16, 1080 - V.SAFE_SIDE - 16 - (s.cx + half)
    side = 'left' if room_l >= room_r else 'right'
    room = max(room_l, room_r)
    if chest:
        ph = min(int(PLAYER_W_MAX * 16 / 9), V.SAFE_BOTTOM - 6 - 78 - ZONE_Y)
        pw = int(ph * 9 / 16)
        px, py = int(540 - pw / 2), ZONE_Y
        side = 'chest'
    elif room >= 260:
        pw = int(min(PLAYER_W_MAX, room))
        px = V.SAFE_SIDE + 16 + int(max(0, (room - pw) / 2)) if side == 'left' else 1080 - V.SAFE_SIDE - 16 - pw - int(max(0, (room - pw) / 2))
        py = ZONE_Y
        ph = int(pw * 16 / 9)
    else:
        ph = zone_h - 80
        pw = int(ph * 9 / 16)
        px, py = int(540 - pw / 2), ZONE_Y
        side = 'above'
    # ---- when
    t_in = T_IN if T_IN is not None else .1
    t_file = T_FILE if T_FILE is not None else t_in + .55
    t_land = t_file + .17
    t_open = T_OPEN if T_OPEN is not None else t_file + .5
    t_player = t_open + .22
    t_stamp = T_STAMP if T_STAMP is not None else t_open + .45
    t_stamp2 = t_stamp + .2
    t_out = T_OUT if T_OUT is not None else s.dur - .2
    t_gone = t_out + .14
    if t_gone > s.dur - .02 or t_stamp2 + .3 > t_out:
        V.die(f'the slot is too short at {s.dur:.2f} s: the stamps land about {t_stamp2 + .15:.2f} s and it fades at {t_out:.2f} s. About 2.3 s or more')
    # ---- the raw clip, real
    raw, at = raw_source(s)
    name = FILE_NAME or os.path.basename(raw)
    length = float(probe(raw, 'stream=duration').split(',')[0] or 0) or float(run(shutil.which('ffprobe') or 'ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', raw).stdout.strip() or 0)
    wh = probe(raw, 'stream=width,height').replace(',', 'x')
    mb = os.path.getsize(raw) / 1048576
    span = (t_gone - t_open + .3) * SPEED
    start = max(0.0, min(at, max(0.0, length - span)))
    FF = shutil.which('ffmpeg') or 'ffmpeg'
    r = run(FF, '-v', 'error', '-y', '-ss', f'{start:.3f}', '-i', raw, '-t', f'{span:.3f}', '-an', '-vf',
            f'setpts=PTS/{SPEED},fps=30,scale=672:1195:force_original_aspect_ratio=increase,crop=672:1195', '-c:v', 'libx264', '-crf', '20', '-preset', 'fast', '-pix_fmt', 'yuv420p', 'assets/raw.mp4')
    if r.returncode:
        V.die(f'could not cut the raw clip for the player: {r.stderr.strip()[-160:]}')
    run(FF, '-v', 'error', '-y', '-ss', f'{start:.3f}', '-i', raw, '-frames:v', '1', '-vf', 'scale=120:-2', '-q:v', '4', 'assets/raw_thumb.jpg')
    sub = f'{clock(length)} · {mb:.1f} MB · {wh.replace("x", "×")}'
    print(f'  file card: {short_name(name)}  |  {sub}  ({raw})')

    p = V.Page(s)
    file_x = int(540 - FILE_W / 2)
    file_h = 162
    land_y = int(ZONE_Y + zone_h / 2 - file_h / 2)
    ic = min(zone_h * .13, 56)
    p.css.append(f"""
#zone{{position:absolute;left:{zone_x}px;top:{ZONE_Y}px;width:{ZONE_W}px;height:{zone_h}px;background:{S["zone"]};border-radius:24px;box-shadow:0 12px 34px rgba(0,0,0,.3)}}
#zone>b{{position:absolute;inset:14px;border:3px dashed {S["dash"]};border-radius:14px;display:block}}
#ztx{{position:absolute;left:0;right:0;top:{zone_h / 2 - ic / 2 - 26:.0f}px;text-align:center;color:{S["dash"]}}}
#ztx svg{{display:block;margin:0 auto 10px;width:{ic:.0f}px;height:{ic:.0f}px}}
#ztx span{{font:{S["zone_weight"]} 34px/42px '{S["zone_font"]}'}}
#file{{position:absolute;left:{file_x}px;top:0;width:{FILE_W}px;height:{file_h}px;background:{S["file_bg"]};border-radius:14px;box-shadow:0 10px 26px rgba(0,0,0,.28)}}
#file img{{position:absolute;left:18px;top:18px;width:70px;height:126px;object-fit:cover;border-radius:6px;display:block}}
#fn{{position:absolute;left:108px;right:14px;top:36px;font:{S["name_weight"]} 37px/50px '{S["name_font"]}';letter-spacing:-.02em;color:{S["file_ink"]};white-space:nowrap}}
#fs{{position:absolute;left:108px;right:14px;top:92px;font:500 25px/30px '{S["mono"]}';color:{S["file_dim"]};white-space:nowrap}}
#pl{{position:absolute;left:{px}px;top:{py}px;width:{pw}px;height:{ph}px;overflow:hidden;background:#000;box-shadow:0 10px 30px rgba(0,0,0,.34);transform-origin:50% 50%}}
#plv{{position:absolute;left:0;top:0;width:100%;height:100%;object-fit:cover}}
#bdg{{position:absolute;right:12px;top:12px;padding:0 10px;height:34px;background:rgba(0,0,0,.82);border-radius:5px;color:#fff;font:500 21px/34px '{S["mono"]}'}}
#pil{{position:absolute;left:{px + pw / 2:.0f}px;top:{py + ph + 12}px;height:66px;padding:0 24px;background:{S["pill_bg"]};border-radius:8px;transform:translateX(-50%);font:{S["name_weight"]} 38px/66px '{S["name_font"]}';letter-spacing:-.02em;color:{S["pill_ink"]};white-space:nowrap}}
#pil i{{font-style:normal;color:{S["pill_num"]}}}
.st{{position:absolute;left:{px + pw / 2:.0f}px;padding:0 16px;height:{pw * .17:.0f}px;line-height:{pw * .17 - 8:.0f}px;background:{S["stamp_bg"]};border:4px solid {S["stamp_ink"]};color:{S["stamp_ink"]};font:500 {pw * .105:.0f}px/{pw * .17 - 8:.0f}px '{S["mono"]}';letter-spacing:.05em;white-space:nowrap;font-weight:700}}""")
    arrow = (f'<svg viewBox="0 0 24 24" fill="none" stroke="{S["dash"]}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
             '<path d="M12 3v12"/><path d="M7 11l5 5 5-5"/><path d="M4 16v4h16v-4"/></svg>')
    st = ''.join(f'<div class="st" id="st{k}" style="top:{py + ph * (.26 if k == 0 else .6):.0f}px">{V.esc(word)}</div>' for k, word in enumerate(STAMPS))
    p.html = [f'<div id="zone"><b></b><div id="ztx">{arrow}<span>{V.esc(DROP_TEXT)}</span></div></div>'
              f'<div id="pl"><video id="plv" src="assets/raw.mp4" muted playsinline data-start="{t_open:.4f}" data-media-start="0" data-duration="{t_gone + .05 - t_open:.4f}" data-track-index="3"></video>'
              f'<div id="bdg">&#9654;&#9654; {SPEED:g}×</div></div>'
              f'<div id="pil"><i>{clock(length)}</i> {V.esc(PILL_TEXT)}</div>{st}'
              f'<div id="file"><img src="assets/raw_thumb.jpg" alt=""><div id="fn">{V.esc(short_name(name))}</div><div id="fs">{V.esc(sub)}</div></div>']
    # the zone
    p.hidden += ['#zone', '#file', '#pl', '#pil']
    p.js.append(f"tl.fromTo('#zone',{{autoAlpha:0,scale:.965}},{{autoAlpha:1,scale:1,duration:.2,ease:'power2.out',immediateRender:false}},{V.T(t_in):.3f});")
    p.js.append(f"tl.to('#ztx',{{autoAlpha:0,duration:.1}},{V.T(t_file - .06):.3f});")
    # the file falls in
    p.js.append(f"tl.fromTo('#file',{{autoAlpha:1,y:{1920 + 40 if chest else -file_h - 40},rotation:-4}},{{autoAlpha:1,y:{land_y},rotation:-.6,duration:.16,ease:'power2.in',immediateRender:false}},{V.T(t_file):.3f});")
    p.js.append(f"tl.to('#file',{{y:{land_y - 8},duration:.06,ease:'power2.out'}},{V.T(t_land):.3f});")
    p.js.append(f"tl.to('#file',{{y:{land_y},rotation:0,duration:.1,ease:'power2.in'}},{V.T(t_land + .067):.3f});")
    p.sound('click-soft', t_land, .4)
    # it opens: card and zone go glassy, the player grows out of them
    p.js.append(f"tl.to('#file',{{autoAlpha:0,scale:.9,duration:.13,ease:'none'}},{V.T(t_open):.3f});")
    p.js.append(f"tl.to('#zone',{{autoAlpha:0,duration:.2,ease:'none'}},{V.T(t_open + .03):.3f});")
    dx = 540 - (px + pw / 2)
    dy = ZONE_Y + zone_h / 2 - (py + ph / 2)
    p.js.append(f"tl.fromTo('#pl',{{autoAlpha:1,x:{dx:.0f},y:{dy:.0f},scale:.42}},{{autoAlpha:1,x:0,y:0,scale:1,duration:.22,ease:'power3.out',immediateRender:false}},{V.T(t_open + .03):.3f});")
    p.js.append(f"tl.fromTo('#pil',{{autoAlpha:0,y:-12}},{{autoAlpha:1,y:0,duration:.14,ease:'power2.out',immediateRender:false}},{V.T(t_open + .15):.3f});")
    p.sound('whoosh-short', t_open + .1, .3)
    # the stamps slam on: big, then down in a few frames
    for k, word in enumerate(STAMPS):
        at = t_stamp if k == 0 else t_stamp2
        rot = -5 if k == 0 else 3
        p.hidden.append(f'#st{k}')
        p.js.append(f"gsap.set('#st{k}',{{xPercent:-50}});")
        p.js.append(f"tl.fromTo('#st{k}',{{autoAlpha:1,scale:2.5,rotation:{rot * .4}}},{{autoAlpha:1,scale:1,rotation:{rot},duration:.1,ease:'power3.in',immediateRender:false}},{V.T(at):.3f});")
        p.sound('impact-bass-2', at + .09, .38)
    # out
    for el in ('#pl', '#pil', '#st0', '#st1'):
        if el == '#st1' and len(STAMPS) < 2:
            continue
        p.js.append(f"tl.to('{el}',{{autoAlpha:0,duration:.14,ease:'none'}},{V.T(t_out):.3f});")
    p.write()
    if chest:
        s.hide_hint([(t_in, t_gone)])
    print(f'  zone {ZONE_W} x {zone_h} at y {ZONE_Y}, player {pw} x {ph} at x {px} ({side}). Zone {t_in:.2f}s, file falls {t_file:.2f}s, opens {t_open:.2f}s, stamps {t_stamp:.2f} and {t_stamp2:.2f}s, fades {t_out:.2f}s')
    print(f'snapshot at: {t_in + .3:.2f},{t_land + .1:.2f},{t_open + .1:.2f},{t_player + .1:.2f},{t_stamp + .05:.2f},{t_stamp2 + .3:.2f},{min(s.dur - .02, t_gone + .01):.2f}')


if __name__ == '__main__':
    main()
