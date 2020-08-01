# FLOnt: Ontology Module

This module provides tools for parsing Wiktionary data and populating an ontology with sensible individuals. The raw ontology schema can be found in [schema.owl](schema.owl).

## Getting Started

### Prerequisites

You'll need Python 3, a correct internet connection (for a 500Mb download), and about 2Gb of available storage space.

### Installation

First install the dependency modules listed in the [requirements](requirements.txt):

```bash
pip install -r requirements.txt
```

Then you will need a local copy of a Wiktionary dump, as an SQLite database. There is a [download](download.py) script for that. Call it with:

```bash
python download.py
```

This will download a 500Mb XML file compressed with BZ2, and convert it into a 800Mb SQLite database, whose main table schema is `entries(id, title, content)`, representing the articles from Wiktionary. The database is named after the dump timestamp `YYYYMMDD.sqlite3`.

### Usage

Within the `ontology` directory, you may execute the main script with the following syntax:

```bash
python . [-h] [-v] [-q] {populate,check_duplicates,extract_tocs} ...
```

Use the `-h` flag for a more detailed help message.

**Warning: working with the whole data through Owlready can be quite memory intensive. Be sure to have several Gbs of RAM free.**
