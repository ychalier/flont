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
python . [-h] [-v] [-q] populate [database] [schema] [output]
```

Use the `-h` flag for a more detailed help message.

## Runtime Measurements

### Time

Here are some metrics for one run on a Windows 10 machine, i5-8600K CPU, 16Gb RAM, with no other application running:

Step | Elasped time (mm:ss)
--- | ---
Creating individuals | 30:10
Inserting properties | 01:29
Exporting the world | 04:20
**Total** | **35:59**

### RAM

Working with the whole data through Owlready2 can be quite memory intensive. Be sure to have several Gbs of RAM free. Here is how a complete parsing did on my machine (16Gb of RAM):

![Parsing RAM Usage](https://i.imgur.com/CrhnDtJ.png)

I got this plot thanks to the [Memory Profiler](https://pypi.org/project/memory-profiler/) module. One can see the RAM consumption throttling, where the first pass over the data was circa 80% done. Individuals creation lasted for 1800 seconds. Then links are created for another 100 seconds. Then temporary objects are dereferenced and the garbage collector is manually called (therefore around 1900 seconds after start), where we can see a drop below the 12Gb of RAM. Then the ontology is saved to the disk.

### Disk

The output is a 2.15Gb SQLite file. It can be exported to a 1.65Gb plain text file with the RDF/XML format.
