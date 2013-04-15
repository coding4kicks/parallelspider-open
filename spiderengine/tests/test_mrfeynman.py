#!/usr/bin/env python
"""
    Test Suite for Mr. Feynman

    TODO: handle/test PDFs?
"""

import os
import unittest
import optparse
import robotparser

import lxml.html

from spiderengine.mrfeynman import Brain


###############################################################################
### Test Cases
###############################################################################

class TestSummaryInfo(unittest.TestCase):
    """Tests Mr Feynman's processing of summary information."""

    def setUp(self):
        """Load test file and output, plus robot.txt."""
        test = 'summary'
        self.params = _load_parameters()
        config = _get_config(test) 
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

class TestVisibleText(unittest.TestCase):
    """Tests Mr Feynman's processing of visible text information."""

    def setUp(self):
        """Load test file and output, plus robot.txt."""
        test = 'text'
        self.params = _load_parameters()
        config = _get_config(test) 
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

class TestHeadlineText(unittest.TestCase):
    """Tests Mr Feynman's processing of headline text information."""

    def setUp(self):
        """Load test file and output, plus robot.txt."""
        test = 'header'
        self.params = _load_parameters()
        config = _get_config(test) 
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

class TestHiddenText(unittest.TestCase):
    """Tests Mr Feynman's processing of hidden text information."""

    def setUp(self):
        """Load test file and output, plus robot.txt."""
        test = 'meta'
        self.params = _load_parameters()
        config = _get_config(test) 
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

class TestLinkText(unittest.TestCase):
    """Tests Mr Feynman's processing link text information."""

    def setUp(self):
        """Load test file and output, plus robot.txt."""
        test = 'a_tags'
        self.params = _load_parameters()
        config = _get_config(test) 
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

class TestAllLinks(unittest.TestCase):
    """Tests Mr Feynman's processing of all link information."""

    def setUp(self):
        """Load test file and output, plus robot.txt."""
        test = 'all_links'
        self.params = _load_parameters()
        config = _get_config(test) 
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

class TestExternalLinks(unittest.TestCase):
    """Tests Mr Feynman's processing of external link information."""

    def setUp(self):
        """Load test file and output, plus robot.txt."""
        test = 'external_links'
        self.params = _load_parameters()
        config = _get_config(test) 
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

class TestWordContext(unittest.TestCase):
    """Tests Mr Feynman's processing of context information."""

    def setUp(self):
        """Load test file and output, plus robot.txt."""
        test = 'context_search'
        self.params = _load_parameters()
        config = _get_config(test) 
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

class TestSynonymRings(unittest.TestCase):
    """Tests Mr Feynman's processing of synonym rings."""

    def setUp(self):
        """Load test file and output, plus robot.txt."""
        test = 'wordnet_lists'
        self.params = _load_parameters()
        config = _get_config(test) 
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

class TestXpathSelectors(unittest.TestCase):
    """Tests Mr Feynman's processing of XPath selectors."""

    def setUp(self):
        """Load test file and output, plus robot.txt."""
        test = 'xpath_selector'
        self.params = _load_parameters()
        config = _get_config(test) 
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

class TestCssSelectors(unittest.TestCase):
    """Tests Mr Feynman's processing of CSS selectors."""

    def setUp(self):
        """Load test file and output, plus robot.txt."""
        test = 'css_selector'
        self.params = _load_parameters()
        config = _get_config(test) 
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

class TestLinkHandling(unittest.TestCase):
    """Test Mr. Feynmans ability to correctly generate links to follow."""

    def setUp(self):
        """Custom configure params for fox, with and without robot.txt."""
        config = {}
        self.robot_txt1 = _FakeRobotText().get_empty()
        self.robot_txt2 = _FakeRobotText().get()
        self.test_file = 'fox0'
        self.test_site = 'http://www.foxnews.com/'
        self.test_page = _TestPage().get(self.test_file)
        self.brain = Brain(self.test_site, config)


    def test_robot_txt(self):
        """Test robot.txt is honored and those links are removed"""
        self.brain.analyze(self.test_page, self.test_file, self.robot_txt1)
        links_no_robot = len(self.brain.on_site_links)
        self.brain.analyze(self.test_page, self.test_file, self.robot_txt2)
        links_with_robot = len(self.brain.on_site_links)
        self.assertTrue(links_with_robot < links_no_robot)

    def test_onsite_links(self):
        """Test correct link generation of onsite links"""
        test_path = ('{0}/{1}_results_links_int').format(
            _test_results_dir(), self.test_file)
        with open(test_path) as f:
            link_results = f.read()
        self.brain.analyze(self.test_page, self.test_file, self.robot_txt2)
        self.assertEqual(link_results, str(self.brain.on_site_links))

    def test_offsite_links(self):
        """Test correct link generation of offsite links"""
        test_path = ('{0}/{1}_results_links_ext').format(
            _test_results_dir(), self.test_file)
        with open(test_path) as f:
            link_results = f.read()
        self.brain.analyze(self.test_page, self.test_file, self.robot_txt2)
        self.assertEqual(link_results, str(self.brain.off_site_links))


