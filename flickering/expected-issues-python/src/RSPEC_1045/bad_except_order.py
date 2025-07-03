def foo():
    try:
        raise FileExistsError()
    except (OSError, RuntimeError) as e:  # Secondary location. FileExistsError is a subclass of OSError
        print(e)
    except FileExistsError as e:  # Noncompliant
        print("Never executed")
    except FileNotFoundError as e:  # Noncompliant
        print("Never executed")


    try:
        raise FileExistsError()
    except (ArithmeticError, RuntimeError) as e:  # Noncompliant. FileExistsError is a subclass of OSError
        print(e)
    except FloatingPointError as e:  # Secondary location
        print("Never executed")
    except OverflowError as e:  # Secondary location
        print("Never executed")
    
    try:
        raise TypeError()
    except TypeError as e:  # Secondary location
        print(e)
    except TypeError as e:  # Noncompliant. Duplicate Except.
        print("Never executed")
    
    try:
        raise ValueError()
    except BaseException as e: # Secondary location
        print(e)
    except:  # Noncompliant. This is equivalent to the bare "except:" block
        print("Never executed")
    
    try:
        raise ModuleNotFoundError()
    except (ImportError, ArithmeticError) as e: # Secondary location
        print(e)
    except (ValueError, ModuleNotFoundError, FloatingPointError, OverflowError) as e: # Noncompliant
        print(e)