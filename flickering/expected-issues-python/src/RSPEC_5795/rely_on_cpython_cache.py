#pylint: disable=pointless-statement

# Corresponding pylint ticket: https://github.com/PyCQA/pylint/issues/786


def literal_comparison(param):
    """
    The following literals will generally create a single object.
    Thus `2000 is 2000` will be True. But when the same value is created another way the object MIGHT be different.
    Ex: `int("2000") is 2000` will be False. Thus we should not use the identity operator with these types, even
    if they are literals.

    Note that not every type is listed here. Only immutable types which can be cached.
    """
    # int
    param is 2000  # Noncompliant
    # bytes
    param is b"a"  # Noncompliant
    # float
    param is 3.0  # Noncompliant

    # str
    param is "test"  # Noncompliant
    param is u"test"  # Noncompliant

    # tuple
    param is (1, 2, 3)  # Noncompliant

    # issues are also raised for "is not"
    param is not 2000  # Noncompliant

    # issues are raised when literals are on the right or on the left of the operator
    2000 is param  # Noncompliant


def functions_returning_cached_types(param):
    """
    Some functions return types which are partially cached. Thus we can't rely on the identity of these returned values.

    Note: other linters don't cover these cases.
    Example of real world issue: https://github.com/KDE/krita/blob/b62774bd0af6b98040b2ca260beed5e488ba8a7a/plugins/python/comics_project_management_tools/comics_metadata_dialog.py#L748
    """
    # int
    param is int("1000")  # Noncompliant. int(1) is cached. int("1000") is not.

    # bytes
    param is bytes(1)  # Noncompliant. bytes() is cached. bytes(1) is not.

    # float
    param is float("1.0")  # Noncompliant

    # str
    param is str(1000)  # Noncompliant. str() is cached. str(1) is not.

    # tuple
    param is tuple([1, 2, 3])  # Noncompliant. tuple() is cached. tuple([1]) is not.

    # frozenset
    param is frozenset([1, 2, 3])  # Noncompliant. frozenset() is cached. frozenset([1]) is not.

    # This is also true when the value is returned by a callable
    param is hash("a")  # Noncompliant.
    # For example: the result of hash(0) is a cached value but hash("a") is not.


def variables(param):
    # For integer, floats and bytes it is never a good idea to use identity operators.
    var = 1
    param is var  # Noncompliant

    # For tuple and string it might happen that a value is used as a sentinel.
    # Pylint has an exception for this.
    # https://github.com/PyCQA/pylint/blob/527db314ecc00ad79be083dcca6134bb68c3bb60/tests/functional/l/literal_comparison.py#L47-L50
    # Let's see what happens on Peach and adjust.
    # TO learn more aboud Sentinels see https://www.revsys.com/tidbits/sentinel-values-python/
    SENTINEL = (0, 1)
    param is SENTINEL  # Noncompliant, but might be noisy
    SENTINEL is param  # Noncompliant, but might be noisy


def compliant_bool(param):
    """No issue for booleans because they are singletons.
    This pattern can be used to avoid automatic conversion from int/float to bool
    when using == and != operators.
    """
    param is True
    param is False

    param is bool(1)


def compliant_none(param):
    """No issue for None as it is a singleton. This is in fact the recommended
    way to check for None values.
    """
    param is None


def noncompliant_even_if_it_works_with_cpython(param):
    """
    As far as I have seen an empty tuple and empty strings always have the same identity.
    It is also the case of simple numbers up to 256.
    However this is not part of the language, it depends on the implementation of the interpreter.
    It is still better to use == or !=

    If we see that this creates a lot of noise on Peach we can make an exception for these cases.
    """
    param is ()  # Noncompliant
    param is tuple()  # Noncompliant
    param is ""  # Noncompliant
    param is 1  # Noncompliant


def default_param(param=(0, 1)):
    """We might encounter this use case: checking if a parameter has the default value using identity operators.
    When a parameter has a default value being a literal string or tuple, it is possible
    to check if the parameter has the default value with identity. This is still a bad idea as empty
    tuples are cached, and nothing prevents CPython from caching other values. Yet it could create some noise.
    Let's keep this as Noncompliant for now and see what Peach shows."""
    print(param is (0, 1))  # Noncompliant, even if it works in this case