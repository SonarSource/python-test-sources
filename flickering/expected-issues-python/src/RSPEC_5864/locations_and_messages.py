#
# Up to now we have avoided listing types explicitely in issue messages because there might
# be some internal representation such as "Union[str, int]" when we are not sure about the type.
# I chose here to be consistent and let developers deduce type incompatibilities when they look
# at the type checks.
#

#
# We don't list every covered or out of scope case because these are described in the corresponding
# rules when type is certain.
#

def silly_equality_s2159(param1, param2):
    if not isinstance(param1, int):
#      ^^^^^^^^^^^^^^^^^^^^^^^^^^^ Secondary message: Inconsistent type check.
        return
    if isinstance(param2, str):
#      ^^^^^^^^^^^^^^^^^^^^^^^ Secondary message: Inconsistent type check.
       return param1 == param2  # Noncompliant
#             ^^^^^^^^^^^^^^^^  Primary message: Fix this equality check; Previous type checks suggest that operands have incompatible types.


def invalid_identity_check_s3403(param):
    if isinstance(param, str):
#      ^^^^^^^^^^^^^^^^^^^^^^ Secondary message: Inconsistent type check.
       return param is 42  # Noncompliant
#             ^^^^^^^^^^^  Primary message: Fix this "is" check; Previous type checks suggest that operands have incompatible types.


def operators_compatible_types_binary_s5607(param):
    if isinstance(param, str):
#      ^^^^^^^^^^^^^^^^^^^^^^ Secondary message: Inconsistent type check.
        return param + 42  # Noncompliant
#              ^^^^^^^^^^  Primary message: Fix this "+" operation; Previous type checks suggest that operands have incompatible types.


def operators_compatible_type_unary_s5607(param):
    if isinstance(param, str):
#      ^^^^^^^^^^^^^^^^^^^^^^ Secondary message: Inconsistent type check.
        return - param  # Noncompliant
#              ^^^^^^^  Primary message: Fix this "-" operation; Previous type checks suggest that the operand has an incompatible type.


def calling_non_callable_s5756(param):
    if isinstance(param, str):
#      ^^^^^^^^^^^^^^^^^^^^^^ Secondary message: Inconsistent type check.
        return param()  # Noncompliant
#              ^^^^^^^  Primary message: Fix this call; Previous type checks suggest that "param" is not callable.


def item_operation_s5644(param):
    if isinstance(param, int):
#      ^^^^^^^^^^^^^^^^^^^^^^ Secondary message: Inconsistent type check.
        return param[2]  # Noncompliant
#              ^^^^^^^^  Primary message: Fix this __getitem__ operation; Previous type checks suggest that "param" does not have this method.


def invalid_unpacking_s3862(param):
    if isinstance(param, int):
#      ^^^^^^^^^^^^^^^^^^^^^^ Secondary message: Inconsistent type check.
        a, b = param  # Noncompliant
#              ^^^^^  Primary message: Fix this unpacking; Previous type checks suggest that "param" is not iterable.


def invalid_loop_iteration_s3862(param):
    if isinstance(param, int):
#      ^^^^^^^^^^^^^^^^^^^^^^ Secondary message: Inconsistent type check.
        for a in param:  # Noncompliant
#                ^^^^^  Primary message: Fix this iteration; Previous type checks suggest that "param" is not iterable.
            pass


def invalid_constant_condition_s5797(param):
    if isinstance(param, type):  # param is a class
#      ^^^^^^^^^^^^^^^^^^^^^^^ Secondary message: Inconsistent type check.
        if param:  # Noncompliant
#          ^^^^^  Primary message: Fix this condition; Previous type checks suggest that it is constant.
            pass


def identity_rely_on_cache_s5795(param1, param2):
    if isinstance(param1, int):  # param is a class
#      ^^^^^^^^^^^^^^^^^^^^^^^ Secondary message: Inconsistent type check.
        if param1 is param2:  # Noncompliant
#          ^^^^^^  Primary message: Fix this condition; Previous type checks suggest that it relies on interpreter's cache.
            pass


def raise_base_exception_s5632(param):
    if isinstance(param, str):
#      ^^^^^^^^^^^^^^^^^^^^^^ Secondary message: Inconsistent type check.
        raise param  # Noncompliant
#       ^^^^^^^^^^^  Primary message: Fix this "raise" statement; Previous type checks suggest that "param" is not an exception.



def accessing_non_existing_member_s5755(param):
    if isinstance(param, int):
#      ^^^^^^^^^^^^^^^^^^^^^^ Secondary message: Inconsistent type check.
        return param.foo  # Noncompliant
#              ^^^^^^^^^  Primary message: Fix this member access; Previous type checks suggest that "param" does not have a member named "foo".


###################################################
# Once we handle type annotations inside a project.
#
# This design might change. The idea here is just
# to see if this design can evolve for our future
# needs.
###################################################

def silly_equality_s2159(param1: int, param2: str):
#                                             ^^^ Secondary message: Inconsistent type check.
#                                ^^^ Secondary message: Inconsistent type check.
    return param1 == param2  # Noncompliant
#          ^^^^^^^^^^^^^^^^  Primary message: Fix this equality check; Previous type checks suggest that operands have incompatible types.


###################################################
# Secondary locations for function return types.
###################################################

def function_return_types(x):
    if not isinstance(x, str):
    #  ^^^^^^^^^^^^^^^^^^^^^^ Secondary message: Inconsistent type check.
        return
    y = round(1.5)
    #   ^^^^^^^^^^ Secondary message: "round return type is 'int'"
    x + y  # Noncompliant. Fix this "+" operation; Previous type checks suggest that operands have incompatible types.

#
# Let's try an even more complex case just to see if our messages are still understandable.
#
# Is the issue understandable if we highlight just the last type annotation giving us a clue?
# We can probably do something more complex but the idea is to keep things simple.
#

# https://docs.python.org/3/library/typing.html#typing.Generator
from typing import Generator

my_generator_type = Generator[str, None, None]  # Maybe we should add some secondary locations here but it is a nice to have

def silly_equality_s2159(param: int, generator: my_generator_type):
#                                               ^^^^^^^^^^^^^^^^^ Secondary message: Inconsistent type check.
#                               ^^^ Secondary message: Inconsistent type check.
    for value in generator:  # here we deduce that value is a str, should we say it?
        if value == param:  # Noncompliant
#          ^^^^^^^^^^^^^^  Primary message: Fix this equality check; Previous type checks suggest that operands have incompatible types.
             return True
