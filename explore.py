"""This scripts contains tools to perform some analysis on the raw database,
as a first approach at handling the data."""


import re
import os
import sqlite3
import logging
import contextlib
import codecs
import owlready2  # pylint: disable=E0401
import tqdm  # pylint: disable=E0401


LOGGER = logging.getLogger("french-wiktionary.explore")

DATABASE_FILENAME = "db.sqlite3"
NUMBER_OF_ENTRIES = 1799266
ONTOLOGY_FILENAME = "empty-ontology.owl"

TITLE_PATTERN = re.compile("^(=+) {{(.+)}}")

@contextlib.contextmanager
def get_db_cursor():
    """Context function for read-only interaction with the database. Use as
    following:
    ```
    with get_db_cursor() as cursor:
        cursor.execute("... SQL QUERY...")
    ```
    """
    connection = sqlite3.connect(DATABASE_FILENAME)
    cursor = connection.cursor()
    yield cursor
    connection.close()


def extract_table_of_content(text):
    """Parse the full text of a database entry to extract its titles hierarchy.
    """
    toc = list()
    for line in text.split("\n"):
        match = TITLE_PATTERN.search(line)
        if match is not None:
            toc.append(tuple((len(match.group(1)), match.group(2))))
    return toc


def extract_tocs():
    """Extract all table of contents of the database entries.
    """
    LOGGER.info("Extracting table of contents")
    tocs = set()
    with get_db_cursor() as cursor:
        for row in tqdm.tqdm(
                cursor.execute("SELECT content FROM entries"),
                total=NUMBER_OF_ENTRIES):
            for title in extract_table_of_content(row[0]):
                tocs.add(title)
    with codecs.open("tocs.tsv", "w", "utf8") as outfile:
        outfile.write("\n".join(map(lambda toc: "%d\t%s" % toc, tocs)))


def test_ontology_features():
    """Test for the OwlReady module.
    """
    ontology = owlready2\
        .get_ontology("file://" + os.path.join(os.getcwd(), ONTOLOGY_FILENAME))\
        .load()
    individuals = map(lambda o: o.name, ontology.individuals())
    print("Classes:\n" + ", ".join(map(lambda o: o.name, ontology.classes())))
    print("\nProperties:\n" + ", ".join(map(lambda o: o.name, ontology.properties())))
    print("\nIndividuals:\n" + ", ".join(individuals))
    chien = ontology.Noun("chien_0")
    chien.label = "chien"
    chien.definition = "Une sorte d'animal."
    canide = ontology.Noun("canide_0")
    canide.label = "canidé"
    canide.definition = "Une sorte d'animal."
    chien.isSynonymOf.append(canide)
    chien2 = ontology.Noun("chien_1")
    chien2.label = "chien2label"
    ontology.save(file="filled-ontology.owl", format="rdfxml")


def main():
    """Wrapper for the function to execute at script execution. The code within
    this function should only call other functions, not perform direct
    operations on the database."""
    test_ontology_features()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    LOGGER.info("Execution starts")
    main()
    LOGGER.info("Execution stops")
