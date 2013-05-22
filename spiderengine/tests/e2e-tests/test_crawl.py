#!/usr/bin/env python

"""
  Places a crawl in the Central Redis Queue to test the SpiderEngine.
  Verifies results of the crawl are correctly uploaded to S3.
"""

import sys
import time
import json
import urllib
import random
import base64
import datetime

import boto
import redis

def mocker():

    crawl = {}
    crawl["primarySite"] = ("https://s3.amazonaws.com/parallel_spider_test/"
                            "index.html")
    crawl["text"] = {"visible":True,"headlines":True,"hidden":True}
    crawl["links"] = {"text":True,"all":True,"external":True}
    crawl["wordContexts"] = [] #["Obama", "democrat", "republican", "sequester"]
    crawl["predefinedSynRings"] = [] #[{"name":"stopWords","title":"Curse Words"}]
    crawl["maxPages"] = 20
    crawl["externalSites"] = False
    crawl["stopWords"] = ""
    crawl["name"] = "Hackalicious News"
    crawl["time"] = "April 11, 2013" 
    crawl["additionalSites"] = [] #["http://www.dhs.gov/"] #, "http://www.cnn.com"]

    
    # TODO: Implement
    crawl["totalResults"] = 100
    crawl["wordSearches"] = ["content", "crazy"]
    crawl["wordnets"] = ["violence", "love"]
    crawl["xpathSelectors"] = ["xpathing"]
    crawl["cssSelectors"] = [{"selector":"selcting","text":True}]

    crawl_info = {}
    crawl_info["shortSession"] = "Q1610Y/rT4K829Pj5b5Cz"
    crawl_info["longSession"] = "U3VwZXIgTW8gRm8vLy9hLy8vPGJ1aWx0LWluIG1"
    crawl_info["crawl"] = crawl
    
    crawl_json = json.dumps(crawl_info)

    # Create fake crawl id
    # Create random fake time so files don't collide
    random_year = str(random.random() * 10000)[:4]
    fake_time = "Fri Mar 15 " + random_year + " 21:00:15 GMT-0700 (PDT)"
    fake_crawl_id = 'test' + "__" + 'politic' + "__" + \
                    fake_time
    fake_crawl_id = urllib.quote_plus(fake_crawl_id)

    # Push into Central Redis (hardcoded)
    c = redis.Redis('localhost', 6379)
    c.set(fake_crawl_id, crawl_json)
    c.expire(fake_crawl_id, (60*60))
    c.set(fake_crawl_id + "_count", -1)
    c.expire(fake_crawl_id + "_count", (60*60))
    c.rpush("crawl_queue", fake_crawl_id)

    # Print out count till done
    count = -1
    while count != -2:
        count = int(c.get(fake_crawl_id + '_count'))
        print count
        time.sleep(5)

    
    print fake_crawl_id
    print crawl_json


    r = redis.StrictRedis(host='localhost', port=6380, db=0)
    config_file = r.get(fake_crawl_id)
    config = json.loads(config_file)

    user_id = config['user_id']
    full_crawl_id = config['crawl_id']
    key = user_id + '/' + full_crawl_id + '.json'

    # Upload to S3 (assumes AWS keys are in .bashrc / env)
    s3conn = boto.connect_s3()
    bucket_name = "ps_users" # TODO: put in config init
    bucket = s3conn.create_bucket(bucket_name)
    k = boto.s3.key.Key(bucket)
    k.key = key
    results = k.get_contents_as_string() 
    print results


if __name__ == "__main__":
    """ enable command line execution """
    sys.exit(mocker())

