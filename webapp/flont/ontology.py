"""Ressources for ontology interation.
"""

import re
from django.urls import reverse
import wikitextparser
import flont.apps


FLONT_IRI = "https://ontology.chalier.fr/flont#"


POS_LABEL_FR = {
    "adj": "Adjectif",
    "adjDem": "Adjectif",
    "adjExcl": "Adjectif",
    "adjIdef": "Adjectif",
    "adjInt": "Adjectif",
    "adjNum": "Adjectif",
    "adjPoss": "Adjectif",
    "adjRel": "Adjectif",
    "adv": "Adverbe",
    "advInt": "Adverbe",
    "advRel": "Adverbe",
    "affInt": "Interfixe",
    "artDef": "Article",
    "artIdef": "Article",
    "artPart": "Article",
    "conj": "Conjonction",
    "conjCoo": "Conjonction",
    "int": "Interjection",
    "let": "Lettre",
    "loc": "Locution",
    "nCom": "Nom",
    "nFam": "Nom propre",
    "nFirst": "Nom propre",
    "nProp": "Nom propre",
    "ono": "Onomatopée",
    "part": "Particule",
    "postp": "Postposition",
    "pref": "Préfixe",
    "prep": "Préposition",
    "pron": "Pronom",
    "pronDem": "Pronom",
    "pronIdef": "Pronom",
    "pronInt": "Pronom",
    "pronPers": "Pronom",
    "pronPoss": "Pronom",
    "pronRel": "Pronom",
    "prov": "Proverbe",
    "sent": "Phrase",
    "suff": "Suffixe",
    "sym": "Symbole",
    "v": "Verbe",
}


INFLECTION_LABEL_FR = {
    "hasFeminine": "féminin",
    "hasPlural": "pluriel",
    "hasFemininePlural": "féminin pluriel",
    "hasMasculinePlural": "masculin pluriel",
    "imperativePresent1P": "1<sup>ère</sup> personne du pluriel de l'impératif présent",
    "imperativePresent2P": "2<sup>ème</sup> personne du pluriel de l'impératif présent",
    "imperativePresent2S": "2<sup>ème</sup> personne du singulier de l'impératif présent",
    "imperativePresent2SPostposed": "2<sup>ème</sup> personne du singulier de l'impératif présent",
    "indicativeImperfect1P": "1<sup>ère</sup> personne du pluriel de l'indicatif imparfait",
    "indicativeImperfect1S": "1<sup>ère</sup> personne du singulier de l'indicatif imparfait",
    "indicativeImperfect2P": "2<sup>ème</sup> personne du pluriel de l'indicatif imparfait",
    "indicativeImperfect2S": "2<sup>ème</sup> personne du singulier de l'indicatif imparfait",
    "indicativeImperfect3P": "3<sup>ème</sup> personne du pluriel de l'indicatif imparfait",
    "indicativeImperfect3S": "3<sup>ème</sup> personne du singulier de l'indicatif imparfait",
    "indicativePresent1P": "1<sup>ère</sup> personne du pluriel de l'indicatif présent",
    "indicativePresent1S": "1<sup>ère</sup> personne du singulier de l'indicatif présent",
    "indicativePresent2P": "2<sup>ème</sup> personne du pluriel de l'indicatif présent",
    "indicativePresent2S": "2<sup>ème</sup> personne du singulier de l'indicatif présent",
    "indicativePresent3P": "3<sup>ème</sup> personne du pluriel de l'indicatif présent",
    "indicativePresent3S": "3<sup>ème</sup> personne du singulier de l'indicatif présent",
    "indicativeSimpleFuture1P": "1<sup>ère</sup> personne du pluriel de l'indicatif futur",
    "indicativeSimpleFuture1S": "1<sup>ère</sup> personne du singulier de l'indicatif futur",
    "indicativeSimpleFuture2P": "2<sup>ème</sup> personne du pluriel de l'indicatif futur",
    "indicativeSimpleFuture2S": "2<sup>ème</sup> personne du singulier de l'indicatif futur",
    "indicativeSimpleFuture3P": "3<sup>ème</sup> personne du pluriel de l'indicatif futur",
    "indicativeSimpleFuture3S": "3<sup>ème</sup> personne du singulier de l'indicatif futur",
    "indicativeSimplePast1P": "1<sup>ère</sup> personne du pluriel du passé simple de l'indicatif",
    "indicativeSimplePast1S":
        "1<sup>ère</sup> personne du singulier du passé simple de l'indicatif",
    "indicativeSimplePast2P": "2<sup>ème</sup> personne du pluriel du passé simple de l'indicatif",
    "indicativeSimplePast2S":
        "2<sup>ème</sup> personne du singulier du passé simple de l'indicatif",
    "indicativeSimplePast3P": "3<sup>ème</sup> personne du pluriel du passé simple de l'indicatif",
    "indicativeSimplePast3S":
        "3<sup>ème</sup> personne du singulier du passé simple de l'indicatif",
    "pastParticipleFP": "participe passé féminin pluriel",
    "pastParticipleFS": "participe passé féminin singulier",
    "pastParticipleMP": "participe passé masculin pluriel",
    "pastParticipleMS": "participe passé masculin singulier",
    "presentParticiple": "participe présent",
    "subjonctiveImperfect1P": "1<sup>ère</sup> personne du pluriel du subjonctif imparfait",
    "subjonctiveImperfect1S": "1<sup>ère</sup> personne du singulier du subjonctif imparfait",
    "subjonctiveImperfect2P": "2<sup>ème</sup> personne du pluriel du subjonctif imparfait",
    "subjonctiveImperfect2S": "2<sup>ème</sup> personne du singulier du subjonctif imparfait",
    "subjonctiveImperfect3P": "3<sup>ème</sup> personne du pluriel du subjonctif imparfait",
    "subjonctiveImperfect3S": "3<sup>ème</sup> personne du singulier du subjonctif imparfait",
    "subjonctivePresent1P": "1<sup>ère</sup> personne du pluriel du subjonctif présent",
    "subjonctivePresent1S": "1<sup>ère</sup> personne du singulier du subjonctif présent",
    "subjonctivePresent2P": "2<sup>ème</sup> personne du pluriel du subjonctif présent",
    "subjonctivePresent2S": "2<sup>ème</sup> personne du singulier du subjonctif présent",
    "subjonctivePresent3P": "3<sup>ème</sup> personne du pluriel du subjonctif présent",
    "subjonctivePresent3S": "3<sup>ème</sup> personne du singulier du subjonctif présent",
    "conditionalPresent1P": "1<sup>ère</sup> personne du pluriel du conditionnel présent",
    "conditionalPresent1S": "1<sup>ère</sup> personne du singulier du conditionnel présent",
    "conditionalPresent2P": "2<sup>ème</sup> personne du pluriel du conditionnel présent",
    "conditionalPresent2S": "2<sup>ème</sup> personne du singulier du conditionnel présent",
    "conditionalPresent3P": "3<sup>ème</sup> personne du pluriel du conditionnel présent",
    "conditionalPresent3S": "3<sup>ème</sup> personne du singulier du conditionnel présent",
}

