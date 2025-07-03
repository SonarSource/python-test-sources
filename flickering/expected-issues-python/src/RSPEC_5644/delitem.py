################################################################################
# Case to cover: Detect when builtin types listed here
# https://docs.python.org/3/reference/datamodel.html#the-standard-type-hierarchy
# have __delitem__ called but this method is not defined.
################################################################################

#
# Builtin types supporting __delitem__
#
mylist = ['a', 'b']
del mylist[0]

mydict = {'a': 1, 'b': 2}
del mydict['a']

del bytearray(b"test")[1]

# list and dict Comprehension
del [nb for nb in range(5)][0]
del {nb: 'a' for nb in range(4)}[0]


#
# Builtin types NOT supporting __delitem__
#

# dictviews https://docs.python.org/3/library/stdtypes.html#dictionary-view-objects
del mydict.keys()[0]  # Noncompliant
del mydict.values()[0]  # Noncompliant
del mydict.items()[0]  # Noncompliant

# iterators
del iter(mylist)[0]  # Noncompliant

# Numeric types
from fractions import Fraction
from decimal import Decimal
del 1[0]  # Noncompliant
del 1.0[0]  # Noncompliant
del complex(1,1)[0]  # Noncompliant
del Fraction(1,1)[0]  # Noncompliant
del Decimal(1)[0]  # Noncompliant
del True[0]  # Noncompliant

del {1}[0]  # Noncompliant. Set
del frozenset({1})[0]  # Noncompliant. frozenset

# set Comprehension
del {nb for nb in range(4)}[0]  # Noncompliant.

del range(10)[0]  # Noncompliant

var = None
del var[0]  # Noncompliant

del bytes(b'123')[0]  # Noncompliant
del memoryview(bytearray(b'abc'))[0]  # Noncompliant

del "abc"[0]  # Noncompliant. String
del (1, 2)[0]  # Noncompliant. Tuple

del NotImplemented[0]  # Noncompliant.

def function():
    pass

del function[0]  # Noncompliant

def generator():
    yield 1

del generator()[0]  # Noncompliant
del (nb for nb in range(5))[0]  # Noncompliant

async def async_function():
    pass

del async_function()[0]  # Noncompliant

async def async_generator():
    yield 1

del async_generator()[0]  # Noncompliant

# module
import math
del math[0]  # Noncompliant

# File
del open("foo.py")[0]  # Noncompliant

import os
del os.popen('ls')[0]  # Noncompliant


##################################################################
# Case to cover: Types which support __delitem__ ok include array.
# https://docs.python.org/3/library/array.html#module-array
##################################################################
from array import array
a = array('b', [0, 1, 2])
del a[0]


#######################################################################
# Case to cover: Types which support __delitem__ ok include collections
# except for Coord.
# https://docs.python.org/3/library/collections.html#module-collections
#######################################################################
from collections import namedtuple, deque, ChainMap, Counter, OrderedDict, defaultdict, UserDict, UserList, UserString

Coord = namedtuple('Coord', ['x', 'y'])
del Coord(x=1, y=1)[0]  # Noncompliant

del deque([0,1,2])[0]
del ChainMap({'a': 1})['a']
del Counter(['a', 'b'])['a']
del OrderedDict.fromkeys('abc')['a']
del defaultdict(int, {0:0})[0]


#####################################################################################
# Case to cover: Detect when a custom class which has no metaclass (see next section)
# has __delitem__ called but this method is not defined.
#####################################################################################


class A:
    def __init__(self, values):
        self._values = values

a = A([0,1,2])

del a[0]  # Noncompliant

class B:
    pass

B[0]  # Noncompliant


class C:
    def __init__(self, values):
        self._values = values

    def __delitem__(self, key):
        del self._values[key]

c = C([0,1,2])

del c[0]


###########################################################################
# Out of scope: detecting issues on Metaclasses or classes with metaclasses
###########################################################################

def delitem(self, key):
    print(f"deleting {key}")


class MyMetaClassWithDelete(type):
    def __new__(cls, name, bases, dct):
        instance = super().__new__(cls, name, bases, dct)
        instance.__delitem__ = delitem
        return instance

    def __delitem__(cls, key):
        print(f"deleting {key}")

class MetaclassedWithDelete(metaclass=MyMetaClassWithDelete):
    pass

del MetaclassedWithDelete[0]  # Ok
del MetaclassedWithDelete()[0]  # Ok. Pylint False Positive


class MyMetaClassWithoutDelete(type):
    pass

class MetaclassedWithoutDelete(metaclass=MyMetaClassWithoutDelete):
    pass

del MetaclassedWithoutDelete[0]  # False Negative
del MetaclassedWithoutDelete()[0]  # False Negative
