""" 
    Spider Client - Communicates between Spider Server and Spider Runner

    Part of Spider Engine package.
    Communicates with Central Redis, Engine Redis.
    Calls Spider Runner to execute a crawl. 
    Calls Spider Cleaner to finish the crawl.  
"""

import os
import sys
import json
import math
import time
import base64
import urllib
import logging
import optparse
import subprocess

import redis
from twisted.internet import reactor


class CrawlTracker(object):
    """ 
    Miidleman between Spider Server and Spider Engine

    Polls Central Redis's crawl queue for crawls.  When a crawl is
    encountered, it's information is extracted, validated, and then passed
    to the Spider Runner to begin a crawl.  The progress of a crawl is
    checked from Engine Redis and passed back to Central Redis.  When the
    crawl is complete Spider Cleaner is called and when complete, Spider
    Server is notified via Central Redis that the crawl is ready in S3.

    __init__ - sets up Redis and testing info
    checkRedisQueue - monitors Central Redis for crawls, upon retrieving a
                      crawl, it formats the crawl info and starts the crawl
    checkCrawlStatus - monitors crawl and clean queues for completion and 
                       handles notifying Central Redis of completion
    """

    def __init__(self, central_redis, engine_redis, engine_redis_host,
            engine_redis_port=6380, mock=False, psuedo=False):
        """
        Construct a singleton Crawl Tracker

        Args:
            central_redis - a redis-py instance of the Central Redis
            engine_redis - a redis-py instance of the local Engine Redis
            engine_redis_host - host info for Engine Redis
            engine_redis_port - port info for Engine Redis
            mock - boolean, True if mocking a crawl
            psuedo - boolean, True if crawling in psuedo distributed mode
        """
        self.central_redis = central_redis
        self.engine_redis = engine_redis
        self.engine_redis_host = engine_redis_host
        self.engine_redis_port = engine_redis_port
        self.mock = mock
        self.psuedo_dist = psuedo

        self.crawlQueue = [] # Queue of IDs of Crawls being executed
        self.cleanQueue = [] # Queue of IDs of Crawls being cleaned up
        self.site_list = {} # List of sites for each Crawl being tracked

        # Defaults
        self.max_pages = 20 # Default Free Ride
        self.mappers = 3
        
  
    def checkRedisQueue(self, queue_poll_time=1):
        """ 
        Checks the Central Redis server for jobs and passes them to Spider
        Runner.

        Polls Central Redis for crawls.  When one is found, id is retrieved and
        used to obtain crawl info from Central Redis.  After validating and
        converting info to what is expected by Spider Engine, the info is saved
        into the local Engine Redis and Spider Engine is called.  The crawl id
        is then saved into the Crawl Tracker's internal crawl queue for
        monitoring.  The Central Redis crawl queue is monitored every 1 second.

        Args
            poll_time - how often in seconds to check Central Redis crawl queue
        """
        
        # Process a crawlid  from the Central Redis queue
        crawl_id = self.central_redis.lpop('crawl_queue') 
        if crawl_id is not None:
  
            # Get the crawl info from Central Redis
            web_crawl_json = self.central_redis.get(crawl_id)       
            web_crawl_info = json.loads(web_crawl_json)
            web_crawl = web_crawl_info['crawl']
  
            crawl = {} # crawl info formatted for Spider Engine
            # TODO: fix crawl id
            user_id, name, ctime, rand = get_crawl_components(crawl_id)
            engine_crawl_id = urllib.quote_plus(user_id + '-' + 
                                        name + '-' + ctime)
  
            crawl['crawl_id'] = engine_crawl_id
            crawl['random'] = rand
            crawl['user_id'] = user_id
  
            # Add primary site to crawl site list
            if 'primarySite' in web_crawl:
                site_list = web_crawl['primarySite']    
            else:
                logging.error('No primary site to crawl.')
  
            # Add other sites to crawl site list
            if 'additionalSites' in web_crawl:
                for site in web_crawl['additionalSites']:
                    site_list += "," + site

            # Add crawls site to the site list
            sites = site_list.split(',')
            self.site_list[crawl_id] = sites
  
            # Add sites to crawl info for spidercleaner
            crawl['sites'] = site_list

            # Set crawl name as either passed name or primary site
            if 'name' in web_crawl:
                crawl['name'] = web_crawl['name']
            else:
                crawl['name'] = web_crawl['primarySite']
  
            # Set crawl date and time
            if 'time' in web_crawl:
                # TODO: web_crawl['time'] should be date
                crawl['date'] = web_crawl['time']
            else:
                logging.error('Crawl date not set in web data.')
                crawl['date'] = 'error'
            crawl['time'] = time.clock()
  
            # Set max pages to crawl
            if 'maxPages' in web_crawl:
                self.max_pages = web_crawl['maxPages']
            else:
                self.max_pages = 20
  
            # Adjust mappers based upon max pages 
            # TODO: benchmark
            if self.max_pages > 100:
                self.mappers = 20
            elif self.max_pages > 20:
                self.mappers = 5
  
            # Calculate max pages for each site (total/# of sites)
            if 'additionalSites' in web_crawl:
                total_num_sites = 1 + len(web_crawl['additionalSites'])
                pages_per_site = float(self.max_pages)/total_num_sites
                # Round up to make sure we hit total max pages and finish
                self.max_pages = int(math.ceil(pages_per_site))
  
            # Set external sites
            if 'externalSites' in web_crawl:
                crawl['analyze_external_pages'] = web_crawl['externalSites']
  
            # Default stop word list.  
            # TODO: Enable deslection
            # TODO: Enable site dependent stoplists
            stop_list = ['a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', "aren't", 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', "can't", 'cannot', 'could', "couldn't", 'did', "didn't", 'do', 'does', "doesn't", 'doing', "don't", 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', "hadn't", 'has', "hasn't", 'have', "haven't", 'having', 'he', "he'd", "he'll", "he's", 'her', 'here', "here's", 'hers', 'herself', 'him', 'himself', 'his', 'how', "how's", 'i', "i'd", "i'll", "i'm", "i've", 'if', 'in', 'into', 'is', "isn't", 'it', "it's", 'its', 'itself', "let's", 'me', 'more', 'most', "mustn't", 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', "shan't", 'she', "she'd", "she'll", "she's", 'should', "shouldn't", 'so', 'some', 'such', 'than', 'that', "that's", 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', "there's", 'these', 'they', "they'd", "they'll", "they're", "they've", 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', "wasn't", 'we', "we'd", "we'll", "we're", "we've", 'were', "weren't", 'what', "what's", 'when', "when's", 'where', "where's", 'which', 'while', 'who', "who's", 'whom', 'why', "why's", 'with', "won't", 'would', "wouldn't", 'you', "you'd", "you'll", "you're", "you've", 'your', 'yours', 'yourself', 'yourselves', '&', '<', '>', '^', '(', ')']
            
            # Add additional words to default stop list
            if 'stopWords' in web_crawl:
                # stopWords is a string with possible white space
                new_list = [w.strip() for w in web_crawl['stopWords'].split(',')]
                for word in new_list:
                    stop_list.append(word) 
            crawl['stop_list'] = stop_list

            # Set text analysis details
            if 'text' in web_crawl:
                if 'visible' in web_crawl['text']:
                    if web_crawl['text']['visible'] == True:
                        crawl['text_request'] = True
                if 'headlines' in web_crawl['text']:
                    if web_crawl['text']['headlines'] == True:
                        crawl['header_request'] = True
                if 'hidden' in web_crawl['text']:
                    if web_crawl['text']['hidden'] == True:
                        crawl['meta_request'] = True

            # Set link analysis details
            if 'links' in web_crawl:
                if 'text' in web_crawl['links']:
                    if web_crawl['links']['text'] == True:
                        crawl['a_tags_request'] = True
                if 'all' in web_crawl['links']:
                    if web_crawl['links']['all'] == True:
                        crawl['all_links_request'] = True
                if 'external' in web_crawl['links']:
                    if web_crawl['links']['external'] == True:
                        crawl['external_links_request'] = True
 
            # Set context analysis details
            if 'wordContexts' in web_crawl:
                crawl['context_search_tag'] = web_crawl['wordContexts']
  
            # Predefined synonym ring lists 
            # TODO: make more, put into redis, load in init
            predefinedRings = {'stopWords': ['and','but','a',
                                             'on','off','again']}
  
            # Set synonym ring analysis
            if 'predefinedSynRings' in web_crawl:
                for ring in web_crawl['predefinedSynRings']:
                    name = ring['name']
                    crawl['wordnet_lists'] = {}
                    if name in predefinedRings:
                        list = predefinedRings[name]
                        crawl['wordnet_lists'][name] = list
                    else:
                        print 'error error should not be here'
    
            # Add crawl info to local engine redis
            crawl_info = json.dumps(crawl)
            self.engine_redis.set(engine_crawl_id, crawl_info)
            hour = 60 * 60 # Expiration
            self.engine_redis.expire(engine_crawl_id, hour)
  
            # Add crawl to the crawl queue for monitoring by checkCrawlStatus
            self.crawlQueue.append(crawl_id)

            # If mocking then fake the funk.
            if self.mock:
                mocker = MockCrawl(crawl_id, self.max_pages, engine_redis)
                mocker.run()
  
            # Otherwise it's the real deal
            else:
                # Execute the crawl
                # TODO: Incorporate Sun Grid Engine
                cmd_line = "python spiderrunner.py " + site_list + \
                           " -r host:" + self.engine_master_host + "," + \
                               "port:" + self.engine_master_port + \
                           " -m " + str(self.mappers) + \
                           " -t " + str(self.max_pages) + \
                           " -c " + engine_crawl_id
                if self.psuedo_dist:
                    cmd_line += " -d"
                p = subprocess.Popen(cmd_line, shell=True) 
  
        # Continue to check the Central Redis queue (default every second).
        reactor.callLater(queue_poll_time, self.checkRedisQueue)
    

    def checkCrawlStatus(self, status_poll_time=5):
        """ 
        Tracks the crawl progress of the Spider Engine
  
        Retrieves the crawl progress for each site from Engine
        and passes the total count back to Central Redis.  When the crawl is
        finished, either when there are no new links or max pages is reach,
        Spider Cleaner is called to process the results of the crawl.  When
        Spider Cleaner updates Engine Redis with -2, the is passed back to
        Central Redis and the crawl is removed from the queue.

        Args
            poll_time - how often in seconds to check Central Redis crawl queue
        """
  
        # Fake the funck
        if self.mock:
            for crawl_id in self.crawlQueue:
                # Retrieve page count from engine and set in central redis
                page_count = self.engine_redis.get(crawl_id + "_count")
                self.central_redis.set(crawl_id + "_count", page_count)
                # If page count is complete (-2), remove from queue
                if page_count == "-2":
                    self.crawlQueue.remove(crawl_id)

        # Real Sexy Crawl
        else: 

            # Monitor the crawl queue
            for crawl_id in self.crawlQueue:
                total_count = 0
                # TODO: fix crawl id
                user_id, name, ctime, rand = get_crawl_components(crawl_id)
                engine_crawl_id = urllib.quote_plus(user_id + '-' + 
                                        name + '-' + ctime)

                # Crawl Completion Variables
                not_done = False            # True if still new links
                really_not_done = False     # True if no success files
                done = False                # True if count > max pages

                # Check counter and new link queue for each site
                # If either indicates complete, then check Success files exist
                for site in self.site_list[crawl_id]:
                    base = '%s::%s' % (site, engine_crawl_id)
                    site_count = self.engine_redis.get(base + "::count")
                    if site_count:
                        total_count += int(site_count)
  
                        # Check if new links empty (only if count has started)
                        new_links = \
                            self.engine_redis.scard(base + "::new_links")
                        if new_links > 0:
                            not_done = True
                        
  
                # Only update to crawling vice initializing if total > 0
                if total_count > 0:
                    self.central_redis.set(crawl_id + "_count", total_count) 
                if total_count > self.max_pages or not not_done:
                    done = True
  
                # If done check all sites for a success file
                if done:
                    for site in self.site_list[crawl_id]:
                        base = '%s::%s' % (site, engine_crawl_id)
                        base_path = base.replace("/","_").replace(":","-")
  
                        # Special case: testing in psuedo distributed mode
                        # No success file so check path exists, TODO: broken
                        if self.psuedo_dist:
                            path = "/home/parallelspider/out/"
                            if not os.path.exists(path + base_path):
                                really_not_done = True

                        # Distributed Crawl 
                        else:
                            # list output files and look for success
                            # TODO: add deferred (will break on psuedo dist)
                            cmd = "dumbo ls /HDFS/parallelspider/out/" + \
                                   base_path + " -hadoop starcluster"
                            files = subprocess.check_output(cmd, shell=True)

                            # If success file then we're not really done yet
                            if "_SUCCESS" not in files:
                                really_not_done = True
  
  
                # If all sites are done, crawl is complete so cleanup.
                # done (> max pages or new links are empty) 
                # really done (success files exist)
                if done and not really_not_done:
  
                    # Kick crawl out of the queue
                    self.crawlQueue.remove(crawl_id)
  
                    # Add crawl to cleaning queue
                    self.cleanQueue.append(crawl_id)
  
                    # Get start time details and set elapsed time
                    config_file = self.engine_redis.get(engine_crawl_id)
                    config = json.loads(config_file)
                    start_time = config['time']
                    stop_time = time.clock()
                    config['time'] = stop_time - start_time
                    config_json = json.dumps(config)
                    self.engine_redis.set(engine_crawl_id, config_json)
  
                    # TODO: should add a -3 for cleaning up
  
                    # Call cleanup
                    cmd_line = "python spidercleaner.py " +  \
                        "-r host:" + self.master_host + "," + \
                        "port:6380 " + \
                        "-c " + engine_crawl_id
                    if self.psuedo_dist:
                        cmd_line += " -d"
                    p = subprocess.Popen(cmd_line, shell=True) 
                    
             
            # Monitor clean queue            
            for crawl_id in self.cleanQueue:
                # TODO: fix crawl id
                user_id, name, ctime, rand = get_crawl_components(crawl_id)
                engine_crawl_id = urllib.quote_plus(user_id + '-' + 
                                        name + '-' + ctime)
 
                # Check the first site for -2 (complete)
                site = self.site_list[crawl_id][0]
                base = '%s::%s' % (site, engine_crawl_id)
                site_count = self.engine_redis.get(base + "::count")
                print ""
                print "clean q base and count"
                print base
                print site_count
                if site_count == "-2":
                    self.central_redis.set(crawl_id + "_count", site_count)
                    self.cleanQueue.remove(crawl_id)

        # Continue to montitor crawl statuses (default every 5 seconds).
        reactor.callLater(status_poll_time, self.checkCrawlStatus)


