myvar = None
myvar.test()  # FN, we wouldn't be able to detect this with belief-style analysis => "'NoneType' object has no attribute 'test'"
