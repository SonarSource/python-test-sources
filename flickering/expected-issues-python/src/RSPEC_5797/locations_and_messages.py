def func():
#   ^^^^^^ Secondary location. Message: "Function definition"
  pass

def using_func():
  if func:  # Noncompliant
#    ^^^^  Primary location. Message: "Call this function; as a condition it is always True.""
    pass


# ===============================================

class MyClass:
#     ^^^^^^^ Secondary location. Message: "Class definition"
  pass

def using_func():
  if MyClass:  # Noncompliant
#    ^^^^^^^  Primary location. Message: "Call this class; as a condition it is always True.""
    pass


# ===============================================


def variables(param):
    if param:
        an_int = 1
    else:
        an_int = 2
    
    an_int = 0
#   ^^^^^^^^^^ Secondary location. Message: "Last assignment"
    if abs(param) or an_int and param:  # Noncompliant.
#                    ^^^^^^  Primary location. Message: "Replace this expression; used as a condition it will always be constant."
        pass


# ===============================================

def literal(param):
  if param and {1, 2, 3}:
#              ^^^^^^^^^ Primary location. Message: "Replace this expression; used as a condition it will always be constant."
    pass

# ===============================================

import math
#      ^^^^ Secondary location. Message: "Module imported here"

def modules(param):
  if param and math:
#              ^^^^ Primary location. Message: "Replace this expression; used as a condition it will always be constant."
    pass