# https://github.com/PyCQA/pylint/blob/97f4f2ae187df933f072d74fd8347ec14213f5de/tests/functional/n/none_dunder_protocols_py36.py
# pylint: disable=missing-docstring, too-few-public-methods,pointless-statement, wildcard-import, unused-wildcard-import, using-constant-test, global-statement
# pylint: disable=expression-not-assigned

from .definitions import *


1 in NonIterableClass  # [unsupported-membership-test]
1 in OldNonIterableClass  # [unsupported-membership-test]
1 in NonContainerClass # [unsupported-membership-test]
1 in NonIterableClass()  # [unsupported-membership-test]
1 in OldNonIterableClass()  # [unsupported-membership-test]
1 in NonContainerClass()  # [unsupported-membership-test]

li = []
'a' in li

foo = None
'a' in foo  # [unsupported-membership-test]

def li_func():
    return []
'a' in li_func()


def none_func():
    return None
'a' in none_func() # really good [unsupported-membership-test]


def none_func2(param):  # [unsupported-membership-test]
    if param:
        return None
    else:
        return None

'a' in none_func2() # False Negative


def none_param(param):
    'a' in param  # False Negative

none_param(None)

prop1 = None
exists = prop1 and 'a' in prop1  # False Postive (will not run the "'a' in prop" part)


prop2 = []
if True:
    prop2 = None
exists = 'a' in prop2  # False Negative

prop3 = []
prop3 = None
exists = 'a' in prop3  # [unsupported-membership-test]

prop4 = None
prop4 = []
exists = 'a' in prop4  # Ok. True Negative


class MyClass:
    _all = None

    @classmethod
    def all(cls):
        cls._all = []
        return cls._all

2 in MyClass.all() # False Positive https://github.com/PyCQA/pylint/issues/3045

class MyClass2:
    all = None

def all():
    MyClass2.all = []
    return MyClass2.all

2 in all() # False Positive https://github.com/PyCQA/pylint/issues/3045


all = None
def func():
    global all
    if not all:
        all = []
    return all
2 in func()