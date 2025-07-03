import unittest


def external_resource_available(): return False


def foo(): return 42


class MyTest(unittest.TestCase):

    def test_something(self):
        if not external_resource_available():
            return  # Noncompliant {{Skip this test explicitly.}}
#           ^^^^^^
        else:
            self.assertEqual(foo(), 42)

    def test_with_skip(self):
        if not external_resource_available():
            self.skipTest("prerequisite not met")
        else:
            self.assertEqual(foo(), 42)
