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
import copy
import urllib
import logging
import optparse
import subprocess

import redis
from twisted.internet import reactor

###############################################################################
### CrawlTracker
###############################################################################
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

    TODO: Break if don't make progress: less than max, still new links
          and count stuck at same number: "-1"
    """

    def __init__(self, central_redis, engine_redis, engine_redis_host,
            engine_redis_port='6380', mock=False, psuedo=False, log_info=None,
            test=False):
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
        self.mock, self.psuedo_dist, self.test = mock, psuedo, test
        self._init_logging(log_info)

        self.crawlQueue = [] # Queue of IDs of Crawls being executed
        self.cleanQueue = [] # Queue of IDs of Crawls being cleaned up
        self.site_list = {} # List of sites for each Crawl being tracked

        # Defaults
        self.max_pages = 20 # Default Free Ride
        self.total_max = 20 # total for all sites
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

        self.log_header['msg_type'] = "checkRedisQueue - "

        # Process a crawlid  from the Central Redis queue
        crawl_id = self.central_redis.lpop('crawl_queue') 
        if crawl_id is not None:
            web_crawl = _get_crawl_info(crawl_id, self.central_redis)
            crawl = _reformat_crawl_info(crawl_id, web_crawl)
            site_list = _get_sites(web_crawl)
            self.site_list[crawl_id] = site_list.split(',')
            self._construct_call_parameters(web_crawl)

            # Logging
            msg = """Crawl info from Spider Web: %s""" % (web_crawl)
            self.logger.debug(msg, extra=self.log_header)
    
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

            # Logging
            #msg = """Crawl info to Spider Runner: %s""" % (crawl)
            #self.logger.info(msg, extra=self.log_header)

            # Add crawl info to local engine redis
            crawl_info = json.dumps(crawl)
            self.engine_redis.set(crawl_id, crawl_info)
            hour = 60 * 60 # Expiration
            self.engine_redis.expire(crawl_id, hour)
  
            # Add crawl to the crawl queue for monitoring by checkCrawlStatus
            self.crawlQueue.append(crawl_id)

            # Execute the crawl
            # TODO: Incorporate Sun Grid Engine
            cmd_line = "python spiderrunner.py " + site_list + \
                       " -r host:" + self.engine_redis_host + "," + \
                           "port:" + self.engine_redis_port + \
                       " -m " + str(self.mappers) + \
                       " -t " + str(self.max_pages) + \
                       " -c " + crawl_id
            if self.psuedo_dist:
                cmd_line += " -d"

            # Logging
            msg = """Cmd Line: %s""" % (cmd_line)
            self.logger.debug(msg, extra=self.log_header)

            # If mocking then fake the funk.
            if self.mock:
                mocker = MockCrawl(crawl_id, self.max_pages, engine_redis)
                mocker.run()

            elif self.test:
                return cmd_line

            # Otherwise it's the real deal
            else:
                p = subprocess.Popen(cmd_line, shell=True) 
  
        # Continue to check the Central Redis queue (default every second).
        reactor.callLater(queue_poll_time, self.checkRedisQueue)

    def _construct_call_parameters(self, web_crawl):
        """Determine SpiderRunner parameters: max pages & mappers."""
        self.max_pages = (web_crawl['maxPages'] if 'maxPages' in web_crawl
                            else 20)
        # TODO: benchmark
        if self.max_pages > 100:
            self.mappers = 15
        elif self.max_pages > 20:
            self.mappers = 5
        # Adjust mappers for number of sites so don't max out the engine
        self.mappers = self.mappers/(len(web_crawl['additionalSites']) + 1)
        # Calculate max pages for each site (total/# of sites)
        if 'additionalSites' in web_crawl:
            total_num_sites = 1 + len(web_crawl['additionalSites'])
            pages_per_site = float(self.max_pages)/total_num_sites
            self.total_max = self.max_pages # used for completion check
            # Round up to make sure we hit total max pages and finish
            self.max_pages = int(math.ceil(pages_per_site))

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

        self.log_header['msg_type'] = "checkCrawlStatus - "
        success_command = "" # only in outerscope for testing (fix with mocks)
        clean_command = ""

        # Fake the funk
        if self.mock:
            for crawl_id in self.crawlQueue:
                # Retrieve page count from engine and set in central redis
                page_count = self.engine_redis.get(crawl_id + "_count")
                self.central_redis.set(crawl_id + "_count", page_count)
                self.central_redis.expire(crawl_id + "_count", 60*60)
                # If page count is complete (-2), remove from queue
                if page_count == "-2":
                    self.crawlQueue.remove(crawl_id)

        # Real Sexy Crawl
        else: 

            # Monitor the crawl queue
            for crawl_id in self.crawlQueue:
                total_count = 0
                
                # Crawl Completion Variables
                not_done = False            # True if still new links
                really_not_done = False     # True if no success files
                done = False                # True if count > max pages

                # Check counter and new link queue for each site
                # If either indicates complete, then check Success files exist
                for site in self.site_list[crawl_id]:
                    base = '%s::%s' % (site, crawl_id)
                    site_count = self.engine_redis.get(base + "::count")
                    if site_count:
                        total_count += int(site_count)
                        # Check if new links empty (only if count has started)
                        new_links = \
                            self.engine_redis.scard(base + "::new_links")
                        if new_links > 0:
                            not_done = True

                            # Logging
                            msg = 'Not Done, still links'                            
                            self.logger.debug(msg, extra=self.log_header)

                    else: # Haven't started so definitely not done
                        not_done = True

                        # Logging
                        msg = 'Not Done, no count yet'                            
                        self.logger.debug(msg, extra=self.log_header)
  
                # Logging
                msg = ('Total count: {!s}').format(total_count)                            
                self.logger.debug(msg, extra=self.log_header)

                # Only update to crawling vice initializing if total > 0
                if total_count > 0:
                    self.central_redis.set(crawl_id + "_count", total_count) 
                    if total_count >= self.total_max or not not_done:
                        done = True

                        # Logging
                        msg = ('total_count: {!s} max_pages: {!s} '
                               'links_not_done {!s}'
                               ).format(total_count, self.total_max, not_done) 
                        self.logger.debug(msg, extra=self.log_header)

  
                # If done check all sites for a success file
                if done:
                    for site in self.site_list[crawl_id]:
                        base = '%s::%s' % (site, crawl_id)
                        base_path = base.replace("/","_").replace(":","-")

                        # Logging
                        msg = """Done, checking: %s""" % (base_path) 
                        self.logger.debug(msg, extra=self.log_header)
  
                        # Special case: testing in psuedo distributed mode
                        # No success file so check path exists, TODO: broken
                        if self.psuedo_dist:
                            path = "/home/parallelspider/out/"
                            with open(path + base_path) as f:
                                line = f.readline()
                                self.logger.debug("Reducing...", 
                                    extra=self.log_header)
                                if line == "":
                                    really_not_done = True

                                    # Logging
                                    msg = """Path doesn't exist""" 
                                    self.logger.debug(msg, extra=self.log_header)

                        # Distributed Crawl 
                        else:
                            # list output files and look for success
                            # TODO: add deferred (will break on psuedo dist)
                            cmd = "dumbo ls /HDFS/parallelspider/out/" + \
                                   base_path + " -hadoop starcluster"
                            if self.test:
                                success_command = cmd
                            else:
                                files = subprocess.check_output(cmd, shell=True)
        
                                # Logging
                                msg = """Checking for success file in: %s""" \
                                        % (files)
                                self.logger.debug(msg, extra=self.log_header)

                                # If success file then we're not really done yet
                                if "_SUCCESS" not in files:
                                    really_not_done = True

                                    # Logging
                                    msg = """No success file""" 
                                    self.logger.debug(msg, extra=self.log_header)
    
                # If all sites are done, crawl is complete so cleanup.
                # done (> max pages or new links are empty) 
                # really done (success files exist)
                if done and not really_not_done:

                    # Kick crawl out of the queue
                    self.crawlQueue.remove(crawl_id)
  
                    # Add crawl to cleaning queue
                    self.cleanQueue.append(crawl_id)
  
                    # Get start time details and set elapsed time
                    config_file = self.engine_redis.get(crawl_id)
                    config = json.loads(config_file)
                    start_time = config['time']
                    stop_time = time.time()
                    config['time'] = stop_time - start_time
                    config_json = json.dumps(config)
                    self.engine_redis.set(crawl_id, config_json)
                    self.engine_redis.expire(crawl_id, 60*60)

                    # TODO: should add a -3 for cleaning up
  
                    # Call cleanup
                    cmd_line = "python spidercleaner.py " +  \
                        "-r host:" + self.engine_redis_host + "," + \
                        "port:6380 " + \
                        "-c " + crawl_id
                    if self.psuedo_dist:
                        cmd_line += " -d"

                    # Logging
                    msg = """cmd_line: %s""" % (cmd_line)
                    self.logger.debug(msg, extra=self.log_header)

                    if self.test:
                        clean_command = cmd_line
                    else:
                        p = subprocess.Popen(cmd_line, shell=True) 
                    
             
            # Monitor clean queue            
            for crawl_id in self.cleanQueue:
                
                # Check the first site for -2 (complete)
                site = self.site_list[crawl_id][0]
                base = '%s::%s' % (site, crawl_id)
                site_count = self.engine_redis.get(base + "::count")

                # Logging
                msg = """Cleanup Queue base: %s count: %s""" \
                            % (base, site_count)
                self.logger.debug(msg, extra=self.log_header)

                if site_count == "-2":
                    self.central_redis.set(crawl_id + "_count", site_count)
                    self.cleanQueue.remove(crawl_id)

                    # Logging
                    msg = """Cleanup Success"""
                    self.logger.debug(msg, extra=self.log_header)

                if self.test:
                        return (clean_command, success_command)


        # Continue to montitor crawl statuses (default every 5 seconds).
        reactor.callLater(status_poll_time, self.checkCrawlStatus)

    def _init_logging(self, log_info):
        "Initilize logging parameters."""
        self.logger, log_header = log_info
        self.log_header = copy.deepcopy(log_header)
        self.debug = True if self.logger.getEffectiveLevel() == 10 else False

