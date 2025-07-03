def foo(a, b, c):
    assert a, "ok"

    assert (a, ), "ok"
    assert (a, b), "ok"
    assert (a, b, c), "ok"
    assert (a, )
    assert ()

    assert (a, b) # Noncompliant
