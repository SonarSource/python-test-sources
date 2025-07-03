# Pylint rule equivalent: undefined-variable

def noncompliant():
    foo()  # Noncompliant
    foo = sum
    foo()

    func()  # Noncompliant
    def func():
        pass
    func()

    MyClass()  # Noncompliant
    class MyClass:
        pass
    MyClass()


    try:
        raise ValueError()
    except ValueError as e:
        pass

    print(e)  # Noncompliant (This is specific to try-except)


    for x in [0, 1, 2]:
        if x == 2:
            break
    else:
        raise ValueError('Value not found')

    print(x)  # Ok. variables are accessible after a loop


    if False:
        condition_var = 0
    else:
        print(condition_var)  # Noncompliant

myglobal = 42


def constants():
    quit
    exit
    copyright
    credits
    license
    __debug__
    Ellipsis
    NotImplemented
    None
    True
    False


def use_local_ok_1():
    myglobal = 21  # This variable is local
    print(myglobal)  # Ok

def use_local_ok_2():
    def myglobal():
        pass
    print(myglobal)  # Ok

def use_local_ok_3():
    class myglobal():
        pass
    print(myglobal)  # Ok

def use_local_bad_1():
    print(myglobal)  # Noncompliant (python will fail with "local variable 'myglobal' referenced before assignment")
    myglobal = 42  # the variable is assigned, which makes it local

def use_local_bad_2():
    print(myglobal)  # Noncompliant
    def myglobal():
        pass

def use_local_bad_3():
    print(myglobal)  # Noncompliant
    class myglobal():
        pass

use_local_ok_3()

def use_global():
    print(myglobal)  # Noncompliant (python will fail with "name 'myglobal' is used prior to global declaration")
    global myglobal


def myfunc(condition):
    if condition:
        print('message')
    else:
        res = 42
    print(res)  # Ok. Can't know if res will be defined

    try:
        if (condition):
            raise Exception('')
        res2 = 42
    finally:
        print(res2)  # Ok Can't know if res will be defined



def run():
    myvar = 0

    def read():
        print(myvar)
    
    myvar = 1  # Ok

    read()

run()

def run():
    myvar = 0
    class Sub():
        def read(self):
            print(myvar)
    
    myvar = 1  # Ok

    a = Sub()
    a.read()

run()


def run():
    myvar = 0
    read = lambda: print(myvar)
    
    myvar = 1  # Ok

    read()

run()


def decorator(param):
    def sub_decorator(wrapped):
        def wrapper(self):
            print(f"wrapper {param}")
            wrapped(self)
        return wrapper
    return sub_decorator

class A:
    _ATTR = 42
    @decorator(_ATTR)  # Ok
    def foo(self):
        print("foo")


def foo(param):
    return 42

print(f'{foo(param=3)}')


global GLOB  # OK
GLOB = 42

def use_glob():
    print(GLOB)  # OK



def use_glob2():
    print(GLOB2)  # OK

global GLOB2  # OK
GLOB2 = 42