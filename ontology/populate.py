"""Tools to parse the raw Wikitext and populate the database.

Here are some pointers into Wiktionary's documentation:
- https://fr.wiktionary.org/wiki/Wiktionnaire:Liste_de_tous_les_mod%C3%A8les
- https://fr.wiktionary.org/wiki/Wiktionnaire:Liste_de_tous_les_mod%C3%A8les/Fran%C3%A7ais
- https://fr.wiktionary.org/wiki/Wiktionnaire:Liste_de_tous_les_mod%C3%A8les/Titres_de_sections
"""

import os
import re
import logging
import owlready2
import tqdm
import utils
import wikitextparser


DEFINITION_PATTERN = re.compile(r"^ *# *(\*?) *(.*)")

MODEL_TO_CLASS_MAPPING = {
    "adj": "Adjective",
    "adjectif": "Adjective",
    "adjectif démonstratif": "DemonstrativeAdjective",
    "adjectif exclamatif": "ExclamativeAdjective",
    "adjectif indéfini": "IndefiniteAdjective",
    "adjectif interrogatif": "InterrogativeAdjective",
    "adjectif numéral": "NumeralAdjective",
    "adjectif possessif": "PossessiveAdjective",
    "adjectif relatif": "RelativeAdjective",
    "adverbe": "Adverb",
    "adverbe interrogatif": "InterrogativeAdverb",
    "adverbe relatif": "RelativeAdverb",
    "article défini": "DefiniteArticle",
    "article indéfini": "IndefiniteArticle",
    "article partitif": "PartitiveArticle",
    "conjonction": "Conjunction",
    "conjonction de coordination": "CoordinatingConjunction",
    "interfixe": "Interfix",
    "interjection": "Interjection",
    "lettre": "Letter",
    "locution": "Locution",
    "locution-phrase": "Locution",
    "nom": "CommonNoun",
    "nom commun": "CommonNoun",
    "nom de famille": "FamilyName",
    "nom propre": "ProperNoun",
    "nom scientifique": "CommonNoun",
    "onomatopée": "Onomatopoeia",
    "particule": "Particle",
    "patronyme": "FamilyName",
    "phrase": "Sentence",
    "phrases": "Sentence",
    "postposition": "Postposition",
    "préfixe": "Prefix",
    "prénom": "FirstName",
    "préposition": "Preposition",
    "pronom": "Pronoun",
    "pronom démonstratif": "DemonstrativePronoun",
    "pronom indéfini": "IndefinitePronoun",
    "pronom interrogatif": "InterrogativePronoun",
    "pronom personnel": "PersonalPronoun",
    "pronom possessif": "PossessivePronoun",
    "pronom relatif": "RelativePronoun",
    "proverbe": "Proverb",
    "substantif": "CommonNoun",
    "suffixe": "Suffix",
    "symbole": "Symbol",
    "verbe": "Verb",
}

LEXICAL_ENTRY_CATEGORIES = frozenset(MODEL_TO_CLASS_MAPPING)

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


def parse_section_title(section):
    """Extract and lemmatize the category of a section title.
    """
    parsed = re.sub("=|{|}", "", section.title).lower()
    split = parsed.split("|")
    if len(split) == 1:
        return split[0].strip()
    if split[0].strip() == "s":
        return split[1].strip()
    return split[0].strip()


def clear_wikitext(text):
    """Clean a string by removing wikitext markup.
    """
    parsed = wikitextparser.parse(text)
    plain_text = ""
    try:
        plain_text = parsed.plain_text()
    except TypeError:
        pass
    return plain_text.strip()


