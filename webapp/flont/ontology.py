"""Ressources for ontology interation.
"""

import re
from django.urls import reverse
import wikitextparser
import flont.apps


FLONT_IRI = "https://ontology.chalier.fr/flont#"


POS_LABEL_FR = {
    "adj": "Adjectif",
    "adjDem": "Adjectif démonstratif",
    "adjExcl": "Adjectif exclamatif",
    "adjIdef": "Adjectif indéfini",
    "adjInt": "Adjectif interrogatif",
    "adjNum": "Adjectif numéral",
    "adjPoss": "Adjectif possessif",
    "adjRel": "Adjectif relatif",
    "adv": "Adverbe",
    "advInt": "Adverbe interrogatif",
    "advRel": "Adverbe relatif",
    "affInt": "Interfixe",
    "artDef": "Article défini",
    "artIdef": "Article indéfini",
    "artPart": "Article partitif",
    "conj": "Conjonction",
    "conjCoo": "Conjonction de coordination",
    "int": "Interjection",
    "let": "Lettre",
    "loc": "Locution",
    "nCom": "Nom",
    "nFam": "Nom de famille",
    "nFirst": "Prénom",
    "nProp": "Nom propre",
    "ono": "Onomatopée",
    "part": "Particule",
    "postp": "Postposition",
    "pref": "Préfixe",
    "prep": "Préposition",
    "pron": "Pronom",
    "pronDem": "Pronom démonstratif",
    "pronIdef": "Pronom indéfini",
    "pronInt": "Pronom interrogatif",
    "pronPers": "Pronom personnel",
    "pronPoss": "Pronom possessif",
    "pronRel": "Pronom relatif",
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


def shorten_iri(uri_ref):
    """Convert a full IRI to a prefix IRI.
    """
    registry = {
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf:",
        "http://www.w3.org/2000/01/rdf-schema#": "rdfs:",
        "http://www.w3.org/2002/07/owl#": "owl:",
        "https://ontology.chalier.fr/flont#": "flont:",
    }
    text = str(uri_ref)
    for full, pref in registry.items():
        text = text.replace(full, pref)
    return text


class MetaInformation:
    """Meta information about an IRI.
    """

    def __init__(self, full_iri):
        self.full_iri = full_iri
        self.edges = list()

    def __str__(self):
        return self.full_iri

    def fetch_triples(self):
        """Fetch triples where the given IRI occurs.
        """
        this = LabeledEntity(self.full_iri, get_iri(self.full_iri))
        query = """
        SELECT ?property ?object
        WHERE {
            <%s> ?property ?object .
        }
        """ % self.full_iri
        for ppty_node, obj_node in flont.apps.graph.query(query):
            ppty = LabeledEntity(str(ppty_node), shorten_iri(ppty_node))
            obj = LabeledEntity(str(obj_node), shorten_iri(obj_node))
            self.edges.append((this, ppty, obj))
        for ppty_name in ["subClassOf", "subPropertyOf", "range", "domain"]:
            query = """SELECT ?subject WHERE { ?subject rdfs:%s <%s> . }"""\
                % (ppty_name, self.full_iri)
            for (subj_node,) in flont.apps.graph.query(query):
                ppty = LabeledEntity(
                    "http://www.w3.org/2000/01/rdf-schema#%s" % ppty_name,
                    "rdfs:%s" % ppty_name
                )
                subj = LabeledEntity(str(subj_node), shorten_iri(subj_node))
                self.edges.append((subj, ppty, this))


def get_meta_information(full_iri):
    """Retrieve meta information about an IRI.
    """
    meta = MetaInformation(full_iri)
    meta.fetch_triples()
    return meta


def format_wikilinks(string):
    """Format WikiText links for HTML.
    """
    pattern = re.compile(r"\[\[(.+?)(\#.*?)?(\|.+?)?\]\]")

    def replacer(match):
        label = match.group(1)
        base = reverse("flont:graph", kwargs={"short_iri": "_" + label.replace(" ", "_")})
        if match.group(3) is not None:
            label = match.group(3)[1:]
        return """<a class="internal" href="%s">%s</a>""" % (base, label)
    return pattern.sub(replacer, string)


def format_wikitemplates(string):
    """Format WikiText templates for HTML.
    """
    pattern = re.compile(r"{{(.+?)(\|.+?)?}}")

    def replacer(match):
        template_name = match.group(1).lower()
        arguments = list()
        if match.group(2):
            arguments = match.group(2)[1:].split("|")
        if template_name == "w":
            name = arguments[0].strip()
            url = re.sub(" ", "_", name)
            return """<a class="external" href="https://fr.wikipedia.org/wiki/%s">%s</a>"""\
                % (url, name)
        if template_name == "lien":
            label = arguments[0].strip()
            base = reverse("flont:graph", kwargs={"short_iri": "_" + label.replace(" ", "_")})
            return """<a class="internal" href="%s">%s</a>""" % (base, label)
        if template_name == "siècle":
            century = arguments[0].strip()
            return "(%s<sup>e</sup> siècle)" % century
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


def retrieve_lexical_entry_info(node):
    """Retrieve a single lexical entry object.
    """
    lexical_entry = LexicalEntry(None, node)
    lexical_entry.fetch_gender()
    lexical_entry.fetch_inflections()
    lexical_entry.fetch_links()
    lexical_entry.fetch_pronunciation()
    if len(lexical_entry.inflections) == 0:
        lexical_entry.fetch_senses()
    return lexical_entry


def retrieve_lexical_sense_info(node):
    """Retrieve a single lexical sense object.
    """
    lexical_sense = LexicalSense(None, node)
    lexical_sense.fetch_definition()
    lexical_sense.fetch_examples()
    return lexical_sense


class WikiTextString:
    """String of WikiText.
    """

    def __init__(self, raw):
        self.raw = raw.strip()

    def __str__(self):
        return self.raw

    def html(self):
        """Convert WikiText to HTML code.
        """
        base_cleaning = wikitextparser.parse(self.raw).plain_text(
            replace_wikilinks=False,
            replace_templates=False
        )
        lines_cleaning = re.sub("\n", "<br>", base_cleaning)
        links_cleaning = format_wikilinks(lines_cleaning)
        templates_cleaning = format_wikitemplates(links_cleaning)
        return re.sub("(  +)", "", templates_cleaning).strip()


class LabeledEntity:
    """IRI with a human-readable label.
    """

    def __init__(self, full_iri, label):
        self.full_iri = full_iri
        self.label = label

    def __hash__(self):
        return hash(self.full_iri)

    def __eq__(self, other):
        return self.full_iri == other.full_iri

    def __lt__(self, other):
        return self.full_iri < other.full_iri

    def short_iri(self):
        """Remove ontology prefix from full IRI.
        """
        return self.full_iri.replace(FLONT_IRI, "")

    def html(self):
        """Format entity link by guessing the class.
        """
        if self.full_iri.startswith(FLONT_IRI):
            return self.html_internal()
        if self.full_iri.startswith("http"):
            return self.html_external()
        return self.label

    def html_black(self):
        """Format entity link with the 'black' class.
        """
        return """<a class="black" href="%s">%s</a>""" % (
            reverse("flont:graph", kwargs={"short_iri": self.short_iri()}),
            self.label
        )

    def html_internal(self):
        """Format entity link with the 'internal' class.
        """
        return """<a class="internal" href="%s">%s</a>""" % (
            reverse("flont:graph", kwargs={"short_iri": self.short_iri()}),
            self.label
        )

    def html_external(self):
        """Format entity link with the 'internal' class.
        """
        return """<a class="external" href="%s">%s</a>""" % (
            self.full_iri,
            self.label
        )


CONJUGATION_TENSES = [
    LabeledEntity(FLONT_IRI + "indicativePresent", "Indicatif présent"),
    LabeledEntity(FLONT_IRI + "indicativeImperfect", "Indicatif imparfait"),
    LabeledEntity(FLONT_IRI + "indicativeSimplePast", "Passé simple"),
    LabeledEntity(FLONT_IRI + "indicativeSimpleFuture", "Future simple"),
    LabeledEntity(FLONT_IRI + "subjonctivePresent", "Subjonctif présent"),
    LabeledEntity(FLONT_IRI + "subjonctiveImperfect", "Subjonctif imparfait"),
    LabeledEntity(FLONT_IRI + "conditionalPresent", "Conditionnel"),
    LabeledEntity(FLONT_IRI + "imperativePresent", "Impératif")
]


class Conjugation:
    """Verb conjugation wrapper.
    """

    def __init__(self, tense):
        self.tense = tense
        self.first_singular = None
        self.second_singular = None
        self.third_singular = None
        self.first_plural = None
        self.second_plural = None
        self.third_plural = None

    def __iter__(self):
        prefix = self.tense.full_iri
        if self.first_singular is not None:
            yield LabeledEntity(prefix + "1S", "je"), self.first_singular
        if self.second_singular is not None:
            yield LabeledEntity(prefix + "2S", "tu"), self.second_singular
        if self.third_singular is not None:
            yield LabeledEntity(prefix + "3S", "il"), self.third_singular
        if self.first_plural is not None:
            yield LabeledEntity(prefix + "1P", "nous"), self.first_plural
        if self.second_plural is not None:
            yield LabeledEntity(prefix + "2P", "vous"), self.second_plural
        if self.third_plural is not None:
            yield LabeledEntity(prefix + "3P", "ils"), self.third_plural

    def inflate_from_literal(self, literal):
        """Fill in the attributes from the inflections of a literal.
        """
        prefix = self.tense.full_iri
        self.first_singular = literal.inflections.get(LabeledEntity(prefix + "1S", ""))
        self.second_singular = literal.inflections.get(LabeledEntity(prefix + "2S", ""))
        self.third_singular = literal.inflections.get(LabeledEntity(prefix + "3S", ""))
        self.first_plural = literal.inflections.get(LabeledEntity(prefix + "1P", ""))
        self.second_plural = literal.inflections.get(LabeledEntity(prefix + "2P", ""))
        self.third_plural = literal.inflections.get(LabeledEntity(prefix + "3P", ""))

    def is_filled(self):
        """Return True if at least one conjugation field is not None.
        """
        return any([
            getattr(self, attr) is not None
            for attr in [
                "first_singular",
                "second_singular",
                "third_singular",
                "first_plural",
                "second_plural",
                "third_plural"
            ]
        ])


class Literal:  # pylint: disable=R0902
    """Representation of a Literal node.
    """

    def __init__(self, node):
        self.node = node
        self.iri = LabeledEntity(str(node), get_iri(node))
        self.label = None
        self.pronunciation = None
        self.entries = list()
        self.inflections = dict()
        self.etymology = None
        self.anagrams = list()
        self.conjugations = list()

    def fetch_data_properties(self):
        """Fetch the label and the pronunciation from the ontology.
        """
        self._fecth_label()
        self._fecth_pronunciation()
        self._fetch_inflections()
        # self._fecth_etymology()
        self._fetch_anagrams()

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
            lexical_entry.fetch_pronunciation()
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

    def _fecth_etymology(self):
        query = """
        PREFIX flont: <https://ontology.chalier.fr/flont#>
        SELECT ?etymology
        WHERE {
            %s flont:etymology ?etymology .
        }
        LIMIT 1
        """ % self.node.n3()
        results = list(flont.apps.graph.query(query))
        if len(results) == 1:
            self.etymology = WikiTextString(results[0][0])

    def _inflate_conjugations(self):
        for tense in CONJUGATION_TENSES:
            conjugation = Conjugation(tense)
            conjugation.inflate_from_literal(self)
            if conjugation.is_filled():
                self.conjugations.append(conjugation)

    def _fetch_inflections(self):
        query = """
        PREFIX flont: <https://ontology.chalier.fr/flont#>
        SELECT ?relation ?literal ?label
        WHERE {
            %s ?relation ?entry .
            ?relation rdfs:subPropertyOf* flont:hasInflection .
            ?entry flont:hasLiteral ?literal .
            ?literal flont:label ?label .
        }
        """ % self.node.n3()
        for relation_node, literal_node, label in flont.apps.graph.query(query):
            relation_label = INFLECTION_LABEL_FR[get_iri(relation_node).replace("flont:", "")]
            relation = LabeledEntity(str(relation_node), relation_label)
            self.inflections[relation] = LabeledEntity(str(literal_node), label)
        self._inflate_conjugations()

    def _fetch_anagrams(self):
        query = """
        PREFIX flont: <https://ontology.chalier.fr/flont#>
        SELECT ?literal ?label
        WHERE {
            %s flont:isAnagramOf ?literal .
            ?literal flont:label ?label .
        }
        """ % self.node.n3()
        for literal, label in flont.apps.graph.query(query):
            self.anagrams.append(LabeledEntity(str(literal), label))

    def get_inflections(self):
        """Only return relevant inflections.
        """
        rel_fp = LabeledEntity("https://ontology.chalier.fr/flont#hasFemininePlural", "")
        rel_mp = LabeledEntity("https://ontology.chalier.fr/flont#hasMasculinePlural", "")
        rel_p = LabeledEntity("https://ontology.chalier.fr/flont#hasPlural", "")
        rel_fs = LabeledEntity("https://ontology.chalier.fr/flont#hasFeminine", "")
        if len({rel_fp, rel_mp}.intersection(self.inflections)) == 0:
            whitelist = {rel_fs, rel_p}
        else:
            whitelist = {rel_fs, rel_fp, rel_mp}
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
        self.iri = LabeledEntity(str(node), get_iri(node))
        self.pos_iri = None
        self.pos = re.sub(r"\d", "", self.iri.full_iri.split("_")[-1])
        self.gender = None
        self.senses = list()
        self.inflections = list()
        self.links = dict()
        self.pronunciation = None

    def fetch_pronunciation(self):
        """Fetch the pronunciation from the ontology.
        """
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
        query = """
        PREFIX flont: <https://ontology.chalier.fr/flont#>
        SELECT ?cls
        WHERE {
            %s rdf:type ?cls .
            ?cls rdfs:subClassOf* flont:LexicalEntry .
        }
        LIMIT 1""" % self.node.n3()
        results = list(flont.apps.graph.query(query))
        if len(results) == 1:
            self.pos_iri = str(results[0][0])

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
        SELECT ?literal ?label ?relation
        WHERE {
            ?literal ?relation %s .
            ?relation rdfs:subPropertyOf* flont:hasInflection .
            ?literal flont:label ?label .
        }
        """ % self.node.n3()
        has_mp_or_fp = set()
        has_p = set()
        for literal, label, relation_node in flont.apps.graph.query(query):
            relation_label = INFLECTION_LABEL_FR[get_iri(
                relation_node).replace("flont:", "")]
            relation = LabeledEntity(str(relation_node), relation_label)
            target = LabeledEntity(str(literal), label)
            self.inflections.append((target, relation))
            if relation_label in {"féminin pluriel", "masculin pluriel"}:
                has_mp_or_fp.add(target)
            elif relation_label == "pluriel":
                has_p.add(target)
        for target in has_p.intersection(has_mp_or_fp):
            self.inflections.remove((
                target,
                LabeledEntity(
                    "https://ontology.chalier.fr/flont#hasPlural",
                    "pluriel")
            ))

    def fetch_links(self):
        """Fetch the general links (synonymy, etc.).
        """
        query = """
        PREFIX flont: <https://ontology.chalier.fr/flont#>
        SELECT ?literal ?label ?relation
        WHERE {
            %s ?relation ?literal .
            ?relation rdfs:subPropertyOf* flont:isLinkedTo .
            ?literal flont:label ?label .
        }
        """ % self.node.n3()
        for literal, label, relation_node in flont.apps.graph.query(query):
            relation_label = LINK_LABEL_FR[get_iri(
                relation_node).replace("flont:", "")]
            relation = LabeledEntity(str(relation_node), relation_label)
            self.links.setdefault(relation, list())
            self.links[relation].append(LabeledEntity(str(literal), label))
        for relation in self.links:
            self.links[relation].sort()

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
        if self.literal is None:
            return LabeledEntity(self.pos_iri, self_label)
        index, total = None, 0
        for other_entry in self.literal.entries:
            other_entry_label = other_entry.pos_label()
            if other_entry_label == self_label:
                total += 1
            if other_entry.iri == self.iri:
                index = total
        if total == 1:
            return LabeledEntity(self.pos_iri, self_label)
        return LabeledEntity(
            self.pos_iri,
            "%s (%s)" % (self_label, roman_numeral(index).lower())
        )


class LexicalSense:
    """Representation of a LexicalSense node.
    """

    def __init__(self, entry, node):
        self.entry = entry
        self.node = node
        self.iri = LabeledEntity(str(node), get_iri(node))
        self.definition = None
        self.examples = list()
        self.precisions = set()

    def _fetch_precisions(self):
        query = """
        PREFIX flont: <https://ontology.chalier.fr/flont#>
        SELECT ?precision ?label
        WHERE {
            %s flont:hasPrecision ?precision .
            ?precision rdfs:label ?label .
        }
        """ % self.node.n3()
        for precision, label in flont.apps.graph.query(query):
            self.precisions.add(LabeledEntity(str(precision), label))

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
            self.definition = WikiTextString(results[0][0])
        if len(self.definition.html()) == 0:
            self.definition = None
        else:
            self._fetch_precisions()

    def fetch_examples(self):
        """Fetch the examples from the ontology.
        """
        query = """
        PREFIX flont: <https://ontology.chalier.fr/flont#>
        SELECT ?example
        WHERE {
            %s flont:example ?example .
        }
        """ % self.node.n3()
        for (example,) in flont.apps.graph.query(query):
            self.examples.append(example)
