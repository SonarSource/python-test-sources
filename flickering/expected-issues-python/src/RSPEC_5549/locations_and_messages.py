def func(a, b=2, c=3):
#^^^^^^^^^^^^^^^^^^^^^ Secondary location
# message: Function definition
    return a * b * c

func(6, 93, b=62)  # Noncompliant: argument "c" is duplicated in "func" call
#       ^^  ^^^^  Primary location on "93", secondary location on "b=62"
# Primary message: "b" argument is passed twice in "func" call
# Secondary message: argument also passed here

params = {'c': 31}
func(6, 93, 31, **params)  # Noncompliant: argument "c" is duplicated in "func" call
#           ^^  ^^^^^^^^  Primary location on "31", secondary location on "**params"
# Primary message: "c" argument is passed twice in "func" call
# Secondary message: argument also passed here


func(6, 93, 31, **{'c': 21, 'd': 21})  # Noncompliant: argument "c" is duplicated in "func" call
#           ^^     ^^^^^^^                   Primary location on "31", secondary location on "'c': 21"
# Primary message: "c" argument is passed twice in "func" call
# Secondary message: argument also passed here


func(6, 93, 31, **dict(c=21, d=21))  # Noncompliant: argument "c" is duplicated in "func" call
#           ^^         ^^^^                   Primary location on "31", secondary location on "c=21"
# Primary message: "c" argument is passed twice in "func" call
# Secondary message: argument also passed here