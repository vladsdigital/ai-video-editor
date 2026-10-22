#!/usr/bin/env python3
"""Reel Lab speech: one place that turns audio into word timings, in the buyer's language.

Two engines, same output:
  soniox    Soniox async API (stt-async-v5). The most accurate for Serbian, Croatian and Bosnian, names included.
            Needs the buyer's own key (console.soniox.com) and the internet. A minute of audio costs a fraction of a cent.
  whisper   faster-whisper on this computer, free and offline. Multilingual models for sr/hr/bs, English-only
            models when the reel is in English (they are better at English).

Which one runs: config.json "transcriber": "auto" (the default: Soniox when a key is saved, else Whisper),
"soniox" or "whisper". The language is config.json "language": "sr" (default), "hr", "bs" or "en".

Library use (every script that needs words calls this, never WhisperModel directly):
    import speech
    segs, engine = speech.transcribe(wav, tier='best', terms=['Claude', 'Reel Lab'])
    -> segs = [{'start', 'end', 'text', 'words': [{'text', 'start', 'end'}]}], engine = 'soniox' | 'whisper:<model>'
    tier 'fast' = picking takes / studying examples, 'best' = the words.json that drives every caption.

Command line:
    PY speech.py status                     which engine, which language, key saved or not (never prints the key)
    PY speech.py key [--clipboard]          save the buyer's Soniox key (stdin or hidden prompt; never an argument)
    PY speech.py key --forget               remove the saved key (Whisper is used from then on)
    PY speech.py use soniox|whisper|auto    pick the engine
    PY speech.py language sr|hr|bs|en       pick the language of the reels
    PY speech.py test <audio or video>      transcribe a file and print the words (a quick check)
Standard library only for Soniox; Whisper needs the skill's own Python (PY), which has faster-whisper.
"""
import getpass
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skillenv  # noqa: E402

LANGUAGES = {'sr': 'Serbian', 'hr': 'Croatian', 'bs': 'Bosnian', 'en': 'English'}
DEFAULT_LANGUAGE = 'sr'
SONIOX_API = 'https://api.soniox.com'
SONIOX_MODEL = 'stt-async-v5'
# Whisper models per tier. sr/hr/bs share one multilingual model; English keeps the sharper English-only ones.
WHISPER = {'fast': {'multi': 'small', 'en': 'small.en'},
           'best': {'multi': 'large-v3-turbo', 'en': 'medium.en'}}
# Whisper has no separate Bosnian; it writes Bosnian well as Croatian/Serbian. Soniox gets all three as hints.
WHISPER_LANG = {'sr': 'sr', 'hr': 'hr', 'bs': 'bs', 'en': 'en'}


# ---------------------------------------------------------------- settings

def settings(state=None):
    """{'language', 'script', 'transcriber'} from config.json, with defaults."""
    try:
        with open(skillenv.config_file(state), encoding='utf-8') as fh:
            cfg = json.load(fh)
    except (OSError, ValueError):
        cfg = {}
    lang = str(cfg.get('language') or DEFAULT_LANGUAGE).lower()
    return {'language': lang if lang in LANGUAGES else DEFAULT_LANGUAGE,
            'script': 'cyrillic' if str(cfg.get('script', '')).lower().startswith('cyr') else 'latin',
            'transcriber': str(cfg.get('transcriber') or 'auto').lower()}


def save_setting(key, value, state=None):
    path = skillenv.config_file(state)
    try:
        with open(path, encoding='utf-8') as fh:
            cfg = json.load(fh)
    except (OSError, ValueError):
        cfg = {}
    cfg[key] = value
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(cfg, fh, indent=1, ensure_ascii=False)
    os.replace(tmp, path)


def whisper_models(language=None):
    """The Whisper models the current language needs (prefetch downloads these)."""
    lang = language or settings()['language']
    kind = 'en' if lang == 'en' else 'multi'
    return [WHISPER['fast'][kind], WHISPER['best'][kind]]


# ---------------------------------------------------------------- the Soniox key

def key_file(state=None):
    return os.path.join(state or skillenv.state_dir(), 'keys', 'soniox.key')


