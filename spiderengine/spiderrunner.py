#!/usr/bin/env python
"""
    spiderrunner - Downloads initial link set and runs parallelspider

    Downloads the first page for each given site and saves the links to 
    Engine Redis's new links set for that site.  Creates an input file for
    Parallel Spider, with the number of lines equal to the number of specified
    mappers.  Then executes Parallel Spider in either distributed or psuedo
    distributed mode, passing the required starting parameters.


    TODO: need try-catch so failure to parse doesn't loop forever
          and need to report back failure to Spider Web 
          (or check earlier in client?)
    TODO: import loggin vice copy and paste?
"""
import os
import sys
import json
import copy
import logging
import urllib2
import optparse
import subprocess
import robotparser

import redis
import lxml.html

from mrfeynman import Brain

###############################################################################
### Spider Runner
###############################################################################
class SpiderRunner(object):
    """
    Downloads initial links and runs parallelspider

    __init__ - constructor to initialize variables
    execute  - downloads the links and runs parallel spider for each site
    """

    def __init__(self, site_list, redis_info, max_mappers, max_pages,
                 crawl_id, psuedo, log_info, test=False):
        """ 
        Initialize inputs

        Args:
            site_list - a list of urls to crawl 
            redis_info - host location and port of redis
            max_mappers - number of mappers to control concurrency
            max_pages - max number of pages to download for each site
            crawl_id - crawl id
            psuedo - psuedo distributed for testing
            log_info - logger and header info
            test - boolean, True if testing

        Returns:
            command parameters - only used for testing, othewise parallel
            spiders are executed asynchronously for each site and they will
            indicate to the Spider Client through Engine Redis when they 
            are complete.
        """

        self.site_list = site_list         
        self.redis_info = redis_info      
        self.max_mappers = max_mappers
        self.max_pages = max_pages
        self.crawl_id = crawl_id
        self.psuedo, self.test = psuedo, test
        self._init_logging(log_info)

    def execute(self):
        """
        Downloads the first page and calls parallelspider
        
        Downloads the first page of links and saves them to redis,
        Then calls parallelspider, passing the following information:
          0) parallelspider.py file location
          1) file locations on HDFS or local (psudo dist mode)
          2) input file name
          3) output file path
          x) mrfeynman.py - used for analysis by parallel spider 
          4) max number of mappers to start
          x) utf encoding
          5-8) dumbo params:
                redis info: host, port, base key and max pages to download
          9) distributed mode (or not)
        """

        r = redis.StrictRedis(host=self.redis_info["host"],
                              port=int(self.redis_info["port"]), db=0)   
        config = json.loads(r.get(self.crawl_id))
        
        for site in self.site_list:

            robots_txt = _init_robot_txt(site, self.test)
            # Need to handle error here: i.e. 403
            page = _parse(site, self.test)
            
            if page == None:
                self.logger.error('File type not support for: %s', site, 
                                  extra=self.log_header)
                continue

            brain = Brain(site, config)
            output = brain.analyze(page, site, robots_txt, no_emit=True)
            links = brain.on_site_links
            print "Here da links"
            print links
            links.append(site) # make sure main page is analyzed
            links = list(set(links)) # remove duplicates
            base = ('{}::{}').format(site, config['crawl_id'])
            _batch_add_links_to_new(r, links, base)

            file_info = self._create_input_file(base)
            upload_cmd = _construct_upload_cmd(file_info)
            if not self.test:
                subprocess.call(upload_cmd, shell=True)

            # Construct and execute dumbo command for parallel spider
            dist_cmd = self._construct_ps_cmd('dist', base)
            psuedo_cmd = self._construct_ps_cmd('psuedo', base)
            if self.psuedo: # execute in psuedo distributed mode
                subprocess.Popen(psuedo_cmd, shell=True)
            elif self.test: # return values for testing
                return (dist_cmd, psuedo_cmd, upload_cmd, output)
            else: # execute in distributed mode
                subprocess.Popen(dist_cmd, shell=True)

            #if self.debug:
            #    self.logger.debug('output: %s', output, extra=self.log_header)
            #    self.logger.debug('links: %s', links, extra=self.log_header)

    def _create_input_file(self, base):
        """Create input file (name equals base escaped) for parallelspider."""
        file_name = _get_base_path(base) + '.txt'
        path_out = "/home/parallelspider/jobs/"
        if self.test:
            path = os.path.realpath(__file__).partition('spiderengine')[0]
            path_out = path + 'spiderengine/tests/unit-tests/jobs/'
        file_path = path_out + file_name
        with open(file_path, "w+") as mapper_file:
            i = 1
            while i < self.max_mappers + 1:
                mapper_file.write("mapper" + str(i) + "\n")
                i = i + 1
        return file_path, file_name

    def _construct_ps_cmd(self, mode, base):
        """Construct dumbo command for distributed or psuedo execution."""
        files_location = _get_files_location(mode)
        dist = ' -hadoop starcluster' if mode == 'dist' else ''
        base_path = _get_base_path(base)
        file_name = base_path + '.txt'
        cmd= ('dumbo start {0} -input {1}jobs/{2} '
              '-output {1}out/{3} -file mrfeynman.py -nummaptasks {4} '
              '-cmdenv PYTHONIOENCODING=utf-8 -param redisInfo=host:{5},'
              'port:{6},base:{7},maxPages:{8}{9}'
              ).format(_ps_location(), files_location, file_name, 
                       base_path, str(self.max_mappers), 
                       self.redis_info['host'], self.redis_info['port'], 
                       base, str(self.max_pages), dist)
        #if self.debug:
        #    self.logger.debug('Command: %s',cmd, extra=self.log_header)
        return cmd

    def _init_logging(self, log_info):
        "Initilize logging parameters."""
        self.logger, log_header = log_info
        self.log_header = copy.deepcopy(log_header)
        self.log_header['msg_type'] = "Execute - "
        self.debug = True if self.logger.getEffectiveLevel() == 10 else False


