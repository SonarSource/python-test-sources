class MyClass:
    code = "bounteous"

    def calculate_code(self):
        self.do_the_thing()
        return self.__class__.code

    def get_name(self):  # Noncompliant
        self.do_the_thing()
        return self.__class__.code
    
    def do_the_thing(self):
        pass  # on purpose

class MyClass2:
    code = "bounteous"

    def calculate_code(self):
        self.do_the_thing()
        return self.__class__.code

    def get_name(self):
        return self.calculate_code()
    
    def do_the_thing(self):
        pass  # on purpose

MyClass().get_name()
MyClass2().get_name()
