class MyClass:
    pass

class MyStr(str):
    pass

var = 42
a_string = "MyClass"
__all__ = [
    MyClass.__name__,
    "MyClass",
    a_string,
    MyStr("foo"),  # Ok. This class derives from str. This should happen rarely.
    MyClass,  # Noncompliant
    42,  # Noncompliant
    var,  # Noncompliant
    round,  # Noncompliant
    lambda x: x,  # Noncompliant
    None,  # Noncompliant
]