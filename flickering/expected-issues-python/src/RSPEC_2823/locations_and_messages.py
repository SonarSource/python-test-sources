class MyClass:
    pass

var = 42
__all__ = [
    "MyClass",
    MyClass,  # Noncompliant
#   ^^^^^^^  Primary message: Replace this symbol with a string; "__all__" can only contain strings.
]