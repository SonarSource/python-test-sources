#
# Generator example
#


def mygenerator(param):  # Noncompliant, if too many elements are generated the maximum recursion depth will be reached
    yield param
    yield from mygenerator(param - 1)


for i in mygenerator(10):
    print(i)
