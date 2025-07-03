class MyException(BaseException):  # Noncompliant
    pass

class MyException(GeneratorExit):  # Noncompliant
    pass

class MyException(KeyboardInterrupt):  # Noncompliant
    pass

class MyException(SystemExit):  # Noncompliant
    pass

class MyException(Exception):
    pass