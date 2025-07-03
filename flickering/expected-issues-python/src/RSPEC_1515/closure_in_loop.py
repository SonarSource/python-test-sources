def simple_reference():
    for i in range(10):
        print(i)


def simple_reference2():
    return [j for j in range(5)]


def default_value():
    """Passing the variable's value via a default value is ok."""
    mylist = []
    for i in range(5):
        mylist.append(lambda i=i: i)

        def func(i=i):
            return i
        mylist.append(func)


def not_using_outer_variables():
    """Shadowing outer variables with parameters is ok."""
    mylist = []
    for j in range(5):
        print(j)
        mylist.append(lambda j: j)
        def func(j):
            return j
        mylist.append(func)


def return_lambda(param):
    """Exception: returning a lambda/function makes it ok.

    The variable will not change its value as there are no more iterations.
    """
    for j in range(5):
        if param:
            return lambda: j
        else:
            def func():
                return j
            return func
    return lambda: 42


def variable_ref_and_func_ref():
    """Referencing a variable updated in the enclosing loop and passing the function via reference is suspicious."""
    mylist = []
    for j in range(5):  # Secondary location on "j", it is the only code updating j.
        mylist.append(lambda: j)  # Noncompliant

        def func():
            return j  # Noncompliant
        mylist.append(func)


def all_iterating_variable():
    """All referenced variable should be considered."""
    mylist = []
    for i, j in zip(range(5), range(5)):  # Secondary location on "j", it is the only code updating j.
        computed = j * 2  # Secondary location on "computed", it is the only code updating computed.
        mylist.append(lambda: computed)  # Noncompliant
        mylist.append(lambda: j)  # Noncompliant

        def func1():  # Noncompliant
            return computed
        mylist.append(func1)

        def func2():  # Noncompliant
            return j
        mylist.append(func2)


def use_default_value():
    """
    The best way to use a loop variable in a function
    s to pass it as a default value.
    """
    for i in range(10):
        def nested1(i=i):  # Ok
            return i

        def nested2(i=[i]):  # Ok
            return i
        
        def nested2(i=i.foo):  # Ok
            return i
        
        def nested2(i=i + 1):  # Ok
            return i


def param_with_same_name():
    """
    Creating a parameter named as a loop variable is ok.
    """
    for i in range(10):
        def nested2(i):  # Ok
            return i

def example_of_api_change():
    """"
    Passing loop variable as default values also makes sure that the code is future-proof.
    For example the following code will work as intended with python 2 but not python 3.
    Why? because "map" behavior changed. It now returns an iterator and executes the lambda
    only when required. The same is true for other functions such as "filter".
    See https://portingguide.readthedocs.io/en/latest/iterators.html#new-behavior-of-map-and-filter
    """
    lst = []
    for i in range(5):
        lst.append(map(lambda x: x + i, range(3)))  # Noncompliant
    for sublist in lst:
        # prints [4, 5, 6] x 4 with python 3, with python 2 it prints [0, 1, 2], [1, 2, 3], ...
        print(list(sublist))


def lambda_variable_not_called_in_loop():
    """If the lambda is saved in a variable which is not called, then an issue should be raised."""
    mylist = []
    for j in range(5):  # Secondary location on "j", it is the only code updating j.
        lamb = lambda: j  # Noncompliant
        mylist.append(lamb)
    return mylist


def lambda_variable_called_after_loop():
    """If the lambda is saved in a variable which is called outside of the loop, then an issue should be raised."""
    for j in range(5): # Secondary location on "j", it is the only code updating j.
        if j == 2:
            lamb = lambda: j  # Noncompliant
    print(lamb())


#
#  Multiple secondary locations on assignments
#

def multiple_assignments():
    for i in range(10):
        var = i * 2  # Secondary location
        def foo(): # Secondary location
            return var
        var = 5  # Secondary location
    return foo

#
# Comprehensions
#

def list_comprehension_lambda_referenced(value):
    """
    Referencing a variable updated in the enclosing
    comprehension and returning a reference to the function is suspicious.
    """
    if value == "list":
        return [lambda: j for j in range(5)]  # Noncompliant
    elif value == "set":
        return {lambda: j for j in range(5)}  # Noncompliant
    elif value == "dict":
        return {j: lambda: j for j in range(5)}  # Noncompliant
    return 42


def list_comprehension_deep_lambda_referenced():
    """
    Lambdas in lambdas with default values. This should be safe.
    """
    return [lambda j=j: lambda: j for j in range(5)]  # Ok


def list_comprehension_lambda_called():
    """
    Referencing a variable updated in the enclosing comprehension
    and calling the function in the comprehension is ok.

    This should happen rarely but is a special case of functions called in loops.
    """
    return [(lambda: j)() for j in range(5)]  # ok


def nested_loop_in_comprehension():
    return [
        (lambda: [i for _ in range(5)])  # Noncompliant
        for i in range(5)
    ]


def nested_loop_in_comprehension2():
    return [lambda: i for _ in range(5) for i in range(3)]  # Noncompliant


def nested_loop_in_comprehension3():
    return [lambda: i for i in range(5) for _ in range(3)]  # Noncompliant

def comprehension_with_called_lambda():
    lst = [1, 2, 3]
    return [filter(lambda a: a == i, lst) for i in range(4)]  # Noncompliant


#
# Generators
#

def generator_expression():
    """Generator expressions are ok when they don't reference outer variables."""
    return (j for j in range(5))


def lambda_in_generator(param):
    """lambdas defined in generator expressions are suspicious enven if it could raise False Positives.
    """
    gen = (lambda: i for i in range(3))  # Noncompliant, Secondary location on "i" of "for i"
    if param:
        return [func() for func in gen]  # This would return [0, 1, 2]
    else:
        funcs = [func for func in gen]
        return [func() for func in funcs]  # This would return [2, 2, 2]


#
#  Exceptions
#

def function_called_in_loop():
    """Exception: Lambda/Functions defined and called in the same loop are ok.

    Having this exception means that we won't detect issues if a different iteration calls the function.
    This False Negative is ok.
    """
    for i in range(10):
        print((lambda param: param * i)(42))

        def func(param):
            return param * i

        print(func(42))


def lambda_variable_called_in_loop():
    """We should make an exception when the lamda is saved in a variable and called in the same loop."""
    for j in range(5):
        lamb = lambda: j  # Ok
        lamb()

# Maybe we should add exceptions when the function is passed to a builtin functions such as sorted, re.sub, list, list.sort


#
# Edge cases
#

def break_in_loop():
    for i in range(10):
        def foo():
            return i  # Noncompliant. The design is overly complex
        break
    return foo

def return_in_loop():
    for i in range(10):
        def foo():
            return i  # Ok. This is quite complex but still understandable. We have to set the limit somewhere.
        return foo

def test_decorators():
    for i in range(10):
        decorator = lambda func: func
        @decorator  # ok
        def foo():
            pass

        decorator2 = lambda param: lambda func: func

        @decorator2(i)  # ok
        def bar():
            pass

def use_nonlocal():
    for i in range(10):
        var = None
        def foo():
            nonlocal var  # ok
            var = 42
    foo()