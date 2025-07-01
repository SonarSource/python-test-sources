#  Pylint tests: https://github.com/search?l=&p=1&q=no-member+repo%3APyCQA%2Fpylint+extension%3Apy+path%3Atests%2Ffunctional%2F&ref=advsearch&type=Code

##############
# In scope
##############

# Note: We focus on attribute accessed on instances of objects. We don't include attribute access on "self" or "cls" in classes.

#########################
# "Attribute-Fixed" types
#########################

# Some types cannot have attributes added. Let's call them "Attribute-Fixed"
# (this is not an official name, and "immutable" would be confusing").
# These types are (probably incomplete list as they were tested manually):
# * None, bool, int, float, complex, str, bytes, bytearray, list, dict, set, frozenset, range, NotImplemented, zip
# * decimal.Decimal, fractions.Fraction
#
# To test if a class is "Attribute-Fixed" simply do the following (here for int)
# x = 5
# x.unknown = 42  # This will fail if it is "Attribute-Fixed"


# Typeshed should list all existing properties for "Attribute-Fixed" types.
# Accessing any member which is not defined will raise an issue, be it for READ or WRITE access.
#
from decimal import Decimal
from fractions import Fraction

def access_builtin_attribute_bad(param):
    i = 42
    i.unknown = 5  # Noncompliant
    print(i.isnumeric())  # Noncompliant
    f = 1.2
    f.unknown  # Noncompliant
    s = "str"
    s.unknown  # Noncompliant
    byte = b'\x00\x10'
    byte.unknown  # Noncompliant
    ba = bytearray(b'\xf0\xf1\xf2')
    ba.unknown  # Noncompliant
    l = []
    l.unknown  # Noncompliant
    se = {1,2}
    se.unknown  # Noncompliant
    d = {1:2}
    d.unknown  # Noncompliant
    fr = frozenset()
    fr.unknown  # Noncompliant
    r = range()
    r.unknown  # Noncompliant
    n = NotImplemented
    n.unknown  # Noncompliant
    z = zip()
    z.unknown  # Noncompliant

    frac = Fraction(1,2)
    frac.unknown  # Noncompliant
    dec = Decimal(1)
    dec.unknown  # Noncompliant

    if isinstance(param, int):
        param.patched = 42  # Noncompliant
        print(param.isnumeric())  # Noncompliant

    if param is None:
        param.unknown  # Noncompliant.


def access_builtin_attribute_ok(param):
    x = "42"
    print(x.isnumeric())

    if isinstance(param, str):
        param.patched = 42


##############
# Custom types
##############

#
# When an attribute is not referenced in a class it is unknown for READ access but ok for WRITE access
#
class MyClassNoAttribute:
    pass

def access_MyClassNoAttribute(param):
    m = MyClassNoAttribute()
    m.unknown  # Noncompliant
    m.other_unknown = 42  # Ok. This adds the property to the instance's __dict__

    if isinstance(param, MyClassNoAttribute):
        param.unknown  # Noncompliant
        param.other_unknown = 42  # Ok

#
# When an attribute is referenced in a class it is known for both READ and WRITE access, even if it is never set.
# This is to avoid false positives on Mixins which can access attributes set in subclasses.
# See https://coderbook.com/@marcus/deep-dive-into-python-mixins-and-multiple-inheritance/
# This is better than relying on class name as Pylint is doing:
# https://github.com/PyCQA/pylint/blob/527db314ecc00ad79be083dcca6134bb68c3bb60/tests/functional/c/class_members_py30.py#L19
#
class MyClassHasAttribute:
    def __init__(self):
        self.set()

    def set(self):
        self.known = 42

def access_MyClassHasAttribute(param):
    m = MyClassHasAttribute()
    print(m.known)

    if isinstance(param, MyClassHasAttribute):
        print(param.known)

# Mixin example
class MyMixin(object):
    """Mixin to enhance subclasses"""
    def get_subject(self):
        return str(self.attribute)

