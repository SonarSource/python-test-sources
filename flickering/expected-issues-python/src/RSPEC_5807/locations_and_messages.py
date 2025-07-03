var = "unknown"

__all__ = [
    '',  # Noncompliant
#   ^^  Primary message: Change or remove this string; "" is not defined.
    'unknown',  # Noncompliant
#   ^^^^^^^^^  Primary message: Change or remove this string; "unknown" is not defined.
    var  # Noncompliant
#   ^^^  Primary message: Change or remove this string; "unknown" is not defined.
]
