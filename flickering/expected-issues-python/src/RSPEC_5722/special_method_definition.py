# Sources:
# * standard methods: https://docs.python.org/3/reference/datamodel.html
# * copy module: https://docs.python.org/3/library/copy.html
# * pickle module: https://docs.python.org/3/library/pickle.html
# * python 2: https://docs.python.org/2.7/reference/datamodel.html
# * fspath: https://www.python.org/dev/peps/pep-0519/#protocol

# Methods
# * No issue because missing a "self" parameter is covered by RSPEC-5720 and there is no maximum number of parameters: __new__, __init__, __call__
# * At least one "class" argument: __new__, __init_subclass__
# * Two parameters including the first class argument: __class_getitem__
# * Only "self" parameter: __del__, __repr__, __str__, __bytes__, __hash__, __bool__, __dir__, __len__, __length_hint__, __iter__, __reversed__, __neg__, __pos__, __abs__, __invert__, __complex__, __int__, __float__, __index__, __trunc__, __floor__, __ceil__, __enter__, __await__, __aiter__, __anext__, __aenter__, __getnewargs_ex__, __getnewargs__, __getstate__, __reduce__, __copy__, __unicode__, __nonzero__, __fspath__
# * "self" + 1 parameter: __format__, __lt__, __le__, __eq__, __ne__, __gt__, __ge__, __getattr__, __getattribute__, __delattr__, __delete__, __instancecheck__, __subclasscheck__, __getitem__, __missing__, __delitem__, __contains__, __add__, __sub__, __mul__, __matmul__, __truediv__, __floordiv__, __mod__, __pow__, __divmod__, __lshift__, __rshift__, __and__, __xor__, __or__, __radd__, __rsub__, __rmul__, __rmatmul__, __rtruediv__, __rfloordiv__, __rmod__, __rpow__, __rdivmod__, __rlshift__, __rrshift__, __rand__, __rxor__, __ror__, __iadd__, __isub__, __imul__, __imatmul__, __itruediv__, __ifloordiv__, __imod__, __ipow__, __ilshift__, __irshift__, __iand__, __ixor__, __ior__, __round__, __setstate__, __reduce_ex__, __deepcopy__, __cmp__, __div__
# * "self" + 2 parameters: __setattr__, __get__, __set__, __setitem__, __set_name__
# * "self" + 3 parameters: __exit__, __aexit__


class A:
    def __mul__(self, other, unexpected):  # Noncompliant. Too many parameters
        return 42

    def __add__(self):  # Noncompliant. Missing one parameter
        return 42

    def __eq__(self, other, with_default=42):  # default values are accepted
        return with_default


A() * 3
A() + 3

class Compliant:
    def __mul__(self, other):
        return 42

    def __add__(self, other):
        return 42

A() * 3
A() + 3