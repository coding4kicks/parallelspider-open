#!/usr/bin/env python

""" 
Depot module for Parallel Spider 

Contains tools to develop, test, and deploy the system.
For ease of use set spider as alias in .bashrc.
Assumes boto is installed and AWS keys are in .bashrc.
Assumes Redis.
TODO: remove assumptions by automatically installing
all requirements with a build.depot command
"""

from fabric.api import *

import data
import deploy
import develop
import engine
import server
import web



  
