from math import *

def gen(param):
    """Yield statements have a side effect."""
    yield 42


async def statements_having_effects_or_meant_to_be_ignored(param):
    """Other statements having a side effect or are meant to be ignored."""
    ...
    pass
    await param
    param()
    x = lambda: param
    (lambda: 2)()
    return 1


def literals():
    True  # Noncompliant
    False  # Noncompliant
    None  # Noncompliant
    1  # Noncompliant
    1.1  # Noncompliant
    [1, 2]  # Noncompliant
    {1, 2}  # Noncompliant
    {1: 1, 2: 2}  # Noncompliant


def str_liters():
    """
    IMPORTANT: issues are raised on strings only if "reportOnStrings" parameter is enabled.
    Sometime strings are used as comments.
    Example: https://github.com/inveniosoftware/invenio-app/blob/867f3c33e8dd1b4fc31ff2ba6761ee580532ada3/invenio_app/config.py#L26
    """

    "str"  # Noncompliant


class MyClass:
    attr = 42

    def method(self):
        pass

    @classmethod
    def class_method(cls):
        pass

    @staticmethod
    def static_method():
        pass

class CustomException(TypeError):
    pass


def a_function():
    pass

def non_called_functions_and_classes():
    """Classes and functions which are not called."""
    round  # Noncompliant
    a_function  # Noncompliant

    MyClass  # Noncompliant
    NotImplemented  # Noncompliant

    # No issue will be raised on Exception classes. This use case is covered by S3984
    BaseException  # Ok
    Exception  # Ok
    ValueError  # Ok
    CustomException  # Ok


def lambdas():
    """Creating a lambda which is not assigned."""
    lambda: 2  # Noncompliant


def parameters_and_variables(param):
    """Referencing a variable or parameter without actually calling a method on it."""
    param  # Noncompliant
    x = 3
    x  # Noncompliant

def multiple_statements(param, func):
    # multiple statements on one line
    return func(42); param  # Noncompliant, "param" has no effect


def binary_op(param):
    """Binary and unary operators are expected to have no side effect.
    However they can have one when special methods are overriden. Example: Apache Beam overrides ">>" and "|" operators.
    It is possible to disable issues on specific operators by listing them in the rule parameter "ignoredOperators"
    Example: https://github.com/apache/beam/blob/85259c2c48020864607f9bed773b92565b50516e/sdks/python/apache_beam/runners/portability/flink_runner_test.py#L283
    """
    param < 1  # Noncompliant
    param + param  # Noncompliant
    + param  # Noncompliant
    - param  # Noncompliant


def identity_op(param):
    """Identity operator"""
    param is None  # Noncompliant. False Negative.
    param is not None  # Noncompliant. False Negative.


def accessing_members(param):
    """
    Sometime members are accessed on purpose.
    Example: to force lazy loading. (https://github.com/tensorflow/tensorflow/blob/5c00e793c61860bbf26778cd4704313e867645be/tensorflow/api_template_v1.__init__.py#L68)
    This is why we will only raise issues when on methods which are not called and class attributes.

    Note: Accessing a member without doing any function call is still confusing so we might have a
    rule dedicated to that later.
    """
    MyClass.attr  # Noncompliant. False Negative.
    MyClass.class_method  # Noncompliant
    MyClass.static_method  # Noncompliant
    MyClass.__eq__  # Noncompliant

    if MyClass.class_method:
        pass


def comprehensions(param):
    """
    Some developers use comprehensions to have side effect.
    This is a bad design and should be replaced with a loop.
    However it is a code smell so this won't be covered by this rule.
    """
    [a() for a in param]  #  Ok. This is a code smell, not a bug

a = 42
class MyClass2:
    """Issues are also raised on useless statements in class body."""
    42  # Noncompliant
    a  # Noncompliant

    b: int  # Ok
    c = 21  # Ok


42  # Noncompliant. Issues are also raised on useless statements in global scope.


def tryExcept(param):
    """No issue is raised when the statement is the only statement in a try...except body.
    Such pattern indicates that the statement is expected to raise an exception in some contexts.
    """
    try:
        MyClass.attr
    except AttributeError as e:
        pass


def callsInSubExpression(param, func):
    """Don't raise any issue on boolean expressions if a call is made anywhere in it.
    Boolean expressions behave like a if...else and we don't know if the goal was to assign the result.
    We should however have a separate code smell rule in this case.
    """
    param and param()  # Ok. Note: Pylint raises on this

    param and param + 1  # Noncompliant


def conditional_expression(func):
    """
    Conditional Expressions are a special case because they are used to return something.
    Not assigning its result is probably a bug.
    """
    1 if True else 2  # Noncompliant
    1 if True else func()  # Ok. This is sometime used instead of a normal if...else. We should probably have a separate code smell rule for that.

    # Careful not to mix conditional expressions with normal if...else
    if True:
        1  # Noncompliant
    else:
        func()  # Ok


def tryExcept(a, b):
    """No issue is raised when the statement is THE ONLY statement in a try...except body.
    Such pattern indicates that the statement is expected to raise an exception in some contexts.
    """
    try:
        a + b
    except IndexError as e:
        a + b  # Noncompliant. False Negative


from contextlib import suppress

def supressExcept(a):
    with suppress(TypeError):
        a + ''  # False positive
        return a


# If a module is referenced once without being used it is generally
# to avoid the "unused import" warning from flake8 or Pylint.
# We will make an exception for now to smooth the transition
# between these linters and SonarLint.
import collections
collections  # Ok.