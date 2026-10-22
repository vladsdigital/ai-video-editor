# Status: Reel Lab
Ažurirano: 23.10.2026.
Faza: razvoj

## Gde smo stali
- Fork Creator Studio v2.6.2 (uz dozvolu autora), preimenovan u Reel Lab; update stiže iz `vladsdigital/reel-lab`.
- Novo `scripts/speech.py`: Soniox (glavni, ključ iz ~/.config/soniox/api_key ili `speech.py key --clipboard`) + offline Whisper (small / large-v3-turbo) za sr/hr/bs, `.en` modeli za engleski. Povezano u ingest, transcribe_cut, fx_new, study, prefetch, two_shot, carousel.
- check_cuts.py: glasnoća u LUFS, `--loud` pravi kopiju na -14 LUFS.
- Test na Macu: setup READY, prefetch DONE, ingest + assemble + transcribe_cut + layout rade. Soniox bez greške na srpskom, Whisper turbo 2 greške na istom isečku.
- U toku (pozadinski poslovi, možda nedovršeni): jezička pravila + ćirilica (engine/lang.py, captions/marks/variations), fontovi sa č ć š ž đ + ćirilica + novi fontovi, prevod SKILL.md/reference/poruka/README na srpski, prevod Pickera i karusela.

## Sledeći korak
1. Pregledati `git diff` posle pozadinskih poslova (da li su završeni), commitovati.
2. Završiti probni rils (scratchpad proba-reel; test.mp4 ima delove sa snimkom ekrana, koristiti samo test2.mp4): marks, init_project, build_reel, render, frames_check, check_cuts.
3. Ažurirati references/cutting.md (korak 5 LUFS; ponovna transkripcija preko `speech.py test` umesto WhisperModel).
4. Napraviti GitHub repo vladsdigital/reel-lab (javan) i push.

## Šta fali od Vladimira
- Odluka: može li repo biti javan.
- Pismena dozvola autora (mejl).
- Materijal za snimanje (lista sledi u sledećoj sesiji).

## Otvorena pitanja / rizici
- RVM model je GPL-3.0; Pixabay zvuci se ne smeju deliti; proveriti licencu HyperFrames-a.
- Soniox: vreme prve reči na samom početku snimka ponekad kasni ~0,25 s (nepotvrđeno).
