import unittest


class MyTest(unittest.TestCase):

    def test_something(self): ...  # OK

    def something_test(self): ...  # Noncompliant {{Rename this method so that it starts with "test" or remove this unused helper.}}
#       ^^^^^^^^^^^^^^