class MockCrawl(object):
    """ 
        Similuates a crawl for development.
    
        Used for local developmment of Spider Web and Spider Server.
        Initiated instead of a normal crawl.  Responds with increasing page
        counts at a predetermined rate.  Initiated by option -r on start.
    """

    def __init__(self, crawl_id, max_pages, engine_redis, speed=100):
        """ 
            MockCrawl Constructor

            Args:
                crawl_id - ID of crawl
                max_pages - Used to stop mock
                engine_redis - Redis used by Spider Engine
                speed - How fast or slow to simulate

            Speed of 100 is the default and normal speed.  Use greater
            than 100 for a fast crawl, and less than for a slow crawl.
        """
        self.crawl_id = crawl_id
        self.max_pages = max_pages
        self.engine_redis = engine_redis
        self.speed = speed

        self.count = 0 # Simulated crawl page count

    def run(self):
        """Executes the mock crawl until max pages is reached"""

        if self.count < self.max_pages:
            self.engine_redis.set(self.crawl_id + "_count", self.count)
            self.count = self.count + self.speed
        else:
            self.engine_redis.set(self.crawl_id + "_count", -2)

        reactor.callLater(5, self.run)

# Helper Funcs
###############################################################################
def get_crawl_components(crawl_id):
    """Construct sanitized engine crawl id"""

    u, n, t, r = crawl_id.split("-")
    user_id = base64.b64decode(u)
    name = base64.b64decode(n)
    ctime = base64.b64decode(t)
    rand = r

    return (user_id, name, ctime, rand)




