# See Documentation: https://docs.python.org/3/library/logging.html#logging.Logger.debug
#                    https://docs.python.org/3/howto/logging.html

# Logger.debug(), Logger.info(), Logger.warning(), Logger.error(), and Logger.critical()
# all create log records with a message and a level that corresponds to their respective
# method names. The message is actually a format string, which may contain the standard
# string substitution syntax of %s, %d, %f, and so on. The rest of their arguments is a
# list of objects that correspond with the substitution fields in the message. With regard
# to **kwargs, the logging methods care only about a keyword of exc_info and use it to
# determine whether to log exception information.

# https://docs.python.org/3/howto/logging-cookbook.html
# "internally the logging package uses %-formatting to merge the format string and the variable arguments"

# Pylint test code: https://github.com/PyCQA/pylint/blob/303b8d852e469379cd0f1a8891a018de5e39a966/tests/checkers/unittest_logging.py


import logging

#####################################################################################
#
# Every Noncompliant case from %-format strings in RSPEC-2275 and RSPEC-3457 is
# Noncompliant for loggers' messages in RSPEC-3457.
# Loggers won't fail if the format is bad. They will simply log the logging error.
# Thus it is a code smell.
#
# See RSPEC_2275/percent_format.py
# See RSPEC_3457/percent_format.py
#
# The following are additional notes specific to logging.
#
#####################################################################################


################################################################################################
# There are different ways of calling logging methods. Either on the "logging" module itself, or
# by creating a dedicated logger
################################################################################################

logging.error("Foo %s", "Bar")  # Ok
logging.error("Foo %s", "Bar", 'Too many')  # Noncompliant

# It is common to initiate a logger per file. We can reasonably expect that this variable
# will never be of a different type even if it is a module variale.
# Example: https://github.com/django/django/blob/4ed534758cb6a11df9f49baddecca5a6cdda9311/django/views/generic/base.py#L16
module_logger = logging.getLogger('mylogger')
module_logger.error("Foo %s", "Bar")
module_logger.error("Foo %s", "Bar", "too many")  # Noncompliant

# renamed module
import logging as renamed_logging
renamed_logging.error("Foo %s", "Bar", 'Too many')  # Noncompliant


########################################################################
# Case to cover: calling a logging function which has replacement fields
# but no value to replace them with.
########################################################################

# No % formatting operation is performed on msg when no args are supplied.
# We consider as Noncompliant any call to a logging function
# * with a message containing one or more %s or any other replacement fields.
# * without any value to replace them.
logging.error("No formatting %s")  # Noncompliant
logging.error("No formatting %(value)G")  # Noncompliant
logging.error("No formatting")  # Ok. No replacement field.


##################################################################################
# Messages might be split on multiple lines with concatenation when they are long.
##################################################################################

logging.error("%s" +
              " %s", 1)  # Noncompliant

logging.error("%s"
              " %s", 1)  # Noncompliant


##########################################
# Case to cover: Invalid type of arguments
##########################################

# We look at the argument when they are positional...
logging.error("%s %s", 1, 2)  # Ok
logging.error("%s %d", 1, "2")  # Noncompliant
# ... or when they are in a mapping
logging.error("%(a)s %(b)s", {"a": 1, "b": 2})  # Ok
logging.error("%(a)s %(b)d", {"a": 1, "b": "2"})  # Noncompliant


######################################################
# Case to cover: Mixing named and positional arguments
######################################################

# If there is even one named replacement field the second argument should be a mapping
# and there shouldn't be additional arguments.
logging.error("%(a)s %s", {"a": 1}, 2)  # Noncompliant
logging.error("%(a)s %s", 1, {"a": 1})  # Noncompliant
logging.error("%(a)s %(b)s", {"a": 1, "b": 2}, 3)  # Noncompliant


#######################################################################################
# Out of scope: logging.Formatter
#
# The logging framework allows the customization of every message with a "Formatter".
# This formatter might fail if it requires extra arguments and we don't provide them.
# However it would be very complex to make a ling between the Formatter and the logging
# call.
#######################################################################################

customized_logger = logging.getLogger('mylogger')
formatter = logging.Formatter('%(custom)s %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
customized_logger.addHandler(ch)
customized_logger.error("Foo %s", "Bar", extra={"custom": "CUSTOM"})
customized_logger.error("Foo %s", "Bar", extra={"unknown": "CUSTOM"})  # False Negative
