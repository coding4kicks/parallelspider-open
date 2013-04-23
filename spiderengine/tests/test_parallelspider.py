#!/usr/bin/env python
"""
    Test Suite for Parallel Spider

    TODO: figure out off by 1 error?
    Eventually mapper output test fails and is different from saved results.
    The only difference is linkci_internal and linkci_external.
    somehow 1 link is moving from internal to external in the map output?
    map int=296,ext=29 ; results int=295, ext=30
    failed - map 295/30 and results 296/29 ...wtf?

    TODO: figure out why having issues with HTTPS:
    freezes on page 1? Or is the just HN?
"""

import os
import json
import urllib
import unittest
import optparse

import redis

from spiderdepot import data
from spiderengine.parallelspider import Mapper, Reducer

###############################################################################
### Test Cases
###############################################################################
class TestParallelSpider(unittest.TestCase):

    def setUp(self):
        self.redis = _initialize_engine_redis()
        self.mapper, self.reducer = _setup_map_reduce()

    def testMapperOutput(self):
        """Test analysis ouput from parallelspider mapper."""
        final_output = _generate_mapper_output(self.mapper)
        # Only looking at start and end, since easier to compare on failure
        self.assertEqual(final_output[0:100], _get_results('mapper')[0:100])
        self.assertEqual(final_output[-100:], _get_results('mapper')[-100:])        

    def testReducerOutput(self):
        """Test processing ouput from parallelspider reducer."""
        final_output = []
        mapper_output = []
        for out in self.mapper("",""):
            mapper_output.append(out)
        reducer_input = _sort_output(mapper_output)
        for out in reducer_input:
            key, value = out
            for reducer_output in self.reducer(key, value):
                final_output.append(str(reducer_output))
        self.assertEqual("\n".join(final_output), _get_results('reducer'))

    def testNewLinkOutput(self):
        """Test new links are generated and stored correctly in Engine Redis."""
        _generate_mapper_output(self.mapper)
        new_links = _get_fake_base_id() + "::new_links"
        link_output = str(self.redis.smembers(new_links))
        self.assertEqual(link_output[0:100], _get_results('new_links')[0:100])
        self.assertEqual(link_output[-100:], _get_results('new_links')[-100:])

    def testFinishedLinkOutput(self):
        """Test that the processed link is stored correctly in finished_links in Engine Redis."""
        _generate_mapper_output(self.mapper)
        finished_links = _get_fake_base_id() + "::finished"
        link_output = str(self.redis.smembers(finished_links))
        self.assertEqual(link_output, _get_results('finished_links'))

    def testProcessingLinksEmpty(self):
        """Check that the single link is removed from processing."""
        _generate_mapper_output(self.mapper)
        processing_links = _get_fake_base_id() + "::processing"
        link_output = str(self.redis.smembers(processing_links))
        self.assertEqual(link_output, 'set([])')

    def testCountIncremented(self):
        """Check that the processed link count is 1."""
        _generate_mapper_output(self.mapper)
        count = finished_links = _get_fake_base_id() + "::count"
        self.assertEqual(self.redis.get(count), '1')

    def testKeyExpirationsSet(self):
        """Test that key expirations are set to an hour."""
        _generate_mapper_output(self.mapper)
        new_links = _get_fake_base_id() + "::new_links"
        processing_links = _get_fake_base_id() + "::processing"
        finished_links = _get_fake_base_id() + "::finished"
        count = finished_links = _get_fake_base_id() + "::count"
        self.assertTrue(self.redis.ttl(new_links) > 3500)
        self.assertTrue(self.redis.ttl(finished_links) > 3500)
        self.assertTrue(self.redis.ttl(count) > 3500)
        
class TestParallelSpiderFailures(unittest.TestCase):

    def setUp(self):
        self.redis = _initialize_redis_for_failure()
        self.mapper, self.reducer = _setup_map_reduce()

    def testParseFail(self):
        """Test that mapper fails to parse"""
        msg = "[('zmsg__error', ('Unable to download and parse: broken_path"
        final_output = _generate_mapper_output(self.mapper)
        processing_links = _get_fake_base_id() + "::processing"
        self.redis.spop(processing_links) #clean up for other tests
        self.assertEqual(final_output[:60], msg)

    def testBadKey(self):
        """Test non-existant key"""
        final_output = []
        key, value = ('junk','input')
        for reducer_output in self.reducer(key, value):
            final_output.append(str(reducer_output))
        msg = """["('zmsg_error', ('unrecognized key', 1))"]"""
        self.assertEqual(str(final_output), msg)

    def testBadReducerInput(self):
        """Test malformed reducer input handling."""
        final_output = []
        key, value = ('tagci_link',('bad', 'input'))
        for reducer_output in self.reducer(key, value):
            final_output.append(str(reducer_output))
        msg = """('zmsg__error', ("Unable to reduce: tagci_link"""
        final_output = " ".join(final_output)
        self.assertEqual(final_output[:46], msg)

    def testNoNewLinks(self):
        """Test that an empty new link set is hanled okay."""
        new_links = _get_fake_base_id() + "::new_links"
        self.redis.spop(new_links)
        final_output = _generate_mapper_output(self.mapper)
        self.assertEqual(final_output, '[]')

    # TODO: handle bad redis connection
    #def testBadRedis(self):
    #    params = {'redisInfo':_set_engine_redis_info(9999)}
    #    Mapper.params = params
    #    final_output = _generate_mapper_output(Mapper())
    #    print final_output

        
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
    r.set(_generate_fake_crawl_id(), json_config)
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
    r.set(_generate_fake_crawl_id(), json_config)
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
        test_file = ('{0}/parallelspider_results_mapper').format(
            _test_results_dir())
        with open(test_file, 'w') as f:
            f.write(mapper_output)
        new_links = _get_fake_base_id() + "::new_links"
        link_output = redis.smembers(new_links)
        test_file = ('{0}/parallelspider_results_new_links').format(
            _test_results_dir())
        with open(test_file, 'w') as f:
            f.write(str(link_output))
        finished_links = _get_fake_base_id() + "::finished"
        link_output = redis.smembers(finished_links)
        test_file = ('{0}/parallelspider_results_finished_links').format(
            _test_results_dir())
        with open(test_file, 'w') as f:
            f.write(str(link_output))

    if test_type == 'reducer':
        final_output = []
        mapper_output = []
        for out in mapper("",""):
            mapper_output.append(out)
        reducer_input = _sort_output(mapper_output)
        for out in reducer_input:
            key, value = out
            for reducer_output in reducer(key, value):
                final_output.append(str(reducer_output))
        test_file = ('{0}/parallelspider_results_reducer').format(
            _test_results_dir())
        with open(test_file, 'w') as f:
            f.write("\n".join(final_output))

###############################################################################
### Helper Delper Classes & Functions
###############################################################################
def _setup_map_reduce():
    """Setup Mapper with redis info."""
    params = {'redisInfo':_set_engine_redis_info()}
    Mapper.params = params
    Reducer.params = params
    return (Mapper(test=True), Reducer())

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

def _set_engine_redis_info(port=6380):
    """Sets Engine Redis info for Parallel Spider initialization."""
    engine_redis_host = 'localhost'
    engine_redis_port = port
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

def _sort_output(map_output):
    """Sorts mapper output for reducer. The sort phase of map reduce."""

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
            "-g", "-G", "--generateTestOutput", 
            action="store", dest="testType", 
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
