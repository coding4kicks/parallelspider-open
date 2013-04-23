"""
    Parallel Spider - Websites parsing and analysis via Hadoop

    Parallel Spider performs website parsing and analysis. Current input is a
    text file with number of mappers to generate.  All parameters for analysis
    are passed in either via the command line or Redis.

    TODO: speed this fucking thing up!
    - combiner may have helped
    - may need a timer if parsing takes to long just quit, since hung up on
      on something
    TODO: id mappers by incrementing a counter to eliminate temp keys?
    TODO: add job for cleanup?
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

    Recieves redis information indicating what parameters to pass to  
    Mr. Feynman for the analysis and where to get new links and place 
    processing and finished links as well as a count of how many pages 
    have been analyzed.  The Engine Redis instance is essentially used 
    to maintain link state in the MapReduce solution.  The input file 
    is essentially meaningless and just matches the number of mappers 
    requested in the processing.  All the page analysis is performed by
    Mr Feynman's Brain's analysis method.  It recieves the lxml parsed 
    page and returns a list of key-value pairs to be emmitted by the mapper.
    Link state, or not analyzing the same page twice, is done through 
    set difference operations.  Only links which are not in the new_link,
    processing, and finished sets are added to the new_link set.  This is 
    done by executing a transaction on Redis.

    __init__ -- initializes redis info (for crawl info and links to follow)
    __call__ -- downloads and passes pages to Mr. Feynman for analysis.
    """

    def __init__(self):
        """ 
        Initializes redis info and config file

        Redis info provides information about required crawl analysis,
        as well as link processing information.

        Args:
            param - dictionary passed in by dumbo
                    redisInfo : host, port, base key, and max mappers
        """

        self.test = True; # Set to true for testing on a local file                      
        self.redis_info = _load_engine_redis_info(self.params)
        self.redis = redis.StrictRedis(host=self.redis_info["host"],
                              port=int(self.redis_info["port"]), db=0)
        self.base = self.redis_info["base"]
        self.site, _, crawl_id = self.base.partition("::")
        self.config = _initialize_config(self.redis.get(crawl_id))
        self.external_analysis = self.config['analyze_external_pages']

    def __call__(self, key, value):
        """ 
        Performs parallel website downloading, parsing, and analysis 
        
        Sets up Redis information. Loops downloading pages, feeding them to
        an analysis engine which emits info to the Reducer.  Stops when no 
        more new links or the max pages has been reached.

        Args:
            key, value - not used

        Yields:
            key, value - tuple for reducer, either Mr. Feynmans output 
                         or an error message.
        """
        
        r = self.redis # analysis Engine Redis instance
        redis_keys = (new_links, processing, finished, count, temp1, temp2
                ) = _create_redis_keys(self.base)
        robots_txt = _init_robot_txt(self.site)
        brain = Brain(self.site, self.config)
        max_pages = int(self.redis_info["maxPages"]) 

        while True: # Here we go... yee hah!

            if _no_more_to_scrape(r, max_pages, new_links, count):
                break

            try: # to pop a link and add it to processing
                link = r.spop(new_links)
                r.sadd(processing, link) 
            except Exception as e:
                msg = ('Unable to pop a link - Exception: {} '
                       '- Exception args: {}').format(type(e), e)
                yield 'zmsg__error', (msg, 1)
                break
            
            try: # to download and parse the page
                external, link = _check_if_external(link)
                page = _parse(link, self.test)
                if page == None: 
                    msg = ('File type not supported: {!s}').format(link) 
                    yield 'zmsg__error', (msg, 1)
                    continue
            except Exception as e:
                msg = ('Unable to download and parse: {} - Exception: {} '
                       '- Exception args: {}').format(link, type(e), e)
                yield 'zmsg__error', (msg, 1)
                continue

            try: # to process the page information
                output = brain.analyze(page, link, robots_txt,
                                       external=external)
                links = brain.on_site_links
                if self.external_analysis:
                    links.extend(_add_external_links(brain))
            except Exception as e:
                msg = ('Unable to process info for: {} - Exception: {} '
                       '- Exception args: {}').format(link, type(e), e)
                yield 'zmsg__error', (msg, 1)
                continue

            try: # to emit the information return by Mr. Feynman 
                for put in output:
                    key, value = put
                    yield key, value
            except Exception as e:
                msg = ('Unable to emit info for: {} - Exception: {} '
                       '- Exception args: {}').format(link, type(e), e)
                yield 'zmsg__error', (msg, 1)
                continue

            try: # to finish processing the link and to add new links
                _add_link_to_finished(r, link, redis_keys)
                _batch_add_links_to_new(r, links, redis_keys) 
            except Exception as e:
                msg = ('Unable to finish processing: {} - Exception: {} '
                       ' - Exception args: {}').format(link, type(e), e)
                yield 'zmsg__error', (msg, 1)
                continue

        _set_key_expiration(r, redis_keys)
            

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
        """Initializes redis info and config file."""
                      
        self.redis_info = _load_engine_redis_info(self.params)
        self.redis = redis.StrictRedis(host=self.redis_info["host"],
                              port=int(self.redis_info["port"]), db=0)
        self.base = self.redis_info["base"]
        self.site, d, crawl_id = self.base.partition("::")
        self.config = _initialize_config(self.redis.get(crawl_id))

    def __call__(self, key, values):
        """ 
        Passes key-value pairs recieved from mapper to Mr. Feynman.

        Mr. Feynmans Brain processes (reduces) the information
        recieved from the mapper (Mr. Feynman's brain's analysis).
        The operations are cumulative and associative so the reducer
        can be used as a combiner.  It's output is disigned to 
        specifically match its input.
        
        Args:
            key -- a text key with a label followed by value
            values -- a list of tubles depending upon key type
       """

        try:
            brain = Brain(self.site, self.config)
            key, new_values = brain.process(key, values)
            yield key, new_values
        except Exception as e:
            msg = ('Unable to reduce: {} - Exception: {}'
                   ' - Exception args: {}').format(key, type(e), e)
            yield 'zmsg__error', (msg, 1)


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

