### USE FABRIC ###
#!/usr/bin/env python

""" Depot module for Parallel Spider 

    Contains tools to develop, test, and deploy the system
    For ease of use set spider as alias in bash.rc
"""

import optparse
import subprocess

class Spider(object):

  def develop(self):

    print 'hello'

if __name__ == "__main__":

    # Parse command line options and arguments.
    usage = "usage: %prog [options]"
    parser = optparse.OptionParser(usage)

    (options, args) = parser.parse_args()

    if len(args) < 1:
        parser.error("Must choose: develop, test or deploy.")

    method = args[0]

    spider = Spider()
    spidermethod = "spider." + method
    eval(spidermethod);


