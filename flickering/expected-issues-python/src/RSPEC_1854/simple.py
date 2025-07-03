def func():
    unused = 42

    unused2 = 3
    unused2 = 4
    return unused2

def func(a, b, compute):
    i = a + b # Noncompliant; calculation result not used before value is overwritten
    i = compute()  # Noncompliant

def func(a, b, compute):
    i = a + b
    i += compute()
    return i

#
# Ignore global variables
#
i = a + b # Ok
i = compute()



def myfunc(param1, param2):
    param2 = param1 + 10
    param1 = 20  # Noncompliant
    return param2


def ifelse(param):
    if param:
        myvar = 1  # Noncompliant
    else:
        myvar = 2
        print(myvar)

#
# For-else loops
#
def myfunc2(mylist):
    var = 5  # Noncompliant
    for i in mylist:
        if i > 0:
            var = 10
        else:
            var = i
        print(var)

    var = 5  # Ok
    for i in mylist:
        if i > 0:
            var = 10
        else:
            var = i
    else:
        print(var)  # If the list is emtpy var has not been reassigned

    var = 5 # Ok
    for i in mylist:
        if i > 0:
            var = 10
        print(var)

    var = 5  # Ok
    for i in mylist:
        if var > i:
            var = 10  # Ok
        else:
            print(var)

#
# Global
#
myglobal = 5

def assign_global():
    global myglobal
    myglobal = 10  # Ok

#
# Ignore None
#
def ignore_none():
    value = None  # Ok

    for value in range(10):
        print(value)

    value2: Optional[PolicyType] = None  # Ok

    for value2 in range(10):
        print(value2)


#
# Ignore underscore
#
def ignore_underscore():
    for _ in range(10):
        pass

    # double underscore https://docs.python-guide.org/writing/style/#create-an-ignored-variable
    for __ in range(10):
        pass