def load_key(state=None):
    """The buyer's Soniox key, or None. Order: SONIOX_API_KEY, the Studio's own key file, then the places the
    standalone soniox-transkript tool keeps one (so a key saved there works here too)."""
    if os.environ.get('SONIOX_API_KEY', '').strip():
        return os.environ['SONIOX_API_KEY'].strip()
    home = os.path.expanduser('~')
    for p in (key_file(state), os.path.join(home, '.config', 'soniox', 'api_key'), os.path.join(home, '.soniox.key')):
        try:
            with open(p, encoding='utf-8') as fh:
                k = fh.read().strip()
            if k:
                return k
        except OSError:
            continue
    return None


def _read_clipboard():
    osn = skillenv.os_name()[0]
    cmds = {'macos': [['pbpaste']], 'windows': [['powershell', '-NoProfile', '-Command', 'Get-Clipboard']],
            'linux': [['wl-paste', '-n'], ['xclip', '-selection', 'clipboard', '-o']]}
    for c in cmds.get(osn, cmds['linux']):
        try:
            r = subprocess.run(c, **skillenv.TEXT, timeout=10)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            continue
    return ''


def save_key(clipboard=False, state=None):
    if clipboard:
        k = _read_clipboard()
    elif sys.stdin.isatty():
        k = getpass.getpass('Soniox ključ (ne prikazuje se dok kucaš): ')
    else:
        k = sys.stdin.read()
    k = (k or '').strip()
    if not re.fullmatch(r'[A-Za-z0-9_\-\.]{20,200}', k):
        print('STATUS soniox KEY INVALID (that does not look like a Soniox key: copy it again from console.soniox.com)')
        return 1
    try:
        _api('/v1/files?limit=1', key=k)
    except SonioxError as e:
        print(f'STATUS soniox KEY REFUSED ({e.plain})')
        return 1
    p = key_file(state)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    fd = os.open(p + '.tmp', os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as fh:
        fh.write(k + '\n')
    os.replace(p + '.tmp', p)
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass
    print(f'STATUS soniox KEY SAVED (ends in ...{k[-4:]}, this computer only)')
    return 0


# ---------------------------------------------------------------- Soniox

class SonioxError(Exception):
    def __init__(self, code, detail):
        self.code, self.detail = code, detail
        plain = {401: 'the key is wrong or was revoked: make a new one at console.soniox.com',
                 402: 'the Soniox account is out of credit: top it up at console.soniox.com',
                 429: 'Soniox is busy or the account hit its limit: try again in a minute'}.get(code)
        self.plain = plain or (f'Soniox said {code}: {detail[:160]}' if code else f'no connection to Soniox ({detail[:120]})')
        super().__init__(self.plain)


def _api(path, method='GET', body=None, content_type=None, key=None, timeout=300):
    req = urllib.request.Request(SONIOX_API + path, data=body, method=method,
                                 headers={'Authorization': f'Bearer {key}', 'User-Agent': 'reel-lab'})
    if content_type:
        req.add_header('Content-Type', content_type)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raise SonioxError(e.code, e.read().decode('utf-8', 'replace'))
    except (urllib.error.URLError, OSError) as e:
        raise SonioxError(0, str(e))


def _upload(path, key):
    boundary = uuid.uuid4().hex
    with open(path, 'rb') as fh:
        data = fh.read()
    body = b''.join([f'--{boundary}\r\n'.encode(),
                     f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(path)}"\r\n'.encode(),
                     b'Content-Type: application/octet-stream\r\n\r\n', data, f'\r\n--{boundary}--\r\n'.encode()])
    return _api('/v1/files', 'POST', body, f'multipart/form-data; boundary={boundary}', key)['id']


