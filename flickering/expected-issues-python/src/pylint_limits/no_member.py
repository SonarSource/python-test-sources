def get_a(a):
    return a.foo  # No attribute 'test' on None [attribute-error]

get_a(None)

def set_a(a):
    a.foo = 5 # No issue

set_a(None)

def all_in_func():
    a = None
    a.foo  # No issue
    a + 5  # unsupported operand type(s) for +: 'None' and 'int' [unsupported-operands]

def foobar(param):
    if param:
        val = "test"
    else:
        val = 1
    
    if param:
        return val + 5

    if not param:
        return val + 5

foobar(False)

def bar(blarg):
    if blarg is None:
        blarg.some_property = ''
        return blarg + 3
    if isinstance(blarg, str):
        blarg.some_property = ''
        return blarg + 3

bar(None)


class A(object):
  def make_foo(self):
    self.foo = 42
  def consume_foo(self):
    return self.foo  # attribute-error

def f():
    return None
def g():
    return f().test