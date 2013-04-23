#!/usr/bin/env python
""" 

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

    def setUp(self):
        self.redis = _initialize_engine_redis()
        self.spider = _setup_spider()

    def testMapperOutput(self):
        """Test analysis ouput from parallelspider mapper."""
        pass
        #final_output = _generate_mapper_output(self.mapper)
        # Only looking at start and end, since easier to compare on failure
        #self.assertEqual(final_output[0:100], _get_results('mapper')[0:100])
        #self.assertEqual(final_output[-100:], _get_results('mapper')[-100:])

    def testNewLinkOutput(self):
        """Test new links are generated and stored correctly in Engine Redis."""
        pass
        #_generate_mapper_output(self.mapper)
        #new_links = _get_fake_base_id() + "::new_links"
        #link_output = str(self.redis.smembers(new_links))
        #self.assertEqual(link_output[0:100], _get_results('new_links')[0:100])
        #self.assertEqual(link_output[-100:], _get_results('new_links')[-100:])

# Test output is none

# Test newlinks

# Test bad parameters


###############################################################################
### Redis Initialization
###############################################################################
def _start_engine_redis():
    """Start Engine Redis with fake crawl info."""
    data.start('kvs', 'engine')

def _initialize_engine_redis():
    """Connect to Redis on 6380 and set up for test crawl."""
    r = redis.Redis('localhost', 6380)
    new_links = _get_fake_base_id() + "::new_links"
    r.delete(new_links) # clean out keys added from previous runs
    r.sadd(new_links, _test_file_path())
    config = {}
    json_config = json.dumps(config)
    r.set(_get_fake_crawl_id(), json_config)
    count = _get_fake_base_id() + "::count"
    r.set(count, 0)
    return r

def _initialize_redis_for_failure():
    """Connect to Redis, but set up a bad path for crawl file."""
    r = redis.Redis('localhost', 6380)
    new_links = _get_fake_base_id() + "::new_links"
    r.delete(new_links) # clean out keys added from previous runs
    r.sadd(new_links, "broken_path")
    config = {}
    json_config = json.dumps(config)
    r.set(_get_fake_crawl_id(), json_config)
    count = _get_fake_base_id() + "::count"
    r.set(count, 0)
    return r

def _stop_engine_redis():
    """Stop Engine Redis."""
    data.stop('kvs', 'engine')


###############################################################################
### Output Generator for Testing
###############################################################################
def _generate_output(test_type):
    """Generate output for testing."""

    redis = _initialize_engine_redis()
    mapper, reducer = _setup_map_reduce()

    if test_type == 'mapper':
        mapper_output = _generate_mapper_output(mapper)
        #test_file = ('{0}/spiderrunner_results_mapper').format(
        #    _test_results_dir())
        #with open(test_file, 'w') as f:
        #    f.write(mapper_output)
        new_links = _get_fake_base_id() + "::new_links"
        link_output = redis.smembers(new_links)
        test_file = ('{0}/spiderrunner_results_new_links').format(
            _test_results_dir())
        with open(test_file, 'w') as f:
            f.write(str(link_output))


###############################################################################
### Helper Delper Classes & Functions
###############################################################################
def _setup_spider(port=6380):
    """Create a SpiderRunner instance."""
    site_list = _test_file_path()
    redis_info = {'host': 'localhost', 'port': port}
    max_mappers = 1
    max_pages = 1
    crawl_info = _get_fake_crawl_id()
    psuedo = False
    log_info = set_logging_level('develop')
    return SpiderRunner(site_list, redis_info, max_mappers, max_pages,
                 crawl_info, psuedo, log_info)

def _get_fake_base_id():
    """Generates a base id for a crawl: site name + crawl id."""
    fake_site = 'http://www.foxnews.com/'
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
            "-g", "-G", "--generateTestOutput", 
            action="store", dest="testType", 
            help="Type of test output to generate: mapper, reduce, ...")
    (options, args) = parser.parse_args()

    if options.redis == 'start':
        _start_engine_redis()
    elif options.redis == 'stop':
        _stop_engine_redis()
    elif options.testType:
        _generate_output(options.testType)
    else: # run tests
        unittest.main()


