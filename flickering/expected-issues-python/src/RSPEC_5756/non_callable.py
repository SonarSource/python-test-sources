
##########################################################
# Case to cover: Calling an object with no __call__ method
##########################################################

class MyNonCallable:
    pass

def call_noncallable():
    myvar = MyNonCallable()
    myvar()  # Noncompliant

    none_var = None
    none_var()  # Noncompliant

    int_var = 42
    int_var()  # Noncompliant

    list_var = []
    list_var()  # Noncompliant

    tuple_var = ()
    tuple_var()  # Noncompliant

    dict_var = {}
    dict_var()  # Noncompliant

    set_var = set()
    set_var()  # Noncompliant


#######################################
# Valid case: Calling a callable object
#######################################

class MyCallable:
    def __call__(self):
        print("called")

def call_callable():
    myvar = MyCallable()
    myvar()



#############################
# Valid case: Call a function
#############################

from math import max

def func():
    pass

def call_function():
    func()
    max()

#############################
# Valid case: Call a method
#############################

class ClassWithMethods:
    def mymethod(self):
        pass

def call_function():
    myvar = ClassWithMethods()
    myvar.mymethod()  # Ok


##########################################################
# Out of scope: detecting that properties cannot be called
#
# A property is not callable, but the value returned
# by the property might be and we are not yet able to know
# if this is the case.
##########################################################

class CustomProperty(property):
    """ test subclasses """

class ClassWithProperties:
    @property
    def prop(self):
        return None

    @prop.setter
    def prop(self, value):
        self._prop = value

    @CustomProperty
    def custom_prop(self):
        return None

    @property
    def callable_prop(self):
        return max

def call_properties():
    myvar = ClassWithProperties()
    myvar.prop()  # False Negative. Out of scope
    myvar.custom_prop()  # False Negative. Out of scope
    myvar.callable_prop(1, 2)  # Ok. This calls "max"
