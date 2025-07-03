#
# Some types will always be True, such as function, class, etc... We then just check the type.
# For some othe types we need to check the actual value: int, bool, etc... and see if it will always be the same value.
#

#
# Constant literals in condition.
#
if 42:  # Noncompliant
    pass

if False:  # Noncompliant
    pass

if 'a string':  # Noncompliant
    pass

if b'bytes':  # Noncompliant
    pass

if 42.0:  # Noncompliant
    pass

if {}:  # Noncompliant
    pass

if {"a": 1, "b": 2}:  # Noncompliant
    pass

if {41, 42, 43}:  # Noncompliant
    pass

if []:  # Noncompliant
    pass

if [41, 42, 43]:  # Noncompliant
    pass

if (41, 42, 43):  # Noncompliant
    pass

if ():  # Noncompliant
    pass

if None:  # Noncompliant
    pass

#
# Out of scope: literals using only unpacking
#
def unpacking_list(p1, p2):
    if ["a string", *p1, *p2]:  # Noncompliant. The list is not empty so it will always be True
        print("never empty")

    if [*p1, *p2]:  # No issue. We don't know if the resulting list will be empty or not
        print("unknown size")

    known_p1 = {}
    known_p2 = {}

    if [*known_p1, *known_p2]:  # False Negative. Always False. We won't follow unpacked variables.
        print("false negative")


def unpacking_dict(p1, p2):
    if {"key": 1, **p1, **p2}:  # Noncompliant. The dict is not empty so it will always be True
        print("never empty")

    if {**p1, **p2}:  # No issue. We don't know if the resulting dict will be empty or not
        print("unknown size")


def unpacking_set(p1, p2):
    if {"key", *p1, *p2}:  # Noncompliant. The set is not empty so it will always be True
        print("never empty")

    if {*p1, *p2}:  # No issue. We don't know if the resulting set will be empty or not
        print("unknown size")


def unpacking_tuple(p1, p2):
    if ("key", *p1, *p2):  # Noncompliant. The set is not empty so it will always be True
        print("never empty")

    if (*p1, *p2):  # No issue. We don't know if the resulting set will be empty or not
        print("unknown size")

#
# Conditional expression
#
var = 1 if 2 else 3  # Noncompliant. 2 is constant


# Boolean expressions can be used outside of "if...elif" or "while"
# They are then used as an alterantive to Conditional Expressions.
var = input() or 3  # Ok. 3 does not act as a condition when it is the last value of an "or" chain.
var = input() and 3  # Ok. 3 does not act as a condition when it is the last value of an "or" chain.
var = input() and 3 and input()  # Noncompliant. 3 is a condition if it is in an "and" chain and it is not the last element.
var = input() or 3 or input()  # Noncompliant. 3 is a condition if it is in an "or" chain and it is not the last element.
var = input() and 3 or input()  # Ok. 3 is the return value when the first input() is True.
var = input() or 3 and input()  # Noncompliant. The last input() will never be executed. 3 acts as a condition.
var = 3 or input() and input()  # Noncompliant.
var = 3 and input() or input()  # Noncompliant.


# When used in an "if...elif" condition, the order of boolean operators has no influence
if input() or 3:  # Noncompliant
    pass


# "not" operators do not change how the rule behaves. In theory they could have a side effect for some types but it is doubtful

if not 3:  # Noncompliant
    pass

#
# while loops are out of scope for now
#
while True:  # Ok
    pass


#
# builtin constructors are for now out of scope. It will probably not add much value
#
if tuple((1, 2, 3)):  # No issue even if it is constant
    pass

if dict():  # No issue even if it is constant
    pass

if list():  # No issue even if it is constant
    pass


#
# Modules
#
import math


if math:  # Noncompliant
    pass


#
# Function
#
def myfunction():
    return 42

if myfunction:  # Noncompliant
    pass
elif round:  # Noncompliant
    pass

#
# Class and methods
#
class MyClass:
    def mymethod(self):
        if self.mymethod:  # Noncompliant
            pass

    @property
    def myprop(self):
        pass

def constant_class_and_methods():
    myinstance = MyClass()
    if MyClass:  # Noncompliant
        pass
    elif MyClass.mymethod:   # Noncompliant
        pass
    elif myinstance.mymethod:   # Noncompliant
        pass
    elif myinstance.myprop:   # Ok
        pass
    elif myinstance:   # Ok
        pass


