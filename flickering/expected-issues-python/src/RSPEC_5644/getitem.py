################################################################################
# Case to cover: Detect when builtin types listed here
# https://docs.python.org/3/reference/datamodel.html#the-standard-type-hierarchy
# have __getitem__ called but this method is not defined.
################################################################################

#
# Builtin types supporting __getitem__
#
mylist = ['a', 'b']
mylist[0]

mydict = {'a': 1, 'b': 2}
mydict['a']

bytearray(b"test")[1]

# list and dict Comprehension
[nb for nb in range(5)][0]
{nb: 'a' for nb in range(4)}[0]

range(10)[0]

bytes(b'123')[0]
memoryview(bytearray(b'abc'))[0]

"abc"[0]
(1, 2)[0]

#
# Builtin types NOT supporting __getitem__
#

# dictviews https://docs.python.org/3/library/stdtypes.html#dictionary-view-objects
mydict.keys()[0]  # Noncompliant
mydict.values()[0]  # Noncompliant
mydict.items()[0]  # Noncompliant

# iterators
iter(mylist)[0]  # Noncompliant

# Numeric types
from fractions import Fraction
from decimal import Decimal
1[0]  # Noncompliant
1.0[0]  # Noncompliant
complex(1,1)[0]  # Noncompliant
Fraction(1,1)[0]  # Noncompliant
Decimal(1)[0]  # Noncompliant
True[0]  # Noncompliant

{1}[0]  # Noncompliant. Set
frozenset({1})[0]  # Noncompliant. frozenset

# set Comprehension
{nb for nb in range(4)}[0]  # Noncompliant.

var = None
var[0]  # Noncompliant

NotImplemented[0]  # Noncompliant.

def function():
    pass

function[0]  # Noncompliant

def generator():
    yield 1

generator()[0]  # Noncompliant
(nb for nb in range(5))[0]  # Noncompliant

async def async_function():
    pass

async_function()[0]  # Noncompliant

async def async_generator():
    yield 1

async_generator()[0]  # Noncompliant

# module
import math
math[0]  # Noncompliant

# File
open("foo.py")[0]  # Noncompliant

import os
os.popen('ls')[0]  # Noncompliant


##################################################################
# Case to cover: Types which support __getitem__ ok include array.
# https://docs.python.org/3/library/array.html#module-array
##################################################################
from array import array
a = array('b', [0, 1, 2])
a[0]


########################################################################
# Case to cover: Types which support __getitem__ ok include collections.
# https://docs.python.org/3/library/collections.html#module-collections
########################################################################
from collections import namedtuple, deque, ChainMap, Counter, OrderedDict, defaultdict, UserDict, UserList, UserString

Coord = namedtuple('Coord', ['x', 'y'])
Coord(x=1, y=1)[0]

deque([0,1,2])[0]
ChainMap({'a': 1})['a']
Counter(['a', 'b'])['a']
OrderedDict.fromkeys('abc')['a']
defaultdict(int, {0:0})[0]


#####################################################################################
# Case to cover: Detect when a custom class which has no metaclass (see next section)
# has __getitem__ or __class_getitem__ called but these methods are not defined.
#####################################################################################

class A:
    def __init__(self, values):
        self._values = values

a = A([0,1,2])

a[0]  # Noncompliant

class B:
    pass

B[0]  # Noncompliant


class C:
    def __init__(self, values):
        self._values = values

    def __getitem__(self, key):
        return self._values[key]

c = C([0,1,2])

c[0]

class D:
    def __class_getitem__(cls, key):
        return [0, 1, 2, 3][key]

D[0]


###########################################################################
# Out of scope: detecting issues on Metaclasses or classes with metaclasses
###########################################################################

def getitem(self, key):
    print(f"getting {key}")


class MyMetaClassWithGet(type):
    def __new__(cls, name, bases, dct):
        instance = super().__new__(cls, name, bases, dct)
        instance.__getitem__ = getitem
        return instance

    def __getitem__(cls, key):
        print(f"getting {key}")

class MetaclassedWithGet(metaclass=MyMetaClassWithGet):
    pass

MetaclassedWithGet[0]  # Ok
MetaclassedWithGet()[0]  # Ok. Pylint False Positive


class MyMetaClassWithoutGet(type):
    pass

class MetaclassedWithoutGet(metaclass=MyMetaClassWithoutGet):
    pass

MetaclassedWithoutGet[0]  # False Negative
MetaclassedWithoutGet()[0]  # False Negative
