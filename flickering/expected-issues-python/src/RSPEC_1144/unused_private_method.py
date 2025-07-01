class Noncompliant:

    @classmethod
    def __mangled_class_method(cls):  # Noncompliant
        print("__mangled_class_method")

    @staticmethod
    def __mangled_static_method():  # Noncompliant
        print("__mangled_static_method")

    def __mangled_instance_method(self):  # Noncompliant
        print("__mangled_instance_method")

class Compliant:

    def __init__(self):
        Compliant.__mangled_class_method()
        Compliant.__mangled_static_method()
        self.__mangled_instance_method()

    @classmethod
    def __mangled_class_method(cls):
        print("__mangled_class_method")

    @staticmethod
    def __mangled_static_method():
        print("__mangled_static_method")

    def __mangled_instance_method(self):
        print("__mangled_instance_method")


    @classmethod
    def _class_method(cls):
        print("_class_method")

    @staticmethod
    def _static_method():
        print("_static_method")

    def _instance_method(self):
        print("_instance_method")
