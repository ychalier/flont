"""Raw WikiText formatting for HTML display.
"""

import re
from django.urls import reverse
import wikitextparser


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
