# Because a subclass instance may be used as an instance of the superclass, overriding methods should uphold the aspects of the superclass contract that relate to the Liskov Substitution Principle.

# Specifically, an overriding method should be callable with the same number and name of parameters as the overriden one.

# This rule raises an issue when the signature of an overriding method does not accept every combination of parameters that the overriden method accepts.

# h2. Noncompliant Code Example:
# {code:python}
# {code}

# Builtin

class MyList(list):
    def append(self):  # Noncompliant. "Add 1 missing parameter; this method overrides list.append"
        pass

    def index(self):  # Noncompliant. "Add 3 missing parameters; this method overrides list.index"
        pass

    def clear(self, added):  # Noncompliant. Remove parameter "added" or provide a default value.
        pass

#
# Positional & Keyword Arguments
#

class ParentClass(object):

    def mymethod(self, param1):
        pass

class ChildClassSame(ParentClass):
    """Same signature"""
    def mymethod(self, param1): # Ok
        pass

class ChildClassMore(ParentClass):

    def mymethod(self, param1, param2, param3): # Noncompliant * 2.
        # Remove parameter "param2" or provide a default value.
        # Remove parameter "param3" or provide a default value.
        pass

class ChildClassLess(ParentClass):

    def mymethod(self): # Noncompliant. Add missing parameter "param1".
        pass

class ChildClassRenamed(ParentClass):

    def mymethod(self, renamed): # Ok. Rename this parameter as "param1".
        pass

class ChildClassReordered(ParentClass):

    def mymethod(self, inserted, param1): # Noncompliant * 2.
        # Move param1 to position 1
        # Remove parameters "inserted" or provide a default value.
        pass


#
# Vararg and Keywords parameters
#

class ChildClassAddVararg(ParentClass):

    def mymethod(self, param1, *args):  # ok. Accepting more optional parameters.
        pass

class ChildClassReplaceVararg(ParentClass):

    def mymethod(self, *args):  # ok. Making param1 optional but still accepting it.
        pass

class ChildClassAddKWarg(ParentClass):

    def mymethod(self, param1, *kwargs):  # ok. Accepting more optional parameters.
        pass

class ChildClassAddKWarg(ParentClass):

    def mymethod(self, *kwargs):  # ok. Making param1 optional but still accepting it.
        pass


class ParentClassVararg(object):

    def mymethod(self, *args):
        pass

class ChildClassNoVararg1(ParentClassVararg):

    def mymethod(self):  # Noncompliant. Add missing vararg parameter (*args)
        pass

class ChildClassNoVararg2(ParentClassVararg):

    def mymethod(self, param1, *args):  # Noncompliant. Remove parameter "param1"
        pass

class ParentClassKWararg(object):

    def mymethod(self, *kwargs):
        pass

class ChildClassNoKWararg1(ParentClassKWararg):

    def mymethod(self):  # Noncompliant. Add missing keywords parameter (*kwargs)
        pass

class ChildClassNoKWararg2(ParentClassKWararg):

    def mymethod(self, param1=None, *kwargs):  # Ok
        pass

class ChildClassNoKWararg3(ParentClassKWararg):

    def mymethod(self, param1, *kwargs):  # Noncompliant. Remove parameter "param1" or provide a default value.
        pass


#
# Positional & Keyword Arguments with defaults
#


class ParentClassDefaults(object):

    def mymethod(self, param1, param2=None, param3=None):
        pass

class ChildDefaultsLess(ParentClassDefaults):

    def mymethod(self, param1, param2=None): # Noncompliant. Add missing parameter "param3"
        pass

class ChildDefaultsRemoved(ParentClassDefaults):

    def mymethod(self, param1, param2, param3=None): # Noncompliant. Add a missing value to "param2"
        pass

class ChildDefaultsAdded(ParentClassDefaults):

    def mymethod(self, param1=None, param2=None, param3=None): # Ok
        pass

#
# Multi-Level inheritance
#

class TopClass(object):

    def mymethod(self, param1):
        pass

