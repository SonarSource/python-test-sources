try:
    raise ValueError("orig")
except ValueError as e:
    new_exc = TypeError("new")
    new_exc.__cause__ = "test"  # Noncompliant
    raise new_exc

try:
    raise ValueError("orig")
except ValueError as e:
    raise TypeError("new") from "test"  # Noncompliant

try:
    raise ValueError("orig")
except ValueError as e:
    new_exc = TypeError("new")
    new_exc.__cause__ = None  # Ok
    raise new_exc

try:
    raise ValueError("orig")
except ValueError as e:
    new_exc = TypeError("new")
    new_exc.__cause__ = e  # Ok
    raise new_exc

try:
    raise ValueError("orig")
except ValueError as e:
    raise TypeError("new") from None  # Ok

try:
    raise ValueError("orig")
except ValueError as e:
    raise TypeError("new") from e  # Ok

