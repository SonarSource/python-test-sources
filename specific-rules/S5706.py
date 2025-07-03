"""This module tests S5706"""

class BareRaiseInExit(object):
    """A case where a bare raise is present in __exit__"""
    def __exit__(self, exc_type, exc_value, traceback):
        raise

class ReRaisingExceptionValue(object):
    """A case where we re-raise the exception in __exit__"""
    def __exit__(self, exc_type, exc_value, traceback):
        raise exc_value