class MiddleClass(TopClass):
    """Same signature"""
    def mymethod(self, param1, param2): # Noncompliant
        pass

class BottomClassGood(MiddleClass):

    def mymethod(self, param1, param2): # Ok
        pass

class BottomClassBad(MiddleClass):

    def mymethod(self, param1): # Noncompliant
        pass

#
# Multi-inheritance


# We don't raise if the same method is defined in multiple parent classes
class ParentMultiClass1(object):

    def mymethod(self, param1):
        pass


ParentMultiClass1().mymethod(1, 2)

class ParentMultiClassDifferent(object):

    def mymethod(self, param1, param2):
        pass

class ChildMultiClass1(ParentMultiClass1, ParentMultiClassDifferent):
    """Same signature"""
    def mymethod(self, param1): # Ok. Out of scope
        pass

class ChildMultiClass2(ParentMultiClass1, ParentMultiClassDifferent):
    def mymethod(self, param1, param2): # Ok. Out of scope
        pass

class ChildMultiClass3(ParentMultiClass1, ParentMultiClassDifferent):
    def mymethod(self, param1, param2, param3):  # Noncompliant. But this could be out of scope.
        pass


# If only one parent has the class defined we 
class ParentMultiClassEmpty(object):
    pass


class ChildMultiClass2(ParentMultiClass1, ParentMultiClassEmpty):
    def mymethod(self, param1, param2): # Ok. Cannot decide which signature to use
        pass

#
# Keyword Only parameters (https://www.python.org/dev/peps/pep-3102/)
#

class ParentClassKWOnly(object):

    def mymethod(self, param1, *, param2):
        pass

class ChildClassKWOnly(ParentClassKWOnly):

    def mymethod(self, param1, *, param2):
        pass

class ChildClassMakeKWOnly(ParentClassKWOnly):

    def mymethod(self, *, param1, param2): # Noncompliant on param1 as be cannot be passed by position anymore
        pass

class ChildClassKWOnlyMore(ParentClassKWOnly):

    def mymethod(self, param1, *, param2, param3): # Noncompliant. Remove parameter "param3" or provide a default value.
        pass

class ChildClassKWOnlyLess(ParentClassKWOnly):

    def mymethod(self, param1): # Noncompliant. Add missing Keyword-only parameter "param2".
        pass

class ChildClassKWOnlyMovedOk(ParentClassKWOnly):

    def mymethod(self, param1, param2): # Ok. This only enables to pass param2 as a positional argument. Compatibility is ok.
        pass

class ChildClassKWOnlyMovedBad(ParentClassKWOnly):

    def mymethod(self, param2, param1): # Noncompliant * 2
        # Make parameter param2 keyword-only
        # Move param1 in position 1
        pass

class ChildClassKWOnlyRenamed(ParentClassKWOnly):

    def mymethod(self, renamed): # Noncompliant. Rename this parameter as "param1".
        pass


class ParentClassKWOnly2(object):

    def mymethod(self, param1, *, param2, param3):
        pass

class ChildClassKWOnlyReordered(ParentClassKWOnly2):

    def mymethod(self, param1, *, param3, param2):  # Ok. reordering keyword only parameters is not a problem.
        pass

#
# Positional Only parameters (https://www.python.org/dev/peps/pep-0570/) Once MMF-1859 "Support Python 3.8" is implemented
#

class ParentClassPosOnly(object):

    def mymethod(self, param1, /, param2, *, param3):
        pass

class ChildClassPosOnlyMovedBad1(ParentClassPosOnly):

    def mymethod(self, param1, param2, /, *, param3): # Noncompliant. Make param2 a keyword or positional parameter
        pass

class ChildClassPosOnlyMovedBad2(ParentClassPosOnly):

    def mymethod(self, param1, param2, param3, /): # Noncompliant * 2
        # Make param2 a keyword or positional parameter
        # Make param3 a keyword only parameter
        pass

class ChildClassPosOnlyLess(ParentClassPosOnly):
    def mymethod(self, param2, *, param3):  # Noncompliant. Add missing parameter "param1"
        pass

