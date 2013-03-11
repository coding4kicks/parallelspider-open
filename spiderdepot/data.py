""" Parallel Spider data tasks. """

import fabric.api as fab

import os
import signal # can I change the process name 
# maybe with: http://code.google.com/p/py-setproctitle/
# Or with Redis just use different config files to start
# since it seems config name shows up in process
import subprocess

# Determine path to parallelspider directory.
# Assumes this file is in spiderdepot or subdirectory,
# and spiderdepot is 1 level below parallelspider.
path = os.path.realpath(__file__).partition('spiderdepot')[0]

@fab.task
def start(type='kvs', conf='redis'):

    # Start Key Value Store (KVS) with specified config file
    if type == 'kvs':

        # Assumes spiderengine is 1 level below parallelspider,
        # and spiderclient.py is in spiderengine
        cmd_line = "redis-server " + path + "spiderdata/" + conf + ".conf"
        p = subprocess.Popen(cmd_line, shell=True)

