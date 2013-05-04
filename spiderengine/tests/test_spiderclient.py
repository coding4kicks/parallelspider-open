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
from spiderengine.spiderclient import CrawlTracker, MockCrawl
from spiderengine.spiderclient import set_logging_level


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

    def testRunnerCommand(self):
        """Test spider runner command is correct."""
        _load_crawl_json(self.central_redis)
        self.central_redis.rpush('crawl_queue', _get_fake_crawl_id())
        command = self.client.checkRedisQueue()
        self.assertEqual(command, _get_results('command'))

    def testTotalCount(self):
        """Test total count passed to Central Redis."""
        _ = _run_client(self.client, self.engine_redis)
        count = self.central_redis.get(_get_fake_crawl_id() + "_count")
        self.assertEqual(count, '1')

    def testSuccessCommand(self):
        """Test correct command to check for success file."""
        command = _run_client(self.client, self.engine_redis)
        self.assertEqual(command[1], _get_results('success_cmd'))

    def testCleanerCommand(self):
        """Test spider cleaner command is correct."""
        command = _run_client(self.client, self.engine_redis)
        self.assertEqual(command[0], _get_results('clean_cmd'))

    def testCrawlQueueEmpty(self):
        """Test crawl is removed from crawl queue upon cleanup"""
        _ = _run_client(self.client, self.engine_redis)
        self.assertEqual(self.client.crawlQueue, [])

    def testKeyExpirationsSet(self):
        """Test that crawl info key expiration is set to an hour."""
        _ = _run_client(self.client, self.engine_redis)
        self.assertTrue(self.engine_redis.ttl(_get_fake_crawl_id()) > 3500)

    def testTimeIncrements(self):
        """Test that crawl time increments by the end."""
        self.client.checkRedisQueue()
        output = self.engine_redis.get(_get_fake_crawl_id())
        time1 = json.loads(output)['time']
        _ = _run_client(self.client, self.engine_redis)
        output = self.engine_redis.get(_get_fake_crawl_id())
        time2 = json.loads(output)['time']
        self.assertTrue((time2-time1) > 0)
 
    def testCompleteNotification(self):
        """Test Central Redis is updated to indicate complete."""
        self.client.cleanQueue.append(_get_fake_crawl_id())
        _ = _run_client(self.client, self.engine_redis, count=-2)
        count = self.central_redis.get(_get_fake_crawl_id() + "_count")
        self.assertEqual(count, '-2')

    def testCleanQueueEmpty(self):
        """Test clients cleanup queue removes completed crawl"""
        self.client.cleanQueue.append(_get_fake_crawl_id())
        _ = _run_client(self.client, self.engine_redis, count=-2)
        self.assertEqual(self.client.cleanQueue, [])


class TestMockCrawl(unittest.TestCase):
    """Test Mock Crawl of Spider Runner."""

    def setUp(self):
        """Initialize redis and mock, and run once."""
        self.engine_redis = _initialize_redis('engine')
        self.mock = MockCrawl(_get_fake_crawl_id(), 200, self.engine_redis)
        self.mock.run()

    def testStartCount(self):
        """Test that page count starts at 0."""
        count = self.engine_redis.get(_get_fake_crawl_id() + "_count")
        self.assertEqual(count, '0')

    def testCountUp(self):
        """Test that page count increments on run."""
        self.mock.run()
        count = self.engine_redis.get(_get_fake_crawl_id() + "_count")
        self.assertEqual(count, '100')

    def testComplete(self):
        """Test that page count is -2 at completion."""
        self.mock.run()
        self.mock.run()
        count = self.engine_redis.get(_get_fake_crawl_id() + "_count")
        self.assertEqual(count, '-2')


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
    return r

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
    command = client.checkRedisQueue()
    output = engine_redis.get(_get_fake_crawl_id())
    test_file = ('{0}/spiderclient_results_crawl_init').format(
        _test_results_dir())
    with open(test_file, 'w') as f:
        f.write(output)
    test_file = ('{0}/spiderclient_results_command').format(
        _test_results_dir())
    with open(test_file, 'w') as f:
        f.write(command)

    client.site_list[_get_fake_crawl_id()] = [_fake_site()]
    client.crawlQueue.append(_get_fake_crawl_id())
    engine_redis.set(_get_fake_base_id() + "::count", 1)
    command = client.checkCrawlStatus()
    test_file = ('{0}/spiderclient_results_success_cmd').format(
        _test_results_dir())
    with open(test_file, 'w') as f:
        f.write(command[1])
    test_file = ('{0}/spiderclient_results_clean_cmd').format(
        _test_results_dir())
    with open(test_file, 'w') as f:
        f.write(command[0])


###############################################################################
### Helper Delper Classes & Functions
###############################################################################
def _setup_client(central_redis, engine_redis):
    """Create instance of CrawlTracker for client testing."""
    log_info = set_logging_level('develop')
    return CrawlTracker(central_redis, engine_redis, 'localhost', 
            log_info=log_info, test=True)

def _run_client(client, e_redis, count=1):
    """Execute the client's Check Redis."""
    client.site_list[_get_fake_crawl_id()] = [_fake_site()]
    client.crawlQueue.append(_get_fake_crawl_id())
    e_redis.set(_get_fake_base_id() + "::count", count)
    command = client.checkCrawlStatus()
    return command

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

def _get_fake_base_id():
    """Generates a base id for a crawl: site name + crawl id."""
    fake_site = _fake_site()
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

def _fake_site():
    return 'http://www.fakesite.com'

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

    
