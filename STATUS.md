# Status: AI Video Editor
Ažurirano: 09.11.2026.
Faza: razvoj

## Gde smo stali
- 09.11 (2): plan ubrzanja u `docs/plan-ubrzanja.md`, na merenjima. Montaža traje 15 do 35 min: pola je Claude (110 do 130 koraka, 12 do 22 slike), pola skripte. Jedini spor alat je čisti izrez (0,5 s po frejmu; 15 min za 60 s rilsa). CoreML 2x, pola rezolucije 4x brže. Kod još nije menjan.
- 09.11: verzija 1.2.1. Setup sad kupcu kaže kako stižu ažuriranja (pitanje u četu, "ažuriraj AI Video Editor"); korisnicima Claude Code-a u terminalu i kako da uključe auto-update (`/plugin` → Marketplaces → ai-video-editor → Enable auto-update). Isto u README-u. Najava za kupce: `docs/najava-1.2.0.md`. Vladimirov plugin ažuriran na 1.2.0 (08.11).
- 07.11 (3): grana spojena u main i pushovana, verzija 1.2.0 (85 efekata). Spisak za landing: `docs/efekti-za-sajt.json`.
- 07.11 (2): zelena izbačena: novi efekti su podrazumevano narandžasti (`#FF6A1A`), a u pickeru je dodat izbor boje (8 boja + svoja, `accentColor` u picks, `fxlib.apply_accent`). Svih 38 efekata izrenderovano na probnom snimku `svi 7` (osim key-rain, nema mesta iznad glave), spojeno u `~/Desktop/svi7-svi-efekti.mp4`. Efekti sad umeju na grudi kad iznad glave nema mesta.
- 07.11: 39 novih efekata (ukupno 85), rekreirani jedan na jedan po javnim demo klipovima sa justyn.ai/masterclass, sa našim kodom i našim nazivima, svi u listi i pickeru sa pregledom na Vladimirovom snimku. Verzija 1.2.0. Grana `feat/novi-efekti`, nije spojena ni pushovana. Upisano u plan rilsa: 7 efekata (`fx_add`); pun rils nije izrenderovan jer licenca nije aktivna na ovom Macu (probni projekat `~/reel-edits/efekti-proba`). Zvuk nije slušan.
- 30.10: verzija 1.1.0 (whats-new.json), da kupci dobiju ponudu za ažuriranje.
- 29.10: MP4 render na Macu sad ide na video čip (`--gpu`, u `skillenv.run_hyperframes`), sa automatskim povratkom na procesor ako ne uspe; `--no-gpu` ga isključuje. Mereno na rilsu od 30 s: procesor 136 → 43 jezgro-sekundi, 33 → 24 s, slika ista (SSIM 0,997), fajl veći (18 → ~50 MB). Manje Chrome radnika nije pomoglo. Cutout (RVM) nije meren, on verovatno najviše greje kod efekata.
- 27.10: svi preview klipovi u Pickeru zamenjeni Vladimirovim snimcima iz studija (Movies/Ai profit lab reels): 20 titlova + 9 stilova (klip 15-23-59, projekat ~/reel-edits/primeri-studio), 46 efekata (8 klipova, ~/reel-edits/efekti-studio), sa posterima (oči otvorene). Spojeno u main i pushovano 28.10. Slabiji: inside-out (nema pravog b-rolla), clone, orbit, spatial-glass, vertigo.
- AI Video Editor 1.0 radi od početka do kraja na Vladimirovom Macu: setup, preuzimanja, ingest, rez, transkript, glava u kadru, titlovi, render (14 s rils za 19 s), provere, telefonska kopija, glasnija kopija.
- Transkripcija: `scripts/speech.py`. Soniox (glavni; ključ iz ~/.config/soniox/api_key ili `speech.py key --clipboard`) i offline Whisper (small + large-v3-turbo za sr/hr/bs). Na probi: Soniox 0 grešaka, Whisper 2.
- Jezik: `engine/lang.py` (sr/hr/bs/en: slabe reči, poštapalice, poziv na akciju, brojevi), ćirilica kao opcija (`speech.py script cyrillic`), sa automatskim zamenskim fontovima za ćirilična slova.
- Ukrasni fontovi bez naših slova: Permanent Marker, Covered By Your Grace i Nothing You Could Do dobili slova u samom fontu; Elsie Swash Caps, Mrs Saint Delafield i Nanum Pen Script dobijaju samo ta slova iz sličnog fonta (engine/fonts/standins.json).
- Fontovi: 66 postojećih ponovo napravljeno sa č ć š ž đ (+ ćirilica gde postoji), 32 nova fonta (Montserrat, Unbounded, Oswald, Lora, Pacifico...).
- Prevedeno na srpski: SKILL.md (poruke kupcu), reference, poruke skripti, Picker, karuseli, README, manifesti (verzija 1.0.0).
- Zvuk: provera u LUFS, `check_cuts.py --loud` pravi kopiju na -14 LUFS.

## Sledeći korak
0. Aktivirati licencu i izrenderovati pun rils sa novim efektima (ivice, titlovi, zvuk). Landing stranica sa svih 85 efekata.
1. Ubrzanje po `docs/plan-ubrzanja.md`: prvo brži izrez (CoreML, pola rezolucije, jedan izrez za ceo rils), pa `montaza.py` (jedna komanda za celu montažu), pa automatsko popunjavanje efekata.
2. Po želji: pravi b-roll za Inside Out i Green Screen, širi kadar za Clone.
3. Test instalacije iz Claude aplikacije (repo je sada javan).
4. Ugrađeni stil "Vladsdigital" (Archivo Black + Inter, boje iz reel-animacije).

## Šta fali od Vladimira
- Odluka o redosledu ubrzanja; 2 do 3 sirova klipa za merenje pre i posle.
- Kod za aktivaciju licence (stiže na mejl) za probu u rilsu; da pogleda 39 novih primera u pickeru i presluša zvuk.
- Snimci i materijal (spisak u poslednjoj poruci u chatu).
- Pismena dozvola autora.

## Otvorena pitanja / rizici
- Kupci u Claude aplikaciji nemaju prekidač za auto-update; ažuriranje vide tek kad pokrenu plugin. Ključ `extraKnownMarketplaces` sa `"autoUpdate": true` u settings.json možda radi, ali nije potvrđeno ni testirano.
- layout.py brada: na svi 7 kaže 676, a stvarna je oko 780 do 830; agenti su ručno zaobilazili. Treba popraviti merenje.
- Odstupanja od dema: ništa preko lica (key-rain, page-roll, marked-sheet, walk-card, file-drop, plate-word, color-picker). Bez pravih logoa. wipe-set (blinds, barn, clock) i pokreti u camera-cuts nisu vidljivi u demu pa su pravljeni po nazivu. cover-build i counter-dive traže rez u slotu.
- Sačuvani picks: efekat van izbora kupca ne ulazi u rils dok ga ne štiklira.
- Efekti ne prebacuju SVOJ tekst na ćirilicu (titlovi da); ui-world limit 15 znakova nije proširen za srpski.
- RVM model je GPL-3.0; Pixabay zvuci se ne smeju deliti; proveriti licencu HyperFrames-a.
- Svaki slot efekta sada nosi 4,4 MB fontova (kopija engine/fonts).
