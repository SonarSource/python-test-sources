def working(x):
  return
  print('dead code!') # Noncompliant


def f0(x):
  if x:
    print(True)
    return
  else:
    print(False)
    return
  print('dead code!') # Noncompliant


def f1(x):
  if x:
    print(True)
    yield
  else:
    print(False)
    yield
  print('Not dead code!') # OK


def f2_while(x):
  while True:
    if x:
      print(True)
      break
    else:
      print(False)
      break
    print('dead code!') # Noncompliant
  else:
    print('dead code!') # Noncompliant
  print("end of loop")


def f3_while(x):
  while True:
    if x:
      print(True)
      continue
    else:
      print(False)
      continue
    print('dead code!') # Noncompliant
  print("end of loop")


def f2_for():
  for value in range(1, 10):
    if value > 2:
      print(True)
      break
    else:
      print(False)
      break
    print('dead code!') # Noncompliant
  else:
    print('dead code!') # Noncompliant
  print("end of loop")


def f3_for():
  for value in range(1, 10):
    if value > 2:
      print(True)
      continue
    else:
      print(False)
      continue
    print('dead code!') # Noncompliant
  print("end of loop")


def f4():
  if x:
    print(True)
    raise TypeError("message")
  else:
    print(False)
    raise TypeError("message")
  print('dead code!') # Noncompliant


def try_except():
    try:
        return
    except:
        return
    print('message') # Noncompliant