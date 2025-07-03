# string
{"one": 1, "two": 2}
{"one": 1, "two": 2, "one": 3}  # Noncompliant
{"one": 1, "two": 2, 'one': 3}  # Noncompliant. Simple and double quotes are equivalent
{"""multi
line""": 1,
"two": 2,
"""multi
line""": 3}  # Noncompliant

# int
{1: "one", 2: "two", 1: "three"}  # Noncompliant

# float
{1.0: "one", 2.0: "two", 1.0: "three"}  # Noncompliant

# bool
{True: "one", False: "two", True: "three"}  # Noncompliant

# int in other bases
{0o1: "one", 0o2: "two", 0o1: "three"}  # Noncompliant
{0x1: "one", 0x3: "two", 0x1: "three"}  # Noncompliant

# None
{None: 1, None: 2}  # Noncompliant

# equality between int/float/bool types
{1: "one", 2: "two", 1.0: "three"}  # Noncompliant
{1: "one", 2: "two", True: "three"}  # Noncompliant. True == 1
{0: "one", 2: "two", False: "three"}  # Noncompliant. False == 0

#
# Tuple
#
{(1, "2"): "one", 2: "two", (1, "2"): "three"}  # Noncompliant
{(1, "2"): "one", 2: "two", ("2", 1): "three"}  # Ok


#
# Repeated variable or parameter as key
#
def variables_and_parameters(a1, a2, a3):
    def func():
        pass
    {a1: 1, a2: 2, a1: 3}  # Noncompliant. Not in pylint but pyflakes detects this (F602).

    {func: 1, a2: 2, func: 3}  # Noncompliant

    [{a: 1, a:2} for a in range(10)]  # Noncompliant

    {a1(): 1, a2: 2, a1(): 3}  # Ok
    {func(): 1, a2: 2, func(): 3}  # Ok

    # Out of scope: we don't check if variables reference the same value.
    var1 = 1
    var2 = var1
    {var1: 1, var2: 2}  # Duplicate but out of scope


def classes_and_attributes(a1, a2, a3):
    class MyClass:
        pass

    {MyClass: 1, a2: 2, MyClass: 3}  # Noncompliant

    # We suppose that the attribute reference will not change while cretaing the dict.
    {MyClass.__doc__: 1, a2: 2, MyClass.__doc__: 3}  # Noncompliant

    {MyClass(): 1, a2: 2, MyClass(): 3}  # Ok
    {MyClass.__eq__(str): 1, a2: 2, MyClass.__eq__(str): 3}  # Ok


#
# Nice to have but optional as probably rare
#

{complex(1, 0): "one", 2: "two", complex(1, 0): "three"}  # Noncompliant
{1: "one", 2: "two", complex(1, 0): "three"}  # Noncompliant
{frozenset([1]): 1, frozenset([1]): 2}
{range(1): 1, range(1): 2}

# Same number with different bases
{1: "one", 2: "two", 0o1: "three"}  # Noncompliant
{1: "one", 2: "two", 0x1: "three"}  # Noncompliant


#
# False Positives to avoid
#
{1: {"a": 1}, 2: {"a": 2}}

{1: {1: "a"}}

#
# Out of scope
#

# Out of scope: formatted strings
p = 1
{f"one{p}": 1, "two": 2, f"one{p}": 3}  # Bug but out of scope

# Out of scope: equality between string/raw string/unicode string
# Detecting when strings with different prefixes are equal and when
# they are not would be difficult and would provide little value.
{"one": 1, "two": 2, u"one": 3}  # Ok. Out of scope
{"one": 1, "two": 2, r"one": 3}  # Ok. Out of scope

# Out of scope: bytes and strings with the same internal value.
# No issue as there are no duplicates in python 3. In Python 2,
# bytes and string would be duplicates.
{"one": 1, "two": 2, b"one": 3}  # Ok

# Out of scope: Custom classes
class A:
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        if not isinstance(other, A):
            return False
        return other.value == self.value

    def __hash__(self):
        return hash(self.value)

{A(1): 1, A(1.0): 2}  # Bug but out of scope

# Out of scope: python 2 unicode builtin
# {"one": 1, "two": 2, unicode("one"): 3}  # Noncompliant
