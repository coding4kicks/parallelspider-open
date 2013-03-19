""" Parallel Spider server tasks. """

import fabric.api as fab

import os
import signal
import subprocess

# Determine path to parallelspider directory.
# Assumes this file is in spiderdepot or subdirectory,
# and spiderdepot is 1 level below parallelspider.
path = os.path.realpath(__file__).partition('spiderdepot')[0]

@fab.task
def start(type='local', mock=False, args=None):
    """Start a Twisted server instance."""

    # Start Spider Server on localhost
    if type == 'local':

        # Assumes spiderserver is 1 level below parallelspider,
        # and spiderserver.py is in spiderserver
        cmd_line = "python spiderserver.py"

        # Mock S3 backend if true
        if mock:
            cmd_line += " -m"

        cwd= path + "spiderserver"
        p = subprocess.Popen(cmd_line, shell=True, cwd=cwd)

@fab.task
def stop(type='local', args=None):
    """Stop a Twisted server instance."""

    # Stop Spider Server on localhost
    if type == 'local':

        # Get a list of all processes
        p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
        out, err = p.communicate()

        # Kill any process with spiderserver in the name
        for line in out.splitlines():
            if 'spiderserver' in line:
                pid = int(line.split(None, 1)[0])
                os.kill(pid, signal.SIGKILL)

@fab.task
def restart(type='local', mock=False, args=None):
    """Restart a Twisted server instance."""

    # Restart Spider Server on localhost
    if type == 'local':
        stop()
        start(mock=mock)

