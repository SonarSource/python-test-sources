class MyClass:
    pass

def builtin_functions(param):
    """Some builtin functions are known to have no side effect when they are called."""
    # Constructors and conversion
    set([1, 2])  # Noncompliant
    dict(one=1, two=2)  # Noncompliant
    frozenset([1, 2])  # Noncompliant
    repr(1)  # Noncompliant
    str(param)  # Noncompliant
    ascii(1)  # Noncompliant
    ord("1")  # Noncompliant
    hex(255)  # Noncompliant
    oct(2)  # Noncompliant
    bin(3)  # Noncompliant
    bool(1)  # Noncompliant
    bytes(1)  # Noncompliant
    memoryview(b'a')  # Noncompliant
    bytearray(b'a')  # Noncompliant

    # math
    abs(-1)  # Noncompliant
    round(1.2)  # Noncompliant
    min([1, 2])  # Noncompliant
    max([1, 2])  # Noncompliant
    divmod(1, 2)  # Noncompliant
    sum([1, 2])  # Noncompliant
    pow(1, 2)  # Noncompliant

    # iterable
    sorted([1, 2])  # Noncompliant
    filter(lambda x: x == 2, [1, 2])  # Noncompliant
    enumerate([1, 2])  # Noncompliant
    reversed([1, 2])  # Noncompliant
    range(1, 2)  # Noncompliant
    slice(1, 2)  # Noncompliant
    zip([1], [2])  # Noncompliant

    # other
    help()  # Noncompliant
    dir(1)  # Noncompliant
    id(1)  # Noncompliant
    object()  # Noncompliant
    staticmethod(lambda: 42)  # Noncompliant
    classmethod(lambda: 42)  # Noncompliant
    property(lambda: 42)  # Noncompliant
    type(MyClass)  # Noncompliant
    isinstance(param, MyClass)  # Noncompliant
    issubclass(param, MyClass)  # Noncompliant
    callable(MyClass)  # Noncompliant
    format("")  # Noncompliant
    vars()  # Noncompliant
    locals()  # Noncompliant
    globals()  # Noncompliant
    super(MyClass)


    # builtin functions which are used to validate values, i.e. can they
    # be converted, are they hashable, is it compilable, etc...
    int(param)
    float(param)
    complex(param)
    chr(param)
    len(param)
    iter(param)
    getattr(param, "__doc__")
    compile(param, "")
    hash(param)

    # builtin used to force lazy loading
    hasattr(param, "__doc__")


    # builtin functions which are often misused as 1-line loop.
    list(param)
    tuple(param)
    all(param)
    any(param)
    map(param)
    list()  # False Negative
    tuple()  # False Negative


    # builtin functions having side effects. No issue raised on those.
    delattr(param, "attr")
    setattr(param, "attr", 42)
    next(param)
    input()
    eval("print('foo')")
    open("file")
    breakpoint()
    exec("print('foo')")
    print("printing...")
    __import__("", globals(), locals(), [], 0)


