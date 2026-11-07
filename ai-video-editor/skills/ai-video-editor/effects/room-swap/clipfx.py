"""Machinery for the effects that show the buyer's own videos (Grid Snap, Feed Flick, Reel Rain, Live Grid, Walk Card,
Room Swap). Each effect folder ships its own copy, next to vgfx.py, so a slot needs nothing else.

  videos(...)       finds the buyer's videos in the CLIPS folder and stops with a clear message when they are missing,
                    too few or too short
  tile(...)         cuts one video to the size and length the effect shows it at (assets/tiles/, never the original)
  Comp              a full-frame page: the slot's footage, room dim, graphics behind the speaker, the cutout in front,
                    graphics in front, the effect's caption line, sounds
No footage ships with the effect: everything on screen is the slot's own clip and the buyer's own videos.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess

import vgfx as V

FF = shutil.which('ffmpeg') or 'ffmpeg'
FP = shutil.which('ffprobe') or 'ffprobe'
VIDEO_EXT = ('.mp4', '.mov', '.m4v', '.webm', '.mkv')
V.SFX_LEN.update({'whoosh': 1.0, 'click': .25, 'impact-bass-1': .9, 'impact-bass-2': .9})


def F(n):
    """a frame number as seconds"""
    return n / V.FPS


def probe(path):
    out = subprocess.run([FP, '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height:format=duration',
                          '-of', 'json', path], capture_output=True, text=True).stdout
    try:
        d = json.loads(out)
        st = d['streams'][0]
        return int(st['width']), int(st['height']), float(d['format']['duration'])
    except (ValueError, KeyError, IndexError):
        return None


def videos(folder, count, secs, skip=1.0, what='videos'):
    """-> [(path, seconds to start from)]: `count` of the buyer's videos, in file-name order, each with `secs` to show.
    Stops with one plain line the editing Claude can pass on when the folder does not hold what the effect needs."""
    if not os.path.isdir(folder):
        V.die(f'CLIPS points at "{folder}", which is not a folder. Ask the buyer for a folder of their own {what} '
              f'(at least {count}, mp4 or mov, each {secs:.1f} s or longer) and set CLIPS in the CLIP block')
    names = sorted(f for f in os.listdir(folder) if f.lower().endswith(VIDEO_EXT) and not f.startswith('.'))
    if len(names) < count:
        V.die(f'CLIPS folder "{folder}" holds {len(names)} video(s) and this effect shows {count}. Ask the buyer for '
              f'{count - len(names)} more of their own {what} (mp4 or mov, each {secs:.1f} s or longer). No stand-ins')
    out, short = [], []
    for n in names:
        path = os.path.join(folder, n)
        info = probe(path)
        if not info:
            short.append(f'{n} (cannot be read)')
            continue
        if info[2] < secs + .1:
            short.append(f'{n} ({info[2]:.1f} s)')
            continue
        out.append((path, min(skip, max(0.0, info[2] - secs - .1))))
    if len(out) < count:
        V.die(f'too few long enough {what} in "{folder}": {len(out)} usable, this effect needs {count}, each at least '
              f'{secs:.1f} s. Too short or unreadable: {", ".join(short)}. Ask the buyer for longer ones')
    return out[:count]


def tile(path, start, secs, w, h, name, focus=.5):
    """the buyer's video cut to w x h (cover crop) and to `secs` seconds, silent: assets/tiles/<name>.mp4"""
    os.makedirs('assets/tiles', exist_ok=True)
    w, h = int(w) // 2 * 2, int(h) // 2 * 2
    real = os.path.realpath(path)
    key = hashlib.sha1(f'{real}|{os.path.getmtime(real)}|{start}|{secs}|{w}x{h}|{focus}'.encode()).hexdigest()[:10]
    out = f'assets/tiles/{name}-{key}.mp4'
    if not os.path.exists(out):
        for old in os.listdir('assets/tiles'):
            if old.startswith(name + '-'):
                os.remove(os.path.join('assets/tiles', old))
        vf = (f'fps=30,scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,'
              f'crop={w}:{h}:(iw-{w})/2:(ih-{h})*{focus},setsar=1')
        r = subprocess.run([FF, '-v', 'error', '-y', '-ss', f'{start:.3f}', '-i', path, '-t', f'{secs + .1:.3f}', '-an', '-vf', vf,
                            '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-g', '15', out],
                           capture_output=True, text=True)
        if r.returncode != 0:
            V.die(f'could not cut {os.path.basename(path)}: {(r.stderr or "").strip()[-160:]}')
    return out


