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
        print("django-flont: Loading app...")
        if world is None:
            print("django-flont: Loading world...")
            world = owlready2.World(filename=settings.FLONT_DB)
        if ontology is None:
            print("django-flont: Loading ontology...")
            ontology = world.get_ontology("https://ontology.chalier.fr/flont").load()
        if graph is None:
            print("django-flont: Loading graph...")
            graph = world.as_rdflib_graph()
        print("django-flont: Loaded app!")
