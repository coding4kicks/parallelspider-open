from twisted.internet import reactor

import redis
import json # for mock test
import optparse
import subprocess


class MockCrawl(object):
    def __init__(self, crawl_id, max_pages, engine_redis):
        self.crawl_id = crawl_id
        self.max_pages = max_pages
        self.engine_redis = engine_redis
        self.count = 0

    def run(self):

        if self.count < self.max_pages:
            self.engine_redis.set(self.crawl_id + "_count", self.count)
            self.count = self.count + 100 # Normal speed
            #self.count = self.count + 50 # Slow speed
            #self.count = self.count + 150 # Fast speed
            #print self.count

        else:
            self.engine_redis.set(self.crawl_id + "_count", -2)

        reactor.callLater(5, self.run)

class CrawlTracker(object):
  """ Class to handle analysis job initialization and tracking """

  def __init__(self, central_redis, engine_redis, mock):
    self.crawlQueue = []
    self.central_redis = central_redis
    self.engine_redis = engine_redis
    self.mock = mock
    self.max_pages = 20 # Default Free Ride
    self.mappers = 3

  def checkRedisQueue(self):
    """ Checks the Central Redis server for jobs and passes them to Grid Engine.
        Places all jobs in the crawl queue with crawl info location
    """
    
    # Get a crawlid  from the central queue
    crawl_id = self.central_redis.lpop('crawl_queue') 

    # Only do something if a crawl exists
    if crawl_id is not None:

        # Get the crawl info from central redis
        web_crawl_json = self.central_redis.get(crawl_id)       
        web_crawl_info = json.loads(web_crawl_json)
        web_crawl = web_crawl_info['crawl']

        # Convert crawl info to format expected by Spider Engine
        crawl = {}

        if 'primarySite' in web_crawl:
            # Only 1 site for now, TODO: append 'additionalSites'
            site_list = web_crawl['primarySite']
            
        else:
            'error, error loan ranger'

        if 'maxPages' in web_crawl:
            self.max_pages = web_crawl['maxPages']

            # Asjust mappers based upon pages (TODO: benchmark)
            if self.max_pages > 100:
                self.mappers = 20
            elif self.max_pages > 20:
                self.mappers = 5
        
        if 'externalSites' in web_crawl:
            crawl['analyze_external_pages'] = web_crawl['externalSites']

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

        if 'wordContexts' in web_crawl:
            crawl['context_search_tag'] = web_crawl['wordContexts']

        # Predefined lists (TODO: make more, put into redis, load in init)
        predefinedRings = {'stopWords': ['and','but','a','on','off','again']}

        if 'predefinedSynRings' in web_crawl:
            for ring in web_crawl['predefinedSynRings']:
                name = ring['name']
                crawl['wordnet_lists'] = {}
                if name in predefinedRings:
                    list = predefinedRings[name]
                    crawl['wordnet_lists'][name] = list
                else:
                    print 'error error should not be here'

        crawl_info = json.dumps(crawl)

        # TEMP - set into config
        self.engine_redis.set('config', crawl_info)

        # Add crawl info to local
        self.engine_redis.set(crawl_id, crawl_info)

        # Add crawl to the crawl queue to monitor
        self.crawlQueue.append(crawl_id)

        # If mocking then fake the funk.
        if self.mock:

          print('starting crawl job')

          crawl_data = json.loads(crawl_info)
          crawl_details = crawl_data['crawl']
          if 'maxPages' in crawl_details:
              max_pages = crawl_details['maxPages']
          else:
              max_pages = 20
          mocker = MockCrawl(crawl_id, max_pages, engine_redis)
          mocker.run()
          # END TESTING

        # Otherwise it's the real deal
        else:
            print self.max_pages
            # Execute the crawl
            # TODO: Sun Grid Engine
            print site_list
            cmd_line = "python spiderrunner.py " + site_list + \
                     " -r host:ec2-23-20-71-90.compute-1.amazonaws.com," + \
                     "port:6380 -m 3 -t " + str(self.max_pages)          
            p = subprocess.Popen(cmd_line, shell=True)          
          
  
    reactor.callLater(1, self.checkRedisQueue)
  
  def checkCrawlStatus(self):
    """ Checks the status of all crawls in the crawl queue 
        Updates Central Redis wit page count, or -2 when complete
    """

    for crawl_id in self.crawlQueue:

        # Retrieve page count from engine and set in central redis
        #print "retrieving crawl status for " + crawl_id
        page_count = self.engine_redis.get(crawl_id + "_count")
        self.central_redis.set(crawl_id + "_count", page_count)
        # If page count is complete (-2), remove from queue
        if page_count == "-2":
            self.crawlQueue.remove(crawl_id)

    reactor.callLater(5, self.checkCrawlStatus)


if __name__ == "__main__":

    # Parse command line options and arguments.
    usage = "usage: %prog [options]"
    parser = optparse.OptionParser(usage)

    # Central Redis host info - default is localhost
    parser.add_option(
            "-c", "-C", "--centralRedisHost", action="store", 
            default="localhost", dest="centralRedisHost", 
            help="Set Central Redis host information. [default: %default]")

    # Central Redis port info - default is 6379
    parser.add_option(
            "-p", "-P", "--centralRedisPort", action="store", 
            default="6379", dest="centralRedisPort", 
            help="Set Central Redis port information. [default: %default]")

    # Engine Redis host info - default is localhost
    parser.add_option(
            "-e", "-E", "--engineRedisHost", action="store", 
            default="localhost", dest="engineRedisHost", 
            help="Set Local Redis host information. [default: %default]")

    # Engine Redis port info - default is 6380
    parser.add_option(
            "-q", "-Q", "--engineRedisPort", action="store", 
            default="6380", dest="engineRedisPort", 
            help="Set Local Redis port information. [default: %default]")

    # Mock remote Analysis Engine by faking page count
    parser.add_option(
            "-m", "-M", "--mock", action="store_true", 
            default="", dest="mock", 
            help="Mock Analysis Engine. [default: False]")

    (options, args) = parser.parse_args()
    if int(options.centralRedisPort) < 1:
        parser.error("Central Redis port number must be greater than 0")
    if int(options.engineRedisPort) < 1:
        parser.error("Engine Redis port number must be greater than 0")

    # Central Redis info 
    central_redis = redis.StrictRedis(host=options.centralRedisHost,
                          port=int(options.centralRedisPort), db=0)
    # Engine Redis info - local to an analysis engine
    engine_redis = redis.StrictRedis(host=options.engineRedisHost,
                          port=int(options.engineRedisPort), db=0)

    # Run twisted client
    tracker = CrawlTracker(central_redis, engine_redis, options.mock)
    reactor.callWhenRunning(tracker.checkRedisQueue)
    reactor.callWhenRunning(tracker.checkCrawlStatus)
    reactor.run()
