#!/usr/bin/env python
"""
    Test Suite for Mr. Feynman

    TODO: handle/test PDFs?
"""

import os
import unittest
import robotparser
import lxml.html

from spiderengine.mrfeynman import Brain


class TestSummary(unittest.TestCase):
    """Tests Mr Feynman's processing of summary information."""

    def setUp(self):
        """Load test file and output, plus robot.txt."""
        test = 'summary'
        self.params = _load_parameters()
        config = {} # No config info for summary
        self.brain = Brain(self.params['test_site'], config)
        self.results = _get_results(self.params['test_file'], test)

    def test_analysis(self):
        """Test generation of mapper output"""
        final_output = _analyze(self.brain, self.params)
        self.assertEqual(self.results['map'], final_output)

    def test_process(self):
        """Test processing of reducer output"""
        final_output = _process(self.brain, self.params)
        self.assertEqual(self.results['red'], final_output)

# Switch to TestSpeed
class TestSpeed(unittest.TestCase):
    """Tests speed of Mr Feynman on 51 documents."""

    def setUp(self):
        """Initialize the brains"""

        self.robots_txt = _FakeRobotText().get()


        # Set up configuration file
        config = {}
        
        # Config variables
       # config['text_request'] = True
       # config['header_request']  = True
       # config['meta_request']  = True
       # config['a_tags_request'] = True
       # config['all_links_request'] = True
       # config['external_links_request'] = True
       # config['context_search_tag'] = ['dream']
       # config['wordnet_lists'] = {
       #         'list1':['word', 'something', 'loser'],
       #         'list2':['news', 'journalism', 'great']}        
       # config['xpath_selectors'] = [
       #    {'selector': "//img/@alt", 'name': "image alt", 
       #         'analyze': False, 'css_text': False},
       #    {'selector': "//div[@class='story']/descendant::text()",
       #         'name': "test1", 'analyze': False, 'css_text': False},
       #    {'selector': 
    #"//#a[@href='http://video.msnbc.msn.com/nightly-news/50032975/']/text()", 
       #     'name': "test2", 'analyze': True, 'css_text': False},
       #     {'selector': "//div[@id='tbx-29618997']/div/h2/text()", 
       #         'name': "test3", 'analyze': False, 'css_text': False}] 
       # config['css_selectors'] = [{'selector': 'p.abstr', 
       #     'name': "testCss", 'analyze': True, 'css_text': True}]

        config['paths_to_follow'] = [] #['worldnews'] 

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
            "what,what's,when,when's,where,where's,which,while,who,who's,"+
            "whom,why,why's,with,won't,would,wouldn't,you,you'd,you'll,"+
            "you're,you've,your,yours,yourself,yourselves,&,<,>,^,(,)")

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
            "microsoft": Brain("http://www.microsoft.com/en-us/default.aspx",
                config),
            "mish": Brain("http://globaleconomicanalysis.blogspot.com/",
                config),
            "nasa": Brain("http://women.nasa.gov/", config),
            "navy": Brain("http://www.navy.mil/", config),
            "nbc": Brain("http://www.nbcnews.com/", config),
            "reddit": Brain("http://www.reddit.com/", config),
            "wh": Brain("http://www.whitehouse.gov/", config),
            "wiki": Brain("http://www.wikipedia.org/", config),
            "hn": Brain("https://news.ycombinator.com/", config)}
        
        
    def test_parser(self):
        """Test both the mapper and reducer."""

        #os.chdir("testpages")
        directory = _test_pages_dir()
        #for file_name in os.listdir("."):
        for file_name in os.listdir(directory):
            # Limit input to one doc for testing
            if file_name != "nbc0":
                continue

            # Brain is filename minus number on the end
            brain = self.site_brains[file_name[:-1]]

            file_path = _test_pages_dir() + '/' + file_name
            # Parse the page with lxml.html
            #page = lxml.html.parse(file_name)
            page = lxml.html.parse(file_path)
        
            # Set up output header
            print
            print "-----------------------"
            print file_name
            print "-----------------------"

            # Analyze the parsed output
            mapper_output = brain.analyze(page, file_name, self.robots_txt)
            
            ### TEST/SAVE MAPPER OUTPUT ###
            #string = ""
            #test_file = _test_results_dir() + '/nbc0_results_summary_map'
            #with open(test_file, 'w') as f:
            #    for put in output:
            #        string += str(put)
            #    f.write(str(string))

            ### SET UP FOR REDUCER ###
            sorter_output = _sort_output(mapper_output)

            # skip if no output
            #if not output:
            #    continue

           # # sort the output
           # sorted_out = sorted(output)

           # # split the sorted output based upon key types
           # # necessary since different value sizes for key type
           # total_out = [] # list to hold outputs for each key type
           # mini_out = [] # list to hold each type's keys
           # previous_key_type = sorted_out[0][0][0:4]
           # for out in sorted_out:
           #     key_type = out[0][0:4]
           #     if key_type == previous_key_type:
           #         mini_out.append(out)
           #     else:
           #         total_out.append(mini_out)
           #         mini_out = [out]
           #         previous_key_type = key_type
           # total_out.append(mini_out)
           # 
           # # a list to hold the new output
           # new_output = []

           # for sorted_out in total_out:
           #     
           #     # Save the value of the previous key for comparison
           #     previous_key = sorted_out[0][0]
           #     key = ""
           #     value_list = []

           #     # For each instance of the same key combine values
           #     for out in sorted_out:
           #         key, value = out
           #           
           #         # If the key is the same just add items to list
           #         if key == previous_key:
           #             value_list.append(value)

           #         # If key is different, output new key_value, reset lists
           #         else:
           #             key_value = (previous_key, value_list)
           #             new_output.append(key_value)
           #             previous_key = key
           #             value_list = [value]

           #     # Clean up last one
           #     key_value = (key, value_list)
           #     new_output.append(key_value)

            # Test mapper output processed correctly
            #for out in new_output:
            #    print out
              
            # Process key value pairs
            for put in sorter_output:
                self.assertEqual(len(put), 2)
                reducer_output = brain.process(put[0], put[1])
                #print reducer_output
            #print brain.on_site_links
            print "What up crew!"

