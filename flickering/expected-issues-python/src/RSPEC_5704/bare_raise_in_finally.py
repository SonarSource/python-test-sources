def foo(param):
    result = 0
    try:
        print("foo")
    except ValueError as e:
        pass
    else:
        if param:
            raise ValueError()
    finally:
        if param:
            raise  # Noncompliant. This will fail in some context.
        else:
            result = 1
    return result


def foo(param):
    result = 0
    try:
        print("foo")
    except ValueError as e:
        pass
    else:
        if param:
            raise ValueError()
    finally:
        if not param:
            result = 1
        # the exception will raise automatically
    return result

def finally_in_except():
    try:
        raise TypeError()
    except TypeError:
        try:
            raise OSError()
        finally:
            raise

def raise_in_function():
    try:
        def function():
            print("foo")
            raise
        function()
    except TypeError:
        pass
    finally:
        def function2():
            raise
        function2

    def function3():
        raise
    function3

class MyContextManager(object):
    def __enter__(self):
        return self
    def __exit__(self, *args):
        try:
            print("foo")
        finally:
            # No issue raised when `raise` is in __exit__ method. This exception is from pylint as there could be an exception available
            raise