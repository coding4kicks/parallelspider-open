"""
    Mr. Feynman analyzes a parsed html document.

    The module takes in a parsed document and emits key value pairs.
    It is designed to be incorporated into a MapReduce solution.

    TODO: Add pagerank for links
    TODO: Add ability to handle other file types, i.e. PDF
"""
import copy

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
        
        Args:
        passed_url - the url of the site to be searched
        config_dict - dictionary of configuration parameters
            text_request: boolean - true to analyze visible text
            header_request: boolean - true to analyze header text
            meta_request: boolean - true to analyze hidden text
            a_tags_request: boolean - true to analyze link text
            all_links_request: boolean - true to analyze all links
            external_links_request: boolean - true to analyze external links
            context_search_tag: list of words to find surrounding words
            wordnet_lists: list of synonym rings to find
            xpath_selectors: dictionary of xpath selectors and info
            css_selectors: dictionary of css selectors and info
            paths_to_follow: list of strings used to filter out urls
            stop_list: list of words not to emit

        If the passed url contains a subdomain, only this will be searched.

        GOALS of REFACTOR:
        TODO: Each type of process should be moved into a strategy pattern, 
            with a common input and output format: 
            input should be the data passed by lxml and 
            output should be the appendage to the map output.
        TODO: Make easy to add additional data
        TODO: Add Selectors
        TODO: Add Synonym Rings
        TODO: Make variables more consitent with Spider Client and Spider Web
        TODO: QA tags associated with each analysis: visible text add div/span
        """   
 
        self.passed_url = passed_url # may contain a path
        self.site_url, self.site_domain, self.scheme = decode(self.passed_url)
        self.on_site_links = []             
        self.off_site_links = []  
        self._validate_requests(config_dict)
        self._set_tag_types()

        # Labels for various processing types - append to start of key
        # All labelels are 4 characters.  A tag for external or internal is
        # then appended, followed by an underscore. i.e. texti_
        self.label = { 'visible_text': 'text', 'headline_text': 'head', 'link_text': 'atag',
                       'hidden_text': 'meta', 'all_links': 'link',
                       'external_links': 'extl', 
                       'context_word': 'cntw', 'synonym_ring': 'wdnt',
                       'total_count': 'totl', 'selector': 'selc', 
                       'selector_word': 'selw', 'tag_count': 'tagc',
                       'link_count': 'lnkc', 'error_message': 'zmsg'}

###############################################################################
### Mapper
###############################################################################
    def analyze(self, doc, page_link, robots_txt,
                external=False, no_emit=False):
        """ 
        Analyze a parsed document, returning key,value pairs (a mapper).

        Args:
            doc - a lxml.html parsed document
            page_link - link to page currently being analyzed
            robots_text - used to determine which links can be followed 
            external - boolean, if True will not pass any links to follow 
                       and will mark all output as external
            no_emit - boolean, if True will only find links on the page 
                      and will not generate output to anlyze. This allows a
                      hole site to be scraped but only certain pages to be
                      analyzed.

        Returns:
            mapper_output - a list of key-value-pair tuples 
                for Parallel Spider to emit

        Keys are prefixed with a 4 character label for type,
        along with one character for external or internal, 
        then an underscore followed by the key name itself

        Key types:
            text - analyze visible text on the page           
            header - analyze headlines on a page         
            anchor_tag - analyze link text on a page
            meta_data - analyze hiddent descriptions on a page
            all_links - analyze all the links on a page
            external_links - analyze external site links on a page
            context - analyze the context around a specified word
            context_word - analyze each word in the context ???
                Q. Do I need this?
            wordnet - analyze synonym rings
            total_count - a total count of all words
            selector - select certain element out of the page
                Q. Do I need this?
            selector_word - analyze the selected words
            error_message - error messages in processing
        """

        mapper_output = [] # key-value tuples for mapper output
        page_links = [] # all the links on the page
        external_bit = 'e' if external else 'i' # external or internal page
        key_total = '%s%s_%s' % (self.label['total_count'],
                                 external_bit, "total") 
         
        for element in doc.iter(): # Iterate once through the entire document
            
            try:  # Grab tag name and text (+ tail text)   
                tag = element.tag
                text = element.text
                tail = element.tail
            except:
                continue

            words = None # text words split to list
            if tail: # combine text and tail
                text = text + " " + tail if text else tail
            if text: # lowercase and split to list
                words = text.lower().split()
 
            if tag == 'a':
                try: 
                    link = element.attrib['href']
                    page_links.append((link, element))
                except:
                    pass
            
            if no_emit: continue # Skip rest if not analyzing page

            # Emit tag count for each tag
            key_tag = '%s%s_%s' % (self.label['tag_count'], external_bit, tag) 
            mapper_output.append((key_tag, 1))

            if not words: continue # Skip analysis if no words to analyze

            # Emit the total count of words - includes stop words
            total = len(words)
            if total > 0:
                # Additional Info (Disabled)
                #value = (key_total, (total, (page_link, total), (tag, total)))
                value = (key_total, total)
                mapper_output.append(value)
 
            if self.visible_text_request:
                if tag in self.visible_text_tags:
                    mapper_output.extend(self._analyze_text(words,
                        self.label['visible_text'], page_link, external_bit))

            if self.headline_text_request:
                if tag in self.headline_text_tags:
                    mapper_output.extend(self._analyze_text(words,
                        self.label['headline_text'], page_link, external_bit))

            if self.link_text_request:
                if (tag == 'a'):
                    mapper_output.extend(self._analyze_text(words,
                        self.label['link_text'], page_link, external_bit))

            if self.hidden_text_request:
                if tag in self.hidden_text_tags:
                   mapper_output.extend(self._analyze_hidden_text(
                        tag, words, page_link, external_bit))
            
            if self.context_words:
                if tag in self.visible_text_tags:
                   mapper_output.extend(self._analyze_context_words(
                        words, page_link, external_bit))

            if self.synonym_rings:
               if tag in self.visible_text_tags:
                   mapper_output.extend(self._analyze_synonym_rings(
                        words, page_link, external_bit))

            # END - cycle through elements in doc

        # Process links to follow (on/off) and to analyze (all/ext)
        (self.on_site_links, self.off_site_links, all_links, ext_links) = \
            process_links(page_links, self.site_url, self.site_domain, 
                          self.scheme, self.paths_to_follow, robots_txt)
        
        if no_emit: return # not analyzing page, return with new links

        mapper_output.extend(self._analyze_summary_link_info(
            all_links, ext_links, external_bit))

        if self.all_links_request: 
            mapper_output.extend(self._analyze_links(
                all_links, external_bit, page_link, 'all'))
 
        if self.ext_links_request: 
            mapper_output.extend(self._analyze_links(
                ext_links, external_bit, page_link, 'ext'))
        
        if self.xpath_selectors:
            mapper_output.extend(self._analyze_selectors(
                doc, external_bit, page_link))

        return mapper_output

    def _analyze_text(self, words, label, page_link, external_bit):
        """Generate mapper output for text types."""
        mapper_output = []
        for word in words:
           if word not in self.stop_list:
               key_word = '%s%s_%s' % (label, external_bit, word)
               # Additional Info
               #value = (key_word, (1, (page_link, 1), (tag, 1)))
               value = (key_word, 1)
               mapper_output.append(value)
        return mapper_output

    def _analyze_hidden_text(self, tag, words, page_link, external_bit):
        """Generate mapper output for hidden text."""
        mapper_output = []
        if tag == 'title':
            mapper_output.extend(self._analyze_text(words,
                self.label['hidden_text'], page_link, external_bit))
        elif tag == 'meta':
            try:
                name = element.attrib['name']
                if name == 'description':
                    try:
                        text = element.attrib['content']
                        if text:
                            words = text.lower().split()
                            mapper_output.extend(self._analyze_text(
                                words, self.label['hidden_text'], 
                                page_link, external_bit))
                    except:
                        pass
            except:
                pass
        return mapper_output

    def _analyze_context_words(self, words, page_link, external_bit):
        """Generate mapper output for context words."""
        mapper_output = []
        for search_word in self.context_words:
            search_word = search_word.lower()
            if search_word in words:
                # Emit each word in context
                for word in words:
                    if word not in self.stop_list:
                        key_word = '%s%s_%s' % (
                            self.label['context_word'],
                            external_bit, word)
                        # Additional Info (Disabled)
                        #value = (key_word, (1, (page_link, 1),
                        #                   (tag, 1), search_word))
                        value = (key_word, (1, search_word))
                        mapper_output.append(value)
        return mapper_output

    def _analyze_synonym_rings(self, words, page_link, external_bit):
        """Generate mapper output for synonym rings."""
        mapper_output = []
        for list_key in self.synonym_rings:
            total = 0
            for word in words:
                if word in self.synonym_rings[list_key]: 
                    key_wordnet = '%s%s_%s' % (
                        self.label['synonym_ring'],
                        external_bit, list_key) 
                    # Additional Info (Disabled)
                    #value = (key_wordnet, (1, (page_link, 1), (tag, 1)))
                    value = (key_wordnet, 1)
                    mapper_output.append(value)
        return mapper_output

    def _analyze_summary_link_info(self, all_links, ext_links, external_bit):
        """Generate mapper output for summary int/ext link count."""
        mapper_output = []
        total_links = len(all_links)
        external_links = len(ext_links)
        internal_links = total_links - external_links
        if internal_links > 0:
            key_int_links = '%s%s_%s' % (
                self.label['link_count'], external_bit, 'internal') 
            value = (key_int_links, internal_links)
            mapper_output.append(value)
        if external_links > 0:
            key_ext_links = '%s%s_%s' % (
                self.label['link_count'], external_bit, 'external') 
            value = (key_ext_links, external_links)
            mapper_output.append(value)
        return mapper_output

    def _analyze_links(self, links, external_bit, page_link, link_type):
        """Generate mapper output for links."""
        mapper_output = []
        for element in links:
            try: 
                link = element.attrib['href']
                try:
                    words = element.text
                except:
                    words = []
                if link_type == 'ext': 
                    label = self.label['external_links'] 
                else:
                    label = self.label['all_links']
                key_name = decode(link)[1] if link_type == 'ext' else link
                key = '%s%s_%s' % (label, external_bit, key_name)
                # Additional Info (Disabled) - different for ext/all (links)
                #value = (key, ( 1, (page_link, 1), (page_link, words), 
                #              (words, page_link), (words, 1), *(link, 1)*dif))
                value = (key, 1)
                mapper_output.append(value)
            except:
                continue
        return mapper_output

    def _analyze_selectors(self, doc, external_bit, page_link):
        """Generate mapper output for all selectors, xpath & converted css."""
        mapper_output = []
        for selector in self.xpath_selectors:
            results = doc.xpath(selector['selector'])
            for result in results:
                if selector['css_text']:
                    text = result.text
                    tail = result.tail
                    if tail:
                        text = text + " " + tail if text else tail
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
       
    def _validate_requests(self, config):
        """Validate analysis requests passed in configuration dictionary."""
        self.visible_text_request = config.get('text_request', False)
        self.headline_text_request = config.get('header_request', False)
        self.hidden_text_request = config.get('meta_request', False)
        self.link_text_request = config.get('a_tags_request', False)
        self.all_links_request = config.get('all_links_request', False)
        self.ext_links_request = config.get('external_links_request', False)
        self.context_words = config.get('context_search_tag', [])
        self.synonym_rings = config.get('wordnet_lists', None)
        self.xpath_selectors = config.get('xpath_selectors', [])
        self.paths_to_follow = config.get('paths_to_follow', [])
        self.stop_list = config.get('stop_list', [])
        self.css_selectors = \
                copy.deepcopy(config.get('css_selectors', None))
        # Compile and append css selectors to xpath_selctors
        if self.css_selectors:
            for selector in self.css_selectors:
                sel = lxml.cssselect.CSSSelector(selector['selector'])
                selector['selector'] = sel.path
                self.xpath_selectors.append(selector)

    def _set_tag_types(self):
        """Set up tag types for certain types of analyses."""
        self.visible_text_tags = ['p', 'li', 'td', 'h1', 'h2', 'h3', 'h4',
                                  'h5', 'h6', 'a']
        self.headline_text_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        self.hidden_text_tags = ['title', 'meta'] #add img(alt)???
        

###############################################################################
### Reducer
###############################################################################
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
        if (label == self.label['visible_text'] or 
            label == self.label['headline_text'] or
            label == self.label['link_text'] or
            label == self.label['hidden_text'] or
            label == self.label['synonym_ring'] or
            label == self.label['total_count'] or
            label == self.label['tag_count'] or
            label == self.label['link_count']):

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

###############################################################################
### Da Func(y) Helpers
###############################################################################
def process_links(links, site_url, site_domain, scheme, 
                  paths_to_follow, robots_txt):
    """
    Make relative links absolute and separate on site and off site links
    
    Args:
        links - list of all the links on the page
        site_url - the url with any paths removed
        site_domain - domain with www removed but other hosts included
        scheme - http or https
        paths_to_follow - list of valid paths for links to add to on_site links
        robots_txt - robot.txt file indicating which links can be followed

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
        elif (link and link[0:2] == '//'):
            link_abs = scheme + link
            if robots_txt.can_fetch('*', link_abs):
                on_site.append(link_abs)

        # If relative add site
        elif (link and link[0] == '/' and len(link) > 1):            
            link_abs = site_url + link
            if robots_txt.can_fetch('*', link_abs):
                on_site.append(link_abs)
        
        # Relative without backslash so add
        else:
            if (link and link != '/' and (';' not in link)
                and ('javascript' not in link)):
                link_abs = site_url + '/' + link
                if robots_txt.can_fetch('*', link_abs):
                    on_site.append(link_abs)

            
    return (on_site, off_site, all_links, ext_links)


def decode(site_url):
    """
    Separate scheme, host, and path from url
    
    Args:
        site_url - ex. http://www.somesite.com/
    
    Returns:
        site_url - http://www.somesite.com/ 
        site_domain - somesite.com/
        scheme - http:

    The returned site_url has no path so it can construct absolute hrefs.
    The domain will include subdomains, so if one is given, 
        only the subdomains will be searched on the site
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

    Args:
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

    Args:
        list_o_tuples - a list of labels and text values

    Returns:
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