###############################################################################
### Helper Funcs
###############################################################################
def _init_robot_txt(site_url, test):
    """Initialize robot.txt for the specified site."""
    robots_txt = robotparser.RobotFileParser()
    if test:
        file_path = os.path.realpath(__file__).rpartition('/')[0] \
                    + '/tests/misc/fake_robot.txt'
        robots_txt.set_url(file_path)
    else:
        robots_txt.set_url(site_url + "robots.txt")
    try:
        robots_txt.read()
    except:
        rotots_txt = None
    print robots_txt
    return robots_txt

def _parse(link, test):
    """Download and parse page depending upon scheme."""
    if 'https' in link:
        page = lxml.html.parse(urllib2.urlopen(link))
    elif 'http' in link or test == True:
        page = lxml.html.parse(link)
    else: 
        page = None
    return page

def _batch_add_links_to_new(r, links, base):
    """Add new links as a batch to Engine Redis, Max batch size is 255."""
    new_links = ('{}::new_links').format(base)
    size = len(links) 
    batch_size = 250
    breaks, remainder = divmod(size, batch_size) # calc number of breaks
    if remainder > 0:   # reminder: crack babies are sad.
        breaks = breaks + 1
    start, finish, i = 0, batch_size, 0
    while i < breaks:
        link_batch = links[start:finish]
        r.sadd(new_links, *link_batch)
        start += batch_size
        finish += batch_size
        i += 1
    hour = 60 * 60
    r.expire(new_links, hour)

