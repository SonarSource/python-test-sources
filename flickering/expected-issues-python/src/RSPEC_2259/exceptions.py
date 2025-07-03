myvar = None
try:
    myvar = open("test.txt", "r")
except Exception as e:
    myvar.close()  # FN, we wouldn't be able to detect this with belief-style analysis; myvar could be null if an exception was thrown in the "try except" block
