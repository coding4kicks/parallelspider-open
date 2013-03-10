""" Parallel Spider development tasks. """

import fabric.api as fab

import os
import subprocess

import server

@fab.task
def test(word=None):

    server.start('local')

    #if word:
    #    print "what up" + word

    #print (os.environ['S3_LOCATION'])

    #os.environ['TEST'] = 'testing'

    #print(os.environ['TEST'])

    # Start central Redis
    #cmd_line = "redis-server"
    #p = subprocess.Popen(cmd_line, shell=True)
    #print (p.pid)


@fab.task(default=True)
def local():
    """ Start local development environment for Parallel Spider """
    
    # Start central Redis
    cmd_line = "redis-server"
    p = subprocess.Popen(cmd_line, shell=True)

    # Start local Redis
    cmd_line = "echo 'port 6389' | redis-server -"
    p = subprocess.Popen(cmd_line, shell=True)

    # Start Yeoman
    cmd_line = "yeoman server"
    cwd="/Users/scottyoung/projects/parallelspider/spiderweb"
    p = subprocess.Popen(cmd_line, shell=True, cwd=cwd)

    # Start Spider Server 
    server.start('local')

    # Start Spider Client
    cmd_line = "python spiderclient.py"
    cwd="/Users/scottyoung/projects/parallelspider/parallelspider"
    p = subprocess.Popen(cmd_line, shell=True, cwd=cwd)

    # Start testacular
    # Use fab for last/one item so ctrl-c will kill all processes
    with fab.lcd("~/projects/parallelspider/spiderweb/"):
        fab.local("testacular start")


