
'''file contains issues for S2733 as they were not found in existring files'''

class MyClass1(object):
    'doc'
    def __enter__(self):
        'doc'
        pass
    def __exit__(self, exc_type, exc_val):
        'doc'
        pass

class MyClass2(object):
    'doc'
    def __enter__(self):
        'doc'
        pass
    def __exit__(self, exc_type, exc_val, exc_trace, exc_one_more):
        'doc'
        pass

class MyClass3(object):
    'doc'
    def __enter__(self):
        'doc'
        pass
    def __exit__(self):
        'doc'
        pass

class MyClass4(object):
    'doc'
    def __enter__(self):
        'doc'
        pass
    def __exit__(self, exc_type, exc_val, exc_tb):
        'doc'
        pass
