"""Tools to parse the raw Wikitext and populate the database.

Here are some pointers into Wiktionary's documentation:
- https://fr.wiktionary.org/wiki/Wiktionnaire:Liste_de_tous_les_mod%C3%A8les
- https://fr.wiktionary.org/wiki/Wiktionnaire:Liste_de_tous_les_mod%C3%A8les/Fran%C3%A7ais
- https://fr.wiktionary.org/wiki/Wiktionnaire:Liste_de_tous_les_mod%C3%A8les/Titres_de_sections
"""

import os
import re
import logging
import slugify
import owlready2
import tqdm
import utils

TITLE_PATTERN = re.compile("^(=+) {{(.+)}}")
WIKITEXT_BRACES = re.compile(r"{{.*}}")
WIKITEXT_BRACKETS = re.compile(r"\[\[(?:.*?\|)?(.*?)\]\]")
WIKITEXT_TAG = re.compile(r"^ *# *\*?")
WIKITEXT_QUOTES = re.compile(r"'''")

CLASS_ABBREVIATIONS = {
    "Adjective": "adj",
    "DemonstrativeAdjective": "adj.dem",
    "ExclamativeAdjective": "adj.excl",
    "IndefiniteAdjective": "adj.idef",
    "InterrogativeAdjective": "adj.int",
    "NumeralAdjective": "adj.num",
    "PossessiveAdjective": "adj.poss",
    "RelativeAdjective": "adj.rel",
    "Adverb": "adv",
    "InterrogativeAdverb": "adv.int",
    "RelativeAdverb": "adv.rel",
    "Interfix": "aff.int",
    "DefiniteArticle": "art.def",
    "IndefiniteArticle": "art.idef",
    "PartitiveArticle": "art.part",
    "Conjunction": "conj",
    "CoordinatingConjunction": "conj.coo",
    "Interjection": "int",
    "Letter": "let",
    "Locution": "loc",
    "CommonNoun": "n.com",
    "FamilyName": "n.fam",
    "FirstName": "n.first",
    "ProperNoun": "n.prop",
    "Onomatopoeia": "ono",
    "Particle": "part",
    "Postposition": "postp",
    "Prefix": "pref",
    "Preposition": "prep",
    "Pronoun": "pron",
    "DemonstrativePronoun": "pron.dem",
    "IndefinitePronoun": "pron.idef",
    "InterrogativePronoun": "pron.int",
    "PersonalPronoun": "pron.pers",
    "PossessivePronoun": "pron.poss",
    "RelativePronoun": "pron.rel",
    "Proverb": "prov",
    "Sentence": "sent",
    "Suffix": "suff",
    "Symbol": "sym",
    "Verb": "v",
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
    level (determined by the number of '=' signs around the section title).
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


def iter_db_rows(database_filename):
    """Iterate over the database rows.
    """
    with utils.get_db_cursor(database_filename) as cursor:
        total = cursor.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        for entry_title, entry_content in tqdm.tqdm(
                cursor.execute("SELECT title, content FROM entries"),
                total=total):
            yield entry_title, entry_content


def extract_french_section(wikitext):
    """Extract the content of the section titled {{langue|fr}}.
    """
    for title, content in iter_sections(wikitext, 2):
        if title == "langue|fr":
            return content
    return None


def create_literal(ontology, title):
    """Append a flont:Literal to the ontology.
    """
    literal_name = utils.format_literal(title)
    literal = ontology.Literal(literal_name)
    literal.label = title
    return literal


def iter_lexical_entries(wikitext):
    """Iterate over the various syntactic occurrences of a literal.
    """
    for title, content in iter_sections(wikitext, 3):
        model = slugify.slugify(title.split("|")[1].strip())
        class_ = MODEL_TO_CLASS_MAPPING.get(model)
        if class_ is not None:
            yield class_, content


def create_lexical_entry(ontology, existing, literal, class_):
    """Append a flont:LexicalEntry to the ontology.
    """
    entry_name_radix = "%s_%s" % (literal.name, CLASS_ABBREVIATIONS[class_])
    existing.setdefault(entry_name_radix, dict())
    index = len(existing[entry_name_radix]) + 1
    entry_name = "%s%d" % (entry_name_radix, index)
    existing[entry_name_radix][entry_name] = 0
    lexical_entry = ontology[class_](entry_name)
    lexical_entry.hasLiteral = literal
    # literal.isLiteralOf.append(lexical_entry)
    return lexical_entry


def extract_senses_section(wikitext):
    """Extract the content of a lexical entry section.
    """
    lines = list()
    for line in wikitext.split("\n"):
        if TITLE_PATTERN.search(line.strip()) is not None:
            break
        lines.append(line)
    return "\n".join(lines)


def iter_lexical_senses(wikitext):
    """Iterate over the definitions listed under a lexical entry.
    """
    definition, examples = None, list()
    for row in wikitext.split("\n"):
        if row.strip().startswith("#*"):
            examples.append(re.sub(r"^#\* *", "", row.strip()))
        elif row.strip().startswith("#"):
            if definition is not None:
                yield definition, examples[:]
                examples = list()
            definition = re.sub(r"^# *", "", row.strip())
    if definition is not None:
        yield definition, examples[:]


def create_lexical_sense(ontology, existing, lexical_entry, definition, examples):
    """Append a flont:LexicalSense to the ontology.
    """
    lexical_entry_name_radix = re.sub(r"\d*$", "", lexical_entry.name)
    index = existing[lexical_entry_name_radix][lexical_entry.name] + 1
    sense_name = "%s.%d" % (lexical_entry.name, index)
    existing[lexical_entry_name_radix][lexical_entry.name] += 1
    lexical_sense = ontology.LexicalSense(sense_name)
    lexical_sense.definition = definition
    lexical_sense.examples = examples
    lexical_sense.isSenseOf = lexical_entry
    return lexical_sense


def populate_individuals(database_filename, ontology_schema, output_filename):
    """Read the database and populate the ontology with individuals.
    """
    logging.info("Populating ontology with %s", database_filename)
    ontology = owlready2\
        .get_ontology("file://" + os.path.join(os.getcwd(), ontology_schema))\
        .load()
    existing = dict()
    for entry_title, entry_content in iter_db_rows(database_filename):
        literal = create_literal(ontology, entry_title)
        for class_, content in iter_lexical_entries(extract_french_section(entry_content)):
            lexical_entry = create_lexical_entry(
                ontology, existing, literal, class_)
            for definition, examples in iter_lexical_senses(extract_senses_section(content)):
                create_lexical_sense(ontology, existing,
                                     lexical_entry, definition, examples)
    logging.info("Saving ontology to %s", os.path.realpath(output_filename))
    ontology.save(file=output_filename, format="rdfxml")
