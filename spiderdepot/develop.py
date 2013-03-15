""" Parallel Spider development tasks. """

import fabric.api as fab

import os
import subprocess


@fab.task
def test(word=None):
    
    import server
    server.start('local')


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

    # Start Yeoman
    cmd_line = "yeoman server"
    cwd="/Users/scottyoung/projects/parallelspider/spiderweb"
    p = subprocess.Popen(cmd_line, shell=True, cwd=cwd)


    # Start testacular
    # Use fab for last/one item so ctrl-c will kill all processes
    with fab.lcd("~/projects/parallelspider/spiderweb/"):
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


