from __future__ import print_function

import socket, binascii, abc, six

class CustomException(object):
    """An Invalid exception class."""

class CustomException2(object):
    """An Invalid exception class."""

class ValidException(Exception):
    """A valid exception class."""

class ValidException2(ValidException):
    """A valid exception class."""

class SocketErrorException(socket.error):
    """This is not an exception in Python 2, but it is one in python 3."""

class SecondSocketErrorException(SocketErrorException):
    """Also a valid exception."""

try:
    "a string" * 1
except CustomException:  # Noncompliant
    print("exception")

try:
    "a string" * 2
except (CustomException, CustomException2):  # Noncompliant * 2
    print("exception")

try:
    "a string" * 3
except ValidException:
    print("exception")

try:
    "a string" * 3
except (ValidException, ValidException2):
    print("exception")

try:
    "a string" * 3
except (SocketErrorException, SecondSocketErrorException):
    print("exception")

try:
    "a string" * 42
except (None, list()):  # Noncompliant * 2
    print("exception")

try:
    "a string" * 24
except None: # Noncompliant
    print("exception")

try:
    "a string" * 24
except [ValueError, TypeError]: # Noncompliant
    print("exception")

try:
    "a string" * 24
except {ValueError, TypeError}: # Noncompliant
    print("exception")

EXCEPTION = None
EXCEPTION = ZeroDivisionError
try:
    "a string" * 46
except EXCEPTION:
    print("exception")

try:
    "a string" * 42
except (list([4, 5, 6]), None, ZeroDivisionError, 4):  # Noncompliant * 3.
    print("exception")

EXCEPTION_TUPLE = (ZeroDivisionError, OSError)
NON_EXCEPTION_TUPLE = (ZeroDivisionError, OSError, 4)

try:
    "a string" * 42
except EXCEPTION_TUPLE:
    print("exception")

try:
    "a string" * 42
except NON_EXCEPTION_TUPLE: # Noncompliant. Out of scope
    print("exception")

from missing_import import UnknownClass
UNKNOWN_COMPONENTS = (ZeroDivisionError, UnknownClass)

try:
    "a string" * 42
except UNKNOWN_COMPONENTS:
    print("exception")

try:
    "a string" * 42
except binascii.Error:
    print('builtin and detected')

try:
    "a string" * 45
except object: # Noncompliant
    print('exception')

try:
    "a string" * 42
except range: # Noncompliant
    print('exception')


class HasAnInvalidMRO(six.with_metaclass(abc.ABCMeta, Exception)):
    pass


class Second(HasAnInvalidMRO):
    pass


try:
    raise Second
except Second:
    pass


class ABaseClass(UnknownClass):
    pass


EXCEPTIONS = (ABaseClass, ValueError)

try:
    raise ValueError
except EXCEPTIONS:
    pass
