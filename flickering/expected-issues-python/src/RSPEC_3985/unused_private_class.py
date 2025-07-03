class Noncompliant:
    class __MyClas1s():  # Noncompliant
        pass

    class _MyClass2():  # Noncompliant
        pass

class Compliant:
    class __MyClass1():
        pass

    class _MyClass2():
        pass

    def process(self):
        return Compliant.__MyClass1()

    def process(self):
        return Compliant._MyClass2()