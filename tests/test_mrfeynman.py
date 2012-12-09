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

            if file_name != "nbc0":
                continue

            brain = self.site_brains[file_name[:-1]]
            ### blank parser
            page = lxml.html.parse(file_name)

            print
            print "-----------------------"
            print file_name
            print "-----------------------"
            brain.analyze(page, file_name)
            output = brain.output

            # TEST MAPPER OUTPUT
            #for put in output:
            #    print put
                #pass
            #print brain.on_site_links
            #print brain.off_site_links
            #print brain.site_domain
            #print brain.site_url

            # SET UP FOR REDUCER

            # sort the output
            sorted_out = sorted(output)

            # determine the number of values
            length = len(sorted_out[0][1])

            # a list to hold the new output for the reducer
            new_output = []
            previous_key = ""

            # initialize a list of lists to hold values
            list_o_lists = []
            i = 0
            while i < length:
                list_o_lists.append([])
                i = i + 1

            # for each instance of the same key combine values into lists
            for out in sorted_out:
                key, value = out
                item0, item1, item2, item3 = value

                # if key is same just add items to list
                if key == previous_key:
                    i = 0
                    while i < length:
                        list_o_lists[i].append(eval("item" + str(i)))
                        i = i + 1

                # if key is different, output new key_value and reset lists
                else:
                    previous_key = key
                    value = (list_o_lists[0], list_o_lists[1], 
                             list_o_lists[2], list_o_lists[3])
                    key_value = (key, value)
                    new_output.append(key_value)

                    list_o_lists = []
                    i = 0
                    while i < length:
                        list_o_lists.append([eval("item" + str(i))])
                        i = i + 1

            for out in new_output:
                print out
                   
            print "what up crew"

if __name__ == '__main__':
    unittest.main()

    
    