###############################################################################
### Mock Crawl
###############################################################################
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

###############################################################################
# Helper Funcs
###############################################################################
def get_crawl_components(crawl_id):
    """Construct sanitized engine crawl id"""

    u, n, t  = urllib.unquote_plus(crawl_id).split("__")
    return (u, n, t)

def _get_crawl_info(crawl_id, central_redis):
    """Download crawl info in Central Redis passed by Spider Web."""
    web_crawl_json = central_redis.get(crawl_id)       
    web_crawl_info = json.loads(web_crawl_json)
    return web_crawl_info['crawl']

def _reformat_crawl_info(crawl_id, web_crawl):
    """Construct crawl info for Spider Engine from Spider Web crawl info."""
    crawl = {}
    crawl['crawl_id'] = crawl_id
    crawl['user_id'] = get_crawl_components(crawl_id)[0]
    crawl['name'] = (web_crawl['name'] if 'name' in web_crawl 
                        else web_crawl['primarySite'])
    crawl['date'] = (web_crawl['time'] if 'time' in web_crawl
                        else "Time not set")
    crawl['time'] = time.time()
    crawl['sites'] = _get_sites(web_crawl)
    crawl['analyze_external_pages'] = (web_crawl['externalSites'] if 
                        'externalSites' in web_crawl else "")
    crawl['stop_list'] = _construct_stop_list(web_crawl)
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
    if 'wordContexts' in web_crawl:
        crawl['context_search_tag'] = web_crawl['wordContexts']
    return crawl

