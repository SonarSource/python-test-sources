def foo():
    x: int = "hello"  # Noncompliant {{Assign to "x" a value of type "int" instead of "str" or update the type hint of "x".}}
#      ^^^>  ^^^^^^^

def bar(param):
    x: int
#      ^^^> {{Type hint.}}
    if param:
        x = 42
    else:
        x = "hello"  # Noncompliant {{Assign to "x" a value of type "int" instead of "str" or update the type hint of "x".}}
#       ^^^^^^^^^^^
