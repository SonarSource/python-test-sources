def custom_noncompliant():
    class Empty:
        pass

    empty = Empty()

    myvar = empty + 1  # Noncompliant
#                 ^ Primary message:  Fix this invalid "+" operation between incompatible types.

    myvar = -empty  # Noncompliant
#           ^ Primary message:  Fix this invalid "-" operation on a type which doesn't support it.

