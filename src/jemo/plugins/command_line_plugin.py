import shlex
import subprocess

from .base import PluginBase

# Examples:
# CommandLinePlugin(
#   "Output to file",
#   8123,
#   "touch testfile.txt",
#   "rm testfile.txt",
#   state_cmd = "ls testfile.txt"
# )
#
# CommandLinePlugin(
#   "Output to file",
#   8123,
#   "touch testfile.txt",
#   "rm testfile.txt",
#   use_fake_state = True
# )


class CommandLinePlugin(PluginBase):
    def __init__(
        self,
        name: str,
        port: int,
        on_cmd: str,
        off_cmd: str,
        state_cmd: str = None,
        use_fake_state: bool = False,
    ):  #
        super().__init__(name=name, port=port)

        self._on_cmd = on_cmd
        self._off_cmd = off_cmd
        self._state_cmd = state_cmd
        self._use_fake_state = use_fake_state

    @staticmethod
    def run_cmd(cmd: str) -> bool:
        shlexed_cmd = shlex.split(cmd)
        process = subprocess.run(shlexed_cmd)
        return process.returncode == 0

    def on(self) -> bool:
        return self.run_cmd(self._on_cmd)

    def off(self) -> bool:
        return self.run_cmd(self._off_cmd)

    def get_state(self) -> str:
        if self._use_fake_state:
            return super().get_state()

        if self._state_cmd is None:
            return "unknown"

        returned_zero = self.run_cmd(self._state_cmd)
        if returned_zero:
            return "on"
        return "off"
