import pytest


def foo(): return 1 / 0


def bar(): return 42


def test_something():
    with pytest.raises(ZeroDivisionError):
#   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^>
        foo()
        assert bar() == 42  # Noncompliant {{Don't perform an assertion here; An exception is expected to be raised before its execution.}}
#       ^^^^^^

def test_something_only_one_statement():
    with pytest.raises(ZeroDivisionError):
#   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^>
        assert foo() == 42  # Noncompliant {{Refactor this test; if this assertion's argument raises an exception, the assertion will never get executed.}}
#       ^^^^^^