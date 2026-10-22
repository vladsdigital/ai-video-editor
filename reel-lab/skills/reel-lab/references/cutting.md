# Cutting: best takes, dead air, a clean transcript

## 1. Ingest
`PY "SK/scripts/ingest.py" "<project>" <clips or one folder> [--newest N]` writes:
- `sources.json` (c1, c2 ... oldest to newest), `work/sheets.jpg` (8 frames across each clip: look at it for
  setups and angles), `words_cN.json`, and `transcript.txt` (per clip: lines with times, every word with its time,
  and a speech map where `S12.40` = silence starts and `E13.10` = silence ends).
Originals are read in place. Nothing is copied or changed. The first transcription downloads the speech model:
about 0.5 GB here, then 1.6 GB more at step 4 for the final pass (one time each; English reels use the English-only
models instead). Setup normally fetched both already (prefetch.py). If not, tell the buyer before you start, once:
"Prva montaža skida model za prepoznavanje govora, oko 2 GB. To se dešava samo jednom."

## 2. Pick takes -> `<project>/edl.json`
People repeat a line until it lands. Rebuild what they meant to say from the takes:
- Use the LAST complete clean take of each line, unless the buyer says otherwise ("the good one starts at 0:47"
  means one continuous take from there).
- In point: 0.05 to 0.07s before the first word. Out point: where the silence starts after the last word (speech map).
- A word can go silent for a moment in the middle: the stop before a t, k, p, b, d or g ("fas" ... "ter"). A short
  burst of sound 0.03 to 0.15s after such a dip is still the word, even when Whisper writes it as a word of its own
  ("here", "Mr."). The out point goes after that burst, never in the dip. After assembling, read the cut's transcript
  once: a last word that comes back short ("fast," where they said "faster") means the out point landed inside it.
- Cut dead air between lines. Before trimming a short pause inside a line, confirm it with silencedetect
  (`ffmpeg -i <clip> -af silencedetect=n=-40dB:d=0.08 -f null -`): Whisper word times can be 0.1 to 0.3s off and it
  can invent a word at a cut.
- Two segments in a row from the same angle: punch one in (zoom 1.3 to 1.9, `cx` / `cy` on the chest). Sharp when
  the source is 4K, soft above about 1.4 on a 1080 source.
- Not sure about a name or the comment keyword: transcribe just that snippet again with the names in the prompt
  (`PY "SK/scripts/speech.py" test "<snippet>" "<names>"`: the buyer's language and engine. Never call WhisperModel
  directly; speech.py keeps the device on 'cpu', see gotchas.md).

```json
[{"id": "hook", "clip": "c1", "in": 12.66, "out": 15.72, "zoom": 1.0, "cx": 0.5, "cy": 0.5, "line": "Everybody's talking about..."},
 {"id": "cta",  "clip": "c2", "in": 4.10,  "out": 7.02,  "zoom": 1.4, "cx": 0.5, "cy": 0.42, "line": "Comment EDIT and..."}]
```
`id` is a short name with letters only. Tell the buyer the plan in two lines and keep going. Do not wait for a yes.

## 3. Assemble
`PY "SK/scripts/assemble.py" "<project>"` cuts straight from the originals into `assets/aroll.mp4` (1080x1920,
clean 30fps from t=0) and writes `segments.json` (first frame and frame count of every segment, source size).
The last line must say the frame totals match.

## 4. Words
`PY "SK/scripts/transcribe_cut.py" "<project>" "Claude, Claude Code, <other names said>"` writes `words.json`:
`[{"text": "Everybody's", "start": 0.08, "end": 0.52}, ...]`. These times drive every caption, so clean them:
- Fix mishearings by hand from what was actually said. Usual ones: "Claude" -> "cloud" / "claws" / "Claud",
  "skill" -> "scale", product names split in two ("GPT" "-6", "5" ".1": the script joins the common cases, check).
  In Serbian, Croatian and Bosnian also: names and surnames, English loanwords ("prompt", "template", "content")
  written phonetically or split, wrong case endings (padeži), č/ć and đ/dž confused, ije/je against the speaker's
  own variant, numbers. The words in the second argument are sent to the engine as context: put every name in.
- Keep Whisper's punctuation honest: a comma or full stop ends a caption phrase, so remove a comma that is not a
  pause and add a full stop where a sentence really ends.
- Keep numbers the way they should READ on screen ("7", not "seven", when a style shows the number big).
- Never change the times unless a word is clearly late or early against the audio.
`work/words_raw.json` keeps Whisper's untouched output.

Then mark the words: `PY "SK/scripts/marks.py" "<project>"` and the rule in `references/captions.md`.

## 5. Check the cuts (after the render)
`PY "SK/scripts/check_cuts.py" "<project>" "renders/<file>.mp4" --phone` writes `work/cut_check.jpg` (the frame before
and after every cut, side by side) and a 720p phone copy. Every "after" frame must show the new shot cleanly.
The render may be written the short way (`renders/<file>.mp4`): both check scripts look inside the project.

The last line it prints is the loudness of the render in LUFS, the way Instagram, TikTok and YouTube measure it,
and what to do. Talking-head reels play at about -14 LUFS. The edit keeps the level the clip was recorded at.
- "fine" or "louder than the platforms play": nothing to do.
- "quieter than other reels" (below about -16.5 LUFS, common with a phone or lavalier recorded too low): say so in
  the delivery note in one line and offer the louder copy. On yes, run the same command again with `--loud`: it
  writes `renders/<file>-loud.mp4` at -14 LUFS (two passes, one even gain for the whole reel so the voice keeps its
  natural dynamics, true peak under -1 dB, picture copied untouched). Deliver that one, and make the phone copy
  from it (`check_cuts.py ... "renders/<file>-loud.mp4" --phone`).
Buyer line: "Snimak ti je dosta tih u odnosu na druge rilsove. Napravio sam i glasniju verziju, ista je samo se
bolje čuje. Hoćeš nju?"
