""" Parallel Spider development tasks. """

import fabric.api as fab

import os
import subprocess


@fab.task
def web(word=None):
    """Build and deploy web client."""
    
    import web
    web.build()
    web.deploy()

