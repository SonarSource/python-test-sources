import logging

##########################################################################################
# Note: this matches the messages from RSPEC_2275/percent_format_locations_and_messages.py
# plus the ones from RSPEC_3457/percent_format_locations_and_messages.py
#
# Note that loggers use the %-format syntax. You can see its documentation here:
# https://docs.python.org/3/library/stdtypes.html#printf-style-string-formatting
##########################################################################################


logging.error("%?3.5lo blabla", 42)  # Noncompliant
#             ^^^^^^^^^^^^^^^^ Primary message: Fix this formatted string's syntax.


logging.error("%(key)s %s", {"key": "str", "other": "str"})  # Noncompliant
#             ^^^^^^^^^^^^  Primary message: Name unnamed replacement field(s).


logging.error('%(a)s %(b)s', ['a', 'b'], 42)  # Noncompliant
#                            ^^^^^^^^^^^^^^ Primary message: Replace formatting argument(s) with a mapping; Replacement fields are named.


logging.error("%(key)s %s", {"key": "str", "other": "str"})  # Noncompliant
#             ^^^^^^^^^^^^  Primary message: Use only positional or only named fields, don't mix them.


logging.error('%d', '42')  # Noncompliant
#                   ^^^^ Primary Message: Replace this value with a number as "%d" requires.


logging.error('%(a)X %(a)s', {"a": 1.5})  # Noncompliant
#                                  ^^^ Primary message: Replace this value with an integer as "%X" requires.


logging.error("%*.*le", 3.2, 5, 1.1234567890)  # Noncompliant
#                       ^^^  Primary message:  Replace this value with an integer as "*" requires.


logging.error('%s %s', 'one')  # Noncompliant.
#             ^^^^^^^   Primary message: Add 1 missing argument(s).


logging.error('%s %s', 'one', 'two', 'three', 'four')  # Noncompliant.
#                                    ^^^^^^^^^^^^^^^  Primary message: Remove 2 unexpected arguments; format string expects 2 arguments.


logging.error("%(1)s", {1: "str"})  # Noncompliant.
#                       ^ Primary message: Replace this key; %-format accepts only string keys.


logging.error("%(a)s %(b)s %(c)s", {"a": "str"})  # Noncompliant x 2
#                                  ^^^^^^^^^^^^ Primary message: Provide a value for field "b".
#                                  ^^^^^^^^^^^^ Primary message: Provide a value for field "c".


logging.error("%s"
#             ^^^^
              " %s", 1)  # Noncompliant
#^^^^^^^^^^^^^^^^^^  Primary message: Add 1 missing argument.

logging.error("%s" +
#             ^^^^^^
              " %s", 1)  # Noncompliant
#^^^^^^^^^^^^^^^^^^  Primary message: Add 1 missing argument.



#####################################################################
# Additional case when a logging call has a message containing %s or
# equivalent with no arguments.
#####################################################################

logging.error("No formatting %s")  # Noncompliant
#             ^^^^^^^^^^^^^^^^^^  Primary message: Add argument(s) corresponding to the message's replacement field(s).