#
# Lambdas
#
def lambdas():
    lamb = lambda: None
    if lamb:  # Noncompliant
        pass


#
#  Generator Expressions
#
def generators():
    gen_exp = (i for i in range(42))
    if gen_exp:  # Noncompliant
        pass

#
# Generator.
#
def generator_function():
    yield

generator = generator_function()
if generator:  # Noncompliant
    pass


#
# Constant filter in comprehension and generator expression
#
def func():
    pass

# list
[i for i in range(42) if func]  # Noncompliant
[i for i in range(42) if 21]  # Noncompliant
# set
{i for i in range(42) if func}  # Noncompliant
# dict
{i: "a string" for i in range(42) if func}  # Noncompliant
# generator expression
(i for i in range(42) if func)  # Noncompliant
(i for i in range(42) if 21)  # Noncompliant

# variables defined in the comprehension should be ignored
[i for i in range(42) if i]  # Ok


#
# Builtins
#
def unused_builtin():
    if dir:  # Noncompliant
        pass

#
# Variables
#

#
# 1/ IMMUTABLE TYPES
# The following types are considered immutable from bool() perspective:
#     NoneType, int, float, bool, complex, Fraction, Decimal, str, tuple, unicode, frozenset, bytes, lambda, function, method, generator, generator expression, module.
#
# We will also consider that a "class" is always True, even if in theory it is possible to make it False using Metaclasses. This is extremely unlikely in our opinion.
#
# For immutanble types we consider that if a variable can only have one value and it is used as a condition, we should raise an issue.
#
def variables(param):
    if param:
        an_int = 1
    else:
        an_int = 2

    an_int = 0  # Overwrite all previus values
    if an_int:  # Noncompliant. an_int can only be 0
        pass

#
# Whatever the type of the value assigned to a variable, immutable or not, we don't consider it a constant if either:
# * it is referenced as "nonlocal" in a function we consider that it is not a constant.
# * it is defined in the global scope.
# * if the variable is captured from another scope
#
glob = 42
def nonlocal_reference():
    loc = 0
    def modifying():
        nonlocal loc
        loc = 2
    modifying()
    if loc:  # Ok. loc has been captured as nonlocal by a nested function
        print(loc)

    global glob
    if glob:  # Ok. glob is global
        print(glob)
    
    loc2 = 1
    def capturing_loc():
        if loc2:  # Ok. loc2 is captured from another scope
            pass

#
# If a variable with an immutable value is just captured, withut being nonlocal or global, we still consider it a constant.
#
def immutable_captured():
    loc = 1
    def different_variable_with_same_name():
        loc = 2
    different_variable_with_same_name()

    def capturing_without_modifying():
        print(loc + 42)
    capturing_without_modifying()

    if loc:  # Noncompliant
        print(loc)


#
# 2/ MUTABLE TYPES: (OUT OF SCOPE for now)
# We could consider any type non-immutable type as mutable. But there could be case were an object changes its state
# without us detecting it. Ex: because of Metaclasses.
# Once we implement this we should limit ourselves to the following types: list, set, dict.
#

def mutable_captured(a, b):
    b_list = []
    for i in range(a):
        b_list.append(i)

    if b_list:
        return b_list

    a_list = []

    for i in range(b):
        b_list.append(i)  # Typo. Should have been a_list

    if a_list:  # Out of scope for now. a_list is only set to an empty list and never modified nor passed to a function
        return a_list

# As soon as a mutable variable is referenced in a nested function, method or lambda we don't consider it a constant
def mutable_captured():
    def capturing():  # Note that the function is defined before the definition of the variable
        a_list.append(1)
    a_list = []
    capturing()
    if a_list:
        print("modified")


# As soon as there is a reference to a mutable variable between the assignment and the condition we can consider that it is not constant
def mutable_modified():
    def modify(lst):  # Note that the function is defined before the definition of the variable
        lst.append(1)
    a_list = []
    modify(a_list)  # reference to a_list
    if a_list:
        print("modified")


# if the condition is in a loop, consider the rest of the loop too
def mutable_modified_in_loop():
    def modify(lst):  # Note that the function is defined before the definition of the variable
        lst.append(1)
    a_list = []
    for i in range(2):
        if a_list:
            print("modified")
        modify(a_list)  # reference to a_list
