class MetaIterable(type):
    __iter__ = None


class MetaOldIterable(type):
    __getitem__ = None


class MetaContainer(type):
    __contains__ = None


class NonIterableClass(metaclass=MetaOldIterable):
    __contains__ = None


class OldNonIterableClass(metaclass=MetaOldIterable):
    __contains__ = None


class NonContainerClass(metaclass=MetaContainer):
    __iter__ = None
