#!/usr/bin/env python
"""Tool to generae configuration pickle file for testing."""
import cPickle
import cStringIO

def create_file():
    """Create config dictionary and return it.
    
    # TO SET THE REDIS CONFIG KEY
    >>> import redis
    >>> r = redis.Redis("localhost")
    >>> import config_pickler
    >>> file = config_pickler.create_file()
    >>> r.set('config',file.getvalue())


    # TO GET THE DICT FROM REDIS
    >>> output = r.get('config')
    >>> import cPickle
    >>> config = cPickle.loads(output)
    """

    # Set up configuration file (HARDCODE for now)
    config = {}
    
    # Config variables
    config['text_request'] = True
    config['header_request']  = True
    config['meta_request']  = True
    config['a_tags_request'] = True
    config['all_links_request'] = True
    config['external_links_request'] = True
    config['context_search_tag'] = ['dream']
    config['wordnet_lists'] = {
            'list1':['word', 'something', 'loser'],
            'list2':['news', 'journalism', 'great']}        
    config['xpath_selectors'] = [
        {'selector': "//img/@alt", 'name': "image alt", 
            'analyze': False, 'css_text': False},
        {'selector': "//div[@class='story']/descendant::text()",
            'name': "test1", 'analyze': False, 'css_text': False},
        {'selector': 
"//a[@href='http://video.msnbc.msn.com/nightly-news/50032975/']/text()", 
        'name': "test2", 'analyze': True, 'css_text': False},
        {'selector': "//div[@id='tbx-29618997']/div/h2/text()", 
            'name': "test3", 'analyze': False, 'css_text': False}] 
    config['css_selectors'] = [{'selector': 'p.abstr', 
        'name': "testCss", 'analyze': True, 'css_text': True}]
    
    config['analyze_external_pages'] = True

    config['paths_to_follow'] = [] #['worldnews'] 

    # Hardcode stop words, later load from pickle config file
    stop_words = ("a,about,above,after,again,against,all,am,an,and,any,"+
        "are,aren't,as,at,be,because,been,before,being,below,between,"+
        "both,but,by,can't,cannot,could,couldn't,did,didn't,do,does,"+
        "doesn't,doing,don't,down,during,each,few,for,from,further,had,"+
        "hadn't,has,hasn't,have,haven't,having,he,he'd,he'll,he's,her,"+
        "here,here's,hers,herself,him,himself,his,how,how's,i,i'd,i'll,"+
        "i'm,i've,if,in,into,is,isn't,it,it's,its,itself,let's,me,more,"+
        "most,mustn't,my,myself,no,nor,not,of,off,on,once,only,or,other,"+
        "ought,our,ours,ourselves,out,over,own,same,shan't,she,she'd,"+
        "she'll,she's,should,shouldn't,so,some,such,than,that,that's,"+
        "the,their,theirs,them,themselves,then,there,there's,these,they,"+
        "they'd,they'll,they're,they've,this,those,through,to,too,under,"+
        "until,up,very,was,wasn't,we,we'd,we'll,we're,we've,were,weren't,"+
        "what,what's,when,when's,where,where's,which,while,who,who's,"+
        "whom,why,why's,with,won't,would,wouldn't,you,you'd,you'll,"+
        "you're,you've,your,yours,yourself,yourselves,&,<,>,^,(,)")

    config['stop_list'] = stop_words.split(",")

    # Save the config dictionary to a pickled stringIO file
    stringIO_file = cStringIO.StringIO()
    cPickle.dump(config, stringIO_file)

    return stringIO_file


if __name__ == "__main__":
    """Just in case."""
    sys.exit(create_file())