def _tokens_to_words(tokens):
    """Soniox returns sub-word tokens: a token that starts with a space starts a new word, punctuation sticks to
    the word before it. -> [{'text', 'start', 'end'}] in seconds."""
    words, space = [], False
    for t in tokens:
        text = t.get('text') or ''
        if not text or text.startswith('<'):          # <end> and similar control tokens
            continue
        s = (t.get('start_ms') or 0) / 1000.0
        e = (t.get('end_ms') if t.get('end_ms') is not None else (t.get('start_ms') or 0) + (t.get('duration_ms') or 0)) / 1000.0
        bare = text.strip()
        if not bare:
            space = True                               # Soniox sometimes sends the space as its own token: " ", "će"
            continue
        new_word = space or text[:1].isspace() or not words
        space = text[-1:].isspace()
        if not new_word or (bare and all(not c.isalnum() for c in bare) and words):
            words[-1]['text'] += bare
            words[-1]['end'] = round(max(words[-1]['end'], e), 3)
        else:
            words.append({'text': bare, 'start': round(s, 3), 'end': round(e, 3)})
    return words


def _soniox(wav, language, terms, key):
    hints = ['en', 'sr', 'hr', 'bs'] if language == 'auto' else [language] + [l for l in ('sr', 'hr', 'bs', 'en') if l != language]
    base = {'model': SONIOX_MODEL, 'language_hints': hints, 'enable_speaker_diarization': False,
            'enable_language_identification': False}
    return _soniox_run(_upload(wav, key), base, terms, key)


def _soniox_run(fid, base, terms, key):
    tid = None
    try:
        # context helps with names and brand words. Newer models take {"terms": [...]}, older ones a plain string:
        # try the richer form first and fall back so a model change never breaks transcription.
        tries = ([{'context': {'terms': terms}}, {'context': ', '.join(terms)}] if terms else []) + [{}]
        last = None
        for extra in tries:
            try:
                tid = _api('/v1/transcriptions', 'POST', json.dumps(dict(base, file_id=fid, **extra)).encode(),
                           'application/json', key)['id']
                break
            except SonioxError as e:
                last = e
                if e.code != 400:
                    raise
        if not tid:
            raise last
        t0 = time.time()
        while True:
            st = _api(f'/v1/transcriptions/{tid}', key=key)
            if st.get('status') == 'completed':
                break
            if st.get('status') == 'error':
                raise SonioxError(500, st.get('error_message') or 'transcription failed')
            if time.time() - t0 > 900:
                raise SonioxError(0, 'no answer from Soniox in 15 minutes')
            time.sleep(1.5)
        tokens = (_api(f'/v1/transcriptions/{tid}/transcript', key=key) or {}).get('tokens', [])
    finally:
        for p in ([f'/v1/transcriptions/{tid}'] if tid else []) + [f'/v1/files/{fid}']:
            try:
                _api(p, 'DELETE', key=key, timeout=30)      # nothing of the buyer's stays on Soniox's servers
            except SonioxError:
                pass
    return _tokens_to_words(tokens)


# ---------------------------------------------------------------- Whisper

def _whisper(wav, language, terms, tier, vad):
    from faster_whisper import WhisperModel
    kind = 'en' if language == 'en' else 'multi'
    name = WHISPER[tier][kind]
    # device='cpu': the default 'auto' picks CUDA on any PC with an NVIDIA card and then dies on the first clip with
    # "Library cublas64_12.dll is not found" unless the CUDA toolkit happens to be installed
    m = WhisperModel(name, device='cpu', compute_type='int8')
    prompt = (', '.join(terms) + '.') if terms else None
    segs, _ = m.transcribe(wav, language=WHISPER_LANG.get(language), word_timestamps=True, vad_filter=vad,
                           initial_prompt=prompt, condition_on_previous_text=False)
    words = []
    for s in segs:
        for w in (s.words or []):
            t = w.word.strip()
            if not t:
                continue
            if words and t[:1] in '-.,' and len(t) > 1 and t[1:2].isdigit():   # "GPT" "-6" / "5" ".1" / "2" ",5"
                words[-1]['text'] += t
                words[-1]['end'] = round(w.end, 3)
                continue
            words.append({'text': t, 'start': round(w.start, 3), 'end': round(w.end, 3)})
    return words, 'whisper:' + name


# ---------------------------------------------------------------- shared