class WikitextArticle:
    """Object representation of a parsed wikitext article.
    """

    IGNORE = {
        "références",
        "voir aussi",
        "voir",
        "variante typographique",
        "liens externes",
        "traductions",
        "sources",
        "erreur",
        "faute",
        "pesornel",  # ???
        "synonymes",  # level error
        "variante",  # level error
        "homophone", # level error
        "paronymes",  # level error
        "quasi-synonymes"  # level error
    }

    def __init__(self, title=None):
        self.title = title
        self.lexical_entries = list()
        self.anagrams = list()
        self.etymology = None
        self.pronunciation = None

    @classmethod
    def from_text(cls, title, content):
        """Instantiate a WikitextArticle object.
        """
        article = cls(title)
        for section in wikitextparser.parse(content).sections:
            if section.title is not None\
                and section.title.strip() == "{{langue|fr}}":
                for subsection in section.get_sections(level=3):
                    article.parse_section(subsection)
                break
        return article

    def to_dict(self):
        """Serialization.
        """
        return {
            "title": self.title,
            "lexical_entries": [e.to_dict() for e in self.lexical_entries],
            "anagrams": self.anagrams,
            "etymology": self.etymology,
            "pronunciation": self.pronunciation
        }

    def _parseanagrams(self, section):
        for link in section.wikilinks:
            self.anagrams.append(link.target)

    def _parseetymology(self, section):
        self.etymology = clear_wikitext(section.contents)
        # TODO: More precise parsing

    def _parse_lexical_entry(self, section):
        lexical_entry = WikitextLexicalEntry.from_section(section)
        self.lexical_entries.append(lexical_entry)

    def _parsepronunciation(self, section):
        self.pronunciation = section.contents
        # TODO: More precise parsing

    def parse_section(self, section):
        """Parse a level 3 section.
        """
        category = parse_section_title(section)
        function = {
            "anagrammes": self._parseanagrams,
            "étymologie": self._parseetymology,
            "prononciation": self._parsepronunciation
        }.get(category)
        if function is not None:
            function(section)
        elif category in LEXICAL_ENTRY_CATEGORIES:
            self._parse_lexical_entry(section)
        elif category in WikitextArticle.IGNORE:
            pass
        else:
            logging.warning(
                "This section could not be parsed: %s",
                section.title
            )


class WikitextLexicalEntry:
    """Object representation for a parsed lexical entry.
    """

    LINKS_FOLDERS = {
        "synonymes": "synonyms",
        "syn": "synonyms",
        "quasi-synonymes": "quasi_synonyms",
        "q-syn": "quasi_synonyms",
        "antonymes": "antonyms",
        "dérivés": "derivatives",
        "vocabulaire": "vocabulary",
        "voc": "vocabulary",
        "hyponymes": "hyponyms",
        "hyperonymes": "hypernyms",
        "apparentés": "related",
        "phrases": "sentences",
        "holonymes": "holonyms",
        "méronymes": "meronyms",
        "homophones": "homophones",
        "abréviations": "abreviations",
        "variantes orthographiques": "spelling_variants",
        "variantes": "variants",
        "variantes dialectales": "dialect_variants",
        "expressions": "locutions",
        "gentilés": "demonyms",
        "paronymes": "paronyms",
        "diminutifs": "diminutives",
        "augmentatifs": "augmentatives",
        "composés": "composites",
        "anciennes orthographes": "old_spellings",
        "troponymes": "troponyms",
    }

    IGNORE = {
        "notes",
        "transcriptions",
        "dérivés autres langues",
        "faux-amis",
        "translittérations",
        "voir aussi",
        "trad-trier",
        "remarque",
        "voir",
        "apparentés étymologiques",
        "traductions"
        "anagrammes",  # level error
    }

    def __init__(self):
        self.pos = None
        self.lexical_senses = list()
        self.links = dict()
        for folder in set(WikitextLexicalEntry.LINKS_FOLDERS.values()):
            self.links[folder] = list()

    @classmethod
    def from_section(cls, section):
        """Instantiate an object from the parsed section.
        """
        entry = cls()
        entry.parse_section(section)
        return entry

    def to_dict(self):
        """Serialization.
        """
        return {
            "pos": self.pos,
            "senses": [s.to_dict() for s in self.lexical_senses],
            "links": self.links
        }

    def _parse_head(self, section):
        head = section.get_sections(include_subsections=False, level=3)[0]
        templates = {
            t.name: t.arguments
            for t in head.templates
        }
        # IDEA: parse templates for gender detection, flexion info and more.
        self.pos = templates["S"][0].value
        definition, examples = None, list()
        for line in head.contents.split("\n"):
            match = DEFINITION_PATTERN.search(line)
            if match is None:
                continue
            if match.group(1) == "":
                if definition is not None:
                    self.lexical_senses.append(
                        WikitextLexicalSense.from_text(definition, examples))
                    examples = list()
                definition = match.group(2)
            else:
                examples.append(match.group(2))
        if definition is not None:
            self.lexical_senses.append(
                WikitextLexicalSense.from_text(definition, examples))

    def _parse_links(self, section, folder):
        for link in section.wikilinks:
            self.links[folder].append(link.target)

    def parse_section(self, section):
        """Parse a wikitext section.
        """
        self._parse_head(section)
        for subsection in section.get_sections(level=4):
            category = parse_section_title(subsection)
            folder = WikitextLexicalEntry.LINKS_FOLDERS.get(category)
            if folder is not None:
                self._parse_links(section, folder)
            elif category in WikitextLexicalEntry.IGNORE:
                pass
            else:
                logging.warning(
                    "This subsection could not be parsed: %s",
                    subsection.title
                )

    def get_class(self):
        """Return the ontology class name of the entry.
        """
        return MODEL_TO_CLASS_MAPPING[self.pos]


