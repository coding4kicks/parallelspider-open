#Parallel Spider
###  Analyze the world
Parallel Spider is a tool for external website and comparisons. It is comprised of various components that allow a non-technical user to initiate a crawl of a website, analyze all the textual information in various ways, and see the end results, all over HTTP through a browser.  The three major componets are Spider Web, the front end client for interacting with the system; Spider Engine, the Hadoop analysis engine that downloads and analyzes websites; and Spider Server, the glue the holds the two together.

## Components

* Spider Web

An Angular based front-end for interacting with the system over HTTP with a browser.

* Spider Engine

A Starcluster running MapReduce scripts on Hadoop using Dumbo and Python.

* Spider Server

A Twisted instance connecting the web to the engine, along with maintaining session and user info.

* Spider Depot

Fabric scripts for development, deployment, and testing.

* Spider Data

Datastore configuration files.

* Spider Tools

Miscellaneous tools for the system.
