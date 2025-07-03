def myfunc():
    pass

def myfunc_commented():
    pass  # This method is empty on purpose


class MyClass:
    def mymethod():
        pass

    def mymethod_commented():
        pass  # This method is empty on purpose

    def mymethod2():
        def mynested_method():
            pass

    def mymethod2_commented():
        def mynested_method():
            pass  # This method is empty on purpose

class MyEmptyClass:
    pass

var = 42
if var == 1:
    pass
elif var == 2:
    pass  # a comment
else:
    pass


for i in range(10):
    pass

for i in range(10):
    pass  # a comment

mylambda = lambda x: x + 3

mylambda = lambda x: None

