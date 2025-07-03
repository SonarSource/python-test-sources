# https://github.com/PyCQA/pylint/issues/626

unknown_var

try:
    raise ValueError()
except ValueError as e:
    pass  # False negative (unused-variable)

print(e)  # False Negative (undefined-variable e) (Pycharm, Mypy True Positive)


if False:
    condition_var = 0
else:
    print(condition_var)  # False Negative


# https://github.com/PyCQA/pylint/issues/624
# => Out of scope. Needs type inference and following the call stack

def test(x):
   return x.lala # not detected

test(1)

# https://github.com/PyCQA/pylint/issues/85

def myfunc(condition):
    if condition:
        print('message')
    else:
        res = 42
    print(res)  # False Negative
    
    try:
        if (condition):
            raise Exception('')
        res = 42
    finally:
        print(res)  # False Negative
