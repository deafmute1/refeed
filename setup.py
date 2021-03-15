#!/usr/bin/env python3

""" Currently, refeed is not packaged.
    Correct install method is to `git clone` or `wget <RELEASE>.tar.gz` to /opt or some other place. 
    As this is server software, this is the distribution method for the foreseeable future. 

    This setuptools file is intended to provided extremely basic packaging for development (pytest) ONLY,
    For use with pip install -e . from within a venv. 
"""
# 3RD PARTY 
from setuptools import setup, find_packages # (included with pip package) 

setup(name="refeed", packages=find_packages())

