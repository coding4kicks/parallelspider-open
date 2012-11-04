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
        self.new_links = 'http://www.foxnews.com/::2012-11-4-10-10::new_links'
        site = "http://www.foxnews.com/"

        # Retrieve a a link
        # later retrieve 5+? Asynchronously, batch process links to Redis
        link = r.spop(self.new_links)

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

        for tag in output:
            for word in tag.split():
                yield word, 1

        for word in value.split():
            yield word, 1

def reducer(key, values):
    yield key, sum(values)

if __name__ == "__main__":
    import dumbo
    dumbo.run(Mapper, reducer)
    
    

