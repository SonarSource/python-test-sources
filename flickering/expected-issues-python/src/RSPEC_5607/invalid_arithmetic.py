################################################
# Case to cover: Detect whem custom types do not
# have the right methods.
################################################

def custom_noncompliant():
    class Empty:
        pass

    class LeftAdd:
        def __add__(self, other):
            return 42

    class RightAdd:
        def __radd__(self, other):
            return 21
    
    class AddAssign:
        def __iadd__(self, other):
            return 42

    empty = Empty()
    left_add = LeftAdd()
    right_add = RightAdd()
    add_assign = AddAssign()

    myvar = empty + 1  # Noncompliant
    myvar = left_add + 1  # Ok
    myvar = 1 + left_add  # Noncompliant
    myvar = empty + left_add  # Noncompliant
    myvar = left_add + empty  # Ok

    myvar = right_add + 1  # Noncompliant
    myvar = 1 + right_add  # Ok
    myvar = empty + right_add  # Ok
    myvar = right_add + empty  # Noncompliant

    empty += 1
    add_assign += 1

    myvar = -empty  # Noncompliant


def custom_compliant():
    class A:
        def __add__(self, other):
            return 42

        def __neg__(self):
            return -1

    a = A()
    myvar = A() + 1
    myvar = -a


#################################################
# Case to cover: Detect whem builtin types do not
# have the right methods.
#################################################

def builtin_noncompliant():
    myvar = 1 + "1"  # Noncompliant
    myvar = 1 + [1]  # Noncompliant
    myvar = 1 + {1}  # Noncompliant
    myvar = 1 + (1,)  # Noncompliant
    myvar = 1 + {'a': 1}  # Noncompliant
    myvar = [1] + (1,)  # Noncompliant


    myvar = -'1'  # Noncompliant


def builtin_compliant():
    myvar = 1 + int("1")
    myvar = -int('1')
    myvar += 2
