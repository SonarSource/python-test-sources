def foo(a, b, c):
    """Having more than 2 parameters in an assert statement is a syntax error and is out of scope."""
    pass
    # assert a, b, "invalid syntax"  # no issue
    # assert a, b, c, "invalid syntax"  # no issue
