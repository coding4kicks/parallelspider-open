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
#import redis

#from optparse import OptionParser

class Mapper():

    def __init__(self):
        #self.redis_info = self.params["redisInfo"]
        we = 2
    
    def __call__(self, key, value):

        for word in value.split():
            yield word, 1

def reducer(key, values):
    yield key, sum(values)

if __name__ == "__main__":
    import dumbo
    dumbo.run(Mapper, reducer)
    
    

