import unittest

#
# RSPEC_5797: Constants should not be used as conditions
#

class ConstantTrueFalseTests(unittest.TestCase):
    """Rule S5914 should raise issues on cases where S5797 raises."""

    def test_constant_assert_true_with_literal(self):
        """assertTrue and assertFalse called on literals will always succeed or always fail."""
        self.assertTrue(True)  # Noncompliant
        self.assertTrue(False)  # Noncompliant
        self.assertTrue(42)  # Noncompliant
        self.assertTrue('a string')  # Noncompliant
        self.assertTrue(b'bytes')  # Noncompliant
        self.assertTrue(42.0)  # Noncompliant
        self.assertTrue({})  # Noncompliant
        self.assertTrue({"a": 1, "b": 2})  # Noncompliant
        self.assertTrue({41, 42, 43})  # Noncompliant
        self.assertTrue([])  # Noncompliant
        self.assertTrue([41, 42, 43])  # Noncompliant
        self.assertTrue((41, 42, 43))  # Noncompliant
        self.assertTrue(())  # Noncompliant
        self.assertTrue(None)  # Noncompliant

        # Same for assertFalse
        self.assertFalse(True)  # Noncompliant
        # ...
    
    def test_assert_statement(self):
        """The assert statement should be analyzed the same way as unittest.assertTrue with one exception.
        
        When the assert statement is used directly on a two elements literal tuple the issue should be raised
        only by RSPEC-5905 "Assert should not be called on a tuple literal". This is a very common mistake
        and having a dedicated rule will make it easier for developer to understand the issue.
        """
        assert True # Noncompliant

        assert (1, "message")  # Ok. Issue raised by RSPEC-5905

    
    def test_constant_assert_true_with_unpacking(self):
        """Rule handles unpacking as S5797."""
        li = [1,2,3]
        di = {1:1}
        self.assertTrue([*li])  # False Negative. We don't check the size of unpacked iterables
        self.assertTrue([1, *li])  # Noncompliant. Always succeeds.

        self.assertTrue((*li))  # False Negative. We don't check the size of unpacked iterables
        self.assertTrue((1, *li))  # Noncompliant. Always succeeds.

        self.assertTrue({*li})  # False Negative. We don't check the size of unpacked iterables
        self.assertTrue({1, *li})  # Noncompliant. Always succeeds.

        self.assertTrue({**di})  # False Negative. We don't check the size of unpacked iterables
        self.assertTrue({2:3, **di})  # Noncompliant. Always succeeds.


    def test_constant_assert_true_with_module_and_functions(self):
        self.assertTrue(round)  # Noncompliant. Always succeeds.
        self.assertTrue(unittest)  # Noncompliant. Always succeeds.
    

    def test_constant_assert_true_with_class_and_methods_and_properties(self):
        class MyClass:
            def mymethod(self):
                if self.mymethod:  # Noncompliant
                    pass

            @property
            def myprop(self):
                pass
        
        myinstance = MyClass()
        self.assertTrue(MyClass)  # Noncompliant
        self.assertTrue(MyClass.mymethod)   # Noncompliant
        self.assertTrue(myinstance.mymethod)   # Noncompliant
        self.assertTrue(myinstance.myprop)   # Ok
        self.assertTrue(myinstance)   # Ok
    
    def test_constant_assert_true_with_generators_and_lambdas(self):
        lamb = lambda: None
        self.assertTrue(lamb)  # Noncompliant

        gen_exp = (i for i in range(42))
        self.assertTrue(gen_exp)  # Noncompliant

        def generator_function():
            yield
        generator = generator_function()
        self.assertTrue(generator)  # False Negative. Not covered by S5797 for now.
    
    def test_constant_assert_true_with_variables_pointing_to_single_immutable_type_value(self):
        """For immutable types we consider that if a variable can only have one value and it is used as a condition, we should raise an issue.
        See S5797 for more info."""
        if 42:
            an_int = 1
        else:
            an_int = 2

        an_int = 0  # Overwrite all previus values
        self.assertTrue(an_int)  # Noncompliant. an_int can only be 0



#
# RSPEC_5727: Comparison to None should not be constant
#

def a_function() -> int:
    return None

class ConstantNoneTests(unittest.TestCase):
    """Rule S5914 should raise issues on cases where S5727 raises."""
    def test_constant_assert_none(self):
        myNone = None
        self.assertIsNone(round)  # Noncompliant. Always fails
        self.assertIsNotNone(round)  # Noncompliant. Always succeeds
        self.assertIsNone(myNone)  # Noncompliant. Always succeeds
        self.assertIsNotNone(myNone)  # Noncompliant. Always fails

    def test_ignore_annotations(self):
        """This rule should ignore type annotations when they are not comming from Typeshed. It
        is ok to test if a function behaves as expected."""
        self.assertIsNotNone(a_function())  # Ok. Avoid False Positive here.


#
# RSPEC_5796: New objects should not be created only to check their identity
#

class ConstantNewObjectTests(unittest.TestCase):
    """Rule S5914 should raise issues on cases where S5796 raises."""
    def helper_constant_assert_new_objects(self, param):
        self.assertIs(param, [1, 2, 3])  # Noncompliant. Always fails
        self.assertIsNot(param, [1, 2, 3])  # Noncompliant. Always succeeds