class TestSpeed(unittest.TestCase):
    """Tests speed of Mr Feynman by analyzing 51 documents."""

    def setUp(self):
        """Initialize all brains for all analysis types"""

        self.robots_txt = _FakeRobotText().get()
        config = _get_config('all')
        self.site_brains = _setup_brains(config)
        
    def test_speed(self):
        """Run all analysis types on all test files."""

        for file_name in os.listdir(_test_pages_dir()):

            # un/comment to turn on/off speed test
            continue

            # Brain is filename minus number on the end
            brain = self.site_brains[file_name[:-1]]
            file_path = _test_pages_dir() + '/' + file_name
            page = lxml.html.parse(file_path)       
            mapper_output = brain.analyze(page, file_name, self.robots_txt)
            sorter_output = _sort_output(mapper_output)
            reducer_output = _process_output(sorter_output, brain) 
            #print reducer_output


###############################################################################
### Output Generator for Testing
###############################################################################
def generate_output(test_type, output_type):
    """
    Generate new test output for map and reduce for all analysis types.

    Creates or modifies a file of the appropriate result type based upon
    a run of Mr. Feynman.  Use to create new result test files when add 
    features.  Check visualy and by running the larger system that the new
    output works, then generate new test files for test coverage.
    
    Args:
        test_type - analysis test type to generate: 'summary', 'test', ...
        output_type - output type to generate: 'map' or 'red'  
    """

    params = _load_parameters()
    config = _get_config(test_type) 
    brain = Brain(params['test_site'], config)

    if output_type == 'map':
        test_file = ('{0}/{1}_results_{2}_map').format(
            _test_results_dir(), params['test_file'], test_type)
        with open(test_file, 'w') as f:
            final_output = _analyze(brain, params)
            f.write(final_output)

    if output_type == 'red':
        test_file = ('{0}/{1}_results_{2}_red').format(
            _test_results_dir(), params['test_file'], test_type)
        with open(test_file, 'w') as f:
            final_output = _process(brain, params)
            f.write(final_output)
            print final_output

def generate_links(link_type=None):
    """Display/Save links generated by Mr. Feynman for testing."""
    config = {}
    robot_txt = _FakeRobotText().get()
    #robot_txt = _FakeRobotText().get_empty()
    test_file = 'fox0'
    test_site = 'http://www.foxnews.com/'
    test_page = _TestPage().get(test_file)
    brain = Brain(test_site, config)
    brain.analyze(test_page, test_file, robot_txt)

    if link_type == 'int':
        test_file = ('{0}/{1}_results_links_int').format(
            _test_results_dir(), test_file)
        with open(test_file, 'w') as f:
            f.write(str(brain.on_site_links))

    elif link_type == 'ext':
        test_file = ('{0}/{1}_results_links_ext').format(
            _test_results_dir(), test_file)
        with open(test_file, 'w') as f:
            f.write(str(brain.off_site_links))

    else: # Display Links
        print "---------------------"
        print "    On Site Links    "
        print "---------------------"
        for link in brain.on_site_links:
            print link
        print "---------------------"
        print "    Off Site Links   "
        print "---------------------"
        for link in brain.off_site_links:
            print link


###############################################################################
### Helper Delper Classes & Functions
###############################################################################

def _get_test_file():
    """Single source for test file."""
    return 'nbc0'

def _get_test_site():
    """Single source for test site."""
    return 'http://www.nbcnews.com/'

