""" Spider Cleaner

    Downloads results from HDFS and Redis.
    Turns those results into JSON format need by Spider Web.
    Uploads the results to S3 and notifies Spider Server.

"""

import sys
import redis
import json
import optparse

class SpiderCleaner(object):
    """
    """

    def __init__(self, redis_info, crawl_info):
        """ 

        """
       
        self.redis_info = redis_info      
        self.crawl_info = crawl_info
           
    def execute(self):
        """
        """

        # Connect to Redis
        r = redis.StrictRedis(host=self.redis_info["host"],
                              port=int(self.redis_info["port"]), db=0)

        # Set up configuration file
        #config_file = r.get('config')
        print self.crawl_info
        config_file = r.get(self.crawl_info)
        #config = json.loads(config_file)

        print "hello"

def main():
    """Handle command line options"""

    # Parse command line options and arguments.
    usage = "usage: %prog [options] <site1url,site2url,...>"
    parser = optparse.OptionParser(usage)

    # Crawl Info (where to find crawl info in Redis)
    parser.add_option(
            "-c", "-C", "--crawlInfo", action="store", 
            default='config', dest="crawlInfo", 
            help="Where crawl info is stored in Redis [default: %default]")

    # Redis info: host and port
    # TODO: determine localhost and make default?
    parser.add_option(
            "-r", "-R", "--redisInfo", action="store",
            dest="redisInfo", help="Set Redis info.")

    # Argument is a comma separted list of site names
    (options, args) = parser.parse_args()

    # Convert Redis info to a Python dictionary
    # TODO: make argument if required or create default
    redis_info = {}
    temp_list = options.redisInfo.split(",")
    for item in temp_list:
        key, delimiter, value = item.partition(':')
        redis_info[key] = value

    
    #  Initialize and execute spider runner
    spider_cleaner = SpiderCleaner(redis_info, options.crawlInfo) 
    spider_cleaner.execute()

if __name__ == "__main__":
    """Enable command line execution """
    sys.exit(main())

