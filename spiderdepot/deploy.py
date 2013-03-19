""" Parallel Spider development tasks. """

import fabric.api as fab

import os
import subprocess


@fab.task
def test(word=None):
    
    import server
    server.start('local')

