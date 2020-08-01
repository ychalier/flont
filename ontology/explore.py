"""This scripts contains tools to perform some analysis on the raw database,
as a first approach at handling the data.
"""

import re
import logging
import codecs
import tqdm
import utils
import populate


def check_for_duplicates(database_filename):
    """Check the database for any collision between the encoded literal strings.
    """
    existing = set()
    collisions = 0
    with utils.get_db_cursor(database_filename) as cursor:
        total = cursor.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        for row in tqdm.tqdm(
                cursor.execute("SELECT title FROM entries"),
                total=total):
            literal = utils.format_literal(row[0])
            if literal in existing:
                collisions += 1
            existing.add(literal)
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
            for toc in populate.extract_table_of_content(row[1]):
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
