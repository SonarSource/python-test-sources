# https://github.com/PyCQA/pylint/issues/1990

class A(Exception):
    myfield = 0

def func(a):
    if isinstance(a, A):
        print(a.myfield) # True Negative

def func_exept():
    try:
        pass
    except Exception as a:
        if isinstance(a, A):
            print(a.myfield) # False Positive

a = None
if a is None:
    a = 1
b = -a


# https://github.com/PyCQA/pylint/issues/801

class MyClass:
    pass
var = MyClass()
if hasattr(var, 'bar'):
    var.bar() # False Positive but useless

def func_hasattr(param):
    if hasattr(param, 'bar'):
        param.bar() # Ok. No issue