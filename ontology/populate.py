"""Tools to parse the raw Wikitext and populate the database.

Here are some pointers into Wiktionary's documentation:
- https://fr.wiktionary.org/wiki/Wiktionnaire:Liste_de_tous_les_mod%C3%A8les
- https://fr.wiktionary.org/wiki/Wiktionnaire:Liste_de_tous_les_mod%C3%A8les/Fran%C3%A7ais
- https://fr.wiktionary.org/wiki/Wiktionnaire:Liste_de_tous_les_mod%C3%A8les/Titres_de_sections
"""

import os
import re
import logging
import gc
import urllib.parse
import sqlite3
import contextlib
import enum
import tqdm
import owlready2
import wikitextparser


@contextlib.contextmanager
def get_db_cursor(database_filename):
    """Context function for read-only interaction with the database.
    """
    connection = sqlite3.connect(database_filename)
    cursor = connection.cursor()
    yield cursor
    connection.close()


def iter_db_rows(database_filename, max_iters=None, desc=None):
    """Iterate over the database rows.
    """
    with get_db_cursor(database_filename) as cursor:
        if max_iters is None:
            total = cursor.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
            query = "SELECT title, content FROM entries"
        else:
            total = max_iters
            query = "SELECT title, content FROM entries LIMIT %d" % max_iters
        for row in tqdm.tqdm(cursor.execute(query), total=total, desc=desc):
            yield row


DEFINITION_PATTERN = re.compile(r"^ *(#+) *(\*?) *(.*)")


TEMPLATE_TO_RELATION_MAPPING = {
    "synonymes": "isSynonymOf",
    "syn": "isSynonymOf",
    "quasi-synonymes": "isQuasiSynonymOf",
    "q-syn": "isQuasiSynonymOf",
    "antonymes": "isAntonymOf",
    "dérivés": "hasDerivedWord",
    "phrases": "hasDerivedPhrase",
    "expressions": "hasDerivedLocution",
    "vocabulaire": "hasRelatedVocabulary",
    "voc": "hasRelatedVocabulary",
    "apparentés": "hasRelatedWord",
    "hyponymes": "hasHyponym",
    "hyperonymes": "hasHypernym",
    "holonymes": "hasHolonym",
    "méronymes": "hasMeronym",
    "homophones": "hasHomophone",
    "abréviations": "hasAbbreviation",
    "variantes orthographiques": "hasSpellingVariant",
    "variantes": "hasVariant",
    "variantes dialectales": "hasDialectVariant",
    "gentilés": "hasDemonym",
    "paronymes": "isParonymOf",
    "diminutifs": "hasDiminutive",
    "augmentatifs": "hasAugmentative",
    "composés": "isComponentOf",
    "anciennes orthographes": "hasOldSpelling",
    "troponymes": "hasTroponym",
}


