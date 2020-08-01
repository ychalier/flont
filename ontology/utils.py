"""Miscellaneous functions of general purpose."""

import sqlite3
import contextlib


@contextlib.contextmanager
def get_db_cursor(database_filename):
    """Context function for read-only interaction with the database.
    """
    connection = sqlite3.connect(database_filename)
    cursor = connection.cursor()
    yield cursor
    connection.close()
