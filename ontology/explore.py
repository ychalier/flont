"""This scripts contains tools to perform some analysis on the raw database,
as a first approach at handling the data and populating the ontology with
individuals."""

import re
import os
import time
import logging
import codecs
import owlready2
import tqdm
import slugify
import utils
import wikitext


def check_for_duplicates(database_filename):
    """Check the database for any collision between entry titles.
    """
    titles = set()
    collisions = 0
    with utils.get_db_cursor(database_filename) as cursor:
        total = cursor.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        for row in tqdm.tqdm(
                cursor.execute("SELECT title FROM entries"),
                total=total):
            title = wikitext.format_entry_title(row[0])
            if title in titles:
                collisions += 1
            titles.add(title)
    print("Found %d collisions" % collisions)


def extract_tocs(database_filename, output_filename):
    """Extract all table of contents of the database entries, and write it to
    a TSV file.
    """
    logging.info("Extracting table of contents")
    tocs = dict()
    with utils.get_db_cursor(database_filename) as cursor:
        total = cursor.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        for row in tqdm.tqdm(
                cursor.execute("SELECT title, content FROM entries"),
                total=total):
            for toc in wikitext.extract_table_of_content(row[1]):
                if toc not in tocs:
                    tocs[toc] = [1, row[0], "\"%s\"" %
                                 re.sub("\t|\n", " ", row[1])]
                else:
                    tocs[toc][0] += 1
    with codecs.open(output_filename, "w", "utf8") as outfile:
        outfile.write(
            "level\tsection_title\toccurrences\tarticle_title\tarticle_content\n")
        for toc in sorted(tocs):
            outfile.write("\t".join(map(str, [*toc, *tocs[toc]])) + "\n")


def test_ontology_features(ontology_filename):
    """Test for the OwlReady module.
    """
    ontology = owlready2\
        .get_ontology("file://" + os.path.join(os.getcwd(), ontology_filename))\
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


def iter_individuals(database_filename):
    """Iterator for the individual lexical entries in the database.
    """
    individuals = dict()
    for title, model, content in iter_senses(database_filename):
        formatted_title = wikitext.format_entry_title(title)\
            + "."\
            + wikitext.MODEL_TO_ABBREVIATION_MAPPING[model]
        class_ = wikitext.MODEL_TO_CLASS_MAPPING[model]
        individuals.setdefault(formatted_title, 0)
        index, definition, examples = individuals[formatted_title] + \
            1, None, list()
        for row in content.split("\n"):
            if row.strip().startswith("#*"):
                pass
                # examples.append(clean_wikitext(row))
            elif row.strip().startswith("#"):
                if definition is not None:
                    yield formatted_title + ".%d" % index, class_, title, definition, examples[:]
                    individuals[formatted_title] += 1
                    index += 1
                    examples = list()
                definition = wikitext.clean_wikitext(row.strip())
            else:
                # print(row)
                pass
        if definition is not None:
            yield formatted_title + ".%d" % index, class_, title, definition, examples[:]
            individuals[formatted_title] += 1
        # break


def iter_senses(database_filename):
    """Iterate over the senses from within the database.
    """
    ignored_section = list()
    without_section = list()
    with utils.get_db_cursor(database_filename) as cursor:
        total = cursor.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        for row in tqdm.tqdm(cursor.execute("SELECT title, content FROM entries"), total=total):
            found_section = False
            for sec_title, sec_content in wikitext.iter_sections(row[1], 2):
                found_section = True
                if sec_title == "langue|fr":
                    for subsec_title, subsec_content in wikitext.iter_sections(sec_content, 3):
                        model = slugify.slugify(
                            subsec_title.split("|")[1].strip())
                        if model in wikitext.MODEL_TO_CLASS_MAPPING:
                            yield row[0], model, wikitext.extract_definitions(subsec_content)
                elif "langue" in sec_title.split("|"):
                    pass
                else:
                    ignored_section.append((row[0], sec_title))
            if not found_section:
                without_section.append(row[0])
        logging.info("iter_models ignored %d sections", len(ignored_section))
        logging.info("iter_models found %d entries with no section",
                     len(without_section))


def populate_individuals(database_filename, ontology_schema, output_filename):
    """Populate the ontology schema with individuals from the Wiktionary
    database, and write the result to a new file.
    """
    ontology = owlready2\
        .get_ontology("file://" + os.path.join(os.getcwd(), ontology_schema))\
        .load()
    for name, class_, label, definition, examples in iter_individuals(database_filename):
        individual = ontology[class_](name)
        individual.label = label
        individual.definition = definition
        individual.example = examples
    ontology.save(file=output_filename, format="rdfxml")


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


def execute_query(graph, query):
    """Execute a Sparql query over an RDFlib graph.
    """
    time_start = time.time()
    logging.info("Querying...")
    response = graph.query(query.strip())
    logging.info("Found response in %.3f seconds", time.time() - time_start)
    return response
