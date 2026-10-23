# Captions: the 20 styles, the word marks, where they sit

One engine (`SK/engine/captions.py`), 20 styles, all driven by the same `words.json`. `build_reel.py` picks the style
from the saved picks. You never edit the engine for a reel: you clean the words, mark them, and write the title.
A buyer with a style of their own (an example they showed, a look they described) gets a custom caption style
instead, a spec the same engine renders: `references/replicate.md`. The marks and the bands below work the same.

## The 20

| Key | Name | The look | Uses the marks | Sits | Needs |
|---|---|---|---|---|---|
| `arcade` | Arcade | White pixel type, short phrases, hard cuts | cta lands twice the size in quotes | chest | |
| `low-key` | Low Key | Tiny quiet captions that build word by word, under a pinned white title pill | | chest + title at the top | a title |
| `field-notes` | Field Notes | Quiet book serif, whole phrases fade in, each in a different open spot | | open wall left / chest / open wall right | open wall beside the speaker (falls back to the chest) |
| `anchor` | Anchor | Bold clean sans in one spot, hard cuts | num and emph take over the frame with a glow, cta drops under in italic | chest | |
| `loud-lowercase` | Loud Lowercase | Huge tight lowercase, one word at a time | num parks top left with what it counts, cta in caps | chest + top left | |
| `vanity` | Vanity | Tall cream serif, one word at a time | any marked word flips to yellow italic, key gets a small icon, cta in quotes | chest | |
| `bubblegum` | Bubblegum | One glowing pink word above the head, swashy pink title | key keeps its capital | above the head + title | room above the head (falls back to the chest), a swash title |
| `moodboard` | Moodboard | Bold rounded line, thin italic line typed under it, sparkles | key keeps its capital | chest | |
| `golden-hour` | Golden Hour | Gold italic film subtitles | cta in quotes | lower third | |
| `spec-sheet` | Spec Sheet | Small wide caps dead centre, big tilted yellow tags | num and cta become tags top left | chest + top left | |
| `bold` | Bold | Heavy tight lowercase, big words BEHIND the head | num / emph / cta go giant behind the head (emph and cta in yellow) | chest + behind the head | a clean cutout, room above the head (else the big word lands over the chest) |
| `cool-girl` | Cool Girl | Small calm lowercase, one big yellow serif italic line per thought | num / emph / cta are the big line | chest (a tall block) | |
| `cool-dude` | Cool Dude | Tiny wide caps over one heavy serif word | num / emph / cta are the serif word | chest (a tall block) | |
| `karaoke` | Karaoke | Wide caps on a frosted dark plate, the spoken word lights up | | chest | |
| `signature` | Signature | Clean wide caps; a marker script signs over heavy italic caps | num and cta get the script moment | chest | |
| `keyword` | Keyword | One clean tight lowercase line | every marked word is yellow; a marked word alone goes bigger | chest | |
| `weight-shift` | Weight Shift | Thin lead-in, heavy black punch word | num / emph / cta are the punch | chest (a tall block) | |
| `terminal` | Terminal | Code-font lead-in, one big serif italic word | num / emph / cta are the punch | chest (a tall block) | |
| `outline` | Outline | Tall condensed caps, the punch word drawn hollow | num / emph / cta are the punch | chest (a tall block) | |
| `viral-guy` | Viral Guy | One quiet cream word at a time, hard cuts, no pop | num / emph / cta go huge; a num brings a tiny caps line of what it counts ("14,000" over FOLLOWERS) | chest | |

`none` = no captions at all (titles and effects only).

## Marking the words (do this for every reel)

Each word in `words.json` can carry one mark in its `e` field. The marks are what make a caption style look
designed instead of typed.

| Mark | Meaning | Mark it when |
|---|---|---|
| `num` | a number worth showing big | the number IS the point of the line: "7 video effects", "$500 a day", "10x". Not for passing numbers ("one of the things", a year, a time of day). |
| `key` | a name or brand | every product, app, company or person said by name: "Claude", "Instagram". It keeps its capital in lowercase styles and turns yellow in Keyword. |
| `emph` | the word the line leans on | a sentence has no number and no comment keyword, and one word carries it ("never", "automatically", "everything"). The word you would stress out loud. |
| `cta` | the comment keyword | the word they ask people to comment: "comment EDIT". Exactly one per reel. |

