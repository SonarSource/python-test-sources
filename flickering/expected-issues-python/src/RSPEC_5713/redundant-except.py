try:
    raise NotImplementedError()
except (NotImplementedError, RuntimeError):  # Noncompliant. NotImplementedError inherits from RuntimeError
    print("Foo")

try:
    raise NotImplementedError()
except (RuntimeError, RuntimeError):  # Noncompliant.
    print("Foo")