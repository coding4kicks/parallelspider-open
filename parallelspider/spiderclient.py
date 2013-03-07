from twisted.internet import reactor

import redis
import json # for mock test

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

        # Add it to Sun Grid Engine
        print('starting crawl job')

        # FOR TESTING
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


# hardcode for now
# Central Redis Info 
central_redis_info = {'host': 'localhost', 'port': 6379}
central_redis = redis.StrictRedis(host=central_redis_info["host"],
                      port=int(central_redis_info["port"]), db=0)
# local redis is for one particular analysis engine
local_redis_info = {'host': 'localhost', 'port': 6389}
local_redis = redis.StrictRedis(host=local_redis_info["host"],
                      port=int(local_redis_info["port"]), db=0)


tracker = CrawlTracker(central_redis, local_redis)
reactor.callWhenRunning(tracker.checkRedisQueue)
reactor.callWhenRunning(tracker.checkCrawlStatus)
reactor.run()
