"""Ressources for ontology interaction.
"""

from django.urls import reverse
import rdflib
import flont.apps
import flont.wikitext


FLONT_IRI = "https://ontology.chalier.fr/flont#"


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


def shorten_iri(uri_ref_):
    """Convert a full IRI to a prefix IRI.
    """
    uri_ref = str(uri_ref_)
    registry = {
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf:",
        "http://www.w3.org/2000/01/rdf-schema#": "rdfs:",
        "http://www.w3.org/2002/07/owl#": "owl:",
        FLONT_IRI: "flont:",
    }
    text = str(uri_ref)
    for full, pref in registry.items():
        text = text.replace(full, pref)
    return text


def get_meta_information(node):
    """Retrieve meta information about an IRI.
    """
    return MetaInformation.from_node(node)


def find_literal_by_label(label):
    """Find a literal by its label within the ontology.
    """
    query = """
    PREFIX flont: <%s>
    SELECT ?literal WHERE {
        ?literal flont:label "%s" .
    }
    LIMIT 1""" % (FLONT_IRI, label)
    results = list(flont.apps.graph.query(query))
    if len(results) == 0:
        return None
    return results[0][0]


def retrieve_literal_info(node):
    """Create a Literal object from a Literal ontology node.
    """
    return Literal.from_node(node)


def retrieve_lexical_entry_info(node):
    """Retrieve a single lexical entry object.
    """
    return LexicalEntry.from_node(node, None)


def retrieve_lexical_sense_info(node):
    """Retrieve a single lexical sense object.
    """
    return LexicalSense.from_node(node, None)


class LabeledEntity:
    """IRI with a human-readable label.
    """

    def __init__(self, full_iri, label=""):
        self.full_iri = str(full_iri)
        if isinstance(label, str):
            self.label = label
        else:
            self.label = label.toPython()

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


class InflectionTable:
    """Wrapper for grouping inflections under a category.
    """

    def __init__(self, title):
        self.title = title
        self.rows = dict()
        self.ordering = list()
        self._setup_rows()

    def _append_row(self, key):
        self.rows[key] = None
        self.ordering.append(key)

    def _setup_rows(self):
        raise NotImplementedError()

    def __iter__(self):
        for key in self.ordering:
            value = self.rows[key]
            if value is not None:
                yield key, value

    def any(self):
        """Return True if at least one raw as a non-null value.
        """
        return any(self.rows.values())

    def inflate(self, inflections):
        """Populate the row values from a dict of inflections.
        """
        for key in self.ordering:
            self.rows[key] = inflections.get(key)
        return self


class AdjectiveAgreementTable(InflectionTable):
    """Inflection table for adjectives and like.
    """

    def __init__(self):
        InflectionTable.__init__(self, LabelFetcher.from_iri("hasAgreement"))

    def _setup_rows(self):
        self._append_row(LabelFetcher.from_iri("hasFeminine"))
        self._append_row(LabelFetcher.from_iri("hasMasculinePlural"))
        self._append_row(LabelFetcher.from_iri("hasFemininePlural"))


class NounAgreementTable(InflectionTable):
    """Inflection table for nouns.
    """

    def __init__(self):
        InflectionTable.__init__(self, LabelFetcher.from_iri("hasAgreement"))

    def _setup_rows(self):
        self._append_row(LabelFetcher.from_iri("hasPlural"))


class ConjugationTable(InflectionTable):
    """Inflection table for verbs.
    """

    TENSES = [
        "indicativePresent",
        "indicativeImperfect",
        "indicativeSimplePast",
        "indicativeSimpleFuture",
        "subjonctivePresent",
        "subjonctiveImperfect",
        "conditionalPresent",
        "imperativePresent",
        "pastParticiple",
        "presentParticiple"
    ]

    def __init__(self, tense):
        self.tense = LabelFetcher.from_iri(tense)
        InflectionTable.__init__(self, self.tense)

    def _setup_rows(self):
        if self.tense.full_iri.endswith("presentParticiple"):
            self._append_row(LabeledEntity(self.tense.full_iri, "inv."))
        elif self.tense.full_iri.endswith("pastParticiple"):
            self._append_row(LabeledEntity(self.tense.full_iri + "MS", "il"))
            self._append_row(LabeledEntity(self.tense.full_iri + "FS", "elle"))
            self._append_row(LabeledEntity(self.tense.full_iri + "MP", "ils"))
            self._append_row(LabeledEntity(
                self.tense.full_iri + "FP", "elles"))
        else:
            self._append_row(LabeledEntity(self.tense.full_iri + "1S", "je"))
            self._append_row(LabeledEntity(self.tense.full_iri + "2S", "tu"))
            self._append_row(LabeledEntity(self.tense.full_iri + "3S", "il"))
            self._append_row(LabeledEntity(self.tense.full_iri + "1P", "nous"))
            self._append_row(LabeledEntity(self.tense.full_iri + "2P", "vous"))
            self._append_row(LabeledEntity(self.tense.full_iri + "3P", "ils"))


