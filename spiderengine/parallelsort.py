"""Sort by number vice letter."""

def mapper(key, value):
    try:
        word, count = value.split()
        yield count, word
    except:
        pass

def reducer(key, values):
    for value in values:
        yield key, value

if __name__ == "__main__":
    import dumbo
    dumbo.run(mapper, reducer)
