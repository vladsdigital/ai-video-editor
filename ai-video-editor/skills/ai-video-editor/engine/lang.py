#!/usr/bin/env python3
"""AI Video Editor language data: every word list a caption / mark / trial heuristic needs, per language, plus the
Serbian Latin -> Cyrillic transliteration used when config.json "script" is "cyrillic".

Languages: 'sr', 'hr', 'bs' share one set of lists (Serbian ekavian and Croatian / Bosnian ijekavian forms are both
in it, so a reel in any of the three is read the same way); 'en' is the English set the skill shipped with,
unchanged.

    import lang
    L = lang.lang_data('sr')          # {'weak', 'pronouns', 'fillers', 'cta_strong', 'cta_weak', 'cta_skip', ...}
    lang.current()                    # {'language': 'sr', 'script': 'latin' | 'cyrillic'} (never raises)
    lang.transliterate('Ljubav, ChatGPT i AI', 'cyrillic')   -> 'Љубав, ChatGPT и AI'
    lang.cta_targets([w['text'] for w in words], L)          -> indices of the comment keywords

Standard library only. This file is also copied into every effect slot by scripts/fx_new.py, together with a
lang.json that holds the language and script, so an effect's build.py can `import lang` from its own folder.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = {'language': 'sr', 'script': 'latin'}

# ---------------------------------------------------------------------------------------------------------------
# English: the lists the skill shipped with (captions.py WEAK / PRONOUNS, marks.py, variations.py, the effects)
# ---------------------------------------------------------------------------------------------------------------
EN = dict(
    weak={'the', 'a', 'an', 'to', 'of', 'and', 'that', 'for', 'can', 'in', 'on', 'with', 'is', 'my', 'your', 'then'},
    pronouns={'i', 'you', 'we', 'he', 'she', 'they', 'it'},
    fillers={'so', 'now', 'okay', 'ok', 'um', 'uh', 'alright', 'well', 'and', 'but', 'look', 'hey', 'yeah', 'like',
             'right', 'listen', 'basically', 'actually', 'honestly'},
    # "one" is left out: it is usually not a number
    numbers={'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen',
             'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty', 'thirty', 'forty',
             'fifty', 'sixty', 'seventy', 'eighty', 'ninety', 'hundred', 'thousand', 'million', 'billion', 'zero',
             'double', 'triple', 'half'},
    cta_strong={'comment'},           # the next word (after cta_skip words) is the keyword
    cta_weak=set(),                   # ... only when it is in quotes / capitals, or a cta_noun came between
    cta_skip={'the', 'word', 'a', 'below', 'down', 'this', 'just', 'me', 'with'},
    cta_nouns={'word'},
    cta_label='comment',              # the small label over the keyword when nothing was said before it
    send={'send'},                    # comment-bubble: the reply lands on this word ("... and I'll send you ...")
    not_names={'i', "i'm", "i'll", "i've", "i'd", 'ok', 'okay'},
)

# ---------------------------------------------------------------------------------------------------------------
# Serbian / Croatian / Bosnian
# ---------------------------------------------------------------------------------------------------------------
# A caption line must not end on these (a dangling conjunction, preposition, clitic, auxiliary or determiner).
_SH_WEAK = {
    # conjunctions and particles
    'i', 'a', 'ili', 'ali', 'pa', 'te', 'ni', 'niti', 'da', 'li', 'ako', 'kad', 'kada', 'dok', 'jer', 'nego', 'već',
    'što', 'šta', 'sto', 'kao', 'no', 'ne', 'kako', 'koji', 'koja', 'koje', 'kojeg', 'kojem', 'kojoj', 'čiji', 'čija',
    'gde', 'gdje', 'čim', 'iako', 'mada', 'premda',
    # prepositions
    'u', 'na', 'za', 'od', 'sa', 's', 'po', 'do', 'iz', 'o', 'uz', 'bez', 'kroz', 'pri', 'prema', 'k', 'ka', 'nad',
    'pod', 'pred', 'među', 'preko', 'zbog', 'kod', 'oko', 'iza', 'ispred', 'umesto', 'umjesto', 'osim', 'protiv',
    # clitics and auxiliaries ("sam", "je", "će" lean on the next word in speech)
    'je', 'se', 'si', 'sam', 'smo', 'ste', 'su', 'će', 'ću', 'ćeš', 'ćemo', 'ćete', 'bi', 'bih', 'bismo', 'biste',
    'mi', 'ti', 'me', 'mu', 'ga', 'joj', 'im', 'ih', 'nas', 'vas', 'ju',
    # determiners and possessives (they belong to the noun after them)
    'taj', 'ta', 'to', 'tog', 'tom', 'tu', 'ti', 'te', 'ovaj', 'ova', 'ovo', 'ovog', 'ovom', 'ovu', 'ovi', 'ove',
    'onaj', 'onog', 'onu', 'neki', 'neka', 'neko', 'neku', 'svaki', 'svaka', 'svako', 'svaku', 'ceo', 'cijeli', 'cela',
    'cijela', 'moj', 'moja', 'moje', 'moju', 'mog', 'tvoj', 'tvoja', 'tvoje', 'tvoju', 'tvog', 'svoj', 'svoja',
    'svoje', 'svoju', 'svog', 'njegov', 'njegova', 'njegovo', 'njegovu', 'njen', 'njena', 'njeno', 'njezin',
    'njezina', 'naš', 'naša', 'naše', 'našu', 'vaš', 'vaša', 'vaše', 'vašu', 'njihov', 'njihova', 'njihovo',
    'vrlo', 'jako', 'baš', 'samo', 'još', 'čak', 'tako', 'toliko',
}
# Personal pronouns: a number never "counts" across one ("3 stvari ja ..." stops before "ja").
_SH_PRONOUNS = {'ja', 'ti', 'on', 'ona', 'ono', 'mi', 'vi', 'oni', 'one', 'meni', 'tebi', 'njemu', 'njoj', 'nama',
                'vama', 'njima', 'mene', 'tebe', 'njega', 'nje', 'njih'}
# Spoken fillers a take often starts with (a trial reel may start straight on the word after one).
_SH_FILLERS = {'e', 'ee', 'eee', 'em', 'hm', 'mhm', 'ovaj', 'znači', 'dakle', 'pa', 'ono', 'mislim', 'evo', 'ajde',
               'hajde', 'dobro', 'okej', 'ok', 'oke', 'eto', 'kao', 'jel', 'jelda', 'ustvari', 'u stvari', 'naime',
               'inače', 'gledaj', 'gledajte', 'slušaj', 'slušajte', 'znaš', 'znate', 'vidi', 'vidite', 'e pa', 'ma',
               'elem', 'zapravo'}
# Cardinal number words, common inflected forms. "jedan / jedna / jedno" are left out, like English "one": they are
# usually an article ("jedan alat"), not a number. Ordinals (prvi, drugi, treći) are left out too: "prvi put" is not
# a number worth showing big.
_SH_NUMBERS = {
    'nula', 'dva', 'dve', 'dvije', 'dvoje', 'dvojica', 'tri', 'troje', 'trojica', 'četiri', 'četvoro', 'pet', 'petoro',
    'šest', 'sedam', 'osam', 'devet', 'deset', 'jedanaest', 'dvanaest', 'trinaest', 'četrnaest', 'petnaest',
    'šesnaest', 'sedamnaest', 'osamnaest', 'devetnaest', 'dvadeset', 'trideset', 'četrdeset', 'pedeset', 'šezdeset',
    'sedamdeset', 'osamdeset', 'devedeset', 'sto', 'stotinu', 'stotine', 'stotina', 'dvesta', 'dvjesto', 'dvjesta',
    'tristo', 'trista', 'četiristo', 'petsto', 'šeststo', 'sedamsto', 'osamsto', 'devetsto', 'hiljadu', 'hiljada',
    'hiljade', 'tisuću', 'tisuća', 'tisuće', 'milion', 'miliona', 'milione', 'milioni', 'milijun', 'milijuna',
    'milijune', 'milijarda', 'milijardu', 'milijarde', 'milijardi', 'pola', 'polovina', 'duplo', 'dvostruko',
    'trostruko', 'dupla',
}
# "komentariši ŠABLON": after a strong verb the next real word is the keyword.
_SH_CTA_STRONG = {'komentariši', 'komentarišite', 'komentarišeš', 'komentarišete', 'komentiraj', 'komentirajte',
                  'komentiraš', 'komentirate', 'komentarisi', 'komentarisite', 'comment'}
# Generic verbs ("napiši", "pošalji", "ostavi") only lead to a keyword when it is quoted or in capitals, or when
# "reč / riječ / komentar" came between: "pošalji mi poruku" must not mark "poruku".
_SH_CTA_WEAK = {'napiši', 'napišite', 'napišeš', 'napišete', 'piši', 'pišite', 'ukucaj', 'ukucajte', 'ukucaš',
                'ukucate', 'upiši', 'upišite', 'upišeš', 'upišete', 'pošalji', 'pošaljite', 'pošalješ', 'pošaljete',
                'javi', 'javite', 'javiš', 'javite', 'ostavi', 'ostavite', 'ostaviš', 'ostavite', 'stavi', 'stavite',
                'staviš', 'kucaj', 'kucajte', 'napisi', 'napisite', 'posalji', 'posaljite'}
_SH_CTA_SKIP = {'ispod', 'dole', 'dolje', 'reč', 'riječ', 'rijec', 'rec', 'rečju', 'riječju', 'reči', 'riječi', 'mi',
                'nam', 'u', 'komentar', 'komentaru', 'komentarima', 'komentare', 'samo', 'je', 'jednu', 'jedno',
                'ovde', 'ovdje', 'tu', 'the', 'word', 'below', 'odmah', 'slobodno', 'sad', 'sada', 'poruku', 'dm',
                'direktno', 'privatno', 'inbox', 'kao', 'mi je'}
_SH_CTA_NOUNS = {'reč', 'riječ', 'rijec', 'rec', 'rečju', 'riječju', 'komentar', 'komentaru', 'komentarima',
                 'komentare', 'word'}

SH = dict(
    weak=_SH_WEAK,
    pronouns=_SH_PRONOUNS,
    fillers=_SH_FILLERS,
    numbers=_SH_NUMBERS,
    cta_strong=_SH_CTA_STRONG,
    cta_weak=_SH_CTA_WEAK,
    cta_skip=_SH_CTA_SKIP,
    cta_nouns=_SH_CTA_NOUNS,
    cta_label='komentariši',
    send={'pošalji', 'pošaljem', 'poslaću', 'poslat', 'pošaljemo', 'šaljem', 'šaljemo', 'stiže', 'dobiješ',
          'dobijaš', 'dobit', 'dobićeš', 'send'},
    not_names={'ok', 'okej', 'oke'},
)
SH_HR = dict(SH, cta_label='komentiraj')

DATA = {'en': EN, 'sr': SH, 'bs': SH, 'hr': SH_HR}


def lang_data(language=None):
    """The word lists for a language ('sr', 'hr', 'bs', 'en'); anything else gets Serbian."""
    if language is None:
        language = current()['language']
    return DATA.get(str(language).lower(), SH)


def current():
    """{'language', 'script'} for this machine. In an effect slot: the lang.json fx_new.py wrote next to this file.
    In the skill: config.json via scripts/speech.py. Never raises: anything wrong gives Serbian in Latin."""
    try:
        side = os.path.join(HERE, 'lang.json')
        if os.path.isfile(side):
            with open(side, encoding='utf-8') as fh:
                got = json.load(fh)
        else:
            import sys
            scripts = os.path.join(os.path.dirname(HERE), 'scripts')
            if scripts not in sys.path:
                sys.path.insert(0, scripts)
            import speech
            got = speech.settings()
        language = str(got.get('language') or DEFAULT['language']).lower()
        script = 'cyrillic' if str(got.get('script') or '').lower().startswith('cyr') else 'latin'
        return {'language': language if language in DATA else DEFAULT['language'], 'script': script}
    except Exception:          # noqa: BLE001: a broken config must never stop a build
        return dict(DEFAULT)


_PUNCT = '.,;:!?"“”„«»\'’‘()[]…–—-'


def norm(text):
    """a word as the lists hold it: lowercase, no surrounding punctuation or quotes"""
    return str(text).strip().strip(_PUNCT).lower()


def is_number_word(text, data):
    return norm(text) in data['numbers']


def is_cta_verb(text, data):
    t = norm(text)
    return t in data['cta_strong'] or t in data['cta_weak']


def cta_targets(texts, data, reach=4):
    """Indices of comment keywords in a list of word texts: the first word after a CTA verb that is not a skip
    word ("komentariši reč ŠABLON", "napiši mi u komentaru VODIČ", "comment the word GUIDE"), at most `reach` skip
    words away and never across the end of a sentence. After a weak verb the keyword must be quoted, in capitals, or
    come after reč / riječ / komentar."""
    out = []
    low = [norm(t) for t in texts]
    for i, n in enumerate(low):
        strong, weak = n in data['cta_strong'], n in data['cta_weak']
        if not (strong or weak) or str(texts[i]).rstrip()[-1:] in '.?!':
            continue
        j, noun = i + 1, False
        while j < len(low) and j - i <= reach and (low[j] in data['cta_skip'] or not low[j]):
            noun = noun or low[j] in data['cta_nouns']
            if str(texts[j]).rstrip()[-1:] in '.?!':
                j = len(low)
                break
            j += 1
        if j >= len(low) or not low[j] or low[j] in data['cta_skip']:
            continue
        if low[j] in data['cta_strong'] or low[j] in data['cta_weak'] or low[j] in data['weak']:
            continue
        raw = str(texts[j]).strip()
        core = raw.strip(_PUNCT)
        quoted = raw[:1] in '"“„«\'‘'
        caps = len(core) > 1 and core.isupper()
        if strong or noun or quoted or caps:
            if j not in out:
                out.append(j)
    return out


# ---------------------------------------------------------------------------------------------------------------
# Latin -> Cyrillic (Serbian; display only: words.json always stays in Latin)
# ---------------------------------------------------------------------------------------------------------------
_ONE = dict(zip('abvgdđežzijklmnoprstćufhcčš', 'абвгдђежзијклмнопрстћуфхцчш'))
_TWO = {'lj': 'љ', 'nj': 'њ', 'dž': 'џ'}
# Words where the two letters are two sounds, not one: (stem the word starts with, the pair inside it).
# nad-/pod-/pred- + ž... (nadživeti, podžupan, predželudac), od- + žal/živ (odžaliti, odživeti; but odžak = оџак),
# in-/kon- + j... (injekcija, konjunkcija, konjugacija).
_SPLIT = [('nadž', 'dž'), ('podž', 'dž'), ('predž', 'dž'), ('odžal', 'dž'), ('odživ', 'dž'), ('injek', 'nj'),
          ('konjunk', 'nj'), ('konjug', 'nj'), ('injunk', 'nj')]
# Names and brands that stay in Latin in Cyrillic text (compared case-insensitively). Add a reel's own with
# plan.json "keep_latin": ["Acme", ...].
KEEP_LATIN = {'claude', 'chatgpt', 'gpt', 'openai', 'anthropic', 'instagram', 'tiktok', 'youtube', 'facebook', 'meta',
              'google', 'gemini', 'whatsapp', 'viber', 'telegram', 'linkedin', 'twitter', 'reel', 'reels', 'reel lab',
              'canva', 'capcut', 'notion', 'figma', 'cursor', 'midjourney', 'soniox', 'whisper', 'iphone', 'ipad',
              'android', 'apple', 'microsoft', 'excel', 'word', 'powerpoint', 'shopify', 'zoom', 'netflix', 'spotify',
              'stripe', 'paypal', 'gmail', 'chrome', 'safari', 'mac', 'macbook', 'windows', 'ios', 'saas', 'ok'}
# All-caps tokens that are acronyms (kept in Latin). Any other all-caps word is transliterated ("KURS" -> "КУРС"),
# because the caption styles upper-case ordinary words for display.
ACRONYMS = {'ai', 'gpt', 'ceo', 'cto', 'coo', 'cfo', 'seo', 'pdf', 'url', 'api', 'cta', 'dm', 'ugc', 'roi', 'kpi',
            'usb', 'tv', 'pr', 'b2b', 'b2c', 'crm', 'ux', 'ui', 'pc', 'mvp', 'faq', 'asap', 'it', 'hr', 'llm', 'gif',
            'html', 'css', 'sql', 'app', 'ads', 'vip', 'diy', 'qr', 'nft', 'pos', 'pov', 'fyi', 'ppc', 'cpm', 'cpc',
            'sms', 'nlp', 'saas', 'smm', 'gpu', 'cpu', 'ram', 'ssd', 'mp3', 'mp4', 'ok', 'id'}
_URL = re.compile(r'^(https?://|www\.)|^[\w.-]+\.(com|rs|hr|ba|me|io|ai|net|org|co|app|dev|eu)(/\S*)?$', re.I)
_CAMEL = re.compile(r'[a-zšđčćž][A-Z]')
_WORD = re.compile(r"[A-Za-zŠĐČĆŽšđčćž]+(?:['’][A-Za-zŠĐČĆŽšđčćž]+)*")


def _convert(word):
    """one plain Latin word -> Cyrillic, digraphs and their exceptions included"""
    lw = word.lower()
    split = set()
    for stem, pair in _SPLIT:
        if lw.startswith(stem):
            split.add(stem.find(pair))
    out, i = [], 0
    while i < len(word):
        two = lw[i:i + 2]
        if two in _TWO and i not in split:
            cyr = _TWO[two]
            out.append(cyr.upper() if word[i].isupper() else cyr)
            i += 2
            continue
        ch = word[i]
        cyr = _ONE.get(ch.lower())
        out.append(ch if cyr is None else (cyr.upper() if ch.isupper() else cyr))
        i += 1
    return ''.join(out)


def _keep_word(core, keep):
    lw = core.lower()
    if lw in keep:
        return True
    if re.search(r'[qwxy]', lw) or _CAMEL.search(core):
        return True                       # a foreign word or a brand written CamelCase (YouTube, ChatGPT, iPhone)
    if core.isupper() and len(core) > 1 and lw in ACRONYMS:
        return True
    return False


def _token(tok, keep):
    """one whitespace-free token: URLs, handles, hashtags and anything with a digit stay as they are; the rest is
    split into letter runs, each converted unless it is kept"""
    if not tok or tok[:1] in '@#' or _URL.search(tok.strip('.,;:!?()"“”„')) or re.search(r'\d', tok):
        return tok
    lw = tok.lower()
    for k in keep:                        # "Instagramu", "Claude-a": a kept name with an ending
        if lw.startswith(k) and len(k) >= 3:
            rest = tok[len(k):]
            if not rest or not rest[:1].isalpha():
                return tok[:len(k)] + _token(rest, keep) if rest else tok
            if len(k) >= 5 and rest.islower() and len(rest) <= 3:
                return tok                # "Instagramu", "Claudeom": stays in Latin as one word (not "meta" -> "metak")
    return _WORD.sub(lambda m: m.group() if _keep_word(m.group(), keep) else _convert(m.group()), tok)


def transliterate(text, script='cyrillic', keep=()):
    """Serbian Latin -> Cyrillic for display. script 'latin' returns the text unchanged. Left in Latin: URLs,
    @handles, #hashtags, tokens with digits, words with q / w / x / y, CamelCase brands, known acronyms in capitals
    (ACRONYMS), KEEP_LATIN and `keep` (case-insensitive; "AI Video Editor" style phrases work too). Text that is already
    Cyrillic passes through unchanged."""
    if script != 'cyrillic' or not text:
        return text
    keep_set = {k.lower() for k in KEEP_LATIN} | {str(k).lower() for k in (keep or ()) if k}
    phrases = sorted((k for k in keep_set if ' ' in k), key=len, reverse=True)
    words = {k for k in keep_set if ' ' not in k}
    text = str(text)
    if phrases:                           # protect multi-word names first
        pat = re.compile('|'.join(re.escape(p) for p in phrases), re.I)
        parts, last = [], 0
        for m in pat.finditer(text):
            parts.append(transliterate(text[last:m.start()], script, words))
            parts.append(m.group())
            last = m.end()
        if parts:
            parts.append(transliterate(text[last:], script, words))
            return ''.join(parts)
    return re.sub(r'\S+', lambda m: _token(m.group(), words), text)
