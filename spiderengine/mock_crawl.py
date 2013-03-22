#!/usr/bin/env python

"""
  Places a crawl in the Central Redis Queue to test the SpiderEngine
"""

import base64
import json
import sys
import time

import redis

def mocker():

    # Create fake crawl info
    crawl = {}
    crawl["name"] = "My Fake Crawls Name"
    crawl["additionalSites"] = ["http://www.foxnews.com", "http://www.cnn.com"]
    crawl["wordSearches"] = ["content", "crazy"]
    crawl["wordContexts"] = ["context", "democrat"]
    crawl["wordnets"] = ["violence", "love"]
    crawl["customSynRings"] = [{"name":"custring","text":"a, word, ring"}]
    crawl["xpathSelectors"] = ["xpathing"]
    crawl["cssSelectors"] = [{"selector":"selcting","text":True}]
    crawl["maxPages"] = 100
    crawl["totalResults"] = 100
    crawl["externalSites"] = True
    crawl["text"] = {"visible":True,"headlines":True,"hidden":True}
    crawl["links"] = {"text":True,"all":True,"external":True}
    crawl["stopWords"] = "a, stop, word"
    crawl["predefinedSynRings"] = [{"name":"curseWords","title":"Curse Words"}]
    crawl["primarySite"] = "http://www.nbcnews.com/"
    crawl["time"] = "Thu Mar 21 2013 01:03:56 GMT-0700 (PDT)"

    crawl_info = {}
    crawl_info["shortSession"] = "Q1610Y/rT4K829Pj5b5Cz"
    crawl_info["longSession"] = "U3VwZXIgTW8gRm8vLy9hLy8vPGJ1aWx0LWluIG1"
    crawl_info["crawl"] = crawl
    
    crawl_json = json.dumps(crawl_info)
    
    # Create fake crawl id
    fake_user = base64.b64encode('fake_user')
    fake_name = base64.b64encode('fake_name')
    fake_time = base64.b64encode('fake_time')
    fake_rand = base64.b64encode('fake_rane')
    fake_crawl_id = fake_user + "-" + fake_name + "-" + \
                    fake_time + "-" + fake_rand

    # Push into Central Redis (hardcoded)
    c = redis.Redis('localhost', 6379)
    c.set(fake_crawl_id, crawl_json)
    c.expire(fake_crawl_id, (60*60))
    c.set(fake_crawl_id + "_count", -1)
    c.expire(fake_crawl_id + "_count", (60*60))
    c.rpush("crawl_queue", fake_crawl_id)

    # Print out count till done
    count = -1
    #while count != -2:
    #    count = int(c.get(fake_crawl_id + '_count'))
    #    print count
    #    time.sleep(5)

    
    print fake_crawl_id
    print crawl_json
 


if __name__ == "__main__":
    """ enable command line execution """
    sys.exit(mocker())

