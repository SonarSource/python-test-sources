import unittest

class ConstantTrueFalseTests(unittest.TestCase):
    def test_constant_assert_true_with_literal(self):
        self.assertTrue(round)  # Noncompliant
        #               ^^^^^      Primary message. Replace this expression; its boolean value is constant.


class ConstantNoneTests(unittest.TestCase):
    def test_constant_assert_none(self):
        self.assertIsNone(round)  # Noncompliant. Always fails
        #    ^^^^^^^^^^^^^^^^^^^      Primary message. Remove this identity assertion; it will always fail.


class ConstantNewObjectTests(unittest.TestCase):
    def helper_constant_assert_new_objects(self, param):
        self.assertIs(param, [1, 2, 3])  # Noncompliant
        #    ^^^^^^^^                   Primary message. Replace this "assertIs" call with an "assertEqual" call.
        #                    ^^^^^^^^^  Secondary location. This expression creates a new object every time.
