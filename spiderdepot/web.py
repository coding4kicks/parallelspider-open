""" Parallel Spider web tasks. """

import os
import fileinput
import subprocess

import fabric.api as fab

import staticbuilder

# Determine path to parallelspider directory.
# Assumes this file is in spiderdepot or subdirectory,
# and spiderdepot is 1 level below parallelspider.
path = os.path.realpath(__file__).partition('spiderdepot')[0]


@fab.task
def build():
    """Perform a Yeoman build of the web client."""
    
    # Set current wroking directory: assumes spiderweb is 1 level 
    # below parallelspider with gruntfile
    cwd = path + "spiderweb/"

    # Build with Yeoman (must call synchronously)
    cmd_line = "yeoman build"
    p = subprocess.call(cmd_line, shell=True, cwd=cwd)


@fab.task
def deploy():
    """Deploy the web client to S3."""

    set_deploy_config()

    # Copy dist directory to S3
    sb = staticbuilder.StaticBuilder()
    directory = path + "spiderweb/dist"
    sb.upload(paths_in=directory, path_out="www.parallelspider.com",
                         recursive=True)

def set_deploy_config():
    """Sets host and mock for deployment"""

    host = "111.111.111.111"

    # Set directory for distribution scripts: 
    # Assumes parallelspider/spiderweb/dist/scripts/ 
    directory_path = path + "spiderweb/dist/scripts/"

    # Find renamed services file
    contents = os.listdir(directory_path)
    for f in contents:
        if "service" in f:
            # avoid backups
            if "~" not in f:
                service_file = f

    # Replace host and mock info in dist version of config service file
    file_path = directory_path + service_file
    for line in fileinput.input(file_path, inplace=1):
        new_host_line = line.replace("localhost:8000", host)
        new_mock_line = new_host_line.replace("mock = true", "mock = false")
        print "%s" % (new_mock_line),