GENDER_LABEL_FR = {
    "flont:masculine": "masculin",
    "flont:feminine": "féminin",
}

LINK_LABEL_FR = {
    "hasDerivative": "Dérivés",
    "hasDerivedLocution": "Proverbes",
    "hasDerivedPhrase": "Phrases dérivées",
    "hasDerivedWord": "Mots dérivés",
    "isComponentOf": "Composés",
    "hasRelative": "Apparentés",
    "hasRelatedVocabulary": "Vocabulaire apparenté",
    "hasRelatedWord": "Mots apparentés",
    "hasDemonym": "Gentilés",
    "hasAugmentative": "Augmentatifs",
    "hasDiminutive": "Diminutifs",
    "hasHolonym": "Holonymes",
    "hasMeronym": "Méronymes",
    "isAntonymOf": "Antonymes",
    "isQuasiSynonymOf": "Quasi-synonymes",
    "isSynonymOf": "Synonymes",
    "hasHypernym": "Hyperonymes",
    "hasHyponym": "Hyponymes",
    "hasTroponym": "Troponymes",
    "hasVariant": "Variantes",
    "hasAbbreviation": "Abréviation",
    "hasDialectVariant": "Variantes dialectales",
    "hasOldSpelling": "Anciennes ortographes",
    "hasSpellingVariant": "Autres ortographes",
    "isAnagramOf": "Anagrammes",
    "hasHomophone": "Homophones",
    "isParonymOf": "Paronymes",
}


def roman_numeral(num):
    """Convert an integer into a string representing its writing in roman
    numerals.
    """
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    sym = ["M", "CM", "D", "CD", "C", "XC",
           "L", "XL", "X", "IX", "V", "IV", "I"]
    roman_num = ""
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += sym[i]
            num -= val[i]
        i += 1
    return roman_num


