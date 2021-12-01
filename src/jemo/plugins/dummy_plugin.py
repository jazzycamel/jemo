from .base import PluginBase


class DummyPlugin(PluginBase):
    def __init__(self, name: str, port: int):
        super().__init__(name=name, port=port)

    def get_state(self) -> str:
        return super().get_state()

    def on(self) -> bool:
        return True

    def off(self) -> bool:
        return True
