#!/usr/bin/env python

"""
test_cleaner.py - an e2e test for Spider Cleaner 

Uploads saved Parallel Spider results to HDFS.
Calls Spider Cleaner to process the results.
Compares these results to one's previously saved.
"""

import os
import sys
import subprocess

def clean_tester():
    """e2e test for Spider Cleaner."""
    result = _upload_test_file()

###############################################################################
### Helper Delper Classes & Functions
###############################################################################
def _upload_test_file():
    """Uploads the test file to HDFS"""
    command = ('dumbo put {} {} -hadoop starcluster').format(
                    _test_file_path(), _hdfs_path())
    result = subprocess.call(command, shell=True)
    return result

#def _put_command():
#    """Returns the command to upload the test files to HDFS."""
#    command = ('dumbo put {} {} -hadoop starcluster').format(
#                    _hdfs_path(), _test_file_path())
#    return command

def _hdfs_path():
    """Return test file directory on hdfs."""
    return '/HDFS/parallelspider/test/' + _test_file()

def _test_file_path():
    """Return the full path to the test file."""
    return _test_dir() + '/testfiles/' + _test_file()

def _result_file_path():
    """Return the full path to the results file."""
    return _test_dir() + '/testresults/' + _results_file()

def _test_file():
    """Return the test file name."""
    return "ps-results"

def _results_file():
    """Return the test file name."""
    return "clean-results"

def _test_dir():
    """Return directory containing test results"""
    return os.path.realpath(__file__).rpartition('/')[0]

if __name__ == "__main__":
    sys.exit(clean_tester())

