def eight(a1, opt1=1, *, a2, a3, a4, a5, a6, a7, a8, opt2=2):  # Noncompliant.
#         ^^             ^^  ^^  ^^  ^^  ^^  ^^  ^^  Secondary locations
#   ^^^^^ Primary location. Message: Function "eight" has 8 mandatory parameters, which is greater than the 7 authorized.
    pass
