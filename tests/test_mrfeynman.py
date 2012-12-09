#!/usr/bin/env python
"""
    test_parser - a test for the parser ;)

    needs test pages to parse
    TODO: handle/test PDFs
"""

import os
import unittest
import lxml.html
import lxml

from parallelspider.mrfeynman import Brain

class TestMrFeynman(unittest.TestCase):
    """
    Tests mrfeynman on 50 documents
    """
    def setUp(self):
        
        """Initialize the brains"""

        # Test with path: ford, fox
        # Test with subdomain: nasa
        ### Test various configurations of config
        self.site_brains = {  
            "cnn": Brain("http://www.cnn.com/"),
            "dhs": Brain("http://www.dhs.gov/"),
            "drudge": Brain("http://www.drudgereport.com/"),
            "fed": Brain("http://www.federalreserve.gov/"),
            "ford": Brain("http://www.ford.com/help/sitemap/"),
            "fox": Brain("http://www.foxnews.com/us/index.html"),
            "ge": Brain("http://www.ge.com/"),
            "github": Brain("https://github.com/"),
            "gm": Brain("http://www.gm.com/"),
            "google": Brain("http://www.google.com/intl/en/about/"),
            "hn": Brain("http://news.ycombinator.com/"),
            "huff": Brain("http://www.huffingtonpost.com/"),
            "microsoft": Brain("http://www.microsoft.com/en-us/default.aspx"),
            "mish": Brain("http://globaleconomicanalysis.blogspot.com/"),
            "nasa": Brain("http://women.nasa.gov/"),
            "navy": Brain("http://www.navy.mil/"),
            "nbc": Brain("http://www.nbcnews.com/"),
            "reddit": Brain("http://www.reddit.com/"),
            "wh": Brain("http://www.whitehouse.gov/"),
            "wiki": Brain("http://www.wikipedia.org/")}

        #self.brain = mrfeynman.Brain()
        
        
    def test_parser(self):

        os.chdir("testpages")
        for file_name in os.listdir("."):

            #if file_name != "nbc0":
            #    continue

            brain = self.site_brains[file_name[:-1]]
            ### blank parser
            page = lxml.html.parse(file_name)

            print
            print "-----------------------"
            print file_name
            print "-----------------------"
            brain.analyze(page, file_name)
            output = brain.output
            for put in output:
                print put
                #pass
            #print brain.on_site_links
            #print brain.off_site_links
            #print brain.site_domain
            #print brain.site_url

        print "what up crew"

if __name__ == '__main__':
    unittest.main()

    
    
