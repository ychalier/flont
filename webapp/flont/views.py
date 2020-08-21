"""Views.
"""

import re
import urllib.parse
import difflib
from django.shortcuts import render, redirect
from django.http import Http404
import flont.apps
import rdflib
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


def landing(request):
    """Landing page.
    """
    return render(request, "flont/landing.html", {})


def iterate_labels():
    """Query the ontology world SQL database to iterate over all the labels
    of the ontology.
    """
    cursor = flont.apps.ontology.graph.db.cursor()
    query = """
    SELECT datas.o
    FROM datas, resources
    WHERE
        datas.p = resources.storid
        AND resources.iri = "https://ontology.chalier.fr/flont#label"
    """
    for (label,) in cursor.execute(query):
        yield label


def search(request):
    """Label search page.
    """
    query_raw = request.GET.get("q", "").strip()
    query = urllib.parse.unquote(query_raw)
    node = ontology.find_literal_by_label(query)
    if node is not None:
        return redirect("flont:graph", short_iri=str(node).replace(ontology.FLONT_IRI, ""))
    top_labels = difflib.get_close_matches(query, iterate_labels(), n=10, cutoff=0.6)
    return render(request, "flont/search.html", {
        "query": query_raw,
        "top_labels": top_labels
    })


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


def graph(request, short_iri):
    """Direct access to the ontology graph.
    """
    iri_no_prefix = short_iri.replace("flont:", "")
    full_iri = ontology.FLONT_IRI + iri_no_prefix
    existing = flont.apps.ontology.search(iri=full_iri)
    if len(existing) == 0:
        raise Http404("Resource '%s' not found." % full_iri)
    node = existing[0]
    is_individual = iri_no_prefix.startswith("_")
    entity_type = None
    entity_data = None
    if is_individual:
        types = set(t.name for t in node.is_a)
        if "Literal" in types:
            entity_type = "literal"
            entity_data = ontology.retrieve_literal_info(rdflib.URIRef(full_iri))
        elif "LexicalSense" in types:
            entity_type = "sense"
            entity_data = ontology.retrieve_lexical_sense_info(rdflib.URIRef(full_iri))
        else:
            entity_type = "entry"
            entity_data = ontology.retrieve_lexical_entry_info(rdflib.URIRef(full_iri))
    else:
        entity_type = "meta"
        entity_data = ontology.get_meta_information(rdflib.URIRef(full_iri))
    return render(request, "flont/graph.html", {
        "flont_iri": ontology.FLONT_IRI,
        "short_iri": iri_no_prefix,
        "entity_type": entity_type,
        "entity_data": entity_data,
    })
