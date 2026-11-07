#!/usr/bin/env python3
"""LENS READOUT: the picture starts punched in, a lens-distance strip snaps open above the head, its scale spins from
tight numbers to wide ones while the picture pulls out to full, the strip goes, and the next words build letter by
letter above the head: a heavy line over a thin running rule, a serif italic line under it.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html   (SAFE=1 safe-zone guide, SFX=0 no sounds, CAPTIONS=0 = no words, strip and pull only)
"""
import json
import os
import shutil
import subprocess

from PIL import ImageFont

import vgfx as V

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    font='Inter Tight',            # the heavy line
    weight=800,
    tracking=-0.03,
    serif_font='Instrument Serif', # the italic line
    serif_weight=400,
    serif_italic=True,
    num_font='JetBrains Mono',     # the strip's numbers
    num_weight=500,
    ink='#F6F1E5',                 # cream
    accent='#CDB062',              # old gold: the number at the pointer, the italic line
    card='#163127',                # the strip (deep forest green)
    band='#2C5243',                # the strip's top band
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
HEAVY = ''          # the heavy line, words the speaker says after the pull. '' = strip and pull only
ITALIC = ''         # the italic line under it, as said. '' = none
NUMBERS = [85, 70, 50, 35, 24]   # the scale, tight to wide (generic lens distances)
PUNCH = 1.40        # how far the picture is punched in before the pull (1.40 = 140 %)
T_STRIP = None      # strip opens (slot seconds). None = when the first word of the slot is said
T_PULL = None       # the scale spins and the picture pulls out. None = 0.2 s after the strip is fully open
T_STRIP_OUT = None  # strip goes. None = 0.6 s after the pull
T_HEAVY = None      # first letter of HEAVY. None = when its first word is said
T_ITALIC = None     # first letter of ITALIC. None = when its first word is said
T_OUT = None        # the words have gone. None = 0.45 s after the last word ends, at most the slot end
STAGGER = 1.5       # frames between two letters
SOUND = 0.0         # volume of a soft tick on the spin. 0 = silent, as the look is meant to be
# ==== END CLIP ====

FR = 1 / V.FPS
STRIP_W, STRIP_H, STOP = 762, 180, 180      # strip size and the px between two numbers on the scale


def font(family, weight, italic=False):
    name = family.replace(' ', '') + f"-{weight}-{'italic' if italic else 'normal'}.woff2"
    path = os.path.join('assets', 'fonts', name)
    if not os.path.isfile(path):
        V.die(f'{name} is not in assets/fonts: use a face from assets/fonts/fonts.css in the STYLE block')
    f = ImageFont.truetype(path, 1000)
    try:                                              # a variable font opens at its default weight: set the real one
        f.set_variation_by_axes([min(a['maximum'], max(a['minimum'], weight)) if a.get('name') in (b'Weight', 'Weight') else a['default']
                                 for a in f.get_variation_axes()])
    except OSError:
        pass
    return f


def starts_on_cut(s):
    proj = s.clip.get('project')
    if not proj:
        return False
    segs = V._json(os.path.join(proj, 'segments.json'), []) or []
    return any(abs(g['frame'] - int(s.clip.get('frame') or 0)) <= 1 for g in segs)


def letters(p, text, f, size, x0, base, cls, fill, family, weight, style, tracking):
    """one absolutely placed letter per wrapper, so each can pop on its own; returns the selectors"""
    out = []
    for k, c in enumerate(text):
        if c == ' ':
            continue
        x = x0 + f.getlength(text[:k]) * size / 1000 + tracking * size * k
        cx = x + f.getlength(c) * size / 2000
        sel = f'{cls}{k}'
        p.html.append(f'<div id="{sel}" class="lt" style="transform-origin:{cx:.1f}px {base:.1f}px"><svg width="1080" height="1920" viewBox="0 0 1080 1920" style="position:absolute;left:0;top:0;overflow:visible">'
                      f'<text x="{x:.1f}" y="{base:.1f}" font-family="{family}" font-weight="{weight}" font-style="{style}" font-size="{size:.1f}" fill="{fill}">{V.esc(c)}</text></svg></div>')
        out.append('#' + sel)
    return out


