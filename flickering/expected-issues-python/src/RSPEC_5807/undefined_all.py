from math import exp
from unresolved import Unresolved  # Unknown import
from .same_package import same_package_function  # Importing from the same package


var = "unknown"

__all__ = [
    'LocalClass',
    '',  # Noncompliant
    Unresolved,  # Out of scope
    undefined_variable,  # Out of scope. Covered by S3827
    'NeverDefined',   # Noncompliant
    'exp',
    'method',   # Noncompliant
    'hidden_variable',   # Noncompliant
    'NestedClass',  # Noncompliant
    exp.__name__,
    var  # Noncompliant
]


class LocalClass:
    pass

def local_function():
    pass

class HindingClass:
    def method(self):
        hidden_variable = 42

    class NestedClass:
        pass
