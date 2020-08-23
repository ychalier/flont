"""Raw WikiText formatting for HTML display.
"""

import re
from django.urls import reverse
import wikitextparser
from flont.languages import LANGUAGE_CODES

NEW_LINES_PATTERN = re.compile("\n")
REFERENCE_PATTERN = re.compile("<ref>(.*?)</ref>")
WIKILINKS_PATTERN = re.compile(r"\[\[(.+?)(\#.*?)?(\|.+?)?\]\]")
TEMPLATES_PATTERN = re.compile(r"{{.*?}}")
SPACES_PATTERN = re.compile("(  +)")


def format_word(raw, trs=None, sense=None):
    """Format a word from a template argument, with possibly a transcript
    and a sense attached to it.
    """
    string = "<i>" + raw.value + "</i>"
    if trs is not None:
        string += """, <span class="transcript">%s</span>""" % trs.value
    if sense is not None:
        string += " (&laquo; %s &raquo;)" % sense.value
    return string


def get_arg_mult(template, *names):
    """Fetch the first existing argument of a template from a sequence of
    candidate argument names. Return `None` if none of them exist.
    """
    for name in names:
        argument = template.get_arg(name)
        if argument is not None:
            return argument
    return None


def repl_wikilinks(match):
    """Pattern replacer for wikilinks.
    """
    label = match.group(1)
    base = reverse("flont:graph", kwargs={"short_iri": "_" + label.replace(" ", "_")})
    if match.group(3) is not None:
        label = match.group(3)[1:]
    return """<a class="internal" href="%s">%s</a>""" % (base, label)


def _external_link_template_hanlder(base_url):
    def fun(template):
        name = template.get_arg("1").value
        url = re.sub(" ", "_", name)
        if template.has_arg("2"):
            name = template.get_arg("2").value
        return """<a class="external" href="%s%s">%s</a>"""\
            % (base_url, url, name)
    return fun


def _template_handler_link(template):
    # https://fr.wiktionary.org/wiki/Mod%C3%A8le:lien
    target = template.get_arg("1").value
    base = reverse("flont:graph", kwargs={"short_iri": "_" + target.replace(" ", "_")})
    format_word(template.get_arg("1"), template.get_arg("tr"))
    label = format_word(template.get_arg("1"), template.get_arg("tr"))
    return """<a class="internal" href="%s">%s</a>""" % (base, label)


def _template_handler_polytonic(template):
    # https://fr.wiktionary.org/wiki/Mod%C3%A8le:Polytonique
    word = template.get_arg("1")
    if TEMPLATES_PATTERN.match(word.value):
        word = get_arg_mult(wikitextparser.parse(word.value).templates[0], "1")
    return format_word(
        word,
        get_arg_mult(template, "tr", "2"),
        get_arg_mult(template, "sens", "3")
    )


def _template_handler_lang(template):
    language = template.get_arg("1")
    language_label = LANGUAGE_CODES.get(language.value)
    if language_label is None:
        language_label = language.value
    string = language_label
    word = get_arg_mult(template, "mot", "3")
    if word is not None:
        string += " " + format_word(
            word,
            get_arg_mult(template, "tr", "4", "R"),
            get_arg_mult(template, "sens", "5"),
        )
    return string


def _template_handler_composed(template):
    # https://fr.wiktionary.org/wiki/Mod%C3%A8le:compos%C3%A9_de
    prefix = "composé de "
    if template.has_arg("f"):
        prefix = "composée de "
    if template.has_arg("m"):
        prefix = prefix[0].upper() + prefix[1:]
    components = list()
    for i in range(1, 8):
        if not template.has_arg(str(i)):
            break
        components.append(format_word(
            template.get_arg(str(i)),
            template.get_arg("tr" + str(i)),
            template.get_arg("sens" + str(i))
        ))
    string = prefix
    for i, component in enumerate(components):
        string += component
        if i == len(components) - 2:
            string += " et "
        elif i < len(components) - 2:
            string += ", "
    return string