def _initialize_config(config_file):
    """Converts json config to python dict and validates ext page analysi."""
    config = json.loads(config_file)
    if 'analyze_external_pages' not in config:
        config['analyze_external_pages'] = False
    return config

def _create_redis_keys(base):
    """Create keys to access data in Engine Redis."""
    new_links = base + "::new_links"       
    processing = base + "::processing"      # links being processed
    finished = base + "::finished"          # links done being processed
    count = base + "::count"                # total pages scraped
    temp1 = base + "::temp1"                # temp keys for set ops
    temp2 = base + "::temp2"
    return (new_links, processing, finished, count, temp1, temp2)

def _init_robot_txt(site_url):
    """Initialize robot.txt for the specified site."""
    robots_txt = robotparser.RobotFileParser()
    robots_txt.set_url(site_url + "robots.txt")
    robots_txt.read()
    return robots_txt

def  _no_more_to_scrape(r, max_pages, new_links, count):
    """Return True if no more links or hit max pages."""            
    link_count = 0
    temp_count = r.get(count)
    if temp_count:
        link_count = int(temp_count)
    more_links = r.exists(new_links)
    if link_count >= max_pages or not more_links:
        return True
    else:
        return False

def _check_if_external(link):
    """Check if ext_ is prepended to link indicating an external page."""
    external = False
    if link[0:4] == 'ext_':
        external = True
        link = link[4:len(link)]
    return (external, link)

def _parse(link, test):
    """Download and parse page depending upon scheme."""
    if 'https' in link:
        page = lxml.html.parse(urllib2.urlopen(link))
    elif 'http' in link or test == True:
        page = lxml.html.parse(link)
    else: 
        page = None
    return page

def _add_external_links(brain):
    """Return a list of flagged ('ext_') external links."""
    new_links = []   
    ext_links = brain.off_site_links
    for link in ext_links:
        new_link = "ext_" + link # Add ext_ flag
        new_links.append(new_link)
    return new_links

def _add_link_to_finished(r, link, redis_keys):
    """Add link to finished set, incr counter, remove from processing"""
    _, processing, finished, count, _, _ = redis_keys
    r.sadd(finished, link) 
    r.incr(count) 
    r.srem(processing, link) 

def _batch_add_links_to_new(r, links, redis_keys):
    """
    Add new links as a batch to Engine Redis

    Max batch size possible is 255
    Set difference operation is performed to make sure no links
    that are in processing, or finished, or already in new,
    are added to new links.  Thus, this transaction makes sure 
    that only "new" links are added to the new links set.
    """
    new_links, processing, finished, count, temp1, temp2 = redis_keys
    pipe = r.pipeline() # start transaction to add new links
    size = len(links) 
    batch_size = 250
    breaks, remainder = divmod(size, batch_size) # calc number of breaks
    if remainder > 0:   # reminder: crack babies are sad.
        breaks = breaks + 1
    start, finish, i = 0, batch_size, 0

    while i < breaks:
        link_batch = links[start:finish]
        pipe.sadd(temp1, *link_batch)
        start += batch_size
        finish += batch_size
        i += 1

    # set diff: new_links = temp - new_links - processing - finished
    pipe.sdiffstore(temp2, temp1, new_links, processing, finished)
    pipe.sunionstore(new_links, new_links, temp2)
    pipe.delete(temp1)
    pipe.delete(temp2)
    pipe.execute() # finish transaction

def _set_key_expiration(r, redis_keys):
    """Set key expirations, must be done after every change."""
    new_links, processing, finished, count, _, _ = redis_keys
    hour = 60 * 60 # 60 seconds/minute * 60 minutes
    if r.exists(new_links): r.expire(new_links, hour)
    if r.exists(processing): r.expire(processing, hour)
    if r.exists(finished): r.expire(finished, hour)
    if r.exists(count): r.expire(count, hour)


###############################################################################
### Starter
###############################################################################
if __name__ == "__main__":
    import dumbo
    dumbo.run(Mapper, Reducer, combiner=Reducer)
    
    

