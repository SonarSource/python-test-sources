def comparing_non_none():
    """Comparing non-None value to None."""
    myint = 1
    if myint is None:  # Noncompliant. Always False
        pass

    if myint is not None:  # Noncompliant. Always True
        pass

    if myint == None:  # Noncompliant. Always False
        pass

    if myint != None:  # Noncompliant. Always True
        pass

def comparing_none():
    """Comparing None value to None."""
    mynone = None

    if mynone is None:  # Noncompliant. Always True
        pass

    if mynone is not None:  # Noncompliant. Always False
        pass

    if mynone == None:  # Noncompliant. This is always True
        print("invalid")

    if mynone != None:  # Noncompliant. This is always False
        print("invalid")