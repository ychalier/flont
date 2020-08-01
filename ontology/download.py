"""Download a Wiktionary dump and cast it into an SQLite database.
"""

import os
import re
import logging
import sqlite3
import xml.etree.ElementTree
import requests
import clint
import bz2file
import tqdm


NS = "{http://www.mediawiki.org/xml/export-0.10/}"

SECTION_TITLE_PATTERN = re.compile(r"^(=+) (.*) =+$")

SECTION_BLACKLIST = {
    "{{S|traductions}}",
    "{{S|traductions à trier}}",
}


def find_last_dump():
    """Step 1.
    Find the last French Wiktionary dump from the //wikimedia.mirror.us.dev/
    index.
    """
    logging.info("Requesting dump index...")
    response = requests.get(
        "https://wikimedia.mirror.us.dev/backup-index.html")
    html = response.text
    match = re.search("<a href=\"frwiktionary/(.*?)\">frwiktionary</a>", html)
    if match is None:
        logging.error("No dump found!")
        return None
    dump = match.group(1)
    logging.info(
        "Found dump at https://wikimedia.mirror.us.dev/frwiktionary/%s", dump)
    return dump


def find_download_link(dump):
    """Step 2.
    From the list of files of that last dump, extract the one with all the
    content we are looking for, i.e. articles.
    """
    url = "https://wikimedia.mirror.us.dev/frwiktionary/%s/dumpstatus.json" % dump
    logging.info("Requesting dump status...")
    response = requests.get(url).json()
    download_link = "https://wikimedia.mirror.us.dev"\
        + response["jobs"]["articlesmultistreamdump"]["files"]\
            ["frwiktionary-%s-pages-articles-multistream.xml.bz2" % dump]["url"]
    logging.info("Found download link: %s", download_link)
    return download_link


def download_file(download_link):
    """Step 3.
    Download this big massive file.
    """
    path = os.path.realpath(download_link.split("/")[-1])
    logging.info("Downloading to %s", path)
    response = requests.get(download_link, stream=True)
    with open(path, "wb") as output_file:
        total_length = int(response.headers.get("content-length"))
        for chunk in clint.textui.progress.bar(
                response.iter_content(chunk_size=1024),
                expected_size=(total_length / 1024) + 1):
            if chunk:
                output_file.write(chunk)
                output_file.flush()
    return path


def create_database(dump):
    """Step 4.
    Create the database and the main table for storing the data.
    """
    filename = "%s.sqlite3" % dump
    if os.path.isfile(filename):
        if input("Database %s already exists. Overwrite?\ny/n> " % filename).lower()\
                in ["y", "yes"]:
            os.remove(filename)
    logging.info("Creating SQLite database %s", filename)
    connection = sqlite3.connect(filename)
    cursor = connection.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        content TEXT NOT NULL
    )
    """.strip())
    connection.commit()
    connection.close()
    return filename


def clear_article_content(raw_content):
    """Minor cleaning for article's contents for step 5.
    """
    clean_content = ""
    active = False
    last_section_level = 10
    for line in raw_content.strip().split("\n"):
        match = SECTION_TITLE_PATTERN.search(line.strip())
        if match is not None:
            section_level = len(match.group(1))
            section_title = match.group(2)
            if not active and section_level > last_section_level:
                pass
            else:
                active = section_title == "{{langue|fr}}"\
                    or (section_title not in SECTION_BLACKLIST
                        and not re.match(r"{{langue\|.+}}", section_title))
                if active:
                    last_section_level = 10
                else:
                    last_section_level = min(last_section_level, section_level)
        if active:
            clean_content += line + "\n"
    return clean_content


def populate_database(database_filename, dump_filename):
    """Step 5.
    Read and parse the downloaded file, and every time an article is
    encountered, we insert it in the database.
    """
    logging.info("Populating database (there are ca. 4M pages)...")
    connection = sqlite3.connect(database_filename)
    cursor = connection.cursor()
    with bz2file.BZ2File(dump_filename) as xml_file:
        parser = xml.etree.ElementTree.iterparse(xml_file)
        pbar = tqdm.tqdm(unit="page")
        for event, element in parser:
            if event == "end" and element.tag == NS + "page":
                pbar.update(1)
                if element.find(NS + "ns").text != "0":
                    element.clear()
                    continue
                title = element.find(NS + "title").text
                content = element.find(NS + "revision").find(NS + "text").text
                if "== {{langue|fr}} ==" not in content:
                    element.clear()
                    continue
                clean_content = clear_article_content(content)
                cursor.execute(
                    """INSERT INTO entries (title, content) VALUES (?, ?)""",
                    (title, clean_content))
                element.clear()
        pbar.close()
    logging.info("Commiting database insertions...")
    connection.commit()
    connection.close()


def main():
    """Main function.
    """
    logging.basicConfig(
        format="%(levelname)s %(asctime)s %(message)s",
        level=logging.INFO)
    dump = find_last_dump()
    if dump is None:
        return
    download_link = find_download_link(dump)
    dump_filename = download_file(download_link)
    database_filename = create_database(dump)
    populate_database(database_filename, dump_filename)
    logging.info("Done. You may delete the .xml.bz2 file now.")


if __name__ == "__main__":
    main()
