"""
    Mr Feynman analyzes a parsed html document.

    The module takes in a parsed document and emits key value pairs.
    It is designed to be incorporated into a MapReduce solution.

    TODO: Add pagerank for links
"""
import lxml.html
import lxml.cssselect

class Brain(object):
    """ 
    Mr. Feynman's Brain performs analysis of a lxml parsed page.

    __init__ - constructor takes a url and config file
    analyze - prepares output for mappers
    process - prepares output for reducers
    """

    def __init__(self, passed_url, config_dict):
        """
        Initialize the Brain with site_url and configuration parameters
        
        Arguments:
        passed_url - the url of the site to be searched
        config_dict - dictionary of configuration parameters
            text_request: boolean - true to analyze text
            header_request: boolean - true to analyze headers
            meta_request: boolean - true to analyze meta information
            a_tags_request: boolean - true to analyze anchor tags
            external_links_request: boolean - true to analyze external links
            context_search_tag: list of words to find context
            wordnet_lists: list of synonym rings to find
            xpath_selectors: dictionary of xpath selectors and info
            css_selectors: dictionary of css selectors and info
            paths_to_follow: list of strings used to filter out urls
            stop_list: list of words not to emit

        If the passed url contains a subdomain, only this will be searched.
        """   
        import copy
 
        # URL passed by the user, may contain a path
        self.passed_url = passed_url

        # URL without path, Site Domain: ex. foxnews.com, Scheme: http/https
        self.site_url, self.site_domain, self.scheme = decode(self.passed_url)

        # Check config variables
        if 'text_request' in config_dict:
            self.text_request = config_dict['text_request']
        else:
            self.text_request = False

        if 'header_request' in config_dict:
            self.header_request  = config_dict['header_request']
        else:
            self.header_request = False

        if 'meta_request' in config_dict:
            self.meta_request  = config_dict['meta_request']
        else:
            self.meta_request = False

        if 'a_tags_request' in config_dict:
            self.a_tags_request = config_dict['a_tags_request']
        else:
            self.a_tags_request = False;

        if 'all_links_request' in config_dict:
            self.all_links_request = config_dict['all_links_request']
        else:
            self.all_links_request = False

        if 'external_links_request' in config_dict:
            self.external_links_request = config_dict['external_links_request']
        else:
            self.external_links_request = False

        if 'context_search_tag' in config_dict:
            self.context_search_tag = config_dict['context_search_tag']
        else:
            self.context_search_tag = []

        if 'wordnet_lists' in config_dict:
            self.wordnet_lists = config_dict['wordnet_lists'] 
        else:
            self.wordnet_lists = None

        if 'xpath_selectors' in config_dict:
            self.xpath_selectors = config_dict['xpath_selectors']
        else:
            self.xpath_selectors = []

        if 'paths_to_follow' in config_dict:
            self.paths_to_follow = config_dict['paths_to_follow']
        else:
            self.paths_to_follow = []

        if 'stop_list' in config_dict:
            self.stop_list = config_dict['stop_list']
        else:
            self.stop_list = []

        # Need to deep copy for lxml or css to xpath conversion fails?
        if 'css_selectors' in config_dict:
            self.css_selectors = copy.deepcopy(config_dict['css_selectors'])
        else:
            self.css_selectors = None

        # Compile and append css selectors to xpath_selctors
        if self.css_selectors:
            for selector in self.css_selectors:
                sel = lxml.cssselect.CSSSelector(selector['selector'])
                selector['selector'] = sel.path
                self.xpath_selectors.append(selector)
 
        # Lists o' Links on the page
        self.on_site_links = []     # links to other pages on the site
        self.off_site_links = []    # links to pages off the site

        # Labels for various processing types - append to start of key
        # All labelels are 4 characters.  A tag for external or internal is
        # then appended, followed by an underscore.
        self.label = { 'text': 'text', 'header': 'head', 'anchor_tag': 'atag',
                        'meta_data': 'meta', 'all_links': 'link',
                        'external_links': 'extl', 'context': 'cnxt', 
                        'context_word': 'cntw', 'wordnet': 'wdnt',
                        'total_count': 'totl', 'selector': 'selc', 
                        'selector_word': 'selw', 'error_message': 'zmsg'}


    def analyze(self, doc, page_link, robots_txt,
                external=False, no_emit=False):
        """ 
        Analyze a parsed document, returning key,value pairs (a mapper).

        Arguments:
        doc -- a lxml.html parsed document
        external -- boolean, if True will not pass any links to follow 
                    and will mark all output as external
        no_emit -- boolean, if True will only find links on the page 
                    and will generate output to anlyze 

        Returns:
        mapper_output - a list of key value pair tuples

        Keys are prefixed with a 4 character label for type,
        along with one character for external or internal, 
        then an underscore followed by the key itself

        Key types:
            text - analyze visible text on the page           
            header - analyze headlines on a page         
            anchor_tag - analyze link text on a page
            meta_data - analyze hiddent descriptions on a page
            all_links - analyze all the links on a page
            external_links - analyze external site links on a page
            context - analyze the context around a specified word
            context_word - analyze each word in the context
            wordnet - analyze synonym rings
            total_count - a total count of all words
            selector - select certain element out of the page
            selector_word - analyze the selected words
            error_message - error messages in processing
        """

        mapper_output = [] # key-value tuples for mapper output
        page_links = [] # all the links on the page
        
        # Iterate once through the document
        for element in doc.iter():
            
            # Grab tag and text (+tail) for html elements
            tag = element.tag
            text = element.text
            tail = element.tail
            words = None # text words split to list

            # Combine text and tail, then lowercase and split to list
            if tail:
                if text:
                    text = text + " " + tail
                else:
                    text = tail
            if text:
                words = text.lower().split()

            # Set as either an external or internal page
            if external:
                external_bit = 'e'
            else:
                external_bit = 'i'
 
            # Process links
            if tag == 'a':
                # Analyze link href
                try: 
                    link = element.attrib['href']
                    page_links.append((link, element))
                except:
                    pass
            
            # Skip the rest of loop if not processing
            if no_emit:
                continue
 
            # Process Text
            if self.text_request:
                if (tag == 'p' or tag == 'li' or tag == 'td' or 
                    tag == 'h1' or tag == 'h2' or tag == 'h3' or
                    tag == 'h4' or tag == 'h5' or tag == 'h6' or
                    tag == 'a'):
                    if words:
                        for word in words:
                            if word not in self.stop_list:
                                key_word = '%s%s_%s' % (
                                        self.label['text'],
                                        external_bit, word)
                                # Additional Info
                                #value = (key_word, ( 
                                #    1, (page_link, 1), (tag, 1)))
                                value = (key_word, 1)
                                mapper_output.append(value)

            # Process Headers
            if self.header_request:
                if (tag == 'h1' or tag == 'h2' or tag == 'h3' or
                    tag == 'h4' or tag == 'h5' or tag == 'h6'):
                    if words:
                        for word in words:
                            if word not in self.stop_list:
                                key_word = '%s%s_%s' % (
                                        self.label['header'],
                                        external_bit, word)
                                # Additional Info
                                #value = (key_word, ( 
                                #    1, (page_link, 1), (tag, 1)))
                                value = (key_word, 1)
                                mapper_output.append(value)

            # Process anchor tags
            if self.a_tags_request:
                if (tag == 'a'):
                    if words:
                        for word in words:
                            if word not in self.stop_list:
                                key_word = '%s%s_%s' % (
                                        self.label['anchor_tag'],
                                        external_bit, word)
                                # Additional Info
                                #value = (key_word, ( 
                                #    1, (page_link, 1), (tag, 1)))
                                value = (key_word, 1)
                                mapper_output.append(value)

            # Process meta data
            if self.meta_request:
                # Retrieve text from the title
                if tag == 'title':
                    if words:
                        for word in words:
                            if word not in self.stop_list:
                                key_word = '%s%s_%s' % (
                                    self.label['meta_data'],
                                    external_bit, word)
                                # Additional Info
                                #value = (key_word, ( 
                                #    1, (page_link, 1), (tag, 1)))
                                value = (key_word, 1)
                                mapper_output.append(value)
                # Retrieve text from the meta description
                if tag == 'meta':
                    try:
                        name = element.attrib['name']
                        if name == 'description':
                            try:
                                text = element.attrib['content']
                                if text:
                                    words = text.lower().split()
                                    for word in words:
                                        if word not in self.stop_list:
                                            key_word = '%s%s_%s' % (
                                                self.label['meta_data'],
                                                external_bit, word)
                                            # Additional Info
                                            #value = (key_word, ( 
                                            #    1, (page_link, 1), (tag, 1)))
                                            value = (key_word, 1)
                                            mapper_output.append(value)
                            except:
                                continue
                    except:
                        continue

            
            # Process words based upon context 
            # (i.e. if a specified word is in the text)
            if self.context_search_tag:
                if words:
                    if (tag == 'p' or tag == 'li' or tag == 'td' or 
                        tag == 'h1' or tag == 'h2' or tag == 'h3' or
                        tag == 'h4' or tag == 'h5' or tag == 'h6' or
                        tag == 'a'):
                        for search_word in self.context_search_tag:
                            search_word = search_word.lower()
                            if search_word in words:
                                # Emit each word in context
                                for word in words:
                                    if word not in self.stop_list:
                                        key_word = '%s%s_%s' % (
                                            self.label['context_word'],
                                            external_bit, word)
                                        # Additional Info (Disabled)
                                        #value = (key_word, (
                                        #    1, (page_link, 1),
                                        #    (tag, 1), search_word))
                                        value = (key_word, (1, search_word))
                                        mapper_output.append(value)
                                # Disable for now,
                                # ??? I think this is like search ???
                                # Emit whole context
                               # key_context = '%s%s_%s' % (
                               #     self.label['context'],
                               #     external_bit, search_word)  
                               # # use text not words-since list type
                               # value = (key_context, (
                               #     1, (page_link, 1), 
                               #     (tag, 1), (page_link, text),
                               #     (text, page_link)))
                               # mapper_output.append(value)

            # Process Synonym Rings (WordNet Synsets or User Chosen)
            if self.wordnet_lists:
                if words:
                    if (tag == 'p' or tag == 'li' or tag == 'td' or 
                        tag == 'h1' or tag == 'h2' or tag == 'h3' or
                        tag == 'h4' or tag == 'h5' or tag == 'h6' or
                        tag == 'a'):
                        for list_key in self.wordnet_lists:
                            total = 0
                            for word in words:
                                if word in self.wordnet_lists[list_key]: 
                                    key_wordnet = '%s%s_%s' % (
                                        self.label['wordnet'],
                                        external_bit, list_key) 
                                    # Additional Info (Disabled)
                                    #value = (key_wordnet, (
                                    #    1, (page_link, 1),
                                    #    (tag, 1)))
                                    value = (key_wordnet, 1)
                                    mapper_output.append(value)
                                # TODO: pull this out so always get total
                                # and not just for wordnet
                                if word not in self.stop_list:
                                    total = total + 1
                                if total > 0:
                                    key_total = '%s%s_%s' % (
                                        self.label['total_count'],
                                        external_bit, "total") 
                                    # Additional Info (Disabled)
                                    #value = (key_total, (
                                    #    total, (page_link, total),
                                    #    (tag, total)))
                                    value = (key_total, total)
                                    mapper_output.append(value)

        # Process the links on the page for parallel spider to follow
        (self.on_site_links, self.off_site_links, all_links, 
                ext_links) = process_links(page_links, 
                                           self.site_url, 
                                           self.site_domain, 
                                           self.scheme, 
                                           self.paths_to_follow,
                                           robots_txt)

        # If not processing just return with new links
        if no_emit:
            return

        # Analyze all the links on the page
        if self.all_links_request:
            for element in all_links:
                try: 
                    link = element.attrib['href']
                    try:
                        words = element.text
                    except:
                        words = []
                    key_word = '%s%s_%s' % (self.label['all_links'],
                            external_bit, link)
                    # Additional Info (Disabled)
                    #value = (key_word, ( 
                    #    1, (page_link, 1), (page_link, words), 
                    #    (words, page_link), (words, 1)))
                    value = (key_word, 1)
                    mapper_output.append(value)
                except:
                    continue

        # Analyze the external links on the page
        if self.external_links_request:
            for element in ext_links:
                try: 
                    link = element.attrib['href']
                    try:
                        words = element.text
                    except:
                        words = []
                    domain = decode(link)[1]
                    key_domain = '%s%s_%s' % (self.label['external_links'],
                            external_bit, domain)
                    # Additional Info (Disabled)
                    #value = (key_domain, ( 
                    #    1, (page_link, 1), (page_link, words), 
                    #    (words, page_link), (words, 1), (link, 1)))
                    value = (key_domain, 1)
                    mapper_output.append(value)
                except:
                    continue
        
        # Process x_path selectors
        # Currently not using
        if self.xpath_selectors:
            for selector in self.xpath_selectors:
                results = doc.xpath(selector['selector'])
                for result in results:
                    if selector['css_text']:
                        text = result.text
                        tail = result.tail
                        if tail:
                            if text:
                                text = text + " " + tail
                            else:
                                text = tail
                        result = text
                    key_selector = '%s%s_%s' % (self.label['selector'],
                            external_bit, selector['name'])
                    value = (key_selector, (
                        1, (page_link, 1), 
                        (page_link, result),
                        (result, page_link)))
                    mapper_output.append(value)
                    if selector['analyze'] and result:
                        for word in result.lower().split():
                            if word not in self.stop_list:
                                key_word = '%s%s_%s' % (
                                    self.label['selector_word'],
                                    external_bit, word) 
                                value = (key_word, (
                                    1, (page_link, 1),
                                    selector['name']))
                                mapper_output.append(value)

        return mapper_output


    def process(self, key, values):
        """
        Processes a key and a list of values (a reducer).

        Arguments:
        key - a string of text
        values - a lists of tuples, tuple size varies by key

        Returns:
        a key value tuple, based upon the key type
        """

        # The first part of the key is a label for its type
        label = key[0:4]

        # sum(total_count) is the total times the item appears
        total_count = []

        # sum_list(page_count) is a list of pages with the count of items/page
        page_count = []

        # sum_list(tag_count) is a list of tags with the count of items/tag
        tag_count = []

        # compress_list(page_info) is a list of pages associated with
        #   the item, and a list of words used on each page
        page_info = []

        # compress_list(words_info) is a list of words associated with 
        #   the item, and a list of pages those words are found on
        words_info = []

        # sum_list(words_count) is a list of words with counts
        words_count = []

        # sum_list(link_count) is a list of links with counts for each
        link_count = []

        # selector is the selector used to extract the information
        selector = ""

        # context is the word being searched for it's context
        context = ""

        # message is the error message
        message_count = []

        # Process based upon label
        if (label == self.label['text'] or 
            label == self.label['header'] or
            label == self.label['anchor_tag'] or
            label == self.label['meta_data'] or
            label == self.label['wordnet'] or
            label == self.label['total_count']):

            # Disabled Addition Info
            #for value in values:
                #count = value
                #count, page, tag = value
                #total_count.append(count)
                #page_count.append(page)
                #tag_count.append(tag)
                #Also changed in mapper!

            #return (key, (
                #sum(total_count) ))#, 
                #sum_list(page_count), 
                #sum_list(tag_count)))
            return  (key, sum(values))

        elif label == self.label['all_links']:

            # Disabled Addition Info
           # for value in values:
           #     count, page, pinfo, winfo, words = value
           #     total_count.append(count)
           #     page_count.append(page)
           #     page_info.append(pinfo)
           #     words_info.append(winfo)
           #     words_count.append(words)

           # return (key, ( 
           #     sum(total_count), 
           #     sum_list(page_count),
           #     compress_list(page_info),
           #     compress_list(words_info),
           #     sum_list(words_count)))
            return  (key, sum(values))

        elif label == self.label['external_links']:

           # # Disabled Addition Info
           # for value in values:
           #     count, page, pinfo, winfo, words, link = value
           #     total_count.append(count)
           #     page_count.append(page)
           #     page_info.append(pinfo)
           #     words_info.append(winfo)
           #     words_count.append(words)
           #     link_count.append(link)

           # return (key, ( 
           #     sum(total_count), 
           #     sum_list(page_count),
           #     compress_list(page_info),
           #     compress_list(words_info),
           #     sum_list(words_count),
           #     sum_list(link_count)))
            return  (key, sum(values))

        elif label == self.label['context_word']:

           # # Disable Additional Info
           # for value in values:
           #     count, page, tag, context = value
           #     total_count.append(count)
           #     page_count.append(page)
           #     tag_count.append(tag)

           # return (key, ( 
           #     sum(total_count), 
           #     sum_list(page_count),
           #     sum_list(tag_count),
           #     context))

            for value in values:
                count, context = value
                total_count.append(count)
            return (key, (sum(total_count), context))

        # Currently not using
        elif label == self.label['context']:

            for value in values:
                count, page, tag, pinfo, winfo = value
                total_count.append(count)
                page_count.append(page)
                tag_count.append(tag)
                page_info.append(pinfo)
                words_info.append(winfo)

            return (key, ( 
                sum(total_count), 
                sum_list(page_count),
                sum_list(tag_count),
                compress_list(page_info),
                compress_list(words_info)))

        # Currently not using
        elif label == self.label['selector']:

            for value in values:
                count, page, pinfo, winfo = value
                total_count.append(count)
                page_count.append(page)
                page_info.append(pinfo)
                words_info.append(winfo)

            return (key, ( 
                sum(total_count), 
                sum_list(page_count),
                compress_list(page_info),
                compress_list(words_info)))

        # Currently not using
        elif label == self.label['selector_word']:

            for value in values:
                count, page, selector = value
                total_count.append(count)
                page_count.append(page)

            return (key, ( 
                sum(total_count), 
                sum_list(page_count),
                selector))

        elif label == self.label['error_message']:
            #return ('zmsg_error', 'error')
            # TODO: Maybe add count for error types?

            for value in values:
                message_count.append(value)

            return (key, sum_list(message))

            #return ('zmsg_error', values)
        
        else:

            return ('zmsg_error', ('unrecognized key', 1))


