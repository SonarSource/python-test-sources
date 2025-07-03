if True:
    raise  # Noncompliant

def foo():
    raise  # Noncompliant
    try:
        raise  # Noncompliant
    except:
        raise  # Ok
    else:
        raise  # Noncompliant
    finally:
        raise  # Ok

if True:
    raise ValueError() # Ok

def foo():
    raise ValueError() # Ok
    try:
        raise ValueError() # Ok
    except:
        raise ValueError() # Ok
    else:
        raise ValueError() # Ok
    finally:
        raise ValueError() # Ok


def function_in_except():
    try:
        raise ValueError()
    except ValueError as e:
        def new_scope():  # This creates a new scope
            raise  # Ok
        new_scope()
    except TypeError as e:
        def other_scope():  # This creates a new scope
            raise  # Noncompliant

def function_in_finally():
    try:
        raise ValueError()
    finally:
        def new_scope():  # This creates a new scope
            raise  # Noncompliant
        return new_scope

class C(object):
    try:
        pass
    except:
        raise
    raise # Noncompliant



class MyContextManager(object):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        # No issue raised when `raise` is in __exit__ method. This exception is from pylint as there could be an exception available
        raise