def _template_hanlder_cf(template):
    # https://fr.wiktionary.org/wiki/Mod%C3%A8le:cf
    args = list()
    for i in range(1, 15):
        arg = template.get_arg(str(i))
        if arg is None:
            break
        args.append("[[%s]]" % arg.value)
    return "(cf. %s)" % ", ".join(args)


def _template_handler_ignore(_):
    return ""


def _fstarg_template_handler(string_template):
    def fun(template):
        return string_template % template.get_arg("1").value
    return fun


def _prefix_template_handler(prefix, isolate=False, first_interfix="de"):
    def fun(template):
        string = prefix
        _fitfx = first_interfix
        if template.has_arg("m"):
            string = prefix[0].upper() + prefix[1:]
        if template.has_arg("texte") and not template.has_arg("nolien"):
            _fitfx = template.get_arg("texte").value
        if template.has_arg("de"):
            string += " %s <i>" % _fitfx + template.get_arg("de").value + "</i>"
            if template.has_arg("de2"):
                string += " et de <i>" + template.get_arg("de2").value + "</i>"
            return string
        if isolate:
            return "(<i>%s</i>)" % string
        return string
    return fun


def _template_hanlder_zh_lien(template):
    return "%s (<i>%s</i>)" % (template.get_arg("1").value, template.get_arg("2").value)


def _template_handler_recons(template):
    # https://fr.wiktionary.org/wiki/Mod%C3%A8le:recons
    return format_word(
        template.get_arg("1"),
        template.get_arg("tr"),
        template.get_arg("sens")
    )


def _template_handler_fchim(template):
    # https://fr.wiktionary.org/wiki/Mod%C3%A8le:fchim
    string = ""
    for i in range(1, 21):
        if not template.has_arg(str(i)):
            break
        if i % 2 == 0:
            string += "<sub>%s</sub>" % template.get_arg(str(i)).value
        else:
            string += template.get_arg(str(i)).value
    return string


def _template_handler_suppletion(template):
    string = ""
    if template.has_arg("mot"):
        string += "Ce mot"
    else:
        string += "Cette forme"
    string += " dénote une supplétion car son étymologie est distincte de celle"
    words = []
    for i in [1, 2, 3]:
        if template.has_arg(str(i)):
            words.append(format_word(
                template.get_arg(str(i)),
                template.get_arg("tr" + ("" if i == 1 else str(i)))
            ))
    if len(words) > 1:
        string += "s"
    if len(words) > 0:
        string += " de " + words[0]
    if len(words) == 2:
        string += " et de " + words[1]
    elif len(words) == 3:
        string += ", de " + words[1] + " et de " + words[2]
    return string


def _jargon_template_handler(jargon):
    return lambda _: "(<i>%s</i>)" % jargon