### Da Func(y) Helpers ###
def process_links(links, site_url, site_domain, scheme, 
                  paths_to_follow, robots_txt):
    """
    Make relative links absolute and separate on site and off site links
    
    Arguments:
    links - list of all the links on the page
    site_url - the url with any paths removed
    site_domain - domain with www removed but other hosts included
    scheme - http or https

    Returns:
    on_site - list of on site urls to follow
    off_site - list of off site urls to follow
    all_links - list of all link elements
    ext_links - list of external site link elements
    """

    # Lists to hold internal and external links
    on_site = []
    off_site = []
    
    # List to hold link elements
    all_links = []
    ext_links = []
    
    # Process all the links
    for link_tuple in links:
      
        link = link_tuple[0]
        element = link_tuple[1]

        # if a paths to follow given, break if not in url
        follow = True
        if paths_to_follow:
            follow = False
            for path in paths_to_follow:
                if path in link:
                    follow = True
        if follow is False:
            continue

        all_links.append(element)

        # If absolute url
        if link[0:4] == "http" or link[0:5] == "https":
            
            # With site name add to on site list, else off site list
            if (site_domain in link and
                robots_txt.can_fetch('*', link)):
                on_site.append(link)

            else:
                off_site.append(link)
                ext_links.append(element)

        # If schemeless add scheme
        if (link and link[0:2] == '//'):
            link_abs = scheme + link
            if robots_txt.can_fetch('*', link_abs):
                on_site.append(link_abs)

        # If relative add site
        elif (link and link[0] == '/' and len(link) > 1):            
            link_abs = site_url + link
            if robots_txt.can_fetch('*', link_abs):
                on_site.append(link_abs)
            
        # Else skip, junk
            
    return (on_site, off_site, all_links, ext_links)


