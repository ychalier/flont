"""Tools for parsing Wiktionary's articles into a Python representation suited
for its integration in the ontology.
"""

import re
import logging
import wikitextparser


SECTION_TITLE_PATTERN = re.compile(r"=|{|}")
DEFINITION_PATTERN = re.compile(r"^ *(#+) *(\*?) *(.*)")
MULTIPLE_SPACES_PATTERN = re.compile("  +")
TEMPLATE_PATTERN = re.compile(r"{{(.*?)}}")
INFLECTION_LINK_REGEX = r"(?:(?:{l(?:ien)?\|(.*?)[\|}])|(?:\[\[(.*?)\]\]))"
AGREEMENT_INFLECTION_PATTERNS = {
    "isFeminineOf": [
        re.compile(
            r"[Ff]éminin(?: singulier)?[' ]*d[ue’'].*"
            + INFLECTION_LINK_REGEX),
        re.compile(
            r"Forme féminine d[e’'].*"
            + INFLECTION_LINK_REGEX)
    ],
    "isFemininePluralOf": [
        re.compile(
            r"[Ff]éminin pluriel[' ]*d[e’'].*"
            + INFLECTION_LINK_REGEX),
        re.compile(
            r"Masculin et féminin pluriels d[e’'].*"
            + INFLECTION_LINK_REGEX)
    ],
    "isMasculinePluralOf": [
        re.compile(
            r"[Mm]asculin pluriel[' ]*d[e’'].*"
            + INFLECTION_LINK_REGEX),
        re.compile(
            r"Masculin et féminin pluriels d[e’'].*"
            + INFLECTION_LINK_REGEX)
    ],
    "isPluralOf": [
        re.compile(
            r"[Pp]luriel(?:le)?(?: traditionnel)?[' ]*d[e’'].*"
            + INFLECTION_LINK_REGEX),
        re.compile(
            r"[Pp]luriel[' ]*du nom.*"
            + INFLECTION_LINK_REGEX),
        re.compile(
            r"Un des(?: deux)? pluriels d[e’'].*"
            + INFLECTION_LINK_REGEX)
    ]
}


def format_literal(raw):
    """Format a literal into a safe format. This is used to format the
    flont:Literal IRI.
    """
    return "_" + raw.replace(" ", "_")


def parse_section_title(section):
    """Extract and lemmatize the category of a section title. Notice: returned
    string is always lowercase and stripped.
    """
    parsed = SECTION_TITLE_PATTERN.sub("", section.title).lower()
    split = parsed.split("|")
    if len(split) == 1:
        return split[0].strip()
    if split[0].strip() == "s":
        return split[1].strip()
    return split[0].strip()


def extract_pronunciation(section):
    """Extract a word pronunciation from the {{pron}} template within a section.
    """
    for template in section.templates:
        if template.name != "pron":
            continue
        argument = template.get_arg("1")
        if argument is not None:
            return argument.value
        break
    return None


class OntologyIndividual:
    """Python representation of an individual in the ontology.
    """

    def __init__(self, rscmgr, cls=None):
        self.rscmgr = rscmgr
        self.cls = cls
        self.iri = None
        self._data_properties = set()
        self._object_properties = set()

    def get_data_properties(self):
        """Getter for the data properties.
        """
        return self._data_properties

    def get_object_properties(self):
        """Getter for the object properties.
        """
        return self._object_properties

    def add_data_property(self, ppty, value):
        """Add a data property to the individual. The value will be inserted
        as passed in the ontology.
        """
        self._data_properties.add((ppty, value))

    def add_object_property(self, ppty, value):
        """Add an object property to the individual. The value is a local IRI
        (i.e. without prefix) to another object.
        """
        self._object_properties.add((ppty, value))

    def _parse_links(self, ppty, section):
        """Parse wikilinks from a wikitext section and add them as object for
        an object property. The wikilink target is expected to be a literal's
        label, that is converted into the literal IRI.
        """
        for link in section.wikilinks:
            self.add_object_property(ppty, format_literal(link.target))