def str_methods():
    """Strings are immutable. None of its methods have a have side effect."""
    s = "string"
    s.capitalize()  # Noncompliant
    s.casefold()  # Noncompliant
    s.center(20, ' ')  # Noncompliant
    s.count('s')  # Noncompliant
    s.endswith('ing')  # Noncompliant
    s.expandtabs(2)  # Noncompliant
    s.find('i')  # Noncompliant
    s.format()  # Noncompliant
    s.format_map({})  # Noncompliant
    s.index('i')  # Noncompliant
    s.isalnum()  # Noncompliant
    s.isalpha()  # Noncompliant
    s.isascii()  # Noncompliant
    s.isdecimal()  # Noncompliant
    s.isdigit()  # Noncompliant
    s.isidentifier()  # Noncompliant
    s.islower()  # Noncompliant
    s.isnumeric()  # Noncompliant
    s.isprintable()  # Noncompliant
    s.isspace()  # Noncompliant
    s.istitle()  # Noncompliant
    s.isupper()  # Noncompliant
    s.join(['1', '2'])  # Noncompliant
    s.ljust(20, ' ')  # Noncompliant
    s.lower()  # Noncompliant
    s.lstrip()  # Noncompliant
    str.maketrans({"s": "1", "t": "2"})  # Noncompliant
    s.partition('t')  # Noncompliant
    s.replace('s', '42', 1)  # Noncompliant
    s.rfind('i')  # Noncompliant
    s.rindex('i')  # Noncompliant
    s.rjust(20, ' ')  # Noncompliant
    s.rpartition('t')  # Noncompliant
    s.rsplit('t')  # Noncompliant
    s.rstrip()  # Noncompliant
    s.split('t')  # Noncompliant
    '111\n222'.splitlines()  # Noncompliant
    s.startswith('str')  # Noncompliant
    s.strip()  # Noncompliant
    s.swapcase()  # Noncompliant
    s.title()  # Noncompliant
    s.translate(str.maketrans({"s": "1", "t": "2"}))  # Noncompliant
    s.upper()  # Noncompliant
    s.zfill(20)  # Noncompliant

    'sdfs'[1]  # Noncompliant. __getitem__ method
    'i' in s  # Noncompliant. __contains__ method

    # Method used to force lazy loading of encodings
    s.encode(encoding='UTF-8', errors='strict')

def bytes_methods():
    b = b"bytes"
    b.capitalize()  # Noncompliant
    b.center(20)  # Noncompliant
    b.count(b'b')  # Noncompliant
    b.decode()  # Noncompliant
    b.endswith(b'es')  # Noncompliant
    b'a\t\tb'.expandtabs(2)  # Noncompliant
    b.find(b'y')  # Noncompliant
    bytes.fromhex(b.hex())  # Noncompliant
    b.hex()  # Noncompliant
    b.index(b'y')  # Noncompliant
    b.isalnum()  # Noncompliant
    b.isalpha()  # Noncompliant
    b.isascii()  # Noncompliant
    b.isdigit()  # Noncompliant
    b.islower()  # Noncompliant
    b.isspace()  # Noncompliant
    b.istitle()  # Noncompliant
    b.isupper()  # Noncompliant
    b.join([b'1', b'2'])  # Noncompliant
    b.ljust(20)  # Noncompliant
    b.lower()  # Noncompliant
    b.lstrip()  # Noncompliant
    bytes.maketrans(b'bytes', b'setyb')  # Noncompliant
    b.partition(b'y')  # Noncompliant
    b.replace(b'b', b'42')  # Noncompliant
    b.rfind(b'y')  # Noncompliant
    b.rindex(b'y')  # Noncompliant
    b.rjust(20)  # Noncompliant
    b.rpartition(b'y')  # Noncompliant
    b.rsplit(b'y')  # Noncompliant
    b.rstrip()  # Noncompliant
    b.split(b'y')  # Noncompliant
    b'line1\nline2'.splitlines()  # Noncompliant
    b.startswith(b'by')  # Noncompliant
    b.strip()  # Noncompliant
    b.swapcase()  # Noncompliant
    b.title()  # Noncompliant
    b.translate(bytes.maketrans(b'bytes', b'setyb'))  # Noncompliant
    b.upper()  # Noncompliant
    b.zfill(20)  # Noncompliant

    b[1]  # Noncompliant. __getitem__ method
    b'y' in b  # Noncompliant. __contains__ method


