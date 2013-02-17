import MySQLdb
import re
from page_parser import WikiPage

# Database values
DATABASE_HOST = "localhost"
DATABASE_USER = ""
DATABASE_PASSWD = ""
DATABASE_NAME = "wikimap"
INDEX_TABLE_NAME = "wiki_index_small"

# Patterns to find end of main wiki article
reference_pattern = re.compile('=+\s?References\s?=+')
extlink_pattern = re.compile('=+\s?External links\s?=+')


def initDB():
    """
    Initialize and return the database connection
    """
    database = MySQLdb.connect(host=DATABASE_HOST, user=DATABASE_USER, passwd=DATABASE_PASSWD, db=DATABASE_NAME)
    return database


def getArticleCount(cursor):
    """
    Return the maximum number of items in the DB by finding the highest row id
    """
    cursor.execute("SELECT id FROM %s ORDER BY id DESC LIMIT 0, 1;" % INDEX_TABLE_NAME)
    max_id = cursor.fetchone()
    if max_id:
        return max_id[0]
    else:
        return 0


def getWikiPage(cursor, rowId):
    """
    Read DB and return a WikiPage object of row with given id if available
    """
    cursor.execute("SELECT title, wiki_id, content FROM %s WHERE id=%d;" % (INDEX_TABLE_NAME, rowId))
    row_data = cursor.fetchone()
    if not row_data or len(row_data) != 3:
        print "Found nothing for row " + str(rowId)
        return None
    else:
        return WikiPage(row_data[0].decode('utf8'), row_data[1], row_data[2].decode('utf8'))


def extractLinks(wikiPage):
    """
    Takes a WikiPage object as an argument
    Returns a list of all valid links found within the current article
    """
    text = wikiPage.text
    links = set()

    # End string at Reference or External Links section if possible
    reference_match = reference_pattern.search(text)
    if reference_match:
        text = text[:reference_match.start()]
    else:
        extlink_match = extlink_pattern.search(text)
        if extlink_match:
            text = text[:extlink_match.start()]

    # Start iteratively hunting for links
    link_start = text.find("[[")
    while link_start != -1:
        # Ignore links that start with 'File:'
        if text[link_start+2 : link_start+7] == "File:":
            link_end = link_start
        else:
            # Find first matching closing bracket pair
            link_end = text.find("]]", link_start)
            new_link = text[link_start+2 : link_end]

            # Remove alternate display text
            alt_text = new_link.find("|")
            if alt_text > 0:
                new_link = new_link[:alt_text]

            # Add new link to current list of links
            links.add(new_link)
        # Edit string to remove previous link
        text = text[link_end+2:]
        link_start = text.find("[[")
    return links



# Main Method
if __name__ == "__main__":
    # Initialize database
    db = initDB()
    dbc = db.cursor()

    total_articles = 0
    total_links = 0

    # Find number of possible objects in DB
    count = getArticleCount(dbc)

    # Fetch every possible row in the database
    for rowId in range(count):
        wiki_page = getWikiPage(dbc, rowId + 1)
        if wiki_page:
            links = extractLinks(wiki_page)
            total_articles += 1
            total_links += len(links)
            print "Num links within %s: %d" % (wiki_page.title, len(links))

    # Show off the output
    print ""
    print "Total articles:  %d" % total_articles
    print "Total links:     %d" % total_links
    print "Avg links/art:   %f" % (1.0 * total_links / total_articles)

    # Close the DB and go home
    dbc.close()
    db.close()