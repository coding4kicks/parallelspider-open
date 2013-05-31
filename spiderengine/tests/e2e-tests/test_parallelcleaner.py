#!/usr/bin/env python

"""
test_cleaner.py - an e2e test for Spider Cleaner 

Uploads saved Parallel Spider results to HDFS.
Calls Spider Cleaner to process the results.
Compares these results to one's previously saved.
"""

import os
import sys
import json
import difflib
import optparse
import subprocess

import boto
import redis

def clean_tester(generating=False):
    """e2e test for Spider Cleaner."""

    # Setup
    print("Setting up info for cleaner test...")
    result = _upload_test_file()
    if result != 0:
        print("Problem uploading test file to HDFS.")
        sys.exit(1)
    fake_crawl_id = "fake_crawl_id"
    _push_engine_redis(fake_crawl_id, _crawl_json(), _e_redis_info())

    # Call Spider Cleaner
    clean_dir = _spider_dir() + 'spiderengine'
    result = _call_cleaner(clean_dir, fake_crawl_id, *_e_redis_info())
    if result != 0:
        print("Problem with Spider Cleaner. Test Failed.")
        sys.exit(1)

    key = _get_crawl_key(fake_crawl_id, _e_redis_info())
    new_results = _get_results_from_s3(key)

    if generating:
        with open(_result_file_path(), 'w') as f:
            f.write(new_results)
        print("Results saved to file.")
    else:
        # Verify Results
        print("Performing checks ...")
        with open(_result_file_path(), 'r') as f:
            old_results = f.read()
        if new_results[0:16520] == old_results[0:16520]:
            print("Test passed successfully.")
        else:
            print("ERROR: test failed comparison.")
            s = difflib.SequenceMatcher(a=new_results, b=old_results)
            for block in s.get_matching_blocks():
                print "match at a[%d] and b[%d] of length %d" % block

    # Cleanup
    print("Cleaning up...")
    #result = _remove_test_file()
    if result != 0:
        print("Problem removing test file from HDFS.")
        sys.exit(1)


###############################################################################
### Helper Delper Classes & Functions
###############################################################################
def _upload_test_file():
    """Uploads the test file to HDFS"""
    command = ('dumbo put {} {} -hadoop starcluster').format(
                    _test_file_path(), _hdfs_path())
    result = subprocess.call(command, shell=True)
    return result

def _call_cleaner( clean_dir, crawl_id, e_redis_host, e_redis_port):
    """Construct command to run Spider Cleaner."""
    print clean_dir
    command = ("python spidercleaner.py -r host:{},port:{} -c {}"
               ).format(e_redis_host, e_redis_port, crawl_id)
    result = subprocess.call(command, shell=True, cwd=clean_dir)
    return result

def _e_redis_info():
    """Return Engine Redis host and port."""
    # Hard coded for now, may switch to option
    return('localhost', 6380)

def _crawl_json():
    """Retrieve the crawl info json from file."""
    with open(_crawl_file_path()) as f:
        crawl_json = f.read()
    return crawl_json

def _push_engine_redis(fake_crawl_id, crawl_json, redis_info):
    """Place crawl info into Engine Redis."""
    e = redis.Redis(*redis_info)
    e.set(fake_crawl_id, crawl_json)
    e.expire(fake_crawl_id, (60*60))
    return e

def _get_crawl_key(fake_crawl_id, redis_info):
    """Create a key from user_id and crawl_id."""
    e = redis.StrictRedis(*redis_info)
    config_file = e.get(fake_crawl_id)
    config = json.loads(config_file)
    user_id = config['user_id']
    full_crawl_id = config['crawl_id']
    key = user_id + '/' + full_crawl_id + '.json'
    return key

def _get_results_from_s3(key):
    """Fetches and returns crawl results from S3."""
    # assumes AWS keys are in .bashrc / env
    s3conn = boto.connect_s3()
    bucket_name = "ps_users" # hardcode
    bucket = s3conn.create_bucket(bucket_name)
    k = boto.s3.key.Key(bucket)
    k.key = key
    results = k.get_contents_as_string()
    return results

def _remove_test_file():
    """Uploads the test file to HDFS"""
    command = ('dumbo rm {} -hadoop starcluster').format(_hdfs_path())
    result = subprocess.call(command, shell=True)
    return result

def _hdfs_path():
    """Return test file directory on hdfs."""
    path = ('/HDFS/parallelspider/out/https-__s3.amazonaws.com_parallel'
            '_spider_test_index.html--fake_test_crawl/part-00000')
    return path

def _test_file_path():
    """Return the full path to the test file to clean."""
    return _test_dir() + '/testfiles/' + _test_file()

def _crawl_file_path():
    """Return the full path to the crawl info file."""
    return _test_dir() + '/testfiles/' + _crawl_file()

def _result_file_path():
    """Return the full path to the results file."""
    return _test_dir() + '/testresults/' + _results_file()

def _test_file():
    """Return the test file name."""
    return "ps-results"

def _crawl_file():
    """Return the crawl file name."""
    return "crawl_info.json"

def _results_file():
    """Return the test file name."""
    return "clean-results"

def _test_dir():
    """Return directory containing test results"""
    return os.path.realpath(__file__).rpartition('/')[0]

def _spider_dir():
    """Return parallelspider directory."""
    path = os.path.realpath(__file__).rpartition('parallelspider')[0]
    return path + 'parallelspider/'

if __name__ == "__main__":
    """ enable command line execution """
    usage = "usage: %prog [options]"
    parser = optparse.OptionParser(usage)
    parser.add_option(
            "-g", "-G", "--generate", action="store_true", 
            default="", dest="generate", 
            help="Generate results to test. [default: False]")
    (options, args) = parser.parse_args()
    sys.exit(clean_tester(options.generate))

