# https://docs.quantifiedcode.com/python-anti-patterns/correctness/not_using_get_to_return_a_default_value_from_a_dictionary.html


def example1(mydict):
    result = "default"
    if "missing" in mydict:
        result = mydict["missing"]  # Noncompliant
    return result


def example2(mydict):
    if "missing" in mydict:
        result = mydict["missing"]  # Noncompliant
    else:
        result = "default"
    return result


def example3(mydict):
    if "missing" in mydict:
        result = mydict.get("missing")  # Noncompliant
    else:
        result = "default"
    return result


mydict = {"key": "value"}

mydict.get("missing", "default")  # Compliant