def bytearray_methods():
    b = bytearray(b'bytes')
    b.capitalize()  # Noncompliant
    b.center(20)  # Noncompliant
    b.count(b'b')  # Noncompliant
    b.decode()  # Noncompliant
    b.endswith(b'es')  # Noncompliant
    b'a\t\tb'.expandtabs(2)  # Noncompliant
    b.find(b'y')  # Noncompliant
    bytes.fromhex(b.hex())  # Noncompliant
    b.hex()  # Noncompliant
    b.index(b'y')  # Noncompliant
    b.isalnum()  # Noncompliant
    b.isalpha()  # Noncompliant
    b.isascii()  # Noncompliant
    b.isdigit()  # Noncompliant
    b.islower()  # Noncompliant
    b.isspace()  # Noncompliant
    b.istitle()  # Noncompliant
    b.isupper()  # Noncompliant
    b.join([b'1', b'2'])  # Noncompliant
    b.ljust(20)  # Noncompliant
    b.lower()  # Noncompliant
    b.lstrip()  # Noncompliant
    bytes.maketrans(b'bytes', b'setyb')  # Noncompliant
    b.partition(b'y')  # Noncompliant
    b.replace(b'b', b'42')  # Noncompliant
    b.rfind(b'y')  # Noncompliant
    b.rindex(b'y')  # Noncompliant
    b.rjust(20)  # Noncompliant
    b.rpartition(b'y')  # Noncompliant
    b.rsplit(b'y')  # Noncompliant
    b.rstrip()  # Noncompliant
    b.split(b'y')  # Noncompliant
    b'line1\nline2'.splitlines()  # Noncompliant
    b.startswith(b'by')  # Noncompliant
    b.strip()  # Noncompliant
    b.swapcase()  # Noncompliant
    b.title()  # Noncompliant
    b.translate(bytes.maketrans(b'bytes', b'setyb'))  # Noncompliant
    b.upper()  # Noncompliant
    b.zfill(20)  # Noncompliant

    b[1]  # Noncompliant. __getitem__ method
    b'y' in b  # Noncompliant. __contains__ method

    # methods having a side effect. No issue raised on those
    b.append(42)
    b.clear()
    b.copy()
    b.extends(b'added')
    b.insert(2, 42)
    b.pop()
    b.remove(42)
    b.reverse()


def memoryview_methods():
    b = memoryview(b'bytes')
    #b.c_contiguous
    b.cast('B')  # Noncompliant
    b.hex()  # Noncompliant
    b.tobytes()  # Noncompliant
    b.tolist()  # Noncompliant
    b.toreadonly()  # Noncompliant
    #b.contiguous
    #b.f_contiguous
    #b.format
    #b.itemsize
    #b.nbytes
    #b.ndim()
    #b.obj
    #b.readonly
    #b.shape
    #b.strides
    #b.suboffsets

    b[1]  # Noncompliant. __getitem__ method
    b'y' in b  # Noncompliant. __contains__ method

    # methods having a side effect. No issue raised on those
    b.release()


def int_methods():
    i = 42
    i.as_integer_ratio()  # Noncompliant
    i.bit_length()  # Noncompliant
    i.conjugate()  # Noncompliant
    int.from_bytes(b'\x10\x00', byteorder='big')  # Noncompliant
    i.to_bytes(1, byteorder='big')  # Noncompliant
    # i.denominator
    # i.imag
    # i.numerator
    # i.real


def float_methods():
    f = 1.0
    f.as_integer_ratio()  # Noncompliant
    f.conjugate()  # Noncompliant
    float.fromhex(f.hex())  # Noncompliant
    f.hex()  # Noncompliant
    f.is_integer()  # Noncompliant
    # f.real
    # f.imag


def complex_methods():
    c = complex(1, 2)
    # no methods


def bool_methods():
    b = True
    b.as_integer_ratio()  # Noncompliant
    b.bit_length()  # Noncompliant
    b.conjugate()  # Noncompliant
    bool.from_bytes(b'\x10\x00', byteorder='big')  # Noncompliant
    b.to_bytes(1, byteorder='big')  # Noncompliant


