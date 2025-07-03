# https://github.com/PyCQA/pylint/issues/2631

a = None
if a is not None:
    print("%d" % (a,)) # False Positive