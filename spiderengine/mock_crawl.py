#!/usr/bin/env python

"""
  Places a crawl in the Central Redis Queue to test the SpiderEngine
"""

import sys
import time
import json
import urllib
import random
import base64
import datetime

import redis

def mocker():

    # Create fake crawl info
    crawl = {}

    # Implemented (At least partially)
    crawl["primarySite"] = "http://www.foxnews.com/"
    crawl["text"] = {"visible":True,"headlines":False,"hidden":False}
    crawl["links"] = {"text":False,"all":False,"external":False}
    crawl["wordContexts"] = [] #["democrat", "republican", "obama"]
    crawl["predefinedSynRings"] = [] #[{"name":"stopWords","title":"Curse Words"}]
    crawl["maxPages"] = 10
    crawl["externalSites"] = False
    crawl["stopWords"] = ""
    crawl["name"] = "News Showdown - Text"
    crawl["time"] = "Sat Apr 06 2013 20:00:00 GMT-0700 (PDT)" 
    crawl["additionalSites"] = [] #["http://www.nbcnews.com", "http://www.cnn.com"]

    
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
    fake_crawl_id = 'fake_user' + "__" + 'fake_name' + "__" + \
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
 


if __name__ == "__main__":
    """ enable command line execution """
    sys.exit(mocker())

