""" Parallel Spider development tasks. """

import os
import subprocess

import fabric.api as fab


# Determine path to parallelspider directory.
# Assumes this file is in spiderdepot or subdirectory,
# and spiderdepot is 1 level below parallelspider.
path = os.path.realpath(__file__).partition('spiderdepot')[0]

""" TODO: Need to fix Redis so can start from directories other that ~
          Uses . when changing files: ./var/lib/spider/ """ 


@fab.task(default=True)
def local():

    import data
    import server
    import engine
    
    # Start Central Redis
    data.start('kvs', 'central')

    # Start User Redis
    data.start('kvs', 'user')

    # Start Session Redis
    data.start('kvs', 'session')

    # Start Data Engine Redis
    data.start('kvs', 'engine')

    # Start Spider Server - needs Central Redis
    server.start('local', mock=True)

    # Start Spider Engine (local mock client only)
    # - needs Central and Engine Redis
    engine.start('local')

    # Set current wroking directory: assumes spiderweb is 1 level 
    # below parallelspider with gruntfile and testacular.conf
    cwd = path + "spiderweb/"

    # Start Yeoman  
    cmd_line = "yeoman server"
    p = subprocess.Popen(cmd_line, shell=True, cwd=cwd)

    # Start testacular
    # Use fab for last/one item so ctrl-c will kill all processes
    with fab.lcd(cwd):
        fab.local("testacular start")


@fab.task
def refresh(datastore='local_redis'):

    if datastore=='local_redis':
        import redis
        test_user = 'a'
        test_user_folders = test_user + "_folders"
        user_redis = redis.Redis('localhost', 6378)
        template_folders = user_redis.get('test_folders')
        user_redis.set(test_user_folders, template_folders)