# List of templates with at least 10 occurrences within the etymologies.
TEMPLATE_HANDLERS = {
    "composé de": _template_handler_composed,
    "recons": _template_handler_recons,
    "étyl": _template_handler_lang,
    "calque": _template_handler_lang,
    "étylp": _template_handler_lang,
    "Lang": _template_handler_lang,
    "lang": _template_handler_lang,
    "polytonique": _template_handler_polytonic,
    "Polytonique": _template_handler_polytonic,
    "lien": _template_handler_link,
    "l": _template_handler_link,
    "cf": _template_hanlder_cf,
    "supplétion": _template_handler_suppletion,
    "zh-lien": _template_hanlder_zh_lien,
    "fchim": _template_handler_fchim,
    "date": _fstarg_template_handler("(<i>%s</i>)"),
    "term": _fstarg_template_handler("(<i>%s</i>)"),
    "siècle": _fstarg_template_handler("(<i>%s<sup>e</sup> siècle</i>)"),
    "siècle2": _fstarg_template_handler("%s<sup>e</sup>"),
    "pc": _fstarg_template_handler("""<span class="small-caps">%s</span>"""),
    "circa": _fstarg_template_handler("(<i>ca. %s</i>)"),
    "smcp": _fstarg_template_handler("""<span class="small-caps">%s</span>"""),
    "variante de": _fstarg_template_handler("Variante de <i>%s</i>"),
    "graphie": _fstarg_template_handler("‹%s›"),
    "petites capitales": _fstarg_template_handler("""<span class="small-caps">%s</span>"""),
    "pron": _fstarg_template_handler("\\<i>%s</i>\\"),
    "phon": _fstarg_template_handler("\\<i>%s</i>\\"),
    "pron-API": _fstarg_template_handler("\\<i>%s</i>\\"),
    "incise": _fstarg_template_handler("&mdash; %s &mdash;"),
    "couleur": _fstarg_template_handler(
        """<div class="colorblock" style="background-color: %s"></div>"""),
    "ébauche-étym": lambda _: "Étymologie manquante",
    "e": lambda _: "<sup>e</sup>",
    "sigle": lambda _: "(<i>Sigle</i>)",
    "er": lambda _: "<sup>er</sup>",
    "grc": lambda _: "grec",
    "la": lambda _: "latin",
    "indo-européen commun": lambda _: "indo-européen commun",
    "ortho1990": lambda _: "orthographe rectifiée de 1990",
    "en": lambda _: "anglais",
    "fro": lambda _: "ancien français",
    "re": lambda _: "<sup>re</sup>",
    "ème": lambda _: "<sup>ème</sup>",
    "ère": lambda _: "<sup>ère</sup>",
    "dénominal": _prefix_template_handler("dénominal"),
    "abréviation": _prefix_template_handler("abréviation"),
    "apocope": _prefix_template_handler("apocope"),
    "mot-valise": _prefix_template_handler("mot-valise", first_interfix="formé de"),
    "acronyme": _prefix_template_handler("acronyme", isolate=True),
    "déverbal sans suffixe": _prefix_template_handler("déverbal sans suffixe"),
    "déverbal": _prefix_template_handler("déverbal"),
    "verlan": _prefix_template_handler("verlan", isolate=True),
    "antonomase": _prefix_template_handler("antonomase"),
    "aphérèse": _prefix_template_handler("aphérèse"),
    "agglutination": _prefix_template_handler("agglutination"),
    "univerbation": _prefix_template_handler("univerbation"),
    "diminutif": _prefix_template_handler("diminutif"),
    "parataxe": _prefix_template_handler("parataxe"),
    "contraction": _prefix_template_handler("contraction"),
    "déglutination": _prefix_template_handler("déglutination"),
    "reverlanisation": _prefix_template_handler("reverlanisation"),
    "w": _external_link_template_hanlder("https://fr.wikipedia.org/wiki/"),
    "W": _external_link_template_hanlder("https://fr.wikipedia.org/wiki/"),
    "WP": _external_link_template_hanlder("https://fr.wikipedia.org/wiki/"),
    "ws": _external_link_template_hanlder("https://fr.wikisource.org/wiki/"),
    "wsp": _external_link_template_hanlder("https://species.wikimedia.org/wiki/"),
    "astronomie": _jargon_template_handler("Astronomie"),
    "mythologie": _jargon_template_handler("Mythologie"),
    "marque": _jargon_template_handler("Marque"),
    "néologisme": _jargon_template_handler("Néologisme"),
    "ellipse": _jargon_template_handler("Ellipse"),
    "louchébem": _jargon_template_handler("Louchébem"),
    "peu attesté": _jargon_template_handler("Peu attesté"),
    "anglicisme": _jargon_template_handler("Anglicisme"),
    "figuré": _jargon_template_handler("Figuré"),
    "astron": _jargon_template_handler("Astronomie"),
    "angl": _jargon_template_handler("Anglicisme"),
    "géographie": _jargon_template_handler("Géographie"),
    "militaire": _jargon_template_handler("Militaire"),
    "faux anglicisme": _jargon_template_handler("Faux anglicisme"),
    "R": _template_handler_ignore,
    "réf": _template_handler_ignore,
    "S": _template_handler_ignore,
    "nom w pc": _template_handler_ignore,
    "source": _template_handler_ignore,
    "refnec": _template_handler_ignore,
    "note": _template_handler_ignore,
    "RÉF": _template_handler_ignore,
    "réf ?": _template_handler_ignore,
    "R:TLFi": _template_handler_ignore,
    "réf?": _template_handler_ignore,
    "réfnéc": _template_handler_ignore,
    "*": _template_handler_ignore,
    "?": _template_handler_ignore,
    "note noms de famille": _template_handler_ignore,
    "lien web": _template_handler_ignore,
    "ouvrage": _template_handler_ignore,
    "ISBN": _template_handler_ignore,
    "trad+": _template_handler_ignore,
    "préciser": _template_handler_ignore,
    "Lien web": _template_handler_ignore,
    "référence nécessaire": _template_handler_ignore,
    "ébauche-exe": _template_handler_ignore,
    "Lien web ": _template_handler_ignore,
    "f": _template_handler_ignore,
    "m": _template_handler_ignore,
    "transliterator": _template_handler_ignore,
    "fr-inv": _template_handler_ignore,
    "R:DMF": _template_handler_ignore,
    "Ouvrage": _template_handler_ignore,
    ",": _template_handler_ignore,
    "invar": _template_handler_ignore,
    " ": _template_handler_ignore,
    "R:DÉCT": _template_handler_ignore,
    "TLFi": _template_handler_ignore,
    "Arab": _template_handler_ignore,
    "R:Larousse2vol1922": _template_handler_ignore,
    "ébauche": _template_handler_ignore,
    "lien web ": _template_handler_ignore,
    "Ouvrage ": _template_handler_ignore,
    # definitions templates
    "intransitif": lambda _: "(Intransitif)",
    "transitif": lambda _: "(Transitif)",
    "vieux": lambda _: "(Vieux)",
    "litt": lambda _: "(Littéraire)",
    "basket": lambda _: "(Basket)",
    "ébauche-déf": lambda _: "Définition manquante."
}


