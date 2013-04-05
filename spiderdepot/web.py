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

    # BROKEN - YEOMAN BUILD???
    #set_deploy_config()

    # Copy dist directory to S3
    #sb = staticbuilder.StaticBuilder()
    #directory = path + "spiderweb/dist"
    #sb.upload(paths_in=directory, path_out="www.parallelspider.com",
    #                     recursive=True)

    # Upload entire APP folder (should be dist, WTF yeoman)
    sb = staticbuilder.StaticBuilder()
    directory = path + "spiderweb/app"
    sb.upload(paths_in=directory, path_out="www.parallelspider.com",
                         recursive=True)

    # Upload compiled CSS
    directory = path + "spiderweb/temp"
    sb.upload(paths_in=directory, path_out="www.parallelspider.com",
                         recursive=True)

    # Copy services.js to parallelspider directroy
    cwd = path + "spiderweb/app/scripts/"
    cmd_line = "cp services.js ../../../"
    p = subprocess.call(cmd_line, shell=True, cwd=cwd)

    # Set host
    set_deploy_config()

    # Upload compiled CSS
    directory = path + "services.js"
    sb.upload(paths_in=directory, path_out="www.parallelspider.com/scripts",
              recursive=False)


def set_deploy_config():
    """Sets host and mock for deployment"""


    host = "ec2-174-129-125-34.compute-1.amazonaws.com:8000"

    # BROKEN until fix yoeman build - wtf
    # Set directory for distribution scripts: 
    # Assumes parallelspider/spiderweb/dist/scripts/ 
    #directory_path = path + "spiderweb/dist/scripts/"
    directory_path = path

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
        # not setting mock yet
        new_mock_line = new_host_line.replace("mock = true", "mock = false")
        print "%s" % (new_mock_line),
        #print "%s" % (new_host_line),


