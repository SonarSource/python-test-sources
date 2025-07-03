# pylint: disable=missing-docstring, too-few-public-methods,pointless-statement, wildcard-import, unused-wildcard-import, using-constant-test, global-statement, function-redefined
# pylint: disable=expression-not-assigned


# https://github.com/PyCQA/pylint/issues/2621

vp1 = 1
if True:
    vp1 = 2

A1, B1 = (vp1,) + (3, ) # False Positive

A1, B1, C1 = (vp1,) + (3, ) # False Negative



def _fn_a3():
    vp1 = 1
    if True:
        vp1 = 2

    return (vp1,) + (3, )

A1, B1 = _fn_a3() # False Positive

A1, B1, C1 = _fn_a3() # False Negative


def _fn_a2():
    vp1 = 1
    # if True:
    vp1 = 2

    return (vp1,) + (3, )

A1, B1 = _fn_a2() # True Negative

A1, B1, C1 = _fn_a2() # True Positive


def func1():
    return 1,2,3

A, B, C, D = func1() # True Positive



# https://github.com/PyCQA/pylint/issues/2461

li = []
li.append(1)
li.append(2)
li.append(3)

A,B,C = li # False Positive