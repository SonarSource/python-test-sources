import sys

try:
    open("foo.txt", "r")
except SystemExit:  # Noncompliant
    pass
except KeyboardInterrupt:  # No issue raised but be careful when you do this
    pass


try:
    open("bar.txt", "r")
except BaseException:  # Noncompliant
    pass
except:  # Noncompliant
    pass

try:
    open("bar.txt", "r")
except BaseException:  # Noncompliant
    pass
except:  # Noncompliant
    pass


try:
    open("foo.txt", "r")
except SystemExit:
    # clean-up
    raise
except KeyboardInterrupt:
    # clean-up
    raise

try:
    open("foo.txt", "r")
except SystemExit as e:
    # clean-up
    raise e
except KeyboardInterrupt as e:
    # clean-up
    raise e

try:
    open("bar.txt", "r")
except BaseException as e:
    # clean-up
    raise e
except: # Noncompliant
    # clean-up
    raise


try:
    open("bar.txt", "r")
except BaseException as f:
    # clean-up
    exc_info = sys.exc_info()
    # raise the exception ...
except: # Noncompliant
    # clean-up
    exc_info = sys.exc_info()
    # raise the exception ...

# or use a more specific exception

try:
    open("bar.txt", "r")
except FileNotFoundError:
    # process the exception
    pass