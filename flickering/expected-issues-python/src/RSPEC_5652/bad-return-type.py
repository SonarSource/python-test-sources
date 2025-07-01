from typing import List, Generator

class MyClass(object):
    def __init__(self):
        return 3

    def __contains__(self, key):
        return "not a bool"  # Noncompliant

    def __int__(self):
        return 3.0  # Noncompliant. __int__ should always return an integer
    
    def __float__(self):
        return 3  # Noncompliant

    def __bytes__(self):
        return 3.0  # Noncompliant

    def __complex__(self):
        return 3  # Noncompliant
    
    def __index__(self):
        return 3.0  # Noncompliant

    def __round__(self):
        return 3.0  # Noncompliant. Should be int
    
    def __round__(self, ndigits):
        return 3.0  # OK
    
    def __hash__(self):
        return 3.0  # Noncompliant
    
    def __repr__(self):
        return 3  # Noncompliant
    
    def __str__(self):
        return 3  # Noncompliant
    
    def __format__(self, options):
        return 3  # Noncompliant
    
    def __setitem__(self, key, value):
        return 42  # Noncompliant. Should return nothing

    def __delitem__(self, key):
        return 42  # Noncompliant. Should return nothing

    def __setattr__(self, key, value):
        return 42  # Noncompliant. Should return nothing
        
    def __delattr__(self, key):
        return 42  # Noncompliant. Should return nothing

int(MyClass())  # This will fail with "TypeError: __int__ returned non-int (type float)"

def hello() -> str:
    return 42  # Noncompliant. Function's type hint asks for a string return value

def should_return_a_string(condition) -> str:
    if condition:
        return "a string"
    # Noncompliant. The function returns None if the condition is not met

def mylist() -> List[str]:
    return [1, 'string']  # Noncompliant

def mylist2() -> List[str]:
    yield ['string']  # Noncompliant

# Generators: https://docs.python.org/3/library/typing.html#typing.Generator
def generator_ok() -> Generator[int, float, str]:
    sent = yield 42
    return '42'

def generator_noncompliant() -> Generator[int, float, str]:
    sent = yield '42'  # Noncompliant
    return 42  # Noncompliant

class Ok:
    def __init__(self):
        return None
