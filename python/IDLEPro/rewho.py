#!/usr/bin/env python

from os import popen
from re import split

f = popen('who', 'r')
for eachLine in f.readlines():
    print split('\s\s+|\t', eachLine.strip())
f.close()
