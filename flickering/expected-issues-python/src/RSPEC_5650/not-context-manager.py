############
# contextlib  https://docs.python.org/3/library/contextlib.html#module-contextlib
############
from contextlib import contextmanager, asynccontextmanager, ExitStack, AsyncExitStack

@contextmanager
def simple_contextmanager():
    print("enter")
    yield
    print("exit")

with simple_contextmanager() as e:
    print(e)
with simple_contextmanager as e:  # Noncompliant
    print(e)

def function():
    return 42

with function() as e:  # Noncompliant
    print(e)

def generator():
    yield 42

with generator() as e:  # Noncompliant
    print(e)

with ExitStack() as stack:
    pass

var = simple_contextmanager
with simple_contextmanager():
    pass


#######
# Class
#######
class SimpleContextManager:
    def __enter__(self):
        print("enter")
    def __exit__(self, type_, value, traceback):
        print("exit")

with SimpleContextManager():
    pass
with SimpleContextManager:  # Noncompliant
    pass

class SubContextManager(SimpleContextManager):
    pass

with SubContextManager():
    pass


class Empty:
    pass

with Empty():  # Noncompliant
    pass

class AbstractClass:
    def process(self):
        with self:  # no issue as __enter__ and __exit__ might be implemented in subclasses
            pass

###########################
# Multiple context managers
###########################
with simple_contextmanager() as first, Empty() as second:  # Noncompliant
    print("here")

with simple_contextmanager() as first, SimpleContextManager() as second:
    print("here")


########################
# async context managers https://docs.python.org/3/library/contextlib.html#contextlib.asynccontextmanager
########################

import asyncio

@asynccontextmanager
async def async_context_manager():
    yield 42

async def call_async_context_manager():
    async with async_context_manager() as context:
        print(context)

with async_context_manager() as context:  # Noncompliant Missing "async"
    print(context)

async def call_AsyncExitStack():
    async with AsyncExitStack() as stack:
        pass

class AsyncContextManager:
    async def __aenter__(self):
        await asyncio.sleep(1)

    async def __aexit__(self, exc_type, exc, tb):
            await asyncio.sleep(1)

async def call_AsyncContextManager():
    async with AsyncContextManager():
        pass

# asyncio.run(call_AsyncContextManager())

with AsyncContextManager():  # Noncompliant. Missing "async"
    pass

