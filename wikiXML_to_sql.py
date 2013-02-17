import sys
import traceback
import page_parser
import MySQLdb


__author__ = 'kevin'

#TODO: learn how to unit test this shit; maybe run loadArticle with its own WikiPage, check output matches text


# Database values
DATABASE_HOST = "localhost"
DATABASE_USER = ""
DATABASE_PASSWD = ""
DATABASE_NAME = "wikimap"
INDEX_TABLE_NAME = "wiki_index_mini"
DEFAULT_WIKI_XML = "miniwiki.xml"

# Change this number to the last wiki_id value added to the database; used for adding articles incrementally
# START_ID = 46288
START_ID = 0


#TODO: Put all the DB stuff in its own method
# Initialize the database connection and create a new table if necessary
# Open connection to database wikimap and set proper encoding to UTF-8
database = MySQLdb.connect(host=DATABASE_HOST, user=DATABASE_USER, passwd=DATABASE_PASSWD, db=DATABASE_NAME)
database.set_character_set('utf8')
database.autocommit(True)
cursor = database.cursor()

# If you're starting the wiki index from scratch, drop the existing table and re-create it
if START_ID == 0:
    try:
        cursor.execute("DROP TABLE IF EXISTS %s" % INDEX_TABLE_NAME)
        cursor.execute("CREATE TABLE %s (id INT(10) UNSIGNED NOT NULL AUTO_INCREMENT, PRIMARY KEY(id), "
                       "title VARBINARY(255), wiki_id INT, content MEDIUMBLOB);" % INDEX_TABLE_NAME)
    except:
        print "POOP, A DATABASE ERROR"
        print traceback.format_exc()
        pass


def loadArticle(wikiPage, dbc=cursor, start_id=START_ID):
    """
    Load the current article into a MySQL table
    Argument: Receives a page_parser.WikiPage object
    Used as callback method with WikiDumpHandler
    :param dbc:
    :param start_id:
    :param wikiPage:
    """
    # If the current WikiPage has been added already, skip it
    if int(wikiPage.id) <= start_id:
        return

    # Generate SQL query to insert new WikiPage row
    sql = "INSERT INTO " + INDEX_TABLE_NAME + " (`title`, `wiki_id`, `content`) VALUES (%s, %s, %s);"
    dbc.execute(sql, (wikiPage.title, wikiPage.id, wikiPage.text))
    print "Inserted " + wikiPage.__str__() + "; length: " + str(len(wikiPage.text))


# Main Method
if __name__ == "__main__":
    # Set name of XML file to read (with default)
    wiki_xml = DEFAULT_WIKI_XML
    if len(sys.argv) == 2:
        wiki_xml = sys.argv[1]

    # Generate a wiki xml parser, open the file, and store each article in DB
    wiki_parser = page_parser.createWikiParser(loadArticle)
    wiki_parser.parse(open(wiki_xml))

    # Close the database
    cursor.close()
    database.close()