class UsesMixin(MyMixin):
    attribute = 42

def access_UsesMixin(param):
    if isinstance(param, MyMixin):
        print(param.attribute)  # Ok, even if the attribute is not set in MyMixin

#
# No issue is raised on attribute READ when the attribute is WRITTEN to before, even if
# it is never referenced in the class.
#
class ModifiedInstance:
    pass

def access_ModifiedInstance(param):
    h = ModifiedInstance()
    h.patched = 42  # Ok
    print(h.patched)  # Ok

    if isinstance(param, ModifiedInstance):
        param.patched = 42  # Ok
        print(param.patched)  # Ok

#
# When an attribute or method is defined in a parent class, they are accessible in subclasses
#
class HasMethod:
    def method(self):
        print("method")

class SubHasMethod(HasMethod):
    pass

def access_method(param):
    h = SubHasMethod()
    h.method()

    if isinstance(param, HasMethod):
        param.method()

    if isinstance(param, SubHasMethod):
        param.method()


#
# When an attribute or method is defined in a subclass, it is not accessible in the parent class
#
class HasNoMethod:
    pass

class MethodAdded(HasNoMethod):
    def method(self):
        print("method")

def access_method_from_subclass(param):
    h = HasNoMethod()
    h.method()  # Noncompliant

    if isinstance(param, HasNoMethod):
        param.method()  # Noncompliant

    if isinstance(param, MethodAdded):
        param.method()


#
# Class attributes are available in class instances.
#
class HasClassAttributes:
    attr = 42

def access_HasClassAttributes():
    h = HasClassAttributes()
    print(h.attr)
    print(h.unknown)  # Noncompliant


#
# If there is an unset attribute with just an annotation we consider that it will exist later somehow.
# Related Pylint False Positive: https://github.com/PyCQA/pylint/issues/3143
#
def lazy_initialization_of_a_class():
    class Top:
        x: str

        @classmethod
        def init(cls):
            cls.x = "a value"  # x is created on demand. Not during the class definition

    class Bottom(Top):
        pass

    Top.init()  # Initializing
    print(Bottom().x)  # False Positive to avoid

#
# We should not raise any issue if a class has an annotated class attribute.
# The field might exist at runtime even if the class doesn't set it explicitly.
# Related Pylint False Positive: https://github.com/PyCQA/pylint/issues/3167
#
class AnnotatedAttribute:
    myfield: int

class SubAnnotatedAttribute(AnnotatedAttribute):
    pass

def access_SubAnnotatedAttribute():
    x = SubAnnotatedAttribute()
    x.myfield  # False Positive to avoid


#
# When a custom class has a __slots__ class attribute, it can be considered as "Attribute-Fixed".
# We raise an issue when all the following are true:
# * we set an attribute
# * the class has a __slots__ attribute
# * the accessed member is not in the __slots__ list/tuple/set
# * there is no method or class attribute with this name
#
# See also the Out of scope part
class HasSlots:
    __slots__ = ['known']  # Secondary location here

    def method(self):
        self.another_unknown = 5  # Noncompliant


def access_HasSlots(param):
    h = HasSlots()
    h.unknown = 42  # Noncompliant
    print(h.unknown)  # No issue as the attribute was set.
    # This follows the rule of "attribute set. Attribute available" and avoids having duplicate issues.

    if isinstance(param, HasSlots):
        param.unknown = 42  # Noncompliant
        print(param.unknown)  # No issue as the attribute was set.


#
# Some "special" attributes and methods exist even for empty instances.
# We should never raise when these are accessed.
#

class Empty:
    pass

dir(Empty())
def access_special_methods():
    e = Empty()
    print(e.__subclasshook__)
    print(e.__unknown__)  # Noncompliant
# This gives the following list of methods and attributes existing in every object:
# __class__, __delattr__, __dict__, __dir__, __doc__, __eq__, __format__, __ge__,
# __getattribute__, __gt__, __hash__, __init__, __init_subclass__, __le__, __lt__,
# __module__, __ne__, __new__, __reduce__, __reduce_ex__, __repr__, __setattr__,
# __sizeof__, __str__, __subclasshook__, __weakref__

