#!python

def myfunc():
    return
    raise Exception('a') # True Positive

def try_except():
    try:
        return
    except:
        return
    raise Exception('a') # False Negative