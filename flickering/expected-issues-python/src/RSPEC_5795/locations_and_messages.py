def locations_and_messages(param):
    param is 2000  # Noncompliant
#         ^^
# Primary location on "is". Message: "Replace this "is" operator with "=="; identity operator is not reliable here."

    param is not round(param)  # Noncompliant
#         ^^^^^^
# Primary location on "is not". Message: "Replace this "is not" operator with "!="; identity operator is not reliable here."
