#!/usr/bin/env python3
"""The clean person cutout (RobustVideoMatting, resnet50, onnxruntime; CoreML on a Mac with Apple Silicon):
<project>/assets/aroll.mp4 -> assets/subject.webm (VP9 + alpha, 1080x1920, frame-for-frame with aroll).

Usage:  PY rvm_cut.py <project_dir> [--src assets/x.mp4] [--out assets/y.webm] [--hard] [--workers N]

Use THIS cutout, not the quick one (cutout.py), whenever something sits behind the speaker or the speaker pops out
of a card: Bold captions, Chalk Talk, Show and Tell, and the effects that say "clean cutout" in effects/INDEX.md.
The quick cutout is fine for measuring (layout.py) but it can take a face in a painting or poster for the speaker
and it is rough around hands.
Speed: on an Apple Silicon Mac the model runs on CoreML and the frames are split over two workers, about 0.1 to
0.15 s per frame (a 60 second reel is about 3 to 5 minutes). On the CPU only (Windows, Linux, Intel Mac) it is about
0.5 s per frame or more. The first line it prints says which and how long. Run it in the background and keep working.

First use needs the model and scipy, one time:   <any python> scripts/setup.py --matting   (about 105 MB download)

--hard   push soft, half-transparent edges solid (for a speaker placed on a new backdrop, as Chalk Talk does)
--no-head-clean   skip the head check. By default, head_clean.py takes a picture behind the head (a face or skull
         the cutout kept as a grey ghost above the speaker) off the finished cutout; a clean cutout is not touched.
         Its "head check:" line says what it did (references/checks.md says what to tell the buyer).
--workers N   how many parts are matted at the same time (default: 2 with CoreML on a long clip, else 1).
         RVM_PROVIDER=cpu in the environment forces the CPU.
The recurrent state is warmed on the first frame of each part and reset at every cut in <project>/segments.json (in
an effect slot: at the "cut_frames" of its clip.json). fx_new.py runs this on a slot's own frames when the reel has
no cutout, and waits for the reel's cutout when one is being made (the file <out>.running exists while it works).
The cutout only appears under its real name when it is complete, so a half-made file is never picked up.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skillenv  # noqa: E402

skillenv.utf8_stdio()
if len(sys.argv) < 2:
    sys.exit(__doc__)
MODEL = os.path.join(skillenv.models_dir(), 'rvm_resnet50_fp32.onnx')
try:
    import numpy as np
    import onnxruntime as ort
    from scipy import ndimage
except ImportError as e:
    sys.exit(f'The clean cutout is not set up yet ({e.name} is missing). Run: setup.py --matting')
if not os.path.isfile(MODEL):
    sys.exit(f'The matting model is not downloaded yet ({MODEL}). Run: setup.py --matting')
ort.set_default_logger_severity(3)        # CoreML prints a partition warning on every load: not useful to the buyer


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


FF = skillenv.tool('ffmpeg')
W, H = 1080, 1920
SELF = os.path.abspath(__file__)
os.chdir(skillenv.path_arg(sys.argv[1]))
src = arg('--src', 'assets/aroll.mp4')
out = arg('--out', 'assets/subject.webm')
hard = '--hard' in sys.argv
part = arg('--range')                      # internal: a worker mats frames [a, b) of src into --out
cuts = set()
if os.path.exists('segments.json') and '--src' not in sys.argv:
    with open('segments.json', encoding='utf-8') as fh:
        cuts = {s['frame'] for s in json.load(fh)}
elif os.path.exists('clip.json') and '--src' not in sys.argv:      # an effect slot: its own cuts, if it spans two shots
    with open('clip.json', encoding='utf-8') as fh:
        cuts = set(json.load(fh).get('cut_frames') or [])
WARM = 12
COREML = os.environ.get('RVM_PROVIDER', '').lower() != 'cpu' and \
    'CoreMLExecutionProvider' in ort.get_available_providers()


def session(threads):
    so = ort.SessionOptions()
    so.intra_op_num_threads = threads
    if COREML:
        try:
            return ort.InferenceSession(MODEL, so, providers=['CoreMLExecutionProvider', 'CPUExecutionProvider']), 'CoreML'
        except Exception:                  # an old macOS or a CoreML hiccup: the CPU always works
            pass
    return ort.InferenceSession(MODEL, so, providers=['CPUExecutionProvider']), 'CPU'


def encoder(path):
    return subprocess.Popen([FF, '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}',
                             '-r', '30', '-i', '-', '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-b:v', '0', '-crf',
                             '20', '-g', '30', '-auto-alt-ref', '0', '-row-mt', '1', '-cpu-used', '4',
                             '-metadata:s:v:0', 'alpha_mode=1', '-f', 'webm', path], stdin=subprocess.PIPE)


def matte(a0, a1, path, threads, report):
    """Mat frames [a0, a1) of src (a1 None = to the end) into path. Returns the number of frames written."""
    sess, _ = session(threads)
    vf = f'scale={W}:{H}'
    if a0 or a1 is not None:
        vf = f"select='between(n\\,{a0}\\,{(a1 or 10 ** 9) - 1})'," + vf
    dec = subprocess.Popen([FF, '-loglevel', 'error', '-i', src, '-vf', vf, '-fps_mode', 'passthrough', '-f',
                            'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = encoder(path)
    ds = np.array([.375], np.float32)
    size = W * H * 3
    rec = None
    n = 0

    def run(rgb, rec):
        x = rgb.astype(np.float32).transpose(2, 0, 1)[None] / 255.
        fgr, pha, *rec = sess.run(None, {'src': x, 'r1i': rec[0], 'r2i': rec[1], 'r3i': rec[2], 'r4i': rec[3],
                                         'downsample_ratio': ds})
        return fgr, pha, rec

    while True:
        buf = dec.stdout.read(size)
        if len(buf) < size:
            break
        rgb = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        if rec is None or a0 + n in cuts:         # warm the recurrent state on the first frame of each shot
            rec = [np.zeros((1, 1, 1, 1), np.float32)] * 4
            for _ in range(WARM):
                _, _, rec = run(rgb, rec)
        fgr, pha, rec = run(rgb, rec)
        a = np.clip(pha[0, 0], 0, 1)
        small = a[::2, ::2] > .1                      # drop small floating islands
        lab, cnt = ndimage.label(small)
        if cnt > 1:
            areas = np.bincount(lab.ravel())[1:]
            drop = [i + 1 for i, ar in enumerate(areas) if ar < areas.max() * .015]
            if drop:
                m = ndimage.binary_dilation(np.isin(lab, drop), iterations=2)
                a = a.copy()
                a[np.repeat(np.repeat(m, 2, axis=0), 2, axis=1)[:H, :W]] = 0
        if hard:                                      # smoothstep: soft edges go solid, faint haze goes away
            s = np.clip((a - .25) / .5, 0, 1)
            a = s * s * (3 - 2 * s)
        f = np.clip(fgr[0].transpose(1, 2, 0), 0, 1)  # decontaminated foreground colour for edge pixels
        edge = (a > .02) & (a < .98)
        col = rgb.copy()
        col[edge] = (f[edge] * 255).astype(np.uint8)
        enc.stdin.write(np.dstack([col, (a * 255).astype(np.uint8)]).tobytes())
        n += 1
        report(n)
    enc.stdin.close()
    enc.wait()
    dec.wait()
    if enc.returncode:
        sys.exit(f'the cutout encoder failed (ffmpeg exit {enc.returncode})')
    return n


def count_frames(path, decode=False):
    """Packets (fast, to plan the split) or decoded frames (exact, for the final frame-for-frame check)."""
    what = 'frames' if decode else 'packets'
    r = subprocess.run([skillenv.tool('ffprobe'), '-v', 'error', f'-count_{what}', '-select_streams', 'v:0',
                        '-show_entries', f'stream=nb_read_{what}', '-of', 'csv=p=0', path], **skillenv.TEXT)
    try:
        return int(r.stdout.strip().split(',')[0])
    except ValueError:
        return 0


cpus = os.cpu_count() or 4
if part:                                   # ---- a worker: mat its frames, print progress lines for the parent
    a0, a1 = (int(x) for x in part.split(':'))
    last = [0.0]

    def tell(n):
        if time.time() - last[0] >= 5:
            last[0] = time.time()
            print(f'progress {n}', flush=True)

    k = matte(a0, a1, out, int(arg('--threads', '4')), tell)
    print(f'progress {k}', flush=True)
    print(f'frames {k}', flush=True)
    sys.exit(0)

total = count_frames(src)
exact = {}
counter = threading.Thread(target=lambda: exact.update(n=count_frames(src, decode=True)), daemon=True)
counter.start()                            # the exact count decodes the whole clip: done while the matting runs
workers = int(arg('--workers', os.environ.get('RVM_WORKERS', '0')) or 0) or (2 if COREML and total >= 240 else 1)
workers = max(1, min(workers, 4, max(1, total // 60)))
per_frame = (0.14 if COREML else 0.5) / (1.5 if workers > 1 else 1)
print(f'cutout: {total} frames on {"CoreML" if COREML else "the CPU"}, {workers} worker{"s" if workers > 1 else ""}, '
      f'about {max(1, round(total * per_frame / 60))} min', flush=True)

# The head check (head_clean.py) finds the face and hands while the matting runs, then takes off a picture behind the
# head if the cutout kept one. --no-head-clean skips it.
HEAD_CLEAN = os.path.join(os.path.dirname(SELF), 'head_clean.py')
head_prep = None
if '--no-head-clean' not in sys.argv:
    try:
        head_prep = subprocess.Popen([sys.executable, HEAD_CLEAN, '.', '--prepare', '--src', src],
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8', errors='replace')
    except OSError:
        head_prep = None

running = out + '.running'
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
with open(running, 'w', encoding='utf-8') as fh:
    json.dump({'pid': os.getpid(), 'frames': total, 'started': time.time()}, fh)
tmpdir = tempfile.mkdtemp(prefix='.cutout-', dir=os.path.dirname(os.path.abspath(out)))
t0 = time.time()
done = [0] * workers
t_print = [time.time()]


def progress():
    if time.time() - t_print[0] < 30:
        return
    t_print[0] = time.time()
    n = sum(done)
    left = (time.time() - t0) / max(n, 1) * (total - n)
    print(f'cutout {n}/{total} frames, about {max(1, round(left / 60))} min left', flush=True)
    try:
        with open(running, 'w', encoding='utf-8') as fh:
            json.dump({'pid': os.getpid(), 'frames': total, 'done': n, 'started': t0}, fh)
    except OSError:
        pass


try:
    whole = os.path.join(tmpdir, 'whole.webm')
    if workers == 1:
        def one(n):
            done[0] = n
            progress()
        n = matte(0, None, whole, max(2, cpus - 2), one)
    else:
        # split points: the cut nearest each even share (a part starts on a fresh shot), else the even share itself
        bounds = [0]
        for i in range(1, workers):
            even = total * i // workers
            near = [c for c in cuts if abs(c - even) <= total * .15 / workers and c > bounds[-1] + 30]
            bounds.append(min(near, key=lambda c: abs(c - even)) if near else even)
        bounds.append(total)
        threads = str(max(2, (cpus - 2) // workers))
        procs, parts = [], []
        for i in range(workers):
            pth = os.path.join(tmpdir, f'part{i}.webm')
            parts.append(pth)
            argv = [sys.executable, SELF, '.', '--range', f'{bounds[i]}:{bounds[i + 1]}', '--out', pth,
                    '--threads', threads] + (['--src', src] if '--src' in sys.argv else []) + (['--hard'] if hard else [])
            procs.append(subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8',
                                          errors='replace'))
        logs = [[] for _ in procs]

        def follow(i):
            for ln in procs[i].stdout:
                if ln.startswith('progress '):
                    done[i] = int(ln.split()[1])
                else:
                    logs[i].append(ln)

        readers = [threading.Thread(target=follow, args=(i,), daemon=True) for i in range(workers)]
        for t in readers:
            t.start()
        while any(p.poll() is None for p in procs):
            time.sleep(1)
            progress()
        for t in readers:
            t.join()
        for i, p in enumerate(procs):
            if p.returncode:
                sys.exit(f'cutout worker {i + 1} failed:\n' + ''.join(logs[i])[-1500:])
        with open(os.path.join(tmpdir, 'parts.txt'), 'w', encoding='utf-8') as fh:
            fh.write(''.join(f"file '{os.path.basename(q)}'\n" for q in parts))
        r = subprocess.run([FF, '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '0', '-i',
                            os.path.join(tmpdir, 'parts.txt'), '-c', 'copy', whole], **skillenv.TEXT)
        if r.returncode:
            sys.exit('joining the cutout parts failed: ' + (r.stderr or '')[-800:])
        n = count_frames(whole)
    print(f'done {out}: {n} frames, {(time.time() - t0) / max(n, 1):.2f}s/frame, '
          f'{(time.time() - t0) / 60:.1f} min', flush=True)
    counter.join()
    total = exact.get('n') or total
    if total and total != n:
        sys.exit(f'FRAME MISMATCH: {src} has {total} frames, the cutout has {n}. Re-run assemble.py, then this script.')
    os.replace(whole, out)
    if head_prep is not None:
        prep_out = head_prep.communicate()[0] or ''
        if 'building the face finder' in prep_out:
            print('head check: built the face finder (one time)', flush=True)
        r = subprocess.run([sys.executable, HEAD_CLEAN, '.', '--src', src, '--cut', out], **skillenv.TEXT)
        lines = [ln for ln in (r.stdout or '').splitlines() if ln.startswith('head check:')]
        if lines:
            print('\n'.join(lines), flush=True)
        if r.returncode != 0 or not lines:
            print('head check: did not finish, the cutout is as matted. ' + (r.stderr or '').strip()[-400:], flush=True)
finally:
    for p in (locals().get('procs') or []) + ([head_prep] if head_prep else []):
        if p.poll() is None:
            p.kill()
    shutil.rmtree(tmpdir, ignore_errors=True)
    try:
        os.remove(running)
    except OSError:
        pass
