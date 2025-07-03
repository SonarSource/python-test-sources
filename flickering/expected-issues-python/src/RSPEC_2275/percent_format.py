# Old style formatting with "%"
# https://docs.python.org/3/library/stdtypes.html#printf-style-string-formatting
# https://pyformat.info/

# pylint: disable=pointless-statement,expression-not-assigned

# Pylint validation code:
# https://github.com/PyCQA/pylint/blob/1e05190ef09f6bdb3d4ce8573e2548853df30cdf/tests/functional/s/string_formatting_py3.py


########################################################
# Case to cover: Detect syntax errors in format strings.
########################################################
# See the link to the documentation above. It describes the valid syntax.

"%(key)s" % {"key": "str"}  # Ok

# truncated replacement field
"%" % "str"  # Noncompliant
"%(key)" % {"key": "str"}  # Noncompliant
"%(keys" % {"key": "str"}  # Noncompliant

# Invalid format character
# let's take a valid format string and replace different parts with a "?" which makes it invalid.
"%#3.5lo" % 42  # Ok
"%?3.5lo" % 42  # Noncompliant
"%#?.5lo" % 42  # Noncompliant
"%#3?5lo" % 42  # Noncompliant
"%#3.?lo" % 42  # Noncompliant
"%#3.5?o" % 42  # Noncompliant
"%#3.5l?" % 42  # Noncompliant

# width and precision are read from the tuple when * is used
"%*.*le" % (3, 5, 1.1234567890)  # Ok.
# The first argument is used as the width.
# The second argument is used as the precision.
# The third argument is the formatted value.


# Extreme cases listed here just to validate the rule once it is implemented.
"%()s" % {"": "str"}  # Ok. Parenthesises indicate that this is a named key, the key is simply an empty string.
"(%()s)" % {"": "str"}  # Ok. Adding parenthesises doesn't change the field.
"%%%()s" % {"": "str"}  # Ok. %% is the equivalent of %. Thus %%%s is just % followed by a replacement field.
"%(k+ey\\)s" % {"k+ey\\": "str"}  # Ok. A replacement field with strange characters in its name.


# Mixing positional and named conversion specifiers
"%(key)s %s" % {"key": "str", "other": "str"}  # Noncompliant
"%(key)*s" % {"key": "str"}  # Noncompliant. "*" requires a positional agument

"%(key)s %%s" % {"key": "str", "other": "str"}  # Ok
"%%(key)s %s" % 42  # Ok


####################################################################################
# Case to cover: Detect mismatches between types requested by the replacement field,
# and provided arguments types.
####################################################################################

# See pylint implementation: https://github.com/PyCQA/pylint/blob/369d952c7e5df010932cf89e528b2f6e9ff08dd6/pylint/checkers/strings.py#L234-L248

class A:
    pass

'%s' % (A(),)  # Ok. Anything can be formatted with %s.
'%r' % (A(),)  # Ok. Anything can be formatted with %r.
'%a' % (A(),)  # Ok. Anything can be formatted with %a.

# %d, %i, %u, %e, %E, %f, %F, %g, %G require a number (float, int, etc...)
'%d' % (1,)  # Ok
'%d' % (1.2,)  # Ok
'%d' % (A(),)  # Noncompliant.
'%i' % (A(),)  # Noncompliant.
'%u' % (A(),)  # Noncompliant.
'%e' % (A(),)  # Noncompliant.
'%E' % (A(),)  # Noncompliant.
'%f' % (A(),)  # Noncompliant.
'%F' % (A(),)  # Noncompliant.
'%g' % (A(),)  # Noncompliant.
'%G' % (A(),)  # Noncompliant.

# %o, %x, %X require an INTEGER. Floats are not accepted.
'%o' % (1,)  # Ok
'%o' % (1.2,)  # Noncompliant.
'%o' % (A(),)  # Noncompliant. 
'%x' % (A(),)  # Noncompliant.
'%X' % (A(),)  # Noncompliant.

#  %c requires an INTEGER or a single character string.
'%c' % ("a",)  # Ok.
'%c' % (1,)  # Ok.
'%c' % (1.5,)  # Noncompliant.
'%c' % ("ab",)  # Noncompliant.
'%c' % (A(),)  # Noncompliant.


# width and precision passed via * should be integers
# The "*" specifier eats an argument every time.
"%*.*le" % (3, 5, 1.1234567890)  # Ok
"%*.*le" % (3.2, 5, 1.1234567890)  # Noncompliant
"%*.*le" % (3, 5.2, 1.1234567890)  # Noncompliant
# Here the last "*" receives a float (3.3) and it fails.
"%*.*le %s %.*e" % (3, 5, 1.1234567890, "a string", 3.3, 0.987654321)  # Noncompliant


# Some additional examples just to validate the rule once it is implemented
'%(a)d %(a)s' % {"a": 1}  # Ok
'%(a)d %(a)s' % {"a": "str"}  # Noncompliant


###########################################################################
# Case to cover: Detect when the right hand side operator of the % operator
# does not have the correct type.
###########################################################################

# If the formatted string contains a single replacement field, the right and
# argument may be a single non-tuple object.
'%s' % A()  # Ok

