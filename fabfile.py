from fabric.api import *

import subprocess

def hello():
    print("Hello world!")
    #cmd_line = "redis-server"
    #p = subprocess.Popen(cmd_line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    #out = p.communicate()[0]
    
    # Start central Redis
    cmd_line = "redis-server"
    p = subprocess.Popen(cmd_line, shell=True)

    # Start local Redis
    cmd_line = "echo 'port 6389' | redis-server -"
    p = subprocess.Popen(cmd_line, shell=True)

    # Start Yeoman
    cmd_line = "yeoman server"
    p = subprocess.Popen(cmd_line, shell=True,
                         cwd="/Users/scottyoung/projects/parallelspider/spiderweb")

    # Start Spider Server
    cmd_line = "python spiderserver.py"
    p = subprocess.Popen(cmd_line, shell=True,
                         cwd="/Users/scottyoung/projects/parallelspider/spiderserver")

    # Start Spider Client
    cmd_line = "python spiderclient.py"
    p = subprocess.Popen(cmd_line, shell=True,
                         cwd="/Users/scottyoung/projects/parallelspider/parallelspider")

    # Start testacular
    with lcd("~/projects/parallelspider/spiderweb/"):
        local("testacular start")

def develop(type_name):
    if type_name == "mockremote":
        start_redis("local_1")
        start_redis("local_2")

@parallel
def start_redis(location):
    if location == "local_1":
        print('starting local redis on port 6379')
        local("redis-server")

    elif location == "local_2":
        print('starting local redis on port 6389')

  
