""" Spider Cleaner

    Downloads results from HDFS and Redis.
    Turns those results into JSON format need by Spider Web.
    Uploads the results to S3 and notifies Spider Server.

"""

import os
import sys
import json
import time
import copy
import redis
import urllib
import logging
import optparse
import subprocess


import boto
import boto.s3.key


class SpiderCleaner(object):
    """
    """

    def __init__(self, redis_info, crawl_info, psuedo, log_info):
        """ 
        args:
            redis_info - local Engine Redis instance
            crawl_info - crawl details, needed for cleanup
            psuedo - True for psuedo distributed testing
            log_info - logger and log header
        """   
        self.redis_info = redis_info      
        self.crawl_info = crawl_info
        self.psuedo_dist = psuedo
        self.logger, log_header = log_info
        self.log_header = copy.deepcopy(log_header)
        self.log_header['msg_type'] = "Execute - "

    def execute(self):
        """
        """

        # Connect to Redis
        r = redis.StrictRedis(host=self.redis_info["host"],
                              port=int(self.redis_info["port"]), db=0)

        # Set up configuration file
        #config_file = r.get('config')
        config_file = r.get(self.crawl_info)
        config = json.loads(config_file)

        # All possible analysis types
        all_analyses = ['visible', 'headline', 'hidden', 'text', 'all',
                        'external', 'wordContexts', 'predefinedSynRings']

        # Types of anlayis acutally performed
        analysis_types = []

        # TEXT
        if ('text_request' in config and 
            config['text_request'] == True):
            analysis_types.append('visible')

        if ('header_request' in config and 
            config['header_request'] == True):
            analysis_types.append('headline')

        if ('meta_request' in config and 
            config['meta_request'] == True):
            analysis_types.append('hidden')

        # LINKS
        if ('a_tags_request' in config and 
            config['a_tags_request'] == True):
            analysis_types.append('text')

        if ('all_links_request' in config and 
            config['all_links_request'] == True):
            analysis_types.append('all')

        if ('external_links_request' in config and 
            config['external_links_request'] == True):
            analysis_types.append('external')

        # CONTEXT
        if ('context_search_tag' in config and
            len(config['context_search_tag']) > 0):
            analysis_types.append('wordContexts')                

        # SYNONYMS
        if 'wordnet_lists' in config:
            analysis_types.append('predefinedSynRings')

        # Content (internal/external) types performed
        content_types = ['internal'] # TODO: allow no internal
        if ('analyze_external_pages' in config and
           config['analyze_external_pages'] == True):
            content_types.append('external')

        # Variables for analysis types
        analysis = {}
        analysis['internal'] = {"key": "i_", "web_name": ""}
        analysis['external'] = {"key": "e_", "web_name": ""}
        analysis["visible"] = {"key": "text", "web_name": "visibleText"} 
        analysis["headline"] = {"key": "head", "web_name": "headlineText"} 
        analysis["hidden"] = {"key": "meta", "web_name": "hiddenText"}
        analysis["text"] = {"key": "atag", "web_name": "linkText"}
        analysis["all"] = {"key": "link", "web_name": "allLinks"}
        analysis["external"] = {"key": "extl", "web_name": "externalDomains"}
        analysis["wordContexts"] = {"key": "cntw", "web_name": "context"}
        analysis["predefinedSynRings"] = {"key": "wdnt", "web_name": "synonymRings"}

        # Analysis to be output (converted to json and uploaded to S3)
        finished_analysis = {}
        finished_analysis['name'] = config['name']
        finished_analysis['date'] = config['date']
        crawl_time = config['time']
        start_time = time.time()
        
        #TODO: pull from config/calculate end here prior to upload

        if 'internal' in content_types:
            finished_analysis['internal'] = True
        else:
            finished_analysis['internal'] = True
            
        if 'external' in content_types:
            finished_analysis['external'] = True
        else:
            finished_analysis['external'] = False

        finished_analysis['sites'] = []

        if isinstance(config['sites'], (str, unicode)):
            site_list = config['sites'].split(',')
        else:
            site_list = config['sites']

        # Logging
        msg = ('sites: {!s}').format(site_list) 
        self.logger.debug(msg, extra=self.log_header)
        msg = ('analysis: {!s}').format(analysis_types) 
        self.logger.debug(msg, extra=self.log_header)
        msg = ('content: {!s}').format(content_types) 
        self.logger.debug(msg, extra=self.log_header)

        # Format results for each site
        for site in site_list:

            site_results = {}
            
            # Construct file name details
            base = '%s::%s' % (site, config['crawl_id'])
            base_path = base.replace("/","_").replace(":","-")

            # Download master file from HDFS if psudeo distributed
            if not self.psuedo_dist:
                # TODO: unix tee into separate files & filter and sort and head
                # if able, or move to MapReduce solution
                cmd_line = ("dumbo cat /HDFS/parallelspider/out/{!s}/part-00000 "
                           "-hadoop starcluster > /home/parallelspider/out/{!s} "
                           ).format(base_path, base_path)
                out = subprocess.call(cmd_line, shell=True)

            # Format both internal and external results
            for c_type in ['internal','external']:
                # If analysis not performed, create empty placeholders and exit
                if c_type not in content_types:
                    
                    placeholders = {'visibleText': {}, 'hiddenText': {}, 'headlineText': {},
                    'allLinks': {}, 'externalDomains': {}, 'linkText': {},
                    'searchWords': {}, 'context': [],
                    'synonymRings': [], 'summary': {'pages':{'count':0}, 'words':{'count':0}},
                    'selectors': {} }
                    
                    if c_type == 'internal':
                        site_results['internalResults'] = placeholders
                    else:
                        site_results['externalResults'] = placeholders
                        
                    # exit loop
                    continue
                
                results = {} # Holder for specific results
                
                for a_type in all_analyses:
                    # Create the correct key for Spider Web name
                    results[analysis[a_type]['web_name']] = {}
                    
                    # Break from loop if no analysis performed
                    # or if it require special handling
                    if a_type not in analysis_types or a_type == 'wordContexts':
                        continue

                    # Logging
                    msg = ('{!s} cleaning up analysis: {!s}'
                           ).format(site, analysis[a_type]['web_name']) 
                    self.logger.debug(msg, extra=self.log_header)

                    # Create the key to grep/filter the master file by
                    key = analysis[a_type]['key'] + analysis[c_type]['key']

                    # Cat the master file into the sort filter
                    cwd = "/home/parallelspider/out/"
                    cmd_line = ("cat {!s} | "
                                "grep '{!s}' | "
                                "sort -k 2 -n -r | "
                                "head -n 150"
                                ).format(base_path, key)
                    
                    try:
                        out = subprocess.check_output(cmd_line, shell=True,
                                                      cwd=cwd)
                    except:
                        msg = ('Failed to process pipeline for {0}'
                               ).format(a_type) 
                        self.logger.debug(msg, extra=self.log_header)
 

                    self.logger.debug("Done with subprocess",
                                       extra=self.log_header)

                    # Handle Word Analysis Types
                    if a_type in ['visible','headline', 'hidden', 'text']:
                         
                        # Process words
                        words = []

                        # Last line of split is junk
                        for i, line in enumerate(out.split('\n')[:-1]):

                            try:
                                word = {}
                                word['rank'] = i + 1
                                w, c = line.split('\t')
                                # Remove the key 
                                if self.psuedo_dist:
                                    # and end quote
                                    word['word'] = w.split(key)[1][:-1]
                                else:
                                    word['word'] = w.split(key)[1]
                                word['count'] = c
                                word['pages'] = []
                                word['tags'] = []
                                words.append(word)

                            except:
                                # error unpacking line
                                # TODO: figure out why it blows up sometimes.
                                pass


                        results[analysis[a_type]['web_name']]['words'] = words 

                        self.logger.debug("Done handling text",
                                           extra=self.log_header)

                    #TODO: Handle Links
                    if a_type in ['all']:
                         
                        # Process words
                        links = []

                        # Last line of split is junk
                        for i, line in enumerate(out.split('\n')[:-1]):
                            try:
                                link = {}
                                link['rank'] = i + 1
                                l, c = line.split('\t')
                                # Remove the key 
                                if self.psuedo_dist:
                                    # and end quote
                                    link['link'] = l.split(key)[1][:-1]
                                else:
                                    link['link'] = l.split(key)[1]
                                link['count'] = c
                                link['pages'] = []
                                link['words'] = []
                                links.append(link)
                            except:
                                # Why is the split blowing up?
                                pass

                        results[analysis[a_type]['web_name']]['links'] = links 

                        self.logger.debug("Done handling all links",
                                           extra=self.log_header)

                    
                    #TODO: Handle Domains
                    if a_type in ['external']:
                         
                        # Process words
                        domains = []

                        # Last line of split is junk
                        for i, line in enumerate(out.split('\n')[:-1]):

                            try:
                                domain = {}
                                domain['rank'] = i + 1
                                d, c = line.split('\t')
                                # Remove the key 
                                if self.psuedo_dist:
                                    # and end quote
                                    domain['domain'] = d.split(key)[1][:-1]
                                else:
                                    domain['domain'] = d.split(key)[1]
                                domain['count'] = c
                                domain['pages'] = []
                                domain['words'] = []
                                domain['links'] = []
                                domains.append(domain)

                            except:
                                # error unpacking line
                                # TODO: figure out why it blows up sometimes.
                                pass


                        results[analysis[a_type]['web_name']]['domains'] \
                            = domains 

                        self.logger.debug("Done handling external links",
                                           extra=self.log_header)

                # Handle Context
                # Handling as a Python string, may blow up on large data
                if 'wordContexts' in analysis_types:

                    # Logging
                    msg = ('{!s} cleaning up analysis: wordContexts'
                           ).format(site) 
                    self.logger.debug(msg, extra=self.log_header)

                    # Word contexts are in a list
                    results[analysis['wordContexts']['web_name']] = []

                    # Create the key to grep/filter the master file by
                    key = analysis['wordContexts']['key'] + analysis[c_type]['key']
                    
                    cwd = "/home/parallelspider/out/"
                    cmd_line = ("cat {!s} | "
                                "grep '{!s}' "
                                ).format(base_path, key)

                    try:
                        out = subprocess.check_output(cmd_line, shell=True,
                                                      cwd=cwd)
                    except:
                        msg = ('Failed to process pipeline for {0}'
                               ).format('wordContexts') 
                        self.logger.debug(msg, extra=self.log_header)

                    self.logger.debug("Done with subprocess",
                                       extra=self.log_header)

                    # Set up dictioary for context words
                    contexts = {}
                    for word in config['context_search_tag']:
                        contexts[word] = []


                    # Extract info and put into list for each context word
                    for line in out.split('\n')[:-1]:

                        try:
                            # Extract word and tuple
                            w, t = line.split('\t')

                            # Strip key and clean word
                            word = w.split(key)[1][:-1]

                            # Split and clean tuple
                            ct, cw = t.split(", u'")
                            count = ct[1:]
                            context = cw[:-2]

                            contexts[context].append((int(count), word))
 
                        except:
                            # error unpacking line
                            # TODO: figure out why it blows up sometimes.
                            pass

                    # Sort and reformat words list for each context word
                    for j, context in enumerate(contexts):

                        # Sort the word for the context
                        contexts[context].sort(reverse=True)

                        words = []
                        total_count = 0

                        for i, tup in enumerate(contexts[context]):
                            word = {}
                            word['rank'] = i + 1
                            c, w = tup
                            # Remove the key 
                            word['word'] = w
                            word['count'] = c
                            word['pages'] = []
                            word['tags'] = []
                            words.append(word)
                            total_count += c

                            # Only add top 150
                            if i > 150:
                                break

                        context_details = {}
                        context_details['word'] = context
                        context_details['count'] = total_count
                        context_details['words'] = words
                        context_details['pages'] = []
                        context_details['tags'] = []

                        # Add context word details to the results
                        results[analysis['wordContexts']['web_name']] \
                                .append(context_details)

                    self.logger.debug("Done handling context",
                                       extra=self.log_header)

                    
                #TODO: Handle Synonyms

                #TODO: Handle Search Words
                # just add to grep for summary info?
                # or do separate?

                msg = ('{!s} finishing with summary'
                           ).format(site) 
                self.logger.debug(msg, extra=self.log_header)
                    
                # Summary Information
                results['summary'] = {}

                # Create the key to grep/filter the master file by
                key = ('totl{0}{1}|lnkc{0}{1}|tagc{0}'
                       ).format(analysis[c_type]['key'], "\\")

                # Cat the master file into the filter
                cwd = "/home/parallelspider/out/"
                cmd_line = ("cat {!s} | "
                            "grep '{!s}'"
                            ).format(base_path, key)

                try:
                    out = subprocess.check_output(cmd_line, shell=True,
                                                  cwd=cwd)
                except:
                    msg = ('Failed to process pipeline for {0}'
                           ).format('summary') 
                    self.logger.debug(msg, extra=self.log_header)
                
                self.logger.debug("Done with subprocess",
                                   extra=self.log_header)

                total_count = 0
                int_link_count = 0
                ext_link_count = 0
                tag_total = 0
                tag_list = []

                for line in out.split('\n'):
                    
                    try:

                        w, c = line.split('\t')

                        if 'tagc' in w:
                            tag = w.split('_')[1][:-1]
                            dic = {}
                            dic['type'] = tag
                            dic['count'] = int(c)

                            tag_list.append(dic)
                            tag_total += int(c)
                            
                        elif 'lnkc' in w:
                            if 'internal' in w:
                                int_link_count = c
                            else: 
                                ext_link_count = c

                        elif 'totl' in w:
                            total_count = c

                        else:
                            msg = 'No proper tag in summary output'
                            self.logger.error(msg, extra=self.log_header)

                    except:
                        # error unpacking line
                        # TODO: figure out why it blows up sometimes.
                        pass

                # Bug fix: sometimes total words is not in out
                # so pull from file
                # TODO: fix grep? so hack not necessary?
                # or just do Parallel Cleaner
                if total_count == 0:
                    key = 'totl' + analysis[c_type]['key']
                    with open('/home/parallelspider/out/' + base_path) as f:
                        string = f.read()
                        index = string.find(key)
                        upper_newline = string.rfind('\n', 0, index)
                        bottom_newline = string.find('\n', index)
                        line = string[upper_newline:bottom_newline]
                        try:
                            w, c = line.split('\t')
                            total_count = c
                        except:
                            msg = 'Not able to process total count.'
                            self.logger.error(msg, extra=self.log_header)

                results['summary']['links'] = {}
                results['summary']['links']['external'] = int(ext_link_count)
                results['summary']['links']['internal'] = int(int_link_count) 
 
                # Pull page download info from engine redis
                finished = base + "::finished"
                page_count = r.scard(finished)
                pages = r.smembers(finished)
                first_pages = []
                for i, page in enumerate(pages):
                    first_pages.append(page)
                    if i > 100:
                        break

                results['summary']['pages'] = {}
                results['summary']['pages']['count'] = page_count 
                results['summary']['pages']['list'] = first_pages

                results['summary']['tags'] = {}
                results['summary']['tags']['list'] = tag_list
                results['summary']['tags']['total'] = tag_total

                results['summary']['words'] = {}
                results['summary']['words']['count'] = int(total_count)

                self.logger.debug("Done handling summary",
                                    extra=self.log_header)

                if c_type == 'internal':
                    site_results['internalResults'] = results
                else:
                    site_results['externalResults'] = results

                site_results['url'] = site
                
                finished_analysis['sites'].append(site_results)
        
        # All done, clock time
        finish_time = time.time()
        cleanup_time = finish_time - start_time
        finished_analysis['time'] = crawl_time + cleanup_time

        json_data = json.dumps(finished_analysis)

        user_id = config['user_id']
        full_crawl_id = config['crawl_id']
        key = user_id + '/' + full_crawl_id + '.json'

        # Logging
        msg = ('crawl_time: {!s}').format(crawl_time + cleanup_time) 
        self.logger.info(msg, extra=self.log_header)
        msg = ('Posting to S3, key: {!s}').format(key) 
        self.logger.debug(msg, extra=self.log_header)
        msg = ('Data: {!s}').format(json_data) 
        self.logger.debug(msg, extra=self.log_header)


        # Upload to S3 (assumes AWS keys are in .bashrc / env)
        s3conn = boto.connect_s3()
        bucket_name = "ps_users" # TODO: put in config init
        bucket = s3conn.create_bucket(bucket_name)
        k = boto.s3.key.Key(bucket)
        k.key = key
        # TODO: add upload monitoring
        k.set_contents_from_string(json_data) 

        # Update first site's count in Engine Redis
        # TODO: fix crawl id
        engine_crawl_id = config['crawl_id']
        for site in site_list:
            base = '%s::%s' % (site, engine_crawl_id)
            r.set(base + "::count", "-2")


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
    # Special format for debugging so boto doesn't blow up
    FORMAT_DEBUG = "SpiderCleaner %(asctime)s %(message)s"
    HOST = socket.gethostbyname(socket.gethostname())
    SPDR_TYPE = "cleaner"
    FILENAME = "/var/log/spider/spider" + SPDR_TYPE + ".log"
    log_header = {'id': 0, 'spider_type': SPDR_TYPE, 'host': HOST, 'msg_type':'none'}

    if level == "develop": # to console
        logging.basicConfig(format=FORMAT, level=logging.INFO)
    elif level == "debug": # extra info
        logging.basicConfig(format=FORMAT_DEBUG, level=logging.DEBUG)
    else: # production, to file (default)
        logging.basicConfig(filename=FILENAME, format=FORMAT, level=logging.INFO)

    logger = logging.getLogger('spider' + SPDR_TYPE)

    return (logger, log_header)


# Command Line Crap & Initialization
###############################################################################

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

    # Set up logging
    options.log_level = "debug"
    #options.log_level = "develop"
    log_info = set_logging_level(level=options.log_level)
    logger, log_header = log_info
    log_header['msg_type'] = "Initialization - "
    msg = """starting options: %s""" % (options)
    logger.info(msg, extra=log_header)

    # Convert Redis info to a Python dictionary
    # TODO: make argument if required or create default
    redis_info = {}
    temp_list = options.redisInfo.split(",")
    for item in temp_list:
        key, delimiter, value = item.partition(':')
        redis_info[key] = value

    
    #  Initialize and execute spider runner
    spider_cleaner = SpiderCleaner(redis_info, options.crawlInfo, 
                                   options.psuedo, log_info) 
    spider_cleaner.execute()

if __name__ == "__main__":
    """Enable command line execution """
    sys.exit(main())

