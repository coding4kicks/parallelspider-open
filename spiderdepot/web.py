""" Parallel Spider web tasks. """

import subprocess

import fabric.api as fab

import staticbuilder

@fab.task
def build():
    """Perform a Yeoman build of the web client."""
    
    # Start Yeoman
    cmd_line = "yeoman build"
    cwd="/Users/scottyoung/projects/parallelspider/spiderweb"
    p = subprocess.Popen(cmd_line, shell=True, cwd=cwd)


@fab.task
def deploy():
    """Deploy the web client to S3"""

    #sb -r dist www.parallelspider.com
    
    pass


