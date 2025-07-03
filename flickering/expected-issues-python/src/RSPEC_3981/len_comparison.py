mylist = []
if len(myList) >= 0:  # Noncompliant
    pass

if len(myList) < 0:  # Noncompliant
    pass

mylist = []
if len(myList) >= 42:
    pass

if len(myList) == 0:
    pass

if len(myList) <= 0:  # confusing but not a bug
    pass