def foo(a, b):
    assert (a, b) # Noncompliant
    #      ^^^^^^  Primary message: Fix this assertion on a tuple literal; did you mean "assert A, B"?
