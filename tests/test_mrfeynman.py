#!/usr/bin/env python
"""
    test_parser - a test for the parser ;)

    needs test pages to parse
    TODO: handle/test PDFs?
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

        # Set up configuration file
        config = {}
        
        # Config variables
        config['text_request'] = True
        config['header_request']  = True
        config['meta_request']  = True
        config['a_tags_request'] = True
        config['all_links_request'] = True
        config['external_links_request'] = True
        config['context_search_tag'] = ['dream']
        config['wordnet_lists'] = {
                'list1':['word', 'something', 'loser'],
                'list2':['news', 'journalism', 'great']}        
        config['xpath_selectors'] = [
            {'selector': "//img/@alt", 'name': "image alt", 'analyze': False, 'css_text': False},
            {'selector': "//div[@class='story']/descendant::text()", 'name': "test1", 'analyze': False, 'css_text': False},
            {'selector': "//a[@href='http://video.msnbc.msn.com/nightly-news/50032975/']/text()", 'name': "test2", 'analyze': True, 'css_text': False},
            {'selector': "//div[@id='tbx-29618997']/div/h2/text()", 'name': "test3", 'analyze': False, 'css_text': False}] 
        config['css_selectors'] = [{'selector': 'p.abstr', 'name': "testCss", 'analyze': True, 'css_text': True}]

        config['paths_to_follow'] = [] #['worldnews'] # list of paths to follow (or domains)

        # Hardcode stop words, later load from pickle config file
        stop_words = ("a,about,above,after,again,against,all,am,an,and,any,"+
            "are,aren't,as,at,be,because,been,before,being,below,between,"+
            "both,but,by,can't,cannot,could,couldn't,did,didn't,do,does,"+
            "doesn't,doing,don't,down,during,each,few,for,from,further,had,"+
            "hadn't,has,hasn't,have,haven't,having,he,he'd,he'll,he's,her,"+
            "here,here's,hers,herself,him,himself,his,how,how's,i,i'd,i'll,"+
            "i'm,i've,if,in,into,is,isn't,it,it's,its,itself,let's,me,more,"+
            "most,mustn't,my,myself,no,nor,not,of,off,on,once,only,or,other,"+
            "ought,our,ours,ourselves,out,over,own,same,shan't,she,she'd,"+
            "she'll,she's,should,shouldn't,so,some,such,than,that,that's,"+
            "the,their,theirs,them,themselves,then,there,there's,these,they,"+
            "they'd,they'll,they're,they've,this,those,through,to,too,under,"+
            "until,up,very,was,wasn't,we,we'd,we'll,we're,we've,were,weren't,"+
            "what,what's,when,when's,where,where's,which,while,who,who's,whom,"+
            "why,why's,with,won't,would,wouldn't,you,you'd,you'll,you're,"+
            "you've,your,yours,yourself,yourselves,&,<,>,^,(,)")

        config['stop_list'] = stop_words.split(",")


        # Test with path: ford, fox
        # Test with subdomain: nasa
        ### Test various configurations of config
        self.site_brains = {  
            "cnn": Brain("http://www.cnn.com/", config),
            "dhs": Brain("http://www.dhs.gov/", config),
            "drudge": Brain("http://www.drudgereport.com/", config),
            "fed": Brain("http://www.federalreserve.gov/", config),
            "ford": Brain("http://www.ford.com/help/sitemap/", config),
            "fox": Brain("http://www.foxnews.com/us/index.html", config),
            "ge": Brain("http://www.ge.com/", config),
            "github": Brain("https://github.com/", config),
            "gm": Brain("http://www.gm.com/", config),
            "google": Brain("http://www.google.com/intl/en/about/", config),
            "hn": Brain("http://news.ycombinator.com/", config),
            "huff": Brain("http://www.huffingtonpost.com/", config),
            "microsoft": Brain("http://www.microsoft.com/en-us/default.aspx", config),
            "mish": Brain("http://globaleconomicanalysis.blogspot.com/", config),
            "nasa": Brain("http://women.nasa.gov/", config),
            "navy": Brain("http://www.navy.mil/", config),
            "nbc": Brain("http://www.nbcnews.com/", config),
            "reddit": Brain("http://www.reddit.com/", config),
            "wh": Brain("http://www.whitehouse.gov/", config),
            "wiki": Brain("http://www.wikipedia.org/", config)}
        
        
    def test_parser(self):
        """Test both the mapper and reducer."""

        os.chdir("testpages")
        for file_name in os.listdir("."):

            # Limit input to one doc for testing
            #if file_name != "nbc0":
            #    continue

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
                value_list = []

                # A list of lists to hold the lists of values
                #list_o_lists = []
               
                # determine the number of values
                #length = len(sorted_out[0][1])

                # Each value should have its own list
                #i = 0
                #while i < length:
                #    list_o_lists.append([])
                #    i = i + 1

                # For each instance of the same key combine values
                for out in sorted_out:
                    key, value = out
                    #i = 0
                    #item = []
                    #while i < length:
                    #    item.append(value[i])
                    #    i = i + 1
                      
                    # If the key is the same just add items to list
                    if key == previous_key:
                        value_list.append(value)
                        #i = 0
                        #while i < length:
                        #    list_o_lists[i].append(item[i])
                        #    i = i + 1

                    # If key is different, output new key_value, reset lists
                    else:
                        #value = []
                        #i = 0
                        #while i < length:
                        #    value.append(list_o_lists[i])
                        #    i = i + 1
                        key_value = (previous_key, value_list)
                        new_output.append(key_value)
                        previous_key = key
                        value_list = [value]
                        #list_o_lists = []
                        #i = 0
                        #while i < length:
                        #    list_o_lists.append([item[i]])
                        #    i = i + 1

                # Clean up last one
                #value = []
                #i = 0
                #while i < length:
                #    value.append(list_o_lists[i])
                #    i = i + 1
                key_value = (key, value_list)
                new_output.append(key_value)

            # Test mapper output processed correctly
            #for out in new_output:
            #    print out
              
            # Process key value pairs
            for put in new_output:

                self.assertEqual(len(put), 2)
                red_output = brain.process(put[0], put[1])
                print red_output

            print "What up crew!"

if __name__ == '__main__':
    unittest.main()

    
    
