a = 0
b = 1

def doOneMoreThing():
    pass

if b == 0:  # Noncompliant
    doOneMoreThing()
elif b == 1:
    doOneMoreThing()
else:
    doOneMoreThing()

b = 4 if a > 12 else 4  # Noncompliant

if b == 0:  # no issue, this could have been done on purpose to make the code more readable
    doOneMoreThing()
elif b == 1:
    doOneMoreThing()
