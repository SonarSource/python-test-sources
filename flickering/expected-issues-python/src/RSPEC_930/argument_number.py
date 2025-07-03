######################
# Positional Arguments
######################

param_args = [1, 2, 3]
param_kwargs = {'x': 1, 'y': 2}

def func(a, b=1):
    print(a, b)

def positional_unlimited(a, b=1, *args):
    print(a, b, *args)

func(1)
func(1, 42)
func(1, 2, 3)  # Noncompliant. Too many positional arguments
func()  # Noncompliant. Missing positional argument for "a"

func(1, 42, *param_args)  # Noncompliant. Maximum bumber of positional arguments already reached, *args should be removed

func(1, *param_args)  # Compliant. We don't check the size of *args

positional_unlimited(1, 2, 3, 4, 5)

def positional_limited(a, *, b=2):
    print(a, b)

positional_limited(1, 2)  # Noncompliant. Too many positional arguments


#############################
# Unexpected Keyword argument
#############################

def keywords(a=1, b=2, *, c=3):
    print(a, b, c)

keywords(1)
keywords(1, z=42)  # Noncompliant. Unexpected keyword argument "z"

keywords(a=21, b=22, **param_kwargs)  # Noncompliant. Maximum bumber of keyword arguments already reached, **kwargs should be removed
keywords(a=21, **param_kwargs)  # Compliant. We don't check the content of **kwargs


def keywords_unlimited(a=1, b=2, *, c=3, **kwargs):
    print(a, b, kwargs)

keywords_unlimited(a=1, b=2, z=42)

#################################
# Mandatory Keyword argument only
#################################

def mandatory_keyword(a, *, b):
    print(a, b)

mandatory_keyword(1, b=2)
mandatory_keyword(1)  # Noncompliant. Missing keyword argument "b"


########################################
# Capturing and not forwarding arguments
########################################

def mandatory_a(b=2, *, a):
    print(a, b)

def capture1(a, **kwargs):
    mandatory_a(**kwargs)  # Noncompliant. There is no way for kwargs to contain an argument named "a"

def capture2(a=42, **kwargs):
    mandatory_a(**kwargs)  # Noncompliant. There is no way for kwargs to contain an argument named "a"

def capture3(*, a, **kwargs):
    mandatory_a(**kwargs)  # Noncompliant. There is no way for kwargs to contain an argument named "a"


#####################################################
# Detect decorators not passing the correct arguments
#####################################################

def mydecorator(original):
    def wrapper(a, b, c):
        original(a, b)  # Secondary location here
    return wrapper

@mydecorator  # Noncompliant. argument "c" is not forwarded so there is one missing argument.
def decorated(a, b, c):
    print(a,b, c)

decorated(1, 2, 3)