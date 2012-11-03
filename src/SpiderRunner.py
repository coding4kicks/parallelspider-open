#!/usr/bin/env python
"""
	Spider Runner

    Downloads the first page of the given site and saves a number of links to 
    a txt file. The number of links saved is the number of mappers that will
    be run. Next, it sets up a redis data-structure server. The runner then
    initiates parallel spider, passing all required info.
"""
import sys
import redis
import urllib

from datetime import datetime
from optparse import OptionParser

from Parser import *

class SpiderRunner:

    def __init__(self, site_list, analysis_info, redis_info, max_mappers):

        self.site_list = site_list 
        self.analysis_info = analysis_info
        self.redis_info = redis_info
        self.max_mappers = max_mappers

        # Create a time stamp (no querries should be issued in the same second)
        d = datetime.now()
        (y, m, d, h, mn) = (str(d.year), str(d.month), str(d.day), 
                            str(d.hour), str(d.minute))
        timestamp = y + "-" + m + "-" + d + "-" + h + "-" + mn

        # Create a list of Redis base key parts based on time and site name
        self.base_keys = []
        for site in self.site_list:
            base = site + "::" + timestamp
            self.base_keys.append(base)
    
           
    def execute(self):
        
        #print self.timestamp
        print self.site_list
        for x in self.site_list:
            print x
        for y in self.base_keys:
            print y

        print self.redis_info

        # Download initial page for each site
        # Later make asynchronous to speed up
        for site in self.site_list:
            f = urllib.urlopen(site)
            data = f.read()
            f.close

            # Hard code tags - later make variable of Analysis Info
            tag_list = ["p", "h1", "h2", "h3", "h4", "h5", "h6"]
            parser = Parser(site, tag_list)
            parser.run(data)
            links = parser.get_links()
            output = parser.get_output() # test only

            print links
            print output


        # Connect to Redis
        r = redis.StrictRedis(host=self.redis_info["host"],
                              port=int(self.redis_info["port"]), db=0)

        # Create keys for each site's link state: new, processing, finished
        for key in self.base_keys:
            new_links = key + "::new_links"
            processing_links = key + "::processing_links"
            finished_links = key + "::finished_links"

        r.set("new_links","self.")
        x = r.get("foo")
        print x


def main():
    """ Run program from the command line. """

    # Parse command line options and arguments.
    usage = "usage: %prog [options] <site1url,site2url,...>"
    parser = OptionParser(usage)

    # Analysis info from the command line (x:y,a:b,wtf:true).
    # Possibly add configuration file
    parser.add_option(
            "-a", "-A", "--analysisInfo", action="store", dest="analysisInfo", 
            help="A comma separated list of analysis options.")

    # Maximum number of mappers (controls download rate)
    parser.add_option(
            "-m", "-M", "--maxMappers", action="store", 
            default=5, dest="maxMappers", 
            help="Set maximum number of mappers. [default: %default]")

    # Redis info: host and port
    # redo defaulat localhost?
    parser.add_option(
            "-r", "-R", "--redisInfo", action="store",
            dest="redisInfo", help="Set Redis info.")

    # Argument is a comma separted list of site names
    (options, args) = parser.parse_args()

    # Make sure there is one and only one list of URLs
    if len(args) == 0:
        parser.error("Must specify list of site URLs")
    if len(args) > 1:
        parser.error("Can only specify 1 input list.")

    # Convert string argument to Python list
    site_list = args[0].split(",")

    # Convert Analysis info to Python Dictionary
    analysis_info = {}
    if options.analysisInfo:
        temp_list = options.analysisInfo.split(",")
        for item in temp_list:
            key, delimiter, value = item.partition('=')
            analysis_info[key] = value

    # Convert Redis info to Python Dictionary (keep default)
    redis_info = {}
    temp_list = options.redisInfo.split(",")
    for item in temp_list:
        key, delimiter, value = item.partition('=')
        redis_info[key] = value

    # Check max mappers is greater than 0
    max_mappers = int(options.maxMappers)
    if max_mappers < 1:
        parser.error("maxMappers must be greater than 0")
    
    #  Initialize and execute spider runner
    spider_runner = SpiderRunner(site_list, analysis_info, 
                                 redis_info, max_mappers) 
    spider_runner.execute()


if __name__ == "__main__":
    """ enable command line execution """
    sys.exit(main())
    

