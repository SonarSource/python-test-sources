# See documentation: https://docs.python.org/3/reference/lexical_analysis.html#formatted-string-literals

#####################################################################
# Case to cover:f-string which does not contain any replacement field
#####################################################################
var = 42
print(f"{var}")
print(f"[var]")  # Noncompliant.
print(F"[var]")  # Noncompliant.
print(f'[var]')  # Noncompliant.
print(f"""[var]""")  # Noncompliant.
print(fr"[var]")  # Noncompliant.


################################
# Be careful with concatenations
################################


# We raise ONLY ONE issue if f-strings are concatenated and none of them contain a replacement field.
# This is to reduce the amount of noise.
(f"This is a [var]"
f" and this is the middle"
f" and the sentence conttinue")  # Noncompliant
(f"This is a [var]" +
f" and this is the middle" +
f" and the sentence conttinue")  # Noncompliant


# We won't raise if an f-string doesn't contain any replacement field, but it is concatenated
# with another f-string which contains a replacement field. This is not perfect but it
# might be done just to be consistent.
(f"This is a {var}"
f" and this is the middle"
f" and the sentence conttinue")  # Ok
(f"This is a {var}" +
f" and this is the middle" +
f" and the sentence conttinue")  # Ok


# We should not make any difference between implicit and explicit (with "+"") contatenation.
(f"With +" +
f" no operator"
f" end")  # Noncompliant