class WikitextLexicalSense:
    """Object representation for a parsed lexical sense.
    """

    def __init__(self):
        self.definition = None
        self.examples = list()

    @classmethod
    def from_text(cls, definition, examples):
        """Instantiate a WikitextLexicalSense from wikitext.
        """
        sense = cls()
        sense.parse_text(definition, examples)
        return sense

    def to_dict(self):
        """Serialization.
        """
        return {
            "definition": self.definition,
            "examples": self.examples
        }

    def parse_text(self, definition, examples):
        """Read some wikitext and set the inner attributes.
        """
        self.definition = clear_wikitext(definition)
        for example in examples:
            self.examples.append(clear_wikitext(example))
        # IDEA: parse definition templates for more info


class OntologyBuilder:
    """Wrapper for methods appending individuals to the ontology.
    """

    def __init__(self, ontology_schema):
        uri = "file://" + os.path.join(os.getcwd(), ontology_schema)
        self.ontology = owlready2.get_ontology(uri).load()
        self.existing = dict()

    def create_literal(self, title):
        """Append a flont:Literal to the ontology.
        """
        literal_name = utils.format_literal(title)
        literal = self.ontology.Literal(literal_name)
        literal.label = title
        return literal

    def create_lexical_entry(self, literal, cls):
        """Append a flont:LexicalEntry to the ontology.
        """
        entry_name_radix = "%s_%s" % (literal.name, CLASS_ABBREVIATIONS[cls])
        self.existing.setdefault(entry_name_radix, dict())
        index = len(self.existing[entry_name_radix]) + 1
        entry_name = "%s%d" % (entry_name_radix, index)
        self.existing[entry_name_radix][entry_name] = 0
        lexical_entry = self.ontology[cls](entry_name)
        lexical_entry.hasLiteral = literal
        # literal.isLiteralOf.append(lexical_entry)
        return lexical_entry

    def create_lexical_sense(self, lexical_entry, definition, examples):
        """Append a flont:LexicalSense to the ontology.
        """
        lexical_entry_name_radix = re.sub(r"\d*$", "", lexical_entry.name)
        index = self.existing[lexical_entry_name_radix][lexical_entry.name] + 1
        sense_name = "%s.%d" % (lexical_entry.name, index)
        self.existing[lexical_entry_name_radix][lexical_entry.name] += 1
        lexical_sense = self.ontology.LexicalSense(sense_name)
        lexical_sense.definition = definition
        lexical_sense.example = examples
        lexical_sense.isSenseOf = lexical_entry
        return lexical_sense


def iter_db_rows(database_filename, max_iters=None):
    """Iterate over the database rows.
    """
    with utils.get_db_cursor(database_filename) as cursor:
        if max_iters is None:
            total = cursor.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
            query = "SELECT title, content FROM entries"
        else:
            total = max_iters
            query = "SELECT title, content FROM entries LIMIT %d" % max_iters
        for row in tqdm.tqdm(cursor.execute(query), total=total):
            yield row


def populate_individuals(database_filename, ontology_schema,
                         output_filename, max_iters=None):
    """Read the database and populate the ontology with individuals.
    """
    logging.info("Populating ontology with %s", database_filename)
    builder = OntologyBuilder(ontology_schema)
    for row in iter_db_rows(database_filename, max_iters):
        article = WikitextArticle.from_text(*row)
        literal = builder.create_literal(article.title)
        for wikitext_lexical_entry in article.lexical_entries:
            ontology_lexical_entry = builder.create_lexical_entry(
                literal,
                wikitext_lexical_entry.get_class()
            )
            for wikitext_lexical_sense in wikitext_lexical_entry.lexical_senses:
                builder.create_lexical_sense(
                    ontology_lexical_entry,
                    wikitext_lexical_sense.definition,
                    wikitext_lexical_sense.examples
                )
    logging.info("Saving ontology to %s", os.path.realpath(output_filename))
    builder.ontology.save(file=output_filename, format="rdfxml")
