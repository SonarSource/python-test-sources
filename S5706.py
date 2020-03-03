class BareRaiseInExit:
    def __exit__(self, exc_type, exc_value, traceback):
        raise # Noncompliant {{Remove this "raise" statement and return "False" instead.}}
       #^^^^^

class ReRaisingExceptionValue:
    def __exit__(self, exc_type, exc_value, traceback):
        raise exc_value # Noncompliant
       #^^^^^^^^^^^^^^^
