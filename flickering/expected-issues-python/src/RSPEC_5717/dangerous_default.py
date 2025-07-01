def myfunction_list1(param=list()):  # Noncompliant.
    param.append('a')  # Secondary location

def myfunction_list2(param=[]):  # Noncompliant.
    param.append('a')  # Secondary location

def myfunction_set1(param=set()):  # Noncompliant.
    param.add('a')  # Secondary location

def myfunction_set2(param={1, 2, 3}):  # Noncompliant.
    param.add('a')  # Secondary location

def myfunction_dict1(param=dict()):  # Noncompliant.
    param['a'] = 1  # Secondary location

def myfunction_dict2(param={}):  # Noncompliant.
    param['a'] = 1  # Secondary location


def myfunction_list1(param=list()):
    param[0]

def myfunction_list2(param=[]):
    param[0]

def myfunction_set1(param=set()):
    [a for a in param]

def myfunction_set2(param={1, 2, 3}):
    [a for a in param]

def myfunction_dict1(param=dict()):
    param['a']

def myfunction_dict2(param={}):
    param['a']


#
# collections
#
import collections


def myfunction_deque(param=collections.deque()):  # Noncompliant.
    param.append('a')  # Secondary location

def myfunction_counter(param=collections.Counter()):  # Noncompliant.
    param['a'] = 1  # Secondary location

def myfunction_chainmap(param=collections.ChainMap()):  # Noncompliant.
    param['a'] = 1  # Secondary location

def myfunction_ordereddict(param=collections.OrderedDict()):  # Noncompliant.
    param['a'] = 1  # Secondary location

def myfunction_defaultdict(param=collections.defaultdict(set)):  # Noncompliant. False Negative. Even if there is no modification made, because even accessing the default dict modifies it.
    pass

def myfunction_userdict(param=collections.UserDict()):  # Noncompliant.
    param['a'] = 1  # Secondary location

def myfunction_userlist(param=collections.UserList()):  # Noncompliant.
    param.append('a')  # Secondary location



def myfunction_deque(param=collections.deque()):
    param[0]

def myfunction_counter(param=collections.Counter()):
    param['a']

def myfunction_chainmap(param=collections.ChainMap()):
    param['a']

def myfunction_ordereddict(param=collections.OrderedDict()):
    param['a']

def myfunction_userdict(param=collections.UserDict()):
    param['a']

def myfunction_userlist(param=collections.UserList()):
    param[0]


#
# Default value set to an attribute
#

class A:
    def __init__(self, param=list()):  # Noncompliant.
        self.param = param  # Secondary location
    def process(self, value):
        self.param.append(value)


def set_value(a_dict, key, values={}):  # Bad but out of scope
    a_dict[key] = values  # Multiple maps will share the same "values" dict

d1, d2 = ({}, {})
set_value(d1, "test")
set_value(d2, "test")
d1["test"][0] = 1
print(d2)  # {'test': {0: 1}}


class M:
    pass

def set_attribute(param=M()):  # Noncompliant
    param.var = 6  # Secondary location


def replace_value_before(param=[]):  # No issue because param is set before being used
    param = [param]
    param.var = 2  # Secondary location


def replace_value_after(param=[]):  # Noncompliant
    param.var = 1
    param = [param]