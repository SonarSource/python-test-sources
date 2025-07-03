from flask import Flask, escape, request
def foo():
    app = Flask(__name__)
    app == None  # Noncompliant but no issue


def noncompliant(condition, param):
    ###################
    # Type checking
    ###################
    # class A:
    #     def __eq__(self, other):
    #         pass

    # a1 = A()
    a2 = A()
    mynone = None
    mystr = "1"
    myint = 1
    mylist = []

    mystr == myint

    foo = mynone is None  # Noncompliant. Always True.
    foo = mynone is not None  # Noncompliant. Always False.
    foo = mynone == None  # Noncompliant. Always True.
    foo = mynone != None  # Noncompliant. Always False.


    mynone == myint

    class A:
        def __eq__(self, other):
            pass

    a1 = A()

    foo = a1 is None  # Noncompliant. Always False.
    foo = a1 is not None  # Noncompliant. Always True.
    foo = a1 == None  # Noncompliant. Always False.
    foo = a1 != None  # Noncompliant. Always True.

    foo = myint is None  # Noncompliant. Always False.
    foo = myint is not None  # Noncompliant. Always True.
    foo = myint == None  # Noncompliant. Always False.
    foo = myint != None  # Noncompliant. Always True.

    foo = mylist is None  # Noncompliant. Always False.
    foo = mylist is not None  # Noncompliant. Always True.
    foo = mylist == None  # No issue
    foo = mylist != None  # No issue

    foo = mystr is None  # Noncompliant. Always False.
    foo = mystr is not None  # Noncompliant. Always True.
    foo = mystr == None  # No issue
    foo = mystr != None  # No issue



    foo = mystr is None  # Noncompliant. Always False.

    foo = 1 == "1"  # Noncompliant. Always False.
    foo = 1 == A()  # Noncompliant. Always False.
    foo = A() == "1"  # Noncompliant. Always False.

    foo = 1 != "1"  # Noncompliant. Always True.
    foo = 1 != A()  # Noncompliant. Always True.
    foo = A() != "1"  # Noncompliant. Always True.

    ###################
    # Reassign and change type
    ###################
    myvar = 1
    myvar = "1"
    foo = myvar == 1  # Noncompliant. Always False.

    ###################
    # Value tracking
    ###################
    foo = a1 == a2  # Noncompliant. Always False.
    foo = a1 != a2  # Noncompliant. Always True.

    ###################
    # contains check
    ###################
    foo = 1 in ["1"]  # Noncompliant. Always False.

    ###################
    # List concatenation
    ###################
    mylist = []
    for a in range(10):
        mylist.append(a)

    foo = "a" in mylist  # Noncompliant. Always False.

    ###################
    # Multiple types
    ###################
    if condition:
        myvar = None
    else:
        myvar = "1"
    
    foo = myvar == 1  # Noncompliant. Always False.

    ###################
    # Handle isinstance
    ###################
    if isinstance(param, A):
        foo = param == 1  # Noncompliant. Always False.

    ###################
    # Handle is None / is not None
    ###################
    if param is None:
        foo = a == 1  # Noncompliant. Always False.

    if param is not None:
        pass
    else:
        foo = a == 1  # Noncompliant. Always False.

    ###################
    # Cross procedural
    ###################
    def func(condition):
        if condition:
            return None
        else:
            return "1"
    
    foo = func(condition) == 1  # Noncompliant. Always False.

    ###################
    # Class properties
    ###################
    class MyClass:
        def __init__(self):
            self.myattr = A()

    m = MyClass()
    foo = m.myattr == 1  # Noncompliant. Always False.

    ###################
    # Class methods (very complex)
    ###################
    class ClsB():
        def __init__(self):
            self._some_cls = None

        @property
        def some_cls(self):
            if self._some_cls:
                return self._some_cls
            self._some_cls = A
            return A

        def is_A(self):
            return self.some_cls == None  # Noncompliant. Always True.

    ###################
    # Avoid false positives
    ###################
    found = None
    for obj in [1,2,3]:
        if found is not None and found != obj:  # Beware of possible false positives! found != None here
            found += obj
        else:
            found = obj

    
    class MyClass:
        def __init__(self):
            self.myattr = A()
        
        def updateAttr(self, value):
            self.myattr = value  # reassign the attribute

    m = MyClass()
    foo = m.myattr == 1  # Avoid to raise as it could raise false positives


def compliant():
    foo = str(1) in ["1"]

    foo = 1 == int("1")

    foo = str(1) != "1"

    class A:
        def __eq__(self, other):
            return True

    myvar = A() == 1


