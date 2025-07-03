# https://github.com/PyCQA/pylint/issues/2880

# pylint: disable=missing-docstring, too-few-public-methods,pointless-statement, wildcard-import, unused-wildcard-import, using-constant-test, global-statement
# pylint: disable=expression-not-assigned

order = [0]
j = None
for i in range(10):
    if j is not None:
        order[j] += 1 # False Positive
    else:
        j = i

i = None
for i in range(10):
    order[i] += 1  # True Negative

i = None
i = 1
order[i] += 1  # True Negative

i = 1
i = None
order[i] += 1 # True Positive (False Negative on Pylint)

i = None
if (True):
    i = 1
order[i] += 1  # True Negative

a = None
a[1] = 3