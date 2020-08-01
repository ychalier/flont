"""Miscellaneous functions of general purpose."""

import os
import sqlite3
import contextlib
import urllib.parse
import time
import logging
import owlready2


@contextlib.contextmanager
def get_db_cursor(database_filename):
    """Context function for read-only interaction with the database.
    """
    connection = sqlite3.connect(database_filename)
    cursor = connection.cursor()
    yield cursor
    connection.close()


def format_literal(raw):
    """Format a literal into a safe format.
    """
    return "entry_" + urllib.parse.quote(raw)


def load_ontology(path):
    """Load an ontology into an RDFlib graph.
    """
    time_start = time.time()
    realpath = os.path.realpath(path)
    logging.info("Loading ontology from  %s", realpath)
    world = owlready2.World()
    world.get_ontology("file://" + realpath).load()
    graph = world.as_rdflib_graph()
    logging.info(
        "Loaded file in %.3f seconds. Found %d triples.",
        time.time() - time_start, len(graph)
    )
    return graph