def decode(site_url):
    """
    Separate scheme, host, and path from url
    
    Arguments
    site_url - ex. http://www.somesite.com/
    
    Returns
    site_url - http://www.somesite.com/ 
    site_domain - somesite.com/
    scheme - http:

    The returned site_url has no path so it can construct absolute hrefs.
    The domain will include subdomains, so if one is given, only the 
    subdomains will be searched on the site
    """
        
    # Remove the scheme
    scheme, delimeter, domain_path = site_url.partition("//")

    # Remove the path
    domain = domain_path.partition("/")[0]

    # Strip out host if www. so can traverse subdomains
    site_domain = domain.replace("www.", "")

    # Add back scheme to domain for url
    site_url = scheme + "//" + domain

    return (site_url, site_domain, scheme)


def sum_list(list_o_tuples):
    """
    Eliminates duplicates and totals counts in a list

    Argument
    list_o_tuples - a list of label, count pairs

    Returns
    new_list - a list of lable, count pairs, no duplicate labels

    i.e. given [(label1, 5),(label2, 6),(label1, 4)]
    the procedure will return: [(label1, 9), (label2, 6)]
    """

    new_list = [] # list to return

    sorted_list = sorted(list_o_tuples)

    label = "" # current label
    previous_label = sorted_list[0][0]

    length = len(sorted_list)
    i = 0
    total_count = 0

    while i < length:

        # Unpack current label and count
        label, count = sorted_list[i]

        # If same label, just add to total
        if label == previous_label:
            total_count  = total_count  + count

        # Otherwise, add to list and set new previous
        else:
            value = (previous_label, total_count)
            new_list.append(value)
            previous_label = label
            total_count = count

        i = i + 1
    
    # clean up the last one
    value = (label, total_count)
    new_list.append(value)
    
    return new_list

def compress_list(list_o_tuples):
    """
    Eliminates duplicates and creates a list of values

    Argument
    list_o_tuples - a list of labels and text values

    Returns
    new_list - a list of labels and text list pairs, no duplicate labels

    i.e. given [(label1, "f"),(label2, "a'hole'),(label1, "off")]
    the procedure will return: [(label1, ["f","off"]), (label2, ["a'hole"])]
    """

    new_list = [] # list to return

    sorted_list = sorted(list_o_tuples)

    label = "" # current label
    previous_label = sorted_list[0][0]

    length = len(sorted_list)
    i = 0
    text_list = [] # list for the text values

    while i < length:

        # Unpack current label and count
        label, text = sorted_list[i]

        # If same label, just add to total
        if label == previous_label:
            if text:
                text_list.append(text)

        # Otherwise, add to list and set new previous
        else:
            text_list = list(set(text_list))  # remove duplicates
            value = (previous_label, text_list)
            new_list.append(value)
            previous_label = label
            if text:
                text_list = [text]

        i = i + 1
    
    # clean up the last one
    text_list = list(set(text_list))  # remove duplicates
    value = (label, text_list)
    new_list.append(value)
    
    return new_list
