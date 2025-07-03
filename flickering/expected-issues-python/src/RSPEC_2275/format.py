# format method and function
# https://docs.python.org/3/library/string.html#format-string-syntax
# https://pyformat.info/

# Pylint validation code:
# https://github.com/PyCQA/pylint/blob/01dfa522195d79217c43065d3d013e2ee31d47b7/tests/functional/s/string_formatting.py
# https://github.com/PyCQA/pylint/blob/527db314ecc00ad79be083dcca6134bb68c3bb60/tests/functional/s/string_formatting_py27.py

####################################################################
# Case to cover: Detect when a formatted string is
# badly formatted. See the syntax here:
# https://docs.python.org/3/library/string.html#format-string-syntax
####################################################################

class A:
    field = 42

class Map:
    def __getitem__(self, key):
        return 42



# Compliant cases
"{0}".format(1)  # Ok
"{a.field.real}".format(a=A())  # Ok
"{m[key]}".format(m=Map())  # Ok
"{m[0]}".format(m=[1])  # Ok

# Note that any character can be used in a field name as long as it doesn't
# conflict with the syntax of replacement fields.
"{'0'}".format(**{"\'0\'": 1})  # Ok
"{m]}".format(**{"m]": 42})  # Ok.



# Noncompliant: we detect when replacement fields are truncated.
"{0".format(1)  # Noncompliant
"0}".format(1)  # Noncompliant
"{a.}".format(a=A())  # Noncompliant
"{a.field.}".format(a=A())  # Noncompliant
"{m[attr}".format(m=Map())  # Noncompliant
"{m[]}".format(m=Map())  # Noncompliant



# Noncompliant: We detect when conversion flags are unknown.
# Only three conversion flags are supported: !a, !s and !r
'{0!s}'.format('str')  # Ok
'{0!r}'.format('str')  # Ok
'{0!a}'.format('str')  # Ok
'{0!z}'.format('str')  # Noncompliant
'{0!}'.format('str')  # Noncompliant



####################################################
# Out of scope: Detect invalid Format Specification.
####################################################

# Classes can create their own format specification so we won't try to support this for now.
# We could later validate format specification for builtin types.
'{:*^30}'.format('centered')  # Ok
'{:>10}'.format('value')  # Ok
'{:;]}'.format('value')  # False Negative. No issue even if it is a bug

# Example of a type with a dedicated format specification: datetime
import datetime
d = datetime.datetime(2020, 1, 1, 1, 1, 1)
'{:%Y-%m-%d %H:%M:%S}'.format(d)  # Ok
# It even allows crazy things like this, which is why we don't want to cover format specification.
'{:%Y-%m-%d %H:%M:%=][;]}'.format(d)  # Ok.

# Documentation about nested fields in format specification:
# "A format_spec field can also include nested replacement fields within it. These nested
# replacement fields may contain a field name, conversion flag and format specification,
# but deeper nesting is not allowed. The replacement fields within the format_spec are
# substituted before the format_spec string is interpreted. This allows the formatting of
# a value to be dynamically specified."

# We only care about nested fields to know the number and name of arguments which are expected.
# See "Number of positional arguments" section below.

# As we won't check format specification we won't either check if it is valid once nested
# fields are replaced. This is just a more complex case of format specification.
'{0:{fill}{align}}'.format('0', fill=1, align=2)  # Ok. Valid format
'{0:{fill}{align}}'.format('0', fill=1, align="arf")  # False Negative. Invalid format specifier because "arf" is added


#######################################################################
# Out of scope: Detect that the type of arguments do not match the type
# specified in replacement fields' format
#######################################################################

# The "type" is part of the "Format Specification"
# https://docs.python.org/3/library/string.html#format-specification-mini-language].
# Contrary to %-format, each formattable type may define how the format specification
# is to be interpreted. This means that ":d" will be interpreted one way for a number,
# and another way for a date.
# There is a "standard" format specifier which works for builtin types, but I think
# we can skip it for a first version. Pylint doesn't validate it, there is already a
# lot to do without covering this, and I believe we will have enough value without it.

# You usually don't need to specify the type for the str.format method. It
# will work out of the box. Thus we can expect it to be less common, even if
# it is still used quite often:
# https://sourcegraph.com/search?q=%7B%5Ba-zA-Z0-9%5D*%3A%5B%5E%7B%5D%2B%7D%5B%5E%5C%22%5D%2B%5C%22.format%5C%28+count%3A1000&patternType=regexp

'{:d}'.format('test')  # False Negative
'{:d}'.format(42)  # Ok
'{:d}'.format(Map())  # False Negative
'{:d}'.format(Exception())  # False Negative


##########################################################
# Case to cover: Detect when there are less arguments than
# replacement fields.
##########################################################

'{} {}'.format('one')  # Noncompliant. Too few arguments
'{{}} {}'.format('one')  # Ok. "{{" is equivalent to "{" and "}}" is equivalent to "}"

# Nested format strings
'{:{}} {:{}}'.format('one', 'two', 'three')  # Noncompliant. Too few arguments.
# Each "{:{}}"" asks for two arguments, one for the value itself, and one for the format.
# You could have more nested fields.

# Having too many arguments works, it is only a code smell. Covered by RSPEC-3457
'{} {}'.format('one', 'two', 'three')  # Ok

# Having too many arguments works, it is only a code smell. Covered by RSPEC-3457
'{:{}} {}'.format('one', 's', 'three', 'four')  # Ok

# Note: this is not a nesting. The braces {} are used as a key here.
# Fields can only be nested in the format, i.e. after ":"
'{0[{}]}'.format({"{}": 0})  # Ok

'{0} {0}'.format('one')  # Ok
'{0} {1}'.format('one')  # Noncompliant. No argument matching index 1

