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

    TODO: figure out why Redis pipeline of new link addition breaks sometimes?
"""

import sys
import json
import copy
import redis
import logging
import urllib2
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

    def __init__(self, site_list, redis_info, max_mappers, max_pages,
                 crawl_info, psuedo, log_info):
        """ 
        Initializes inputs and creates a timestamp

        Arguments:
        site_list       --  a list of urls to crawl 
        redis_info      --  host location and port of redis
        max_mappers     --  number of mappers to control concurrency
        max_pages       --  max number of pages to download
        crawl_info      --  crawl id
        psuedo          --  psuedo distributed for testing
        log_info        --  logger and header info

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
        self.crawl_info = crawl_info
        self.psuedo = psuedo
        self.logger, log_header = log_info
        self.log_header = copy.deepcopy(log_header)
        self.log_header['msg_type'] = "Execute - "

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
        
        config_file = r.get(self.crawl_info)
        config = json.loads(config_file)

        # Download initial page for each site
        # TODO: make asynchronous to speed things up for multiple sites
        for site in self.site_list:

            # Get robots.txt
            robots_txt = robotparser.RobotFileParser()
            robots_txt.set_url(site)
            robots_txt.read() 

            # Download and parse page
            # TODO: need try catch so failure to parse doesn't loop forever
            # and need to report back failure to Spider Web
            if 'https' in site:
                page = lxml.html.parse(urllib2.urlopen(site))
            elif 'http' in site:
                page = lxml.html.parse(site)
            else: # file type not supported
                msg = ('File type not supported: {!s}').format(site) 
                self.logger.error(msg, extra=self.log_header)
                break
            brain = Brain(site, config)
            output = brain.analyze(page, site, robots_txt, no_emit=True)
            links = brain.on_site_links

            msg = """output: %s""" % (output)
            self.logger.debug(msg, extra=self.log_header)
            msg = """links: %s""" % (links)
            self.logger.debug(msg, extra=self.log_header)

            # Create base part of Redis key from timestamp and site name
            # TODO: fix crawl id
            base = '%s::%s' % (site, config['crawl_id'])
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

            for link in links:
                print link
            #break

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
            #cmds = []
            add_file = ("dumbo put " + file_path + \
                        " /HDFS/parallelspider/jobs/" + file_name + \
                        " -hadoop starcluster")
            subprocess.call(add_file, shell=True)

            # Distributed mode
            parallel_spider = ("dumbo start /home/parallelspider/parallelspider/spiderengine/parallelspider.py" \
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
            psuedo_dist = ("dumbo start /home/parallelspider/parallelspider/spiderengine/parallelspider.py" \
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

            # Logging
            msg = ('psuedo: {!s}').format(self.psuedo) 
            self.logger.debug(msg, extra=self.log_header)

            if self.psuedo:
                subprocess.Popen(psuedo_dist, shell=True)

                # Logging
                msg = ('cmd_line: {!s}').format(psuedo_dist) 
                self.logger.debug(msg, extra=self.log_header)

            else:
                subprocess.Popen(parallel_spider, shell=True)

                # Logging
                msg = ('cmd_line: {!s}').format(parallel_spider) 
                self.logger.debug(msg, extra=self.log_header)


# Helper Funcs
###############################################################################
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
    SPDR_TYPE = "runner"
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


# Command Line Crap & Initialization
###############################################################################
def main():
    """Run the program from the command line."""

    # Parse command line options and arguments.
    usage = "usage: %prog [options] <site1url,site2url,...>"
    parser = optparse.OptionParser(usage)

    # Crawl Info (where to find crawl info in Redis)
    parser.add_option(
            "-c", "-C", "--crawlInfo", action="store", 
            default='config', dest="crawlInfo", 
            help="Where crawl info is stored in Redis [default: %default]")

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

    # Psuedo Distributed (for easier testing on cluster)
    parser.add_option(
            "-d", "-D", "--psuedo", action="store_true", 
            default="", dest="psuedo", 
            help="Psuedo Distributed Mode. [default: False]")
    
    # Logging Level 
    parser.add_option(
            "-l", "-L", "--logging", action="store", 
            default="production", dest="log_level", 
            help="Set log level. [default: False]")

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

    # Set up logging
    options.log_level = "debug"
    #options.log_level = "develop"
    log_info = set_logging_level(level=options.log_level)
    logger, log_header = log_info
    log_header['msg_type'] = "Initialization - "
    msg = """starting options: %s""" % (options)
    logger.info(msg, extra=log_header)

    # Check total pages is greater than 0
    # TODO: make robust against float or string
    max_pages = int(options.maxPages)
    if max_pages < 1:
        parser.error("maxPages must be greater than 0")
    print options.psuedo
    #  Initialize and execute spider runner
    spider_runner = SpiderRunner(site_list, redis_info, 
                                 max_mappers, max_pages, 
                                 options.crawlInfo, options.psuedo,
                                 log_info) 
    spider_runner.execute()


if __name__ == "__main__":
    """ enable command line execution """
    sys.exit(main())
    

