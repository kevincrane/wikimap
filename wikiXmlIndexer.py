#!/usr/bin/python

import argparse
import atexit
import page_parser
from model.IndexModel import IndexModel


__author__ = 'kevin'

#TODO: learn how to unit test this shit; maybe run loadArticle with its own WikiPage, check output matches text


# Table and XML file values
INDEX_TABLE = "wiki_index_mini"
DEFAULT_WIKI_XML = "miniwiki.xml"


class WikiXmlIndexer:
    """
    Class to read a Wikipedia XML data file, extract the title/text and store in a local MySQL database.
    """

    def __init__(self, wikiXml=DEFAULT_WIKI_XML, indexTableName=INDEX_TABLE):
        """
        Initialize the database and cursor
        :param wikiXml:
        :param indexTableName:
        """
        self.wikiXml = wikiXml      # The XML file containing the Wikipedia data
        self.lastId = -1            # The last wikiId that was added to the index

        # Initialize the database connection
        self.indexModel = IndexModel(indexTable=indexTableName)

        # Initialize article counter
        self.counter = 0

    def storeArticle(self, wikiPage):
        """
        Load the current article into a MySQL indexTable
        Argument: Receives a page_parser.WikiPage object
        Used as callback method with WikiDumpHandler
        :param wikiPage:
        """
        # If the current WikiPage has been added already, skip it
        if int(wikiPage.id) <= self.lastId:
            return

        # Store the WikiPage in a new row in the indexTable
        self.indexModel.storeWikiPage(wikiPage)
        self.counter += 1
        print "Inserted " + wikiPage.__str__() + "; length: " + str(len(wikiPage.text))

    def addAllNewArticles(self):
        """
        Determine last article ID added to DB
        Create a new XML parser
        Iterate through all articles in the XML file and create a WikiPage object from each
        Call loadArticle(wikiPage) and insert title, id, and text into MySQL
        """

        # Determine last article ID added to DB
        self.lastId = self.indexModel.getMaxWikiId()
        if self.lastId > 0:
            print "Last WikiID found was %d, adding all articles past that." % self.lastId
        else:
            print "No previous articles found in indexTable %s, adding all new articles from the beginning." \
                  % self.indexModel.indexTable

        # Generate a wiki xml parser, open the file, and store each article in DB
        wikiParser = page_parser.createWikiParser(self.storeArticle)
        wikiParser.parse(open(self.wikiXml))

    def exitHandler(self):
        """
        Called when program is killed
        """
        self.indexModel.closeTable()
        print ""
        print "WikiXmlIndexer closing. Added %d new entries." % self.counter


def parseArguments():
    # Command-line argument parsing
    parser = argparse.ArgumentParser(description="Reads through an XML file containing Wikipedia data, "
                                                 "parses out each article, and stores each into a row in a DB table")
    parser.add_argument("-f", "--file", dest="wikiXml", type=str, default=DEFAULT_WIKI_XML,
                        help="The XML file that contains the Wikipedia data. Default=%s" % DEFAULT_WIKI_XML)
    parser.add_argument("-t", "--table", dest="indexTable", type=str, default=INDEX_TABLE,
                        help="The table to store everything into. Default=%s" % INDEX_TABLE)
    parser.add_argument("--reset", help="Drop existing indexTable and recreate it. WARNING: could be very "
                                        "time-consuming to index everything again.", action="store_true")
    return parser.parse_args()


# Main Method
if __name__ == "__main__":
    # Parse command-line arguments
    args = parseArguments()

    # Initialize WikiXmlIndexer
    wikiIndexer = WikiXmlIndexer(wikiXml=args.wikiXml, indexTableName=args.indexTable)
    atexit.register(wikiIndexer.exitHandler)

    # If you want to start over and re-index the DB, uncomment the following line (MASSIVE TIMESINK)
    if args.reset:
        print "DROPPING AND RECREATING EXISTING INDEX TABLE %s" % wikiIndexer.indexModel.indexTable
        wikiIndexer.indexModel.resetTable()

    # Index and add every new article to the DB (wikiID > the last wikiId added)
    wikiIndexer.addAllNewArticles()