def format_wikilinks(string):
    """Format WikiText links for HTML.
    """
    pattern = re.compile(r"\[\[(.+?)(\#.*?)?(\|.+?)?\]\]")

    def replacer(match):
        base = reverse("flont:search")
        query = re.sub(" ", "+", match.group(1))
        label = match.group(1)
        if match.group(3) is not None:
            label = match.group(3)[1:]
        return """<a href="%s?q=%s">%s</a>""" % (base, query, label)
    return pattern.sub(replacer, string)


def format_wikitemplates(string):
    """Format WikiText templates for HTML.
    """
    pattern = re.compile(r"{{(.+?)(\|.+?)?}}")

    def replacer(match):
        if match.group(1).lower() == "w":
            name = match.group(2)[1:].split("|")[0].strip()
            url = re.sub(" ", "_", name)
            return """<a class="external" href="https://fr.wikipedia.org/wiki/%s">%s</a>"""\
                % (url, name)
        if match.group(1).lower() == "lien":
            base = reverse("flont:search")
            label = match.group(2)[1:].split("|")[0].strip()
            query = re.sub(" ", "+", label)
            return """<a href="%s?q=%s">%s</a>""" % (base, query, label)
        return ""
    return pattern.sub(replacer, string)


def get_iri(node):
    """Extract the short IRI of an ontology node.
    """
    return str(node).replace(FLONT_IRI, "flont:")


def find_literal_by_label(label):
    """Find a literal by its label within the ontology.
    """
    query = """
    PREFIX flont: <https://ontology.chalier.fr/flont#>
    SELECT ?literal WHERE {
        ?literal flont:label "%s" .
    }
    LIMIT 1""" % label
    results = list(flont.apps.graph.query(query))
    if len(results) == 0:
        return None
    return results[0][0]


def retrieve_literal_info(node):
    """Create a Literal object from a Literal ontology node.
    """
    literal = Literal(node)
    literal.fetch_data_properties()
    literal.fetch_entries()
    return literal


class Literal:
    """Representation of a Literal node.
    """

    def __init__(self, node):
        self.node = node
        self.iri = get_iri(node)
        self.label = None
        self.pronunciation = None
        self.entries = list()
        self.inflections = dict()

    def fetch_data_properties(self):
        """Fetch the label and the pronunciation from the ontology.
        """
        self._fecth_label()
        self._fecth_pronunciation()
        self._fetch_inflections()

    def fetch_entries(self):
        """Fetch the lexical entries from the ontology.
        """
        query = """
        PREFIX flont: <https://ontology.chalier.fr/flont#>
        SELECT ?entry
        WHERE {
            %s flont:isLiteralOf ?entry .
        }
        """ % self.node.n3()
        for (entry,) in flont.apps.graph.query(query):
            lexical_entry = LexicalEntry(self, entry)
            lexical_entry.fetch_gender()
            lexical_entry.fetch_inflections()
            lexical_entry.fetch_links()
            if len(lexical_entry.inflections) == 0:
                lexical_entry.fetch_senses()
            self.entries.append(lexical_entry)

    def _fecth_label(self):
        self.label = flont.apps.ontology[str(
            self.node).replace(FLONT_IRI, "")].label

    def _fecth_pronunciation(self):
        query = """
        PREFIX flont: <https://ontology.chalier.fr/flont#>
        SELECT ?pronunciation
        WHERE {
            %s flont:pronunciation ?pronunciation .
        }
        LIMIT 1
        """ % self.node.n3()
        results = list(flont.apps.graph.query(query))
        if len(results) == 1:
            self.pronunciation = results[0][0]

    def _fetch_inflections(self):
        query = """
        PREFIX flont: <https://ontology.chalier.fr/flont#>
        SELECT ?relation ?label
        WHERE {
            %s ?relation ?entry .
            ?relation rdfs:subPropertyOf* flont:hasInflection .
            ?entry flont:hasLiteral ?literal .
            ?literal flont:label ?label .
        }
        """ % self.node.n3()
        for relation, label in flont.apps.graph.query(query):
            relation_label = INFLECTION_LABEL_FR[get_iri(relation).replace("flont:", "")]
            self.inflections[relation_label] = label

    def get_inflections(self):
        """Only return relevant inflections.
        """
        if len({"féminin pluriel", "masculin pluriel"}.intersection(self.inflections)) == 0:
            whitelist = {"féminin", "pluriel"}
        else:
            whitelist = {"féminin", "féminin pluriel", "masculin pluriel"}
        return [
            (relation, self.inflections[relation])
            for relation in sorted(whitelist.intersection(self.inflections))
        ]