#
# No issue is raised when a class has the __getattribute__
#
class HasGetattribute:
    def __getattribute__(self, key):
        return 42

def access_HasGetattribute(param):
    m = HasGetattribute()
    print(m.unknown)  # False Positive to avoid

    if isinstance(param, HasGetattribute):
        print(param.unknown)  # False Positive to avoid

#
# No issue is raised when a class has the __getattribute__
#
class HasGetattr:
    def __getattr__(self, key):
        return 42

def access_HasGetattr(param):
    m = HasGetattr()
    print(m.unknown)  # False Positive to avoid

    if isinstance(param, HasGetattr):
        print(param.unknown)  # False Positive to avoid

#
# No issue when setattr is used in the class or one of its parent classes.
# We can't know if setattr is used in classes defined by typeshed and that's ok.
#
# Example: MagicMock defines __index__ using setattr
# https://github.com/python/cpython/blob/518835f3354d6672e61c9f52348c1e4a2533ea00/Lib/unittest/mock.py#L2065
#
class UseSetattr:
    def __init__(self):
        setattr(UseSetattr, "myattr", 42)

def access_UseSetattr(param):
    m = UseSetattr()
    print(m.myattr)  # False Positive to avoid

    if isinstance(param, UseSetattr):
        print(param.myattr)  # False Positive to avoid


#
# No issue is raised when AttributeError is caught
#
def catch_attribute_error(param):
    if isinstance(param, list):
        try:
            print(param.unknown)  # False Positive to avoid. Always raising but maybe intentional.
        except AttributeError:
            print(param.unknown)  # Noncompliant

#
# No issue is raised when hasattr is used
#
def use_hasattr(param):
    if isinstance(param, list):
        if hasattr(param, "isnumeric"):  # Always false, this will be in a different rule
            print(param.isnumeric)  # False Positive to avoid



################################################
# Out of scope / Cases when the rule is disabled
################################################

# Out of Scope: Supporting type of __slots__ different from list, set and tuple.
# We should only try to read the __slots__ attribute if it is a list or a tuple.
# We don't raise any issue if we are not able to guess the value of __slots__.
#
# Related Mypy False Positive: https://github.com/python/mypy/issues/5941
from collections import UserList

class HasStrangeSlots:
    __slots__ = UserList(['a'])

def access__HasStrangeSlots():
    strange = HasStrangeSlots()
    strange.a = 10
    strange.a  # False Positive to avoid
    strange.b  # False Negative


#
# Out of scope: detect attributes added by modifying setattr
# No issue will be raised on instances of class using "setattr"
#

class UseSetAttr:
    def __init__(self):
        self.add_attribute("known", 42)
        self.add_class_attribute("class_known", 21)

    def add_attribute(self, key, value):
        setattr(self, key, value)
    
    @classmethod
    def add_class_attribute(cls, key, value):
        setattr(cls, key, value)

def access_UseSetAttr():
    x = UseSetAttr()
    print(x.known)  # False Positive to avoid
    print(x.class_known)  # False Positive to avoid
    print(x.unknown)  # False Negative

#
# Same thing when __setattr__ is used.
# Pylint test: https://github.com/PyCQA/pylint/blob/527db314ecc00ad79be083dcca6134bb68c3bb60/tests/functional/c/class_members_py30.py#L27
#
class Use__setattr__(object):
    def __init__(self):
        self.__setattr__('known', '42')

def access_Use__setattr__():
    x = Use__setattr__()
    print(x.known)  # False Positive to avoid
    print(x.unknown)  # False Negative

#
# Out of scope: detect attributes added by modifying __dict__
# No issue is raised when __dict__ is modified in a class
#
class ModifiesDict:
    def __init__(self):
        self.__dict__['known'] = 42

