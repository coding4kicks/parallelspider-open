"""
    Parallel Spider - Websites parsing and analysis via Hadoop

    Parallel Spider performs website parsing and analysis. Current input is a
    text file with number of mappers to generate.  All parameters for analysis
    are passed in either the command line or exist in redis.

    TODO: speed this fucking thing up!
    * TODO: id mappers by incrementing a counter. *
    * Use this id to replace sharing temp keys *
"""

import sys
import json
import urllib2
import robotparser

import redis
import lxml.html

from mrfeynman import Brain

###############################################################################
### Mapper
###############################################################################
class Mapper():
    """
    Downloads and analyzes web pages on parallel computers.

    __init__ -- initializes redis info (for crawl info and links to follow)
    __call__ -- downloads and passes pages to Mr. Feynman for analysis.
    """

    def __init__(self):
        """ 
        Initializes redis info and config file

        Redis info provides information about required crawl analysis,
        as well as link processing information.

        Args:
        param - dictionary passed by dumbo
           redisInfo : host, port, base key, and max mappers
        """

        self.test = True; # Set to true for testing on local file                      
        self.redis_info = _load_engine_redis_info(self.params)
    
        # Connect to redis
        self.redis = redis.StrictRedis(host=self.redis_info["host"],
                              port=int(self.redis_info["port"]), db=0)

        self.base = self.redis_info["base"]

        # TODO: fix crawl id
        self.site, d, crawl_id = self.base.partition("::")

        # Set up configuration file
        config_file = self.redis.get(crawl_id)
        self.config = json.loads(config_file)

        # make sure external analysis flag is set
        if 'analyze_external_pages' not in self.config:
            self.config['analyze_external_pages'] = False


    def __call__(self, key, value):
        """ 
        Performs parallel website downloading, parsing, and analysis 
        
        Arguments:
        key -- not used
        value -- not used

        Sets up Redis information.
        Loops downloading pages, feeding them to
        an analysis engine which emits info to
        the Reducer.  Stops when no more new links
        or the max pages has been reached.
       """
        

        # Redis
        r = self.redis

        # Create keys for Redis
        new_links = self.base + "::new_links"        # new links
        processing = self.base + "::processing"      # links being processed
        finished = self.base + "::finished"          # links done being processed
        count = self.base + "::count"                # total pages scraped
        temp1 = self.base + "::temp1"                # temp keys for set ops
        temp2 = self.base + "::temp2"

        # Get robots.txt
        robots_txt = robotparser.RobotFileParser()
        robots_txt.set_url(self.site + "robots.txt")
        robots_txt.read() 

        # Set up analysis engine
        brain = Brain(self.site, self.config)

        stuff_to_scrape = True
        link_count = 0 # Total links downloaded by all mappers
        max_pages = int(self.redis_info["maxPages"]) # Total pages to scrape

        # Here we go... yee hah
        while stuff_to_scrape:
            
            # Update total count and check still links to download
            temp_count = r.get(count)
            if temp_count:
                link_count = int(temp_count)
            still_links = r.exists(new_links)
            # Check conditions and break if done
            # Goes over by the number of mappers?
            if link_count >= max_pages or not still_links:
                break

            # Try to pop a link
            try:

                # Retrieve a a link
                # later retrieve 5+? 
                #Asynchronously, batch process links to Redis
                link = r.spop(new_links)

                # Add link to processing
                r.sadd(processing, link)

            # Alert that can't pop a link
            except Exception as exc:
                message = """Unable to pop a link
                             Exception: %s
                             Exception args: %s
                          """ % (type(exc), exc)                
                yield 'zmsg__error', (message, 1)
                break
            
            # Try to download and parse the page
            try:
                # If link is external, set flag and adjust link
                external = False
                if link[0:4] == 'ext_':
                    external = True
                    link = link[4:len(link)]
            
                # Download and parse page
                if 'https' in link:
                    page = lxml.html.parse(urllib2.urlopen(link))
                elif 'http' in link or self.test == True:
                    page = lxml.html.parse(link)
                else: # file type not supported
                    msg = ('File type not supported: {!s}').format(link) 
                    self.logger.error(msg, extra=self.log_header)
                    break

                output = brain.analyze(page, link, robots_txt,
                                       external=external)
                links = brain.on_site_links

                if self.config['analyze_external_pages']:
                    ext_links = brain.off_site_links
                    
                    for link in ext_links:
                        new_link = "ext_" + link
                        links.append(new_link)
                    #links.extend(new_links)
                #yield('zmsg_error', (links, 1)

            # Alert that can't parse and restart loop
            except Exception as exc:
                message = """Unable to download and parse: %s
                             Exception: %s
                             Exception args: %s
                          """ % (link, type(exc), exc)
                yield 'zmsg__error', (message, 1)
                continue

            # Try to process / emit information
            try:           
                for put in output:
                    key, value = put
                    yield key, value

            # Alert that can't process info
            except Exception as exc:
                message = """Unable to process info for: %s
                             Exception: %s
                             Exception args: %s
                          """ % (link, type(exc), exc)
                yield 'zmsg__error', (message, 1)
                continue

            # Try to finish processing link
            try:

                # Add link to finished
                r.sadd(finished, link)

                # increase total pages processed
                r.incr(count)

                # Remove from processing
                r.srem(processing, link)

                # Transaction to store new links
                pipe = r.pipeline()

                # Add any new links found
                # Attempting to process as batch vice adding 1 at a time
                # Can only add 255 elements max at a time
                size = len(links)

                # Calculate number of breaks
                breaks, remainder = divmod(size, 250)
                if remainder > 0:   # Reminder: crack babies are sad.
                    breaks = breaks + 1

                # Initialize indices based upon batch size
                start = 0
                finish = 250
                i = 0

                while i < breaks:
                    links_part = links[start:finish]

                    #Add single quotes around each element in list: map
                    #   Then combine elements to form a string for eval: join
                    link_string = (',').join(map(lambda x: "'" + x + "'",
                                                 links_part))

                    # ??? SECURITY ??? - site name is user provided
                    eval("pipe.sadd('" + temp1 + "'," + link_string + ")") 

                    # Increment indices
                    start = start + 250
                    finish = finish + 250
                    i = i + 1

                # new links = temp - new links - processing - finished
                pipe.sdiffstore(temp2, temp1, new_links, processing, finished)
                pipe.sunionstore(new_links, new_links, temp2)
                pipe.delete(temp1)
                pipe.delete(temp2)
                pipe.execute()
 
            # Alert that can't process info
            except Exception as exc:
                message = """Unable to finish processing: %s
                             Exception: %s
                             Exception args: %s
                          """ % (link, type(exc), exc)
                yield 'zmsg__error', (message, 1)
                continue          
            
        # Set 1 hour expirations on all keys
        hour = 60 * 60 # 60 seconds/minute * 60 minutes
        if r.exists(new_links): r.expire(new_links, hour)
        if r.exists(processing): r.expire(processing, hour)
        if r.exists(finished): r.expire(finished, hour)
        if r.exists(count):r.expire(count, hour)


