def locations_and_messages(param):
    param is {1: 2, 3: 4}  # Noncompliant
#         ^^
# Primary location on "is". Message: "Replace this "is" operator with "=="."

# ====================================================

    {1: 2, 3: 4} is not complex(1, 2)  # Noncompliant
#                ^^^^^^
# Primary location on "is not". Message: "Replace this "is not" operator with "!="."

# ====================================================

    mylist = []
#            ^^
# Secondary location on "mylist". Message: This expression creates a new object every time.

    param is mylist  # Noncompliant
#         ^^
# Primary location on "is". Message: "Replace this "is" operator with "=="."
