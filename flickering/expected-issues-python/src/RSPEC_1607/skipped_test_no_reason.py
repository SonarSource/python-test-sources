import unittest

import pytest


class MyTest(unittest.TestCase):

    @unittest.skip  # Noncompliant
    def test_ignored_no_reason(self):
        self.assertEqual(1 / 0, 99)

    @unittest.skip("Fix math")  # OK
    def test_ignored_with_reason(self):
        self.assertEqual(1 / 0, 99)

    @unittest.skip("")  # Noncompliant
    def test_ignored_empty_reason(self):
        self.assertEqual(1 / 0, 99)

    def test_calls_skipTest_no_reason(self):
        self.skipTest()  # Noncompliant

    def test_calls_skipTest_with_reason(self):
        self.skipTest("a reason")  # OK

    def test_raises_unittest_SkipTest_no_reason(self):
        raise unittest.SkipTest()  # Noncompliant

    def test_raises_unittest_SkipTest_with_reason(self):
        raise unittest.SkipTest("a reason")


# Pytest

@pytest.mark.skip  # Noncompliant
def test_pytest_skip_no_reason():
    assert 1 == 2


@pytest.mark.skip("")  # Noncompliant
def test_pytest_skip_no_reason2():
    assert 1 == 2


@pytest.mark.skip("fix something")  # OK
def test_pytest_skip():
    assert 1 == 2


def func():
    return 42


def test_skipped():
    if func() == 41:
        pytest.skip()  # Noncompliant
    else:
        pytest.skip("a reason")  # OK
