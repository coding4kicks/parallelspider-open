#!/usr/bin/env python
"""
	spiderrunner - Downloads initial link set and runs parallelspider

    Downloads the first page for each given site and saves a number of links to 
    a txt file. The number of links saved is the number of mappers that will
    be run? Next, it sets up a redis data-structure server. The runner then
    initiates a ParallelSpider, passing all required info.

        ex. to call:    
        python SpiderRunner.py
        http://www.foxnews.com/ 
        -r host:ec2-50-17-32-136.compute-1.amazonaws.com,port:6379
        -m 3
"""

import sys
import redis
import urllib
import datetime
import optparse
import contextlib
import subprocess

import spiderparser


class SpiderRunner(object):
    """
    SpiderRunner - downloads initial links and runs parallelspider

    __init__ - constructor to initialize variables and create timestamp
    execute  - downloads the links and runs parallel spider for each site
    main     - executes the program from the command line
    """

    def __init__(self, site_list, analysis_info, redis_info, 
                 max_mappers, max_pages):
        """ 
        Initializes inputs and creates a timestamp

        Arguments:
        site_list       --  a list of urls to crawl 
        analysis_info   --  tags and info to analyze
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
        self.analysis_info = analysis_info 
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

        # Download initial page for each site
        # TODO: make asynchronous to speed things up for multiple sites
        for site in self.site_list:
            with contextlib.closing(urllib.urlopen(site)) as f:
                data = f.read()
            
            # Security for false site name in eval
            # ??? could still breach with fake website ???
            if data is None:
                break

            # Hard code tags - later make variable of Analysis Info
            tag_list = ["p", "h1", "h2", "h3", "h4", "h5", "h6"]
            parser = spiderparser.Parser(site, tag_list)
            parser.run(data)
            links = parser.get_links()
            output = parser.get_output() # TEST only

            # Create base part of Redis key from timestamp and site name
            base = '%s::%s' % (site, self.timestamp)
            new_link_set = '%s::new_links' % (base)
            
            # Add new links to Redis
            # Process as batch vice adding 1 at a time (max 255)

            # Calculate number of breaks
            size = len(links)
            breaks, remainder = divmod(size, 250)
            if remainder > 0:
                breaks = breaks + 1
    
            # Initialize indices based upon batch size
            start = 0
            finish = 250
            i = 0

            while i < breaks:
                links_part = links[start:finish]

                # map: add single quotes around each element in list
                # join: combine elements to form a string for eval
                link_string = (',').join(map(lambda x: "'" + x + "'",
                                             links_part))

                # Add links, ??? SECURITY ??? - site name is user provided
                eval("r.sadd('" + new_link_set + "'," + link_string + ")") 

                # Set key expiration to 1 hour
                hour = 60 * 60
                r.expire(new_link_set, hour)

                # Increment all indices
                start = start + 250
                finish = finish + 250
                i = i + 1
              
            # Create valid file name for output  
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

            # Call ParallelSpider (MapReduce)
            # must switch to asynchronous later for multiple sites

            cmds = []

            cmds.append("dumbo put " + file_path + \
                        " /HDFS/parallelspider/jobs/" + file_name + \
                        " -hadoop starcluster")

            #port = self.redis_info["port"]
            #port = str(port)

            #print file_name
            #print base_path
            #print base

            # Distributed mode
            cmds.append("dumbo start /home/parallelspider/ParallelSpider.py" \
                         " -input /HDFS/parallelspider/jobs/" + file_name + \
                         " -output /HDFS/parallelspider/out/" + base_path + \
                         " -file spiderparser.py" + \
                         " -nummaptasks " + str(self.max_mappers) + \
                         " -param redisInfo=" + \
                         "host:" + self.redis_info["host"] + \
                         ",port:" + self.redis_info["port"] + \
                         ",base:" + base + \
                         ",maxPages:" + str(self.max_pages) + \
                         " -hadoop starcluster")

            # Psuedo-distributed for testing
            cmds.append("dumbo start /home/parallelspider/ParallelSpider.py" \
                         " -input /home/parallelspider/jobs/" + file_name + \
                         " -output /home/parallelspider/out/" + base_path + \
                         " -file spiderparser.py" + \
                         " -nummaptasks " + str(self.max_mappers) + \
                         " -param redisInfo=" + \
                         "host:" + self.redis_info["host"] + \
                         ",port:" + self.redis_info["port"] + \
                         ",base:" + base + \
                         ",maxPages:" + str(self.max_pages))

            # uncomment 1, comment 2 for testing in psuedo distributed
            #cmds.pop(1)
            cmds.pop(2)


            #print cmds[0]

            # run the commands
            for cmd in cmds:
                print "Running %s" % cmd
                subprocess.call(cmd, shell=True)

            # TEST REDIS
            #mem = r.smembers(new_link_set)
            #print mem


def main():
    """ Run program from the command line. """

    # Parse command line options and arguments.
    usage = "usage: %prog [options] <site1url,site2url,...>"
    parser = optparse.OptionParser(usage)

    # Analysis info from the command line.
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

    # Convert Analysis info to Python Dictionary
    analysis_info = {}
    if options.analysisInfo:
        temp_list = options.analysisInfo.split(",")
        for item in temp_list:
            key, delimiter, value = item.partition(':')
            analysis_info[key] = value

    # Convert Redis info to Python Dictionary (keep default)
    redis_info = {}
    temp_list = options.redisInfo.split(",")
    for item in temp_list:
        key, delimiter, value = item.partition(':')
        redis_info[key] = value

    # Check max mappers is greater than 0
    max_mappers = int(options.maxMappers)
    if max_mappers < 1:
        parser.error("maxMappers must be greater than 0")

    # Check total pages is greater than 0
    max_pages = int(options.maxPages)
    if max_pages < 1:
        parser.error("maxPages must be greater than 0")

    
    #  Initialize and execute spider runner
    spider_runner = SpiderRunner(site_list, analysis_info, 
                                 redis_info, max_mappers, max_pages) 
    spider_runner.execute()


if __name__ == "__main__":
    """ enable command line execution """
    sys.exit(main())
    

