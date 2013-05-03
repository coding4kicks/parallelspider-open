#!/usr/bin/env python
"""
Test spiderclient.py

TODO: handle failures
"""

import os
import json
import urllib
import unittest
import optparse

import redis

from spiderdepot import data
from spiderengine.spiderclient import CrawlTracker, set_logging_level 


###############################################################################
### Test Cases
###############################################################################
class TestSpiderRunner(unittest.TestCase):
    """Test for success."""

    def setUp(self):
        """Intialize Central and Engine Redis and SpiderClient."""
        self.central_redis = _initialize_redis('central')
        self.engine_redis = _initialize_redis('engine')
        self.client = _setup_client(self.central_redis, self.engine_redis )

    def tearDown(self):
        pass

    def testInitialization(self):
        """Test initial parameters are set correctly."""
        self.assertEqual(self.client.crawlQueue, [])
        self.assertEqual(self.client.cleanQueue, [])
        self.assertEqual(self.client.site_list, {})
        self.assertEqual(self.client.central_redis, self.central_redis)
        self.assertEqual(self.client.engine_redis, self.engine_redis)
        self.assertEqual(self.client.max_pages, 20)
        self.assertEqual(self.client.total_max, 20)
        self.assertEqual(self.client.mappers, 3)
        self.assertEqual(self.client.engine_redis_host, 'localhost')
        self.assertEqual(self.client.engine_redis_port, '6380')
        self.assertFalse(self.client.mock)
        self.assertFalse(self.client.psuedo_dist)

    def testCrawlInfo(self):
        """Test correct crawl info placed in engine redis."""
        _load_crawl_json(self.central_redis)
        self.central_redis.rpush('crawl_queue', _get_fake_crawl_id())
        self.client.checkRedisQueue()
        output = self.engine_redis.get(_get_fake_crawl_id())
        crawl = json.loads(output)
        results = json.loads(_get_results('crawl_init'))
        results['time'], crawl['time'] = 0, 0
        self.assertEqual(crawl, results)

    def testCommand(self):
        """Test spider runner command is correct."""
        _load_crawl_json(self.central_redis)
        self.central_redis.rpush('crawl_queue', _get_fake_crawl_id())
        command = self.client.checkRedisQueue()
        print command




###############################################################################
### Redis Initialization
###############################################################################
def _start_engine_redis():
    """Start Central and Engine Redis."""
    data.start('kvs', 'central')
    data.start('kvs', 'engine')

def _initialize_redis(redis_type):
    """Connect to Redis"""
    if redis_type == 'central':
        r = redis.Redis('localhost', 6379)
    else: # engine redis
        r = redis.Redis('localhost', 6380)
    #config = {'crawl_id': _get_fake_crawl_id() }
    #json_config = json.dumps(config)
    #r.set(_get_fake_crawl_id(), json_config)
    return r

#def _initialize_redis_for_failure():
#    """Connect to Redis, but set up a bad path for crawl file."""
#    r = redis.Redis('localhost', 6380)
#    config = {}
#    json_config = json.dumps(config)
#    r.set(_get_fake_crawl_id(), json_config)
#    return r

def _stop_engine_redis():
    """Stop Central and Engine Redis."""
    data.stop('kvs', 'central')
    data.stop('kvs', 'engine')

###############################################################################
### Output Generator for Testing
###############################################################################
def _generate_output():
    """Generate output for testing."""

    central_redis = _initialize_redis('central')
    engine_redis = _initialize_redis('engine')
    client = _setup_client(central_redis, engine_redis )
    _load_crawl_json(central_redis)
    central_redis.rpush('crawl_queue', _get_fake_crawl_id())
    client.checkRedisQueue()
    output = engine_redis.get(_get_fake_crawl_id())
    test_file = ('{0}/spiderclient_results_crawl_init').format(
        _test_results_dir())
    with open(test_file, 'w') as f:
        f.write(output)

###############################################################################
### Helper Delper Classes & Functions
###############################################################################
def _setup_client(central_redis, engine_redis):
    """Create instance of CrawlTracker for client testing."""
    log_info = set_logging_level('develop')
    return CrawlTracker(central_redis, engine_redis, 'localhost', 
            log_info=log_info)

def _load_crawl_json(redis):
    crawl_json = json.dumps(_sample_crawl_input())
    redis.set(_get_fake_crawl_id(), crawl_json) 

def _get_results(test_type):
    """Load the saved test results."""
    test_path = ('{0}/spiderclient_results_{1}').format(
            _test_results_dir(), test_type)
    with open(test_path) as f:
        test_results = f.read()
    return test_results

def _get_fake_crawl_id():
    """Create a fake crawl id with all parameters fixed."""
    fake_user = "yankeecharlie"
    fake_name = "badpolitics"
    fake_time = "Fri Mar 15 2020 21:00:15 GMT-0700 (PDT)"
    fake_crawl_id = ('{0}__{1}__{2}').format(fake_user, fake_name, fake_time)
    fake_crawl_id = urllib.quote_plus(fake_crawl_id)
    return fake_crawl_id

def _test_results_dir():
    """Return directory containing test results"""
    return os.path.realpath(__file__).rpartition('/')[0] + '/testresults'

def _sample_crawl_input():
    sample_crawl = \
    {        
     "shortSession":"Q1610Y/rT4K829Pj5b5Cz",
     "longSession":"U3VwZXIgTW8gRm8vLy9hLy8vPGJ1aWx0LWluIG1ldGhvZCBub3"\
                   "cgb2YgdHlwZSBvYmplY3QgYXQgMHgxMDljZGU0MjA+/Bqy",
     "crawl":{
         "name":"http://ccn.com",
         "additionalSites":["http://www.foxnews.com"],
         "wordSearches":["andax"],
         "wordContexts":["contextwordy"],
         "wordnets":["nettyword"],
         "customSynRings":[
              {
                   "name":"custring",
                   "text":"a, word, ring"
              }
         ],
         "xpathSelectors":["xpathing"],
         "cssSelectors":[
              {
                   "selector":"selcting",
                   "text":True
              }
         ],
         "maxPages":100,
         "totalResults":100,
         "externalSites":True,
         "text":{
              "visible": True,
              "headlines": True,
              "hidden": True
         },
         "links":{
              "text": True,
              "all": True,
              "external": True
         },
         "stopWords":"a, stop, word",
          "predefinedSynRings":[
               #{
               #     "name":"curseWords",
               #     "title":"Curse Words"
               #}
          ],
         "primarySite":"http://ccn.com",
         "time":"Thu Mar 21 2013 01:03:56 GMT-0700 (PDT)"
        }
    }
    return sample_crawl



###############################################################################
### Commad Line Gook
###############################################################################
if __name__ == '__main__':
    """Run test or start/stop redis for testing."""

    usage = "usage: %prog [options]"
    parser = optparse.OptionParser(usage)

    parser.add_option(
            "-r", "-R", "--redis", 
            action="store", dest="redis", 
            help="Start/Stop Redis datastores.")
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

    
