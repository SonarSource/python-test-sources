def noncompliant():
    def nested_function():  # Noncompliant
        print("nested_function")
    
    class NestedClass:  # Noncompliant
        def __init__(self):
            print("NestedClass")


def compliant():
    def nested_function():
        print("nested_function")
    
    class NestedClass:
        def __init__(self):
            print("NestedClass")

    nested_function()
    NestedClass()


def compliant2():
    def using():
        nested_function()
        NestedClass()

    def nested_function():
        print("nested_function")
    
    class NestedClass:
        def __init__(self):
            print("NestedClass")

    using()


def noncompliant2():
    def using():  # Noncompliant
        nested_function()
        NestedClass()

    def nested_function():
        print("nested_function")
    
    class NestedClass:
        def __init__(self):
            print("NestedClass")