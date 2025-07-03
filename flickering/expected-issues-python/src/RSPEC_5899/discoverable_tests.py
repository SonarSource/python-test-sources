import unittest


class MyTest(unittest.TestCase):

    def __init__(self): ...  # OK

    def setUp(self) -> None: ...  # OK (unittest.TestCase method)

    def my_helper_method(self): ...

    def test_something(self): ...  # OK

    def test_something_else(self):
        self.my_helper_method()
        ...

    def something_test(self):  # Noncompliant
        ...

    def testSomething(self): ...  # OK

    # test must be lowercase.
    def tesT_other(self): ...  # Noncompliant


class MyMixin(object):

    def test_something(self):
        self.assertEqual(self.some_helper(), 42)


class MyCustomTest(MyMixin, unittest.TestCase):
    """
    Classes subclassing other classes than unittest.TestCase might be mixins
    See: https://github.com/RMerl/asuswrt-merlin/blob/master/release/src/router/samba-3.6.x/lib/dnspython/tests/resolver.py
    """
    def some_helper(self):  # OK
        return 42


class MyParentTest(unittest.TestCase):
    """
    As classes subclassing unittest.TestCase will be executed as tests,
    they should define test methods and not be used as "abstract" parent helper
    We should watch out for FPs on Peach, though.
    """
    def some_helper(self):  # Noncompliant
        ...


class MyChildTest(MyParentTest):

    def test_something(self):
        self.some_helper()
        ...
