import urllib.parse
from typing import Mapping, Optional, Union

from PyQt6.QtCore import QUrl
from PyQt6.QtNetwork import (
    QAuthenticator,
    QNetworkAccessManager,
    QNetworkReply,
    QNetworkRequest,
)
from PyQt6.QtWidgets import QApplication

from .. import logger
from .base import PluginBase

CommandData = Union[Mapping, str]
OptionalCommandData = Optional[CommandData]


class HTTPPlugin(PluginBase):  # pylint:disable=too-many-instance-attributes
    def __init__(
        self,
        *,
        headers: Optional[dict] = None,
        method: str = "GET",
        name: str,
        off_cmd: str,
        off_data: OptionalCommandData = None,
        on_cmd: str,
        on_data: OptionalCommandData = None,
        state_cmd: Optional[str] = None,
        state_data: OptionalCommandData = None,
        state_method: str = "GET",
        state_response_off: Optional[str] = None,
        state_response_on: Optional[str] = None,
        password: Optional[str] = None,
        port: int,
        use_fake_state: bool = False,
        user: Optional[str] = None,
    ):
        super().__init__(name=name, port=port)

        self._method = method
        self._state_method = state_method
        self._headers = headers

        self._on_cmd = on_cmd
        self._on_data = self._to_bytes(on_data) if on_data else None

        self._off_cmd = off_cmd
        self._off_data = self._to_bytes(off_data) if off_data else None

        self._state_cmd = state_cmd
        self._state_data = self._to_bytes(state_data) if state_data else None
        self._state_response_on = state_response_on
        self._state_response_off = state_response_off

        self._use_fake_state = use_fake_state

        self._user = user
        self._password = password

        self._nam = QNetworkAccessManager(
            authenticationRequired=self.authentication_required
        )  # type:ignore

    @staticmethod
    def _to_bytes(data: CommandData) -> bytes:
        if isinstance(data, Mapping):
            data = urllib.parse.urlencode(data)
        if isinstance(data, str):
            return data.encode("utf8")
        return data

    def set_state(self, cmd: str, data: Optional[bytes]) -> bool:
        request = QNetworkRequest(QUrl(cmd))
        reply: QNetworkReply
        if self._method == "POST":
            reply = self._nam.post(request, data)  # type: ignore
        elif self._method == "GET":
            reply = self._nam.get(request)
        else:
            raise Exception(f"Method '{self._method}' not supported!")

        while not reply.isFinished():
            QApplication.processEvents()
            continue

        if reply.error() != QNetworkReply.NetworkError.NoError:
            logger.error(f"HTTPPlugin set_state cmd failed: {reply.errorString()}")
            return False

        status_code = int(
            reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        )
        logger.debug(f"Status code '{status_code}' for '{cmd}'")
        return status_code in (200, 201)

    def get_state(self) -> str:
        if self._use_fake_state:
            return super().get_state()

        if not (self._state_method and self._state_cmd):
            return "unknown"

        logger.debug(
            f"HTTPPlugin get_state cmd: {self._state_method} {self._state_cmd}"
        )
        request = QNetworkRequest(QUrl(self._state_cmd))
        reply: QNetworkReply
        if self._state_method == "POST":
            reply = self._nam.post(request, self._state_data)  # type:ignore
        elif self._state_method == "GET":
            reply = self._nam.get(request)
        else:
            raise Exception(f"Method '{self._method}' not supported!")

        logger.debug("Wait for reply to finish...")
        while not reply.isFinished():
            QApplication.processEvents()
            continue
        logger.debug("...finished!")

        if reply.error() != QNetworkReply.NetworkError.NoError:
            logger.error(f"HTTPPlugin get_state cmd failed: {reply.errorString()}")
        content = reply.readAll().data().decode("utf8")
        logger.debug(f"HTTPPlugin get state response content: {content}")
        has_response_off = (
            self._state_response_off and self._state_response_off in content
        )
        has_response_on = self._state_response_on and self._state_response_on in content
        if has_response_off == has_response_on:
            return "unknown"
        if has_response_off:
            return "off"
        if has_response_on:
            return "on"
        return "unknown"

    def on(self) -> bool:
        return self.set_state(self._on_cmd, self._on_data)

    def off(self) -> bool:
        return self.set_state(self._off_cmd, self._off_data)

    def authentication_required(self, _, authenticator: QAuthenticator):
        if self._user:
            authenticator.setUser(self._user)
        if self._password:
            authenticator.setPassword(self._password)
