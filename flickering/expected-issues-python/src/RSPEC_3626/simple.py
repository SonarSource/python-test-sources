def redundant_jump(x):
    if x == 1:
        print(True)
        return  # NonCompliant


def redundant_jump1(p1, p2):
    while p1:
        if p2:
            continue  # NonCompliant
        else:
            print("foo")


def redundant_jump2(b):
    for x in range(0, 3):
        continue  # NonCompliant
    if b:
        print("b")
        return  # NonCompliant


def compliant1(b):
    for x in range(0, 3):
        break  # OK
    if b:
        print("b")
        return
    print("End")
