from .badly_named_self_import import ExternalMetaclass
import badly_named_self_import
import six
from  typing import Protocol
from abc import ABCMeta, abstractmethod

class MyClass1:
    def send_request(request):  # Noncompliant. "self" was probably forgotten
        print("send_request")

    def __init_subclass__(cls):  # ok
        print("__init_subclass__")

    def __class_getitem__(cls, key):  # ok
        print("__class_getitem__")

    def __new__(cls, *args, **kwargs):  # ok
        print("__new__")


class MyClass2:
    def send_request(self, request):
        print("send_request")

    @classmethod
    def class_method(cls):
        print("class_method")

    @staticmethod
    def static_method():
        print("static_method")

    # old style static method. Ex: https://github.com/ActiveState/code/blob/61a74f5f93da087d27c70b2efe779ac6bd2a3b4f/recipes/Python/440555_Twisted__BitTorrent___Client_/recipe-440555.py#L215-L217
    def old_style_static_method():
        print("old_style_static_method")
    old_style_static_method = staticmethod(old_style_static_method)

    def old_style_class_method(cls):
        print("old_style_class_method")
    old_style_class_method = classmethod(old_style_class_method)


class MyClassMeta(type):
    def process(cls):  # Ok. This is a metaclass
        print("process")

class MyClassMeta(type):
    def process(cls):  # Ok. This is a metaclass
        print("process")

class MyClassMeta2(ExternalMetaclass):
    def process(cls):  # Ok. This is a metaclass
        print("process")

class MyClassMeta3(badly_named_self_import.ExternalMetaclass):
    def process(cls):  # Ok. This is a metaclassten
        print("process")


class MySixMetaclass1(six.with_metaclass(MyClassMeta, type)):
    def process(cls):  # Ok. This is a metaclass
        print("process")

@six.add_metaclass(MyClassMeta)
class MySixMetaclass2:
    def process(cls):  # Ok. This is a metaclass
        print("process")

class MyProtocol(Protocol):
    def process(cls):  # Ok. This is a protocol
        print("process")


class MethodReferencedInBody:
    def referenced_method(param):  # Ok referenced in the class body
        """"""
        pass
    config = [referenced_method()]

    def used_as_decorator(method):  # Ok. Used as a decorator
        # https://jira.sonarsource.com/browse/SONARPY-637
        return method

    @used_as_decorator
    def decorated(self):
        """"""
        pass

MethodReferencedInBody.config[0]()

class A:
    def meth(self):
        class B:
            def nested(this):  # Ok
                pass



class AbstractClass(metaclass=ABCMeta):
    @abstractmethod
    def abs_method():  # Ok. abstractmethod is the default value of ignoredDecorators
        pass

from enum import Enum

class MyAutoName(Enum):
     def _generate_next_value_(name, start, count, last_values): # False Positive 
         return name