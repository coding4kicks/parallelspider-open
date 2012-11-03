import robotparser
from bs4 import BeautifulSoup

class Parser:
    """ 
        Parser - recieves a document

        return - a list of links from the page.
        * Checks robots.txt for permission *
    """
    
    # List of saved content files
    #file_list = []

    def __init__(self, site, tags):
        """ Initializes the parser for a site address and retrieve robots.txt"""

        self.site_url = site    # Site url received from the spider
        self.link_list = []     # List of links
        self.output = {}        # Dictionary of output by tag
        self.tag_list = tags    # List of tags to search for content

        if self.tag_list == None:
            self.tag_list = ["p", "h1", "h2", "h3", "h4", "h5", "h6"]

        # Download robots.txt
        self.robots_txt = robotparser.RobotFileParser()
        self.robots_txt.set_url(self.site_url)
        self.robots_txt.read()

    def run(self, doc):
        """ Parses document 
        
            Input
                doc - an html document
        """

        #try:
            
        # Set up the beautifulsoup parser with lxml
        # http://www.crummy.com/software/BeautifulSoup/
        # http://lxml.de/
        soup = BeautifulSoup(doc, "lxml")

        #output = {}

        #initialize dictionary and find content
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

        print links
        # Process the links so they are absolute urls
        self.link_list = process_links(links, self.site_url)

        # Process the links so can be output to a file
        #link_output = ''
        #for link in self.link_list:
        #   link_output += link + '\n'

        # Save the content information for the page
        #### TODO - fix the hardwired file paths
        #outfile_name = "/home/project/Files/Content/" + doc_name + ".cnt"
        #data_out = output.encode('utf-8')
        #outfile = open(outfile_name, "w")
        #outfile.write(data_out)

        # Update the file list
        #self.file_list += [outfile_name]

        # Save the link information for the page
        #linkfile_name = "Files/Links/" + doc_name + ".lk"
        #linkfile = open(linkfile_name, "w")
        #linkfile.write(link_output)
            
        #except IOError: # Error opening the file
            #print("Problem opening page file: " + file_name)
        
        #except: 
        #    print("Problem parsing the Data")
        
        #finally: # Release the files
            #outfile.close()
            #linkfile.close()

    def get_links(self):
        """ Return the list of links found on the page. """
        return self.link_list

    def get_output(self):
        """ Return the output found on the page. """
        return self.output


#   def get_file_list(self):
#       """ Return the list of files """
#       return self.file_list


def process_links(links, site):
    """ 
        Process links based upon site name so don't leave the site.
        Returns a list of the links on a page.
    """

    # List to hold the new links
    link_list = []

    # Determine the site name from the site
    # Remove www, https://, http://, .com, .org
    temp1 = site.replace("www.", "")
    temp2 = temp1.replace("https://", "")
    temp3 = temp2.replace("http://", "")
    temp4 = temp3.replace(".com", "")
    site = temp4.replace(".org", "")

    # Split the output into a list
    list = links.split();

    # Process all the links
    for link in list:

        # If absolute url
        if link[0:3] == "http":
            
            # With site name add to list
            if site in link:
                
                    link_list += [link]
                    
            # If absolute without site name skip
        
        # If relative add site
        if (link[0] == '/' and len(link) > 1):
            
            link_abs = site + link
            link_list += [link_abs]
            
            # Else skip, junk
            
    return link_list