def segments(words, gap=0.7):
    """Words -> sentence-like segments: a break after . ? ! or a pause longer than `gap` seconds."""
    out, cur = [], []
    for w in words:
        if cur and (w['start'] - cur[-1]['end'] > gap):
            out.append(cur); cur = []
        cur.append(w)
        if w['text'][-1:] in '.?!':
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return [{'start': s[0]['start'], 'end': s[-1]['end'], 'text': ' '.join(w['text'] for w in s), 'words': s} for s in out]


def engine_for(cfg=None):
    cfg = cfg or settings()
    want = cfg['transcriber']
    if want == 'whisper':
        return 'whisper'
    if want == 'soniox' or load_key():
        return 'soniox'
    return 'whisper'


def to_wav(src, wav):
    subprocess.run([skillenv.tool('ffmpeg'), '-loglevel', 'error', '-y', '-i', src, '-vn', '-ac', '1', '-ar', '16000', wav],
                   check=True)
    return wav


def transcribe(audio, tier='best', terms=None, language=None, vad=False, quiet=False):
    """-> (segments, engine). `audio` is a 16 kHz mono wav (or any file ffmpeg reads). Soniox failing (offline, no
    credit) falls back to Whisper with one NOTE line, so an edit never stops on it. language='auto' detects it
    (examples from other creators); None = the buyer's language from config.json."""
    cfg = settings()
    lang = language or cfg['language']
    terms = [t.strip() for t in (terms or []) if t and t.strip()][:100]
    if not audio.lower().endswith('.wav'):
        audio = to_wav(audio, os.path.join(tempfile.gettempdir(), f'reel-lab-{uuid.uuid4().hex}.wav'))
    if engine_for(cfg) == 'soniox':
        key = load_key()
        if key:
            try:
                return segments(_soniox(audio, lang, terms, key)), 'soniox'
            except SonioxError as e:
                if not quiet:
                    print(f'NOTE Soniox did not work ({e.plain}). Using the offline transcription for this one.', flush=True)
        elif not quiet:
            print('NOTE Soniox is picked but no key is saved: using the offline transcription. Save one with speech.py key.',
                  flush=True)
    words, engine = _whisper(audio, lang, terms, tier, vad)
    return segments(words), engine


def flat(segs):
    return [w for s in segs for w in s['words']]


def parse_terms(text):
    """'Claude, Claude Code, skill.' -> ['Claude', 'Claude Code', 'skill']"""
    return [t.strip(' .') for t in re.split(r'[,;\n]', text or '') if t.strip(' .')]


# ---------------------------------------------------------------- command line

def main(argv):
    skillenv.utf8_stdio()
    cmd = argv[0] if argv else 'status'
    if cmd == 'status':
        cfg = settings()
        k = load_key()
        print(f"STATUS speech language {cfg['language']} ({LANGUAGES[cfg['language']]}), script {cfg['script']}")
        print(f"STATUS speech engine {engine_for(cfg).upper()} (setting: {cfg['transcriber']}; "
              f"Soniox key {'SAVED ...' + k[-4:] if k else 'NOT SET'})")
        return 0
    if cmd == 'key':
        if '--forget' in argv:
            try:
                os.remove(key_file())
                print('STATUS soniox KEY REMOVED')
            except OSError:
                print('STATUS soniox KEY NOT SET')
            return 0
        return save_key(clipboard='--clipboard' in argv)
    if cmd == 'use' and len(argv) > 1 and argv[1] in ('soniox', 'whisper', 'auto'):
        save_setting('transcriber', argv[1])
        return main(['status'])
    if cmd == 'language' and len(argv) > 1 and argv[1] in LANGUAGES:
        save_setting('language', argv[1])
        return main(['status'])
    if cmd == 'script' and len(argv) > 1 and argv[1] in ('latin', 'cyrillic'):
        save_setting('script', argv[1])
        return main(['status'])
    if cmd == 'test' and len(argv) > 1:
        segs, engine = transcribe(skillenv.path_arg(argv[1]), terms=parse_terms(argv[2]) if len(argv) > 2 else None)
        print(f'engine: {engine}')
        for s in segs:
            print(f"[{s['start']:6.2f}-{s['end']:6.2f}] {s['text']}")
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
