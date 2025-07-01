# Locations and messages for .format method

"{0 blablabla".format(1)  # Noncompliant
#^^^^^^^^^^^^^ Primary message: Fix this formatted string's syntax.


'{0!z}'.format('str')
#^^^^^^ Primary message: Fix this formatted string's syntax; !z is not a valid conversion flag.


'{} {} {}'.format('one')
#^^^^^^^^^  Primary message: Provide a value for field(s) with index 1, 2.


'{0} {1}'.format('one')  # Noncompliant. No argument matching index 1
#^^^^^^^^  Primary message: Provide a value for field(s) with index 1.


'{0} {}'.format('one', 'two')  # Noncompliant.
#^^^^^^^ Primary message: Use only manual or only automatic field numbering, don't mix them.


'{a} {b} {}'.format(a=1)  # Noncompliant.
#^^^^^^^^^^^ Primary message. Provide a value for field "b".
#^^^^^^^^^^^ Primary message. Provide a value for field(s) with index 0.


("%s"
#^^^^
 " %s".format(1))  # Noncompliant
#^^^^^^  Primary message: Provide a value for field at index 1.


##################
#  With a variable
##################

format_string = "{0 blablabla"
#               ^^^^^^^^^^^^^^ Secondary location
format_string.format("1")  # Noncompliant.
#^^^^^^^^^^^^ Primary message: Fix this formatted string's syntax.
