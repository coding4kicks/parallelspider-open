""" Parallel Spider analysis engine tasks. """

import fabric.api as fab

import os
import sys
import signal
import threading
import subprocess

# Determine path to parallelspider directory.
# Assumes this file is in spiderdepot or subdirectory,
# and spiderdepot is 1 level below parallelspider.
path = os.path.realpath(__file__).partition('spiderdepot')[0]

@fab.task
def launch_new_scratch():
    """Start a spider engine from scratch, not an AMI."""

    # Initial commands must be synchronous
    # Use basecluster template
    ###cmd = 'starcluster start -c basecluster basecluster'
    ###p = subprocess.call(cmd, shell=True)
    ###if p != 0:
    ###    print "Starcluster failed to start."
    ###    sys.exit(1)

    # Create list of nodes
    instance_list = []
    nodes = 1
    i = 1;
    while i <= nodes:
        if i < 10:
            node_name = 'node00' + str(i)
        elif i < 100:
            node_name = 'node0' + str(i)
        elif i < 1000:
            node_name = 'node' + str(i)
        else:
            print "Too many nodes dumbass."
            sys.exit(1)
        instance_list.append(node_name)
        i += 1

    # Launch master and nodes
    t = threading.Thread(target=init_config, args=('master', 'master'))
    t.start()
    for instance in instance_list:
        t = threading.Thread(target=init_config, args=('node', instance))
        t.start()
    #print instance_list

def init_config(instance_type=None, instance=None):
    print 'here'
    cmd_list = [
            'sudo apt-get update',
            'sudo apt-get install --yes --force-yes libxml2-dev libxslt1-dev',
            'sudo pip install lxml',
            'sudo pip install beautifulsoup4',
            'sudo pip install cssselect',
            'sudo pip install redis',
            'sudo pip install boto'
            'git clone https://coding4kicks:\!6Graham9@github.com/' + \
            'coding4kicks/parallelspider.git /home/spideradmin/parallelspider'
            ]
    for cmd in cmd_list:
        if instance_type == 'master':
            full_cmd = 'starcluster sshmaster basecluster ' + cmd
        elif instance_type == 'node':
            full_cmd = 'starcluster sshnode basecluster node001 ' + cmd
        else:
            print('Error: Unknown Instance Type')
            sys.exit(1)
        p = subprocess.call(full_cmd, shell=True)
        if p != 0:
            print 'Command failed: ' + cmd
            print 'For instance: ' + instance
            sys.exit(1)
        print 'Command: ' + cmd + ' executed on ' + instance + '.'

    # upload bash
    full_cmd = 'starcluster put basecluster --node ' + instance + \
            '~/projects/bash_profiles/.bashrc-spiderengine /root/.bash_aliases'
    p = subprocess.call(full_cmd, shell=True)
    if p != 0:
        print 'Command failed: upload bashrc'
        print 'For instance: ' + instance
        sys.exit(1)

    # install redis only on master
    cmd_list = [
     'wget -P /home/spideradmin/ http://redis.googlecode.com/files/' + \
             'redis-2.6.11.tar.gz',
     'tar xzf /home/spideradmin/redis-2.6.11.tar.gz -C /home/spideradmin',
     'make -C /home/spideradmin/redis-2.6.11' 
            ]
    if instance_type == 'master'
        for cmd in cmd_list:
            full_cmd = 'starcluster sshmaster basecluster ' + cmd
            p = subprocess.call(full_cmd, shell=True)
            if p != 0:
                print 'Command failed: ' + cmd
                print 'For instance: ' + instance
                sys.exit(1)
            print 'Command: ' + cmd + ' executed on ' + instance + '.'



@fab.task
def start(type='local', args=None):
    """Start an analysis engine."""

    # Start Spider Engine on localhost (only a mock client)
    # Must have Redis running (Central and Engine) to start
    if type == 'local':

        # Assumes spiderengine is 1 level below parallelspider,
        # and spiderclient.py is in spiderengine
        cmd_line = "python spiderclient.py -m"
        cwd= path + "spiderengine"
        p = subprocess.Popen(cmd_line, shell=True, cwd=cwd)

@fab.task
def stop(type='local', args=None):
    """Stop an analysis engine."""

    # Stop Spider Engine on localhost
    if type == 'local':

        # Get a list of all processes
        p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
        out, err = p.communicate()

        # Kill any process with spiderclient in the name
        for line in out.splitlines():
            if 'spiderclient' in line:
                pid = int(line.split(None, 1)[0])
                os.kill(pid, signal.SIGKILL)