class LexicalEntry:  # pylint: disable=R0902
    """Representation of a LexicalEntry node.
    """

    def __init__(self, literal, node):
        self.literal = literal
        self.node = node
        self.iri = get_iri(node)
        self.pos = re.sub(r"\d", "", self.iri.split("_")[-1])
        self.gender = None
        self.senses = list()
        self.inflections = list()
        self.links = dict()

    def fetch_gender(self):
        """Fetch the gender from the ontology.
        """
        query = """
        PREFIX flont: <https://ontology.chalier.fr/flont#>
        SELECT ?gender
        WHERE {
            %s flont:hasGender ?gender .
        }
        LIMIT 1""" % self.node.n3()
        results = list(flont.apps.graph.query(query))
        if len(results) == 1:
            self.gender = get_iri(results[0][0])

    def fetch_senses(self):
        """Fetch the lexical senses from the ontology.
        """
        query = """
        PREFIX flont: <https://ontology.chalier.fr/flont#>
        SELECT ?sense
        WHERE {
            %s flont:hasSense ?sense .
        }
        """ % self.node.n3()
        for (sense,) in flont.apps.graph.query(query):
            lexical_sense = LexicalSense(self, sense)
            lexical_sense.fetch_definition()
            self.senses.append(lexical_sense)

    def fetch_inflections(self):
        """Fetch the inflections where the entry is the inflected form.
        """
        query = """
        PREFIX flont: <https://ontology.chalier.fr/flont#>
        SELECT ?label ?relation
        WHERE {
            ?literal ?relation %s .
            ?relation rdfs:subPropertyOf* flont:hasInflection .
            ?literal flont:label ?label .
        }
        """ % self.node.n3()
        has_mp_or_fp = set()
        has_p = set()
        for label, relation in flont.apps.graph.query(query):
            relation_label = INFLECTION_LABEL_FR[get_iri(
                relation).replace("flont:", "")]
            self.inflections.append((label, relation_label))
            if relation_label in {"féminin pluriel", "masculin pluriel"}:
                has_mp_or_fp.add(label)
            elif relation_label == "pluriel":
                has_p.add(label)
        for label in has_p.intersection(has_mp_or_fp):
            self.inflections.remove((label, "pluriel"))

    def fetch_links(self):
        """Fetch the general links (synonymy, etc.).
        """
        query = """
        PREFIX flont: <https://ontology.chalier.fr/flont#>
        SELECT ?label ?relation
        WHERE {
            %s ?relation ?literal .
            ?relation rdfs:subPropertyOf* flont:isLinkedTo .
            ?literal flont:label ?label .
        }
        """ % self.node.n3()
        for label, relation in flont.apps.graph.query(query):
            relation_label = LINK_LABEL_FR[get_iri(
                relation).replace("flont:", "")]
            self.links.setdefault(relation_label, set())
            self.links[relation_label].add(label)

    def pos_label(self):
        """Entry POS formatting without indexing.
        """
        label = POS_LABEL_FR[self.pos]
        if label == "Nom" and self.gender is not None:
            return "Nom %s" % GENDER_LABEL_FR[self.gender]
        return label

    def format_pos(self):
        """Entry POS formatting with indexing.
        """
        self_label = self.pos_label()
        index, total = None, 0
        for other_entry in self.literal.entries:
            other_entry_label = other_entry.pos_label()
            if other_entry_label == self_label:
                total += 1
            if other_entry.iri == self.iri:
                index = total
        if total == 1:
            return self_label
        return "%s (%s)" % (self_label, roman_numeral(index).lower())


class LexicalSense:
    """Representation of a LexicalSense node.
    """

    def __init__(self, entry, node):
        self.entry = entry
        self.node = node
        self.iri = get_iri(node)
        self.definition = None

    def fetch_definition(self):
        """Fetch the definition from the ontology.
        """
        query = """
        PREFIX flont: <https://ontology.chalier.fr/flont#>
        SELECT ?definition
        WHERE {
            %s flont:definition ?definition .
        }
        LIMIT 1""" % self.node.n3()
        results = list(flont.apps.graph.query(query))
        if len(results) == 1:
            if not results[0][0].strip().startswith("#*"):
                self.definition = re.sub("^#*", "", results[0][0].strip())
        if len(self.format_definition()) == 0:
            self.definition = None

    def format_definition(self):
        """Output clean HTML format of the definition.
        """
        if self.definition is None:
            return ""
        base_cleaning = wikitextparser.parse(self.definition).plain_text(
            replace_wikilinks=False,
            replace_templates=False
        )
        links_cleaning = format_wikilinks(base_cleaning)
        templates_cleaning = format_wikitemplates(links_cleaning)
        return re.sub("(  +)", "", templates_cleaning).strip()
