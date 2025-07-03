for i in range(10):
    if i == 42:
        print('Magic number in range')
else:   # Noncompliant. This will be executed every time
    print('Magic number not found')


for i in range(10):
    if i == 42:
        print('Magic number in range')
    else:
        raise ValueError("Foo")
else:   # Noncompliant.
    print('Magic number not found')


for i in range(10):
    if i == 42:
        print('Magic number in range')
        return i
else:   # Noncompliant.
    print('Magic number not found')


for i in range(10):
    if i == 42:
        print('Magic number in range')
print('Magic number not found')