@fab.task
def restart(type='local', args=None):
    """Restart an analysis engine."""

    # Restart Spider Engine on localhost
    if type == 'local':
        stop()
        start()

@fab.task
def deploy():
    """Push spider engine components to cluster"""

    cwd = path + "spiderengine/"
    files = ['spiderclient.py', 'parallelspider.py',
             'mrfeynman.py', 'spidercleaner.py', 'mock_crawl.py']
    for f in files:
        cmd_line = ("starcluster put basecluster "
                    "~/projects/parallelspider/spiderengine/{} "
                    "/home/spideradmin/parallelspider/spiderengine/"
                    ).format(f)
        p = subprocess.Popen(cmd_line, shell=True, cwd=cwd)


@fab.task
def deploy_tests():
    """Push spider engine components to cluster"""

    cwd = path + "spiderengine/"
    files = ['test_crawl.py', 'test_cleaner.py']
    for f in files:
        cmd_line = ("starcluster put basecluster "
                "~/projects/parallelspider/spiderengine/"
                "tests/e2e-tests/{} "
                "/home/spideradmin/parallelspider/spiderengine/"
                "tests/e2e-tests/").format(f)
        p = subprocess.Popen(cmd_line, shell=True, cwd=cwd)

@fab.task
def deploy_production():
    """Push to spiderengine cluster"""

    # Use Starcluster to push up client, runner, spider, and feynman
    cwd = path + "spiderengine/"
    cmd_line = "starcluster put spiderengine " + \
               "~/projects/parallelspider/spiderengine/spiderclient.py " + \
               "/home/parallelspider/parallelspider/spiderengine/"
    p = subprocess.Popen(cmd_line, shell=True, cwd=cwd)
    cmd_line = "starcluster put spiderengine " + \
               "~/projects/parallelspider/spiderengine/spiderrunner.py " + \
               "/home/parallelspider/parallelspider/spiderengine/"
    p = subprocess.Popen(cmd_line, shell=True, cwd=cwd)
    cmd_line = "starcluster put spiderengine " + \
               "~/projects/parallelspider/spiderengine/parallelspider.py " + \
               "/home/parallelspider/parallelspider/spiderengine/"
    p = subprocess.Popen(cmd_line, shell=True, cwd=cwd)
    cmd_line = "starcluster put spiderengine " + \
               "~/projects/parallelspider/spiderengine/mrfeynman.py " + \
               "/home/parallelspider/parallelspider/spiderengine/"
    p = subprocess.Popen(cmd_line, shell=True, cwd=cwd)
    cmd_line = "starcluster put spiderengine " + \
               "~/projects/parallelspider/spiderengine/mock_crawl.py " + \
               "/home/parallelspider/parallelspider/spiderengine/"
    p = subprocess.Popen(cmd_line, shell=True, cwd=cwd)
    cmd_line = "starcluster put spiderengine " + \
               "~/projects/parallelspider/spiderengine/spidercleaner.py " + \
               "/home/parallelspider/parallelspider/spiderengine/"
    p = subprocess.Popen(cmd_line, shell=True, cwd=cwd)

@fab.task
def restart_datanodes():
    """Restart datanodes on all slaves."""
    total_nodes = 9
    remote_cmd = '/etc/init.d/hadoop-0.20-datanode restart'
    execute_remote(total_nodes, remote_cmd)

@fab.task
def delete_hadoop_logs():
    """Clear out all hadoop logs"""
    total_nodes = 9
    remote_cmd = 'rm -rf /usr/lib/hadoop-0.20/logs/*'
    execute_remote(total_nodes, remote_cmd)

@fab.task
def delete_hadoop_conf_files():
    """Clear out all hadoop logs"""
    total_nodes = 9
    remote_cmd = 'rm /usr/lib/hadoop-0.20/conf/slaves'
    execute_remote(total_nodes, remote_cmd)
    remote_cmd = 'rm /usr/lib/hadoop-0.20/conf/masters'
    execute_remote(total_nodes, remote_cmd)

def execute_remote(total_nodes, remote_cmd):
    """Execute command on all remote nodes"""
    node_num = 1
    while node_num <= total_nodes:
        if node_num < 10:
            node_name = 'node00' + str(node_num)
        elif node_num < 100:
            node_name = 'node0' + str(node_num)
        elif node_num < 1000:
            node_name = 'node' + str(node_num)
        else:
            print "Too many nodes dumbass."
        node_num += 1
        cmd = ("starcluster sshnode spiderengine {0} '{1}'"
               ).format(node_name, remote_cmd)
        p = subprocess.Popen(cmd, shell=True)






