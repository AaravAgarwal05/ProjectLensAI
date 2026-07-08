"""Thread-safe Singleton metaclass."""

import threading
from typing import Any


class Singleton(type):
    """Metaclass that ensures a class has only one instance.

    Thread-safe via a per-class lock.

    Usage::

        class MyClass(metaclass=Singleton):
            ...
    """

    _instances: dict[type, object] = {}
    _locks: dict[type, threading.Lock] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> object:
        if cls not in cls._instances:
            lock = cls._locks.setdefault(cls, threading.Lock())
            with lock:
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]
