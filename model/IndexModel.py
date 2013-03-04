import MySQLdb
import traceback
from page_parser import WikiPage

__author__ = 'kevin'


class IndexModel:
    """
    Database model to play with the Index DB table of WikiMap (MySQL)
    Columns: id (int), title (varchar), wiki_id (int), content (medblob)
    """

    # Database values
    DATABASE_HOST = "localhost"
    DATABASE_USER = ""
    DATABASE_PASSWD = ""
    DATABASE_NAME = "wikimap"
    INDEX_TABLE = "wiki_index_mini"


    def __init__(self, dbHost=DATABASE_HOST, dbUser=DATABASE_USER, dbPasswd=DATABASE_PASSWD,
                 dbName=DATABASE_NAME, indexTable=INDEX_TABLE):
        """
        Initialize the database and cursor
        :param dbHost:
        :param dbUser:
        :param dbPasswd:
        :param dbName:
        :param indexTable:
        """

        # Initialize the database connection and create a new indexTable if necessary
        # Open connection to database wikimap and set proper encoding to UTF-8
        self.database = MySQLdb.connect(host=dbHost, user=dbUser, passwd=dbPasswd, db=dbName)
        self.database.set_character_set('utf8')
        self.database.autocommit(True)

        # Open cursor and set index table name
        self.cursor = self.database.cursor()
        self.indexTable = indexTable

    def resetTable(self):
        """
        Drop current indexTable and re-create it
        """
        try:
            self.cursor.execute("DROP TABLE IF EXISTS %s" % self.indexTable)
            self.cursor.execute("CREATE TABLE %s (id INT(10) UNSIGNED NOT NULL AUTO_INCREMENT, PRIMARY KEY(id), "
                                "title VARCHAR(255) CHARACTER SET utf8, wiki_id INT, content MEDIUMBLOB);"
                                % self.indexTable)
        except:
            print "POOP, A DATABASE ERROR"
            print traceback.format_exc()

    def closeTable(self):
        """
        Close the database
        """
        self.cursor.close()
        self.database.close()

    def storeWikiPage(self, wikiPage):
        """
        Store a WikiPage object into a new row
        """
        sql = "INSERT INTO " + self.indexTable + " (`title`, `wiki_id`, `content`) VALUES (%s, %s, %s);"
        self.cursor.execute(sql, (wikiPage.title, wikiPage.id, wikiPage.text))

    def getWikiPage(self, rowId):
        """
        Read Index table and return a WikiPage object of row with given id if available
        """
        self.cursor.execute("SELECT title, wiki_id, content FROM %s WHERE id=%s;" % (self.indexTable, rowId))
        row_data = self.cursor.fetchone()
        if not row_data or len(row_data) != 3:
            print "Found nothing for row %d" % rowId
            return None
        else:
            return WikiPage(row_data[0].decode('utf8'), row_data[1], row_data[2].decode('utf8'))

    def getMaxWikiId(self):
        """
        Return the largest WikiId stored in the Index table
        Used to determine the last article added, helps when restarting the indexing process
        """
        self.cursor.execute("SELECT wiki_id FROM %s ORDER BY wiki_id DESC LIMIT 0, 1;" % self.indexTable)
        max_id = self.cursor.fetchone()
        if max_id:
            return max_id[0]
        else:
            return -1

    def getMaxRowId(self):
        """
        Return the maximum number of items in the Index table by finding the highest row id
        """
        self.cursor.execute("SELECT id FROM %s ORDER BY id DESC LIMIT 0, 1;" % self.indexTable)
        max_id = self.cursor.fetchone()
        if max_id:
            return max_id[0]
        else:
            return 0
