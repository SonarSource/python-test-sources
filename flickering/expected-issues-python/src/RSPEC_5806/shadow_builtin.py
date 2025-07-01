# Shadowing a builtin at global scope is ok. It is probably intentional.
# Multiple reasons exist for that:
# * supporting multiple versions of python
# * having a more readable API

int = 42  # Ok

def max():  # Ok
    pass

def process(object=[]):  # Ok
    pass

from math import exp as max  # Ok
import math as max  # Ok
# https://github.com/apache/airflow/blob/78e48ba46a7f721384417ebf8a798dd320632fa8/airflow/models/__init__.py#L26
from airflow.models.errors import ImportError  # Ok
from airflow.models.errors import *  # Ok

class Exception():  # Ok
    # class attributes and methods would only shadow builtins in
    # the rare case where some code is executed in the body of the class.
    # Thus we won't rase issues on class attributes and methods when their name
    # matches the name of a builtin.
    min = 42  # Ok
    def max(self):  # Ok
        int = 42  # Noncompliant

    def process(object=[]):  # Ok
        pass



def a_function():
    int = 42  # Noncompliant

    def max():  # Ok. Functions might be publicly accessible. Example: returned or assigned to a class.
        pass

    def process(object=[]):  # Ok.
        pass

    class Int:  # Ok. Classes might be publicly accessible.
        pass



def not_in_python2_and_python3():
    """We won't raise issues when builtin names exist only on python 2 or in python 3.
    To do this we need to know the exact version of python analyzed."""
    exec = 21  # False Negative. This doesn't exist in python 2.

    # As a first version we will just builtin names existing in both python 3.8 and python 2.7
    # This might create some False Positives for older versions of python.
    # The intersection result is: {'ArithmeticError', 'AssertionError', 'AttributeError', 'BaseException', 'BufferError', 'BytesWarning', 'DeprecationWarning', 'EOFError', 'Ellipsis', 'EnvironmentError', 'Exception', 'False', 'FloatingPointError', 'FutureWarning', 'GeneratorExit', 'IOError', 'ImportError', 'ImportWarning', 'IndentationError', 'IndexError', 'KeyError', 'KeyboardInterrupt', 'LookupError', 'MemoryError', 'NameError', 'None', 'NotImplemented', 'NotImplementedError', 'OSError', 'OverflowError', 'PendingDeprecationWarning', 'ReferenceError', 'RuntimeError', 'RuntimeWarning', 'StopIteration', 'SyntaxError', 'SyntaxWarning', 'SystemError', 'SystemExit', 'TabError', 'True', 'TypeError', 'UnboundLocalError', 'UnicodeDecodeError', 'UnicodeEncodeError', 'UnicodeError', 'UnicodeTranslateError', 'UnicodeWarning', 'UserWarning', 'ValueError', 'Warning', 'ZeroDivisionError', '__debug__', '__doc__', '__import__', '__name__', '__package__', 'abs', 'all', 'any', 'bin', 'bool', 'bytearray', 'bytes', 'callable', 'chr', 'classmethod', 'compile', 'complex', 'copyright', 'credits', 'delattr', 'dict', 'dir', 'divmod', 'enumerate', 'eval', 'filter', 'float', 'format', 'frozenset', 'getattr', 'globals', 'hasattr', 'hash', 'help', 'hex', 'id', 'input', 'int', 'isinstance', 'issubclass', 'iter', 'len', 'license', 'list', 'locals', 'map', 'max', 'memoryview', 'min', 'next', 'object', 'oct', 'open', 'ord', 'pow', 'print', 'property', 'range', 'repr', 'reversed', 'round', 'set', 'setattr', 'slice', 'sorted', 'staticmethod', 'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip'}


#
# Assigning a global variable in a function/method should not raise an issue.
# https://github.com/pypa/pipenv/blob/7745e51a63cbd17c7ba9ef9f75ec974f8b5543d1/pipenv/patched/notpip/_vendor/requests/status_codes.py#L115-L118
def redefine_global():
    global __doc__
    __doc__ = "test"  # Ok. This is a global variable

#
# Additional example of patterns used to support multiple versions of python
#

from sys import version_info
import six
# https://github.com/kashifh99/splunk/blob/4558eb043a43dad62867ae089d152bb81c279b6b/splunk/lib/python2.7/site-packages/slim/utils/internal.py#L17
if version_info.major >= 3:
    int = 42  # Ok
# https://github.com/alibaba/x-deeplearning/blob/04cc0497150920c64b06bb8c314ef89977a3427a/blaze/thirdparty/protobuf/protobuf-3.6.0/python/google/protobuf/text_format.py#L51
if six.PY3:
    int = 42  # Ok

# https://github.com/ndparker/gensaschema/blob/de269f761d0778269be5a42b1c0370cdbe5f452c/gensaschema/_util.py#L32-L38
try:
    int = 42  # Ok
except NameError:
    int = 42  # Ok
else:
    int = 42  # Ok
