import unittest


class MyTest(unittest.TestCase):

    def test_comparison_builtins(self):
        x = 1
        y = "1"
        self.assertEqual(x, y)  # Noncompliant
        self.assertNotEqual(x, y)  # Noncompliant
        self.assertIs(x, y)  # Noncompliant
        self.assertIsNot(x, y)  # Noncompliant

        self.assertEqual(x, None)  # comparison to None are out of scope


#########
# Classes
#########
class A: ...


class SubA(A): ...


class B: ...


class EQ:
    def __eq__(self, other):
        return True


class Ne:
    def __ne__(self, other):
        return True


class TestClasses(unittest.TestCase):

    def test_classes_and_builtins(self):
        self.assertEqual(A(), 1)  # Noncompliant
        self.assertNotEqual(A(), 1)  # Noncompliant

        self.assertEqual(Ne(), 1)  # Noncompliant. Always False. "__eq__" does not call "__ne__" by default
        self.assertEqual(1, Ne())  # Noncompliant
        self.assertNotEqual(Ne(), 1)  # OK
        self.assertNotEqual(1, Ne())  # OK

    def test_comparing_classes(self):
        self.assertEqual(A(), B())  # Noncompliant

        # The default implementation of __eq__ checks object identity. Thus comparing
        # objects of exactly the same type is a valid operation even when __eq__ is not overloaded.
        self.assertEqual(A(), SubA())  # Always false but no issue raised because operands' classes are related

        # operations on class overloading __eq__ will raise no issue as it could be either true or false
        self.assertEqual(EQ(), A())  # No issue. Might be True or False
        self.assertEqual(A(), EQ())  # No issue. Might be True or False


class TestCollections(unittest.TestCase):

    def test_comparing_collections(self):
        from collections import namedtuple, deque, ChainMap, Counter, OrderedDict, defaultdict

        my_list = [1, 2, 3]
        my_set = {1, 2, 3}

        self.assertEqual(my_list, my_set)  # Noncompliant
        self.assertEqual([nb for nb in range(5)], my_set)  # Noncompliant
        self.assertEqual({nb: "a" for nb in range(5)}, my_list)  # Noncompliant
        self.assertEqual(iter(my_list), my_list)  # Noncompliant

        coord = namedtuple('Coord', ['x', 'y'])
        self.assertEqual(coord(x=1, y=1), my_list)  # Noncompliant
        self.assertEqual(deque([1, 2, 3]), my_list)  # Noncompliant
        self.assertEqual(ChainMap({'a': 1}), my_list)  # Noncompliant
        self.assertEqual(Counter([0, 1, 3]), my_list)  # Noncompliant
        self.assertEqual(OrderedDict.fromkeys('abc'), my_list)  # Noncompliant
        self.assertEqual(defaultdict(int, {0, 0}), my_list)  # Noncompliant

        self.assertEqual(ChainMap({'a': 1}), {'a': 1})  # OK
        self.assertEqual(Counter([0, 1, 2]), {0: 1, 1: 1, 2: 1})  # OK
        self.assertEqual(defaultdict(int, {0: 0}), {0: 0})  # OK
        self.assertEqual(OrderedDict.fromkeys('abc'), dict(a=None, b=None, c=None))  # OK
        self.assertEqual(coord(x=1, y=1), (1, 1))  # OK