def access_ModifiesDict(param):
    h = ModifiesDict()
    print(h.known)  # False Positive to avoid
    print(h.unknown)  # False Negative

    if isinstance(param, ModifiesDict):
        param.known  # False Positive to avoid
        param.unknown  # False Negative

#
# No issue is raised on Classes defining the __dir__ method
# and their subclasses.
# Class defining __dir__ want to customize the list of attribute.
# It indicates that some magic is probably going on.
#
class HasDir:
    def __dir__(self):
        return ["known"]

setattr(HasDir, "known", 42)

def access_HasDir(param):
    h = HasDir()
    print(h.known)  # False Positive to avoid
    print(h.unknown)  # False Negative

    if isinstance(param, HasDir):
        param.known  # False Positive to avoid
        param.unknown  # False Negative

#
# Out of scope: detect when an attribute is read but never written
# In theory an attribute is not set in the class it is unknown for READ access. Other linters to it.
# However this would raise issues on Mixins. Thus we will avoid to do it, for now at least.
#
class MyClassAttributeNotSet:
    def get(self):
        return self.notset  # False Negative

def access_MyClassAttributeNotSet(param):
    m = MyClassAttributeNotSet()
    m.notset  # False Negative

    if isinstance(param, MyClassAttributeNotSet):
        param.notset  # False Negative


#
# Out of scope: Checking members of functions/methods and classes.
# Custom functions and methods can be monkeypatched to add attributes. This is sometime used by decorators.
#
# Note for later: It not possible to set attributes on the following functions/classes:
# * ArithmeticError, AssertionError, AttributeError, BaseException, BlockingIOError, BrokenPipeError, BufferError,
# * BytesWarning, ChildProcessError, ConnectionAbortedError, ConnectionError, ConnectionRefusedError,
# * ConnectionResetError, DeprecationWarning, EOFError, EnvironmentError, Exception, FileExistsError, FileNotFoundError,
# * FloatingPointError, FutureWarning, GeneratorExit, IOError, ImportError, ImportWarning, IndentationError, IndexError,
# * InterruptedError, IsADirectoryError, KeyError, KeyboardInterrupt, LookupError, MemoryError, ModuleNotFoundError,
# * NameError, NotADirectoryError, NotImplementedError, OSError, OverflowError, PendingDeprecationWarning,
# * PermissionError, ProcessLookupError, RecursionError, ReferenceError, ResourceWarning, RuntimeError, RuntimeWarning,
# * StopAsyncIteration, StopIteration, SyntaxError, SyntaxWarning, SystemError, SystemExit, TabError, TimeoutError,
# * TypeError, UnboundLocalError, UnicodeDecodeError, UnicodeEncodeError, UnicodeError, UnicodeTranslateError,
# * UnicodeWarning, UserWarning, ValueError, Warning, ZeroDivisionError, abs, all, any, ascii, bin, bool, breakpoint,
# * bytearray, bytes, callable, chr, classmethod, compile, complex, delattr, dict, dir, divmod, enumerate, eval, exec,
# * filter, float, format, frozenset, get_ipython, getattr, globals, hasattr, hash, hex, id, input, int, isinstance,
# * issubclass, iter, len, list, locals, map, max, memoryview, min, next, object, oct, open, ord, pow, print, property,
# * range, repr, reversed, round, set, setattr, slice, sorted, staticmethod, str, sum, super, tuple, type, vars, zip
def access_function():
    print(access_function.known)  # False Positive to avoid
    print(access_function.unknown)  # False Negative

access_function.known = 42

class AClass:
    pass
AClass.known = 42

def access_Aclass():
    print(AClass.known)  # False Positive to avoid
    print(AClass.unknown)  # False Negative

#
# Out of scope: Detecting if an attribute is read only, read-write, callable, etc... is out of scope of this rule.
# This will be handled by a different rule.
#

class HasProperty:
    @property
    def prop(self):
        return 42

def access_thrid_party():
    h = HasProperty()
    print(h.prop)
    h.prop = 21  # Bug. Out of scope


