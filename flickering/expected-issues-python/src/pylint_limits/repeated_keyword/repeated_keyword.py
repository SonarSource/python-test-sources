def test1():
    def func(a, b, c):
        pass

    params0 = {'c': 5}
    func(1, 2, **params0)  # True Negative

    # func(1,2,c=4, c=3)  # syntax-error

    params1 = {'c': 5}
    func(1, 2, c=3, **params1)  # True Positive (PyCharm True Positive but bad message)

    params2 = {}
    if not params2:
        params2 = {'c': 5}
    func(1, 2, c=3, **params2)  # False Negative (PyCharm True Positive but bad message)
    # => Pylint does not detect when the max of possible arguments is already provided

    params4 = {'b': 1, 'c': 5}
    func(2, c=3, **params4)  # True Positive (PyCharm False Negative)
    # => PyCharm only detects an issue when all the arguments are already provided and additional arguments are given. It does not detect when a specific keyword argument is duplicated.

    params5 = {}
    if not params5:
        params5 = {'b': 1, 'c': 5}
    func(2, c=3, **params5)  # False Negative (PyCharm False Negative)


    params6 = {}
    params7 = {}
    for val in [1, 2, 3]:
        func(2, c=5, **params6, **params7) # False Negative (pylint and PyCharm)
        params6['c'] = val
        params7['b'] = val

# Mypy doesn't detect anything

bar()
bar = sum

foo = sum
myfunc()

def myfunc():
    # foo()
    global foo

marf
marf = 1
mc = MyClass()
class MyClass:
    pass

# def  foo():
#     def other(a, a, c): # Noncompliant
#         return a * c