###############################################################################
### Helper Delper Classes & Functions
###############################################################################

class _FakeRobotText(object):
    """Singleton of robot.txt used by the Brain."""

    # Borg Singleton: http://code.activestate.com/recipes/66531/
    __shared_state = {"robots_txt":""}

    def __init__(self):
        self.__dict__ = self.__shared_state

    def get(self):
        if type(self.robots_txt) is str:
            self.robots_txt = robotparser.RobotFileParser()
            self.robots_txt.set_url('http://www.foxnews.com/')
            self.robots_txt.read()
        return self.robots_txt

class _TestPage(object):
    """Singleton to parse test page."""

    # Borg Singleton: http://code.activestate.com/recipes/66531/
    __shared_state = {"test_file":"", "test_page": ""}

    def __init__(self):
        self.__dict__ = self.__shared_state

    def get(self, test_file):
        if self.test_file != test_file:
            test_path = _test_pages_dir() + '/' + test_file
            self.test_file = test_file
            self.test_page = lxml.html.parse(test_path)
        return self.test_page

def _load_parameters():
    params = {}
    params['robots_txt'] = _FakeRobotText().get()
    params['test_file'] = _get_test_file()
    params['test_site'] = _get_test_site()
    params['test_page'] = _TestPage().get(params['test_file'])
    return params

def _analyze(brain, params):
    """Brain analyze mapper output."""
    mapper_output = brain.analyze(
        params['test_page'], params['test_file'], params['robots_txt'])
    final_output = _concat_output(mapper_output)
    return final_output

def _process(brain, params):
    """Brain process reducer output."""
    mapper_output = brain.analyze(
        params['test_page'], params['test_file'], params['robots_txt'])
    reducer_output = _sort_output(mapper_output)
    final_output = _process_output(reducer_output, brain)
    return final_output

def _get_test_file():
    """Single source for test file."""
    return 'nbc0'

def _get_test_site():
    """Single source for test site."""
    return 'http://www.nbcnews.com/'

def _test_pages_dir():
    """Return directory containing test pages"""
    return os.path.realpath(__file__).rpartition('/')[0] + '/testpages'

def _test_results_dir():
    """Return directory containing test results"""
    return os.path.realpath(__file__).rpartition('/')[0] + '/testresults'

def _get_results(test_file, results_type):
    """Load the saved test results."""
    test_results = {}
    test_path = ('{0}/{1}_results_{2}_map').format(
            _test_results_dir(), test_file, results_type)
    with open(test_path) as f:
        test_results['map'] = f.read()
    test_path = ('{0}/{1}_results_{2}_red').format(
            _test_results_dir(), test_file, results_type)
    with open(test_path) as f:
        test_results['red'] = f.read()
    return test_results

def _concat_output(mapper_output):
    """Combines all output from the mapper."""
    final_output = ""
    for put in mapper_output:
        final_output += str(put)
    return final_output

def _process_output(reducer_output, brain):
    """Combines all output following brain processing."""
    final_output = ""
    for put in reducer_output:
        processed_output = brain.process(put[0], put[1])
        final_output += str(processed_output) + "\n"
    return final_output

def _sort_output(map_output):
    """Sorts output for reducer."""

    sorted_out = sorted(map_output)
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
    reducer_input = []

    for sorted_out in total_out:       
        # Save the value of the previous key for comparison
        previous_key = sorted_out[0][0]
        key = ""
        value_list = []
        # For each instance of the same key combine values
        for out in sorted_out:
            key, value = out              
            # If the key is the same just add items to list
            if key == previous_key:
                value_list.append(value)
            # If key is different, output new key_value, reset lists
            else:
                key_value = (previous_key, value_list)
                reducer_input.append(key_value)
                previous_key = key
                value_list = [value]
        # Clean up last one
        key_value = (key, value_list)
        reducer_input.append(key_value)

    return reducer_input


if __name__ == '__main__':
    unittest.main()

    
    
