class MyNonCallable:
#     ^^^^^^^^^^^^^ Secondary message: Class definition.
    pass

def call_noncallable():
    myvar = MyNonCallable()
#           ^^^^^^^^^^^^^^^  Secondary message: Assigned value.
    myvar()  # Noncompliant
#   ^^^^^  Primary message: Fix this call; "myvar" is not callable.