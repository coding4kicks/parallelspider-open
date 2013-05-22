#!/usr/bin/env python
"""
Test spider_runner.py

Tests SpiderRunner to determine if 
    1) New links are parsed and uploaded to Engine Redis correctly
    2) Dumbo psuedo, distributed, and file upload commands are correct
    3) Brain process with no emit returns None
    4) New link key expiration set
    5) Input file is created correctly

TODO: handle failures
"""

import os
import json
import urllib
import unittest
import optparse

import redis

from spiderdepot import data
from spiderengine.spiderrunner import SpiderRunner, set_logging_level 


###############################################################################
### Test Cases
###############################################################################
class TestSpiderRunner(unittest.TestCase):
    """Test for success."""

    def setUp(self):
        """Intialize Engine Redis and SpiderRunner."""
        self.redis = _initialize_engine_redis()
        self.spider = _setup_spider()

    def tearDown(self):
        """Delete input file created for parallelspider."""
        with open(_input_file(), 'w') as f:
            f.write("")

    def testNewLinkOutput(self):
        """Test new links are generated/stored correctly in Engine Redis."""
        _ = self.spider.execute()
        new_links = _get_fake_base_id() + "::new_links"
        link_output = str(self.redis.smembers(new_links))
        self.assertEqual(link_output, _get_results('new_links'))

    def testDumboCall(self):
        """Test that Dumbo is called with appropriate parameters."""
        output = self.spider.execute()
        self.assertEqual(output[0], _get_results('dumbo_cmd'))

    def testPsuedoCall(self):
        """Test that Psuedo is called with appropriate parameters."""
        output = self.spider.execute()
        self.assertEqual(output[1], _get_results('psuedo_cmd'))

    def testFileCall(self):
        """Test that file upload is called with appropriate parameters."""
        output = self.spider.execute()
        self.assertEqual(output[2], _get_results('file_cmd'))

    def testBrainOutput(self):
        """Test that brain output is None."""
        output = self.spider.execute()
        self.assertEqual(str(output[3]), _get_results('spdr_out'))

    def testInputFile(self):
        _ = self.spider.execute()
        with open(_input_file(), 'r') as f:
            out = f.read()
        self.assertEqual(out, 'mapper1\n')

    def testKeyExpirationsSet(self):
        """Test that key expirations are set to an hour."""
        _ = self.spider.execute()
        new_links = _get_fake_base_id() + "::new_links"
        self.assertTrue(self.redis.ttl(new_links) > 3500)

      
#class TestSpiderFail(unittest.TestCase):
#    """Test for failure."""
#
#    def setUp(self):
#        """Intialize Engine Redis and SpiderRunner for failure, ha ha ha."""
#        self.redis = _initialize_redis_for_failure()
#        self.spider = _setup_spider()
#
#    def tearDown(self):
#        """Delete input file created for parallelspider."""
#        with open(_input_file(), 'w') as f:
#            f.write("")
#
#    def testNewLinkOutput(self):
#        """Test new links are generated/stored correctly in Engine Redis."""
#        _ = self.spider.execute()


###############################################################################
### Redis Initialization
###############################################################################
def _start_engine_redis():
    """Start Engine Redis with fake crawl info."""
    data.start('kvs', 'engine')

def _initialize_engine_redis():
    """Connect to Redis on 6380 and set up for test crawl."""
    r = redis.Redis('localhost', 6380)
    config = {'crawl_id': _get_fake_crawl_id() }
    json_config = json.dumps(config)
    r.set(_get_fake_crawl_id(), json_config)
    return r

def _initialize_redis_for_failure():
    """Connect to Redis, but set up a bad path for crawl file."""
    r = redis.Redis('localhost', 6380)
    config = {}
    json_config = json.dumps(config)
    r.set(_get_fake_crawl_id(), json_config)
    return r

def _stop_engine_redis():
    """Stop Engine Redis."""
    data.stop('kvs', 'engine')


