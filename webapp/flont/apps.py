# pylint: disable=all
from django.apps import AppConfig
import owlready2

world = None
ontology = None
graph = None


ONTOLOGY_WORLD_DB = "../ontology/filled.db"


class FlontConfig(AppConfig):
    name = 'flont'

    def ready(self):
        global world
        global ontology
        global graph
        print("Loading world...")
        world = owlready2.World(filename=ONTOLOGY_WORLD_DB)
        print("Loading ontology...")
        ontology = world.get_ontology("https://ontology.chalier.fr/flont").load()
        print("Loading graph...")
        graph = world.as_rdflib_graph()
        print("Loaded!")
