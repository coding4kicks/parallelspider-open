"""Script to stop and start server on deployed instance."""

import os
import subprocess

mock = False

# Determine path to parallelspider directory.
# Assumes this file is in spiderdepot or subdirectory,
# and spiderdepot is 1 level below parallelspider.
path = os.path.realpath(__file__).partition('spiderserver')[0]


def server_master():

    # Start the server
    cmd_line = "nohup python " + path + "spiderserver/spiderserver.py &"
    # Mock S3 backend if true
    if mock:
        cmd_line += " -m"
    p = subprocess.Popen(cmd_line, shell=True)

    # Start the client
    #cmd_line = "nohup python " + path + "spiderengine/spiderclient.py &"
    #p = subprocess.Popen(cmd_line, shell=True)

    return

if __name__ == "__main__":
    server_master()
