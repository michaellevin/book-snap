from typing import Callable, Any


class Signal(object):
    def __init__(self, id: int):
        self.id = id
        self.callables = []

    def connect(self, callable: Callable):
        if callable not in self.callables:
            self.callables.append(callable)

    def disconnect(self, callable: Callable):
        if callable in self.callables:
            self.callables.remove(callable)

    def emit(self, data: Any):
        for callable in self.callables:
            callable(data)
