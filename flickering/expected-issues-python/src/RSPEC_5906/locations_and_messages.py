import unittest


class MyTestCase(unittest.TestCase):

    def test_equal(self):
        x = 1
        y = 2
        z = 3

        self.assertTrue(x == y)  # Noncompliant {{Consider using "assertEqual" instead.}}
#       ^^^^^^^^^^^^^^^ ^^^^^^<

        self.assertAlmostEqual(x, round(y, z))  # Noncompliant {{Consider using the "places" argument of assertAlmostEqual instead.}}
#       ^^^^^^^^^^^^^^^^^^^^^^>   ^^^^^^^^^^^
