import unittest

import pytest


def foo(): return 1 / 0


def bar(): return 42


# To avoid risks of FP, it is acceptable to raise issues only for simple control flows within the "with" block

# Pytest
def test_base_case():
    with pytest.raises(ZeroDivisionError):
        foo()
        assert bar() == 42  # Noncompliant


def test_ok():
    with pytest.raises(ZeroDivisionError):
        foo()
    assert bar() == 42  # OK


def test_base_case_2():
    with pytest.raises(ZeroDivisionError):
        assert bar() == 42  # OK, issue only on last assert
        assert foo() == 42  # Noncompliant


def test_for_loop_ok():
    with pytest.raises(ZeroDivisionError):
        for _ in range(5):
            foo()
            assert bar() == 42  # OK (might not be dead code depending on foo())


def test_for_loop_nok():
    with pytest.raises(ZeroDivisionError):
        for _ in range(5):
            foo()
        assert bar() == 42  # Noncompliant


def test_if_stmt():
    with pytest.raises(ZeroDivisionError):
        if bar() == 42:
            foo()
        else:
            assert bar() == 42  # Accepted FN


def test_if_stmt_nok():
    with pytest.raises(ZeroDivisionError):
        if bar() == 42:
            foo()
        assert bar() == 42  # Noncompliant


# Unittest
class MyTest(unittest.TestCase):

    def test_something(self):
        with self.assertRaises(ZeroDivisionError):
            self.assertEqual(foo(), 42)  # Noncompliant

    def test_something_2(self):
        with self.assertRaises(ZeroDivisionError):
            foo()
            self.assertEqual(bar(), 42)  # Noncompliant
