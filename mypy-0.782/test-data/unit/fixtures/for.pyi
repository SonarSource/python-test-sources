# builtins stub used in for statement test cases

from typing import TypeVar, Generic, Iterable, Iterator, Generator
from abc import abstractmethod, ABCMeta

t = TypeVar('t')

class object:
    def __init__(self) -> None: pass

class type: pass
class tuple(Generic[t]):
    def __iter__(self) -> Iterator[t]: pass
class function: pass
class bool: pass
class int: pass # for convenience
class str: pass # for convenience

class list(Iterable[t], Generic[t]):
    def __iter__(self) -> Iterator[t]: pass
