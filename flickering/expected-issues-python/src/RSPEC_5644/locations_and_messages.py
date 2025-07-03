#################################################
# Missing __getitem__, __setitem__ or __delitem__
#################################################
class A:
#     ^ Secondary message: Class definition.
    def __init__(self, values):
        self._values = values

def subscript_A():
    myvar = A([0,1,2])
#           ^^^^^^^^^^ Secondary message: Assigned value.

    myvar[0]  # Noncompliant
#   ^^^^^  # Primary message: Fix this code; "myvar" does not have a "__getitem__" method.

    del myvar[0]  # Noncompliant
#   ^^^^^  # Primary message: Fix this code; "myvar" does not have a "__delitem__" method.

    myvar[0] = 42  # Noncompliant
#   ^^^^^  # Primary message: Fix this code; "myvar" does not have a "__setitem__" method.


###########################
# Missing __class_getitem__
###########################


class B:
#     ^ Secondary message: Class definition.
    pass

def subscript_B():
    B[0]  # Noncompliant
#   ^  # Primary message: Fix this code; class "B" does not have a "__class_getitem__" method.