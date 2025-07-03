#
# Non-iterable type used with "for..in"
#
def for_in():
    non_iterable = 42

    for a in non_iterable:  # Noncompliant
        #    ^^^^^^^^^^^^  Primary message: Replace this expression with an iterable object.
        pass


#
# Non-iterable type used with unpacking
#
def unpacking1():
    non_iterable = 42

    a, *rest = non_iterable  # Noncompliant
    #          ^^^^^^^^^^^^  Primary message: Replace this expression with an iterable object.


def unpacking2():
    non_iterable = 42

    print(*non_iterable)  # Noncompliant
    #      ^^^^^^^^^^^^  Primary message: Replace this expression with an iterable object.


def unpacking_async():
    async def async_function():
        pass

    a, *rest = async_function()  # Noncompliant
    #          ^^^^^^^^^^^^^^^^  Primary message: Replace this expression with an iterable object.


#
# Looping on an async object without the "async" keyword
#
def looping_async():
    async def async_function():
        pass

    for a in async_function():  # Noncompliant
        #    ^^^^^^^^^^^^^^^^  Primary message: Add "async" before "for"; Expression is an async generator.
        pass
