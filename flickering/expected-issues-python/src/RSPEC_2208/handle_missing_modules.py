# A module can be used as a way to handle missing modules

# As seen in project spyder.
# https://github.com/spyder-ide/spyder/blob/509f281ff0ede786c15f8fe38c4d95bc2c91fb02/spyder/pyplot.py

try:
    from guiqwt.pyplot import *  # Ok
except Exception:
    from matplotlib.pyplot import *  # Ok


# As seen in pypy
# https://github.com/mozillazg/pypy/blob/576fbd50a1a1a62adebb8de5525d45c26de6f8b1/lib_pypy/readline.py

try:
    from pyrepl.readline import *  # Ok
except ImportError:
    import sys
    if sys.platform == 'win32':
        raise ImportError("the 'readline' module is not available on Windows"
                          " (on either PyPy or CPython)")
    raise
