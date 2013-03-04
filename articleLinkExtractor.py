#!/usr/bin/python

import argparse
import atexit
import re
from model.IndexModel import IndexModel
from model.LinksModel import LinksModel


# TODO: make this all multi-threaded; read row to get WikiPage, then split thread to analyze and insert to new DB

# Index and Links tables
INDEX_TABLE = "wiki_index_small"
LINKS_TABLE = "wiki_links_small"


class ArticleLinkExtractor:
    """
    Class to read through a MySQL index of wiki articles, extract a list of all links contained, and store in new indexTable
    """

    def __init__(self, indexTableName=INDEX_TABLE, linksTableName=LINKS_TABLE):
        """
        Initialize the database and cursors
        """
        # Patterns to find end of main wiki article
        self.reference_pattern = re.compile('=+\s?References\s?=+')
        self.extlink_pattern = re.compile('=+\s?External links\s?=+')

        # Initialize the needed database connections and create a new indexTable if necessary
        self.linksModel = LinksModel(linksTable=linksTableName)
        self.indexModel = IndexModel(indexTable=indexTableName)

        # Stats counters
        self.total_articles = 0
        self.total_links = 0

    def extractLinks(self, wikiPage):
        """
        Takes a WikiPage object as an argument
        Returns a list of all valid links found within the current article
        """
        text = wikiPage.text
        links = set()

        # End string at Reference or External Links section if possible
        reference_match = self.reference_pattern.search(text)
        if reference_match:
            text = text[:reference_match.start()]
        else:
            extlink_match = self.extlink_pattern.search(text)
            if extlink_match:
                text = text[:extlink_match.start()]

        # Start iteratively hunting for links (items surrounded by double square brackets)
        link_start = text.find("[[")
        while link_start != -1:
            # Ignore links that start with 'File:'
            if text[link_start + 2: link_start + 7] == "File:":
                link_end = link_start
            #TODO: Check for "Category:" also
            else:
                # Find first matching closing bracket pair
                link_end = text.find("]]", link_start)
                new_link = text[link_start + 2: link_end]

                # Remove alternate display text
                alt_text = new_link.find("|")
                if alt_text > 0:
                    new_link = new_link[:alt_text]
                    # Remove category display text
                category_text = new_link.find("#")
                if category_text > 0:
                    new_link = new_link[:category_text]

                # Add new link to current list of links
                links.add(new_link.strip())

            # Edit string to remove previous link
            text = text[link_end + 2:]
            link_start = text.find("[[")
        return links

    def parseAllNewArticles(self):
        """
        Determine last index row ID added to DB
        Iterate through all articles starting from this row in the indexTable
        Create a WikiPage from the row and pass to extractLinks(WikiPage)
        Store all links found in linksTable
        """
        # Find number of possible objects in DB
        max_count = self.indexModel.getMaxRowId()

        # Determine last article ID added to DB
        last_id = self.linksModel.getMaxIndexId()
        if last_id > 0:
            curr_row = last_id + 1
            print "Indexing all articles starting from row %d in indexTable %s" % (curr_row, self.indexModel.indexTable)
        else:
            curr_row = 1
            print "No previous articles found in linksTable %s, adding all new articles from the beginning." \
                  % self.linksModel.linksTable

        # Fetch every possible row in the database
        while curr_row <= max_count:
            wiki_page = self.indexModel.getWikiPage(curr_row)
            if wiki_page:
                links = self.extractLinks(wiki_page)
                self.total_articles += 1
                self.total_links += len(links)

                # Store links in links_from indexTable
                self.linksModel.storeLinks(curr_row, links)
                print "Links within %s (rowid %d): %d" % (wiki_page.title, curr_row, len(links))
            curr_row += 1

    def exitHandler(self):
        """
        Called when program is killed
        """
        self.linksModel.closeTable()
        self.indexModel.closeTable()
        # Show off the output
        print ""
        print "ArticleLinkExtractor closing. Parsed the following new articles:"
        if self.total_articles > 0:
            print "Total articles:  %d" % self.total_articles
            print "Total links:     %d" % self.total_links
            print "Avg links/art:   %f" % (1.0 * self.total_links / self.total_articles)
        else:
            print "No new articles added."


def parseArguments():
    # Command-line argument parsing
    parser = argparse.ArgumentParser(description="Reads each row of the Wiki Index table, parsing the article content,"
                                                 "extracts every link within, and stores each link in a new row in the"
                                                 "Links table, mapping the Index row id to the name of the link.")
    parser.add_argument("-l", "--links", dest="linksTable", type=str, default=LINKS_TABLE,
                        help="The XML file that contains the Wikipedia data. Default=%s" % LINKS_TABLE)
    parser.add_argument("-i", "--index", dest="indexTable", type=str, default=INDEX_TABLE,
                        help="The table to store everything into. Default=%s" % INDEX_TABLE)
    parser.add_argument("--reset", help="Drop existing indexTable and recreate it. WARNING: could be very "
                                        "time-consuming to index everything again.", action="store_true")
    return parser.parse_args()


# Main Method
if __name__ == "__main__":
    # Parse command-line arguments
    args = parseArguments()

    # Initialize ArticleLinkExtractor
    linkExtractor = ArticleLinkExtractor(linksTableName=args.linksTable, indexTableName=args.indexTable)
    atexit.register(linkExtractor.exitHandler)

    # If you want to start over and re-index the DB, uncomment the following line (MASSIVE TIMESINK)
    if args.reset:
        print "DROPPING AND RECREATING EXISTING INDEX TABLE %s" % linkExtractor.linksModel.linksTable
        linkExtractor.linksModel.resetTable()

    # Find last article parsed, start extracting links from every article past that and store in linksTable
    linkExtractor.parseAllNewArticles()