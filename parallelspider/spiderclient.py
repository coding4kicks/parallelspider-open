from twisted.internet import reactor

import redis
import json # for mock test
import optparse


class MockCrawl(object):
    def __init__(self, crawl_id, max_pages, local_redis):
        self.crawl_id = crawl_id
        self.max_pages = max_pages
        self.local_redis = local_redis
        self.count = 0

    def run(self):

        if self.count < self.max_pages:
            self.local_redis.set(self.crawl_id + "_count", self.count)
            self.count = self.count + 100 # Normal speed
            #self.count = self.count + 50 # Slow speed
            #self.count = self.count + 150 # Fast speed
            #print self.count

        else:
            self.local_redis.set(self.crawl_id + "_count", -2)

        reactor.callLater(5, self.run)

class CrawlTracker(object):
  """ Class to handle analysis job initialization and tracking """

  def __init__(self, central_redis, local_redis):
    self.crawlQueue = []
    self.central_redis = central_redis
    self.local_redis = local_redis

  def checkRedisQueue(self):
    """ Checks the Central Redis server for jobs and passes them to Grid Engine.
        Places all jobs in the crawl queue with crawl info location
    """
    
    # Get a crawlid  from the central queue
    crawl_id = self.central_redis.lpop('crawl_queue') 

    # Only do something if a crawl exists
    if crawl_id is not None:

        # Get the crawl info from central redis
        crawl_info = self.central_redis.get(crawl_id)

        # Add crawl info to local
        self.local_redis.set(crawl_id, crawl_info)

        # Add crawl to the crawl queue to monitor
        self.crawlQueue.append(crawl_id)

        ###
        ### Add it to Sun Grid Engine
        ### (should enable and disable depending upon if mocking remote)
        ###
        print('starting crawl job')

        # FOR TESTING
        # (should enable and disable depending upon if mocking remote)
        crawl_data = json.loads(crawl_info)
        crawl_details = crawl_data['crawl']
        if 'maxPages' in crawl_details:
            max_pages = crawl_details['maxPages']
        else:
            max_pages = 20
        mock = MockCrawl(crawl_id, max_pages, local_redis)
        mock.run()
        # END TESTING
  
    reactor.callLater(1, self.checkRedisQueue)
  
  def checkCrawlStatus(self):
    """ Checks the status of all crawls in the crawl queue 
        Updates Central Redis wit page count, or -2 when complete
    """

    for crawl_id in self.crawlQueue:

        # Retrieve page count from local and set in central redis
        #print "retrieving crawl status for " + crawl_id
        page_count = self.local_redis.get(crawl_id + "_count")
        self.central_redis.set(crawl_id + "_count", page_count)

        # If page count is complete (-2), remove from queue
        if page_count == -2:
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

    # Local Redis host info - default is localhost
    parser.add_option(
            "-l", "-L", "--localRedisHost", action="store", 
            default="localhost", dest="localRedisHost", 
            help="Set Local Redis host information. [default: %default]")

    # Central Redis port info - default is 6379
    parser.add_option(
            "-q", "-Q", "--localRedisPort", action="store", 
            default="6379", dest="localRedisPort", 
            help="Set Local Redis port information. [default: %default]")

    (options, args) = parser.parse_args()
    central_redis_host = options.centralRedisHost
    central_redis_port = int(options.centralRedisPort)
    local_redis_host = options.centralRedisHost
    local_redis_port = int(options.centralRedisPort)
    if central_redis_port < 1:
        parser.error("Central Redis port number must be greater than 0")
    if local_redis_port < 1:
        parser.error("Central Redis port number must be greater than 0")

    # Central Redis info 
    central_redis_info = {'host': central_redis_host,
                          'port': central_redis_port}
    central_redis = redis.StrictRedis(host=central_redis_info["host"],
                          port=int(central_redis_info["port"]), db=0)
    # Local Redis info - local to an analysis engine
    local_redis_info = {'host': local_redis_host,
                        'port': local_redis_port}
    local_redis = redis.StrictRedis(host=local_redis_info["host"],
                          port=int(local_redis_info["port"]), db=0)

    # Run twisted client
    tracker = CrawlTracker(central_redis, local_redis)
    reactor.callWhenRunning(tracker.checkRedisQueue)
    reactor.callWhenRunning(tracker.checkCrawlStatus)
    reactor.run()
