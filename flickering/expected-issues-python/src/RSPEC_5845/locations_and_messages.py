import unittest


class MyTest(unittest.TestCase):

    def test_something(self):
        self.assertEqual(1, "1")  # Noncompliant {{Change this assertion's arguments to not compare incompatible types ("int" and "str").}}
#                        ^^^^^^
        x = 1
#       ^> {{Last assignment of "x".}}
        y = "1"
#       ^> {{Last assignment of "y".}}
        self.assertEqual(x, y)  # Noncompliant {{Change this assertion's arguments to not compare incompatible types ("int" and "str").}}
#                        ^^^^

        self.assertIs(x, y)  # # Noncompliant {{Change this assertion's arguments to not compare incompatible types ("int" and "str").}}
#                     ^^^^
