
# pylint: disable=missing-docstring, too-few-public-methods,pointless-statement, wildcard-import, unused-wildcard-import, using-constant-test, global-statement
# pylint: disable=expression-not-assigned

import math

class A:
    def __init__(self):
        self.myfunc = sum
        self.mynumber = 42

class B(A):
    def __init__(self):
        super(B,self).__init__()
        self.myfunc()  # True Negative
        self.mynumber()  # True Positive


def mycallable():
    pass

mycallable()  # True Negative


def call_func():
    return mycallable

call_func()()  # True Negative


def none_func():
    return None

none_func()()  # True Positive



def choice_func():
    if False:
        return mycallable
    return None

choice_func()()  # False Negative


var1 = mycallable
var1 = None
var1()  # True Positive


var2 = None
var2 = mycallable
var2()  # True Negative


# https://github.com/PyCQA/pylint/issues/2900
class C():
    def __init__(self):
        self._fp1 = []
        self.fp2 = []
    @property
    def fp1(self):
        self._fp1 = math.sin
        return self._fp1

    @property
    def tn1(self):
        return math.sin

    @property
    def tn2(self):
        var = math.sin
        return var
    
    @property
    def tp1(self):
        var = None
        return var

C().fp1(0)  # False Positive
C().fp2(0)  # False Positive

C().tn1(0)  # True Negative
C().tn2(0)  # True Negative
C().tp1(0)  # True Positive


# https://github.com/PyCQA/pylint/issues/1730

# => Type inference engine suposes that class attributes have their original value type. It does not check for later assignments. 

class ClsA():
    pass


class ClsB():

    def __init__(self):
        self._some_cls = None

    @property
    def some_cls(self):
        if self._some_cls:
            return self._some_cls
        self._some_cls = ClsA
        return ClsA

    def get_object(self):
        return self.some_cls()  # False Positive

class ClsB2():

    def __init__(self):
        self._some_cls = None

    @property
    def some_cls(self):
        self._some_cls = ClsA
        return self._some_cls

    def get_object(self):
        return self.some_cls()  # False Positive

class ClsB3():

    def __init__(self):
        self._some_cls = None

    @property
    def some_cls(self):
        myclassA = ClsA
        return myclassA

    def get_object(self):
        return self.some_cls()  # True Negative



# https://github.com/PyCQA/pylint/issues/1510

class Runner:
    '''callable class that might take work to construct'''
    def __call__(self, *args, **kwargs):
        pass

class Runstuff:
    def __init__(self):
        self._runner = None

    def dostuff(self):
        '''call the runner class'''
        self.runner('hello world')  # False Positive

    @property
    def runner(self):
        '''constructs Runner and returns it'''
        if self._runner is None:
            self._runner = Runner()
        return self._runner


from .definitions import MyClassImport, MyClassImport2, MyClassImport3

class MyClassLocal:
    pass

mycl = MyClassLocal()
mycl()  # True Positive (MyPy, Pylint and PyCharm)

myci = MyClassImport()
myci()  # True Positive (MyPy, Pylint and PyCharm)

myci2 = MyClassImport2()
myci2()  # True Negative (MyPy, Pylint and PyCharm)

myci3 = MyClassImport3()
myci3()  # True Negative (MyPy, Pylint and PyCharm)


# https://github.com/PyCQA/pylint/issues/436
# => defaultdict is defined in CPython's C code => out of scope

import collections
class KeyedFactoryDefaultDict(collections.defaultdict):
    """Modified defaultdict that passes the key to default_factory calls."""

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        value = self.default_factory(key)
        self[key] = value
        return value