###############################################################################
### Reducer
###############################################################################
class Reducer():
    """
    Condenses web analysis output from mappers

    __init__ -- initializes redis info and config file
    __call__ -- takes in key - values, and compresses/counts values
    """


    def __init__(self):
        """ 
        Initializes redis info and config file

        Config file is only used to initialize the Brain, 
        but process doesn't make use of parameters.
        Option to remove or keep later, to remove, config must 
        be initialized in the analyzer and not __init__.
        """
                      
        # Convert Redis info to Python Dictionary
        self.redis_info = _load_engine_redis_info(self.params)
    
        # Connect to redis
        self.redis = redis.StrictRedis(host=self.redis_info["host"],
                              port=int(self.redis_info["port"]), db=0)

        self.base = self.redis_info["base"]

        # TODO: fix crawl id
        self.site, d, crawl_id = self.base.partition("::")

        # Set up configuration file 
        config_file = self.redis.get(crawl_id)
        self.config = json.loads(config_file)


    def __call__(self, key, values):
        """ 
        Performs parallel website downloading, parsing, and analysis 
        
        Arguments:
        key -- a text key with a label followed by value
        values -- a list of tubles depending upon key type
       """
        

        try:

            # Reduce key-value pairs
            brain = Brain(self.site, self.config)
            output = brain.process(key, values)
            key, new_values = output

            yield key, new_values

        except Exception as exc:
            message = """Unable to reduce: %s
                         Exception: %s
                         Exception args: %s
                      """ % (key, type(exc), exc)
            yield 'zmsg__error', (message, 1)


###############################################################################
### Helper Funcs
###############################################################################
def _load_engine_redis_info(params):
    """Convert Redis info to Python Dictionary"""
    redis_info = {}
    param = params["redisInfo"]
    temp_list = param.split(",")
    for item in temp_list:
        key, _, value = item.partition(':')
        redis_info[key] = value
    if not redis_info['host']:
        sys.stderr.write('Must specify Redis host information! Please.')
        sys.exit(1)
    if not redis_info['port']:
        redis_info['port'] = 6380
    return redis_info


### STARTER ###
if __name__ == "__main__":
    import dumbo
    # TODO: is this running the reducer as a combiner? I think, No?
    dumbo.run(Mapper, Reducer)
    
    

