# Locations and messages for %-format

"%?3.5lo blabla" % 42  # Noncompliant
#^^^^^^^^^^^^^^^ Primary message: Fix this formatted string's syntax.


"%(key)s %s" % {"key": "str", "other": "str"}  # Noncompliant
#^^^^^^^^^^^  Primary message: Name unnamed conversion specifiers.


'%s %s' % ['a', 'b']  # Noncompliant
#         ^^^^^^^^^^ Primary message: Replace this formatting argument with a tuple.

'' % 'a'  # Noncompliant
#^  Primary message: Add replacement(s) field(s) to this formatted string.

'%(one)s %(two)s' % ('one', 'two')  # Noncompliant
#                   ^^^^^^^^^^^^^^ Primary message: Replace this formatting argument with a mapping.

"%(key)s %s" % {"key": "str", "other": "str"}  # Noncompliant
#^^^^^^^^^^^  Primary message: Use only positional or only named field, don't mix them.

'%d' % '42'  # Noncompliant
#      ^^^^ Primary Message: Replace this value with a number as "%d" requires.


'%(a)X %(a)s' % {"a": 1.5}  # Noncompliant
#                     ^^^ Primary message: Replace this value with an integer as "%X" requires.


"%*.*le" % (3.2, 5, 1.1234567890)  # Noncompliant
#           ^^^  Primary message:  Replace this value with an integer as "*" requires.


'%s %s' % ('one',)  # Noncompliant. Too few argumennts
#         ^^^^^^^^   Primary message: Add 1 missing argument.


'%s %s' % ('one', 'two', 'three', 'four')  # Noncompliant.
#                        ^^^^^^^^^^^^^^^  Primary message: Remove 2 unexpected arguments.


"%(1)s" % {1: "str"}  # Noncompliant. Keys have to be string
#          ^ Primary message: Replace this key; %-format accepts only string keys.


"%(a)s %(b)s %(c)s" % {"a": "str"}  # Noncompliant x 2
#                     ^^^^^^^^^^^^ Primary message: Provide a value for field "b".
#                     ^^^^^^^^^^^^ Primary message: Provide a value for field "c".


("%s"
 " %s" % (1,))  # Noncompliant
#        ^^^^  Primary message: Add 1 missing argument.


#######################################
#  With a variable as left hand operand
#######################################

format_string = "{0 blablabla"
#               ^^^^^^^^^^^^^^ Secondary location
format_string % "1"  # Noncompliant.
#^^^^^^^^^^^^ Primary message: Fix this formatted string's syntax.


###########################################
#  With variables in the right hand operand
###########################################

a_string = 'a string'
'%d' % a_string  # Noncompliant
#      ^^^^^^^^ Primary Message: Replace this value with a number as "%d" requires.

'%d' % (a_string,)  # Noncompliant
#       ^^^^^^^^ Primary Message: Replace this value with a number as "%d" requires.

'%(p)d' % {"p": a_string}  # Noncompliant
#               ^^^^^^^^ Primary Message: Replace this value with a number as "%d" requires.