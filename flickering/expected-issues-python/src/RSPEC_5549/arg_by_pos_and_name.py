# Example of real issues;
# https://github.com/canonical/cloud-init/commit/64a3df16d9c63db470a3ba55d9c5cc8e05d050d7#diff-37e9420fd809b0fd8d863f3b6eef1f4aL78-R78
# https://github.com/compiz-reloaded/ccsm/commit/eb2169446efa884ed63e0dea9ab60d896d359a62#diff-a9c1e6a6128f45b5d9b86ac700f58c0dL956-R956
#
# Example of projects using dict literal unpacking
# https://sourcegraph.com/search?q=%22%28%22+%22**%7B%22+%7D%5C%29%24+lang:%22python%22+count:%225000%22&patternType=regexp#50
#

def func(a, b=2, c=3):
    return a * b * c

func(6, 93, b=62)  # Noncompliant: argument "b" is duplicated
func(6, 93, 21, c=62)  # Noncompliant: argument "c" is duplicated

params1 = {'c': 31}
func(6, 93, 31, **params1)  # Noncompliant: argument "c" is duplicated

params2 = {'c': 31}
func(6, 93, c=62, **params2)  # Noncompliant: argument "c" is duplicated
func(6, 93, c=62, **{'c': 31})  # Noncompliant: argument "c" is duplicated (yes devs unpack literal dicts)

params_dict = dict(c=31)
func(6, 93, c=62, **params_dict)  # Noncompliant: argument "c" is duplicated
func(6, 93, c=62, **dict(c=31))  # Noncompliant: argument "c" is duplicated


def func2(condition):
    if condition:
        multiple_assignments = {'e': 31}
    else:
        multiple_assignments = {'c': 31}
    func(6, 93, 31, **multiple_assignments)  # Out of scope. We only support single assignments to variable.

    
params_modified = {'c': 31}
def modify_params(params):
    del params['c']
modify_params(params_modified) # reference to params_modified 
# As params_modified is referenced in another context than the call and the assignment we want to avoid False Positives.
func(6, 93, 31, **params_modified)  # No issue. 


params_complex = {'c': 3}
del params_complex['c']
func(6, 93, 31, **params_complex)  # Out of scope to avoid False Positives


# Out of Scope
# func(c=31, b=93, c=62)  # Out of scope because the interpreter will fail with a SyntaxError before even running the script

# Out of scope, varargs
pos = [1, 2, 3]
func(*pos, a=2)  # Out of scope because in most case we won't know how big is the list


# Current implementation of S930 overlaps in the following cases.
# S5549 has a more precise message and S930 message is confusing in this case.
# Thus S930 should ignore parameters provided at the same time by value and by name.

def keyword_only(a, *, b):
    return a * b

keyword_only(1, b=2, a=2)  # Noncompliant for S5549. False Positive for S930.


def positional_only(a, /, b):
    return a * b

positional_only(1, 2, b=2)  # Noncompliant for S5549. "b" is duplicated. False Positive for S930.
positional_only(1, 2, a=2)  # Ok for S5549. Noncompliant for S930. "a" cannot be passed via keyword arguments.
positional_only(1, a=2)  # Ok for S5549. Noncompliant for S930. "a" cannot be passed via keyword arguments + missing argument "b"


#
# As PEP-457 says: "many CPython “builtin” functions still only accept positional-only arguments."
# [...] "there are many builtin functions whose signatures are simply not expressable with Python syntax."
# https://www.python.org/dev/peps/pep-0457/
#
# Typeshed is not using the positional only syntax, probably to not break backward compatibility.
# Because of that Typeshed has a convention for naming positional only arguments. It adds two underscores
# in front of positional only arguments' names. Example:
# https://github.com/python/typeshed/pull/3648/files
#
# We can rely on this naming hack to avoid False Positives on most parameters. However the "self" and "cls" arguments
# have not been renamed with two underscores even though they can be passed only as positional arguments for builtin
# functions and methods. This can create some False Positives on calls such as...

"{self}".format(self=self)  # Ok. Avoid this potential False Positive.

# ... This works because the format method's "self" argument cannot be passed as a keyword argument. Yet if we follow
# what typeshed says there should be a bug as it doesn't mark "self" as positional only.
# https://github.com/python/typeshed/blob/637dba1beba84cc51800a9ffb4054d0b760da115/stdlib/2and3/builtins.pyi#L434
#
# Thus we will not raise when the duplicated argument is the self or cls argument of a method. It is out of scope.

class MyClass:
    def method1(self, a):
        pass

    def method2(self, a):
        self.method1(self, a)  # No issue from S5549. This is correctly covered by S930
        self.method1(self, a=a) # Noncompliant for S5549: argument "a" is duplicated. False Positive for S930.

        self.method1(a, self=self) # False positive for S930. Out of scope for S5549.
        self.method1(a, **{"self": self}) # Out of scope