# Otherwise, the right hand argument must be a tuple with exactly the number
# of items specified by the format string...
'%s %s' % A()  # Noncompliant
'%s %s' % ['a', 'b']  # Noncompliant
'%s %s' % ('one', 'two')  # Ok


# ... or a single mapping object (for example, a dictionary).
# https://docs.python.org/3/glossary.html#term-mapping
# https://docs.python.org/3/library/collections.abc.html#collections-abstract-base-classes

# For builtin types which are defined in Typeshed. They should inherit Mapping or MutableMapping.
'%(one)s %(two)s' % {'one': '1', 'two': 2}  # Ok
'%(one)s %(two)s' % ('one', 'two')  # Noncompliant. Not a mapping

# For custom classes we can consider that any class NOT implementing __getitem__ IS NOT a mapping.
class Map:
    def __getitem__(self, key):
        return 42

'%(one)s %(two)s' % A()  # Noncompliant
'%(one)s %(two)s' % Map()  # Ok



#################################################################################
# Case to cover: Detect when the number of replacement fields is greater or lower
# than the number of arguments when arguments are positionsl. Contrary to the
# "format" method, having too many arguments will fail.
#################################################################################

'' % ('one',)  # Noncompliant. Too many arguments.
'%s %s' % ('one',)  # Noncompliant. Too few arguments.
'%s %s' % ('one', 'two', 'three')  # Noncompliant. Too many arguments.
'%s' % ('one', 'two', 'three')  # Noncompliant. Too many arguments.
'%s' % ('one', 'two')  # Noncompliant. Too many arguments.

'%s %%s' % ('one')  # Ok. %%s is not a replacement field as %% is equivalent to the character %


################################################################################
# Case to cover: When replacement fields are named, detect when a key is missing
# in the provided mapping.
################################################################################

# Missing key
"%(key)s" % {}  # Noncompliant
"%(1)s" % {1: "str"}  # Noncompliant. Keys have to be string

# Out of scope. This rule won't raise any issue when too many arguments are provided.
# This doesnt fail so it is covered by RSPEC-3457 which is a code smell rule.
"%(key)s" % {"key": "str", "other": "key"}  # Ok
"%%(key)s" % {"other": "str"}  # OK. Pylint FP

# Duplicate key is ok
"%(key)s %(key)s" % {"key": "str"}  # Ok



##########################################################################
# Case to cover: Handle properly formatted strings which are concatenated.
##########################################################################

# Example: https://github.com/0xProject/0x-monorepo/blob/fe36cd86bb3e0308d940acbaa26daeead2ddc49e/python-packages/sra_client/src/zero_ex/sra_client/api/relayer_api.py#L100
# Implicit concatenation is done at compile time
("%s"
 " concatenated" % (1,))  # Ok

("%s"
 " %s" % (1,))  # Noncompliant

# concatenation with "+" is done at runtime
("%s" +
 " concatenated" % (1,))  # Noncompliant

("%s" +
 " %s" % (1,))  # Ok


#################################################################################
# Case to cover: Detect all these issues when the formatted string is a variable.
#################################################################################

# when the format string is in a variable we validate the formatting
# Examples: https://sourcegraph.com/search?q=msg%5Cs%25%5Cs%5C%28+lang:%22python%22+count:1000&patternType=regexp
format_string = '%s %s %s %s'
format_string % ("1", 2, 3)  # Noncompliant.


#################################################################################
# Case to cover: when the format string requires only one positional argument, we
# validate the type of this argument
#################################################################################

# This happens very often: https://sourcegraph.com/search?q=%5C%22%5Cs%25%5Cs%5Ba-z%5D+lang:%22python%22+count:1000&patternType=regexp
def right_is_variable():
    a_string = 'a string'
    '%d' % a_string  # Noncompliant


##################################################################################
# Case to cover: when an argument in a tuple or mapping is a variable, we validate
# the type of this argument
##################################################################################
# we validate the type of variables in tuples and dicts literals
def right_is_variable2():
    a_string = 'a string'
    '%d' % (a_string,)  # Noncompliant
    '%(p)d' % {"p": a_string}  # Noncompliant


################################################################
# OUT OF SCOPE: We don't analyze string formatting when the
# string requires multple parameters and the right hand operator
# of "%" is a variable.
#################################################################
# In most cases the variable won't be a literal or it will be
# assigned multiple times. Thus it would be very comples to
# detect anything.
# https://sourcegraph.com/search?q=%25s%5B%5E%25%5C%22%5D%2B%25s%5B%5E%25%5C%22%5D%2B%5C%22%5Cs%25%5Cs%5Ba-z%5D+lang:%22python%22+count:1000&patternType=regexp
dict_data = {'one': '1', 'two': 2}
tuple_data = ("1", 2, 3)
'%s %s %s %s' % tuple_data  # False Negative.
'%(one)d %(two)d' % dict_data  # False Negative.


##################################################################
# Out Of Scope: We don't raise issues when the right hand operand
# of the % operator is a tuple or a mapping, and unpacking is used
# in this tuple or mapping.
##################################################################
'%s %s %s %s' % (*tuple_data,)  # False Negative. Pylint detects it
'%(unknown)s %(two)d' % {**dict_data}  # False Negative.
