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
class TestSomething(unittest.TestCase):

    def setUp(self):
        params = {'redisInfo':_set_engine_redis_info()}
        Mapper.params = params
        self.mapper = Mapper()

    def testSomething(self):
        pass
        
###############################################################################
### Redis Initialization
###############################################################################
def _start_engine_redis():
    """Start Engine Redis with fake crawl info."""
    data.start('kvs', 'engine')

def _initialize_engine_redis():
    r = redis.Redis('localhost', 6380)
    new_links = _get_fake_base_id() + "::new_links"
    r.sadd(new_links, _test_file_path())
    config = {}
    json_config = json.dumps(config)
    r.set(_generate_fake_crawl_id(), json_config)

def _stop_engine_redis():
    """Stop Engine Redis."""
    data.stop('kvs', 'engine')

###############################################################################
### Helper Delper Classes & Functions
###############################################################################
def _initialize_engine_redis_info():
    """Single source for Engine Redis information: host, port, and base id."""
    pass

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
    fake_base_id = _get_fake_base_id()
    redis_info = ('host:{0},port:{1},base:{2}').format(
            engine_redis_host, engine_redis_port, fake_base_id)
    return redis_info


def _test_file_path():
    """Test file to crawl."""
    return _test_pages_dir() + '/fox0'

def _test_pages_dir():
    """Return directory containing test pages"""
    return os.path.realpath(__file__).rpartition('/')[0] + '/testpages'

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

    (options, args) = parser.parse_args()

    if options.redis == 'start':
        _start_engine_redis()
    elif options.redis == 'stop':
        _stop_engine_redis()
    elif options.redis == 'init':
        _initialize_engine_redis()
    else: # run tests
        unittest.main()
