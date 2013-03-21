#!/usr/bin/env python
"""
    spiderrunner - Downloads initial link set and runs parallelspider

    Downloads the first page for each given site 
    and saves a number of links to a txt file.
    The number of links saved is the number of mappers that will
    be run? Next, it sets up a redis data-structure server.
    The runner then initiates a ParallelSpider, passing all required info.

        ex. to call:    
        python SpiderRunner.py
        http://www.foxnews.com/ 
        -r host:ec2-50-17-32-136.compute-1.amazonaws.com,port:6379
        -m 3
"""

import sys
import redis
import cPickle
import datetime
import optparse
import lxml.html
import contextlib
import subprocess
import robotparser

from mrfeynman import Brain



class SpiderRunner(object):
    """
    Downloads initial links and runs parallelspider

    __init__ - constructor to initialize variables and create timestamp
    execute  - downloads the links and runs parallel spider for each site
    main     - executes the program from the command line
    """

    def __init__(self, site_list, redis_info, 
                 max_mappers, max_pages):
        """ 
        Initializes inputs and creates a timestamp

        Arguments:
        site_list       --  a list of urls to crawl 
        redis_info      --  host location and port of redis
        max_mappers     --  number of mappers to control concurrency
        max_pages       --  max number of pages to download

        Returns:
        data_location   --  location in S3 data is saved to
        ### must somehow communciate this to calling process

        max_mappers and max_pages default to 1 and 20 respectively.  This is
        for the free case.  Otherwise max_mappers should depend upon system
        load and available resources and max_pages should be specified by the
        user.

        TODO: save initial link into new_links???

        """

        self.site_list = site_list         
        self.redis_info = redis_info      
        self.max_mappers = max_mappers
        self.max_pages = max_pages

        # Create a time stamp (no querries should be issued in the same second
        # for the same website - default to cache??? refactor?)
        d = datetime.datetime.now()
        self.timestamp = '%d-%d-%d-%d-%d' % (d.year, d.month, d.day, 
                d.hour, d.minute)
        print self.timestamp
           
    def execute(self):
        """
        Downloads the first page and calls parallelspider
        
        Downloads the first page of links and saves them to redis,
        Then calls parallelspider, passing the following information:
          parallelspider.py location
          input file location (
          location to save output file
          spiderparser.py 
          max number of mappers to start
          redis info: host, port, and base key (site name + timestamp)
          max number of pages to download

        TODO: stop passing spiderparser.py and save on nodes instead,
        Then pass a file with all the required analysis info
        """

        # Connect to Redis
        r = redis.StrictRedis(host=self.redis_info["host"],
                              port=int(self.redis_info["port"]), db=0)

        # Set up configuration file
        config_file = r.get('config')
        config = cPickle.loads(config_file) 

        # Download initial page for each site
        # TODO: make asynchronous to speed things up for multiple sites
        for site in self.site_list:

            # Get robots.txt
            robots_txt = robotparser.RobotFileParser()
            robots_txt.set_url(site)
            robots_txt.read() 

            # Download and parse page
            page = lxml.html.parse(site)
            brain = Brain(site, config)
            output = brain.analyze(page, site, robots_txt, no_emit=True)
            links = brain.on_site_links

            # Create base part of Redis key from timestamp and site name
            base = '%s::%s' % (site, self.timestamp)
            new_link_set = '%s::new_links' % (base)
            
            # Add new links to Redis
            # Calculate number of breaks
            size = len(links)
            breaks, remainder = divmod(size, 250)
            if remainder > 0:
                breaks = breaks + 1
    
            # Initialize indices based upon batch size
            start = 0
            finish = 250
            i = 0

            # Add links to Engine Redis as a batch 
            # vice adding 1 at a time (max 255)
            while i < breaks:
                links_part = links[start:finish]

                # map: add single quotes around each element in list
                # join: combine elements to form a string for eval
                link_string = (',').join(map(lambda x: "'" + x + "'",
                                             links_part))

                # Add links, SECURITY - site name is user provided
                # but lxml.html.parse will catch if invalid link
                eval("r.sadd('" + new_link_set + "'," + link_string + ")") 

                # Set key expiration to 1 hour
                hour = 60 * 60
                r.expire(new_link_set, hour)

                # Increment all indices
                start = start + 250
                finish = finish + 250
                i = i + 1
              
            # Create valid file name for output 
            # TODO: file name should be based on crawl id
            base_path = base.replace("/","_").replace(":","-")
            file_name = '%s.txt' % (base_path)
            path_out = "/home/parallelspider/jobs/"
            file_path = path_out + file_name

            # Create input file: file name equals base key
            with open(file_path, "w+") as mapper_file:
                i = 1
                while i < self.max_mappers + 1:
                    mapper_file.write("mapper" + str(i) + "\n")
                    i = i + 1

            # Put input file on HDFS and call parallelspider
            # TODO: must switch to asynchronous for multiple sites
            # and deal with notifying calling process when complete?
            cmds = []
            cmds.append("dumbo put " + file_path + \
                        " /HDFS/parallelspider/jobs/" + file_name + \
                        " -hadoop starcluster")

            # Distributed mode
            cmds.append("dumbo start /home/parallelspider/parallelspider.py" \
                         " -input /HDFS/parallelspider/jobs/" + file_name + \
                         " -output /HDFS/parallelspider/out/" + base_path + \
                         " -file mrfeynman.py" + \
                         " -nummaptasks " + str(self.max_mappers) + \
                         " -cmdenv PYTHONIOENCODING=utf-8" + \
                         " -param redisInfo=" + \
                         "host:" + self.redis_info["host"] + \
                         ",port:" + self.redis_info["port"] + \
                         ",base:" + base + \
                         ",maxPages:" + str(self.max_pages) + \
                         " -hadoop starcluster")

            # Psuedo-distributed for testing
            cmds.append("dumbo start /home/parallelspider/parallelspider.py" \
                         " -input /home/parallelspider/jobs/" + file_name + \
                         " -output /home/parallelspider/out/" + base_path + \
                         " -file mrfeynman.py" + \
                         " -nummaptasks " + str(self.max_mappers) + \
                         " -cmdenv PYTHONIOENCODING=utf-8" + \
                         " -param redisInfo=" + \
                         "host:" + self.redis_info["host"] + \
                         ",port:" + self.redis_info["port"] + \
                         ",base:" + base + \
                         ",maxPages:" + str(self.max_pages))

            # Uncomment 1, comment 2 for testing in psuedo distributed
            #cmds.pop(1)
            cmds.pop(2)

            # Run the commands
            for cmd in cmds:
                #print "Running %s" % cmd
                subprocess.call(cmd, shell=True)


