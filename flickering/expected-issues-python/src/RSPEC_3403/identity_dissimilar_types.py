def noncompliant(condition):
    ###################
    # Type checking
    ###################
    class A:
        pass

    a1 = A()
    mystr = "1"

    foo = a1 is 1  # Noncompliant. Always False.

    foo = mystr is 1  # Noncompliant. Always False.


    foo = a1 is not 1  # Noncompliant. Always True.

    foo = mystr is not 1  # Noncompliant. Always True.