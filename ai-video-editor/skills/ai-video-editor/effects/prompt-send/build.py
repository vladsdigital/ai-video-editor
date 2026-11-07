#!/usr/bin/env python3
"""PROMPT SEND (explain): a cream bar opens from a dot at the top of the frame, what the speaker tells the AI types
itself in as it is said, the send button presses and spins while the words dim, the result rolls in over them in a
serif italic with a check, and the bar collapses back into a dot and is gone.

Run from the slot folder (effect.md has the full run order):
    python3 build.py      writes index.html   (SAFE=1 safe-zone guide, SFX=0 no sounds, CAPTIONS=0 accepted:
                                               the reel's own captions keep running under it)
"""
import vgfx as V

# ==== STYLE (the reel's look wins: match this block to the reel's caption style before building) ====
STYLE = dict(
    font='Inter',                  # the typed words
    weight=500,
    result_font='Instrument Serif',   # the result, italic
    label_font='JetBrains Mono',   # the small label
    paper='#F3EFE1',               # the bar (cream paper)
    ink='#17170F',                 # typed words and result
    dimmed='#85827A',              # the words after they are sent
    label='#8F8E82',               # the small label
    dot='#C4A55C',                 # the small dot before the label after sending
    green='#1B3C2E',               # the button (deep forest green)
    mark='#FFFFFF',                # arrow, spinner, check
)
# ==== END STYLE ====

# ==== CLIP (edit this) ====
TEXT = 'Snimim se, dam AI agentu'  # what types in: the speaker's own words. Required. Up to about 60 characters
RESULT = 'dobijem video.'          # what rolls in after it, short. Required
LABELS = ('ZA AI AGENTA', 'POSLATO', 'GOTOVO')   # small label: while typing, while waiting, when done
TIMES = {}          # slot seconds, to overrule a step: open, send, result, close
TOP = None          # top of the bar, screen px. None = above the head, as high as the look has it
SOUND = 0.3         # the small ping when the result lands. 0 = silent
# ==== END CLIP ====

F = 1 / 30
ARROW = '<path d="M12 19V5.5M6 11.5 12 5.5l6 6" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
CHECK = '<path d="M5 12.5 10 17.5 19.5 7" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>'
SPIN = '<circle cx="12" cy="12" r="6.6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-dasharray="30 12"/>'


