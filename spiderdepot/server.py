""" Parallel Spider server tasks. """

import fabric.api as fab

import os
import signal
import subprocess

@fab.task
def start(type='local', args=None):

    # Start Spider Server on localhost
    if type == 'local':
        cmd_line = "python spiderserver.py"
        cwd="/Users/scottyoung/projects/parallelspider/spiderserver"
        p = subprocess.Popen(cmd_line, shell=True, cwd=cwd)

@fab.task
def stop(type='local', args=None):

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
def restart(type='local', args=None):

    # Restart Spider Server on localhost
    if type == 'local':
        stop()
        start()

