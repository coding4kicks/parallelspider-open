#!/usr/bin/env python
"""
    test_parser - a test for the parser ;)

    needs test pages to parse
    TODO: handle/test PDFs
"""

import os
import unittest
import lxml.html
import lxml

from parallelspider import spiderparser

class TestParser(unittest.TestCase):
    """
    Tests the spiderparser on 50 sites
    """
    def setUp(self):
        """Initialize parser with one site, link names will be wrong"""

        site = "http://www.foxnews.com"
        tag_list = ["p", "h1", "h2", "h3", "h4", "h5", "h6"]

        self.parser = spiderparser.Parser(site, tag_list)

    def test_parser(self):

        os.chdir("testpages")
        for file_name in os.listdir("."):

            ### blank parser
            page = lxml.html.parse(file_name)

            ### parse and get the root
            #root = lxml.html.parse(file_name).getroot()

            ### print links, must check root not none
            ### can find tags: a, img, scirpt, link (feeds?), form
            ### need to make links absolute with url
            #if root:
            #    for link in root.iterlinks():
            #        print link
                    #el, ref, link, pos = link
                    #if el.tag == 'a':
                    #    print el.text
                    #    print link

            ### cycle through all elements in a page
            ### use to find tags: h1-6, p, title, li, td
            #for element in page.iter():
            #    print element
            #    if element.tag == 'p':
            #        print tag
            #        print element.text

            ### get alt attribute on image
            #for element in page.iter():
            #    if element.tag == 'img':
            #        try:
            #            alt = element.attrib["alt"]
            #            print alt
            #        except:
            #            continue

            ### print all elements and values
            #for element in page.iter():
            #    print element.tag
            #    print element.keys()
            #    print element.items()

            #try to print all a tags and link
            for element in page.iter():
                if element.tag == 'a':
                    #print element.text
                    try: 
                        link =  element.attrib['href']
                        #print link
                    except: 
                        continue

            ### css selectors

            ### prints all text content - too much js, etc.
            #print root.text_content()
            
            ### print the whole page
            #print lxml.etree.tostring(page)

            ### print all text - includes js, css, comments
            #print lxml.etree.tostring(page, method='text', encoding='UTF-8')
            
            ###



            #print file_name
            #with open(file_name, 'r') as f:
            #    try:
            #        self.parser.run(f)
            #        print file_name
            #    except:
            #        print "Error: " + file_name

        #print "what up crew"

        #return 0

    # test parser

    # test parser on pdfs

    # test links

    #test output

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

if __name__ == '__main__':
    unittest.main()

    
    
