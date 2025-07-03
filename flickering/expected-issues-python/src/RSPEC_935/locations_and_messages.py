class BasicReturns:
    def __bool__(self):
#       ^^^^^^^^>
        return "hello"  # Noncompliant {{Return a value of type "bool" instead of "str", as should any "__bool__" method.}}
#       ^^^^^^^^^^^^^^

    def __int__(self):
#       ^^^^^^^>
        return  # {{Return a value of type "int" instead of "None", as should any "__int__" method".}}
#       ^^^^^^

    def __repr__(self):  # {{Return a value of type "str"; "__repr__" may reach its end and return None.}}
#       ^^^^^^^^
        for _ in range(10):
            print("Hello")

    def __init__(self):
#       ^^^^^^^>
        return 42  # {{Return "None" instead of a value of type "int", as should any "__init__" method".}}
#       ^^^^^^
