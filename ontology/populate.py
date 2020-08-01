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


def iter_individuals(database_filename):
    """Iterator for the individual lexical entries in the database.
    """
    individuals = dict()
    for title, model, content in iter_senses(database_filename):
        class_ = MODEL_TO_CLASS_MAPPING[model]
        formatted_title = utils.format_literal(title)\
            + "."\
            + CLASS_ABBREVIATIONS[class_]
        individuals.setdefault(formatted_title, 0)
        index, definition, examples = individuals[formatted_title] + \
            1, None, list()
        for row in content.split("\n"):
            if row.strip().startswith("#*"):
                examples.append(utils.clean_wikitext(row))
            elif row.strip().startswith("#"):
                if definition is not None:
                    yield formatted_title + ".%d" % index, class_, title, definition, examples[:]
                    individuals[formatted_title] += 1
                    index += 1
                    examples = list()
                definition = utils.clean_wikitext(row.strip())
            else:
                pass
        if definition is not None:
            yield formatted_title + ".%d" % index, class_, title, definition, examples[:]
            individuals[formatted_title] += 1


def iter_senses(database_filename):
    """Iterate over the senses from within the database.
    """
    ignored_section = list()
    without_section = list()
    with utils.get_db_cursor(database_filename) as cursor:
        total = cursor.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        for row in tqdm.tqdm(cursor.execute("SELECT title, content FROM entries"), total=total):
            found_section = False
            for sec_title, sec_content in iter_sections(row[1], 2):
                found_section = True
                if sec_title == "langue|fr":
                    for subsec_title, subsec_content in iter_sections(sec_content, 3):
                        model = slugify.slugify(
                            subsec_title.split("|")[1].strip())
                        if model in MODEL_TO_CLASS_MAPPING:
                            yield row[0], model, extract_definitions(subsec_content)
                elif "langue" in sec_title.split("|"):
                    pass
                else:
                    ignored_section.append((row[0], sec_title))
            if not found_section:
                without_section.append(row[0])
        logging.info("iter_models ignored %d sections", len(ignored_section))
        logging.info("iter_models found %d entries with no section",
                     len(without_section))


def populate_individuals(database_filename, ontology_schema, output_filename):
    """Populate the ontology schema with individuals from the Wiktionary
    database, and write the result to a new file.
    """
    ontology = owlready2\
        .get_ontology("file://" + os.path.join(os.getcwd(), ontology_schema))\
        .load()
    for name, class_, label, definition, examples in iter_individuals(database_filename):
        individual = ontology[class_](name)
        individual.label = label
        individual.definition = definition
        individual.example = examples
    ontology.save(file=output_filename, format="rdfxml")