###############################################################################
### Output Generator for Testing
###############################################################################
def _generate_output():
    """Generate output for testing."""

    redis = _initialize_engine_redis()
    output = _setup_spider().execute()
    new_links = _get_fake_base_id() + "::new_links"
    link_output = redis.smembers(new_links)
    test_file = ('{0}/spiderrunner_results_new_links').format(
        _test_results_dir())
    with open(test_file, 'w') as f:
        f.write(str(link_output))
    test_file = ('{0}/spiderrunner_results_dumbo_cmd').format(
        _test_results_dir())
    with open(test_file, 'w') as f:
        f.write(str(output[0]))
    test_file = ('{0}/spiderrunner_results_psuedo_cmd').format(
        _test_results_dir())
    with open(test_file, 'w') as f:
        f.write(str(output[1]))
    test_file = ('{0}/spiderrunner_results_file_cmd').format(
        _test_results_dir())
    with open(test_file, 'w') as f:
        f.write(str(output[2]))
    test_file = ('{0}/spiderrunner_results_spdr_out').format(
        _test_results_dir())
    with open(test_file, 'w') as f:
        f.write(str(output[3]))


###############################################################################
### Helper Delper Classes & Functions
###############################################################################
def _setup_spider(port=6380):
    """Create a SpiderRunner instance."""
    site_list = [_test_file_path()]
    redis_info = {'host': 'localhost', 'port': str(port)}
    max_mappers, max_pages = 1, 1
    crawl_info = _get_fake_crawl_id()
    psuedo = False
    log_info = set_logging_level('develop')
    return SpiderRunner(site_list, redis_info, max_mappers, max_pages,
                 crawl_info, psuedo, log_info, test=True)

def _get_results(test_type):
    """Load the saved test results."""
    test_path = ('{0}/spiderrunner_results_{1}').format(
            _test_results_dir(), test_type)
    with open(test_path) as f:
        test_results = f.read()
    return test_results

def _get_fake_base_id():
    """Generates a base id for a crawl: site name + crawl id."""
    #fake_site = 'http://www.foxnews.com/'
    fake_site = _test_file_path()
    fake_crawl_id = _get_fake_crawl_id()
    fake_base_id = ('{0}::{1}').format(fake_site, fake_crawl_id)
    return fake_base_id

def _get_fake_crawl_id():
    """Create a fake crawl id with all parameters fixed."""
    fake_user = "yankeecharlie"
    fake_name = "badpolitics"
    fake_time = "Fri Mar 15 2020 21:00:15 GMT-0700 (PDT)"
    fake_crawl_id = ('{0}__{1}__{2}').format(fake_user, fake_name, fake_time)
    fake_crawl_id = urllib.quote_plus(fake_crawl_id)
    return fake_crawl_id

def _test_file_path():
    """Test file to crawl."""
    return _test_pages_dir() + '/fox0'

def _test_pages_dir():
    """Return directory containing test pages"""
    return os.path.realpath(__file__).rpartition('/')[0] + '/testpages'

def _test_results_dir():
    """Return directory containing test results"""
    return os.path.realpath(__file__).rpartition('/')[0] + '/testresults'

def _input_file():
    """Constructs a path to the input file created for parallelspider."""
    phil = _get_fake_base_id().replace("/","_").replace(":","-") + ".txt"
    path = (os.path.realpath(__file__).partition('spiderengine')[0] + 
                'spiderengine/tests/jobs/')
    return path + phil



###############################################################################
### Commad Line Gook
###############################################################################
if __name__ == '__main__':
    """Run test or start/stop redis for testing."""

    usage = "usage: %prog [options]"
    parser = optparse.OptionParser(usage)

    parser.add_option(
            "-e", "-E", "--engineRedis", 
            action="store", dest="redis", 
            help="Start/Stop Engine Redis datastore with fake crawl info.")
    parser.add_option(
            "-g", "-G", "--generateOutput", 
            action="store_true", dest="genOutput", 
            help="Generate test output")
    (options, args) = parser.parse_args()

    if options.redis == 'start':
        _start_engine_redis()
    elif options.redis == 'stop':
        _stop_engine_redis()
    elif options.genOutput:
        _generate_output()
    else: # run tests
        unittest.main()


