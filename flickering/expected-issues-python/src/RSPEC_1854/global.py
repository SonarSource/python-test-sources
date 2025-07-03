myvar = 5


def myfunc():
    global myvar
    myvar = 10  # Compliant because it is a global variable and we don't know how it will be used


myfunc()
print(myvar)