def caption_lines(words, a, b, chars=24):
    """the spoken words between a and b, split into short lines: [(start, end, [word, ...])]"""
    pick = [w for w in words if w['end'] > a + .02 and w['start'] < b - .02]
    lines, cur = [], []
    for w in pick:
        if cur and (sum(len(x['text']) + 1 for x in cur) + len(w['text']) > chars):
            lines.append(cur)
            cur = []
        cur.append(w)
        if re.search(r'[,.:;!?]$', w['text']) and sum(len(x['text']) + 1 for x in cur) > 8:
            lines.append(cur)
            cur = []
    if cur:
        lines.append(cur)
    out = []
    for k, ln in enumerate(lines):
        t0 = max(a, ln[0]['start'])
        t1 = min(b, lines[k + 1][0]['start'] if k + 1 < len(lines) else max(ln[-1]['end'] + .25, ln[-1]['end']))
        out.append((t0, t1, ln))
    return out


class Comp:
    """A full-frame slot page. Layers, bottom to top: backdrop, footage (#sw), dim, under, cutout, over, captions."""

    def __init__(self, slot, style, footage=True, overlay=False):
        self.s, self.st = slot, style
        self.css, self.backdrop, self.under, self.over, self.top, self.js, self.sfx = [], [], [], [], [], [], []
        self.track = 20
        self.n = 0
        self.overlay = overlay        # graphics only: transparent, the reel lays them over its own footage (SAFE=1 shows the footage)
        self.footage = footage and (not overlay or V.PREVIEW)
        self.cutout = False

    def nid(self, p='e'):
        self.n += 1
        return f'{p}{self.n}'

    def video(self, src, start=0.0, dur=None, media=0.0, cls='fill', vid=None):
        """a muted <video> tag, playing from `start` for `dur` slot seconds"""
        dur = self.s.dur - start if dur is None else min(dur, self.s.dur - start)
        self.track += 1
        vid = vid or self.nid('v')
        return (f'<video id="{vid}" class="{cls}" src="{src}" muted playsinline data-start="{start:.4f}" data-media-start="{media:.4f}" '
                f'data-duration="{dur:.4f}" data-track-index="{self.track}"></video>')

    def sound(self, name, at, vol=.35):
        if V.SFX_ON and os.path.exists(f'assets/sfx/{name}.mp3') and not any(n == name and abs(a - at) < .02 for n, a, _ in self.sfx):
            self.sfx.append((name, at, vol))

    def to(self, sel, at, dur, ease='none', **props):
        self.js.append(f"tl.to('{sel}',{json.dumps(dict(duration=dur, ease=ease, **props))},{V.T(at):.3f});")

    def set(self, sel, at, **props):
        self.js.append(f"tl.set('{sel}',{json.dumps(props)},{V.T(at):.3f});")

    def table(self, sel, at, rows):
        """frame-exact motion: rows is a list of dicts, one per frame from `at` on"""
        for k, props in enumerate(rows):
            self.set(sel, at + F(k), **props)

    def captions(self, a, b, y=None, size=None, chars=24):
        """the spoken words as a line on a plate: said words light up, the rest wait in the dim colour"""
        st = self.st
        y = y if y is not None else st.get('cap_y', 1356)
        size = size or st.get('cap_size', 66)
        self.css.append(f'''
.capl{{position:absolute;left:0;right:0;display:flex;justify-content:center;visibility:hidden;z-index:40}}
.capl>div{{font-family:'{st["cap_font"]}';font-weight:{st["cap_weight"]};font-style:{st.get("cap_style", "normal")};font-size:{size}px;line-height:1.14;letter-spacing:{st.get("cap_tracking", -.012)}em;
  color:{st["cap_wait"]};background:{st["cap_plate"]};padding:{int(size * .06)}px {int(size * .2)}px {int(size * .1)}px;border-radius:{int(size * .08)}px;white-space:nowrap}}''')
        lines = caption_lines(self.s.words, a, b, chars)
        for t0, t1, ws in lines:
            i = self.nid('cap')
            spans = []
            for k, w in enumerate(ws):
                sid = f'{i}w{k}'
                spans.append(f'<span id="{sid}">{V.esc(V.cased(w["text"], st.get("cap_case", "as-said")))}</span>')
                self.set(f'#{sid}', max(t0, w['start']), color=st['cap_ink'])
            self.top.append(f'<div id="{i}" class="capl" style="top:{int(y - size * .66)}px"><div>{" ".join(spans)}</div></div>')
            self.set(f'#{i}', t0, visibility='visible')
            if t1 < self.s.dur - .02:
                self.set(f'#{i}', t1, visibility='hidden')
        return [(t0, t1) for t0, t1, _ in lines]

    def write(self):
        s = self.s
        dur = s.dur
        audio, lanes = [], []
        for k, (name, hit, vol) in enumerate(sorted(self.sfx, key=lambda x: x[1])):
            t = max(0.0, hit - V.SFX_LEAD.get(name, 0))
            d = min(V.SFX_LEN.get(name, .5), dur - t)
            if d < .08:
                continue
            lane = next((i for i, end in enumerate(lanes) if end <= t), None)
            if lane is None:
                lanes.append(0)
                lane = len(lanes) - 1
            lanes[lane] = t + d
            audio.append(f'<audio id="sfx{k}" src="assets/sfx/{name}.mp3" data-start="{t:.3f}" data-duration="{d:.3f}" '
                         f'data-track-index="{5 + lane}" data-volume="{vol:.3f}"></audio>')
        nl = '\n  '
        foot = (f'<div id="sw" class="full"><video id="bgv" class="fill" src="assets/aroll.mp4" muted playsinline data-start="0" '
                f'data-media-start="0" data-duration="{dur:.4f}" data-track-index="0"></video></div>') if self.footage else ''
        sub = (f'<div id="subw" class="full" style="z-index:15"><video id="subj" class="fill" src="assets/subject.webm" muted playsinline data-start="0" '
               f'data-media-start="0" data-duration="{dur:.4f}" data-track-index="1"></video></div>') if self.cutout else ''
        bg = 'transparent' if self.overlay and not V.PREVIEW else '#000'
        voice = (f'<audio id="bga" src="assets/aroll.mp4" data-start="0" data-media-start="0" data-duration="{dur:.4f}" data-track-index="2" '
                 f'data-volume="1"></audio>') if self.footage else ''
        page = f'''<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<link rel="stylesheet" href="assets/fonts/fonts.css" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:{bg}}}
#root{{position:relative;width:1080px;height:1920px;overflow:hidden;background:{bg}}}
.full{{position:absolute;left:0;top:0;width:1080px;height:1920px}}
.fill{{display:block;width:100%;height:100%;object-fit:cover}}
#lay-back{{z-index:1}} #sw{{z-index:2;transform-origin:50% 50%}} #lay-under{{z-index:10}} #lay-over{{z-index:20}} #lay-top{{z-index:40}}
{''.join(self.css)}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{dur:.4f}" data-width="1080" data-height="1920">
  {voice}
  {nl.join(audio)}
  <div id="lay-back" class="full">{''.join(self.backdrop)}</div>
  {foot}
  <div id="lay-under" class="full">{''.join(self.under)}</div>
  {sub}
  <div id="lay-over" class="full">{''.join(self.over)}</div>
  <div id="lay-top" class="full">{''.join(self.top)}</div>
  {V.SAFE_GUIDE if V.SAFE else ''}
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(self.js)}
tl.set({{}},{{}},{dur:.4f});
window.__timelines["main"] = tl;
</script>
</body>
</html>
'''
        with open('index.html', 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(page)
        print(f'index.html written: {s.frames} frames ({dur:.2f}s), {len(audio)} sound(s)' + (', SAFE guide ON (snapshots only)' if V.SAFE else ''))
