"""
spiderparser - parses web pages for parallelspider and spiderrunner

Currently uses beautifulsoup and lxml.  
"""

import bs4
import robotparser

class Parser(object):
    """ 
    Parses a web page for requested content
        
    __init__ - Initializes site, tags, and checks robots.txt for permission.
    run      - parses a page
    get_links - returns the links found on the page
    get_output - returns a dictionary of tags with their content
    processlinks - makes all links absolute
    """

    def __init__(self, site, tags):
        """ 
        Initializes the parser, retrieves robots.txt
        
        Arguments:
        site -- name of site to scrape
        tags -- html tags to retrieve content from                                
        """

        self.site_url = site    # Site url received from the spider
        self.link_list = []     # List of links
        self.output = {}        # Dictionary of output by tag
        self.tag_list = tags    # List of tags to search for content

        # Default tag list
        if not self.tag_list:
            self.tag_list = ["p", "h1", "h2", "h3", "h4", "h5", "h6"]

        # Download robots.txt
        self.robots_txt = robotparser.RobotFileParser()
        self.robots_txt.set_url(self.site_url)
        self.robots_txt.read()

    def run(self, doc):
        """ 
        Parses a web page 
        
        Arguments
        doc - the html document to parse
        """
            
        # Set up the beautifulsoup parser with lxml
        soup = bs4.BeautifulSoup(doc, "lxml")

        #Initialize dictionary and find content
        for tag in self.tag_list:
            self.output[tag] = ""
        for tag in self.tag_list:
            for output in soup.find_all(tag):
                self.output[tag] += (output.text.encode('utf-8') + " ") 

        # Find all the links
        links = ''
        for link in soup.find_all('a'):
            # Only add if okay by robots.txt
            if self.robots_txt.can_fetch('*', str(link)):
                links += str(link.get('href')) + " \n"

        # Process the links so they are absolute urls
        self.link_list = process_links(links, self.site_url)


    def get_links(self):
        """ Return the list of links found on the page. """
        return self.link_list

    def get_output(self):
        """ Return the output found on the page. """
        return self.output


def process_links(links, site):
    """ 
        Process links based upon site name so don't leave the site.

        Returns a list of the links on a page.
    """

    # List to hold found links
    link_list = []

    # Determine the site name from the site
    # Remove www, https://, http://, .com, .org
    temp1 = site.replace("www.", "")
    temp2 = temp1.replace("https://", "")
    temp3 = temp2.replace("http://", "")
    temp4 = temp3.replace(".com", "")
    temp5 = temp4.replace(".org", "")
    site_stripped = temp5.replace("/", "")

    # Split the output into a list
    list = links.split();
    
    # Process all the links
    for link in list:
      
        # If absolute url
        if link[0:4] == "http" or link[0:5] == "https":
            
            # With site name add to list
            if site_stripped in link:
                
                    link_list += [link]
                    
            # If absolute without site name skip
        
        # If relative add site
        if (link[0] == '/' and len(link) > 1):
            
            link_abs = site + link
            link_list += [link_abs]
            
            # Else skip, junk
            
    return link_list
