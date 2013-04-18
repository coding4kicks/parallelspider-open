#!/usr/bin/env python
"""
    Test Suite for Parallel Spider
"""

import os
import json
import urllib
import unittest
import optparse

import redis

from spiderdepot import data
from spiderengine.parallelspider import Mapper

###############################################################################
### Test Cases
###############################################################################
class TestParallelSpider(unittest.TestCase):

    def setUp(self):
        _initialize_engine_redis()
        self.mapper = _setup_mapper()

    def testMapperOutput(self):
        final_output = _generate_mapper_output(self.mapper)
        self.assertEqual(final_output, _get_results('mapper'))

        
###############################################################################
### Redis Initialization
###############################################################################
def _start_engine_redis():
    """Start Engine Redis with fake crawl info."""
    data.start('kvs', 'engine')

def _initialize_engine_redis():
    r = redis.Redis('localhost', 6380)
    new_links = _get_fake_base_id() + "::new_links"
    r.delete(new_links) # clean out keys added from previous runs
    r.sadd(new_links, _test_file_path())
    config = {}
    json_config = json.dumps(config)
    r.set(_generate_fake_crawl_id(), json_config)
    count = _get_fake_base_id() + "::count"
    r.set(count, 0)

def _stop_engine_redis():
    """Stop Engine Redis."""
    data.stop('kvs', 'engine')

###############################################################################
### Output Generator for Testing
###############################################################################
def _generate_output(test_type):
    """Generate output for testing."""
    if test_type == 'mapper':
        _initialize_engine_redis()
        mapper = _setup_mapper()
        mapper_output = _generate_mapper_output(mapper)
        test_file = ('{0}/parallelspider_results_{1}').format(
            _test_results_dir(), test_type)
        with open(test_file, 'w') as f:
            f.write(mapper_output)
        print mapper_output

###############################################################################
### Helper Delper Classes & Functions
###############################################################################

def _setup_mapper():
    """Setup Mapper with redis info."""
    params = {'redisInfo':_set_engine_redis_info()}
    Mapper.params = params
    return Mapper()

def _generate_mapper_output(mapper):
    """Join together all mapper output for a run."""
    output = []
    for out in mapper("",""):
        output.append(out)
    return "".join(str(output))

def _get_fake_base_id():
    """Generates a base id for a crawl: site name + crawl id."""
    fake_site = 'http://www.foxnews.com/'
    fake_crawl_id = _generate_fake_crawl_id()
    fake_base_id = ('{0}::{1}').format(fake_site, fake_crawl_id)
    return fake_base_id

def _generate_fake_crawl_id():
    """Create a fake crawl id with all parameters fixed."""
    fake_user = "yankeecharlie"
    fake_name = "badpolitics"
    fake_time = "Fri Mar 15 2020 21:00:15 GMT-0700 (PDT)"
    fake_crawl_id = ('{0}__{1}__{2}').format(fake_user, fake_name, fake_time)
    fake_crawl_id = urllib.quote_plus(fake_crawl_id)
    return fake_crawl_id

def _set_engine_redis_info():
    """Sets Engine Redis info for Parallel Spider initialization."""
    engine_redis_host = 'localhost'
    engine_redis_port = 6380
    max_pages = 1
    fake_base_id = _get_fake_base_id()
    redis_info = ('host:{0},port:{1},base:{2},maxPages:{3}').format(
            engine_redis_host, engine_redis_port, fake_base_id, max_pages)
    return redis_info

def _get_results(test_type):
    """Load the saved test results."""
    test_path = ('{0}/parallelspider_results_{1}').format(
            _test_results_dir(), test_type)
    with open(test_path) as f:
        test_results = f.read()
    return test_results

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
### Commad Line Gunk
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
            "-t", "-T", "--testType", action="store", dest="testType", 
            help="Type of test output to generate: map, reduce, ...")
    (options, args) = parser.parse_args()

    if options.redis == 'start':
        _start_engine_redis()
    elif options.redis == 'stop':
        _stop_engine_redis()
    elif options.testType:
        _generate_output(options.testType)
    else: # run tests
        unittest.main()
