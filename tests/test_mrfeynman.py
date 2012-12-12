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
        
        
    def test_parser(self):
        """Test both the mapper and reducer."""

        os.chdir("testpages")
        for file_name in os.listdir("."):

            # Limit input to one doc for testing
            if file_name != "nbc0":
                continue

            # Brain is filename minus number on the end
            brain = self.site_brains[file_name[:-1]]

            # Parse the page with lxml.html
            page = lxml.html.parse(file_name)
        
            # Set up output header
            print
            print "-----------------------"
            print file_name
            print "-----------------------"

            # Analyze the parsed output
            output = brain.analyze(page, file_name)
            
            ### TEST MAPPER OUTPUT ###
            #for put in output:
            #    print put
                #pass


            ### SET UP FOR REDUCER ###

            # skip if no output
            if not output:
                continue

            # sort the output
            sorted_out = sorted(output)

            # split the sorted output based upon key types
            # necessary since different value sizes for key type
            total_out = [] # list to hold outputs for each key type
            mini_out = [] # list to hold each type's keys
            previous_key_type = sorted_out[0][0][0:4]
            for out in sorted_out:
                key_type = out[0][0:4]
                if key_type == previous_key_type:
                    mini_out.append(out)
                else:
                    total_out.append(mini_out)
                    mini_out = [out]
                    previous_key_type = key_type
            total_out.append(mini_out)
            
            # a list to hold the new output
            new_output = []

            for sorted_out in total_out:
                
                # Save the value of the previous key for comparison
                previous_key = sorted_out[0][0]
                key = ""
                value = []

                # A list of lists to hold the lists of values
                list_o_lists = []
               
                # determine the number of values
                length = len(sorted_out[0][1])

                # Each value should have its own list
                i = 0
                while i < length:
                    list_o_lists.append([])
                    i = i + 1
                
                # Enter the first value in list o' lists
                #value = sorted_out[0][1]
                #i = 0
                #while i < length:
                #    list_o_lists[i].append(value[i])
                #    i = i + 1

                # For each instance of the same key combine values into lists
                for out in sorted_out:
                    key, value = out
                    i = 0
                    item = []
                    while i < length:
                        item.append(value[i])
                        i = i + 1
                      
                    # If the key is the same just add items to list
                    if key == previous_key:
                        i = 0
                        while i < length:
                            list_o_lists[i].append(item[i])
                            i = i + 1

                    # If key is different, output new key_value and reset lists
                    else:
                        value = []
                        i = 0
                        while i < length:
                            value.append(list_o_lists[i])
                            i = i + 1
                        key_value = (previous_key, value)
                        new_output.append(key_value)
                        previous_key = key
                        list_o_lists = []
                        i = 0
                        while i < length:
                            list_o_lists.append([item[i]])
                            i = i + 1

                # Clean up last one
                value = []
                i = 0
                while i < length:
                    value.append(list_o_lists[i])
                    i = i + 1
                key_value = (key, value)
                new_output.append(key_value)

            # Test mapper output processed correctly
            #print "new output --------------"
            #for out in new_output:
            #    print out
              
            # Process key value pairs
            for put in new_output:
                red_output = brain.process(put[0], put[1])
                print red_output

            print "what up crew"

if __name__ == '__main__':
    unittest.main()

    
    
