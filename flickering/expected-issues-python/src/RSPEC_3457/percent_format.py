# Bug cases are covered by RSPEC-2275

###############################################################
# Case to cover: Unused keys when replacement fields are named.
###############################################################

"%(key)s" % {"key": "str", "other": "key"}  # Noncompliant.

# %% is used to get a single % in the output string. It escapes the `%` character.
"%%(key)s" % {"key": "str"}  # Noncompliant.