################################################
# Case to cover: Detect whem custom types do not
# have the right methods.
################################################

def custom_noncompliant():
    class Empty:
        pass

    class LessThan:
        def __lt__(self, other):
            return True

    empty = Empty()
    lessThan = LessThan()

    myvar = empty < 1  # Noncompliant
    myvar = lessThan < 1  # Ok
    myvar = 1 < lessThan  # Noncompliant
    myvar = empty < lessThan  # Noncompliant
    myvar = lessThan < empty  # Ok
    myvar = empty > lessThan  # Ok


def custom_compliant():
    class A:
        def __lt__(self, other):
            return True

        def __neg__(self):
            return -1

    a = A()

    myvar = A() < 1


#################################################
# Case to cover: Detect whem builtin types do not
# have the right methods.
#################################################

def builtin_noncompliant():
    myvar = 1 < "1"  # Noncompliant
    myvar = complex(1) < complex(1)  # Noncompliant
    myvar = [1] < (1,)  # Noncompliant
    myvar = 1 < "1"  # Noncompliant
    myvar = 1 < "1"  # Noncompliant


def builtin_compliant():
    myvar = 1 < int("1")
