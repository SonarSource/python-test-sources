unknown_var  # Noncompliant (variable is never defined)

def noncompliant():
    foo()  # Noncompliant
    foo = sum

    func()  # Noncompliant
    def func():
        pass

    MyClass()  # Noncompliant
    class MyClass:
        pass


def compliant():
    foo = sum
    foo()

    def func():
        pass
    func()

    class MyClass:
        pass
    MyClass()