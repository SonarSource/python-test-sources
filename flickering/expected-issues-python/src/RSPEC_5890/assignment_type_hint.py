from typing import SupportsFloat, List, Iterable, Generator, Set


def assigned_directly():
    my_int_nok: int = "hello"  # Noncompliant
    my_str_ok: str = 42  # Noncompliant
    my_int_ok: int = 42  # OK
    my_str_ok: str = "hello"  # OK


def assigned_later(param):
    a: int
    a = "hello"  # Noncompliant
    b: int
    if param:
        b = 42
    else:
        b = "42"  # Noncompliant

    c: int
    c = 1 if a else 2  # OK
    d: int
    d = 1 if a else "hello"  # Noncompliant


def custom_classes():
    class A:
        ...

    class B(A):
        ...

    my_a_ok: A = A()  # OK
    my_a_ok2: A = B()  # OK
    my_a_nok: A = A
    my_b_nok: B = A()  # Noncompliant
    my_b_ok: B = B()


def get_generator():
    yield 1


def type_aliases():
    """We should avoid raising FPs on type aliases"""
    my_float: SupportsFloat = 42  # OK
    my_iterable: Iterable = []  # OK
    my_generator: Generator = get_generator()  # OK


def collections():
    my_list: List = {}  # Noncompliant

    my_str_list_nok: List[str] = [1, 2, 3]  # Out of scope? (Detected by PyCharm)

    my_str_list_ok: List[str] = ["a", "b", "c"]  # OK

    my_set_nok: Set = {}  # Noncompliant

    my_set_nok2: Set = set  # Noncompliant

    my_set_ok: Set = set()  # OK


def function_params():
    def overwritten_param(param: int):
        param = "hello"  # Out of scope (S1226)

    def used_param(param: int):
        print(param)
        param = "hello"  # Noncompliant
        print(param)


class ClassAttributes:
    my_attr: str = "hello"  # OK
    my_attr_2: str = 42  # Noncompliant

    my_attr_3: str

    def __init__(self):
        self.my_attr_3 = 42  # Noncompliant
