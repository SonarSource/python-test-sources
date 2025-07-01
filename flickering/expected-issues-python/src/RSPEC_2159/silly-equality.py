##########
# Builtins
##########


def comparing_builtins():
    s = ""
    i = 1

    if s == i:
        print("invalid")

#########
# Classes
#########
class A:
    pass

class SubA(A):
    pass

class B:
    pass

class EQ:
    def __eq__(self, other):
        return True

class Ne:
    def __ne__(self, other):
        return True

def comparing_classes():
    result = A() == B()  # Noncompliant. Always False

    # The default implementation of __eq__ checks object identity. Thus comparing
    # objects of exactly the same type is a valid operation even when __eq__ is not overloaded.
    a = A()
    sub = SubA()
    if a == sub:  # Always false but no issue raised because operands' classes are related
        pass

    # operations on class overloading __eq__ will raise no issue as it could be either true or false
    if EQ() == A():  # No issue. Might be True or False
        pass
    if A() == EQ():  # No issue. Might be True or False
        pass

    myvar = Ne() == 1  # Noncompliant. Always False. "__eq__" does not call "__ne__" by default
    myvar = 1 == Ne()  # Noncompliant. Always False.
    myvar = Ne() != 1  # Ok
    myvar = 1 != Ne()  # Ok

#############
# Metaclasses
#############

class MyMetaClass(type):
    def __eq__(cls, key):
        return True

class Metaclassed(metaclass=MyMetaClass):
    pass

def test_metaclasses():
    myint = 1
    myint == Metaclassed
    myint == Metaclassed()  # Noncompliant

###############
# Builtin Types
###############

def builtin_types():
    myint = 1
    mystr = ""

    mylist = ['a', 'b']
    myint == mylist  # Noncompliant

    mydict = {'a': 1, 'b': 2}
    myint == mydict  # Noncompliant

    myint == bytearray(b"test")  # Noncompliant

    # list and dict Comprehension
    myint == [nb for nb in range(5)][0]  # Noncompliant
    myint == {nb: 'a' for nb in range(4)}  # Noncompliant

    # dictviews https://docs.python.org/3/library/stdtypes.html#dictionary-view-objects
    myint == mydict.keys()  # Noncompliant
    myint == mydict.values()  # Noncompliant
    myint == mydict.items()  # Noncompliant

    # iterators
    myint == iter(mylist)  # Noncompliant

    # Numeric types
    from fractions import Fraction
    from decimal import Decimal
    mystr == 1  # Noncompliant
    mystr == 1.0  # Noncompliant
    mystr == complex(1,1)  # Noncompliant
    mystr == Fraction(1,1)  # Noncompliant
    mystr == Decimal(1)  # Noncompliant
    mystr == True  # Noncompliant

    myint == {1}  # Noncompliant
    myint == frozenset({1})  # Noncompliant

    # set Comprehension
    myint == {nb for nb in range(4)}  # Noncompliant

    myint == range(10)  # Noncompliant

    myint == bytes(b'123')  # Noncompliant
    myint == memoryview(bytearray(b'abc'))  # Noncompliant

    myint == "abc"  # Noncompliant
    myint == (1, 2)  # Noncompliant

    myint == NotImplemented  # Noncompliant

    def function():
        pass

    myint == function  # Noncompliant

    def generator():
        yield 1

    myint == generator()  # Noncompliant
    myint == (nb for nb in range(5))  # Noncompliant

    # coroutine
    async def async_function():
        pass
    myint == async_function()  # Noncompliant

    # async_generator
    async def async_generator():
        yield 1
    myint == async_generator()  # Noncompliant

    # module
    import math
    myint == math  # Noncompliant

    # File
    myint == open("foo.py")  # Noncompliant

    # process
    import os
    myint == os.popen('ls')  # Noncompliant

#######
# array https://docs.python.org/3/library/array.html#module-array
#######
from array import array
def test_array():
    a = array('b', [0, 1, 2])
    1 == a  # Noncompliant
    array('b', [0, 1, 2]) == [0, 1, 2]  # Noncompliant

#############
# collections https://docs.python.org/3/library/collections.html#module-collections
#############
from collections import namedtuple, deque, ChainMap, Counter, OrderedDict, defaultdict, UserDict, UserList, UserString

def test_collections():
    Coord = namedtuple('Coord', ['x', 'y'])
    1 == Coord(x=1, y=1)  # Noncompliant

    1 == deque([0, 1, 2, 3])   # Noncompliant
    1 == ChainMap({'a': 1})  # Noncompliant
    1 == Counter([0,1,2])  # Noncompliant
    1 == OrderedDict.fromkeys('abc')  # Noncompliant
    1 == defaultdict(int, {0:0})  # Noncompliant

    deque([0, 1, 2, 3]) == [0, 1, 2, 3]  # Noncompliant

    # The following comparisons work
    ChainMap({'a': 1}) == {'a': 1}
    Counter([0,1,2]) == {0: 1, 1: 1, 2: 1}
    defaultdict(int, {0:0}) == {0:0}
    OrderedDict.fromkeys('abc') == dict(a=None, b=None, c=None)
    Coord(x=1, y=1) == (1,1)