def main():
    s = V.Slot()
    print('words: ' + s.word_list())
    print(s.where())
    text, result = TEXT.strip(), RESULT.strip()
    if not text or not result:
        V.die('write TEXT and RESULT in the CLIP block: what the speaker tells the AI, and what comes back')
    if len(text) > 70:
        V.die('TEXT is too long for the bar: keep it to about 60 characters')
    S = STYLE

    # ---- when: each word of TEXT types while it is said, as far as the words can be found
    said = text.split()
    times, cur = [], 0.0
    for w in said:
        hit = next((x for x in s.words if x['start'] >= cur - .01 and V.bare(x['text']).lower() == V.bare(w).lower()), None)
        if hit:
            times.append((hit['start'], max(hit['end'], hit['start'] + .03 * len(w))))
            cur = hit['end']
        else:
            times.append(None)
    if times[0] is None:
        start = next((t[0] for t in times if t), .3)
        times[0] = (start, start + .03 * len(said[0]))
    for k in range(1, len(times)):         # a word not found goes right after the one before it
        if times[k] is None:
            a = times[k - 1][1]
            times[k] = (a, a + .05 * len(said[k]))
    t_first = times[0][0]
    t_open = float(TIMES.get('open', max(0.0, t_first - 5 * F)))
    t_done = times[-1][1]
    t_send = float(TIMES.get('send', t_done + 4 * F))
    first_r = V.bare(result.split()[0]).lower()
    wr = next((x for x in s.words if x['start'] >= t_send - .01 and V.bare(x['text']).lower() == first_r), None)
    t_res = float(TIMES.get('result', max(t_send + 7 * F, wr['start'] if wr else t_send + 22 * F)))
    t_close = float(TIMES.get('close', min(s.dur - 6 * F, max(t_res + 10 * F, s.dur - 8 * F))))
    if t_close <= t_res + 3 * F:
        V.die(f'{s.dur:.1f} s is too short: the slot has to run on at least 0.5 s after the result word is said')

    # ---- where
    bar_w, bar_h, x0 = 960, 150, 60
    top = int(TOP if TOP is not None else 272)
    if TOP is None and top + bar_h > s.head_top + 10:
        top = max(V.SAFE_TOP + 8, s.head_top + 10 - bar_h)
    if top + bar_h > s.head_top + 40:
        V.die(f'the head starts at y {s.head_top}: no room for the bar above it. It needs a wide or medium shot')
    area = bar_w - 47 * 2 - 84 - 20
    fs_t = min(46, area / (len(text) * .53))

    p = V.Page(s)
    p.css.append(f'''
#bar{{position:absolute;left:{x0}px;top:{top}px;width:{bar_w}px;height:{bar_h}px;background:{S['paper']};border-radius:34px;overflow:hidden;box-shadow:0 10px 30px rgba(0,0,0,.2)}}
#inner{{position:absolute;left:0;top:0;width:{bar_w}px;height:{bar_h}px}}
.lb{{position:absolute;left:47px;top:0;font-family:'{S['label_font']}';font-weight:500;font-size:22px;letter-spacing:.2em;color:{S['label']};white-space:pre;line-height:26px;display:flex;align-items:center;gap:12px}}
.lb i{{display:inline-block;width:7px;height:7px;border-radius:50%;background:{S['dot']}}}
#lm{{position:absolute;left:0;top:26px;width:700px;height:26px;overflow:hidden}}
#tm{{position:absolute;left:0;top:56px;width:{bar_w - 140}px;height:84px;overflow:hidden}}
#tx{{position:absolute;left:47px;top:12px;font-family:'{S['font']}';font-weight:{S['weight']};font-size:{fs_t:.1f}px;line-height:1.2;color:{S['ink']};white-space:pre;letter-spacing:-.018em}}
#tx span{{display:none}}
#cr{{display:inline-block;width:3px;height:{fs_t * 1.1:.1f}px;background:{S['ink']};vertical-align:-{fs_t * .17:.1f}px;margin-left:1px}}
#rs{{position:absolute;left:47px;top:6px;font-family:'{S['result_font']}';font-style:italic;font-weight:400;font-size:66px;line-height:1.1;color:{S['ink']};white-space:pre}}
#btn{{position:absolute;right:32px;top:{(bar_h - 84) / 2}px;width:84px;height:84px;border-radius:50%;background:{S['green']};color:{S['mark']};overflow:hidden}}
#btn svg{{position:absolute;left:18px;top:18px;width:48px;height:48px;overflow:visible}}''')
    typed = ''.join(f'<span id="c{k}">{V.esc(c)}</span>' for k, c in enumerate(text))
    p.html.append(f'''<div id="bar"><div id="inner">
<div id="lm"><div id="l0" class="lb">{V.esc(LABELS[0])}</div><div id="l1" class="lb"><i></i>{V.esc(LABELS[1])}</div><div id="l2" class="lb"><i></i>{V.esc(LABELS[2])}</div></div>
<div id="tm"><div id="tx">{typed}<b id="cr"></b></div><div id="rs">{V.esc(result)}</div></div>
<div id="btn"><svg id="ar" viewBox="0 0 24 24">{ARROW}</svg><svg id="sp" viewBox="0 0 24 24">{SPIN}</svg><svg id="ck" viewBox="0 0 24 24">{CHECK}</svg></div>
</div></div>''')

    def ft(sel, frm, to, dur, ease, at):
        p.js.append(f"tl.fromTo('{sel}',{frm},{{{to},duration:{dur:.3f},ease:'{ease}',immediateRender:false}},{V.T(at):.3f});")

    def set_(sel, vals, at):
        p.js.append(f"tl.set('{sel}',{vals},{V.T(at):.3f});")

    p.hidden += ['#bar', '#l1', '#l2', '#rs', '#sp', '#ck', '#btn']
    # opens from a dot on its left end: width grows, the corners tighten, in 6 frames; the button is uncovered as it goes
    ft('#bar', f'{{autoAlpha:0,width:{bar_h},borderRadius:{bar_h / 2}}}', f'autoAlpha:1,width:{bar_w},borderRadius:34', 6 * F, 'power3.out', t_open)
    set_('#btn', '{autoAlpha:1}', t_open + 2 * F)

    # typing word by word as said
    pos = 0
    idx = []
    for w in said:
        at = text.index(w, pos)
        idx.append(at)
        pos = at + len(w)
    for k, (w, (a, b)) in enumerate(zip(said, times)):
        end_at = idx[k + 1] if k + 1 < len(said) else len(text)
        chars = list(range(idx[k], end_at))
        for j, c in enumerate(chars):
            at = a + (b - a) * j / max(1, len(chars))
            p.js.append(f"tl.set('#c{c}',{{display:'inline'}},{V.T(at):.3f});")

    # send: the small label rolls, the button squeezes, the arrow flies up, the words dim, the spinner turns
    def roll(old, new, at):
        ft(old, '{y:0,autoAlpha:1}', 'y:-22,autoAlpha:0', 3 * F, 'power2.in', at)
        ft(new, '{y:22,autoAlpha:0}', 'y:0,autoAlpha:1', 3 * F, 'power2.out', at + F)

    ts = t_send
    set_('#cr', '{autoAlpha:0}', ts - 2 * F)
    roll('#l0', '#l1', ts - 2 * F)
    ft('#btn', '{scale:1}', 'scale:.86', 2 * F, 'power2.out', ts)
    ft('#btn', '{scale:.86}', 'scale:1', 4 * F, 'back.out(2)', ts + 2 * F)
    ft('#ar', '{y:0,autoAlpha:1}', 'y:-46,autoAlpha:1', 3 * F, 'power2.in', ts + F)
    set_('#ar', '{autoAlpha:0}', ts + 4 * F)
    p.js.append(f"tl.fromTo('#tx',{{color:'{S['ink']}'}},{{color:'{S['dimmed']}',duration:{3 * F:.3f},ease:'none',immediateRender:false}},{V.T(ts + F):.3f});")
    tr = t_res
    ft('#sp', '{autoAlpha:0,scale:.6}', 'autoAlpha:1,scale:1', 2 * F, 'power2.out', ts + 3 * F)
    p.js.append(f"tl.fromTo('#sp',{{rotation:0}},{{rotation:{(tr - ts) * 420:.0f},duration:{tr + F - ts - 3 * F:.3f},ease:'none',immediateRender:false}},{V.T(ts + 3 * F):.3f});")
    # the result: the words roll up and out, the result rolls up in, the spinner becomes a check, a small ping
    roll('#l1', '#l2', tr)
    set_('#sp', '{autoAlpha:0}', tr + F)
    ft('#ck', '{autoAlpha:0,scale:.5}', 'autoAlpha:1,scale:1', 3 * F, 'back.out(2)', tr)
    ft('#tx', '{y:0}', 'y:-74', 3 * F, 'power2.in', tr)
    set_('#tx', '{autoAlpha:0}', tr + 3 * F)
    ft('#rs', '{y:74,autoAlpha:1}', 'y:0,autoAlpha:1', 4 * F, 'power3.out', tr + F)
    if SOUND:
        p.sound('ping', tr + F, SOUND)
    # collapses into the dot on its left end, and the dot goes
    tc = t_close
    ft('#bar', f'{{width:{bar_w},borderRadius:34}}', f'width:{bar_h},borderRadius:{bar_h / 2}', 4 * F, 'power2.in', tc)
    ft('#bar', '{autoAlpha:1,scale:1}', 'autoAlpha:0,scale:.9', 2 * F, 'none', tc + 4 * F)
    p.write()
    print(f'  opens {t_open:.2f}, types {t_first:.2f} to {t_done:.2f}, send {t_send:.2f}, result {t_res:.2f}, closes {t_close:.2f}; bar top {top}, text {fs_t:.0f} px (head top {s.head_top})')
    sn = [t_open + 3 * F, (t_first + t_done) / 2, t_send + 3 * F, t_res - 3 * F, t_res + 2 * F, t_close + 2 * F]
    print('snapshot at: ' + ','.join(f'{min(x, s.dur - .05):.2f}' for x in sn))


if __name__ == '__main__':
    main()