def pop(p, sel, at, size):
    p.hidden.append(sel)
    p.js.append(f"gsap.set('{sel}',{{scale:.5,y:0}});")
    p.js.append(f"tl.set('{sel}',{{autoAlpha:.28}},{V.T(at):.3f});")
    kf = [dict(scale=1.03, y=round(-.2 * size, 1), autoAlpha=.78), dict(scale=1, y=round(-.07 * size, 1), autoAlpha=1), dict(y=0)]
    kf = [dict(v, duration=round(FR, 4), ease='none') for v in kf]
    p.js.append(f"tl.to('{sel}',{{keyframes:{json.dumps(kf)}}},{V.T(at):.3f});")


def lowest_chin(s):
    """The layout's head box can stop above the real chin, and a speaker leans. When the reel has a cutout, the lowest
    neck over this slot's frames (the narrowest row under the head) moves s.chin down. No cutout: the layout stands."""
    sub = os.path.join(s.clip.get('project') or '', 'assets', 'subject.webm')
    if not os.path.isfile(sub):
        return
    try:
        import numpy as np
        w, h = 270, 480
        raw = subprocess.run([shutil.which('ffmpeg') or 'ffmpeg', '-v', 'error', '-c:v', 'libvpx-vp9', '-ss', f'{s.t0:.3f}', '-t', f'{s.dur:.3f}', '-i', sub,
                              '-vf', f"select='not(mod(n\\,{max(1, s.frames // 14)}))',alphaextract,scale={w}:{h}", '-fps_mode', 'passthrough',
                              '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True).stdout
        a = np.frombuffer(raw, dtype=np.uint8)
        n = len(a) // (w * h)
        necks = []
        for fr in a[:n * w * h].reshape(n, h, w):
            rows = (fr > 128).sum(1)
            lit = np.where(rows >= 6)[0]
            if not len(lit):
                continue
            t = lit[0]
            hw = rows[t:t + 45].max()                 # the head's width, from its top part
            lo, hi = t + int(.5 * hw), min(h - 1, t + int(1.9 * hw))
            below = np.where(rows[lo:hi] > 1.7 * hw)[0]   # stop where the shoulders start
            hi = lo + below[0] if len(below) else hi
            if hi > lo:
                necks.append((lo + int(np.argmin(rows[lo:hi]))) * 4 + 40)      # 40 px: the jaw sits over the narrowest row
        if necks and max(necks) > s.chin:
            print(f'placement: chin moved from y {s.chin} to y {max(necks)} (the lowest neck in this slot, from the cutout)')
            s.chin = max(necks)
    except (OSError, ValueError, ImportError):
        pass


def main():
    s = V.Slot()
    s.dur = int(s.frames / V.FPS * 1000) / 1000      # rounded down: a duration rounded up renders one frame too many
    lowest_chin(s)
    V.PREVIEW = True                                 # the picture itself moves: the render holds the footage
    print('words: ' + s.word_list())
    print(s.where())
    S = STYLE
    if len(NUMBERS) < 3:
        V.die('NUMBERS needs at least 3 values')
    if not s.words and T_STRIP is None:
        V.die('no words in this slot: set T_STRIP')
    t_strip = T_STRIP if T_STRIP is not None else max(0.0, s.words[0]['start'] - 2 * FR)
    t_pull = T_PULL if T_PULL is not None else t_strip + 3 * FR + .2
    t_gone = T_STRIP_OUT if T_STRIP_OUT is not None else t_pull + .6
    if t_pull + 6 * FR > s.dur:
        V.die('the slot ends before the pull is over: make the slot longer')

    # ---- where
    top = V.SAFE_TOP + 8
    room = s.head_top - 18 - top
    # no room above the head: the strip sits under the punched-in chin, the words on the chest under the real chin
    chest_top = s.chin + 24
    on_chest = room < 130
    if on_chest:
        low = s.head_top + (chest_top - s.head_top) * PUNCH + 10
        if low + STRIP_H > V.SAFE_BOTTOM - 6:
            V.die(f'no room for the strip above the head (top at y {s.head_top}) or under the punched-in chin (y {low:.0f})')
        k_strip, strip_y = 1.0, low
        top, room = chest_top, V.SAFE_BOTTOM - 6 - chest_top
        print(f'placement: no room above the head (top at y {s.head_top}), so the strip sits at y {low:.0f} and the words from y {top:.0f}')
    else:
        k_strip = min(1.0, room / (STRIP_H + 20))
        strip_y = top + (room - STRIP_H * k_strip) / 2    # in the middle of the room above the head
    strip_h, strip_w = STRIP_H * k_strip, min(STRIP_W, 1080 - 2 * V.SAFE_SIDE - 20)
    strip_x = (1080 - strip_w) / 2
    stop = STOP * k_strip
    origin_x, origin_y = min(max(s.cx, 300), 780), s.head_top

    p = V.Page(s)
    k_n = k_strip
    band_h, tick_y, num_y = 34 * k_n, 62 * k_n, 92 * k_n
    p.css.append(f"""
#bgv{{transform-origin:{origin_x}px {origin_y}px}}
#st{{position:absolute;left:{strip_x:.1f}px;top:{strip_y:.1f}px;width:{strip_w:.1f}px;height:{strip_h:.1f}px;background:{S['card']};border-radius:{22 * k_n:.0f}px;overflow:hidden;box-shadow:0 6px 18px rgba(0,0,0,.28)}}
#st .band{{position:absolute;left:{18 * k_n:.1f}px;right:{18 * k_n:.1f}px;top:{14 * k_n:.1f}px;height:{band_h:.1f}px;
  background:repeating-linear-gradient(90deg,{S['band']} 0 3px,{S['card']} 3px 8px)}}
#st .tag{{position:absolute;right:{20 * k_n:.1f}px;top:{14 * k_n:.1f}px;height:{band_h:.1f}px;padding:0 {6 * k_n:.1f}px;background:{S['card']};color:{S['ink']};font:{S['num_weight']} {18 * k_n:.1f}px '{S['num_font']}';line-height:{band_h:.1f}px}}
#st .ptr{{position:absolute;left:50%;top:{band_h + 18 * k_n:.1f}px;margin-left:{-8 * k_n:.1f}px;width:0;height:0;border-left:{8 * k_n:.1f}px solid transparent;border-right:{8 * k_n:.1f}px solid transparent;border-top:{10 * k_n:.1f}px solid {S['accent']}}}
#tp{{position:absolute;left:0;top:0;height:100%}}
.nm{{position:absolute;top:{band_h + num_y - 24 * k_n:.1f}px;transform-origin:50% 50%;font-family:'{S['num_font']}';font-weight:{S['num_weight']};font-size:{46 * k_n:.1f}px;color:{S['ink']};line-height:1;width:120px;margin-left:-60px;text-align:center}}
.tk{{position:absolute;width:{2.4 * k_n:.1f}px;background:{S['ink']};opacity:.82}}
.lt{{position:absolute;inset:0}}
.rl{{position:absolute;height:3px;transform-origin:0 50%}}
""")
    if on_chest:                                     # words over a shirt need the dark behind them
        p.css.append(".lt svg{filter:drop-shadow(0 2px 3px rgba(0,0,0,.75)) drop-shadow(0 0 22px rgba(0,0,0,.7))}")
    n = len(NUMBERS)
    # the scale runs past both ends so the strip is never empty
    ticks = []
    lo, hi = -int(strip_w / 2 / stop) - 2, n + int(strip_w / 2 / stop) + 1
    for j in range(lo * 5, hi * 5):
        tall = j % 5 == 0
        h = (20 if tall else 10) * k_n
        ticks.append(f'<div class="tk" style="left:{j * stop / 5:.1f}px;top:{band_h + tick_y - h / 2:.1f}px;height:{h:.1f}px"></div>')
    nums = ''.join(f'<div id="n{i}" class="nm" style="left:{i * stop:.1f}px">{v}</div>' for i, v in enumerate(NUMBERS))
    p.html.append(f'<div id="st"><div class="band"></div><div class="tag">mm</div><div class="ptr"></div><div id="tp">{"".join(ticks)}{nums}</div></div>')
    cx = strip_w / 2
    p.js.append(f"gsap.set('#tp',{{x:{cx:.1f}}});")
    state = lambda at_stop: [(i, abs(i - at_stop)) for i in range(n)]

    def number_look(at_stop, when=None):
        for i, d in state(at_stop):
            px = abs(i - at_stop) * stop
            sc = 1.0 if px < strip_w * .3 else max(.55, 1 - (px - strip_w * .3) / (strip_w * .2) * .45)
            col = S['accent'] if d < .5 else S['ink']
            vals = f"{{scale:{sc:.3f},color:'{col}'}}"
            p.js.append(f"gsap.set('#n{i}',{vals});" if when is None else f"tl.set('#n{i}',{vals},{V.T(when):.3f});")

    number_look(0)
    # the strip snaps open
    p.hidden.append('#st')
    p.js.append("gsap.set('#st',{scale:.82,y:18});")
    p.js.append(f"tl.set('#st',{{autoAlpha:.42}},{V.T(t_strip):.3f});")
    kf = [dict(scale=.95, y=4, autoAlpha=.9), dict(scale=1.01, y=-2, autoAlpha=1), dict(scale=1, y=0)]
    p.js.append(f"tl.to('#st',{{keyframes:{json.dumps([dict(v, duration=round(FR, 4), ease='none') for v in kf])}}},{V.T(t_strip):.3f});")
    # the spin and the pull, frame by frame
    frac = [.42, .72, .9, .98, 1]
    travel = n - 1
    kf = [dict(x=round(cx - f * travel * stop, 1), duration=round(FR, 4), ease='none') for f in frac]
    p.js.append(f"tl.to('#tp',{{keyframes:{json.dumps(kf)}}},{V.T(t_pull):.3f});")
    for j, f in enumerate(frac):
        number_look(f * travel, t_pull + (j + 1) * FR)
    # the picture: punched in, an ease into the punch when the slot does not start on a cut
    if starts_on_cut(s):
        p.js.append(f"gsap.set('#bgv',{{scale:{PUNCH}}});")
    else:
        p.js.append(f"tl.fromTo('#bgv',{{scale:1}},{{scale:{PUNCH},duration:{8 * FR:.4f},ease:'power2.inOut',immediateRender:false}},0);")
    if t_pull < 8 * FR:
        V.die('the pull comes too early: leave at least 0.3 s before T_PULL')
    kf = [dict(scale=round(1 + (PUNCH - 1) * (1 - f), 4), duration=round(FR, 4), ease='none') for f in [.46, .76, .92, .98, 1]]
    p.js.append(f"tl.to('#bgv',{{keyframes:{json.dumps(kf)}}},{V.T(t_pull):.3f});")
    if SOUND:
        p.sound('whoosh-short', t_pull, SOUND)
    # the strip goes
    kf = [dict(scale=.97, autoAlpha=.55), dict(scale=.93, autoAlpha=.15), dict(autoAlpha=0)]
    p.js.append(f"tl.to('#st',{{keyframes:{json.dumps([dict(v, duration=round(FR, 4), ease='none') for v in kf])}}},{V.T(t_gone):.3f});")
    print(f'  strip y {strip_y:.0f}..{strip_y + strip_h:.0f} opens {t_strip:.2f}s; spin and pull {t_pull:.2f}s to {t_pull + 5 * FR:.2f}s, punch {PUNCH}; strip gone {t_gone + 3 * FR:.2f}s; head top {s.head_top}')

    # ---- the words
    hide = None
    heavy = HEAVY.strip() if V.env('CAPTIONS') != '0' else ''
    ital = ITALIC.strip() if V.env('CAPTIONS') != '0' else ''
    if heavy:
        def say(text, after):
            w = s.find('^' + V.re.escape(V.bare(text.split()[0])) + '$', after)
            if not w:
                V.die(f'"{text.split()[0]}" is not said in this slot after {after:.2f}s: check the words or set the time by hand')
            return w
        fh = font(S['font'], S['weight'])
        fi = font(S['serif_font'], S['serif_weight'], S['serif_italic'])
        fh_w = lambda t, z: fh.getlength(t) * z / 1000 + S['tracking'] * z * (len(t) - 1)
        room_w = 1080 - 2 * V.SAFE_SIDE - 40
        fs = min(190.0, .9 * 1080 / (fh_w(heavy, 1)) if fh_w(heavy, 1) else 190.0)
        fs2 = (min(190.0, room_w * 1000 / fi.getlength(ital)) if ital else 0)
        tail = .22 if any(c in 'gjpqy' for c in heavy) else .12   # the rule clears the tails of g, j, p, q, y
        h_need = lambda a, b: a * .76 + a * tail + 22 + (b * .92 if b else 0)
        k = min(1.0, room / h_need(fs, fs2))
        fs, fs2 = fs * k, fs2 * k
        base1 = top + fs * .76
        drop = fs * tail
        x1 = (1080 - fh_w(heavy, fs)) / 2
        rule_y = base1 + drop
        p.css.append(f".rl.a{{left:{x1:.1f}px;width:{fh_w(heavy, fs):.1f}px;top:{rule_y:.1f}px;background:{S['ink']};opacity:.42;height:2px}}"
                     f".rl.d{{left:{x1:.1f}px;width:{fh_w(heavy, fs):.1f}px;top:{rule_y - 2:.1f}px;height:6px;background:repeating-linear-gradient(90deg,{S['ink']} 0 5px,transparent 5px 12px)}}"
                     f"#tick{{position:absolute;left:{x1:.1f}px;top:{rule_y - 12:.1f}px;width:3px;height:26px;background:{S['ink']}}}")
        sel1 = letters(p, heavy, fh, fs, x1, base1, 'h', S['ink'], S['font'], S['weight'], 'normal', S['tracking'])
        p.html.append('<div class="rl a"></div><div class="rl d"></div><div id="tick"></div>')
        w0 = say(heavy, t_pull)
        t_h = T_HEAVY if T_HEAVY is not None else w0['start']
        step = STAGGER * FR
        for j, sel in enumerate(sel1):
            pop(p, sel, t_h + j * step, fs)
        t_h_done = t_h + (len(sel1) - 1) * step + 3 * FR
        p.hidden += ['.rl.a', '.rl.d', '#tick']
        rw = fh_w(heavy, fs)
        p.js.append(f"tl.fromTo('.rl.a',{{autoAlpha:1,scaleX:0}},{{autoAlpha:1,scaleX:1,duration:{3 * FR:.4f},ease:'none',immediateRender:false}},{V.T(t_h):.3f});")
        p.js.append(f"tl.fromTo('.rl.d',{{autoAlpha:1,clipPath:'inset(0% 100% 0% 0%)'}},{{autoAlpha:1,clipPath:'inset(0% 0% 0% 0%)',duration:{t_h_done - t_h:.3f},ease:'none',immediateRender:false}},{V.T(t_h):.3f});")
        p.js.append(f"tl.fromTo('#tick',{{autoAlpha:1,x:0}},{{autoAlpha:1,x:{rw:.1f},duration:{t_h_done - t_h:.3f},ease:'none',immediateRender:false}},{V.T(t_h):.3f});")
        p.js.append(f"tl.set('#tick',{{autoAlpha:0}},{V.T(t_h_done + 2 * FR):.3f});")
        sel2, t_i = [], None
        if ital:
            base2 = rule_y + 22 + fs2 * .68
            x2 = (1080 - fi.getlength(ital) * fs2 / 1000) / 2
            sel2 = letters(p, ital, fi, fs2, x2, base2, 'i', S['accent'], S['serif_font'], S['serif_weight'], 'italic' if S['serif_italic'] else 'normal', 0)
            w1 = say(ital, w0['start'] + .01)
            t_i = T_ITALIC if T_ITALIC is not None else w1['start']
            for j, sel in enumerate(sel2):
                pop(p, sel, t_i + j * step, fs2)
            print(f'  italic "{ital}" size {fs2:.0f} from {t_i:.2f}s, line at y {base2:.0f}')
        last = V.bare((ital or heavy).split()[-1])
        wl = s.find('^' + V.re.escape(last) + '$', t_i if t_i is not None else t_h)
        t_end = wl['end'] if wl else (t_i or t_h) + 1
        t_out = min(s.dur, T_OUT if T_OUT is not None else t_end + .45)
        # out: letters go left to right
        m = max(len(sel1), len(sel2))
        out_step = min(.75, 6 / m)                    # a long line leaves as fast as a short one
        t0 = t_out - (m * out_step + 3) * FR
        for row in (sel1, sel2):
            for j, sel in enumerate(row):
                at = t0 + j * out_step * FR
                p.js.append(f"tl.to('{sel}',{{autoAlpha:0,y:{-.05 * fs:.1f},duration:{3 * FR:.4f},ease:'none'}},{V.T(at):.3f});")
        p.js.append(f"tl.to(['.rl.a','.rl.d'],{{autoAlpha:0,duration:{3 * FR:.4f},ease:'none'}},{V.T(t0 + m * .5 * FR):.3f});")
        print(f'  heavy "{heavy}" size {fs:.0f} from {t_h:.2f}s, line at y {base1:.0f}; words gone {t_out:.2f}s')
        hide = (t_h, t_out)
        if t_h < t_gone + 3 * FR:
            print('  note: the words start before the strip has gone: move T_STRIP_OUT or T_HEAVY')
    p.write()
    print(f'snapshot at: {t_strip + .1:.2f},{t_pull + .04:.2f},{t_pull + .25:.2f}' + (f',{hide[0] + .15:.2f},{hide[1] - .3:.2f}' if hide else ''))
    if hide:
        s.hide_hint([hide])


if __name__ == '__main__':
    main()
