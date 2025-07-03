def parameter(p):
    p = 42  # NonCompliant
    return p


def forLoop(strings):
    for string in strings:
        string = "hello world"  # NonCompliant
        print(string)


def exception():
    try:
        z = x / y
    except ZeroDivisionError as e:
        e = 42  # NonCompliant
        raise e


def param_used_conditionally(p, cond):
    if cond:
        p = 42  # OK
    return p


def used_inside_nested_function(p):
    return lambda x: x + p  # OK

