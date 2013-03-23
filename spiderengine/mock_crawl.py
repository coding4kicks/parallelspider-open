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

    # tempory overwrite
    crawl_json = '{"stop_list": ["a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren\'t", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can\'t", "cannot", "could", "couldn\'t", "did", "didn\'t", "do", "does", "doesn\'t", "doing", "don\'t", "down", "during", "each", "few", "for", "from", "further", "had", "hadn\'t", "has", "hasn\'t", "have", "haven\'t", "having", "he", "he\'d", "he\'ll", "he\'s", "her", "here", "here\'s", "hers", "herself", "him", "himself", "his", "how", "how\'s", "i", "i\'d", "i\'ll", "i\'m", "i\'ve", "if", "in", "into", "is", "isn\'t", "it", "it\'s", "its", "itself", "let\'s", "me", "more", "most", "mustn\'t", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan\'t", "she", "she\'d", "she\'ll", "she\'s", "should", "shouldn\'t", "so", "some", "such", "than", "that", "that\'s", "the", "their", "theirs", "them", "themselves", "then", "there", "there\'s", "these", "they", "they\'d", "they\'ll", "they\'re", "they\'ve", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn\'t", "we", "we\'d", "we\'ll", "we\'re", "we\'ve", "were", "weren\'t", "what", "what\'s", "when", "when\'s", "where", "where\'s", "which", "while", "who", "who\'s", "whom", "why", "why\'s", "with", "won\'t", "would", "wouldn\'t", "you", "you\'d", "you\'ll", "you\'re", "you\'ve", "your", "yours", "yourself", "yourselves", "&", "<", ">", "^", "(", ")"], "context_search_tag": ["dream"], "wordnet_lists": {"list1": ["word", "something", "loser"], "list2": ["news", "journalism", "great"]}, "meta_request": true, "external_links_request": true, "header_request": true, "all_links_request": true, "css_selectors": [{"selector": "p.abstr", "analyze": true, "name": "testCss", "css_text": true}], "a_tags_request": true, "xpath_selectors": [{"selector": "//img/@alt", "analyze": false, "name": "image alt", "css_text": false}, {"selector": "//div[@class=\'story\']/descendant::text()", "analyze": false, "name": "test1", "css_text": false}, {"selector": "//a[@href=\'http://video.msnbc.msn.com/nightly-news/50032975/\']/text()", "analyze": true, "name": "test2", "css_text": false}, {"selector": "//div[@id=\'tbx-29618997\']/div/h2/text()", "analyze": false, "name": "test3", "css_text": false}], "paths_to_follow": [], "text_request": true}'

    crawl_json = '{"a_tags_request": true}'


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
    while count != -2:
        count = int(c.get(fake_crawl_id + '_count'))
        print count
        time.sleep(5)

    
    print fake_crawl_id
    print crawl_json
 


if __name__ == "__main__":
    """ enable command line execution """
    sys.exit(mocker())

