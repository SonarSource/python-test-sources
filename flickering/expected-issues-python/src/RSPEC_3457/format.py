# See documentation: https://docs.python.org/3/library/string.html#format-string-syntax
#                    https://docs.python.org/3/library/stdtypes.html#str.format
#
# Note that this rule focuses on code smells.
# See RSPEC-2275 for formatting bugs.

############################################
# Case to cover: Unused positional arguments
############################################

# Too many positional args
'{} {}'.format('one', 'two', 'three')  # Noncompliant.

# With nesting
'{:{}} {}'.format('one', 's', 'three', 'four')  # Noncompliant
'{0:{1}} {2}'.format('one', 's', 'three', 'four')  # Noncompliant

# Note: Braces can only be nested in "format specifiers", i.e after a ":"
# In the following example a positional argument is accessed with __getitem__ and the key "{}".
# We don't have to necessarily support such cases. If it is too complex we could simply exclude
# format strings using nesting. The main idea is to not raise False Positives because we miscounted
# the number of required arguments.
'{0[{}]}'.format({"{}": 0})  # Ok

#######################################
# Case to cover: Unused named arguments
#######################################

# Too many named args
'{a}'.format(a=1, b=2)  # Noncompliant

# With nesting
'{a:{b}} {c}'.format(a='one', b='s', c='three', d='four')  # Noncompliant


#####################################################
# Be careful with string concatenation and formatting
#####################################################

# implicit concatenation is done at compile time
("{}"
 " concatenated".format(1))  # Ok

# concatenation with "+" is done at runtime
("{}" +
 " concatenated".format(1))  # Noncompliant