# Command Line Crap & Initialization
###############################################################################

if __name__ == "__main__":
    """
    Command line gook
    
    Options:
        -c - Central Redis host info (default localhost)
        -p - Central Redis port info (default 6379)
        -e - Engine Redis host info (default localhost)
        -q - Engine Redis port info (default 6380)
        -m - Mock backend for front-end testing
        -d - psuedo distributed mode for testing
    """

    usage = "usage: %prog [options]"
    parser = optparse.OptionParser(usage)

    # Central Redis
    parser.add_option(
            "-c", "-C", "--centralRedisHost", action="store", 
            default="localhost", dest="centralRedisHost", 
            help="Set Central Redis host information. [default: %default]")
    parser.add_option(
            "-p", "-P", "--centralRedisPort", action="store", 
            default="6379", dest="centralRedisPort", 
            help="Set Central Redis port information. [default: %default]")

    # Engine Redis 
    parser.add_option(
            "-e", "-E", "--engineRedisHost", action="store", 
            default="localhost", dest="engineRedisHost", 
            help="Set Local Redis host information. [default: %default]")
    parser.add_option(
            "-q", "-Q", "--engineRedisPort", action="store", 
            default="6380", dest="engineRedisPort", 
            help="Set Local Redis port information. [default: %default]")

    # Mock (remote Analysis Engine by faking page count)
    parser.add_option(
            "-m", "-M", "--mock", action="store_true", 
            default="", dest="mock", 
            help="Mock Analysis Engine. [default: False]")

    # Psuedo Distributed (for easier testing on cluster)
    parser.add_option(
            "-d", "-D", "--psuedo", action="store_true", 
            default="", dest="psuedo", 
            help="Psuedo Distributed Mode. [default: False]")

    # Poll Times
    parser.add_option(
            "-t", "-T", "--queuePollTime", action="store", 
            default="1", dest="queuePollTime", 
            help="How often to poll for crawls. [default: %default]")
    parser.add_option(
            "-s", "-S", "--statusPollTime", action="store", 
            default="5", dest="statusPollTime", 
            help="How often to poll for crawl status. [default: %default]")

    # Parse and validate
    (options, args) = parser.parse_args()
    if int(options.centralRedisPort) < 1:
        parser.error("Central Redis port number must be greater than 0")
    if int(options.engineRedisPort) < 1:
        parser.error("Engine Redis port number must be greater than 0")
    if int(options.queuePollTime) <= 0:
        parser.error("Queue poll time must be positive")
    if int(options.statusPollTime) <= 0:
        parser.error("Status poll time must be positive")

    # Create redis objects
    central_redis = redis.StrictRedis(host=options.centralRedisHost,
                          port=int(options.centralRedisPort), db=0)
    engine_redis = redis.StrictRedis(host=options.engineRedisHost,
                          port=int(options.engineRedisPort), db=0)

    # Run the twisted client
    tracker = CrawlTracker(central_redis, engine_redis,
                           options.engineRedisHost, options.engineRedisPort, 
                           options.mock)
    reactor.callWhenRunning(tracker.checkRedisQueue, 
                            int(options.queuePollTime))
    reactor.callWhenRunning(tracker.checkCrawlStatus,
                            int(options.statusPollTime))
    reactor.run()
