'''file contains issues for S1862 as they were not found in existring files'''
param = 2

if param == 1:
    print(1)
elif param == 2:
    print(2)
elif param == 1:            # Noncompliant
    print(3)

if param == 1:
    print(1)
else:
    if param == 2:
        print(2)
    else:
        if param == 2:            # Noncompliant
            print(3)


if param == 1:
    print(1)
else:
    if param == 2:
        print(2)
    elif param == 1:            # Noncompliant
            print(3)


if param == 1:
    print(1)
else:
    print(2)
    if param == 1:
        print(2)
    elif param == 1:  # Noncompliant
        print(3)
    print(2)

if param == 1:
    if param > 0:
        print(1)
elif param == 2:
    if param > 0:  # Compliant
        print(2)
elif param == 3:
    if param > 0:  # Compliant
        print(2)
    else:
        print(3)
