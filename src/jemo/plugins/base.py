from abc import ABC, abstractmethod
from typing import Callable


class PluginBase(ABC):
    def __init__(self, *, name: str, port: int) -> None:
        self._name = name
        self._port = port
        self._latest_action = "off"

    def __getattribute__(self, name: str) -> Callable:
        if name in ("on", "off"):
            success = object.__getattribute__(self, name)()
            if success is True:
                self._latest_action = name
            return lambda: success
        return object.__getattribute__(self, name)

    def __repr__(self) -> str:
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({attrs}"

    @property
    def port(self) -> int:
        return self._port

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    def on(self) -> bool:
        pass

    @abstractmethod
    def off(self) -> bool:
        pass

    @abstractmethod
    def get_state(self) -> str:
        return self._latest_action

    def close(self) -> None:
        pass

    @property
    def latest_action(self) -> str:
        return self._latest_action
