def numbers(a):
    if a == 1:
        return 42
    return 42  # NonCompliant


def strings(a):
    if a == 1:
        return "foo"
    return "foo"  # NonCompliant


def identifiers(a):
    b = 12
    if a == 1:
        return b
    return b  # NonCompliant

def identifiers_ok(a):
    b = 12
    if a == 1:
        return b
    b += 1
    return b  # OK

# def walrus_param_override(a, b):  # uncomment this once walrus operator is supported
#     if (b := 12) == a:
#         return b
#     else:
#         return b  # NonCompliant

def one_return_value():
    return 42  # OK

def foo():
    for a in range(10):
        try:
            print("in try")
        finally:
            continue


def with_implicit_return(p):  
    if p:
        return 42
    elif not p:
        return 42  # OK
    # implicit return


lambda p: 1 if p else 1  # NonCompliant

def foo(a):  # NonCompliant
    b = 12
    c = 12
    if a == 1:
        return b
    return c