def format_limit(lim):
    """Format the 'LIMIT' keyword line for SPARQL queries.
    """
    if lim is None:
        return ""
    return "\nLIMIT %d" % lim


class OntologyObject:
    """Wrapper for common utilities for fetching attributes from the ontology.
    """

    def __init__(self, node):
        self.node = node
        self.iri = LabeledEntity(node, shorten_iri(node))

    def fetch(self):
        """Inflate the object attributes with data fetched from the ontology.
        """
        raise NotImplementedError()

    @classmethod
    def from_node(cls, node, *args):
        """Create the object from a RDFLib node.
        """
        obj = cls(node, *args)
        obj.fetch()
        return obj

    @classmethod
    def from_iri(cls, iri, *args):
        """Create the object from its IRI.
        """
        if FLONT_IRI in iri:
            node = rdflib.URIRef(iri)
        else:
            node = rdflib.URIRef(FLONT_IRI + iri)
        return cls.from_node(node, *args)

    def _query(self, query):
        formatted = "PREFIX flont: <%s>\n%s" % (
            FLONT_IRI,
            query % {"iri": self.node.n3()}
        )
        return flont.apps.graph.query(formatted)

    def _query_ppty(self, ppty, lim=None):
        results = self._query("""
        SELECT ?o
        WHERE {
            %%(iri)s %s ?o .
        }%s
        """ % (ppty, format_limit(lim)))
        if lim == 1:
            if len(list(results)) == 1:
                return list(results)[0][0]
            return None
        return results

    def _query_ppty_label(self, ppty, lim=None, lbl_ppty="rdfs:label",
                          o_constraint=""):
        results = self._query("""
        SELECT ?o ?ol
        WHERE {
            %%(iri)s %s ?o .
            %s
            ?o %s ?ol .
        }%s
        """ % (ppty, o_constraint, lbl_ppty, format_limit(lim)))
        if lim == 1:
            if len(list(results)) == 1:
                return list(results)[0]
            return None
        return results


class LabelFetcher(OntologyObject, LabeledEntity):
    """Auto label fetcher.
    """

    def __init__(self, node):
        OntologyObject.__init__(self, node)
        LabeledEntity.__init__(self, str(node))

    def fetch(self):
        self.label = self._query_ppty("rdfs:label", lim=1)


class MetaInformation(OntologyObject):
    """Meta information about an IRI.
    """

    def __init__(self, node):
        OntologyObject.__init__(self, node)
        self.edges = list()

    def fetch(self):
        """Fetch triples where the given IRI occurs.
        """
        results = self._query("""
        SELECT ?property ?object
        WHERE {
            %(iri)s ?property ?object .
        }
        """)
        for ppty_node, obj_node in results:
            ppty = LabeledEntity(str(ppty_node), shorten_iri(ppty_node))
            obj = LabeledEntity(str(obj_node), shorten_iri(obj_node))
            self.edges.append((self.iri, ppty, obj))
        for ppty_name in ["subClassOf", "subPropertyOf", "range", "domain"]:
            results = self._query("""
            SELECT ?subject
            WHERE {
                ?subject rdfs:%s %%(iri)s .
            }
            """ % ppty_name)
            for (subj_node,) in results:
                ppty = LabeledEntity(
                    "http://www.w3.org/2000/01/rdf-schema#%s" % ppty_name,
                    "rdfs:%s" % ppty_name
                )
                subj = LabeledEntity(str(subj_node), shorten_iri(subj_node))
                self.edges.append((subj, ppty, self.iri))


class Literal(OntologyObject):
    """Representation of a Literal node.
    """

    def __init__(self, node):
        OntologyObject.__init__(self, node)
        self.label = None
        self.entries = list()
        self.pronunciation = None
        self.etymology = None
        self.anagrams = list()
        self.inflections = {
            NounAgreementTable: list(),
            AdjectiveAgreementTable: list(),
            ConjugationTable: list(),
        }

    def fetch(self):
        self._fecth_label()
        self._fecth_etymology()
        self._fetch_anagrams()
        self._fetch_inflections()
        self._fetch_entries()

    def _fetch_entries(self):
        for (node,) in self._query_ppty("flont:isLiteralOf"):
            self.entries.append(LexicalEntry.from_node(node, self))
        self.entries.sort(key=lambda e: e.iri)
        for i, entry in enumerate(self.entries):
            entry.index = roman_numeral(i + 1)

    def _fecth_label(self):
        self.label = self._query_ppty("flont:label", 1)

    def _fecth_etymology(self):
        wikitext = self._query_ppty("flont:etymology", 1)
        if wikitext is not None:
            self.etymology = flont.wikitext.WikiTextString(wikitext)

    def _fetch_inflections(self):
        results = self._query("""
        SELECT ?relation ?relationLabel ?literal ?literalLabel
        WHERE {
            %(iri)s ?relation ?entry .
            ?relation rdfs:subPropertyOf* flont:hasInflection .
            ?entry flont:hasLiteral ?literal .
            ?literal flont:label ?literalLabel .
            ?relation rdfs:label ?relationLabel .
        }
        """)
        inflections = dict()
        for relation, relation_label, literal, literal_label in results:
            inflections[LabeledEntity(relation, relation_label)] =\
                LabeledEntity(literal, literal_label)
        tables = [
            AdjectiveAgreementTable().inflate(inflections),
            NounAgreementTable().inflate(inflections)
        ] + [
            ConjugationTable(tense).inflate(inflections)
            for tense in ConjugationTable.TENSES
        ]
        for table in tables:
            if table.any():
                self.inflections[table.__class__].append(table)

    def _fetch_anagrams(self):
        for literal, label in self._query_ppty_label(
                "flont:hasAnagram",
                lbl_ppty="flont:label"):
            self.anagrams.append(LabeledEntity(literal, label))


