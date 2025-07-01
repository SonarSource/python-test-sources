from abc import ABC, abstractstaticmethod, abstractmethod, abstractclassmethod, abstractproperty
from django.utils.decorators import classproperty

class MyClass:
    def instance_method():  # Noncompliant. "self" parameter is missing.
        print("instance_method")

    @classmethod
    def class_method():  # Noncompliant. "cls" parameter is missing.
        print("class_method")

    def old_style_class_method():  # Noncompliant. False Negative but not a lot of value as this is a very old style
        print("old_style_class_method")
    old_style_class_method = classmethod(old_style_class_method)


class MyClass2:
    def instance_method(self):
        print("instance_method")

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


class MyAbstractClass(ABC):
    @abstractproperty
    def myproperty():  # Noncompliant. "self" parameter is missing.
        pass

    @abstractclassmethod
    def myclassmethod():  # Noncompliant. "cls" parameter is missing.
        pass

    @abstractmethod
    def mymethod():  # Noncompliant. "self" parameter is missing.
        pass

    @abstractstaticmethod
    def mystaticmethod():  # Compliant. False Positive
        pass


class WithDecorator:
    @classproperty
    def prop():
        return 42

    def foo():
        pass

def foo(a,b,c, * d):
    pass

foo()


class HasProperty:

    @property
    def foo():  # Noncompliant. False Negative
        return 42

    @foo.setter
    def foo():  # Noncompliant. False Negative
        pass

    @foo.deleter
    def foo():  # Noncompliant. False Negative
        pass