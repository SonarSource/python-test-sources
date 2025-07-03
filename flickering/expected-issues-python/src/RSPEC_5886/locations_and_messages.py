def my_str() -> str:
#               ^^^>  {{Return type hint.}}
    return 42  # Noncompliant {{Return a value of type "str" instead of "int" or change the return type hint of function "my_str".}}
#   ^^^^^^^^^

def my_str_empty_return() -> str:
#                            ^^^>  {{Return type hint.}}
    return  # Noncompliant {{Return a value of type "str" instead of "None" or change the return type hint of function "my_str_empty_return".}}
#   ^^^^^^

def my_str_no_return() -> str: # Noncompliant {{Return a value of type "str" or change the return type hint of function "my_str_no_return"; Function may reach its end and return None.}}
#   ^^^^^^^^^^^^^^^^
    ...

def my_str_unknown_return(param) -> str:
#                                   ^^^>  {{Return type hint.}}
    if param:
        x = 42
    else:
        x = {}
    return x  # Noncompliant {{Return a value of type "str" instead of "Union[int, dict]" or change the return type hint of function "my_str_unknown_return".}}
