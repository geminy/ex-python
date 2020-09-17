#!/usr/bin/env python

import types # decreases the called times of type() function
from types import IntType, LongType, FloatType, ComplexType # decreases the parsing times of types module

def displayNumType(num):
    'best: calls isinstance() function'
    print num, 'is',
    if isinstance(num, (int, long, float,complex)):
        print 'a number of type:', type(num).__name__
    else:
        print 'not a number at all!!'

def displayNumType2(num):
    'calls type() function'
    print num, 'is',
    if type(num) == type(0):
        print 'an integer'
    elif type(num) == type(0L):
        print 'a long'
    elif type(num) == type(0.0):
        print 'a float'
    elif type(num) == type(0 + 0j):
        print 'a complex number'
    else:
        print 'not a number at all!!'

def displayNumType3(num):
    'uses types module to decrease the called times of type() function'
    print num, 'is',
    if type(num) == types.IntType:
        print 'an integer'
    elif type(num) == types.LongType:
        print 'a long'
    elif type(num) == types.FloatType:
        print 'a float'
    elif type(num) == types.ComplexType:
        print 'a complex number'
    else:
        print 'not a number at all!!'

def displayNumType4(num):
    'import some types from types module to decrease the parsing times of types module'
    print num, 'is',
    if type(num) == IntType:
        print 'an integer'
    elif type(num) == LongType:
        print 'a long'
    elif type(num) == FloatType:
        print 'a float'
    elif type(num) == ComplexType:
        print 'a complex number'
    else:
        print 'not a number at all!!'

def displayNumType5(num):
    'replaces == with is'
    print num, 'is',
    if type(num) is IntType:
        print 'an integer'
    elif type(num) is LongType:
        print 'a long'
    elif type(num) is FloatType:
        print 'a float'
    elif type(num) is ComplexType:
        print 'a complex number'
    else:
        print 'not a number at all!!'

displayNumType(-69)
displayNumType(99999999999999999999L)
displayNumType(98.6)
displayNumType(-5.2 + 1.9j)
displayNumType('xxx')
print "----------1"
displayNumType2(-69)
displayNumType2(99999999999999999999L)
displayNumType2(98.6)
displayNumType2(-5.2 + 1.9j)
displayNumType2('xxx')
print "----------2"
displayNumType3(-69)
displayNumType3(99999999999999999999L)
displayNumType3(98.6)
displayNumType3(-5.2 + 1.9j)
displayNumType3('xxx')
print "----------3"
displayNumType4(-69)
displayNumType4(99999999999999999999L)
displayNumType4(98.6)
displayNumType4(-5.2 + 1.9j)
displayNumType4('xxx')
print "----------4"
displayNumType5(-69)
displayNumType5(99999999999999999999L)
displayNumType5(98.6)
displayNumType5(-5.2 + 1.9j)
displayNumType5('xxx')
print "----------5"
