class MyClass:
    def __add__(self, other):
        raise NotImplementedError()  # Noncompliant
    def __radd__(self, other):
        raise NotImplementedError()  # Noncompliant

class MyOtherClass:
    def __add__(self, other):
        return 42
    def __radd__(self, other):
        return 42

MyClass() + MyOtherClass()  # This will raise NotImplementedError


class MyClass:
    def __add__(self, other):
        return NotImplemented
    def __radd__(self, other):
        return NotImplemented

class MyOtherClass:
    def __add__(self, other):
        return 42
    def __radd__(self, other):
        return 42

MyClass() + MyOtherClass()  # This returns 42