def _get_config(test_type):
    """Single source for config creation"""
    config = {}
    if test_type == 'text' or test_type == 'all':
        config['text_request'] = True
    if test_type == 'header' or test_type == 'all':
        config['header_request']  = True
    if test_type == 'meta' or test_type == 'all':
        config['meta_request']  = True
    if test_type == 'a_tags' or test_type == 'all':
        config['a_tags_request'] = True
    if test_type == 'all_links' or test_type == 'all':
        config['all_links_request'] = True
    if test_type == 'external_links' or test_type == 'all':
        config['external_links_request'] = True
    if test_type == 'context_search' or test_type == 'all':
        config['context_search_tag'] = ['twitter', 'travel', 'video']
    if test_type == 'wordnet_lists' or test_type == 'all':
        config['wordnet_lists'] = {
                'list1':['life', 'health', 'go', 'walking', 'house'],
                'list2':['news', 'fiscal', 'entertainment', 'cliff']}  
    if test_type == 'xpath_selector' or test_type == 'all':
        config['xpath_selectors'] = [
            {'selector': "//img/@alt", 'name': "image alt", 
             'analyze': True, 'css_text': False},
            {'selector': "//div[@class='story']/descendant::text()",
             'name': "test1", 'analyze': False, 'css_text': False}] 
    if test_type == 'css_selector' or test_type == 'all':
        config['css_selectors'] = [{'selector': 'p.abstr', 
            'name': "testCss", 'analyze': True, 'css_text': True}]
    #if test_type == 'paths' or test_type == 'all':
    #    config['paths_to_follow'] = [] #['worldnews']
    config['stop_list'] = _get_stop_list()
    return config

def _get_stop_list():
    """Single source for stop list."""
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
    return stop_words.split(",")

def _load_parameters():
    """Configure parameters necessary for all tests."""
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

def _process_output(sorter_output, brain):
    """Combines all output following brain processing."""
    final_output = ""
    for put in sorter_output:
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

def _setup_brains(config):
    """Initialize all brains for speed test."""
    site_brains = {  
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
    return site_brains

class _FakeRobotText(object):
    """Singleton of robot.txt used by the Brain."""

    # Borg Singleton: http://code.activestate.com/recipes/66531/
    __shared_state = {"robots_txt":"", "empty_txt":""}

    def __init__(self):
        self.__dict__ = self.__shared_state

    def get(self):
        if type(self.robots_txt) is str:
            file_path = os.path.realpath(__file__).rpartition('/')[0] \
                    + '/misc/fake_robot.txt'
            self.robots_txt = robotparser.RobotFileParser()
            self.robots_txt.set_url(file_path)
            self.robots_txt.read()            
        return self.robots_txt

    def get_empty(self):
        if type(self.empty_txt) is str:
            file_path = os.path.realpath(__file__).rpartition('/')[0] \
                    + '/misc/empty_robot.txt'
            self.empty_txt = robotparser.RobotFileParser()
            self.empty_txt.set_url(file_path)
            self.empty_txt.read()            
        return self.empty_txt

class _TestPage(object):
    """Singleton to parse test page."""

    __shared_state = {"test_file":"", "test_page": ""}

    def __init__(self):
        self.__dict__ = self.__shared_state

    def get(self, test_file):
        if self.test_file != test_file:
            test_path = _test_pages_dir() + '/' + test_file
            self.test_file = test_file
            self.test_page = lxml.html.parse(test_path)
        return self.test_page


###############################################################################
### Commad Line Gunk
###############################################################################

if __name__ == '__main__':
    """Run test or generate new output for tests."""

    usage = "usage: %prog [options]"
    parser = optparse.OptionParser(usage)

    parser.add_option(
            "-o", "-O", "--outputType", action="store", dest="outputType", 
            help="Type of output to generate: map or reduce")

    parser.add_option(
            "-t", "-T", "--testType", action="store", dest="testType", 
            help="Type of test to generate output for: summary, visible, ...")

    parser.add_option(
            "-l", "-L", "--links", action="store", dest="links", 
            help="dis displays links, int/ext saves output")

    (options, args) = parser.parse_args()

    # If testType then generate output 
    if options.testType:
        generate_output(options.testType, options.outputType)
    elif options.links:
        generate_links(options.links)
    else: # run tests
        unittest.main()
