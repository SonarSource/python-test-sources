def mypow(num, exponent):  # Noncompliant
    num = num * mypow(num, exponent - 1)
    return num  # this is never reached


def my_pow(num, exponent):  # Compliant
    if exponent > 1:
      num = num * my_pow(num, exponent - 1)
    return num


def myrec(myparam):  # Noncompliant
    if myparam == 0:
        myrec(myparam)
    else:
        myrec(myparam - 1)
    return myparam  # this is never reached


async def foo():  # Compliant as this is an async function
    return foo()


async def foo():  # Noncompliant - False Negative
    return await foo()


def get_cls_and_bases(cls):  # False Positive
    return {cls}.union({b for base in cls.__bases__ for b in get_cls_and_bases(base)})

get_cls_and_bases(ImportError)