def list_methods():
    l = [1, 2, 3]
    l.copy()  # Noncompliant
    l.count(1)  # Noncompliant
    l.index(1)  # Noncompliant

    l[1]  # Noncompliant. __getitem__ method
    1 in l  # Noncompliant. __contains__ method

    # methods having a side effect. No issue raised on those
    l.clear()
    l.append(4)
    l.extend([4, 5, 6])
    l.insert(1, 42)
    l.pop()
    l.remove(2)
    l.reverse()
    l.sort()


def tuple_methods():
    t = (1, 2, 3)
    t.count(1)  # Noncompliant
    t.index(1)  # Noncompliant

    t[1]  # Noncompliant. __getitem__ method
    1 in t  # Noncompliant. __contains__ method


def range_methods():
    r = range(10)
    r.count(1)  # Noncompliant
    r.index(1)  # Noncompliant
    r[1]  # Noncompliant. __getitem__ method
    1 in r  # Noncompliant. __contains__ method
    # r.start
    # r.stop
    # r.step


def set_methods():
    s = {1, 2, 3}
    s.copy()  # Noncompliant
    s.difference({2})  # Noncompliant
    s.intersection({2, 5})  # Noncompliant
    s.isdisjoint({5, 6})  # Noncompliant
    s.issubset({1, 2, 3, 4, 5})  # Noncompliant
    s.issuperset({2})  # Noncompliant
    s.symmetric_difference({2})  # Noncompliant
    s.union({2, 4, 5})  # Noncompliant

    1 in s  # Noncompliant. __contains__ method

    # methods having a side effect. No issue raised on those
    s.add(1)
    s.clear()
    s.difference_update({2})
    s.discard(2)
    s.intersection_update({2, 5})
    s.pop()
    s.remove(2)
    s.symmetric_difference_update({2})
    s.update({2, 4, 5})


def frozenset_methods():
    s = frozenset({1, 2, 3})
    s.copy()  # Noncompliant
    s.difference({2})  # Noncompliant
    s.intersection({2, 5})  # Noncompliant
    s.isdisjoint({5, 6})  # Noncompliant
    s.issubset({1, 2, 3, 4, 5})  # Noncompliant
    s.issuperset({2})  # Noncompliant
    s.symmetric_difference({2})  # Noncompliant
    s.union({2, 4, 5})  # Noncompliant

    1 in s  # Noncompliant. __contains__ method


def dict_methods():
    d = {'a': 1, 'b': 2, 'c': 3}
    d.copy()  # Noncompliant
    dict.fromkeys([1, 2, 3, 4], 'value')  # Noncompliant
    d.get('a')  # Noncompliant
    d.items()  # Noncompliant
    d.keys()  # Noncompliant
    d.values()  # Noncompliant

    d['a']  # Noncompliant. __getitem__ method
    'a' in d  # Noncompliant. __contains__ method

    # methods having a side effect. No issue raised on those
    d.clear()
    d.pop()
    d.popitem()
    d.setdefault('d')
    d.update({'g': 42})

#
# IMPORTANT: this isn't necessary true for subclasses
# Example: defaultdict
#
from collections import defaultdict
d = defaultdict(lambda k: 42)
print(d.keys())  # dict_keys([])
d['a']  # accessing the dict modifies it
print(d.keys())  # dict_keys(['a'])


def calling_instance_methods_via_string():
    # Calling instance methods on the class has no side effect either
    str.islower('this is passed as self')  # Noncompliant


def tryExcept():
    """No issue is raised when the statement in a try...except body.
    Such pattern indicates that the statement is expected to raise an exception in some contexts.
    """
    d = {}
    try:
        d[1]
    except IndexError as e:
        d[1]  # Noncompliant

    try:
        int("abc")  # Ok
    except ValueError as e:
        int("abc")  # Noncompliant

    try:
        int("abc")  # Ok
        int("cde")  # Ok
    except ValueError as e:
        pass

    def is_int(param):
        try:
            int(param)  # Ok
            return True
        except ValueError as e:
            return False