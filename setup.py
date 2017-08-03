#!/usr/bin/env python
#-*- coding: utf-8 -*-
import re, os
from setuptools import setup

descr = "A light-weight parsing toolkit written in pure Python."
longDescr = descr

if os.path.exists("README.rst"):
    longDescr = open("README.rst").read()

def version(*file_paths):
    f = open(*file_paths).read()
    m = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f, re.M)
    if m:
        return m.group(1)

    raise RuntimeError("Unable to find version string.")

setup(
    name = "pynetree",
    version = version("pynetree/pynetree.py"),

    author="Jan Max Meyer",
    author_email="info@pynetree.org",

    url = "http://pynetree.org",
    description=descr,
    long_description=longDescr,

    license="MIT",

    keywords="parsing parser parse packrat left-recursive ast syntax compiler",

    packages=["pynetree"],

    entry_points={
        "console_scripts": [
            "pynetree=pynetree:main"]}
)
