def myfunc(param):
    if param is None:
        print(param.test())  # Noncompliant

    if param == None:
        print(param.test())  # Noncompliant

    if param is not None:
        pass
    else:
        print(param.test())  # Noncompliant

    if param != None:
        pass
    else:
        print(param.test())  # Noncompliant