class SectionParser:
    """Common utilities wrapper for articles parsing. Callbacks are set by
    inheriting this class and implementing the `_parse_head` and the
    `_parse_subsection` methods.
    """

    IGNORE = set()
    SELECT = None

    def __init__(self, top_level, sub_level):
        self._top_level = top_level
        self._sub_level = sub_level

    def _parse_head(self, title, head):
        raise NotImplementedError()

    def _parse_subsection(self, subtitle, subsection):
        raise NotImplementedError()

    def parse_section(self, section):
        """Parse a top level section: first its head (piece of text below the
        section title and above the first subsection), and then all of its
        non-ignored subsections.
        """
        title = parse_section_title(section)
        head = section.get_sections(
            level=self._top_level,
            include_subsections=False
        )
        if len(head) > 0:
            self._parse_head(title, head[0])
        for subsection in section.get_sections(level=self._sub_level):
            subtitle = parse_section_title(subsection)
            if subtitle not in self.IGNORE:
                if not self._parse_subsection(subtitle, subsection):
                    logging.warning(
                        "Could not parse level %d section entitled '%s'",
                        self._sub_level,
                        subsection.title
                    )

    def parse_wikitext(self, wikitext):
        """Parse a string with wikitext markup. Check all top level sections
        until the selected one is found, and parse it.
        """
        parsed = wikitextparser.parse(wikitext)
        for section in parsed.get_sections(level=self._top_level):
            if section.title is not None\
                    and section.title.strip() == self.SELECT:
                for subsection in section.get_sections(level=self._sub_level):
                    self.parse_section(subsection)
                break


class WikitextLiteral(SectionParser, OntologyIndividual):
    """Python representation of a flont:Literal.
    """

    SELECT = "{{langue|fr}}"

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
        "pesornel",
        "synonymes",
        "variante",
        "homophone",
        "paronymes",
        "quasi-synonymes"
    }

    def __init__(self, rscmgr):
        SectionParser.__init__(self, 2, 3)
        OntologyIndividual.__init__(self, rscmgr, "Literal")
        self.entries = list()
        self.pronunciation = None

    def _parse_head(self, title, head):
        pass

    def _parse_subsection(self, subtitle, subsection):
        if subtitle == "étymologie":
            self._parse_etymology(subsection)
        elif subtitle == "anagrammes":
            self._parse_links("isAnagramOf", subsection)
        elif subtitle == "pronunciation":
            self._parse_pronunciation(subsection)
        elif subtitle in self.rscmgr.pos_templates:
            self._parse_lexical_entry(subtitle, subsection)
        else:
            return False
        return True

    def _parse_lexical_entry(self, _, subsection):
        entry = WikitextEntry.from_section(self, subsection)
        self.entries.append(entry)

    def _parse_etymology(self, section):
        self.add_data_property("etymology", section.contents.strip())

    def _parse_pronunciation(self, section):
        self.pronunciation = extract_pronunciation(section)

    def set_iri(self, title):
        """Set the literal IRI from the article title.
        """
        self.iri = format_literal(title)
        self.add_data_property("label", title)

    @classmethod
    def from_article(cls, rscmgr, article_title, article_content):
        """Create a literal from an article.
        """
        literal = cls(rscmgr)
        literal.set_iri(article_title)
        literal.parse_wikitext(article_content)
        for entry in literal.entries:
            entry.check_for_pronunciation()
            entry.set_iri()
        return literal


