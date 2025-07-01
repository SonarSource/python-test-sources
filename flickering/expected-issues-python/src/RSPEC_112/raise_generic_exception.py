def process1():
    raise BaseException("Wrong user input for field X")  # Noncompliant

def process2():
    raise BaseException("Wrong configuration")  # Noncompliant

def process3(param):
    if not isinstance(param, int):
        raise Exception("param should be an integer")  # Noncompliant

def caller1():
    try:
         process1()
         process2()
         process3(3)
    except BaseException as e:
        if e.args[0] == "Wrong user input for field X":
            # process error
            pass
        elif e.args[0] == "Wrong configuration":
            # process error
            pass
        else:
            # re-raise other exceptions
            raise


class MyProjectError(Exception):
    """Exception class from which every exception in this library will derive.
         It enables other projects using this library to catch all errors coming
         from the library with a single "except" statement
    """
    pass

class BadUserInputError(MyProjectError):
    """A specific error"""
    pass

class ConfigurationError(MyProjectError):
    """A specific error"""
    pass

def process4():
    raise BadUserInputError("Wrong user input for field X")

def process5():
    raise ConfigurationError("Wrong configuration")

def process6(param):
    if not isinstance(param, int):
        raise TypeError("param should be an integer")

def caller2():
    try:
         process4()
         process5()
         process6(3)
    except BadUserInputError as e:
        # process error
        pass
    except ConfigurationError as e:
        # process error
        pass