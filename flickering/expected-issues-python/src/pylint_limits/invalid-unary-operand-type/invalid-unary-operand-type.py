from typing import Optional

a = None
if a is None:
    a = 1
b = -a # False Positive

# https://github.com/PyCQA/pylint/issues/1472
def frob(value: Optional[int] = None):
    if value is not None:
        return -value # False Positive
    return value

frob(42)