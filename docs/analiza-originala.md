# Analiza: Creator Studio (tenfoldmarc/studio-plugin) v2.6.2

Datum: 23.10.2026. Izvor: ceo repozitorijum `studio-plugin-main` (674 fajla, 40 MB, od toga ~76k linija koda/teksta, ostalo preview MP4/JPG i fontovi).

## 1. Šta je to u jednoj rečenici

Claude Code plugin (marketplace `creator-studio`, plugin `video-studio`) u kome **Claude radi kao montažer**: kroz niz malih Python CLI skripti pretvara sirove 9:16 talking-head klipove u gotov Instagram rils, u imenovanom stilu kupca. Plus karuseli, "trial reels" varijacije i objavljivanje preko Zernio API-ja.

Nema servera, nema licence/aktivacije, nema telemetrije. Sve se vrti lokalno na kupčevom računaru. **Vrednost proizvoda je u know-how-u**: promptovi (SKILL.md + references/*.md), caption engine, 46 efekata i QA rutina.

## 2. Arhitektura (najvažnije)

```
Claude (mozak, urednik)                     Python skripte (ruke)                  Renderer
───────────────────────                     ─────────────────────                  ────────
čita transcript + contact sheet  ───────►   ingest.py (whisper small.en)
piše edl.json (koji take, rezovi) ──────►   assemble.py (ffmpeg, 1080x1920 30fps)
ispravlja words.json (mishearings) ◄──────  transcribe_cut.py (whisper medium.en)
označava reči (num/key/emph/cta)  ◄──────  marks.py (heuristika, prvi predlog)
gleda check.jpg (head box)        ◄──────  layout.py (silueta iz cutout-a → bendovi za titlove)
piše plan.json (naslov, slojevi)  ───────►  init_project.py
bira efekte                       ───────►  footage_check.py → fx_new/fx_run/fx_add
                                            build_reel.py → index.html (GSAP timeline) ──► HyperFrames (npx, HTML→MP4)
gleda sheet-ove, popravlja        ◄──────  frames_check.py, check_cuts.py (--phone 720p)
```

Ključni dizajnerski potezi:
- **LLM donosi sve uredničke odluke** (izbor take-a, rezovi, ispravke transkripta, naglašene reči, tekst na ekranu). Skripte samo mere i izvršavaju. Komunikacija preko JSON fajlova u folderu projekta + `STATUS ...` linije na stdout-u koje Claude čita.
- **Render = HTML stranica**. Ceo rils je jedna HyperFrames kompozicija: `<video>` slojevi (footage, cutout, efekti) + DOM titlovi + `<audio>` SFX, animirano jednim pauziranim GSAP timeline-om (`window.__timelines.main`) koji renderer premotava frejm po frejm. Zabranjeni CSS keyframes i random, da bi render bio deterministički.
- **Vizuelna samokontrola**: posle svakog koraka skripta pravi contact sheet (JPG) koji Claude *gleda* (head box zeleno, safe zone crveno, frejmovi pre/posle reza).
- **Stanje kupca van plugina** (`~/Library/Application Support/video-studio`): Python venv, Node, ffmpeg, modeli, stilovi, picks. Update plugina ne briše ništa.

## 3. Komponente

### 3.1 Instalacija i okruženje
- `start.sh` / `start.ps1`: ako nema Python 3.9–3.13, skida **python-build-standalone 3.12** (SHA-256 pinovano). Na Macu nikad ne zove `/usr/bin/python3` (otvara "install developer tools").
- `setup.py` (samo stdlib): ffmpeg (preko `static-ffmpeg` paketa), **Node 22** sa nodejs.org, venv sa `faster-whisper==1.2.1`, `av<19`, `pillow`. Self-test i auto-popravka venv-a. Piše `.platform.json` (putanje do PY, HF, ffmpeg, node; `cutout: CoreML|CPU`).
- `prefetch.py` u pozadini (~3 GB): whisper `small.en` + `medium.en`, HyperFrames + njegov headless browser, background-removal model (~170 MB), **RobustVideoMatting** resnet50 ONNX (~105 MB).
- `update.py`: jednom dnevno čita `plugin.json` sa GitHub raw-a, nudi update, poziva `claude plugin marketplace update` + `claude plugin update`.
- CI: GitHub Actions matrix (Windows, Intel Mac, Apple Silicon) sa *sklonjenim* Python/Node/ffmpeg iz PATH-a, simulira čist računar i pravi kompletan rils od test-pattern videa + OS text-to-speech.

### 3.2 Montaža ("edit it")
- **Transkripcija**: faster-whisper na CPU int8. Pass 1 `small.en` po klipu (za biranje take-ova), pass 2 `medium.en` na sastavljenom rezu sa `initial_prompt` imenima. Samo engleski modeli (`.en`)!
- **Biranje take-a i rezovi**: piše ih Claude u `edl.json` (`{id, clip, in, out, zoom, cx, cy, line}`). Pravila: poslednji čist take svake rečenice, ulaz 0.05–0.07 s pre prve reči, punch-in 1.3–1.9 kad su dva segmenta za redom isti kadar. ffmpeg `silencedetect -38dB/0.35s` daje "speech map", ništa se ne seče automatski.
- **Layout (gde je glava)**: ne koristi face detection nego **siluetu iz cutout-a**: najveći blob, širina glave, brada = najuži red (vrat). Iz toga bendovi: iznad glave, grudi (y 1170), lower third (1376), zidovi levo/desno, "iza glave". Klasifikacija kadra (wide/medium/close) i kamere (still/drifting/moving).
- **Safe zone** (1080x1920): gore 220, dole 450, strane 35, desno 100 od y 1155 naniže. Titlovi i efekti nikad preko lica (oči–brada).
- **Titlovi**: `engine/captions.py` (1571 linija), **20 stilova** kao Python funkcije sa hardkodovanim CSS-om (keyword, karaoke, bold "iza glave", vanity, terminal, viral-guy...). Zajednička logika: grupisanje u fraze (max reči/karaktera, interpunkcija, pauza >0.3 s, bez visećih "the/and"), 4 tipa oznaka reči (`num`, `key`, `emph`, `cta`) sa pravilima gustine. Postoji i **custom spec** (font, boja, plate, stroke, lit, entrance, GSAP motion) za stilove napravljene po uzoru.
- **9 "overall" stilova**: paket grade (CSS filter) + tretman snimka (push-in, jump zoom, 4:3 prozor, cutout na pozadini) + default titlovi.
- **Cutout**: brzi (HyperFrames remove-background, CoreML na M čipu) ili čist (RVM ONNX, ~1.2 s/frejm, + Apple Vision `track.swift` za čišćenje "duhova" iznad glave).
- **QA**: `hf lint` 0 grešaka, snapshot sheet, frames_check (promena piksela u safe zoni/face boxu >1.5% = nešto je nacrtano tu), cuts strip, audio peak (ispod -6 dB nudi glasniju kopiju; nema LUFS normalizacije).

### 3.3 Efekti (46)
- Svaki efekat je folder: `effect.md` (uputstvo za Claude-a), `slot.json` (ugovor), `build.py` sa `CLIP` blokom koji Claude popunjava, opciono `prep/track/bake/check.py`.
- Tok: `fx_new` napravi izolovan "slot" projekat od N frejmova reela → `fx_run` pokreće korake → efekat se renderuje u svoj MP4 (ili providan WebM za overlay) → `fx_add` ga vraća u `plan.json`, uz **automatsko usklađivanje boja** (3x3 matrica + offset) i preuzimanje SFX cue-ova.
- `footage_check.py` propušta/odbija efekat po izmerenom kadru (shot, kamera, slobodan zid, broj segmenata) i po delovima reela koje je kupac dozvolio (hook/middle/end).
- Tehnike: ~20 HTML/GSAP preko snimka (+cutout iznad), ~14 "baked" numpy/OpenCV kompozitora (shatter-3d, spatial-glass, god-rays, vertigo, word-pile sa 2D fizikom...), 6 čistih overlay grafika, neki sa per-frame trackingom (digital-zoom, sticky-text, pointer-callout).
- Skoro svi traže čist cutout. Nema generatora novih efekata; očigledno su pravljeni negde drugde i uvezeni (`pack`, `imported` polja).
- SFX (19 zvukova) se **ne isporučuju** (Pixabay licenca), skidaju se iz HeyGen hyperframes repoa.

### 3.4 Stilovi po uzoru ("replicate")
- `get_example.py`: **yt-dlp** (instalira se pri prvom linku) za IG/TikTok/YT/FB/X/Pinterest/Threads..., opciono cookies iz browsera uz pristanak.
- `study.py`: frejm na 0.5 s → contact sheets; rezovi (ffmpeg scene >0.32) i medijan dužine kadra; "motion strips" (lokalni pikovi razlike frejmova); glasnoća/udari zvuka; tempo govora (reči/s, pauze). **Font i boje ne detektuje automatski, to Claude "vidi" sa slika.**
- Stil = folder `styles/<slug>/` sa `style.json` (šta build čita) i `style.md` (beleške za Claude-a, sa "Standing notes"). Komande: list/show/save/new/default/rename/duplicate/retire (nikad brisanje).
- `side_by_side.py`: primer gore, naš render dole, za proveru.

### 3.5 Trial reels varijacije
- N verzija istog reela, svaka menja **jednu** stvar: hook (drugi take, preskok filler reči, punch-in, dodat efekat, novi naslov), titlove, efekte ili stil.
- Anti-duplikat sloj: svaka dobija svoju brzinu (0.965–1.035, pitch očuvan), reframe (zoom 3.5–7% + pomeraj), lagani grade; nikad dve iste. Mirror samo ako nema čitljivog teksta u kadru. Fingerprint odbacuje identične.
- Render jedan po jedan (lock fajl), "posted" verzije zaključane zauvek.

### 3.6 Objavljivanje
- **Zernio API** (`zernio.com/api/v1`): connect URL za naloge, presign upload, `POST /posts` sa idempotency ključem, raspored, IG trial reels (`trialParams.graduationStrategy`), TikTok privacy podešavanja, YT title/category. Ključ u `posting/zernio.env` (0600), nikad kao argument.
- Signup ide preko **affiliate linka autora** (dodatni prihod).
- Ništa ne ide bez `--yes` i eksplicitnog "da" kupca na tačan plan.

### 3.7 Studio Picker
- Lokalni HTTP server (127.0.0.1:4747), stranica sa preview klipom na svakoj kartici; bira overall stil ili titlove + efekte (tagovani Hook/Explain/Proof/CTA) i po delu reela. Čuva `studio-picks.json`. Sam se gasi kad se tab zatvori.

### 3.8 Karuseli (drugi skill)
- Tok: handle + look (iz screenshotova ili 8 ugrađenih) → Claude piše copy po slajdu → **čeka odobrenje** → `carousel.json` → render → IG preview stranica sa swipe-om.
- Render: jedna HTML stranica po slajdu → **headless Chrome `--screenshot`** (browser koji je HyperFrames već skinuo), 1080x1440 default (3:4), 4:5, 1:1; PDF za LinkedIn.
- `fit.js`: automatsko uklapanje teksta (širenje/skupljanje, izbegavanje lica, provera preklapanja), vraća QA beleške.
- Look = `look.json` (CSS varijable, fontovi) + `look.css` nad fiksnim DOM ugovorom; ~27 vrsta "stikera" (iPhone UI, polaroid, rukom crtano).
- Slike: OpenAI / Gemini / fal.ai (bring-your-own key), sa procenom cene pre generisanja. "Iz videa": koristi transkript i čiste frejmove iz Studio projekta.

## 4. Spoljne zavisnosti i licence (proveriti pre gradnje)

| Komponenta | Uloga | Napomena |
|---|---|---|
| HyperFrames `hyperframes@0.8.34` (HeyGen) | HTML→MP4 renderer, background removal, browser | **Srce sistema. Proveriti licencu i stabilnost API-ja**; alternativa Remotion (ima komercijalnu licencu za firme) ili sopstveni Playwright + ffmpeg |
| GSAP 3.14 | animacije | besplatan, ali licenca ima ograničenja |
| faster-whisper (MIT) + Whisper `.en` modeli | transkripcija | za srpski treba multijezički model (`large-v3`/`turbo`) |
| RobustVideoMatting | čist cutout | **GPL-3.0**: oprez ako prodajemo zatvoren kod |
| ffmpeg static, Node 22, python-build-standalone | runtime | OK |
| yt-dlp | primeri | OK, ali skidanje tuđih rilsova je siva zona prema ToS mreža |
| Pixabay SFX | zvukovi | ne smeju se redistribuirati |
| Zernio | objavljivanje | plaćeno po nalogu posle 2 besplatna |
| Google Fonts (OFL) | fontovi | OK |

## 5. Šta je stvarno teško (gde je vrednost)

1. **Promptovi i pravila** (SKILL.md 384 linije + 11 reference fajlova): precedencija stilova, pravila rezanja, pravila označavanja reči, šta kupcu reći i kako. Ovo je 50% proizvoda i ne može se kopirati, mora se napisati iz sopstvenog iskustva montaže.
2. **Caption engine sa 20 stilova** i layout iz siluete: veliki, ali razumljiv posao.
3. **46 efekata**: najskuplji deo (najveći fajlovi 500–1200 linija numpy/OpenCV). Za MVP nije potreban.
4. **Cross-platform bootstrap** (Win/Mac Intel/M, bez ičeg instaliranog) i CI na čistim mašinama: dosadno ali kritično za kupce koji nisu tehnički.
5. **Samokontrola preko contact sheet-ova**: jednostavna ideja, velika razlika u kvalitetu.

## 6. Plan: balkanska verzija (izmena 23.10.2026)

Vladimir ima dozvolu autora da napravi verziju za Balkan na osnovu ovog plugina. Zato plan više nije pisanje od nule nego **fork + lokalizacija**: zadržavamo arhitekturu, renderer (HyperFrames) i efekte, a menjamo jezik, fontove, tekstove i brending. To je višestruko brže.

**Dozvolu treba imati pismeno** (mejl je dovoljan), sa obimom: kod, promptovi, preview klipovi, efekti; da li smemo da prodajemo; da li se pominje original; ko održava sinhronizaciju sa njihovim update-ima. Dozvola autora ne pokriva tuđe komponente: RVM (GPL-3.0), Pixabay zvukove, HyperFrames licencu i GSAP uslove. One važe i dalje.

### 6.1 Šta konkretno mora da se menja (provereno u kodu)

**1. Transkripcija (blokira sve)**
- Svuda su zakucani engleski modeli `small.en` / `medium.en`:
  - `scripts/ingest.py:79`
  - `scripts/transcribe_cut.py:26`
  - `scripts/fx_new.py:318`
  - `scripts/study.py:250`
  - `scripts/prefetch.py:94`
  - `effects/zoom-through-cut/two_shot.py:108`
  - `carousel-studio/scripts/carousel.py:492`
- Treba multijezički model (`large-v3-turbo` ili `medium`) sa `language="sr"` (hr/bs po izboru kupca).
- Treba testirati brzinu na CPU int8 i tačnost vremena reči na srpskom.
- Spisak tipičnih grešaka Whisper-a na srpskom ide u `cutting.md`.

**2. Fontovi (svi pucaju na č ć š ž đ)**
- Proverio sam svih 58 isporučenih `.woff2` fontova.
- 57 nema srpska latinična slova; jedino InstrumentSerif-regular (karuseli) ih ima.
- Nijedan nema ćirilicu.
- Isporučeni su samo `latin` podskupovi sa Google Fonts.
- Bez ispravke, titlovi bi slova sa kvačicama crtali drugim fontom.
- Ispravka:
  - ponovo skinuti iste porodice sa `latin-ext` (i `cyrillic` gde postoji);
  - izmeniti `scripts/get_font.py:68-70`, koji uzima samo blok `latin`;
  - za porodice bez latin-ext naći zamenu.

**3. Jezička pravila u kodu (engleski spiskovi reči)**
- `engine/captions.py:108`: `WEAK` reči na kojima se red ne sme završiti (the, a, to...). Treba srpska lista: i, a, u, na, da, je, se, za, od, sa, ili, ali...
- `scripts/marks.py`: CTA posle reči "comment", brojevi kao engleske reči, `key` = reč sa velikim slovom.
  - Treba "komentariši/napiši/ukucaj" + srpski brojevi (jedan, dva, tri, sto, hiljadu).
- `scripts/variations.py:83`: `FILLERS` (so, um, okay...). Treba: e, pa, ovaj, znači, dakle, ono, mislim.
- Isto u `effects/stat-stack/build.py:68`, `effects/comment-bubble/measure.py:101` i `effects/ui-world/build.py:164`.
- Pravila za velika i mala slova u titlovima, i dužine reči: srpske reči su duže, pa treba proveriti `max_chars` po stilu.

**4. Tekstovi za kupca**
- SKILL.md i references/*.md se prevode u celosti: rečenice "What the buyer hears", setup pitanja, poruke o greškama.
- Ostaje engleski samo tamo gde Claude čita tehničke STATUS linije.
- Picker UI (`picker/index.html`, `data/*.json`, `captions/styles.json`) se prevodi.
- `whats-new.json` vodimo na srpskom.
- U karuselima treba preraditi copy pravila i `looks/*/look.md` za srpski.

**5. Brending i infrastruktura**
- Novi naziv, autor i marketplace u `.claude-plugin/marketplace.json` i `video-studio/.claude-plugin/plugin.json`.
- `scripts/update.py` proverava `raw.githubusercontent.com/tenfoldmarc/studio-plugin`. Mora da gleda **naš** repo, inače bi naši kupci dobijali njihove update-e.
- Zernio affiliate link (`references/posting.md`) treba zameniti našim ili ga ukloniti, po dogovoru sa autorom.
- Prepraviti README, portal link i email podrške.
- CI (`ci/e2e.py`) treba da pravi test klip sa srpskim govorom.

### 6.2 Redosled rada
1. Pismena dozvola + napravljen privatni GitHub repo (fork).
2. Transkripcija na srpskom + fontovi sa latin-ext. Test: jedan pravi Vladimirov snimak od početka do kraja, samo titlovi.
3. Jezička pravila (WEAK, marks, fillers) + prevod SKILL.md i references.
4. Brending, update URL, picker na srpskom, README.
5. Efekti: prolazak kroz svih 46, prevod reči u efektima, provera fontova.
6. Karuseli na srpskom.
7. Windows test + CI, pa lansiranje.

## 7. Otvorena pitanja za Vladimira
1. Da li je dozvola pismena i šta tačno pokriva (prodaja, kod, preview klipovi, ime)?
2. Pismo titlova: samo latinica, ili i ćirilica kao opcija?
3. Samo srpski ili i hrvatski/bosanski kao izbor jezika (utiče na Whisper `language` i pravila)?
4. Ime proizvoda i gde se prodaje (AI Profit Lab, poseban proizvod)?
5. Posting: zadržati Zernio ili neki drugi servis?