class WikiTextString:
    """String of WikiText.
    """

    def __init__(self, parsed):
        self.parsed = parsed

    @classmethod
    def from_text(cls, raw):
        """Create a WikiTextString from a string of WikiText.
        """
        parsed = None
        try:
            parsed = wikitextparser.parse(re.sub("''+", "", raw.strip()))
        except TypeError:
            return None
        return cls(parsed)

    def html(self):
        """Convert WikiText to HTML code.
        """
        repls = list()
        for template in self.parsed.templates:
            handler = TEMPLATE_HANDLERS.get(template.name)
            if handler is not None:
                repl = ""
                try:
                    repl = handler(template)
                except AttributeError:
                    # An argument that should exist according to the
                    # documentation was not found.
                    pass
                placeholder = str(template)
                repls.append((placeholder, repl))
        string = self.parsed.plain_text(
            replace_wikilinks=False,
            replace_templates=False,
            replace_tags=False,
        )
        for placeholder, repl in repls:
            string = string.replace(placeholder, repl)
        string = WIKILINKS_PATTERN.sub(repl_wikilinks, string)
        string = NEW_LINES_PATTERN.sub("<br>", string)
        string = REFERENCE_PATTERN.sub("", string)
        string = TEMPLATES_PATTERN.sub("", string)
        string = SPACES_PATTERN.sub("", string)
        return string.strip()

    def list(self):
        """Convert WikiText to HTML code, taking lists into account.
        """
        lists = self.parsed.get_lists()
        if len(lists) != 1:
            return self.html()
        if len(lists[0].items) == 1:
            sublists = lists[0].sublists()
            if len(sublists) > 0:
                return "%s<ul>%s</ul>" % (
                    WikiTextString.from_text(lists[0].items[0]).html(),
                    "\n".join(
                        "<li>%s</li>" % WikiTextString.from_text(i).html()
                        for sublist in sublists
                        for i in sublist.items
                    )
                )
            return WikiTextString.from_text(lists[0].items[0]).html()
        return "<ul>%s</ul>" % ("\n".join(
            "<li>%s</li>" % WikiTextString.from_text(i).html()
            for i in lists[0].items
        ))
