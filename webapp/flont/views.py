"""Views.
"""

import re
import urllib.parse
from django.shortcuts import render
import flont.apps
from . import ontology


DEFAUTL_SPARQL_QUERY = """
PREFIX flont: <https://ontology.chalier.fr/flont#>
SELECT ?literal ?label
WHERE {
    flont:_musique_nCom1 flont:hasDerivedWord ?literal .
    ?literal flont:label ?label .
}
LIMIT 10
""".strip()


def landing_page(request):
    """Landing page.
    """
    return render(request, "flont/landing_page.html", {})


def search(request):
    """Label search page.
    """
    query = urllib.parse.unquote(request.GET.get("q", ""))
    node = ontology.find_literal_by_label(query)
    literal = None
    if node is not None:
        literal = ontology.retrieve_literal_info(node)
    return render(request, "flont/search.html", {"query": query, "literal": literal})


def endpoint(request):
    """SPARQL endpoint.
    """
    header_pattern = re.compile(r"SELECT(\s\?.*)+\s*WHERE", re.MULTILINE)
    query = request.POST.get("query", DEFAUTL_SPARQL_QUERY)
    results = None
    header = None
    if request.method == "POST":
        match = header_pattern.search(query)
        if match is not None:
            header = match.group(1).strip().split(" ")
        results = flont.apps.graph.query(query)
    return render(request, "flont/endpoint.html", {
        "sparql_query": query,
        "results": results,
        "header": header
    })
