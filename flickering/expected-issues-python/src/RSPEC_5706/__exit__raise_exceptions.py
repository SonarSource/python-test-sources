class MyContextManager:
    def __enter__(self, stop_exceptions):
        return self
    def __exit__(self, *args):
        raise  # Noncompliant
        raise args[1]  # Noncompliant

class MyContextManager:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        raise exc_value # Noncompliant

class MyContextManager:
    def __enter__(self, stop_exceptions):
        return self
    def __exit__(self, *args):
        try:
            print("42")
        except:
            print("exception")
            raise  # Ok
        raise MemoryError("No more memory")  # Ok

class MyContextManager:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        # by default the function will return None, which is always False, and the exc_value will naturally raise.
        pass
