"""CLI interface components."""

import logging
import argparse
import explore


def main():
    """Argument parsing.
    """
    parser = argparse.ArgumentParser(
        description="FLOnt: French Lexicon Ontology.")
    parser.add_argument("database", type=str, help="path to the database")
    parser.add_argument("ontology_schema", type=str,
                        help="path to the blank ontology")
    parser.add_argument("output_filename", type=str,
                        help="output filename")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-q", "--quiet", action="store_true")
    args = parser.parse_args()
    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG
    elif args.quiet:
        log_level = logging.WARNING
    logging.basicConfig(
        format='%(levelname)s %(asctime)s %(module)s %(message)s',
        level=log_level)
    explore.populate_individuals(
        args.database, args.ontology_scheman, args.output_filename)


main()
