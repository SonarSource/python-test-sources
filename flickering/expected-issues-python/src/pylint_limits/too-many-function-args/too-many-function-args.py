
# pylint: disable=missing-docstring, too-few-public-methods,pointless-statement, wildcard-import, unused-wildcard-import, using-constant-test, global-statement
# pylint: disable=expression-not-assigned


# https://github.com/PyCQA/pylint/blob/527db314ecc00ad79be083dcca6134bb68c3bb60/tests/functional/u/unpacking_generalizations.py
def func_variadic_args(*args):
    return args


def func_variadic_positional_args(a, b, *args):
    return a, b, args

def func_positional_args(a, b, c, d):
    return a, b, c, d

func_positional_args(*(2, 3, 4), *(2, 3)) # [too-many-function-args]
func_positional_args(1, *(2, ), 3, *(4, 5)) # [too-many-function-args]



# https://github.com/PyCQA/pylint/blob/d39f7abc50bebd46bec51d4776b622b5176d3420/tests/functional/a/arguments.py#L47
def function_1_arg(first_argument):
    """one argument function"""
    return first_argument

def function_3_args(first_argument, second_argument, third_argument):
    """three arguments function"""
    return first_argument, second_argument, third_argument


function_1_arg(420)
function_1_arg()  # [no-value-for-parameter]
function_1_arg(1337, 347)  # [too-many-function-args]
function_3_args()
function_3_args(1337, 347, 456)
function_3_args('bab', 'bebe', None, 5.6)  # [too-many-function-args]


# https://github.com/PyCQA/pylint/issues/2826

def function_0_arg():
    """one argument function"""
    return None

var = function_0_arg
var()  # True Negative
def func():
    global var
    var = function_1_arg
var()  # True Negative


# https://github.com/PyCQA/pylint/issues/1123
# => Monkey patching a class

class A:
    def get_stuff(self, x):
        return x


def test1():
    def g():
        pass
    a = A()
    a.get_stuff = g
    a.get_stuff() # True Negative for Pylint (False Positive for PyCharm)
    a.get_stuff(1) # True Positive for Pylint (False Negative for PyCharm)


def test2():
    a = A()
    value = a.get_stuff(1) # False Positive (True Negative for PyCharm)