import MySQLdb
import traceback

__author__ = 'kevin'


class LinksModel:
    """
    Database model to play with the Links DB table of WikiMap (MySQL)
    Columns: id (int), index_id_from (int), link_to (varchar)
    """

    # Database values
    DATABASE_HOST = "localhost"
    DATABASE_USER = ""
    DATABASE_PASSWD = ""
    DATABASE_NAME = "wikimap"
    LINKS_TABLE = "wiki_links_mini"


    def __init__(self, dbHost=DATABASE_HOST, dbUser=DATABASE_USER, dbPasswd=DATABASE_PASSWD,
                 dbName=DATABASE_NAME, linksTable=LINKS_TABLE):
        """
        Initialize the database and cursor
        :param dbHost:
        :param dbUser:
        :param dbPasswd:
        :param dbName:
        :param linksTable:
        """

        # Initialize the database connection and create a new indexTable if necessary
        # Open connection to database wikimap and set proper encoding to UTF-8
        self.database = MySQLdb.connect(host=dbHost, user=dbUser, passwd=dbPasswd, db=dbName)
        self.database.set_character_set('utf8')
        self.database.autocommit(True)

        # Open cursor and set table names
        self.cursor = self.database.cursor()
        self.linksTable = linksTable

    def resetTable(self):
        """
        Drop current linksTable and re-create it
        """
        try:
            self.cursor.execute("DROP TABLE IF EXISTS %s" % self.linksTable)
            self.cursor.execute("CREATE TABLE %s (id INT(10) UNSIGNED NOT NULL AUTO_INCREMENT, PRIMARY KEY(id), "
                                "index_id_from INT(10) UNSIGNED NOT NULL, link_to VARCHAR(255) CHARACTER SET utf8);"
                                % self.linksTable)
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

    def storeLinks(self, indexId, links):
        """
        Receives an index id (corresponds to row in Index table) and a list of links associated with that article
        Serialize the list to a JSON string and insert into Links table
        """
        # TODO: Uncomment the next three lines if inserting a new row for each link is too crazy
        # pickledLinks = json.dumps(list(links))
        # sql = "INSERT INTO " + self.linksTable + " (`index_id`, `links_from`) VALUES (%s, %s);"
        # self.cursor.execute(sql, (indexId, pickledLinks))

        self.database.autocommit(False)
        if len(links) > 2:
            for link in links:
                # wikiId = self.getWikiId(link)
                # if wikiId > 0:
                # print "Root ID %d: The article '%s' has a wiki id of %d" % (indexId, link, self.getWikiId(link))
                sql = "INSERT INTO " + self.linksTable + " (`index_id_from`, `link_to`) VALUES (%s, %s);"
                self.cursor.execute(sql, (indexId, link))
            self.database.commit()
        self.database.autocommit(True)

    def getMaxIndexId(self):
        """
        Return the largest index row ID stored in the Links table
        Used to determine last article added to DB
        """
        self.cursor.execute("SELECT index_id_from FROM %s ORDER BY index_id_from DESC LIMIT 0, 1;" % self.linksTable)
        max_id = self.cursor.fetchone()
        if max_id:
            return max_id[0]
        else:
            return -1
