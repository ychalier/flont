# pylint: disable=all
import sqlite3
from django.apps import AppConfig
from django.conf import settings
import owlready2

world = None
ontology = None
graph = None


class FlontConfig(AppConfig):
    name = 'flont'

    def ready(self):
        global world
        global ontology
        global graph
        if world is None:
            world = owlready2.World(filename=settings.FLONT_DB)
        if ontology is None:
            ontology = world.get_ontology("https://ontology.chalier.fr/flont").load()
        if graph is None:
            graph = world.as_rdflib_graph()