class ChildClassPosOnlyMore(ParentClassPosOnly):
    def mymethod(self, param1, unknown, /, param2, *, param3):  # Noncompliant. Remove parameter "unknown"
        pass

class ChildClassPosOnlyToKworPos(ParentClassPosOnly):
    def mymethod(self, param1, param2, *, param3):  # ok. "param1" can be passed as positional argument at the same position
        pass

class ChildClassPosOnlyReorder(ParentClassPosOnly):
    def mymethod(self, param2, param1, *, param3):  # Noncompliant * 2
        # Move param1 in position 1
        # Move param2 in position 2
        pass


#
# Class methods are ignored on purpose
#

class ParentClassMethodClass(object):
    @classmethod
    def mymethod(cls, param1):
        pass

class ChildClassMethodClassMore(ParentClassMethodClass):
    """Same signature"""
    @classmethod
    def mymethod(cls, param1): # Ok
        pass

class ChildClassMethodClassMore(ParentClassMethodClass):
    @classmethod
    def mymethod(cls, param1, param2): # Ok
        pass

class ChildClassMethodClassLess(ParentClassMethodClass):
    @classmethod
    def mymethod(cls): # Ok
        pass

class ChildClassMethodClassRenamed(ParentClassMethodClass):
    @classmethod
    def mymethod(cls, renamed): # Ok
        pass

class ChildClassMethodClassRenamedInstance(ParentClassMethodClass):
    def mymethod(renamed): # Ok. We should have a different rules for class methods and instance method having the same name
        pass

#
# Static methods are ignored on purpose
#

class ParentStaticMethodClass(object):
    @staticmethod
    def mymethod(param1):
        pass

class ChildStaticMethodClassMore(ParentStaticMethodClass):
    """Same signature"""
    @staticmethod
    def mymethod(param1): # Ok
        pass

class ChildStaticMethodClassMore(ParentStaticMethodClass):
    @staticmethod
    def mymethod(param1, param2): # Ok
        pass

class ChildStaticMethodClassLess(ParentStaticMethodClass):
    @staticmethod
    def mymethod(): # Ok
        pass

class ChildStaticMethodClassRenamed(ParentStaticMethodClass):
    @staticmethod
    def mymethod(renamed): # Ok
        pass

class ChildStaticMethodClassRenamedInstance(ParentStaticMethodClass):
    def mymethod(renamed): # Ok. We should have a different rules for static methods and instance method having the same name
        pass

#
#  Private methods are ignored on purpose
#

class ParentStaticMethodClass(object):

    def __mymethod(param1):
        pass

class ChildStaticMethodClassMore(ParentStaticMethodClass):
    """Same signature"""
    def __mymethod(param1): # Ok
        pass

class ChildStaticMethodClassMore(ParentStaticMethodClass):

    def __mymethod(param1, param2): # Ok
        pass

class ChildStaticMethodClassLess(ParentStaticMethodClass):

    def __mymethod(): # Ok
        pass

class ChildStaticMethodClassRenamed(ParentStaticMethodClass):

    def __mymethod(renamed): # Ok
        pass

#
# Properties
#

class PropertyClass(object):

    @property
    def myproperty(self):
        pass

class PropertyClassWithSetter(PropertyClass):

    @property
    def myproperty(self):  # Ok
        pass

    @myproperty.setter
    def myproperty(self, attr):  # Ok
        return attr


#
#  Special methods are out of scope as another rule covers them. Renaming their parameters should have no effect.
#

class SpecMethod(object):

    def __add__(self, param1, param2, param3):  # Ok for this rule
        pass  # This method is invalid on purpose

class SpecMethodSub(SpecMethod):

    def __add__(self, param1, param2):  # Ok for this rule
        pass  # This method is invalid on purpose




#
# This might raise some false positives. Need to check on Peach once implemented
#
class AbstractClass(object):

    def mymethod(self, arg, arg1):
        raise NotImplementedError

class ChildOfAbstractClass(AbstractClass):

    def mymethod(self, _arg, dummy):  # Noncompliant???
        pass