# Example: https://github.com/v8/v8/commit/4d2659a706bf02cbea7387e2a8e7b289f016d81b
# Pylint test cases: https://github.com/PyCQA/pylint/blob/527db314ecc00ad79be083dcca6134bb68c3bb60/tests/functional/b/bad_open_mode_py3.py

################################################################################
# We should follow pylint's implementation: https://github.com/PyCQA/pylint/blob/4756b3c611ef710c99b51d2fe5f04d72b28e75d6/pylint/checkers/stdlib.py#L52-L79
# It doesn't seem to rise false positives.
################################################################################

path = "test.txt"
# With python 3 the following fails
# With python 2.7.16 "open" will just ignore the "w" flag
with open(path, "aw") as f:  # Noncompliant
    pass

# Pass mode by keyword
open(path, mode="aw")  # Noncompliant

open(path, "a")
open(path, "r")
open(path, "w")
open(path, "x")
open(path, "ab")
open(path, "rb")
open(path, "wb")
open(path, "xb")
open(path, "at")
open(path, "rt")
open(path, "wt")
open(path, "xt")
open(path, "ab+")
open(path, "a+b")
open(path, "+ab")
open(path, "a+b")
open(path, "+ta")
open(path, "br")
open(path, "xb")
open(path, "+rUb")  # Noncompliant. Pylint accepts it but it will fail, at least in python 3
open(path, "x+b")
open(path, "Ut")
open(path, "Ubr")

open(path, "wtb")  # Noncompliant
open(path, "rwx")  # Noncompliant
open(path, "ww")  # Noncompliant
open(path, "+")  # Noncompliant
open(path, "xw")  # Noncompliant
open(path, "Ua")  # Noncompliant
open(path, "Ur++")  # Noncompliant
open(path, "z")  # Noncompliant
