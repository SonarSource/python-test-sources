class NonCompliant:
    def __bool__(self):
        """should return bool"""
        return "hello"  # Noncompliant

    def __contains__(self, item):
        """should return bool"""
        return "hello"  # Noncompliant

    def __round__(self, n=None):
        """should return a number"""
        return "42"  # Noncompliant

    def __index__(self):
        """should return an int"""
        return "42"  # Noncompliant

    def __hash__(self):
        """should return an int"""
        return "42"  # Noncompliant

    def __int__(self):
        """should return an int"""
        return "42"  # Noncompliant

    def __float__(self):
        """should return a float"""
        return "42"  # Noncompliant

    def __complex__(self):
        """should return a complex"""
        return 42  # Noncompliant

    def __bytes__(self):
        """should return a bytes"""
        return 42  # Noncompliant

    def __repr__(self):
        """should return a str"""
        return 42  # Noncompliant

    def __str__(self):
        """should return a str"""
        return 42  # Noncompliant

    def __format__(self, format_spec):
        """should return a str"""
        return 42  # Noncompliant

    def __getnewargs_ex__(self):
        """should return a tuple of the form (tuple,dict)"""
        return 42  # Noncompliant

    def __getnewargs__(self):
        """should return a tuple"""
        return 42  # Noncompliant

    def __init__(self):
        """should not return anything"""
        return 42  # Noncompliant

    def __setitem__(self, key, value):
        """should not return anything"""
        return 42  # Noncompliant

    def __delitem__(self, key):
        """should not return anything"""
        return 42  # Noncompliant

    def __setattr__(self, key, value):
        """should not return anything"""
        return 42  # Noncompliant

    def __delattr__(self, item):
        """should not return anything"""
        return 42  # Noncompliant


class MultipleReturns:

    def __bool__(self):
        if self.x:
            return True
        else:
            return "hello"  # Noncompliant

    def __int__(self):
        if self.x:
            return 42
        else:
            return 42.5  # Noncompliant

    def __hash__(self):
        return NotImplemented  # OK

    def __format__(self, format_spec):  # Noncompliant
        for _ in range(10):
            print("hello")


class MyInt(int):
    ...


class Compliant:

    def __bool__(self):
        if self.cond:
            return 100  # OK, int is compatible with bool
        else:
            return False

    def __contains__(self, item):
        return True  # OK

    def __round__(self, n=None):
        if n is None:
            return 42
        else:
            return 42.44  # OK

    def __index__(self):
        return 42  # OK

    def __hash__(self):
        return MyInt(42)  # OK

    def __int__(self):
        return 42  # OK

    def __float__(self):
        return 42  # OK (int is compatible with float)

    def __complex__(self):
        return complex(1, 2)  # OK

    def __bytes__(self):
        if self.cond:
            return b'\x00'  # OK
        else:
            return bytes(42)  # OK

    def __repr__(self):
        return "42"  # OK

    def __str__(self):
        return "42"  # OK

    def __format__(self, format_spec):
        return "42"  # OK

    def __getnewargs_ex__(self):
        return {"a"}, {"a": "b"}  # OK

    def __getnewargs__(self):
        return 1, 2  # OK

    def __init__(self):
        return None  # OK

    def __setitem__(self, key, value):
        ...  # OK

    def __delitem__(self, key):
        return  # OK

    def __setattr__(self, key, value):
        return None  # OK

    def __delattr__(self, item):
        return None  # OK
