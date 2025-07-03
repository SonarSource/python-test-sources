class CustomException(TypeError):
    pass

def InstantiatedBuiltinExceptions():
    BaseException()  # Noncompliant
    Exception()  # Noncompliant
    ValueError()  # Noncompliant
    CustomException()  # Noncompliant

    BaseException  # Noncompliant
    Exception  # Noncompliant
    ValueError  # Noncompliant
    CustomException  # Noncompliant


def compliant(param, func):
    lambda: ValueError() if param else None
    func(ValueError())
    if param == 1:
        raise ValueError
    elif param == 2:
        raise ValueError()
    return ValueError()

def variables_are_out_of_scope():
    """S3984 doesn't raise on exceptions assigned to unused variables.
    S1481 already raises on unused variables.
    """
    var = ValueError()  # No issue from S3984

def gen():
    yield ValueError()


try:
    WindowsError  # No issue here. This will raise an exception if the program doesn't run on Windows. (Pylint False Positive)
except NameError:
    ...
