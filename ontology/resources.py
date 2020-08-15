"""Tools for managing the CSV resources in the 'resources' folder.
"""

import os
import logging
import pandas


class ResourceManager:
    """Wrapper for the mappings described in the 'resources' folder.
    """

    def __init__(self, folder):
        self.folder = folder
        self.pos_templates = None
        self.pos_abbreviations = None
        self.conjugation = None
        self.links = None
        self.definitions = None
        self.definitions_type = None

    def load_mapping(self,  # pylint: disable=R0913
                     filename,
                     val_col="iri",
                     key_col="template_names",
                     iri_prefix="flont:",
                     remove_iri_prefix=True):
        """Load one file.
        """
        path = os.path.join(self.folder, filename)
        logging.info("Loading templates from %s", path)
        dataframe = pandas.read_csv(path)
        mapping = dict()
        for _, row in dataframe.iterrows():
            val = row[val_col].strip()
            if remove_iri_prefix:
                val = val.replace(iri_prefix, "")
            for key in row[key_col].split(";"):
                if remove_iri_prefix:
                    key = key.replace(iri_prefix, "")
                mapping[key.strip()] = val
        return mapping

    def load(self):
        """Load all the files.
        """
        self.pos_templates = self.load_mapping("templates_pos.csv")
        self.pos_abbreviations = self.load_mapping(
            "templates_pos.csv", key_col="iri", val_col="abbreviation")
        self.conjugation = self.load_mapping("templates_conjugation.csv")
        self.links = self.load_mapping("templates_links.csv")
        self.definitions = self.load_mapping("templates_definitions.csv")
        self.definitions_type = self.load_mapping(
            "templates_definitions.csv", key_col="iri", val_col="type")
