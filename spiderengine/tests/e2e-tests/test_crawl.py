#!/usr/bin/env python

"""
  Places a crawl in the Central Redis Queue to test the SpiderEngine.
  Verifies results of the crawl are correctly uploaded to S3.

  Bug: on a single page crawl, on one occasion didn't finish
       because count didn't increment to 1 in Central Redis.
"""

import os
import sys
import time
import json
import urllib
import random
import base64
import datetime
import optparse

import boto
import redis

def e2e_tester(generating=False):
    """
    Test e2e crawl

    Tests crawl from Spider Client to Spider Cleaner.
    Places crawl in Central Redis and checks results in S3.
    Uses a static test page.
    Set generating to true to save new results for future tests.
    """

    print("Setting up test crawl...")
    crawl_info = _setup_crawl()    
    crawl_json = json.dumps(crawl_info)
    fake_crawl_id = _generate_id()

    print("Placing crawl into redis...")
    c = _push_central_redis(fake_crawl_id, crawl_json, _c_redis_info())

    # Print out count till crawl done
    count = -1
    while count != -2:
        count = int(c.get(fake_crawl_id + '_count'))
        print count
        time.sleep(5)

    print("Performing checks ...")
    key = _get_crawl_key(fake_crawl_id, _e_redis_info())
    #r = redis.StrictRedis(host='localhost', port=6380, db=0)
    #config_file = r.get(fake_crawl_id)
    #config = json.loads(config_file)
    #user_id = config['user_id']
    #full_crawl_id = config['crawl_id']
    #key = user_id + '/' + full_crawl_id + '.json'

    # Upload to S3 (assumes AWS keys are in .bashrc / env)
    s3conn = boto.connect_s3()
    bucket_name = "ps_users" # TODO: put in config init
    bucket = s3conn.create_bucket(bucket_name)
    k = boto.s3.key.Key(bucket)
    k.key = key
    results = k.get_contents_as_string()

    if generating:
        _save_results(results)
        print("Results saved to file.")
    else:
        
        pass
        
    print results

###############################################################################
### Helper Delper Classes & Functions
###############################################################################
def _setup_crawl():
    """Set up crawl info."""
    crawl = {}
    crawl["primarySite"] = ("https://s3.amazonaws.com/parallel_spider_test/"
                            "index.html")
    crawl["text"] = {"visible":True,"headlines":True,"hidden":True}
    crawl["links"] = {"text":True,"all":True,"external":True}
    crawl["wordContexts"] = [] 
    crawl["predefinedSynRings"] = [] 
    crawl["maxPages"] = 20
    crawl["externalSites"] = False
    crawl["stopWords"] = ""
    crawl["name"] = "Hackalicious News"
    crawl["time"] = "April 11, 2013" 
    crawl["additionalSites"] = []
    # Not Implement
    crawl["totalResults"] = 100
    crawl["wordSearches"] = ["content", "crazy"]
    crawl["wordnets"] = ["violence", "love"]
    crawl["xpathSelectors"] = ["xpathing"]
    crawl["cssSelectors"] = [{"selector":"selcting","text":True}]

    crawl_info = {}
    crawl_info["shortSession"] = "Q1610Y/rT4K829Pj5b5Cz"
    crawl_info["longSession"] = "U3VwZXIgTW8gRm8vLy9hLy8vPGJ1aWx0LWluIG1"
    crawl_info["crawl"] = crawl

    return crawl_info

def _generate_id():
    """Create a fake crawl id."""
    # Create random fake time so files don't collide
    random_year = str(random.random() * 10000)[:4]
    fake_time = "Fri Mar 15 " + random_year + " 21:00:15 GMT-0700 (PDT)"
    fake_crawl_id = 'test' + "__" + 'politic' + "__" + \
                    fake_time
    fake_crawl_id = urllib.quote_plus(fake_crawl_id)
    return fake_crawl_id

def _c_redis_info():
    """Return Central Redis host and port."""
    # Hard coded for now, may switch to option
    return('localhost', 6379)

def _e_redis_info():
    """Return Engine Redis host and port."""
    # Hard coded for now, may switch to option
    return('localhost', 6380)

def _push_central_redis(fake_crawl_id, crawl_json, redis_info):
    """Place crawl into Central Redis to initiate."""
    c = redis.Redis(*redis_info)
    c.set(fake_crawl_id, crawl_json)
    c.expire(fake_crawl_id, (60*60))
    c.set(fake_crawl_id + "_count", -1)
    c.expire(fake_crawl_id + "_count", (60*60))
    c.rpush("crawl_queue", fake_crawl_id)
    return c

def _get_crawl_key(fake_crawl_id, redis_info):
    """Create a key from user_id and crawl_id."""
    e = redis.StrictRedis(*redis_info)
    config_file = e.get(fake_crawl_id)
    config = json.loads(config_file)
    user_id = config['user_id']
    full_crawl_id = config['crawl_id']
    key = user_id + '/' + full_crawl_id + '.json'
    return key

def _load_results():
    """Load json crawl results for comparison."""
    with open(_test_file_path(), 'w') as f:
        f.write(results)

def _save_results(results):
    """Save json crawl results to file for future tests."""
    with open(_test_file_path(), 'w') as f:
        f.write(results)

def _test_file_path():
    """Return the full path to the test file."""
    return _test_results_dir() + _test_file()

def _test_file():
    """Return the test file name."""
    return "e2e_test_results.json"

def _test_results_dir():
    """Return directory containing test results"""
    return os.path.realpath(__file__).rpartition('/')[0] + '/testresults/'


###############################################################################
### Command Line
###############################################################################
if __name__ == "__main__":
    """ enable command line execution """
    usage = "usage: %prog [options]"
    parser = optparse.OptionParser(usage)
    parser.add_option(
            "-g", "-G", "--generate", action="store_true", 
            default="", dest="generate", 
            help="Generate results to test. [default: False]")
    (options, args) = parser.parse_args()
    sys.exit(e2e_tester(options.generate))