TEMPLATE_TO_CLASS_MAPPING = {
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
    "locution phrase": "Locution",
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
LEXICAL_ENTRY_CATEGORIES = frozenset(TEMPLATE_TO_CLASS_MAPPING)


VERB_INFLECTION_MAPPING = {
    "ppr": "presentParticiple",
    "ppms": "pastParticipleMS",
    "ppm": "pastParticipleMS",
    "pp": "pastParticipleMS",
    "ppfs": "pastParticipleFS",
    "ppf": "pastParticipleFS",
    "ppmp": "pastParticipleMP",
    "ppfp": "pastParticipleFP",
    "ind.p.1s": "indicativePresent1S",
    "ind.p.2s": "indicativePresent2S",
    "ind.p.3s": "indicativePresent3S",
    "ind.p.1p": "indicativePresent1P",
    "ind.p.2p": "indicativePresent2P",
    "ind.p.3p": "indicativePresent3P",
    "ind.i.1s": "indicativeImperfect1S",
    "ind.i.2s": "indicativeImperfect2S",
    "ind.i.3s": "indicativeImperfect3S",
    "ind.i.1p": "indicativeImperfect1P",
    "ind.i.2p": "indicativeImperfect2P",
    "ind.i.3p": "indicativeImperfect3P",
    "ind.ps.1s": "indicativeSimplePast1S",
    "ind.ps.2s": "indicativeSimplePast2S",
    "ind.ps.3s": "indicativeSimplePast3S",
    "ind.ps.1p": "indicativeSimplePast1P",
    "ind.ps.2p": "indicativeSimplePast2P",
    "ind.ps.3p": "indicativeSimplePast3P",
    "ind.f.1s": "indicativeSimpleFuture1S",
    "ind.f.2s": "indicativeSimpleFuture2S",
    "ind.f.3s": "indicativeSimpleFuture3S",
    "ind.f.1p": "indicativeSimpleFuture1P",
    "ind.f.2p": "indicativeSimpleFuture2P",
    "ind.f.3p": "indicativeSimpleFuture3P",
    "cond.p.1s": "conditionalPresent1S",
    "cond.p.2s": "conditionalPresent2S",
    "cond.p.3s": "conditionalPresent3S",
    "cond.p.1p": "conditionalPresent1P",
    "cond.p.2p": "conditionalPresent2P",
    "cond.p.3p": "conditionalPresent3P",
    "sub.p.1s": "subjonctivePresent1S",
    "sub.p.2s": "subjonctivePresent2S",
    "sub.p.3s": "subjonctivePresent3S",
    "sub.p.1p": "subjonctivePresent1P",
    "sub.p.2p": "subjonctivePresent2P",
    "sub.p.3p": "subjonctivePresent3P",
    "sub.i.1s": "subjonctiveImperfect1S",
    "sub.i.2s": "subjonctiveImperfect2S",
    "sub.i.3s": "subjonctiveImperfect3S",
    "sub.i.1p": "subjonctiveImperfect1P",
    "sub.i.2p": "subjonctiveImperfect2P",
    "sub.i.3p": "subjonctiveImperfect3P",
    "imp.p.2s": "imperativePresent2S",
    "imp.p.1p": "imperativePresent1P",
    "imp.p.2p": "imperativePresent2P",
    "imp.p.2s.postposé": "imperativePresent2SPostposed"
}


CLASS_ABBREVIATIONS = {
    "Adjective": "adj",
    "DemonstrativeAdjective": "adjDem",
    "ExclamativeAdjective": "adjExcl",
    "IndefiniteAdjective": "adjIdef",
    "InterrogativeAdjective": "adjInt",
    "NumeralAdjective": "adjNum",
    "PossessiveAdjective": "adjPoss",
    "RelativeAdjective": "adjRel",
    "Adverb": "adv",
    "InterrogativeAdverb": "advInt",
    "RelativeAdverb": "advRel",
    "Interfix": "affInt",
    "DefiniteArticle": "artDef",
    "IndefiniteArticle": "artIdef",
    "PartitiveArticle": "artPart",
    "Conjunction": "conj",
    "CoordinatingConjunction": "conjCoo",
    "Interjection": "int",
    "Letter": "let",
    "Locution": "loc",
    "CommonNoun": "nCom",
    "FamilyName": "nFam",
    "FirstName": "nFirst",
    "ProperNoun": "nProp",
    "Onomatopoeia": "ono",
    "Particle": "part",
    "Postposition": "postp",
    "Prefix": "pref",
    "Preposition": "prep",
    "Pronoun": "pron",
    "DemonstrativePronoun": "pronDem",
    "IndefinitePronoun": "pronIdef",
    "InterrogativePronoun": "pronInt",
    "PersonalPronoun": "pronPers",
    "PossessivePronoun": "pronPoss",
    "RelativePronoun": "pronRel",
    "Proverb": "prov",
    "Sentence": "sent",
    "Suffix": "suff",
    "Symbol": "sym",
    "Verb": "v",
}


@enum.unique
class AgreementInflection(enum.Enum):
    """Types of inflection for non-verbs.
    """

    FEMININE_SINGULAR = 0
    FEMININE_PLURAL = 1
    MASCULINE_PLURAL = 2
    MASCULINE_FEMINE_PLURAL = 3
    PLURAL = 4


@enum.unique
class GrammaticalTrait(enum.Enum):
    """Types of traits for nouns.
    """

    MASCULINE = 0
    FEMINE = 1
    SINGULAR = 2
    PLURAL = 3


INFLECTION_LINK_REGEX = r"(?:(?:{l(?:ien)?\|(.*?)[\|}])|(?:\[\[(.*?)\]\]))"


AGREEMENT_INFLECTION_PATTERNS = {
    AgreementInflection.FEMININE_SINGULAR: [
        re.compile(r"[Ff]éminin(?: singulier)?[' ]*d[ue’'].*" + INFLECTION_LINK_REGEX),
        re.compile(r"Forme féminine d[e’'].*" + INFLECTION_LINK_REGEX)
    ],
    AgreementInflection.FEMININE_PLURAL: [
        re.compile(r"[Ff]éminin pluriel[' ]*d[e’'].*" + INFLECTION_LINK_REGEX)
    ],
    AgreementInflection.MASCULINE_PLURAL: [
        re.compile(r"[Mm]asculin pluriel[' ]*d[e’'].*" + INFLECTION_LINK_REGEX)
    ],
    AgreementInflection.MASCULINE_FEMINE_PLURAL: [
        re.compile(r"Masculin et féminin pluriels d[e’'].*" + INFLECTION_LINK_REGEX)
    ],
    AgreementInflection.PLURAL: [
        re.compile(r"[Pp]luriel(?:le)?(?: traditionnel)?[' ]*d[e’'].*" + INFLECTION_LINK_REGEX),
        re.compile(r"[Pp]luriel[' ]*du nom.*" + INFLECTION_LINK_REGEX),
        re.compile(r"Un des(?: deux)? pluriels d[e’'].*" + INFLECTION_LINK_REGEX)
    ]
}


def format_literal(raw):
    """Format a literal into a safe format.
    """
    return "_" + urllib.parse.quote(raw)


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

    def parse_anagrams(self, section):
        """Parse anagrams within a section. Public as it could be called from
        a lexical entry having a misplaced anagrams section.
        """
        for link in section.wikilinks:
            self.anagrams.append(link.target)

    def _parse_etymology(self, section):
        self.etymology = section.contents # clear_wikitext(section.contents)

    def _parse_lexical_entry(self, section):
        lexical_entry = WikitextLexicalEntry.from_section(self, section)
        self.lexical_entries.append(lexical_entry)

    def _parse_pronunciation(self, section):
        for template in section.templates:
            if template.name != "pron":
                continue
            argument = template.get_arg("1")
            if argument is not None:
                self.pronunciation = argument.value
            break

    def parse_section(self, section):
        """Parse a level 3 section.
        """
        category = parse_section_title(section)
        function = {
            "anagrammes": self.parse_anagrams,
            "étymologie": self._parse_etymology,
            "prononciation": self._parse_pronunciation
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
        "traductions",
        "vidéos",
        "note",
        "références",
        "liens externes",
        "anagrammes",  # level error
    }

    def __init__(self):
        self.pos = None
        self.lexical_senses = list()
        self.links = dict()
        for folder in set(TEMPLATE_TO_RELATION_MAPPING.values()):
            self.links[folder] = list()
        self.inflections = set()
        self.traits = set()
        self.pronunciation = None

    @classmethod
    def from_section(cls, literal, section):
        """Instantiate an object from the parsed section.
        """
        entry = cls()
        entry.parse_section(literal, section)
        return entry

    def to_dict(self):
        """Serialization.
        """
        return {
            "pos": self.pos,
            "senses": [s.to_dict() for s in self.lexical_senses],
            "links": self.links
        }

    def _parse_pronunciation(self, section):
        for template in section.templates:
            if template.name != "pron":
                continue
            argument = template.get_arg("1")
            if argument is not None:
                self.pronunciation = argument.value
            break

    def _parse_traits(self, head):
        for template in head.templates:
            if template.name == "m":
                self.traits.add(GrammaticalTrait.MASCULINE)
            elif template.name == "f":
                self.traits.add(GrammaticalTrait.FEMINE)
            elif template.name == "mf":
                self.traits.add(GrammaticalTrait.MASCULINE)
                self.traits.add(GrammaticalTrait.FEMINE)
            elif template.name == "p":
                self.traits.add(GrammaticalTrait.PLURAL)

    def _parse_verbal_inflections(self, head):
        templates = {
            t.name: t.arguments
            for t in head.templates
        }
        verb_template = templates.get("fr-verbe-flexion")
        if verb_template is None:
            return
        for i in range(1, len(verb_template)):
            inflection = VERB_INFLECTION_MAPPING.get(verb_template[i].name)
            if inflection is not None:
                self.inflections.add((verb_template[0].value, inflection))

    def _parse_agreement_inflections(self):
        for lexical_sense in self.lexical_senses:
            for agreement_inflection in AgreementInflection:
                for pattern in AGREEMENT_INFLECTION_PATTERNS[agreement_inflection]:
                    match = pattern.search(lexical_sense.definition)
                    if match is not None:
                        if match.group(1) is not None:
                            target = match.group(1).strip()
                        else:
                            target = match.group(2).strip().split("|")[0].split("#")[0].strip()
                        if agreement_inflection == AgreementInflection.FEMININE_SINGULAR:
                            self.inflections.add((target, "hasFeminine"))
                        elif agreement_inflection == AgreementInflection.FEMININE_PLURAL:
                            self.inflections.add((target, "hasFemininePlural"))
                        elif agreement_inflection == AgreementInflection.MASCULINE_PLURAL:
                            self.inflections.add((target, "hasMasculinePlural"))
                        elif agreement_inflection == AgreementInflection.MASCULINE_FEMINE_PLURAL:
                            self.inflections.add((target, "hasMasculinePlural"))
                            self.inflections.add((target, "hasFemininePlural"))
                        elif agreement_inflection == AgreementInflection.PLURAL:
                            self.inflections.add((target, "hasPlural"))

    def _parse_inflections(self, head):
        if "flexion" not in head.title:
            return
        if self.pos == "verbe":
            self._parse_verbal_inflections(head)
        else:
            self._parse_agreement_inflections()

    def _parse_definitions(self, head):
        definition, examples = None, list()
        for line in head.contents.split("\n"):
            match = DEFINITION_PATTERN.search(line)
            if match is None:
                continue
            if len(match.group(1)) > 1:
                # Here the definition is a sub definition, a precision,
                # which is outside of our focus.
                continue
            if match.group(2) == "":
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

    def _parse_head(self, section):
        head = section.get_sections(include_subsections=False, level=3)[0]
        self._parse_definitions(head)
        self._parse_traits(head)
        self._parse_inflections(head)
        self._parse_pronunciation(head)

    def _parse_links(self, section, folder):
        for link in section.wikilinks:
            self.links[folder].append(link.target)

    def parse_section(self, literal, section):
        """Parse a wikitext section.
        """
        self.pos = parse_section_title(section)
        self._parse_head(section)
        for subsection in section.get_sections(level=4):
            category = parse_section_title(subsection)
            folder = TEMPLATE_TO_RELATION_MAPPING.get(category)
            if folder is not None:
                self._parse_links(subsection, folder)
            elif category in WikitextLexicalEntry.IGNORE:
                pass
            elif category == "anagrammes":
                literal.parse_anagrams(subsection)
            elif category == "prononciation":
                self._parse_pronunciation(subsection)
            else:
                logging.warning(
                    "This subsection could not be parsed: %s",
                    subsection.title
                )

    def get_class(self):
        """Return the ontology class name of the entry.
        """
        return TEMPLATE_TO_CLASS_MAPPING[self.pos]


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
        self.definition = definition
        for example in examples:
            self.examples.append(clear_wikitext(example))
        # IDEA: parse definition templates for more info


class OntologyBuilder:
    """Wrapper for methods appending individuals to the ontology.
    """

    def __init__(self, ontology_schema):
        uri = "file://" + os.path.join(os.getcwd(), ontology_schema)
        self.world = owlready2.World()
        self.ontology = self.world.get_ontology(uri).load()
        self.existing = dict()
        self.memory = dict()

    def create_literal(self, article):
        """Append a flont:Literal to the ontology.
        """
        literal_name = format_literal(article.title)
        literal = self.ontology.Literal(literal_name)
        literal.label = article.title
        if article.pronunciation is not None:
            literal.pronunciation.append(article.pronunciation)
        if article.etymology is not None:
            literal.etymology = article.etymology
        self.memory[article.title] = {
            "literal": literal,
            "entries": list(),
            "wikitext": article
        }
        return literal

    def create_lexical_entry(self, title, literal, wikitext_lexical_entry):
        """Append a flont:LexicalEntry to the ontology.
        """
        cls = wikitext_lexical_entry.get_class()
        entry_name_radix = "%s_%s" % (literal.name, CLASS_ABBREVIATIONS[cls])
        self.existing.setdefault(entry_name_radix, dict())
        index = len(self.existing[entry_name_radix]) + 1
        entry_name = "%s%d" % (entry_name_radix, index)
        self.existing[entry_name_radix][entry_name] = 0
        lexical_entry = self.ontology[cls](entry_name)
        lexical_entry.hasLiteral = literal
        if wikitext_lexical_entry.pronunciation is not None:
            lexical_entry.pronunciation.append(wikitext_lexical_entry.pronunciation)
        self.memory[title]["entries"].append({
            "wikitext": wikitext_lexical_entry,
            "ontology": lexical_entry
        })
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

    def create_property_links(self, entry):
        """Create links between nodes, such as synonyms.
        """
        for folder, links in entry["wikitext"].links.items():
            for link in links:
                target_memory_elt = self.memory.get(link)
                if target_memory_elt is None:
                    continue
                getattr(entry["ontology"], folder).append(target_memory_elt["literal"])

    def create_inflection_links(self, entry):
        """Create inflection links.
        """
        for target, inflection in entry["wikitext"].inflections:
            target_memory_elt = self.memory.get(target)
            if target_memory_elt is not None:
                if inflection == "hasPlural":
                    getattr(target_memory_elt["literal"], inflection).append(entry["ontology"])
                else:
                    setattr(target_memory_elt["literal"], inflection, entry["ontology"])
            # else:
            #     logging.warning("Literal not found for inflection: %s", target)

    def create_trait_links(self, entry):
        """Create grammatical trait links.
        """
        for trait in entry["wikitext"].traits:
            if trait == GrammaticalTrait.MASCULINE:
                entry["ontology"].hasGender.append(self.ontology.masculine)
            elif trait == GrammaticalTrait.FEMINE:
                entry["ontology"].hasGender.append(self.ontology.feminine)
            elif trait == GrammaticalTrait.SINGULAR:
                entry["ontology"].hasNumber.append(self.ontology.singular)
            elif trait == GrammaticalTrait.PLURAL:
                entry["ontology"].hasNumber.append(self.ontology.plural)

    def create_anagram_links(self, memory_elt):
        """Create anagram links between literals.
        """
        for target in memory_elt["wikitext"].anagrams:
            target_memory_elt = self.memory.get(target)
            if target_memory_elt is not None:
                memory_elt["literal"].isAnagramOf.append(target_memory_elt["literal"])

    def create_links(self):
        """Create all relationships between lexical entries and literals
        in the ontology. Future work may consider fine-tuning the left hand of
        those relationships, linking lexical entries together, or even both
        sides of the relationships by linking lexical senses together.
        """
        for memory_elt in tqdm.tqdm(
                self.memory.values(), total=len(self.memory),
                desc="Inserting properties"):
            self.create_anagram_links(memory_elt)
            for entry in memory_elt["entries"]:
                self.create_property_links(entry)
                self.create_inflection_links(entry)
                self.create_trait_links(entry)

    def save(self, output_filename):
        """Save the ontology to the disk.
        """
        logging.info("Clearing memory...")
        self.existing.clear()
        self.memory.clear()
        gc.collect()
        if os.path.isfile(output_filename):
            logging.info("Deleting previous DB file %s", output_filename)
            os.remove(output_filename)
        logging.info("Saving world...")
        self.world.set_backend(filename=output_filename)
        self.world.save()


def populate_individuals(database_filename, ontology_schema,
                         output_filename, max_iters=None):
    """Read the database and populate the ontology with individuals.
    """
    logging.info("Populating ontology with %s", database_filename)
    builder = OntologyBuilder(ontology_schema)
    logging.info("Creating individuals...")
    for row in iter_db_rows(database_filename, max_iters, "Creating individuals"):
        article = WikitextArticle.from_text(*row)
        literal = builder.create_literal(article)
        for wikitext_lexical_entry in article.lexical_entries:
            ontology_lexical_entry = builder.create_lexical_entry(
                article.title,
                literal,
                wikitext_lexical_entry
            )
            for wikitext_lexical_sense in wikitext_lexical_entry.lexical_senses:
                builder.create_lexical_sense(
                    ontology_lexical_entry,
                    wikitext_lexical_sense.definition,
                    wikitext_lexical_sense.examples
                )
    logging.info("Creating relationships between entries...")
    builder.create_links()
    logging.info("Saving ontology to %s", os.path.realpath(output_filename))
    builder.save(output_filename)
    logging.info("Done populating the ontology!")