def _construct_stop_list(web_crawl):
    """Add user passed stop list to default."""
    # TODO: enable deselection of default and site dependent lists
    stop_list = _get_default_stop_list()
    if 'stopWords' in web_crawl:
        new_list = [w.strip() for w in web_crawl['stopWords'].split(',')]
        for word in new_list:
            stop_list.append(word)
    return stop_list

def _get_default_stop_list():
    """Retrieve the default stop list from a file."""
    stop_list = []
    path = os.path.realpath(__file__).rpartition('/')[0] + '/misc/stoplists/'
    with open(path + 'default_stop_list.txt') as f:
        for line in f:
            stop_list.append(line.rstrip())
    return stop_list
            
def _get_sites(web_crawl):
    """Construct list of primary and additional sites."""
    site_list = ""
    if 'primarySite' in web_crawl:
        site_list = web_crawl['primarySite']    
    else:
        # TODO: throw exception, must have primary site
        pass
    if 'additionalSites' in web_crawl:
        for site in web_crawl['additionalSites']:
            site_list += "," + site
    return site_list

def set_logging_level(level="production"):
    """
    Initialize logging parameters
    
    3 levels: production, develop & debug
    production - default, output info & errors to logfile
    develop - output info and errors to console
    debug - output debug, info and errors to console

    Args:
        level - set output content & location

    Message format:
        type: spider type: cleaner, server, client, ...
        host: computer executing program
        id: unique run id (set at start of program)
        asctime: time
        mtype: type of message (set at call in program)
        message: (set at call in program)

    Sample:
        logger.warning('Protocol problem: %s', 'connection reset', 
                        extra=log_header)

    TODO: import vice copy and paste
    """
    import socket

    # Log message is spider type, host, unique run id, time, and message
    FORMAT = "spider%(spider_type)s %(host)s %(id)d %(asctime)s " + \
             "%(msg_type)s %(message)s"
    HOST = socket.gethostbyname(socket.gethostname())
    SPDR_TYPE = "client"
    FILENAME = "/var/log/spider/spider" + SPDR_TYPE + ".log"
    log_header = {'id': 0, 'spider_type': SPDR_TYPE, 'host': HOST, 'msg_type':'none'}

    if level == "develop": # to console
        logging.basicConfig(format=FORMAT, level=logging.INFO)
    elif level == "debug": # extra info
        logging.basicConfig(format=FORMAT, level=logging.DEBUG)
    else: # production, to file (default)
        logging.basicConfig(filename=FILENAME, format=FORMAT, level=logging.INFO)

    logger = logging.getLogger('spider' + SPDR_TYPE)

    return (logger, log_header)

###############################################################################
### Command Line Crap & Initialization
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
        -l - logging level (default production)
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

    # Logging Level 
    parser.add_option(
            "-l", "-L", "--logging", action="store", 
            default="production", dest="log_level", 
            help="Set log level. [default: False]")

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

    # Set up logging
    options.log_level = "debug"
    #options.log_level = "develop"
    log_info = set_logging_level(level=options.log_level)
    logger, log_header = log_info
    log_header['msg_type'] = "Initialization - "
    msg = """starting options: %s""" % (options)
    logger.info(msg, extra=log_header)

    # Create redis objects
    central_redis = redis.StrictRedis(host=options.centralRedisHost,
                          port=int(options.centralRedisPort), db=0)
    engine_redis = redis.StrictRedis(host=options.engineRedisHost,
                          port=int(options.engineRedisPort), db=0)
    
    # Run the twisted client
    tracker = CrawlTracker(central_redis, engine_redis,
                           options.engineRedisHost, options.engineRedisPort, 
                           options.mock, options.psuedo, log_info)
    reactor.callWhenRunning(tracker.checkRedisQueue, 
                            int(options.queuePollTime))
    reactor.callWhenRunning(tracker.checkCrawlStatus,
                            int(options.statusPollTime))
    reactor.run()
