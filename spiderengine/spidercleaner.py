""" Spider Cleaner

    Downloads results from HDFS and Redis.
    Turns those results into JSON format need by Spider Web.
    Uploads the results to S3 and notifies Spider Server.

"""

import os
import sys
import json
import time
import redis
import optparse
import subprocess

import pprint
pp = pprint.PrettyPrinter(indent=2)

class SpiderCleaner(object):
    """
    """

    def __init__(self, redis_info, crawl_info):
        """ 

        """   
        self.redis_info = redis_info      
        self.crawl_info = crawl_info
        # Is this necessary???
        self.psuedo_dist = False # Psuedo distributed for testing
           

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
        #analysis_types = ['visible', 'headline', 'text'] #TODO: pull from conf

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
        if config['analyze_external_pages'] == True:
            content_types.append('external')

        print analysis_types

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
        analysis["predefinedSynRings"] = {"key": "cntw", "web_name": "synonymRings"}

        # Analysis to be output (converted to json and uploaded to S3)
        finished_analysis = {}
        finished_analysis['name'] = config['name']
        #finished_analysis['date'] = config['date']
        #start_time = config['time']
        
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
            site_list = [config['sites']]
        else:
            site_list = config['sites']
        
        # Format results for each site
        for site in site_list:

            site_results = {}
            
            print "MADE IT COWBOY"
            print "MADE IT COWBOY"
            print "MADE IT COWBOY"

            # Construct file name details
            base = '%s::%s' % (site, config['crawl_id'])
            base_path = base.replace("/","_").replace(":","-")

            if not self.psuedo_dist:
                # Download master file from HDFS
                # TODO: unix tee into separate files & filter and sort and head
                # if able, or move to MapReduce solution
                cmd_line = ("dumbo cat /HDFS/parallelspider/out/{!s}/part-00000 "
                           "-hadoop starcluster > /home/parallelspider/out/{!s} "
                           ).format(base_path, base_path)
                out = subprocess.call(cmd_line, shell=True)
                print cmd_line

            # Format both internal and external results
            for c_type in ['internal','external']:
                
                # If analysis not performed, create empty placeholders and exit
                if c_type not in content_types:
                    
                    placeholders = {'visibleText': {}, 'hiddenText': {}, 'headlineText': {},
                    'allLinks': {}, 'externalDomains': {}, 'linkText': {},
                    'searchWords': {}, 'context': {},
                    'synonymRings': {}, 'summary': {'pages':{'count':0}, 'words':{'count':0}},
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
                    if a_type not in analysis_types:
                        continue
                        
                    # Create the key to grep/filter the master file by
                    key = analysis[a_type]['key'] + analysis[c_type]['key']

                    # Cat the master file into the sort filter
                    if self.psuedo_dist:# Psuedo Distributed

                        cwd = "/home/parallelspider/out/"
                        cmd_line = ("cat {!s} | "
                                    "grep '{!s}' | "
                                    "sort -k 2 -n -r | "
                                    "head -n 10"
                                    ).format(base_path, key)

                        # Loop while no output
                        # I believe a race has been causing problems
                        # where the file is created but nothing is in it
                        out = ""
                        while not out:
                            out = subprocess.check_output(cmd_line, shell=True,
                                    cwd=cwd)
                        print ""
                        print "OUTPUT"
                        print type(out)
                        print out
                        
                    else: # Normal
                        cwd = "/home/parallelspider/out/"
                        cmd_line = ("cat {!s} | "
                                    "grep '{!s}' | "
                                    "sort -k 2 -n -r | "
                                    "head -n 10"
                                    ).format(base_path, key)

                        # No loop on out
                        out = subprocess.check_output(cmd_line, shell=True,
                                                      cwd=cwd)
                        print ""
                        print "OUTPUT"
                        print type(out)
                        print out


                    # Handle Word Analysis Types
                    if a_type in ['visible','headline', 'text']:
                         
                        # Process words
                        words = []

                        # Last line of split is junk
                        for i, line in enumerate(out.split('\n')[:-1]):
                            print ""
                            print "line"
                            print line
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

                        print "words: " + str(words)    
                        results[analysis[a_type]['web_name']]['words'] = words 

                    #TODO: Handle Links
                    
                    #TODO: Handle Domains 
                    
                    #TODO: Handle Context 
                    
                    #TODO: Handle Synonyms

                #TODO: Handle Search Words
                    
                # Summary Information
                results['summary'] = {}

                #TODO: ??? Must do link analysis to retrieve this info?
                results['summary']['links'] = {}
                results['summary']['links']['external'] = 1000 #TODO: pull?
                results['summary']['links']['internal'] = 4000 #TODO: pull?
 
                # Pull page download info from engine redis
                results['summary']['pages'] = {}
                results['summary']['pages']['count'] = 200000 
                results['summary']['pages']['list'] = ['http://www.exsite.com/path1',
                                                           'http://www.exsite.com/path2',
                                                           'http://www.exsite.com/path3']

                #TODO: I'm not counting tags?
                results['summary']['tags'] = {}
                results['summary']['tags']['list'] = [{ 'count': 25000,
                                                            'type': 'text'},
                                                          { 'count': 5000,
                                                            'type': 'links'},
                                                          { 'count': 8000,
                                                            'type': 'headlines'},
                                                          { 'count': 4000,
                                                            'type': 'image'},
                                                          { 'count': 3000,
                                                            'type': 'other'}]
                results['summary']['tags']['total'] = 45000

                #TODO: ??? Must do total count on every analysis?
                results['summary']['words'] = {}
                results['summary']['words']['count'] = 5000000

                if c_type == 'internal':
                    site_results['internalResults'] = results
                else:
                    site_results['externalResults'] = results

                site_results['url'] = site
                
                finished_analysis['sites'].append(site_results)
                
        # All done, clock time
        finish_time = time.clock()
        #print finish_time
        #finished_analysis['time'] = finish_time - start_time

        json_data = json.dumps(finished_analysis)

        #TODO: use boto to upload data
        #TODO: crawl_id is mising random end
        # so either pass in, or remove from Spider Server

        #with open('../spiderweb/app/results1SiteAll.json', 'w') as f:
        #    f.write(json_data)

        pp.pprint(json_data)

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
