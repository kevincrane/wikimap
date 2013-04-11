import unittest
from articleLinkParser import extractLinks
from page_parser import WikiPage

__author__ = 'kevin'


class ArticleLinkParserTest(unittest.TestCase):
    """
    Test cases for articleLinkParser
    """

    def test_basic(self):
        """
        Test the recognition of a very basic text
        [[Page Title]]
        """
        text = "[[Cats]] are the [[shit]] and everyone knows it."
        wiki_page = WikiPage("Test 1", 1, text)

        correct_links = {'Cats', 'shit'}
        found_links = extractLinks(wiki_page)
        self.assertSetEqual(found_links, correct_links)

    def test_empty(self):
        """
        Test the a page with no links
        """
        text = "No one put any links inside me!"
        wiki_page = WikiPage("Test 2", 2, text)

        correct_links = set()
        found_links = extractLinks(wiki_page)
        self.assertSetEqual(found_links, correct_links)

    def test_alt_text(self):
        """
        Test the recognition of alt-text values
        [[Page Title|Displayed Text]]
        """
        text = "At first, this was a play on words, as [[Abba Seafood|Abba]] is also the name of a well-known fish-" \
               "canning company in Sweden"
        wiki_page = WikiPage("Test 3", 3, text)

        correct_links = {'Abba Seafood'}
        found_links = extractLinks(wiki_page)
        self.assertSetEqual(found_links, correct_links)

    def test_cat_text(self):
        """
        Test the recognition of category-text values
        [[Page Title#Displayed Text]]
        """
        text = "Sometimes I worry about [[Supermajority#Majority of the entire membership]]"
        wiki_page = WikiPage("Test 4", 4, text)

        correct_links = {'Supermajority'}
        found_links = extractLinks(wiki_page)
        self.assertSetEqual(found_links, correct_links)

    def test_files(self):
        """
        Test ignoring of embedded files
        [[File:some-pic.jpg]]
        Is that embedded link in the 'File:' tag an issue? Should probably check that.
        """
        text = """Anna Kournikova was a [[Russian]] I think, and she played tennis.
[[File:Kournikova-Hingis-SYD-1.jpg|thumb|300px|right|Kournikova (left) with doubles partner Martina Hingis.]]
While [[Kournikova]] had a successful singles season, she was even more successful in doubles.
        """
        wiki_page = WikiPage("Test 5", 5, text)

        correct_links = {'Russian', 'Kournikova'}
        found_links = extractLinks(wiki_page)
        self.assertSetEqual(found_links, correct_links)

    def test_categories(self):
        """
        Test ignoring of embedded categories
        [[Category:some-pic.jpg]]
        """
        text = "Other commonly received and repeated types of [[Athena]] in sculpture may be found in [[:Category:" \
               "Athena types|this list]] or fun stuff like [[Category:Fun Stuff|these categories!]]."
        wiki_page = WikiPage("Test 6", 6, text)

        correct_links = {'Athena'}
        found_links = extractLinks(wiki_page)
        self.assertSetEqual(found_links, correct_links)

    def test_end_sections(self):
        """
        Test ignoring of common ending sections
        ==References== (also possibly ==External Links==)
        """
        text = """Done Talking.
        ==References==
        [[My references]]
        """
        wiki_page = WikiPage("Test 7", 7, text)

        correct_links = set()
        found_links = extractLinks(wiki_page)
        self.assertSetEqual(found_links, correct_links)

    def test_small_example(self):
        """
        Test full page with several things present.
        """
        text = """==Events in August==
[[August]] is a boring month. Nothing fun in [[August]]. School I guess.
[[File:Les Tres Riches Heures du duc de Berry aout.jpg|right|thumb|August, from the Tres Riches Heures du Duc de Berry showing a group of travelers]]
* In the [[neopaganism|neopagan]] [[wheel of the year]] August begins at or near [[Lughnasadh#Location]] (also known as Lammas) in the [[northern hemisphere]] and [[Imbolc]] (also known as Candlemas) in the [[southern hemisphere]].
==External links==
[[Some link]]
[[Another link|Not a fun link]]
        """
        wiki_page = WikiPage("Test 7", 7, text)

        correct_links = {'August', 'neopaganism', 'wheel of the year', 'Lughnasadh', 'northern hemisphere',
                         'Imbolc', 'southern hemisphere'}
        found_links = extractLinks(wiki_page)
        self.assertSetEqual(found_links, correct_links)


if __name__ == '__main__':
    unittest.main()
