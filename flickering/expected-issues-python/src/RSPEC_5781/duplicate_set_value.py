# string
{"one", "two"}
{"one", "two", "one"}  # Noncompliant
{"one", "two", 'one'}  # Noncompliant. Simple and double quotes are equivalent
{"""multi
line""",
"two",
"""multi
line"""}  # Noncompliant

# int
{1, 2, 1}  # Noncompliant

# float
{1.0, 2.0, 1.0}  # Noncompliant

# bool
{True, False, True}  # Noncompliant

# int in other bases
{0o1, 0o2, 0o1}  # Noncompliant
{0x1, 0x3, 0x1}  # Noncompliant

# None
{None, None}  # Noncompliant

# equality between int/float/bool types
{1, 2, 1.0}  # Noncompliant
{1, 2, True}  # Noncompliant. True == 1
{0, 2, False}  # Noncompliant. False == 0

# Out of scope: equality between different kind of strings
{"one", "two", u"one"}  # Out of scope
{"one", "two", r"one"}  # Out of scope


# No issue as there are no duplicates in python 3. In Python 2, bytes and string would be duplicates.
{"one", "two", b"one"} # Out of scope

#
# Tuple
#
{(1, "2"), 2, (1, "2")}  # Noncompliant
{(1, "2"), 2, ("2", 1)}  # Ok


#
# Repeated variable or parameter as key
#
def variables_and_parameters(a1, a2, a3):
    def func():
        pass
    {a1, a2, a1}  # Noncompliant. Not in pylint but pyflakes detects this (F602).

    {func, a2, func}  # Noncompliant

    [{a, a} for a in range(10)]  # Noncompliant

    {a1(), a2, a1()}  # Ok
    {func(), a2, func()}  # Ok

    # Out of scope: we don't check if variables reference the same value.
    var1 = 1
    var2 = var1
    {var1, var2}  # Duplicate but out of scope


def classes_and_attributes(a1, a2, a3):
    class MyClass:
        pass

    {MyClass, a2, MyClass}  # Noncompliant

    # We suppose that the attribute reference will not change while cretaing the set.
    {MyClass.__doc__, a2, MyClass.__doc__}  # Noncompliant

    {MyClass(), a2, MyClass()}  # Ok
    {MyClass.__eq__(str), a2, MyClass.__eq__(str)}  # O


#
# Out of scope because it is probably rare
#

{complex(1, 0), 2, complex(1, 0)}  # Out of scope
{1, 2, complex(1, 0)}  # Out of scope
{frozenset([1]), frozenset([1])}
{range(1), range(1)}  # Out of scope

# Same number with different bases
{1, 2, 0o1}  # Noncompliant
{1, 2, 0x1}  # Noncompliant

#
# Out of scope
#

# Out of scope: formatted strings
p = 1
{f"one{p}", "two", f"one{p}"}  # Bug but out of scope

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

{A(1), A(1.0)}  # Bug but out of scope

# Out of scope: python 2 unicode builtin
# {"one", "two", unicode("one")}  # Noncompliant