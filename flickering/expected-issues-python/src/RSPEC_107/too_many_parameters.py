# With the maximum number of parameters set to 7

def seven(a1, a2, a3, a4, a5, a6, a7):  # Ok. 7 parameters.
    pass

def seven_with_optional(a1, a2, a3, a4, a5, a6=1, a7="a string"):  # Ok. 7 parameters.
    pass

def positional_only(a1, a2, a3, a4, a5, a6, a7, /):  # False Positive. "/" should not be counted.
    pass

def keyword_only(a1, a2, a3, a4, a5, a6, *, a7):  # False Positive. "*" should not be counted.
    pass

def varargs(a1, a2, a3, a4, a5, a6, a7, *args):  # Noncompliant. *args counts as an argument
    pass

def keywords(a1, a2, a3, a4, a5, a6, a7, *kwargs):  # Noncompliant. **kwargs counts as an argument
    pass

def eight(a1, a2, a3, a4, a5, a6, a7, a8):  # Noncompliant. 8 parameters. 1 more than authorized.
    pass

def eight_with_optionals(a1, a2, a3, a4, a5, a6, a7=1, a8="a string"):  # Noncompliant. 8 parameters. 1 more than authorized.
    pass

lamb_seven = lambda a1, a2, a3, a4, a5, a6, *, a7: None  # Ok. 7 parameters.

lamb_eight = lambda a1, a2, a3, a4, a5, a6, *, a7, a8: None # Noncompliant. 8 parameters. 1 more than authorized.

class MyClass:
    """The first argument of non-static methods should not be counted."""
    def seven_with_self(self, a1, a2, a3, a4, a5, a6, a7):  # False Positive. The first argument, i.e. "self", should be ignored
        pass

    @classmethod
    def seven_with_cls(cls, a1, a2, a3, a4, a5, a6, a7):  # False Positive. The first argument, i.e. "cls", should be ignored
        pass

    @staticmethod
    def static_seven_with_self(self, a1, a2, a3, a4, a5, a6, a7):  # Noncompliant. This is a static method. The first argument is counted.
        pass

    def eight_with_self(self, a1, a2, a3, a4, a5, a6, a7, a8):  # Noncompliant. 8 parameters. 1 more than authorized.
        pass

    @classmethod
    def eight_with_cls(cls, a1, a2, a3, a4, a5, a6, a7, a8):  # Noncompliant. 8 parameters. 1 more than authorized.
        pass


    def nesting_function(self):
        def nested_seven(a1, a2, a3, a4, a5, a6, a7):  # Ok. 7 parameters.
            pass

        def nested_eight(a1, a2, a3, a4, a5, a6, a7, a8):  # Noncompliant. 8 parameters. 1 more than authorized.
            pass

# Following Liskov psubstitution principle is more important than having too many parameters.
# Thus the rule doesn't raise when a method overrides a method from a parent class and it has the
# same number of parameters.

class ParentClass:
    def eight_with_self(self, a1, a2, a3, a4, a5, a6, a7, a8):  # Noncompliant. 8 parameters. 1 more than authorized.
        pass

def SubClassCompliant(ParentClass):
    def eight_with_self(self, a1, a2, a3, a4, a5, a6, a7, a8):  # Ok. Following Liskov Principle is more important
        pass

def SubClassNoncompliant(ParentClass):
    def eight_with_self(self, a1, a2, a3, a4, a5, a6, a7, a8, a9):  # Noncompliant. One more parameter was added
        pass