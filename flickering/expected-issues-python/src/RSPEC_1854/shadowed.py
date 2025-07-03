# Shadowing global variable with function parameter

#
# Example 1
#
myvar = 5  # OK, myvar may be used in another file


def myfunc(myvar):
    print(myvar)


print(10)

#
# Example 2
#
myvar2 = 5  # Ok


def myfunc2():
    myvar2 = 10
    print(myvar2)
    myvar2 = 22  # Noncompliant


print(myvar2)
