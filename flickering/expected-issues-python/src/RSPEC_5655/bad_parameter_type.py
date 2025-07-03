def assert_isinstance(var):
    assert isinstance(var, str), "unexpected type for var"

assert_isinstance(42)  # Noncompliant
assert_isinstance("42")

def raise_type_error(var):
    if not isinstance(var, str):
        raise TypeError("unexpected type for var")

raise_type_error(42)  # Noncompliant
raise_type_error("42")

def annotation(a_str: str, an_int: int):
    pass

annotation(42, 42)  # Noncompliant
annotation("42", "42")  # Noncompliant
annotation(an_int="42", a_str="42")  # Noncompliant
annotation(an_int=42, a_str=42)  # Noncompliant
annotation("42", 42)
annotation(an_int=42, a_str="42")

len("42.3")
len(42.3)  # Noncompliant
round("42.3")  # Noncompliant. False Negative.
round(42.3)

def expect_number(var):
    round(var)  # This makes it clear that "var" is a number

expect_number("42.3")  # Noncompliant

def not_none(var):
   var.foo()  # This makes it clear that "var" is not None

not_none(None)  # Noncompliant


class A:
    def foo(self):
        return 42
class B:
    def foo(self):
        return 42
def func(p: A):
    print(p.foo())
func(B())  # No issue currently as we consider A and B as duck type compatible