def main():
    """Run the program from the command line."""

    # Parse command line options and arguments.
    usage = "usage: %prog [options] <site1url,site2url,...>"
    parser = optparse.OptionParser(usage)

    # Maximum number of mappers (controls download rate)
    parser.add_option(
            "-m", "-M", "--maxMappers", action="store", 
            default=5, dest="maxMappers", 
            help="Set maximum number of mappers. [default: %default]")

    # Redis info: host and port
    # TODO: determine localhost and make default?
    parser.add_option(
            "-r", "-R", "--redisInfo", action="store",
            dest="redisInfo", help="Set Redis info.")

    # Total/max pages to download
    parser.add_option(
            "-t", "-T", "--maxPages", action="store",
            default=20, dest="maxPages",
            help="Set total/max pages to download. [default: %default]")

    # Argument is a comma separted list of site names
    (options, args) = parser.parse_args()

    # Make sure there is one and only one list of URLs
    if len(args) == 0:
        parser.error("Must specify list of site URLs")
    if len(args) > 1:
        parser.error("Can only specify 1 input list.")

    # Convert string argument to Python list
    site_list = args[0].split(",")

    # Convert Redis info to a Python dictionary
    # TODO: make argument if required or create default
    redis_info = {}
    temp_list = options.redisInfo.split(",")
    for item in temp_list:
        key, delimiter, value = item.partition(':')
        redis_info[key] = value

    # Check that max_mappers is greater than 0
    # TODO: make robust against float or string
    max_mappers = int(options.maxMappers)
    if max_mappers < 1:
        parser.error("maxMappers must be greater than 0")

    # Check total pages is greater than 0
    # TODO: make robust against float or string
    max_pages = int(options.maxPages)
    if max_pages < 1:
        parser.error("maxPages must be greater than 0")
    
    #  Initialize and execute spider runner
    spider_runner = SpiderRunner(site_list, redis_info, 
                                 max_mappers, max_pages) 
    spider_runner.execute()


if __name__ == "__main__":
    """ enable command line execution """
    sys.exit(main())
    

