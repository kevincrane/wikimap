import sys
import traceback
from xml.sax import handler, make_parser
import page_parser
import MySQLdb

__author__ = 'kevin'

# Database
DATABASE_HOST = "localhost"
DATABASE_USER = "root"
DATABASE_PASSWD = "password"
DATABASE_NAME = "wikimap"
INDEX_TABLE_NAME = "wiki_index"


# Open connection to database wikimap and set proper encoding to UTF-8
#TODO: put this somewhere more formal?
database = MySQLdb.connect(host=DATABASE_HOST, user=DATABASE_USER, passwd=DATABASE_PASSWD, db=DATABASE_NAME)
database.set_character_set('utf8')
database.autocommit(True)
cursor = database.cursor()
try:
    cursor.execute("DROP TABLE IF EXISTS %s" % INDEX_TABLE_NAME)
    cursor.execute("CREATE TABLE %s (id INT NOT NULL AUTO_INCREMENT, PRIMARY KEY(id), title TEXT, wiki_id INT, "
                   "content LONGTEXT;" % INDEX_TABLE_NAME)
except:
    print "POOP, A DATABASE ERROR"
    print traceback.format_exc()
    pass


def loadArticle(wikiPage, db=database, dbc=cursor):
    """
    Load the current article into a MySQL table
    :param wikiPage:
    Argument: Receives a page_parser.WikiPage object
    Used as callback method with WikiDumpHandler
    """
    # Generate SQL query to insert new WikiPage row
    sql = "INSERT INTO " + INDEX_TABLE_NAME + " (`title`, `wiki_id`, `content`) VALUES (%s, %s, %s);"
    dbc.execute(sql, (wikiPage.title, wikiPage.id, wikiPage.text))
    print "Inserted " + wikiPage.__str__() + "; length: " + str(len(wikiPage.text))


# Main Method
if __name__ == "__main__":
    # Set name of XML file to read (with default)
    wiki_xml = "miniwiki.xml"
    if len(sys.argv) == 2:
        wiki_xml = sys.argv[1]

    # Apply the text_normalize_filter (from page_parser.py)
    wiki_parser = make_parser()
    wdh = page_parser.WikiDumpHandler(pageCallBack=loadArticle)
    filter_handler = page_parser.text_normalize_filter(wiki_parser, wdh)

    # Parse the whole XML file, storing each article in the DB
    filter_handler.parse(open(wiki_xml))

    # Close the database
    cursor.close()
    database.close()