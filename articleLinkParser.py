import re

__author__ = 'kevin'


# Regular expressions to extract ending footers
reference_pattern = re.compile('=+\s?References\s?=+')
extlink_pattern = re.compile('=+\s?External links\s?=+')


def removeAltText(new_link):
    """
    Returns the string new_link with alt display text removed:
    e.g. new_link|alt_text -> new_link
    """
    # Remove alternate display text
    alt_index = new_link.find("|")
    if alt_index >= 0:
        new_link = new_link[:alt_index]
    return new_link


def removeCatText(new_link):
    """
    Returns the string new_link with category display text removed:
    e.g. new_link#category -> new_link
    """
    category_index = new_link.find("#")
    if category_index >= 0:
        new_link = new_link[:category_index]
    return new_link


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

            # Remove modifiers from the end of the links
            new_link = removeAltText(new_link)
            new_link = removeCatText(new_link)

            # Add new link to current list of links
            if len(new_link) > 0:
                links.add(new_link.strip())

        # Edit string to remove previous link
        text = text[link_end + 2:]
        link_start = text.find("[[")
    return links
