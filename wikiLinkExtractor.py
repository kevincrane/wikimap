#!/usr/bin/python

import argparse
import atexit
from articleLinkParser import extractLinks
from model.IndexModel import IndexModel
from model.LinksModel import LinksModel
import page_parser


__author__ = 'kevin'

#TODO: learn how to unit test this shit; maybe run loadArticle with its own WikiPage, check output matches text
#TODO: multi-threading, each article read -> new thread
#TODO: update README


# Table and XML file values
INDEX_TABLE = "wiki_index_mini"
LINKS_TABLE = "wiki_links_mini"
DEFAULT_WIKI_XML = "miniwiki.xml"

# The minimum number of links needed to save an article
MIN_LINKS = 3


class WikiLinkExtractor:
    """
    Class to read a Wikipedia XML data file, extract the title/text and store in a local MySQL database.
    """

    def __init__(self, wikiXml=DEFAULT_WIKI_XML, indexTableName=INDEX_TABLE, linksTableName=LINKS_TABLE):
        """
        Initialize the database and cursor
        :param wikiXml:
        :param indexTableName:
        :param linksTableName:
        """
        self.wikiXml = wikiXml      # The XML file containing the Wikipedia data
        self.lastId = -1            # The last wikiId that was added to the index

        # Initialize the database connection
        self.indexModel = IndexModel(indexTable=indexTableName)
        self.linksModel = LinksModel(linksTable=linksTableName)

        # Initialize article counter
        self.total_articles = 0
        self.total_links = 0

    def extractLinksFromArticle(self, wikiPage):
        """
        Read a WikiPage, extract all the links from it, and store them
          and the article data into Linktable and IndexTable
        Argument: Receives a page_parser.WikiPage object
        Used as callback method with WikiDumpHandler
        :param wikiPage:
        """
        # If the current WikiPage has been added already, skip it
        if int(wikiPage.id) <= self.lastId:
            return

        # Extract links from the current article
        links = extractLinks(wikiPage=wikiPage)

        # If the article is significant enough
        if len(links) >= MIN_LINKS:
            self.linksModel.storeLinks(wikiPage.id, links)
            self.indexModel.storeWikiArticle(wikiPage, len(links), 0)

            self.total_articles += 1
            self.total_links += len(links)
            print "Inserted %s; Number of links: %d" % (wikiPage.__str__(), len(links))

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
        wikiParser = page_parser.createWikiParser(self.extractLinksFromArticle)
        #TODO: change this to something with 'with', close file later?
        wikiParser.parse(open(self.wikiXml))

    def exitHandler(self):
        """
        Called when program is killed
        """
        self.indexModel.closeTable()
        self.linksModel.closeTable()
        print ""
        print "WikiLinkExtractor closing. Parsed the following new articles:"
        if self.total_articles > 0:
            print "Total articles:  %d" % self.total_articles
            print "Total links:     %d" % self.total_links
            print "Avg links/art:   %f" % (1.0 * self.total_links / self.total_articles)
        else:
            print "No new articles added."


def parseArguments():
    # Command-line argument parsing
    parser = argparse.ArgumentParser(description="Reads through an XML file containing Wikipedia data, "
                                                 "parses out each article, and stores each into a row in a DB table")
    parser.add_argument("-f", "--file", dest="wikiXml", type=str, default=DEFAULT_WIKI_XML,
                        help="The XML file that contains the Wikipedia data. Default=%s" % DEFAULT_WIKI_XML)
    parser.add_argument("-i", "--table", dest="indexTable", type=str, default=INDEX_TABLE,
                        help="The table to store everything into. Default=%s" % INDEX_TABLE)
    parser.add_argument("-l", "--links", dest="linksTable", type=str, default=LINKS_TABLE,
                        help="The table to store everything into. Default=%s" % LINKS_TABLE)

    parser.add_argument("--reset", help="Drop existing indexTable and recreate it. WARNING: could be very "
                                        "time-consuming to index everything again.", action="store_true")
    return parser.parse_args()


# Main Method
if __name__ == "__main__":
    # Parse command-line arguments
    args = parseArguments()

    # Initialize WikiXmlIndexer
    wikiIndexer = WikiLinkExtractor(wikiXml=args.wikiXml, indexTableName=args.indexTable, linksTableName=args.linksTable)
    atexit.register(wikiIndexer.exitHandler)

    # If you want to start over and re-index the DB, uncomment the following line (MASSIVE TIMESINK)
    if args.reset:
        print "DROPPING AND RECREATING EXISTING INDEX TABLE %s" % wikiIndexer.indexModel.indexTable
        # print "TEMPORARILY DISABLED."
        #TODO: Uncomment this
        wikiIndexer.indexModel.resetTable()
        wikiIndexer.linksModel.resetTable()

    # Index and add every new article to the DB (wikiID > the last wikiId added)
    wikiIndexer.addAllNewArticles()
