
'''file contains issues for S2712 as they were not found in existring files'''


def fun1(n):
    'doc'
    num = 0
    while num < n:
        yield num
        num += 1
    return num

def fun2(n):
    'doc'
    num = 0
    while num < n:
        yield num
        num += 1
    return


def fun3(n):
    'doc'
    num = 0
    while num < n:
        yield num
        num += 1

def fun5(n):
    'doc'
    num = 0
    if n == 0:
        return
    while num < n:
        yield num
        num += 1
    return num

def fun4(n):
    'doc'
    num = 0
    while num < n:
        num += 1
    return num
