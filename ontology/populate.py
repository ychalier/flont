"""Main functions for populating the ontology from a database. The database
should follow the schema precised in `download.py`.
"""

import os
import gc
import logging
import contextlib
import sqlite3
import tqdm
import owlready2
from resources import ResourceManager
from article_parser import WikitextLiteral


TQDM_BAR_FORMAT = "{desc}:\t{percentage:3.0f}%|{bar:10}{r_bar}"


@contextlib.contextmanager
def get_db_cursor(database_filename):
    """Context function for read-only interaction with the database.
    """
    connection = sqlite3.connect(database_filename)
    cursor = connection.cursor()
    yield cursor
    connection.close()


def iter_db_rows(database_filename, max_iters=None, desc=None):
    """Iterate over the database rows.
    """
    with get_db_cursor(database_filename) as cursor:
        if max_iters is None:
            total = cursor.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
            query = "SELECT title, content FROM entries"
        else:
            total = max_iters
            query = "SELECT title, content FROM entries LIMIT %d" % max_iters
        for row in tqdm.tqdm(cursor.execute(query), total=total, desc=desc,
                             bar_format=TQDM_BAR_FORMAT):
            yield row


class OntologyManager:
    """Interface between the interal Python representation of individuals and
    the owlready2 reprensation.
    """

    def __init__(self, folder):
        self.folder = folder
        self.world = None
        self.ontology = None
        self._functional = dict()

    def load(self):
        """Load the ontology schema.
        """
        uri = "file://" + os.path.join(os.getcwd(), self.folder, "schema.owl")
        self.world = owlready2.World()
        self.ontology = self.world.get_ontology(uri).load()

    def _add_property(self, subj, ppty, obj):
        functionality = self._functional.get(ppty)
        if functionality is None:
            ppty_node = self.ontology[ppty]
            functionality = ppty_node.is_functional_for(obj)
            self._functional[ppty] = functionality
        if functionality:
            setattr(subj, ppty, obj)
        else:
            getattr(subj, ppty).append(obj)

    def add_individual(self, individual):
        """Add an individual to the ontology.
        """
        _ = self.ontology[individual.cls](individual.iri)

    def add_properties(self, individual):
        """Add all properties of an individual to the ontology.
        """
        node = self.ontology[individual.iri]
        for ppty, value in individual.get_data_properties():
            self._add_property(node, ppty, value)
        for ppty, value in individual.get_object_properties():
            obj = self.ontology[value]
            if obj is None:
                continue
            self._add_property(node, ppty, obj)

    def save(self, output_filename, save_as_owl=False):
        """Save the ontology to the disk.
        """
        logging.info("Clearing memory...")
        gc.collect()
        if os.path.isfile(output_filename):
            logging.info("Deleting previous DB file %s", output_filename)
            os.remove(output_filename)
        logging.info("Saving world...")
        if save_as_owl:
            self.ontology.save(file=output_filename, format="rdfxml")
        else:
            self.world.set_backend(filename=output_filename)
            self.world.save()


def populate_individuals(
        database_filename,
        resource_folder,
        output_filename,
        max_iters=None,
        save_as_owl=False):
    """Populate the ontology with individuals parsed from the database.
    """
    logging.info("Loading resources...")
    resmgr = ResourceManager(resource_folder)
    resmgr.load()
    ontmgr = OntologyManager(resource_folder)
    ontmgr.load()
    logging.info("Parsing the database...")
    literals = list()
    for article in iter_db_rows(database_filename, max_iters, "Parsing database"):
        literals.append(WikitextLiteral.from_article(resmgr, *article))
    logging.info("Creating individuals...")
    for literal in tqdm.tqdm(literals, desc="Creating individuals", bar_format=TQDM_BAR_FORMAT):
        ontmgr.add_individual(literal)
        for entry in literal.entries:
            ontmgr.add_individual(entry)
            for sense in entry.senses:
                ontmgr.add_individual(sense)
    logging.info("Creating properties...")
    for literal in tqdm.tqdm(literals, desc="Creating properties", bar_format=TQDM_BAR_FORMAT):
        ontmgr.add_properties(literal)
        for entry in literal.entries:
            ontmgr.add_properties(entry)
            for sense in entry.senses:
                ontmgr.add_properties(sense)
    del literals
    logging.info("Saving ontology to %s", os.path.realpath(output_filename))
    ontmgr.save(output_filename, save_as_owl)
    logging.info("Done populating the ontology!")
