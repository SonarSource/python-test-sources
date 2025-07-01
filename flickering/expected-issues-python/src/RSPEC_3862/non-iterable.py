##################################################################
# Case to cover: Detect every kind of iteration on a non-iterable.
##################################################################
def every_kind_of_iteration():
    iterable = ['a', 'b', 'c']
    not_an_iterable = 42
    # unpacking arguments
    print(*iterable)
    print(*not_an_iterable)  # Noncompliant

    # for-in loop
    for a in iterable:
        print(a)

    for a in not_an_iterable:  # Noncompliant
        print(a)

    # comprehensions
    a, *rest = [a for a in iterable]
    a, *rest = {a for a in iterable}
    a, *rest = {a: a for a in iterable}


    a, *rest = [a for a in not_an_iterable]  # Noncompliant
    a, *rest = {a for a in not_an_iterable}  # Noncompliant
    a, *rest = {a: a for a in not_an_iterable}  # Noncompliant

    # yield from
    def yield_from():
        yield from iterable
        yield from not_an_iterable  # Noncompliant


##########################################################################
# Case to cover: Detect when non-iterable builtin types are iterated over.
##########################################################################
def builtins():
    iterable = ['a', 'b', 'c']
    mydict = {"a": 1, "b": 2}

    # unpacking
    a, *rest = iterable
    a, *rest = iter(iterable)
    a, *rest = set(iterable)
    a, *rest = frozenset(iterable)
    a, *rest = iterable
    a, *rest = "abc"
    a, *rest = f"abc"
    a, *rest = u"abc"
    a, *rest = b"abc"
    a, *rest = bytes(b"abc")
    a, *rest = bytearray(b"abc")
    a, *rest = memoryview(b"abc")
    a, *rest = mydict.keys()
    a, *rest = mydict.values()
    a, *rest = mydict.items()
    a, *rest = range(10)


    # Numeric types
    from fractions import Fraction
    from decimal import Decimal
    a, *rest = 1  # Noncompliant
    a, *rest = 1.0  # Noncompliant
    a, *rest = complex(1,1)  # Noncompliant
    a, *rest = Fraction(1,1)  # Noncompliant
    a, *rest = Decimal(1)  # Noncompliant
    a, *rest = True  # Noncompliant
    a, *rest = None  # Noncompliant
    a, *rest = NotImplemented  # Noncompliant

    def function():
        pass

    a, *rest = function  # Noncompliant

    # generators
    def generator():
        yield 1

    a, *rest = generator()
    a, *rest = generator  # Noncompliant


#############################################################################################
# Out of scope: We won't raise issues when non-iterable are used in a "dictionary unpacking",
# i.e. two stars (**). This should later be covered by a dedicated rule.
#############################################################################################

def dict_unpacking():
    not_a_dict = 42
    dict(**not_a_dict)  # Out of scope

###########################################################################
# Case to cover: Detect when non-iterable custom classes are iterated over.
###########################################################################
def custom_types():
    class NewStyleIterable:
        li = [1,2,3]

        def __iter__(self):
            return iter(self.__class__.li)

    class OldStyleIterable:
        li = [1,2,3]

        def __getitem__(self, key):
            return self.__class__.li[key]


    a, *rest = NewStyleIterable()
    a, *rest = OldStyleIterable()
    a, *rest = NewStyleIterable  # Noncompliant
    a, *rest = OldStyleIterable  # Noncompliant

    class Empty():
        pass

    a, *rest = Empty()  # Noncompliant

    class NonIterableClass:
        li = [1,2,3]

        def __class_getitem__(cls, key):
            "__class_getitem__ does not make a class iterable"
            return cls.li[key]

    a, *rest = NonIterableClass  # Noncompliant


    # Inheritance
    # same for list, dict, set, ...
    class customTuple(tuple):
        pass

    a, *rest = customTuple([1,2,3])

##############################################################################
# Case to cover: Detect when Coroutines and Async generators are iterated over
# without the "async" keyword.
##############################################################################

def async_iteration():
    async def async_function():
        pass

    a, *rest = async_function()  # Noncompliant
    a, *rest = async_function  # Noncompliant

    async def async_generator():
        yield 1

    a, *rest = async_generator()  # Noncompliant
    for a in async_generator():  # Noncompliant
        print(a)

    async for a in async_generator():
        print(a)

    class AsyncIterable:
        def __aiter__(self):
            return AsyncIterator()

    class AsyncIterator:
        def __init__(self):
            self.start = True

        async def __anext__(self):
            if self.start:
                self.start = False
                return 42
            raise StopAsyncIteration

    async for a in AsyncIterable():
        print(a)

    for a in AsyncIterable():  # Noncompliant
        print(a)


########################################################################
# Out of scope: check if custom classes having a metaclass are iterable.
#
# We don't know if the Metaclass added the required methods.
# This is expected to be a rare use case so it has a low priority.
# Example: https://github.com/tensorflow/probability/blob/7e4e3a17482f6150a4b9d9c0e2bec88fd0d51243/tensorflow_probability/python/util/deferred_tensor.py#L84
########################################################################
def metaclasses():
    class MyMetaClassWithouIter(type):
        pass

    class MetaclassedNonIterable(metaclass=MyMetaClassWithouIter):
        pass

    a, *rest = MetaclassedNonIterable  # False Negative. Out of scope.
    a, *rest = MetaclassedNonIterable() # False Negative. Out of scope.

    def myiter(self):
        return iter(range(10))

    class MyMetaClassWithIter(type):
        def __new__(cls, name, bases, dct):
            instance = super().__new__(cls, name, bases, dct)
            instance.__iter__ = myiter
            return instance

    class MetaclassedIterable(metaclass=MyMetaClassWithIter):
        pass

    a, *rest = MetaclassedIterable() # Ok
    print(a)

#########################################################################################
# Out of scope: Detect when a non-iterable class and instance attribute is iterated over.
#########################################################################################
def attributes_and_properties():
    class MyContainer:
        def __init__(self):
            self._mylist = None
        
        @property
        def mylist(self):
            if not self._mylist:
                self._mylist = [1, 2, 3]
            return self._mylist

    a, *rest = MyContainer().mylist

    class AbstractClass():
        attribute_set_in_subclass = None

        def process(self):
            for a in self.attribute_set_in_subclass:  # False Negative. Out of scope as the attribute might be set in a subclass
                print(a)


#######################################################################################
# Out of scope: Detect when non-iterable are provided to functions expecting iterables.
#
# We definetely should detect this later.
#######################################################################################

def calling_iter_with_non_iterable():
    not_an_iterable = 42
    iter(not_an_iterable)  # False Negative for now


###################################################################
# Just for validation. Check that "array" does not raise any issue.
# https://docs.python.org/3/library/array.html#module-array
###################################################################
from array import array

def array_works():
    a, *rest = array('b', [0, 1, 2])


#######################################################################
# Just for validation. Check that "collections" don't raise any issue.
# https://docs.python.org/3/library/collections.html#module-collections
#######################################################################

from collections import namedtuple, deque, ChainMap, Counter, OrderedDict, defaultdict, UserDict, UserList, UserString

def collections_works():
    Coord = namedtuple('Coord', ['x', 'y'])
    a, *rest = Coord(x=1, y=1)

    a, *rest = deque([0,1,2])
    a, *rest = ChainMap({'a': 1})
    a, *rest = Counter(['a', 'b'])
    a, *rest = OrderedDict.fromkeys('abc')
    a, *rest = defaultdict(int, {0:0})
