class A:
    @property
    def foo(self, unexpected, unexpected2):  # Noncompliant. Too many parameters.
        return self._foo

    @foo.setter
    def foo(self, value, unexpected):  # Noncompliant. Too many parameters.
        self._foo = value

    @foo.deleter
    def foo(self, unexpected):  # Noncompliant. Too many parameters.
        del self._foo


class A2:
    @property
    def foo(self, unexpected):  # Noncompliant. Too many parameters.
        return self._foo

    @foo.setter
    def foo(self):  # Noncompliant. missing value
        self._foo = 42

    @foo.deleter
    def foo(self, unexpected):  # Noncompliant. Too many parameters.
        del self._foo

class A3:
    @property
    def foo():  # Ok. Should be covered by S5719
        return 42

    @foo.setter
    def foo():  # Noncompliant. missing value
        pass

    @foo.deleter
    def foo():  # Ok. Should be covered by S5719
        pass


class B:
    def get_foo(self, unexpected):  # Noncompliant. Too many parameters.
        return self._foo

    def set_foo(self, value, unexpected):  # Noncompliant. Too many parameters.
        self._foo = value

    def del_foo(self, unexpected):  # Noncompliant. Too many parameters.
        del self._foo

    foo = property(get_foo, set_foo, del_foo, "'foo' property.")

class B2:
    def get_foo(self, unexpected):  # Noncompliant. Too many parameters.
        return self._foo

    def set_foo2(self):  # Noncompliant. missing value
        self._foo = 42

    def del_foo(self, unexpected):  # Noncompliant. Too many parameters.
        del self._foo

    foo2 = property(get_foo, set_foo2, del_foo, "'foo2' property.")

class ACompliant:
    @property
    def foo(self):
        return self._foo

    @foo.setter
    def foo(self, value):
        self._foo = value

    @foo.deleter
    def foo(self):
        del self._foo

class BCompliant:
    def get_foo(self):
        return self._foo

    def set_foo(self, value):
        self._foo = value

    def del_foo(self):
        del self._foo

    foo = property(get_foo, set_foo, del_foo, "'foo' property.")