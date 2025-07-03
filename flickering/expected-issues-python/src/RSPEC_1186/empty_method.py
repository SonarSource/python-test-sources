from abc import ABC, abstractmethod, abstractclassmethod, abstractstaticmethod, abstractproperty


def myfunc1(foo="Noncompliant"):
    pass

def myfunc2():
    """
        this is a docstring
    """

def myfunc3():
    pass  # comment explaining why this function is empty

def myfunc4():
    raise NotImplementedError()


class MyClass:
    def mymethod1(self, foo="Noncompliant"):
        pass

    def mymethod2(self):
        """
            this is a docstring
        """

    def mymethod3(self):
        pass  # comment explaining why this method is empty

    def mymethod4(self):
        raise NotImplementedError()

# empty abstract methods and properties are ok
class MyAbstractClass(ABC):
    @abstractproperty
    def myproperty(self):
        pass

    @abstractclassmethod
    def myclassmethod(cls):
        pass

    @abstractmethod
    def mymethod(self):
        pass

    @abstractstaticmethod
    def mystaticmethod():
        pass

class MySubClass(MyAbstractClass):
    pass

sub = MySubClass()
sub.myclassmethod()