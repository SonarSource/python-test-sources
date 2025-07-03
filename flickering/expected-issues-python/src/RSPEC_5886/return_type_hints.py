from typing import List, SupportsFloat, Set, Dict, NoReturn, Text, Generator


def my_str_nok() -> str:
    return 42  # Noncompliant


def my_str_ok() -> str:
    return "hello"


def my_int_nok() -> int:
    return "42"  # Noncompliant


def my_int_ok() -> int:
    return 42


def my_none_nok() -> None:
    return 42  # Noncompliant


def my_none_ok() -> None:
    print("hello")


def my_noreturn() -> NoReturn:
    """NoReturn functions should never return normally. To be checked with actual usage on Peach to avoid noise"""
    return None  # Noncompliant


def collections():
    def my_list_nok() -> List:  # Noncompliant
        return 42

    def my_list_ok() -> List:
        return [42]

    def my_set() -> Set:
        return {}  # Noncompliant ( {} is empty dict literal)

    def my_set() -> Set:
        return {42}  # OK

    def my_dict() -> Dict:
        return {}  # OK


def type_aliases():
    """We should avoid FPs for type aliases used as type hint"""

    def my_supports_float() -> SupportsFloat:
        return 42  # OK

    def my_supports_float() -> SupportsFloat:
        return "42"  # Acceptable FN

    def returns_text() -> Text:
        return "Hello"  # OK


def other_returns():
    def my_int(param) -> int:
        if param:
            return 42
        else:
            return "42"  # Noncompliant

    def my_int_2(param) -> int:  # Noncompliant
        if param:
            return 42
        else:
            print("hello")

    def my_int_3() -> int:  # Noncompliant
        return

    def my_int_4() -> int:  # Noncompliant. may return None. But we should check on Peach as this could be quite noisy.
        try:
            print("hello")
        except IndexError as e:
            return 3


def custom_classes():
    class A:
        ...

    class B(A):
        ...

    def my_func() -> A:
        return B()  # OK

    def my_func2() -> B:
        return A()  # Noncompliant


def generators():
    def my_generator() -> Generator:
        for i in range(10):
            yield i
        return "nothing left"  # OK, still yield a generator

    def my_generator_2() -> Generator[str]:
        for i in range(10):
            yield i  # Out of scope FN
        return "nothing left"  # OK, still yield a generator


def out_of_scope():
    def my_list_oos() -> List[str]:
        return [1, 2, 3]  # FN

    def my_list_oos2() -> List[str]:
        return [1, "my_str", 2]  # OK

    def my_list_oos3() -> List[str]:
        x = 1
        y = 2
        return [x, y]  # FN

    def my_list_oos4() -> List[str]:
        x = 1
        y = 2
        my_list = [x, y]
        print("hello")
        my_list.append(3)
        return my_list  # FN

    def my_set_str() -> Set[str]:
        return {42, 43}  # FN
