from twisted.internet import reactor

import redis
import json # for mock test
import optparse


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

          # Add crawl to Sun Grid Engine
          # Should I move crawl info from central to engine redis?
          print "not mocking, serious"
          pass
  
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
