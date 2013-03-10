""" Parallel Spider analysis engine tasks. """

import fabric.api as fab

import os
import signal
import subprocess

# Determine path to parallelspider directory
# Assumes we are in spiderdepot or subdirectory,
# and spiderdepot is 1 level below parallelspider
# and spiderclient.py is in spiderengine
path = os.path.realpath(__file__).partition('spiderdepot')[0]

@fab.task
def start(type='local', args=None):

    # Start Spider Engine on localhost (only a mock client)
    # Must have Redis running (Central and Engine) to start
    if type == 'local':
        cmd_line = "python spiderclient.py"
        cwd= path + "spiderengine"
        p = subprocess.Popen(cmd_line, shell=True, cwd=cwd)

@fab.task
def stop(type='local', args=None):

    # Stop Spider Engine on localhost
    if type == 'local':

        # Get a list of all processes
        p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
        out, err = p.communicate()

        # Kill any process with spiderclient in the name
        for line in out.splitlines():
            if 'spiderclient' in line:
                pid = int(line.split(None, 1)[0])
                os.kill(pid, signal.SIGKILL)

@fab.task
def restart(type='local', args=None):

    # Restart Spider Engine on localhost
    if type == 'local':
        stop()
        start()

