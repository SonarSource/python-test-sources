################################################
# This file lists code examples with issues
# with different levels of complexity.
# The goal is to see the limits of our analyzer.
################################################


def called_indirectly(param):
    if param is None:
        return param + 1 # Mypy detects. Pytype doesn't.

locals()['called_indirectly'](None)

def called_directly(param):
    if param is None:
        return param + 2  # Mypy and Pytype detect

called_directly(None)

def without_condition(param):
    return param + 1 # Pytype detects. Mypy doesn't.

without_condition(None)

def path_sensitive(param):
    if not param:
        var = 1
        cond = False
    else:
        var = 0
        cond = True

    if cond:
        return 1 / var # Pytype detects. Mypy doesn't.

path_sensitive(True)

########
# Basics
########

def simple_variable():
    myvar = "1"
    return myvar > 1  # Noncompliant


def default_value(param = None):
    "The default value should never make the function fail."
    return param > 1  # Noncompliant

########################
# dict.get default value
########################

def list_default_get():
    "when using dict.get(...), the default value should always be of a compatible type with the next operation."
    mydict = {}
    # ...

    # Here we can suppose that get() will always return the same type as the default value, except when the default value is None.
    myvar = mydict.get('foo', "1") > 1  # Noncompliant. The default value "1" is not compatible

    # This one is more complex because we don't know all the possible types of get().
    myvar = mydict.get('foo') > 1  # Noncompliant. The default value None is not compatible.


#######################
# builtins and Typeshed
#######################
def support_builtins():
    myvar = 1.3
    myvar2 = round(myvar)  # Typeshed: https://github.com/python/typeshed/blob/97ecd2b91ffe7feab76aa1d6e30c5dc998358a04/stdlib/2and3/builtins.pyi#L1384

    myvar3 = myvar2 > 3  # Ok
    myvar3 = myvar2 = "1"  # Noncompliant


##################
# Path sensitivity
##################

def isinstance_guard(param = None):
    "Type can be easily deduced when there is a single isinstance guard at the beginning."
    if not isinstance(param, str):  # Noncompliant. param is a string here
        raise ValueError('param is expected to be a string')

    myvar = param + 1  # Noncompliant. param is a string

def isinstance_guard_assert(param = None):
    "Type can be easily deduced when there is a single assert-isinstance guard at the beginning."
    assert isinstance(param, str), 'param is expected to be a string'  # This is not recommended but it is sometime done

    myvar = param + 1  # Noncompliant. param is a string


def path_sensitive(param = None):
    "Type should become more precise when None guard and isinstance are used on if-elif-else branches."
    number = 1
    if isinstance(param, str) and number < param:  # Noncompliant. param is a string here
        pass

    if isinstance(param, str):
        myvar = param < number  # Noncompliant. param is a string here

    if param is None:
        myvar = param < number  # Noncompliant. param is None here

    if param is not None:
        pass
    else:
        myvar = param < number  # Noncompliant. param is None here

###########
# Sequences
###########

def sequences():
    mysequence = []
    for a in range(10):
        mysequence.append(a)
    return mysequence[0] + "test"  # Noncompliant


###############################
# Classes and operator overload
###############################

class LT:
    def __lt__(self, other):
        return True

class Empty:
    pass

def missing_method():
    "A class has to implement the right special metbhod in order to overload an operator."
    lt = LT()
    empty = Empty()

    myvar = lt < empty  # Ok
    myvar = empty > lt  # Ok

    myvar = empty < lt  # Noncompliant
    myvar = lt > empty  # Noncompliant


##################################
# Subclasses and operator overload
##################################

class SubLT(LT):  # inherits __lt__ method
    pass

def missing_inherited_method():
    "A class has to implement the right special metbhod in order to overload an operator."
    lt = SubLT()
    empty = Empty()

    myvar = lt < empty  # Ok
    myvar = empty > lt  # Ok

    myvar = empty < lt  # Noncompliant
    myvar = lt > empty  # Noncompliant


####################
# Classes attributes
####################

class MyClass:
    def __init__(self):
        self.myattr = "a string"

m = MyClass()
foo = m.myattr < 1  # Noncompliant.


######################################
# Classes attributes with reassignment
######################################

class MyClassWithReassignment:
    def __init__(self):
        self._myattr = None
    
    @property
    def myproperty(self):
        if self._myattr is None:
            self._myattr = "a string"
        return self._myattr

m = MyClassWithReassignment()
foo = m.myproperty < 1  # Noncompliant.


###################################
# Cross Procedural for return types
###################################

def return_42_or_none(param):
    if param > 0:
        return 42
    else:
        return None

def cross_procedural_return():
    myvar = return_42_or_none(1)
    myvar2 = myvar + "test"  # Noncompliant
    myvar = return_42_or_none(0)
    myvar3 = myvar + "test"  # Noncompliant


##################################
# Cross Procedural for param types
##################################

def expect_int(param):
    if param > 0:  # Noncompliant. param is a string
        pass

def cross_procedural_parameter_noncompliant():
    return expect_int("bad parameter")  # secondary location here


def cross_procedural_parameter_compliant():
    return expect_int(1)  # Ok


#########################################
# Cross Procedural for param types deeper
#########################################

def expect_int(param):
    if param > 0:  # Noncompliant. param is a string
        pass

def intermediate(param):
    expect_int(param)

def cross_procedural_parameter_noncompliant():
    return intermediate("bad parameter")  # secondary location here


def cross_procedural_parameter_compliant():
    return intermediate(1)  # Ok


################################################
# Cross Procedural for param types and data flow
################################################

def expect_int(param):
    if param > 0:  # Noncompliant. param is a string
        pass

def intermediate(param):
    if param is not None:
        expect_int(param)  # passing here
    else:
        expect_int(42)  # this one would have been ok


def cross_procedural_parameter_noncompliant():
    return intermediate("bad parameter")  # secondary location here


def cross_procedural_parameter_compliant():
    return intermediate(1)  # Ok