#
# Out of scope: classes inheriting from a class defined in a third party library will not raise any issue
#
from django.views.generic import TemplateView


class View(TemplateView):
    pass

def access_thrid_party():
    v = View()
    print(v.get)  # False Positive to avoid
    print(v.unknown)  # Bug. Out of scope


#
# Out of scope: support decorated classes
# No issue is raised on decorated classes
#
# Related Pylint False Positive: https://github.com/PyCQA/pylint/issues/3344
# It raises because class DatetimeIndex has a "tz_localize" method generated
# See https://github.com/pandas-dev/pandas/blob/c1fd95bece36815d7b3fa09f1e103a5218c5f5e9/pandas/core/indexes/datetimes.py#L79
#
def add_method(cls):
    cls.method = lambda self: print("method")

@add_method
class Decorated:
    pass

def access_Decorated(param):
    x = Decorated()
    x.method()  # False Positive to avoid

    if isinstance(param, Decorated):
        param.method()  # False Positive to avoid

#
# Out of scope: no issue will be raised when a class has a metaclass
# Related Pylint False Positive: https://github.com/PyCQA/pylint/issues/3339
#
class AMetaclass(type):
    def __init__(cls, what, bases=None, attrs=None):
        super().__init__(what, bases, attrs)
        cls.known = 'I exist'


class HasMetaclass(metaclass=AMetaclass):
    pass

def access_HasMetaclass(param):
    h = HasMetaclass()
    print(h.known)  # False Positive to avoid

    if isinstance(param, HasMetaclass):
        print(param.known)  # False Positive to avoid

#
# Out of scope: the type of attributes will not be guessed
# Related Pylint False Positive: https://github.com/PyCQA/pylint/issues/3334
#

class HasAttributeType:
    @property
    def prop(self):
        return 42

def access_HasAttributeType(param):
    h = HasAttributeType()
    print(h.prop.unknown)  # Ok. False Negative

    if isinstance(param, HasAttributeType):
        param.prop.unknown  # Ok. False Negative

#
# Out of scope: support of typing.Generic
# We won't raise any issue when one of the parent classes is a generic class.
# Related Pylint False Positive: https://github.com/PyCQA/pylint/issues/3131
#
from typing import Generic, TypeVar

T = TypeVar('T')

class Base(Generic[T]):
    def foo(self) -> None:
        print('bar')

class Intermediate(Base[T]):
    pass

class Concrete(Intermediate[int]):
    pass

obj = Concrete()
obj.foo()  # False Positive to avoid

#
# Out of scope: supporting typing.NewType
# Related Pylint False Positive: https://github.com/PyCQA/pylint/issues/3162
#
from typing import NewType

def access_NewType():
    mystr = NewType("mystr", str)
    x = mystr("test")
    x.upper()  # False Positive to avoid

#
# Out of scope: support attributes added by monkey patching the class
# We won't raise any issue if we detect that a class is modified (monkey patching).
# We won't check how the class is modified. We will simply not run the rule on this type.
#
class MonkeyPatched:
    pass

MonkeyPatched.attr = 42  # monkey patching the class

def monkey_patching():
    mp = MonkeyPatched()
    print(mp.attr)  # False Positive to avoid

#########################
# Complex False Positives
#########################

#
# We expect to raise false positives when methods are defined in strange ways.
# Users will then need to provide type annotations or disable the rule for these classes.
#
# Related pylint False Positive: https://github.com/PyCQA/pylint/issues/3313
# https://github.com/python/cpython/blob/fa919fdf2583bdfead1df00e842f24f30b2a34bf/Lib/multiprocessing/managers.py#L1222-L1241
# https://github.com/python/typeshed/blob/6b55f5c49877c37e603d746493071ff07b89d3dd/stdlib/3/multiprocessing/managers.pyi#L59-L71
# Note: Every linter fails on this use case (PyCharm, Pylint, Mypy, etc...)
#
from multiprocessing import Manager

with Manager() as m:
    m.Lock()  # False Positive to avoid