The rule:
1. Run `PY "SK/scripts/marks.py" "<project>"` AFTER fixing mishearings. It guesses `num` (digits and number words),
   `cta` (the word after "comment") and `key` (capitalised words that do not start a sentence). It never guesses `emph`.
   It reads the word lists of the reel's language (config.json `language`; all lists live in `SK/engine/lang.py`,
   sr / hr / bs share one set, en is the original English one):
   - `num`: digits, plus "dva / dve / dvije, tri, pet, deset, dvadeset, sto, hiljadu / tisuću, milion / milijun,
     pola, duplo" and their common forms. "jedan / jedna / jedno" are never guessed (like English "one": usually an
     article), and neither are ordinals ("prvi put").
   - `cta`: the first word after "komentariši / komentarišite / komentiraj(te)" (or English "comment"), skipping
     "reč / riječ, ispod, dole / dolje, u komentaru, mi, samo ...": "komentariši reč ŠABLON" -> `ŠABLON`. After a
     generic verb ("napiši(te), ukucaj(te), upiši(te), pošalji(te), javi(te), ostavi(te), stavi(te)") only a word
     in capitals or quotes, or one after "reč / riječ / komentar", counts: "napiši mi u komentaru VODIČ" -> `VODIČ`,
     but "pošalji mi poruku" marks nothing. Never across the end of a sentence.
   - `key`: the same rule in every language (Serbian, Croatian and Bosnian also capitalise only names).
2. Then go through the transcript sentence by sentence:
   - at most ONE of `num` / `emph` per sentence (they are the punch; two punches fight). Keep the one the
     sentence is about and remove the other. A long sentence counts part by part: a comma, "and", "then" or "so"
     starts a new part.
   - the comment keyword ALWAYS keeps its `cta` mark, also when its sentence already has a `num` or an `emph`
     (a one-sentence reel: "get all 21 effects, then just comment VIDEO" keeps `21` num and `VIDEO` cta).
   - `key` on every name, as many as there are. Check sentence openers by hand: the script cannot tell a name that
     starts a sentence from a normal word (it lists them).
   - add `emph` where a sentence has no punch yet and one word clearly carries it. Not every sentence needs one.
   - never mark filler ("the", "and", "so", "that", "for"; "i", "da", "je", "znači", "ovaj", "evo", "pa").
3. A short reel (under 10 seconds) usually ends up with 2 to 5 marks. More than one mark every 4 words is too many.

Example: "Everybody's talking about Claude editing videos, so here are seven video effects that Claude created
for me." -> `Claude` key, `seven` num (write it as `7` if the buyer's style shows numbers big), second `Claude` key.

```json
{"text": "seven", "start": 3.18, "end": 3.52, "e": "num"}
```

## Phrases and script (Latin or Cyrillic)

Every style breaks the words into phrases the same way (`chunk` in `SK/engine/captions.py`): on length, on
punctuation, on a pause, and a line never ends on a weak word of the reel's language (sr / hr / bs: "i, a, u, na,
da, je, se, za, od, sa, ili, ali, što, kao, taj, ovaj, moj, svoj ..."; the full list is `weak` in
`SK/engine/lang.py`). For sr / hr / bs every built-in style allows 12% more characters per line than its English
tuning (their words are longer); a custom spec's `chars` is used as written.

Cyrillic: config.json `"script": "cyrillic"` (`PY "SK/scripts/speech.py" script cyrillic`) shows every caption,
title and style text in Serbian Cyrillic. It is display only: `words.json`, `plan.json` and every mark stay in
Latin, so write and fix them in Latin as usual. Stays in Latin: brands and names in `KEEP_LATIN` (Claude, ChatGPT,
Instagram, TikTok, YouTube, Reel Lab ...), any CamelCase word, words with q / w / x / y, URLs, @handles, #hashtags,
anything with a digit, known acronyms in capitals (AI, GPT, CEO, SEO, PDF ...) and any word of 2 to 5 capitals in
`words.json` that is not the comment keyword. Add the reel's own with plan.json `"keep_latin": ["Acme", "Bojan
Studio"]`. Layer html you write yourself (`layers`) and effect slots are not converted: write layer text in
Cyrillic. "dj" is never read as "ђ" (write "đ"); nad- / pod- / od- words such as "nadživeti", "podžupan",
"odžaliti" keep д+ж.

## Titles come from the hook

`plan.json` (started by `init_project.py` with a first guess, rewrite it):
- `"title": ["line one", "line two"]`: the reel's hook as two short lines, up to about 26 characters each, sentence
  case. Low Key pins it at the top for the whole reel. Overall styles use it as their fallback headline.
- `"swash": ["Line One", "Line Two"]`: the same idea, shorter (up to about 16 characters a line), Title Case.
  Bubblegum's title.
Write what the reel promises, in the speaker's own words: "7 video effects" / "Claude made for me". Not a summary,
not clickbait they did not say.

## Where captions sit (worked out per clip, never typed in)

`PY "SK/scripts/layout.py" "<project>"` samples the reel, cuts the speaker out of just those frames, reads the head
off the silhouette and writes `layout.json`. Look at `work/layout/check.jpg` once (up to four frames, half size):
the green box has to run from the top of the head to the chin, and its numbers are printed under it. Blue lines are
the bands, red is the Reels safe zone. When the clean cutout is installed (`setup.py --matting`) the samples are cut
out with it, which takes about a minute and is not fooled by what hangs behind the head.