class WikitextEntry(SectionParser, OntologyIndividual):
    """Python representation of a flont:LexicalEntry.
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
        "anagrammes",
    }

    def __init__(self, literal):
        SectionParser.__init__(self, 3, 4)
        OntologyIndividual.__init__(self, literal.rscmgr, "LexicalEntry")
        self.literal = literal
        self.senses = list()
        self._known_pronunciation = False

    def set_iri(self):
        """Set the entry IRI and link it to its literal. The literal IRI must
        have been set before!
        """
        nth_of_type = 1
        for other in self.literal.entries:
            if self == other:
                break
            nth_of_type += 1
        self.iri = "%s_%s%d" % (
            self.literal.iri,
            self.rscmgr.pos_abbreviations[self.cls],
            nth_of_type
        )
        self.literal.add_object_property("isLiteralOf", self.iri)
        for i, sense in enumerate(self.senses):
            sense.set_iri(i)

    @classmethod
    def from_section(cls, literal, section):
        """Create an entry from a entry section.
        """
        entry = cls(literal)
        entry.parse_section(section)
        return entry

    def check_for_pronunciation(self):
        """Set the pronunciation from the literal if it is missing for the entry.
        """
        if not self._known_pronunciation and self.literal.pronunciation is not None:
            self._known_pronunciation = True
            self.add_data_property("pronunciation", self.literal.pronunciation)

    def _parse_head(self, title, head):
        self.cls = self.rscmgr.pos_templates[title]
        self._parse_pronunciation(head)
        self._parse_traits(head)
        self._parse_verbal_inflections(head)
        self._parse_senses(head)
        self._parse_sense_inflections()

    def _parse_pronunciation(self, section):
        pronunciation = extract_pronunciation(section)
        if pronunciation is not None:
            self._known_pronunciation = True
            self.add_data_property("pronunciation", pronunciation)

    def _parse_traits(self, section):
        for template in section.templates:
            if template.name == "m":
                self.add_object_property("hasGender", "masculine")
            elif template.name == "f":
                self.add_object_property("hasGender", "feminine")
            elif template.name == "mf":
                self.add_object_property("hasGender", "masculine")
                self.add_object_property("hasGender", "feminine")
            elif template.name == "p":
                self.add_object_property("hasNumber", "plural")
            elif template.name == "s":
                self.add_object_property("hasNumber", "singular")

    def _parse_verbal_inflections(self, head):
        templates = {
            t.name: t.arguments
            for t in head.templates
        }
        verb_template = templates.get("fr-verbe-flexion")
        if verb_template is None:
            return
        literal = format_literal(verb_template[0].value)
        for i in range(1, len(verb_template)):
            inflection = self.rscmgr.conjugation.get(verb_template[i].name)
            if inflection is not None:
                self.add_object_property(inflection, literal)

    def _parse_senses(self, head):
        senses = list()
        definition, examples = None, list()
        for line in head.contents.split("\n"):
            match = DEFINITION_PATTERN.search(line)
            if match is None:
                continue
            if len(match.group(1)) > 1:
                # Here the definition is a sub definition, outside of our focus.
                continue
            if match.group(2) == "":
                if definition is not None:
                    senses.append((definition, examples[:]))
                    examples = list()
                definition = match.group(3)
            else:
                examples.append(match.group(3))
        if definition is not None:
            senses.append((definition, examples[:]))
        for definition, examples in senses:
            sense = WikitextSense.from_definition(self, definition, examples)
            if sense.has_dependency and len(self.senses) > 0:
                sense.depends_on = self.senses[-1]
            self.senses.append(sense)

    def _parse_sense_inflections(self):
        for sense in self.senses[:]:
            is_inflection = False
            for inflection, patterns in AGREEMENT_INFLECTION_PATTERNS.items():
                for pattern in patterns:
                    match = pattern.search(sense.definition)
                    if match is not None:
                        is_inflection = True
                        if match.group(1) is not None:
                            target = match.group(1).strip()
                        else:
                            target = match.group(2).strip().split("|")[0]\
                                .split("#")[0].strip()
                        self.add_object_property(
                            inflection,
                            format_literal(target)
                        )
            if is_inflection:
                self.senses.remove(sense)

    def _parse_subsection(self, subtitle, subsection):
        link = self.rscmgr.links.get(subtitle)
        if link is not None:
            self._parse_links(link, subsection)
        elif subtitle == "prononciation":
            self._parse_pronunciation(subsection)
        else:
            return False
        return True


class WikitextSense(OntologyIndividual):
    """Python representation of a flont:LexicalSense.
    """

    def __init__(self, entry):
        OntologyIndividual.__init__(self, entry.rscmgr, "LexicalSense")
        self.entry = entry
        self.definition = None
        self.has_dependency = False
        self.depends_on = None

    def set_iri(self, i):
        """Set the sense IRI and link it to its entry. The entry IRI must have
        been set before!
        """
        self.iri = "%s.%d" % (
            self.entry.iri,
            i + 1
        )
        self.entry.add_object_property("hasSense", self.iri)
        if self.depends_on is not None:
            self.add_object_property("dependsOn", self.depends_on.iri)

    def _parse_precisions_callback(self, match):
        split = match.group(1).split("|")
        if len(split) > 0:
            template_name = split[0].strip()
            precision = self.rscmgr.definitions.get(template_name)
            if precision is not None:
                if self.rscmgr.definitions_type[precision]\
                    == "RelationshipBetweenDefinition":
                    self.has_dependency = True
                self.add_object_property("hasPrecision", precision)
                return ""
        return match.group(0)

    def parse_definition(self, definition, examples):
        """Inflate the sense with a definition and some examples.
        """
        definition = TEMPLATE_PATTERN.sub(
            self._parse_precisions_callback,
            definition
        )
        definition = MULTIPLE_SPACES_PATTERN.sub(" ", definition).strip()
        self.add_data_property("definition", definition)
        self.definition = definition
        for example in examples:
            self.add_data_property("example", example)

    @classmethod
    def from_definition(cls, entry, definition, examples):
        """Create a sense from a definition and examples.
        """
        sense = cls(entry)
        sense.parse_definition(definition, examples)
        return sense
