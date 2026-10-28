#!/usr/bin/env python3
"""Word timings for the assembled cut -> <project>/words.json (these drive every caption).

Usage:  PY transcribe_cut.py <project_dir> ["names and brand words said in the reel: Claude, AI Video Editor, Vladsdigital"]
The engine is speech.py's: Soniox when the buyer saved a key (the most accurate for sr/hr/bs), else offline Whisper
(large-v3-turbo for sr/hr/bs, medium.en for English), in the language set in config.json. The names are sent as
context. Both still mishear names and loanwords sometimes: fix captions by hand from what the speaker actually said.
"""
import json
import os
import subprocess
import sys

sys.dont_write_bytecode = True   # no __pycache__ next to the scripts (a plugin's folder is not ours to write in)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skillenv  # noqa: E402
import speech  # noqa: E402

skillenv.utf8_stdio()
proj = skillenv.path_arg(sys.argv[1])
wav = os.path.join(proj, 'work', 'aroll.wav')
os.makedirs(os.path.join(proj, 'work'), exist_ok=True)
terms = speech.parse_terms(sys.argv[2]) if len(sys.argv) > 2 else []
subprocess.run([skillenv.tool('ffmpeg'), '-loglevel', 'error', '-y', '-i', os.path.join(proj, 'assets', 'aroll.mp4'), '-vn', '-ac', '1',
                '-ar', '16000', wav], check=True)
segs, engine = speech.transcribe(wav, tier='best', terms=terms)
ws = speech.flat(segs)
with open(os.path.join(proj, 'words.json'), 'w', encoding='utf-8') as fh:
    json.dump(ws, fh, indent=1, ensure_ascii=False)
# keep the untouched output too: words.json is then cleaned and marked by hand (see references/captions.md)
with open(os.path.join(proj, 'work', 'words_raw.json'), 'w', encoding='utf-8') as fh:
    json.dump(ws, fh, indent=1, ensure_ascii=False)
print(f'engine: {engine}')
print(' '.join(f"{w['text']}@{w['start']:.2f}" for w in ws))
