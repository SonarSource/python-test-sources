print 1, 2  # Ok
print (1,), 2  # False positive on "2". SonarLint parser thinks that the print statement is a python 3 call because of the parentesises.