###############################################
# Case to cover: Detect when replacement fields
# mix automatic and manual field numbering
###############################################

'{0} {}'.format('one', 'two')  # Noncompliant.
'{} {0}'.format('one', 'two')  # Noncompliant.


##########################################################
# Case to cover: Detect when there are less arguments than
# replacement fields.
##########################################################

'{a} {b}'.format(a=1, b=2)  # Ok.
'{a} {a}'.format(a=1)  # Ok.
'{a} {{z}}'.format(a=1)  # Ok.
'{a} {b}'.format(a=1)  # Noncompliant. Missing key b
'{} {b}'.format(1)  # Noncompliant. Missing key b

'{0} {a}'.format('pos', a='one')  # Ok.
'{} {a}'.format('pos', a='one')  # Ok.
'{} {a}'.format('pos')  # Noncompliant. Missing field "a"
'{} {a}'.format(a='one')  # Noncompliant. Missing field 0
'{0} {a}'.format(a='one')  # Noncompliant. Missing field 0


#################################################################
# Out of scope: Detect unused arguments, i.e. too many arguments.
# This is covered by RSPEC-3457.
#################################################################

'{a}'.format(a=1, b=2)  # No issue. Covered by RSPEC-3457.
'{}'.format(1, 2)  # No issue. Covered by RSPEC-3457.


##########################################################################
# Case to cover: Handle properly formatted strings which are concatenated.
##########################################################################

# Example: https://github.com/ray-project/ray/blob/97430b2d0fd835faa5aa012171bcd3a153b42a9d/python/ray/serve/backend_worker.py#L200-L204

# implicit concatenation is done at compile time
("{}"
 " concatenated".format(1))  # Ok

("{}"
 " {}".format(1))  # Noncompliant

# concatenation with "+" is done at runtime
("{}" +
 " concatenated".format(1))  # Too many arguments. Covered by RSPEC-3457.

("{}" +
 " {}".format(1))  # Ok


#################################################################################
# Case to cover: Detect all these issues when the formatted string is a variable.
#################################################################################
# This is quite frequent: https://sourcegraph.com/search?q=msg%5C.format%5C%28+lang:%22python%22+count:1000&patternType=regexp
# Pylint doesn't detect this

format_string = '{} {} {} {}'

# format string in a variable
format_string.format("1", 2, 3)  # Noncompliant.


##################################################################
# Out of scope: The rule is disabled if parameters are unpacked in
# the .format(...) call.
##################################################################
# Happens but not that often: https://sourcegraph.com/search?q=msg%5C.format%5C%28%5B%5E%29%5D*%5C*+lang:%22python%22+count:1000&patternType=regexp
# Most of the time the dict or sequence is built dynamically, which means that we won't be able to know
# what keys/values they have. This happens less often so it is not worth the effort for now.

dict_data = {'one': '1', 'two': 2}
tuple_data = ("1", 2, 3)

'{} {} {} {}'.format(*tuple_data)  # False Negative.
'{one} {two} {three}'.format(**dict_data)  # False Negative.

#####################################################################################
# Out of scope: When a replacement field calls __getitem__ on its argument, i.e. when
# it is of the form "{myfield[key]}", we don't try to detect if a key exists.
#####################################################################################
# Pylint detects this
# Happens but not that often: https://sourcegraph.com/search?q=%5C%5D%7D%5B%5E%5C%22%5D%2B%5C%22%5C.format+lang:%22python%22+count:1000&patternType=regexp#23
# Not worth it for a first implementation.

a_dict = {'one': 1}
a_list = [1, 2, 3]

'{p[one]} {p[two]}'.format(p={'one': 1, 'two': 2})  # Ok. Access the keys "one" and "two" of argument "p".
'{p[1]} {p[two]}'.format(p={1: 1, 'two': 2})  # Ok

# Out Of Scope. Detecting that an object doesn't have the requested key
'{p[one]} {p[unknown]}'.format(p={'one': 1})  # False Negative. Pylint detects it.
'{p[0]} {p[42]}'.format(p=[1, 2, 3])  # False Negative. Pylint detects it.

# Out Of Scope. Detecting that the object doesn't implements __getitem__
# This should be covered later by RSPEC-5644
'{p[one]} {p[unknown]}'.format(p=A())  # False Negative. Pylint detects it.
'{p[one]} {p[unknown]}'.format(p=Map())  # Ok


##########################################################################################
# Out of scope: When a replacement field access an attribute, i.e. when
# it is of the form "{myfield.attribute}", we don't try to detect if the attribute exists.
##########################################################################################
# Pylint detects this
# Happens but not that often: https://sourcegraph.com/search?q=%5C.%5Ba-z%5D%7D%5B%5E%5C%22%5D%2B%5C%22%5C.format+lang:%22python%22+count:1000&patternType=regexp#4
# Not worth it for a first implementation.

'{a.field}'.format(a=A())
'{0.field}'.format(A())

# Out of scope. Detecting that an unknown field is accessed
# This should be covered later by RSPEC-5755
'{a.unknown}'.format(a=A())  # False Negative. Pylint detects it.


###################################################################################
# Out of scope: It is possible to "save" a reference to the "format" method in a
# variable of a string and later call it. We don't try to validate such formatting.
###################################################################################
# Pylint detects this
# This is quite rare: https://sourcegraph.com/search?q=%3D%5Cs*%5C%22%5B%5E%5C%22%5D%2B%5C%22%5C.format%5Cn+lang:%22python%22+count:1000&patternType=regexp
# Not worth it for a first implementation.

def format_assignment():
    var = '{} {}'.format
    var(1)  # False Negative. Too few arguments.
    var(1, 2)
    var(1, 2, 3)  # False Negative. Too many arguments.
