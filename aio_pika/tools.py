import asyncio
from functools import wraps
from collections import Set
from typing import Iterator, _T_co, Callable, Iterable

__all__ = 'create_task', 'iscoroutinepartial', 'shield', 'CallbackCollection',


def iscoroutinepartial(fn):
    """
    Function returns True if function it's a partial instance of coroutine.
    See additional information here_.

    :param fn: Function
    :return: bool

    .. _here: https://goo.gl/C0S4sQ

    """

    while True:
        parent = fn

        fn = getattr(parent, 'func', None)

        if fn is None:
            break

    return asyncio.iscoroutinefunction(parent)


def create_task(func, *args, loop=None, **kwargs):
    loop = loop or asyncio.get_event_loop()

    if iscoroutinepartial(func):
        return loop.create_task(func(*args, **kwargs))

    def run(future):
        if future.done():
            return

        try:
            future.set_result(func(*args, **kwargs))
        except Exception as e:
            future.set_exception(e)

        return future

    future = loop.create_future()
    loop.call_soon(run, future)
    return future


def shield(func):
    """
    Simple and useful decorator for wrap the coroutine to `asyncio.shield`.
    """

    async def awaiter(future):
        return await future

    @wraps(func)
    def wrap(*args, **kwargs):
        return wraps(func)(awaiter)(asyncio.shield(func(*args, **kwargs)))

    return wrap


class CallbackCollection(Set):
    __slots__ = '__callbacks',

    def __init__(self):
        self.__callbacks = set()

    def add(self, callback: Callable):
        if not callable(callback):
            raise ValueError("Callback is not callable")

        self.__callbacks.add(callback)

    def remove(self, callback: Callable):
        self.__callbacks.remove(callback)

    @property
    def is_frozen(self) -> bool:
        return isinstance(self.__callbacks, frozenset)

    def freeze(self):
        if self.is_frozen:
            raise RuntimeError("Collection already frozen")

        self.__callbacks = frozenset(self.__callbacks)

    def unfreeze(self):
        if not self.is_frozen:
            raise RuntimeError("Not collection is not frozen")

        self.__callbacks = set(self.__callbacks)

    def __contains__(self, x: object) -> bool:
        return x in self.__callbacks

    def __len__(self) -> int:
        return len(self.__callbacks)

    def __iter__(self) -> Iterable[Callable]:
        return iter(self.__callbacks)

    def __copy__(self):
        instance = self.__class__()
        for cb in self.__callbacks:
            instance.add(cb)

        return instance
