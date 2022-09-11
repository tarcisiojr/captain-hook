import asyncio
import logging
from functools import partial, wraps


logger = logging.getLogger(__name__)


def _run_serial(*coroutines):
    async def fn():
        for coroutine in coroutines:
            await coroutine

    return fn()


def run_in_new_loop(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        p_func = partial(f, *args, **kwargs)
        loop = asyncio.new_event_loop()
        try:
            ret = loop.run_until_complete(_run_serial(p_func()))
            return ret
        finally:
            loop.close()

    return wrap


async def run_in_executor(fnc, *args, **kwargs):
    loop = asyncio.get_event_loop()
    new_func = partial(fnc, *args, **kwargs)
    await loop.run_in_executor(None, new_func)