class LexicalEntry(OntologyObject):  # pylint: disable=R0902
    """Representation of a LexicalEntry node.
    """

    def __init__(self, node, literal):
        OntologyObject.__init__(self, node)
        self.literal = literal
        self.pos = None
        self.index = None
        self.gender = None
        self.pronunciation = None
        self.senses = list()
        self.inflections = dict()
        self.links = dict()

    def fetch(self):
        self._fetch_pos()
        self._fetch_gender()
        self._fetch_inflections()
        self._fetch_links()
        self._fetch_pronunciation()
        self._fetch_senses()

    def literal_inflections(self):
        """Return the inflections of literal pushed down to the lexical entry.
        """
        short = self.pos.short_iri()
        if short == "Verb":
            return self.literal.inflections[ConjugationTable]
        if short == "CommonNoun":
            return self.literal.inflections[NounAgreementTable]
        if "Adjective" in short or "Article" in short or "Pronoun" in short:
            return self.literal.inflections[AdjectiveAgreementTable]
        return list()

    def _fetch_pos(self):
        pos = self._query_ppty_label(
            "rdf:type", lim=1,
            o_constraint="?o rdfs:subClassOf* flont:LexicalEntry .")
        if pos is not None:
            self.pos = LabeledEntity(*pos)

    def _fetch_pronunciation(self):
        self.pronunciation = self._query_ppty("flont:pronunciation", 1)

    def _fetch_gender(self):
        gender = self._query_ppty_label("flont:hasGender", 1)
        if gender is not None:
            self.gender = LabeledEntity(*gender)

    def _fetch_senses(self):
        for (node,) in self._query_ppty("flont:hasSense"):
            self.senses.append(LexicalSense.from_node(node, self))
        self.senses.sort(key=lambda s: s.iri)

    def _fetch_inflections(self):
        results = list(self._query("""
        SELECT ?relation ?relationLabel ?literal ?literalLabel
        WHERE {
            ?literal ?relation %(iri)s .
            ?relation rdfs:subPropertyOf* flont:hasInflection .
            ?literal flont:label ?literalLabel .
            ?relation rdfs:label ?relationLabel .
        }
        """))
        for relation, relation_label, literal, literal_label in results:
            self.inflections[LabeledEntity(literal, literal_label)]\
                = LabeledEntity(relation, relation_label)
        key_p = LabeledEntity(FLONT_IRI + "hasPlural")
        key_mp = LabeledEntity(FLONT_IRI + "hasMasculinePlural")
        key_fp = LabeledEntity(FLONT_IRI + "hasFemininePlural")
        if key_p in self.inflections and (key_mp in self.inflections
                                          or key_fp in self.inflections):
            del self.inflections[key_p]

    def _fetch_links(self):
        results = self._query("""
        SELECT ?literal ?literalLabel ?relation ?relationLabel
        WHERE {
            %(iri)s ?relation ?literal .
            ?relation rdfs:subPropertyOf* flont:hasLink .
            ?literal flont:label ?literalLabel .
            ?relation rdfs:label ?relationLabel .
        }
        """)
        for literal, literal_label, relation_node, relation_label in results:
            relation = LabeledEntity(relation_node, relation_label)
            self.links.setdefault(relation, list())
            self.links[relation].append(LabeledEntity(literal, literal_label))
        for relation in self.links:
            self.links[relation].sort()


class LexicalSense(OntologyObject):
    """Representation of a LexicalSense node.
    """

    def __init__(self, node, entry):
        OntologyObject.__init__(self, node)
        self.entry = entry
        self.definition = None
        self.examples = list()
        self.precisions = set()

    def fetch(self):
        self._fetch_definition()
        self._fetch_examples()

    def _fetch_precisions(self):
        for precision, label in self._query_ppty_label("flont:hasPrecision"):
            self.precisions.add(LabeledEntity(str(precision), label))

    def _fetch_definition(self):
        wikitext = self._query_ppty("flont:definition", 1)
        if wikitext is not None:
            self.definition = flont.wikitext.WikiTextString(wikitext)
        if len(self.definition.html()) == 0:
            self.definition = None
        else:
            self._fetch_precisions()

    def _fetch_examples(self):
        for (example,) in self._query_ppty("flont:example"):
            self.examples.append(example)
