# https://github.com/PyCQA/pylint/issues/267

def arf():
    dest = test + 3  # True Positive
    test = 1


def false_positive(condition):
    if condition:
        test = 1
        dest = test + 2
    else:
        dest = test + 3  # False Negative
        test = 1
