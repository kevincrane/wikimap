import sys
import traceback
import page_parser
import MySQLdb


__author__ = 'kevin'

#TODO: learn how to unit test this shit; maybe run loadArticle with its own WikiPage, check output matches text


class WikiXmlIndexer:
    """
    Class to read a Wikipedia XML data file, extract the title/text and store in a local MySQL database.
    """

    # Database values
    DATABASE_HOST = "localhost"
    DATABASE_USER = ""
    DATABASE_PASSWD = ""
    DATABASE_NAME = "wikimap"

    # Table and XML file values
    INDEX_TABLE = "wiki_index_mini"
    DEFAULT_WIKI_XML = "miniwiki.xml"

    def __init__(self, wikiXml=DEFAULT_WIKI_XML, dbHost=DATABASE_HOST, dbUser=DATABASE_USER,
                 dbPasswd=DATABASE_PASSWD, dbName=DATABASE_NAME, table=INDEX_TABLE):
        """
        Initialize the database and cursor
        :param wikiXml:
        :param dbHost:
        :param dbUser:
        :param dbPasswd:
        :param dbName:
        :param table:
        """
        self.wikiXml = wikiXml      # The XML file containing the Wikipedia data
        self.lastId = -1            # The last wikiId that was added to the index

        # Initialize the database connection and create a new table if necessary
        # Open connection to database wikimap and set proper encoding to UTF-8
        self.database = MySQLdb.connect(host=dbHost, user=dbUser, passwd=dbPasswd, db=dbName)
        self.database.set_character_set('utf8')
        self.database.autocommit(True)

        self.cursor = self.database.cursor()
        self.table = table


    def resetTable(self):
        """
        Drop current index table and re-create it
        """
        try:
            self.cursor.execute("DROP TABLE IF EXISTS %s" % self.table)
            self.cursor.execute("CREATE TABLE %s (id INT(10) UNSIGNED NOT NULL AUTO_INCREMENT, PRIMARY KEY(id), "
                                "title VARBINARY(255), wiki_id INT, content MEDIUMBLOB);" % self.table)
        except:
            print "POOP, A DATABASE ERROR"
            print traceback.format_exc()
            pass

    def closeTable(self):
        """
        Close the database
        """
        self.cursor.close()
        self.database.close()

    def loadArticle(self, wikiPage):
        """
        Load the current article into a MySQL table
        Argument: Receives a page_parser.WikiPage object
        Used as callback method with WikiDumpHandler
        :param wikiPage:
        """
        # If the current WikiPage has been added already, skip it
        if int(wikiPage.id) <= self.lastId:
            return

        # Generate SQL query to insert new WikiPage row
        sql = "INSERT INTO " + self.INDEX_TABLE + " (`title`, `wiki_id`, `content`) VALUES (%s, %s, %s);"
        self.cursor.execute(sql, (wikiPage.title, wikiPage.id, wikiPage.text))
        print "Inserted " + wikiPage.__str__() + "; length: " + str(len(wikiPage.text))

    def addAllNewArticles(self):
        """
        Determine last article ID added to DB
        Create a new XML parser
        Iterate through all articles in the XML file and create a WikiPage object from each
        Call loadArticle(wikiPage) and insert title, id, and text into MySQL
        """
        # Determine last article ID added to DB
        self.cursor.execute("SELECT wiki_id FROM %s ORDER BY wiki_id DESC LIMIT 0, 1;" % self.table)
        max_id = self.cursor.fetchone()
        if max_id:
            self.lastId = max_id[0]
            print "Last WikiID found was %d, adding all articles past that." % self.lastId
        else:
            self.lastId = -1
            print "No previous articles found in table %s, adding all new articles from the beginning." % self.table

        # Generate a wiki xml parser, open the file, and store each article in DB
        wikiParser = page_parser.createWikiParser(self.loadArticle)
        wikiParser.parse(open(self.wikiXml))


# Main Method
if __name__ == "__main__":
    # Initialize WikiXmlIndexer
    if len(sys.argv) == 2:
        wikiIndexer = WikiXmlIndexer(wikiXml=sys.argv[1])
    else:
        wikiIndexer = WikiXmlIndexer()

    #TODO: add command line arguments to change table and file names and resetTable

    # If you want to start over and re-index the DB, uncomment the following line (MASSIVE TIMESINK)
    # wikiIndexer.resetTable()

    # Index and add every new article to the DB (wikiID > the last wikiId added)
    wikiIndexer.addAllNewArticles()

    # Close the database
    wikiIndexer.closeTable()