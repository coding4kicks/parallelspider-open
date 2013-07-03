"""Sort by number vice letter."""
from dumbo import opt 

def mapper(key, value):
    # Read in a word and count, emit reverse
    try:
        word, count = value.split()
        yield count, word
    except:
        pass

@opt("hadoopconf", "mapred.output.key.comparator.class=org.apache.hadoop.mapred.lib.KeyFieldBasedComparator")
@opt("hadoopconf", "mapred.text.key.comparator.options=-r")
def reducer(key, values):
    # May be multiple words with the same count
    for value in values:
        yield key, value

if __name__ == "__main__":
    import dumbo
    dumbo.run(mapper, reducer)
