#pylint: disable=pointless-statement

# Corresponding pylint ticket: https://github.com/PyCQA/pylint/issues/786


def literal_comparison(param):
    # dict
    param is {1: 2, 3: 4}  # Noncompliant
    # list
    param is [1, 2, 3]  # Noncompliant
    # set
    param is {1, 2, 3}  # Noncompliant

    # issues are also raised for "is not"
    param is not {1: 2, 3: 4}  # Noncompliant
    param is not [1, 2, 3]  # Noncompliant
    param is not {1, 2, 3}  # Noncompliant

    # issues are raised when literals are on the right or on the left of the operator
    {1} is param  # Noncompliant


def builtin_constructor(param):
    """We can't raise on every constructor because some might always return the same object (singletons).
    However we can raise on builtin functions because we know that they won't return the same value.
    """
    # dict
    param is dict(a=2, b=3)  # Noncompliant
    # list
    param is list({4, 5, 6})  # Noncompliant
    # set
    param is set([1, 2, 3])  # Noncompliant
    # complex
    param is complex(1, 2)  # Noncompliant

glob = 5
def variable(param):
    """
    We also raise an issue when
    * one of the literals or calls previously mentionned are assigned to a
    variable
    * AND the variable is assigned only once.
    * AND this variable is ONLY referenced in the identity check.
    * AND the variable is not global.
    """
    mylist = []
    param is mylist  # Noncompliant

    referenced = []
    def referencing():
        nonlocal referenced
        referenced = param
        param is referenced  # No issue

    referencing()
    param is referenced  # No issue

    reassigned = []
    reassigned = param
    param is reassigned  # No issue

    global glob
    param is glob  # No issue


def is_none():
    a = list()
    if a is None:  # Only S5727 should raise
        pass

def different_types():
    a = []
    if a is "":  # Only S3403 should raise an issue
        pass