# pylint: disable=all
import sqlite3
from django.apps import AppConfig
from django.conf import settings
import owlready2

world = None
ontology = None
graph = None
labels = None


class FlontConfig(AppConfig):
    name = 'flont'

    def ready(self):
        global world
        global ontology
        global graph
        global labels
        print("Loading labels...")
        connection = sqlite3.connect(settings.ONTOLOGY_WORLD_DB)
        cursor = connection.cursor()
        labels = list()
        query = """
        SELECT datas.o
        FROM datas, resources
        WHERE
            datas.p = resources.storid
            AND resources.iri = "https://ontology.chalier.fr/flont#label"
        """
        for (label,) in cursor.execute(query):
            labels.append(label)
        connection.close()
        print("Loading world...")
        world = owlready2.World(filename=settings.ONTOLOGY_WORLD_DB)
        print("Loading ontology...")
        ontology = world.get_ontology("https://ontology.chalier.fr/flont").load()
        print("Loading graph...")
        graph = world.as_rdflib_graph()
        print("Loaded!")
