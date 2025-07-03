# A module might be a Shim created to smooth the transition
# when some definitions are moved to another module.

# As seen in numpy
# https://github.com/numpy/numpy/blob/d329a66dbb9710aefd03cce6a8b0f46da51490ca/numpy/core/umath_tests.py
import warnings
# 2018-04-04, numpy 1.15.0
warnings.warn(("numpy.core.umath_tests is an internal NumPy "
               "module and should not be imported. It will "
               "be removed in a future NumPy release."),
              category=DeprecationWarning, stacklevel=2)
from ._umath_tests import *
