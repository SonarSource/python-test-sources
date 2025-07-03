###################################
# Too many positional or named args
###################################

# We will be consistent with RSPEC-930, i.e. we will raise:
# * One issue listing the number of positional arguments which are unused.
# * One issue PER NAMED ARGUMENT which is unused.
'{:{}} [a] {b}'.format('one', 's', 'three', 'four', 'five', a=42, b=2, c=3)  # Noncompliant x 2
#                                                                      ^^^  Issue 1. Primary Message: Remove this unused argument.
#                                                           ^^^^  Issue 2. Primary Message: Remove this unused argument.
#               ^^^^^^  Issue 3. Primary Message: Remove 2 unused positional arguments.

#####################################
# string concatenation and formatting
#####################################

# concatenation with "+" is done at runtime.
("{}" +
 " concatenated".format(1))  # Noncompliant
#                       ^  Primary Message: Remove this unused argument.