def test1():
    def func(a,b,c):
        pass

    func(1,2,3,c=4) # True Positive  (PyCharm True Positive but bad message)

    params1 = {'c':5}
    func(1,2,3,**params1) # True Positive  (PyCharm True Positive but bad message)

    params2 = {}
    if not params2:
        params2 = {'c':5}
    func(1,2,3,**params2) # False Negative