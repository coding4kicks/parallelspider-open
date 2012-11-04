#!/usr/bin/env python
"""
	Parallel Spider

	Parallel Spider performs website analysis. The input is a document of 
        web pages to download, each separated by a line.  For each page, a 
        mapper will be called that both parses and analyzes the data.  The 
        particular analysis to be performed is included in the input, along 
        with information to connect to Redis, a data structure server used 
        to maintain link state.
"""
class Mapper():

    def __init__(self):
                      
        # Convert Redis info to Python Dictionary (keep default)
        self.redis_info = {}
        param = self.params["redisInfo"]
        temp_list = param.split(",")
        for item in temp_list:
            key, delimiter, value = item.partition(':')
            self.redis_info[key] = value
    
    
    def __call__(self, key, value):
        
        import redis
        import urllib

        from Parser import Parser

        # Connect to Redis
        r = redis.StrictRedis(host=self.redis_info["host"],
                              port=int(self.redis_info["port"]), db=0)

        # temporary - hard code key name
        base = 'http://www.foxnews.com/::2012-11-4-20-2'
        #new_links = 'http://www.foxnews.com/::2012-11-4-10-10::new_links'
        site = "http://www.foxnews.com/"

        # Create keys for Redis
        new_links = base + "::new_links"
        processing = base + "::processing"
        finished = base + "::finished"
        temp1 = base + "::temp1"
        temp2 = base + "::temp2"


        # Retrieve a a link
        # later retrieve 5+? Asynchronously, batch process links to Redis
        link = r.spop(new_links)

        # Add link to processing
        r.sadd(processing, link)

        # Set key expiration
        hour = 60 * 60 # 60 seconds/minute * 60 minutes
        r.expire(processing, hour)

        # Download page
        f = urllib.urlopen(link)
        data = f.read()
        f.close

        # Hard code tags - later make variable of Analysis Info
        tag_list = ["p", "h1", "h2", "h3", "h4", "h5", "h6"]
        parser = Parser(site, tag_list)
        parser.run(data)
        links = parser.get_links()
        output = parser.get_output() 

        
        yield link, 1

        for tag in tag_list:
            for word in output[tag].split():
                yield word, 1

        for word in value.split():
            yield word, 1

        # Add link to finished
        r.sadd(finished, link)
        r.expire(processing, hour)

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
        if remainder > 0:
            breaks = breaks + 1

        # Set initial indices
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

            # Set key expiration - don't expire,
            # remove when done
            #hour = 60 * 60 # 60 seconds/minute * 60 minutes
            #r.expire(new_link_set, hour)

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

def reducer(key, values):
    yield key, sum(values)

if __name__ == "__main__":
    import dumbo
    dumbo.run(Mapper, reducer)
    
    

