# https://github.com/PyCQA/pylint/issues/2793

# pylint: disable=missing-docstring, too-few-public-methods,pointless-statement, wildcard-import, unused-wildcard-import, using-constant-test, global-statement, function-redefined
# pylint: disable=expression-not-assigned

class Foo:
  def __init__(self):
    self._exc = None

  def fail(self):
    self._exc = Exception("")

  def doit(self):
    if self._exc:
        exc = self._exc
        self._exc = None
        raise exc  # False Positive


class Foo:
  def __init__(self):
    self._exc = None

  def doit(self):
    if self._exc:
        exc = self._exc
        raise exc # False Positive


class Foo:
  def __init__(self):
    self._exc = None

  def doit(self):
    if self._exc:
        raise self._exc # False Positive


class Foo:
  def __init__(self):
    self._exc = None

  def doit(self):
    if True:
        raise self._exc # False Negative
    self._exc = RuntimeError()


class Bar1:
  _exc = None

  @classmethod
  def doit(cls):
    if True:
        raise Bar1._exc # True Positive
    Bar1._exc = RuntimeError()


class Bar2:
  _exc = None

  @classmethod
  def doit(cls):
    if True:
        raise cls._exc # True Positive
    cls._exc = RuntimeError()


class Bar2:
  _exc = None

  @classmethod
  def setexc(cls):
      cls._exc = RuntimeError()

  @classmethod
  def doit(cls):
    if cls._exc:
        raise cls._exc # False Positive

class Bar3:
  _exc = None

  @classmethod
  def setexc(cls):
      Bar3._exc = RuntimeError()

  @classmethod
  def doit(cls):
    if Bar3._exc:
        raise Bar3._exc # False Positive


def func1():
    a = RuntimeError()
    b = a
    a = None
    raise b # True Negative


def func2():
    b = RuntimeError()
    if True:
        raise b # True Negative
    b = None

def func3():
    b = None
    if True:
        raise b # True Positive
    b = RuntimeError()

def func4():
    b = None
    if True:
        raise b # True Positive
    b = RuntimeError()


# https://github.com/PyCQA/pylint/issues/157

def main():
    exc = None
    try:
        [][1] = 12
    except IndexError as exc:
        pass
    if exc is not None:
        raise exc  # False Positive
