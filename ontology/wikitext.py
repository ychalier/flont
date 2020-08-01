"""Tools to parse the raw wikitext. Pointers to documentation:
- https://fr.wiktionary.org/wiki/Wiktionnaire:Liste_de_tous_les_mod%C3%A8les/Titres_de_sections/Liste_automatique
- https://fr.wiktionary.org/wiki/Wiktionnaire:Liste_de_tous_les_mod%C3%A8les
- https://fr.wiktionary.org/wiki/Wiktionnaire:Liste_de_tous_les_mod%C3%A8les/Fran%C3%A7ais
"""

import re
import hashlib
import slugify

TITLE_PATTERN = re.compile("^(=+) {{(.+)}}")
WIKITEXT_BRACES = re.compile(r"{{.*}}")
WIKITEXT_BRACKETS = re.compile(r"\[\[(?:.*?\|)?(.*?)\]\]")
WIKITEXT_TAG = re.compile(r"^ *# *\*?")
WIKITEXT_QUOTES = re.compile(r"'''")


MODEL_TO_ABBREVIATION_MAPPING = {
    "adj": "adj",
    "adjectif": "adj",
    "adjectif-demonstratif": "adj",
    "adjectif-exclamatif": "adj",
    "adjectif-indefini": "adj",
    "adjectif-interrogatif": "adj",
    "adjectif-numeral": "adj",
    "adjectif-possessif": "adj",
    "adjectif-relatif": "adj",
    "adverbe": "adv",
    "adverbe-interrogatif": "adv",
    "adverbe-relatif": "adv",
    "article-defini": "art",
    "article-indefini": "art",
    "article-partitif": "art",
    "conjonction": "con",
    "conjonction-de-coordination": "con",
    "interfixe": "aff",
    "interjection": "int",
    "lettre": "let",
    "locution": "sen",
    "locution-phrase": "sen",
    "nom": "nou",
    "nom-commun": "nou",
    "nom-de-famille": "nou",
    "nom-propre": "nou",
    "nom-scientifique": "nou",
    "onomatopee": "int",
    "particule": "par",
    "patronyme": "nou",
    "phrase": "sen",
    "phrases": "sen",
    "postposition": "adp",
    "prefixe": "aff",
    "prenom": "nou",
    "preposition": "adp",
    "pronom": "pro",
    "pronom-demonstratif": "pro",
    "pronom-indefini": "pro",
    "pronom-interrogatif": "pro",
    "pronom-personnel": "pro",
    "pronom-possessif": "pro",
    "pronom-relatif": "pro",
    "proverbe": "sen",
    "substantif": "nou",
    "suffixe": "aff",
    "symbole": "sym",
    "verbe": "ver",
}

MODEL_TO_CLASS_MAPPING = {
    "adj": "Adjective",
    "adjectif": "Adjective",
    "adjectif-demonstratif": "DemonstrativeAdjective",
    "adjectif-exclamatif": "ExclamativeAdjective",
    "adjectif-indefini": "IndefiniteAdjective",
    "adjectif-interrogatif": "InterrogativeAdjective",
    "adjectif-numeral": "NumeralAdjective",
    "adjectif-possessif": "PossessiveAdjective",
    "adjectif-relatif": "RelativeAdjective",
    "adverbe": "Adverb",
    "adverbe-interrogatif": "InterrogativeAdverb",
    "adverbe-relatif": "RelativeAdverb",
    "article-defini": "DefiniteArticle",
    "article-indefini": "IndefiniteArticle",
    "article-partitif": "PartitiveArticle",
    "conjonction": "Conjunction",
    "conjonction-de-coordination": "CoordinatingConjunction",
    "interfixe": "Interfix",
    "interjection": "Interjection",
    "lettre": "Letter",
    "locution": "Locution",
    "locution-phrase": "Locution",
    "nom": "CommonNoun",
    "nom-commun": "CommonNoun",
    "nom-de-famille": "FamilyName",
    "nom-propre": "ProperNoun",
    "nom-scientifique": "CommonNoun",
    "onomatopee": "Onomatopoeia",
    "particule": "Particle",
    "patronyme": "FamilyName",
    "phrase": "Sentence",
    "phrases": "Sentence",
    "postposition": "Postposition",
    "prefixe": "Prefix",
    "prenom": "FirstName",
    "preposition": "Preposition",
    "pronom": "Pronoun",
    "pronom-demonstratif": "DemonstrativePronoun",
    "pronom-indefini": "IndefinitePronoun",
    "pronom-interrogatif": "InterrogativePronoun",
    "pronom-personnel": "PersonalPronoun",
    "pronom-possessif": "PossessivePronoun",
    "pronom-relatif": "RelativePronoun",
    "proverbe": "Proverb",
    "substantif": "CommonNoun",
    "suffixe": "Suffix",
    "symbole": "Symbol",
    "verbe": "Verb",
}


def extract_table_of_content(text):
    """Parse the full text of an entry to extract its titles hierarchy.
    """
    toc = list()
    for line in text.split("\n"):
        match = TITLE_PATTERN.search(line)
        if match is not None:
            level, title = len(match.group(1)), match.group(2).strip()
            if "S|" in title or "S |" in title:
                clean_title = slugify.slugify(title.split("|")[1].strip())
            else:
                clean_title = slugify.slugify(title.split("|")[0].strip())
            toc.append((str(level), clean_title))
    return toc


def iter_sections(content, target_level):
    """Read a Wiktionary article content and iterate over sections of a given
    level.
    """
    is_recording = False
    buffer_title, buffer_content = None, list()
    for line in content.split("\n"):
        match = TITLE_PATTERN.search(line)
        if match is not None:
            level, name = len(match.group(1)), match.group(2)
            if level == target_level:
                is_recording = True
                if buffer_title is not None:
                    yield buffer_title, "\n".join(buffer_content)
                buffer_title = name
                buffer_content = list()
            elif is_recording:
                buffer_content.append(line)
        elif is_recording:
            buffer_content.append(line)
    if is_recording and buffer_title is not None:
        yield buffer_title, "\n".join(buffer_content)


def clean_wikitext(text):
    """Clean a sentence of Wikitext markups.
    """
    text = WIKITEXT_BRACES.sub("", text)
    text = WIKITEXT_BRACKETS.sub(r"\1", text)
    text = WIKITEXT_TAG.sub("", text)
    text = WIKITEXT_QUOTES.sub("", text)
    text = re.sub("''", "\"", text)
    return text.strip()


def format_entry_title(raw):
    """Format the title of an entry. Should be bijective, to conserve
    the inexistence of collisions.
    """
    digest = hashlib.md5(raw.encode("utf8")).hexdigest()[-6:]
    slug = slugify.slugify(raw).replace("-", "_")
    return "w%s.%s" % (digest, slug)


def extract_definitions(content):
    """Exract the beginning of a section, where lies the definitions and the
    examples.
    """
    lines = list()
    for line in content.split("\n"):
        if TITLE_PATTERN.search(line.strip()) is not None:
            break
        lines.append(line)
    return "\n".join(lines)
