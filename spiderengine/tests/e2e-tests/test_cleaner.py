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

    # Setup
    result = _upload_test_file()
    if result != 0:
        print("Problem uploading test file to HDFS.")
        sys.exit(1)

    # Call Spider Cleaner

    # Verify Results

    # Cleanup
    result = _remove_test_file()
    if result != 0:
        print("Problem removing test file from HDFS.")
        sys.exit(1)


###############################################################################
### Helper Delper Classes & Functions
###############################################################################
def _upload_test_file():
    """Uploads the test file to HDFS"""
    command = ('dumbo put {} {} -hadoop starcluster').format(
                    _test_file_path(), _hdfs_path())
    result = subprocess.call(command, shell=True)
    return result

def _cleanup_command(self, crawl_id):
    """Construct command to run Spider Cleaner."""
    cmd_line = ("python spidercleaner.py -r host:{},port:{} -c {}"
               ).format(self.engine_redis_host,
                        self.engine_redis_port, crawl_id)
    if self.psuedo_dist:
        cmd_line += " -d"
    return cmd_line

def _remove_test_file():
    """Uploads the test file to HDFS"""
    command = ('dumbo rm {} -hadoop starcluster').format(_hdfs_path())
    result = subprocess.call(command, shell=True)
    return result

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

