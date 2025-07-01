class CanCall:
    def __call__(self):
        print('called')

can_call = CanCall()
can_call()  # Ok


class Parent:
    def __call__(self):
        print('called')

class Child(Parent):
    pass

can_call2 = Child()
can_call2()  # Ok


class CannotCall:
    pass

cannot_call = CannotCall()
cannot_call()  # Noncompliant

none_var = None
none_var()  # Noncompliant


# From Pylint_limits

import math

class A:
    def __init__(self):
        self.myfunc = sum
        self.mynumber = 42

class B(A):
    def __init__(self):
        super(B,self).__init__()
        self.myfunc()
        self.mynumber()  # Noncompliant


def mycallable():
    pass

mycallable()


def call_func():
    return mycallable

call_func()()


def none_func():
    return None

none_func()()  # Noncompliant



def choice_func():
    if False:
        return mycallable
    return None

choice_func()()  # Noncompliant


var1 = mycallable
var1 = None
var1()  # Noncompliant


var2 = None
var2 = mycallable
var2()


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

C().fp1(0)
C().fp2(0)

C().tn1(0)
C().tn2(0)
C().tp1(0)  # Noncompliant


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
        return self.some_cls()

class ClsB2():

    def __init__(self):
        self._some_cls = None

    @property
    def some_cls(self):
        self._some_cls = ClsA
        return self._some_cls

    def get_object(self):
        return self.some_cls()

class ClsB3():

    def __init__(self):
        self._some_cls = None

    @property
    def some_cls(self):
        myclassA = ClsA
        return myclassA

    def get_object(self):
        return self.some_cls()



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
        self.runner('hello world')

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
mycl()  # Noncompliant (MyPy, Pylint and PyCharm)

myci = MyClassImport()
myci()  # Noncompliant (MyPy, Pylint and PyCharm)

myci2 = MyClassImport2()
myci2()

myci3 = MyClassImport3()
myci3()