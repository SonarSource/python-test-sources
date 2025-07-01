# pylint: disable=missing-docstring, too-few-public-methods,pointless-statement, wildcard-import, unused-wildcard-import, using-constant-test, global-statement, function-redefined
# pylint: disable=expression-not-assigned

# https://github.com/PyCQA/pylint/issues/2072
a1 = None
for i in range(1, 5):
    if i % 2:
        a1 = "foo"
    else:
        a1 = a1[1:] # No issue

a2 = None
for i in range(1, 5):
    if i % 2:
        a2 = "foo"
    if not i % 2:
        a2 = a2[1:] # No issue

a3 = None
for i in range(1, 5):
    if i % 2:
        a3 = "foo"
    elif not i % 2:
        a3 = a3[1:] # why is there an issue here?

a4 = None
if True:
    a4 = "foo"
elif False:
    a4 = a4[1:] # False Positive

# This is equivalent but it doesn't raise any issue
a5 = None
if True:
    a5 = "foo"
else:
    a5 = a5[1:] # True Negative


# https://github.com/PyCQA/pylint/issues/2016
def subscriptable(flag):
    state = None
    for _ in [0, 1]:
        if state is None:
            if flag:
                state = [None]
        elif state[0] is None:  # False Positive
            print('subscripted')


# https://github.com/PyCQA/pylint/issues/1498
a = None
while True:
    if a is None or a["1"] == 0:  # False Positive
        a = {"1":1}
    else:
        break


# https://github.com/PyCQA/pylint/issues/1498#issuecomment-511298935

def func_list(mylist=None):
    # if mylist is None:
    #     mylist = []
    # mylist.append(42)
    return mylist[0] # False negative