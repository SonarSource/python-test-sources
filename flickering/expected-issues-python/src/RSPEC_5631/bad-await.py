import asyncio

# See also https://docs.python.org/3/library/asyncio-task.html#awaitables

###############
# builtin types
###############
async def my_await():
    iterable = ['a', 'b', 'c']
    mydict = {"a": 1, "b": 2}

    await iterable  # Noncompliant
    await iter(iterable)  # Noncompliant
    await set(iterable)  # Noncompliant
    await frozenset(iterable)  # Noncompliant
    await iterable  # Noncompliant
    await "abc"  # Noncompliant
    await f"abc"  # Noncompliant
    await u"abc"  # Noncompliant
    await b"abc"  # Noncompliant
    await bytes(b"abc")  # Noncompliant
    await bytearray(b"abc")  # Noncompliant
    await memoryview(b"abc")  # Noncompliant
    await mydict.keys()  # Noncompliant
    await mydict.values()  # Noncompliant
    await mydict.items()  # Noncompliant
    await range(10)  # Noncompliant

    # Numeric types
    from fractions import Fraction
    from decimal import Decimal
    await 1  # Noncompliant
    await 1.0  # Noncompliant
    await complex(1,1)  # Noncompliant
    await Fraction(1,1)  # Noncompliant
    await Decimal(1)  # Noncompliant
    await True  # Noncompliant
    await None  # Noncompliant
    await NotImplemented  # Noncompliant

    def function():
        pass

    await function  # Noncompliant

    # comprehensions
    await [a for a in iterable]  # Noncompliant
    await {a for a in iterable}  # Noncompliant
    await {a: a for a in iterable}  # Noncompliant

    ################
    # async function
    ################
    def non_async_function():
        print("myfunction")

    async def async_function():
        print("myfunction")

    async def otherfunction():
        await non_async_function()  # Noncompliant. non_async_function is not marked as "async"
        await myfunction()

    ##############
    # Async method
    ##############
    class AsyncClass:
        async def async_method(self):
            return 42

        def non_asyn_method(self):
            return 42

    async def call_async_class():
        res = await AsyncClass().non_asyn_method()  # Noncompliant
        res = await AsyncClass().async_method()  # Noncompliant
        print(res)

    #################
    # Async generator
    #################
    async def async_generator():
        yield 1

    async def call_async_generator():
        await async_generator()  # Noncompliant

    # Async iterable
    class AsyncIterable:
        def __aiter__(self):
            return AsyncIterator()

    class AsyncIterator:
        def __init__(self):
            self.start = True

        async def __anext__(self):
            if self.start:
                self.start = False
                return 42
            raise StopAsyncIteration

    await AsyncIterable()  # Noncompliant

    ############################
    # Generator based coroutines (deprecated but still valid)
    ############################

    # https://docs.python.org/3/library/asyncio-task.html#generator-based-coroutines
    import asyncio

    @asyncio.coroutine
    def old_style_coroutine():
        yield from asyncio.sleep(1)

    async def call_old_style_coroutine():
        await old_style_coroutine()
        await old_style_coroutine  # Noncompliant

    ############
    # Async task
    ############
    async def mytask():
        task = asyncio.create_task(async_function())
        await task

    ########
    # Future
    ########
    def myfunction():
        return "myfunction"

    async def call_myfunction():
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, myfunction)

# asyncio.run(my_await())