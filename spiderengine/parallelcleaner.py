"""TODO: push cleanup into MapReduce"""

def mapper(key, value):
    yield key, value
    #for word in value.split():
    #    yield word, 1

def reducer(key, values):
    #yield key, values
    yield key, sum(values)

if __name__ == "__main__":
    import dumbo
    dumbo.run(mapper) #, reducer)
