#!/usr/bin/env python

from random import choice

class RandSeq(object):
    def __init__(self, seq):
        self.data = seq

    def __iter__(self):
        return self

    def next(self):
        return choice(self.data)

if __name__ == '__main__':
    for eachItem in RandSeq([1, 2, 3]):
        print eachItem
