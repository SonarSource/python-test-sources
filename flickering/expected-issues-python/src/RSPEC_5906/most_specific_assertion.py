import unittest


def foo():
    return 42


def bar():
    return 24


class MyTestCase(unittest.TestCase):

    def test_equal(self):
        x = foo()
        y = bar()

        self.assertTrue(x == y)  # Noncompliant
        self.assertTrue(x != y)  # Noncompliant

        self.assertFalse(x == y)  # Noncompliant
        self.assertFalse(x != y)  # Noncompliant

        self.assertEqual(x, y)  # OK

    def test_true(self):
        x = foo()
        self.assertEqual(x, True)  # Noncompliant
        self.assertEqual(x, False)  # Noncompliant

        self.assertNotEqual(x, True)  # Noncompliant
        self.assertNotEqual(x, False)  # Noncompliant

        self.assertTrue(x)  # OK

    def test_comparision(self):
        x = foo()
        y = bar()
        self.assertTrue(x > y)  # Noncompliant
        self.assertTrue(x < y)  # Noncompliant
        self.assertTrue(x >= y)  # Noncompliant
        self.assertTrue(x <= y)  # Noncompliant

        self.assertFalse(x > y)  # OK (might not be equivalent to self.assertLessEqual(x, y)

        self.assertGreater(x, y)  # OK

    def test_identity(self):
        x = foo()
        y = bar()
        self.assertTrue(x is y)  # Noncompliant
        self.assertTrue(x is not y)  # Noncompliant

        self.assertFalse(x is y)  # Noncompliant
        self.assertFalse(x is not y)  # Noncompliant

        self.assertIs(x, y)  # OK

    def test_in(self):
        x = foo()
        y = bar()
        self.assertTrue(x in y)  # Noncompliant
        self.assertTrue(x not in y)  # Noncompliant

        self.assertFalse(x in y)  # Noncompliant
        self.assertFalse(x not in y)  # Noncompliant

        self.assertIn(x, y)  # OK

    def test_isInstance(self):
        x = foo()
        y = bar()
        self.assertTrue(isinstance(x, y))  # Noncompliant
        self.assertFalse(isinstance(x, y))  # Noncompliant

        self.assertIsInstance(x, y)  # OK

    def test_almost_equal(self):
        x = foo()
        y = bar()
        z = 1
        self.assertEqual(x, round(y, z))  # Noncompliant
        self.assertAlmostEqual(x, round(y, z))  # Noncompliant
        self.assertNotEqual(x, round(y, z))  # Noncompliant
        self.assertNotAlmostEqual(x, round(y, z))  # Noncompliant

        self.assertAlmostEqual(x, y)  # OK
        self.assertAlmostEqual(x, y, z)  # OK

    def test_none(self):
        x = 1
        self.assertTrue(x is None)  # Noncompliant
        self.assertTrue(x is not None)  # Noncompliant

        self.assertFalse(x is None)  # Noncompliant
        self.assertFalse(x is not None)  # Noncompliant

        self.assertIsNone(x)  # OK