def _construct_upload_cmd(file_info):
    """Construct command to upload file to HDFS."""
    file_path, file_name = file_info
    cmd = ('dumbo put {} /HDFS/parallelspider/jobs/{} '
           '-hadoop starcluster').format(file_path, file_name)
    return cmd

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
    """
    import socket
    # Log message is spider type, host, unique run id, time, and message
    FORMAT = "spider%(spider_type)s %(host)s %(id)d %(asctime)s " + \
             "%(msg_type)s %(message)s"
    HOST = socket.gethostbyname(socket.gethostname())
    SPDR_TYPE = "runner"
    FILENAME = "/var/log/spider/spider" + SPDR_TYPE + ".log"
    log_header = {'id': 0, 'spider_type': SPDR_TYPE, 
                  'host': HOST, 'msg_type':'none'}
    if level == "develop": # to console
        logging.basicConfig(format=FORMAT, level=logging.INFO)
    elif level == "debug": # extra info
        logging.basicConfig(format=FORMAT, level=logging.DEBUG)
    else: # production, to file (default)
        logging.basicConfig(filename=FILENAME, format=FORMAT, 
                            level=logging.INFO)
    logger = logging.getLogger('spider' + SPDR_TYPE)
    return (logger, log_header)

def _ps_location():
    """parallelspider location on analysis engine."""
    return '/home/parallelspider/parallelspider/spiderengine/parallelspider.py'

def _get_files_location(mode):
    """Jobs & Output location on HDFS or local.""" 
    if mode == 'dist':
        return '/HDFS/parallelspider/'
    else:
        return '/home/parallelspider/'

def _get_base_path(base):
    """Construct file safe base path."""
    return base.replace("/","_").replace(":","-")


###############################################################################
### Command Line Crap & Initialization
###############################################################################
def main():
    """Run the program from the command line."""

    usage = "usage: %prog [options] <site1url,site2url,...>"
    parser = optparse.OptionParser(usage)
    parser.add_option(
            "-c", "-C", "--crawlInfo", action="store", 
            default='config', dest="crawlInfo", 
            help="Where crawl info is stored in Redis [default: %default]")
    parser.add_option(
            "-m", "-M", "--maxMappers", action="store", 
            default=5, dest="maxMappers", 
            help="Set maximum number of mappers. [default: %default]")
    parser.add_option(
            "-r", "-R", "--redisInfo", action="store",
            dest="redisInfo", help="Set Redis info.")
    parser.add_option(
            "-t", "-T", "--maxPages", action="store",
            default=20, dest="maxPages",
            help="Set total/max pages to download. [default: %default]")
    parser.add_option(
            "-d", "-D", "--psuedo", action="store_true", 
            default="", dest="psuedo", 
            help="Psuedo Distributed Mode. [default: False]")
    parser.add_option(
            "-l", "-L", "--logging", action="store", 
            default="production", dest="log_level", 
            help="Set log level. [default: False]")
    (options, args) = parser.parse_args()

    if len(args) == 0:
        parser.error("Must specify list of site URLs")
    if len(args) > 1:
        parser.error("Can only specify 1 input list.")
    site_list = args[0].split(",")

    redis_info = {}
    temp_list = options.redisInfo.split(",")
    for item in temp_list:
        key, delimiter, value = item.partition(':')
        redis_info[key] = value

    max_mappers = int(options.maxMappers)
    if max_mappers < 1:
        parser.error("maxMappers must be greater than 0")
    max_pages = int(options.maxPages)
    if max_pages < 1:
        parser.error("maxPages must be greater than 0")
    print options.psuedo

    options.log_level = "debug"
    #options.log_level = "develop"
    log_info = set_logging_level(level=options.log_level)
    logger, log_header = log_info
    log_header['msg_type'] = "Initialization - "
    msg = """starting options: %s""" % (options)
    logger.info(msg, extra=log_header)

    spider_runner = SpiderRunner(site_list, redis_info, 
                                 max_mappers, max_pages, 
                                 options.crawlInfo, options.psuedo,
                                 log_info) 
    spider_runner.execute()

if __name__ == "__main__":
    """ enable command line execution """
    sys.exit(main())
