################################################################################
# Case to cover: Detect when builtin types listed here
# https://docs.python.org/3/reference/datamodel.html#the-standard-type-hierarchy
# have __setitem__ called but this method is not defined.
################################################################################

#
# Builtin types supporting __setitem__
#
mylist = ['a', 'b']
mylist[0] = 42

mydict = {'a': 1, 'b': 2}
mydict['a'] = 42

bytearray(b"test")[1] = 42

# list and dict Comprehension
[nb for nb in range(5)][0] = 42
{nb: 'a' for nb in range(4)}[0] = 42


# No issue raised on memoryview even when the memory is read-only
memoryview(bytearray(b'abc'))[0] = 42
memoryview(bytes(b'abc'))[0] = 42  # This will fail because bytes is read-only but we don't raise any issue


#
# Builtin types NOT supporting __setitem__
#

# dictviews https://docs.python.org/3/library/stdtypes.html#dictionary-view-objects
mydict.keys()[0] = 42  # Noncompliant
mydict.values()[0] = 42  # Noncompliant
mydict.items()[0] = 42  # Noncompliant

# iterators
iter(mylist)[0] = 42  # Noncompliant

# Numeric types
from fractions import Fraction
from decimal import Decimal
1[0] = 42  # Noncompliant
1.0[0] = 42  # Noncompliant
complex(1,1)[0] = 42  # Noncompliant
Fraction(1,1)[0] = 42  # Noncompliant
Decimal(1)[0] = 42  # Noncompliant
True[0] = 42  # Noncompliant

{1}[0] = 42  # Noncompliant. Set
frozenset({1})[0] = 42  # Noncompliant. frozenset

# set Comprehension
{nb for nb in range(4)}[0] = 42 # Noncompliant.

range(10)[0] = 42  # Noncompliant

var = None
var[0] = 42  # Noncompliant

bytes(b'123')[0] = 42  # Noncompliant

"abc"[0] = 42  # Noncompliant. String
(1, 2)[0] = 42 # Noncompliant. Tuple

NotImplemented[0] = 42  # Noncompliant.

def function():
    pass

function[0] = 42  # Noncompliant

def generator():
    yield 1

generator()[0] = 42  # Noncompliant
(nb for nb in range(5))[0] = 42  # Noncompliant

async def async_function():
    pass

async_function()[0] = 42  # Noncompliant

async def async_generator():
    yield 1

async_generator()[0] = 42  # Noncompliant

# module
import math
math[0] = 42  # Noncompliant

# File
open("foo.py")[0] = 42  # Noncompliant

import os
os.popen('ls')[0] = 42  # Noncompliant


##################################################################
# Case to cover: Types which support __setitem__ ok include array.
# https://docs.python.org/3/library/array.html#module-array
##################################################################
from array import array
a = array('b', [0, 1, 2])
a[0] = 42


#######################################################################
# Case to cover: Types which support __setitem__ ok include collections
# except for Coord.
# https://docs.python.org/3/library/collections.html#module-collections
#######################################################################
from collections import namedtuple, deque, ChainMap, Counter, OrderedDict, defaultdict, UserDict, UserList, UserString

Coord = namedtuple('Coord', ['x', 'y'])
Coord(x=1, y=1)[0] = 42 # Noncompliant

deque([0,1,2])[0] = 42
ChainMap({'a': 1})['a'] = 42
Counter(['a', 'b'])['a'] = 42
OrderedDict.fromkeys('abc')['a'] = 42
defaultdict(int, {0:0})[0] = 42


#####################################################################################
# Case to cover: Detect when a custom class which has no metaclass (see next section)
# has __setitem__ called but this method is not defined.
#####################################################################################

class A:
    def __init__(self, values):
        self._values = values

a = A([0,1,2])

a[0] = 42  # Noncompliant

class B:
    pass

B[0]  # Noncompliant


class C:
    def __init__(self, values):
        self._values = values

    def __setitem__(self, key, value):
        self._values[key] = value

c = C([0,1,2])

c[0] = 42


###########################################################################
# Out of scope: detecting issues on Metaclasses or classes with metaclasses
###########################################################################

def setitem(self, key, value):
    print(f"setting {key}")


class MyMetaClassWithSet(type):
    def __new__(cls, name, bases, dct):
        instance = super().__new__(cls, name, bases, dct)
        instance.__setitem__ = setitem
        return instance

    def __setitem__(cls, key, value):
        print(f"setting {key}")

class MetaclassedWithSet(metaclass=MyMetaClassWithSet):
    pass

MetaclassedWithSet[0] = 42  # Ok
MetaclassedWithSet()[0] = 42  # Ok. Pylint False Positive


class MyMetaClassWithoutSet(type):
    pass

class MetaclassedWithoutSet(metaclass=MyMetaClassWithoutSet):
    pass

MetaclassedWithoutSet[0] = 42  # False Negative
MetaclassedWithoutSet()[0] = 42  # False Negative