""" Parallel Spider server tasks. """

import fabric.api as fab

import fileinput
import os
import signal
import subprocess

# Determine path to parallelspider directory.
# Assumes this file is in spiderdepot or subdirectory,
# and spiderdepot is 1 level below parallelspider.
path = os.path.realpath(__file__).partition('spiderdepot')[0]

fab.env.key_filename = '~/.ssh/mykey.rsa'

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

@fab.task
def deploy():
    """Push server.py to the server and restart"""

    # Copy spiderserver.py to parallelspider directory
    cwd = path + "spiderserver/"
    cmd_line = "cp spiderserver.py ../"
    p = subprocess.call(cmd_line, shell=True, cwd=cwd)

    set_deploy_config()

    # secure copy server.py (in parallelspider directory) to server 
    cwd = path
    cmd_line = "scp -i ~/.ssh/mykey.rsa spiderserver.py " + \
               "ubuntu@ec2-50-16-63-62.compute-1.amazonaws.com:" + \
               "~/parallelspider/spiderserver/spiderserver.py"
    p = subprocess.call(cmd_line, shell=True, cwd=cwd)
    # copy server starter
    cwd = path + "spiderserver/"
    cmd_line = "scp -i ~/.ssh/mykey.rsa server_starter.py " + \
               "ubuntu@ec2-50-16-63-62.compute-1.amazonaws.com:" + \
               "~/parallelspider/spiderserver/server_starter.py"
    p = subprocess.call(cmd_line, shell=True, cwd=cwd)


@fab.task
@fab.hosts('ubuntu@ec2-50-16-63-62.compute-1.amazonaws.com')
def restart_remote():
    """Restart the deployed server."""

    # KIll *ALL* Python processes
    processes = fab.run('ps -A')
    for line in processes.splitlines():
        if 'python' in line:
            pid = int(line.split(None, 1)[0])
            cmd = "kill " + str(pid)
            fab.run(cmd)

    cmd_line = "ssh -i ~/.ssh/mykey.rsa ubuntu@ec2-50-16-63-62.compute-1.amazonaws.com 'python ~/parallelspider/spiderserver/server_starter.py'"
    p = subprocess.call(cmd_line, shell=True)

def set_deploy_config():
    """Sets port in server deployment"""

    port = "50070"

    # Directory for deployment server.py 
    directory_path = path

    # Replace port info in server.py
    file_path = directory_path + "spiderserver.py"
    for line in fileinput.input(file_path, inplace=1):
        new_port_line = line.replace("8000", port)
        print "%s" % (new_port_line),