| Band | In `bands` | Rule | When there is no room |
|---|---|---|---|
| Above the head | `Y_ABOVE_HEAD` | 104px above the highest head position, never above y 236 | `null`: Bubblegum's word goes over the chest |
| Behind the head | `HEAD_TOP` | Bold's big word shows 72% of its height above the head, shrinking to fit under y 226 | under 110px of type: the word lands over the chest, in front |
| Chest | `Y_CHEST` | y 1170, as long as the chin is at least 100px above it | the face is low or fills the frame: the picture is lifted (up to 260px, `lift`) and the captions take the collar band under the chin. `fits.chest` says `tight`: one-line styles only |
| Lower third | `Y_LOWER` | y 1376 (one line ends at 1452) | same lift |
| Open wall | `WALL_LEFT`, `WALL_RIGHT` | beside the speaker at face height, at least 240px wide | `null`: Field Notes uses the spots that exist |

Punch-ins move the head between segments: the bands are the ones that are safe in every segment, and Bold reads
the head height of the segment each word falls in.

The quick cutout can be fooled: a framed picture, poster or lamp right behind the head joins the outline and the
box starts about 100px too high and stops at the nose. `layout.py` prints `CHECK THE HEAD BOX` when it could not
find a neck under the head (the usual sign, also normal with long hair or a hood), and `fx_new.py` / `fx_add.py`
print `CHECK layout.json` when an effect's own clean cutout disagrees with it by more than 60px. Either way: if
`check.jpg` shows the green box off the face (too high, a poster, a second person), run `setup.py --matting` once
and `layout.py` again, or correct `head` and `bands` in `layout.json` by hand. They are plain numbers in the
1080x1920 frame. Bold, Bubblegum, Field Notes and the face box of the self-check all read them.

Tall styles (Cool Girl, Cool Dude, Weight Shift, Terminal, Outline) stack three lines from about 70px above
`Y_CHEST`. On a `tight` chest band tell the buyer and use a one-line style for that reel.

## Fonts for custom caption specs

Every family below is in `assets/fonts/fonts.css` (weights listed are the declared ones). All cover
č ć š ž đ unless marked. Cyr = Serbian Cyrillic (љ њ џ ђ ћ ј) included. For Cyrillic captions pick a Cyr face:
a face without it falls back to a system font for those letters.

| Role | Family: weights | Cyr |
|---|---|---|
| Sans | Inter 300 500, Inter Tight 500i 700 800 900, Montserrat 500 700 800 900, Arimo 400 500 700, Manrope 600 800, Onest 500 800, Rubik 700 900 | yes |
| Sans | Figtree 500 600, Poppins 600 700, Archivo 800 900 900i (expanded) | no |
| Wide / heavy display | Unbounded 700 900, Russo One 400, Dela Gothic One 400 | yes |
| Wide / heavy display | Archivo Black 400 | no |
| Condensed | Oswald 500 700, Roboto Condensed 500 800, Fira Sans Extra Condensed 700 900 | yes |
| Condensed | Bebas Neue 400, Barlow Condensed 500 600 | no |
| Rounded | Nunito 800 900 | yes |
| Serif | Playfair Display 500i 600i 700, Lora 500 500i, Cormorant Garamond 600 500i | yes |
| Serif | Instrument Serif 400 400i, DM Serif Display 400 400i, Newsreader 400 500 500i 600i | no |
| Script / hand | Caveat 600, Marck Script 400, Bad Script 400, Pacifico 400, Lobster 400, Pangolin 400 (marker), Amatic SC 700 | yes |
| Script / hand | Covered By Your Grace 400, Berkshire Swash 400, Elsie Swash Caps 400 900 (its č ć đ come from Berkshire Swash, see `standins.json`), Permanent Marker 400 (file `PermanentMarker-400-normal.woff2`, not in fonts.css) | no |
| Mono / pixel | JetBrains Mono 500 | yes |
| Mono / pixel | Pixelify Sans 500 600 700 (basic Cyrillic, no ђ ћ љ њ џ) | partly |

Cyrillic stand-ins for the faces without it: Archivo expanded or Archivo Black -> Unbounded or Dela Gothic One;
Bebas Neue -> Oswald 700; Barlow Condensed -> Roboto Condensed; Poppins or Figtree -> Montserrat or Onest;
Instrument Serif or DM Serif Display -> Playfair Display or Cormorant Garamond; Newsreader -> Lora;
Permanent Marker or Covered By Your Grace -> Pangolin or Caveat. A face that is not here: `get_font.py`
(it reports whether the face has č ć š ž đ and Cyrillic).
