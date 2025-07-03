# https://github.com/PyCQA/pylint/issues/392

class Users:
    __slots__ = ['name']
    def __init__(self, name="Unknown"):
        self.name = name

def get_user():
    return Users('name')

def get_users_list1():
    result = [Users('first user')]
    for name in ['a', 'b', 'c']:
        result.append(Users(name))
    return result

def get_users_list2():
    result = [] # start with empty list
    for name in ['a', 'b', 'c']:
        result.append(Users(name))
    return result


def get_users_generator():
    for name in ['a', 'b', 'c']:
        yield Users(name)


user1 = get_user()
user1.unknown_field = 'value'  # True Positive

for user2 in get_users_list1():
    user2.unknown_field = 'value'  # True Positive

for user2 in get_users_list2():
    user2.unknown_field = 'value'  # False Negative
# => Type inference doesn't work with empty lists + concatenation

for user2 in get_users_generator():
    user2.unknown_field = 'value'  # False Negative
# => Type inference doesn't work with generators
