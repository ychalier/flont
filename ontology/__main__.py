"""CLI interface components."""

import logging
import argparse
from __init__ import __version__  # pylint: disable=E0611
import populate


def main():
    """Argument parsing.
    """
    parser = argparse.ArgumentParser(
        description="FLOnt: French Lexicon Ontology.")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-q", "--quiet", action="store_true")
    subparsers = parser.add_subparsers(dest="action", required=True)
    populate_parser = subparsers.add_parser("populate")
    populate_parser.add_argument(
        "database", type=str, help="path to the database")
    populate_parser.add_argument(
        "ontology", type=str, help="path to the ontology schema file (*.owl)")
    populate_parser.add_argument("output", type=str, help="output filename")
    populate_parser.add_argument(
        "-mi", "--max-iter", type=int, default=0,
        help="maximum number of iterations")
    args = parser.parse_args()
    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG
    elif args.quiet:
        log_level = logging.WARNING
    logging.basicConfig(
        filename="flont.log",
        format='%(levelname)s %(asctime)s %(module)s %(message)s',
        level=log_level)
    logging.info("FLOnt v%s", __version__)
    if args.action == "populate":
        max_iters = None
        if args.max_iter > 0:
            max_iters = args.max_iter
        populate.populate_individuals(
            args.database, args.ontology, args.output, max_iters)


main()
