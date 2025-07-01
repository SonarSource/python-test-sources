class Noncompliant:
    _class_attr = 0  # Noncompliant if enable_single_underscore_issues is enabled
    __mangled_class_attr = 1  # Noncompliant
    
    def __init__(self, value):
        self._attr = 0  # Noncompliant if enable_single_underscore_issues is enabled
        self.__mangled_attr = 1  # Noncompliant

    def compute(self, x):
        return x * x

class Compliant:
    _class_attr = 0
    __mangled_class_attr = 1
    __indirect_access = 42
    
    def __init__(self, value):
        self._attr = 0
        self.__mangled_attr = 1

    def compute(self, x):
        return x * Compliant._class_attr * Compliant.__mangled_class_attr * self._attr * self.__mangled_attr
    
    def access(self):
        print(type(self).__indirect_access)
