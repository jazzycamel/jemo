import importlib
import os.path
import signal
import sys
import uuid
from email.utils import formatdate
from functools import partial
from random import random
from typing import List, Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSlot
from PyQt6.QtNetwork import (
    QHostAddress,
    QNetworkDatagram,
    QTcpServer,
    QTcpSocket,
    QUdpSocket,
)
from PyQt6.QtWidgets import QApplication

from . import logger
from .config import load_config_file
from .plugins import PluginBase
from .utils import get_local_ip, make_serial

NEW_LINE = "\r\n"


class JemoDevice(QObject):
    def __init__(self, name: str, plugin: PluginBase, **kwargs) -> None:
        super().__init__(parent=None, **kwargs)  # type:ignore
        self._name = name
        self._serial = make_serial(name)
        self._plugin = plugin
        self._server: Optional[QTcpServer] = None
        self._sockets: List[QTcpSocket] = []

    def start_server(self, ip_address: str, port: int):
        logger.debug(f"Starting TCP server on {ip_address}:{port}")
        self._server = QTcpServer(
            self, newConnection=self.new_connection
        )  # type:ignore
        self._server.listen(QHostAddress(ip_address), port)
        if not self._server.isListening():
            raise Exception(
                f"{self.__class__.__name__} not able to listen on {ip_address}:{port}"
            )

    @pyqtSlot()
    def new_connection(self):
        socket: QTcpSocket = self._server.nextPendingConnection()
        logger.debug(
            f"New TCP connection from {socket.peerAddress().toString()}:{socket.peerPort()}"
        )
        socket.readyRead.connect(self.read_data)
        socket.disconnected.connect(self.remove_socket)
        self._sockets.append(socket)

    @pyqtSlot()
    def read_data(self):
        socket: QTcpSocket = self.sender()
        msg = socket.readAll().data().decode("utf8")
        logger.debug(f"Received message:\n{msg}")

        if msg.startswith("GET /setup.xml HTTP/1.1"):
            logger.info("setup.xml requested by Echo")
            self.handle_setup(socket)
        elif "/eventservice.xml" in msg:
            logger.info("eventservice.xml requested by Echo")
            self.handle_event(socket)
        elif "/metainfoservice.xml" in msg:
            logger.info("metainfoservice.xml requested by Echo")
            self.handle_metainfo(socket)
        elif msg.startswith("POST /upnp/control/basicevent1 HTTP/1.1"):
            logger.info("BasicEvent1 requested")
            self.handle_action(msg, socket)

    @pyqtSlot()
    def remove_socket(self):
        logger.debug("Delete socket")
        socket: QTcpSocket = self.sender()
        self._sockets.remove(socket)
        socket.deleteLater()

    @staticmethod
    def add_http_headers(xml: str) -> str:
        date_str = formatdate(timeval=None, localtime=False, usegmt=True)
        return NEW_LINE.join(
            [
                "HTTP/1.1 200 OK",
                f'CONTENT-LENGTH: {len(xml.encode("utf8"))}',
                "CONTENT-TYPE: text/xml",
                f"DATE: {date_str}",
                "LAST-MODIFIED: Sat, 01 Jan 2000 00:01:15 GMT",
                "SERVER: Unspecified, UPnP/1.0, Unspecified",
                "X-User-Agent: Jemo",
                f"CONNECTION: close{NEW_LINE}",
                f"{xml}",
            ]
        )

    def handle_setup(self, socket: QTcpSocket):
        setup_xml = (
            '<?xml version="1.0"?>'
            "<root>"
            "<specVersion><major>1</major><minor>0</minor></specVersion>"
            "<device>"
            "<deviceType>urn:Belkin:device:controllee:1</deviceType>"
            f"<friendlyName>{self._name}</friendlyName>"
            "<manufacturer>Belkin International Inc.</manufacturer>"
            "<modelName>Emulated Socket</modelName>"
            "<modelNumber>3.1415</modelNumber>"
            f"<UDN>uuid:Socket-1_0-{self._serial}</UDN>"
            "<serviceList>"
            "<service>"
            "<serviceType>urn:Belkin:service:basicevent:1</serviceType>"
            "<serviceId>urn:Belkin:serviceId:basicevent1</serviceId>"
            "<controlURL>/upnp/control/basicevent1</controlURL>"
            "<eventSubURL>/upnp/event/basicevent1</eventSubURL>"
            "<SCPDURL>/eventservice.xml</SCPDURL>"
            "</service>"
            "<service>"
            "<serviceType>urn:Belkin:service:metainfo:1</serviceType>"
            "<serviceId>urn:Belkin:serviceId:metainfo1</serviceId>"
            "<controlURL>/upnp/control/metainfo1</controlURL>"
            "<eventSubURL>/upnp/event/metainfo1</eventSubURL>"
            "<SCPDURL>/metainfoservice.xml</SCPDURL>"
            "</service>"
            "</serviceList>"
            "</device>"
            "</root>"
        )

        setup_response = self.add_http_headers(setup_xml)
        logger.debug(f"Jemo response to setup request:\n{setup_response}")
        socket.write(setup_response.encode("utf8"))
        socket.waitForBytesWritten()
        socket.close()

    def handle_event(self, socket: QTcpSocket):
        eventservice_xml = (
            '<scpd xmlns="urn:Belkin:service-1-0">'
            "<actionList>"
            "<action>"
            "<name>SetBinaryState</name>"
            "<argumentList>"
            "<argument>"
            "<retval/>"
            "<name>BinaryState</name>"
            "<relatedStateVariable>BinaryState</relatedStateVariable>"
            "<direction>in</direction>"
            "</argument>"
            "</argumentList>"
            "</action>"
            "<action>"
            "<name>GetBinaryState</name>"
            "<argumentList>"
            "<argument>"
            "<retval/>"
            "<name>BinaryState</name>"
            "<relatedStateVariable>BinaryState</relatedStateVariable>"
            "<direction>out</direction>"
            "</argument>"
            "</argumentList>"
            "</action>"
            "</actionList>"
            "<serviceStateTable>"
            '<stateVariable sendEvents="yes">'
            "<name>BinaryState</name>"
            "<dataType>Boolean</dataType>"
            "<defaultValue>0</defaultValue>"
            "</stateVariable>"
            '<stateVariable sendEvents="yes">'
            "<name>level</name>"
            "<dataType>string</dataType>"
            "<defaultValue>0</defaultValue>"
            "</stateVariable>"
            "</serviceStateTable>"
            "</scpd>"
        ) + 2 * NEW_LINE

        eventservice_response = self.add_http_headers(eventservice_xml)
        logger.debug(f"Jemo response to eventservice request:\n{eventservice_response}")
        socket.write(eventservice_response.encode("utf8"))
        socket.waitForBytesWritten()
        socket.close()

    def handle_metainfo(self, socket: QTcpSocket):
        metainfoservice_xml = (
            '<scpd xmlns="urn:Belkin:service-1-0">'
            "<specVersion>"
            "<major>1</major>"
            "<minor>0</minor>"
            "</specVersion>"
            "<actionList>"
            "<action>"
            "<name>GetMetaInfo</name>"
            "<argumentList>"
            "<retval />"
            "<name>GetMetaInfo</name>"
            "<relatedStateVariable>MetaInfo</relatedStateVariable>"
            "<direction>in</direction>"
            "</argumentList>"
            "</action>"
            "</actionList>"
            "<serviceStateTable>"
            '<stateVariable sendEvents="yes">'
            "<name>MetaInfo</name>"
            "<dataType>string</dataType>"
            "<defaultValue>0</defaultValue>"
            "</stateVariable>"
            "</serviceStateTable>"
            "</scpd>"
        ) + 2 * NEW_LINE

        metainfoservice_response = self.add_http_headers(metainfoservice_xml)
        logger.debug(
            f"Jemo response to metainfoservice request:\n{metainfoservice_response}"
        )
        socket.write(metainfoservice_response.encode("utf8"))
        socket.waitForBytesWritten()
        socket.close()

    def handle_action(self, msg: str, socket: QTcpSocket):
        logger.debug(f"Handling action for plugin type {self._plugin}")

        soap_format = (
            "<s:Envelope "
            'xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
            's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
            "<s:Body>"
            "<u:{action}{action_type}Response "
            'xmlns:u="urn:Belkin:service:basicevent:1">'
            "<{action_type}>{return_val}</{action_type}>"
            "</u:{action}{action_type}Response>"
            "</s:Body>"
            "</s:Envelope>"
        ).format

        command_format = 'SOAPACTION: "urn:Belkin:service:basicevent:1#{}"'.format

        action: Optional[str] = None
        action_type: Optional[str] = None
        return_val: Optional[str] = None
        success: bool = False

        if command_format("GetBinaryState").casefold() in msg.casefold():
            logger.info(f"Attempting to get state for {self._plugin.name}")

            action = "Get"
            action_type = "BinaryState"
            state = self._plugin.get_state().casefold()
            logger.info(f"{self._plugin.name} state: {state}")

            if state in ("on", "off"):
                success = True
                return_val = str(int(state.lower() == "on"))

        elif command_format("SetBinaryState").casefold() in msg.casefold():
            action = "Set"
            action_type = "BinaryState"

            if "<BinaryState>0</BinaryState>" in msg:
                logger.info(f"Attempting to turn off {self._plugin.name}")
                return_val = "0"
                success = self._plugin.off()
            elif "<BinaryState>1</BinaryState>" in msg:
                logger.info(f"Attempting to turn on {self._plugin.name}")
                return_val = "1"
                success = self._plugin.on()
            else:
                logger.warning(f"Unrecognized request:\n{msg}")

        elif command_format("GetFriendlyName").casefold() in msg.casefold():
            action = "Get"
            action_type = "FriendlyName"
            return_val = self._plugin.name
            success = True
            logger.info(f"{self._plugin.name} returning friendly name")

        if success:
            soap_message = soap_format(
                action=action, action_type=action_type, return_val=return_val
            )
            response = self.add_http_headers(soap_message)
            logger.debug(f"Successful SOAP response:\n{response}")
            socket.write(response.encode("utf8"))
            socket.waitForBytesWritten()
        else:
            logger.warning(
                f"Unable to complete command for {self._plugin.name}:\n{msg}"
            )
            socket.close()


class SSDPServer(QObject):
    DISCOVER_PATTERNS = (
        "ST: urn:Belkin:device:**",
        "ST: upnp:rootdevice",
        "ST: ssdp:all",
    )

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self._devices: List[dict] = []
        self._socket: Optional[QUdpSocket] = None

    def add_device(self, name: str, ip_address: str, port: int):
        self._devices.append({"name": name, "ip_address": ip_address, "port": port})

    def start_server(self):
        self._socket = QUdpSocket(
            self, readyRead=self.read_datagrams, bytesWritten=self.bytes_written
        )
        if not self._socket.bind(
            QHostAddress.SpecialAddress.AnyIPv4,
            1900,
            mode=QUdpSocket.BindFlag.ReuseAddressHint,
        ):
            raise Exception("SSDPServer not able to bind port 1900")
        self._socket.joinMulticastGroup(QHostAddress("239.255.255.0"))

    @pyqtSlot("qint64")
    def bytes_written(self, num_bytes):  # pylint:disable=no-self-use
        logger.debug(f"UDP bytes written: {num_bytes}")

    @pyqtSlot()
    def read_datagrams(self):
        while self._socket.hasPendingDatagrams():
            datagram = self._socket.receiveDatagram()
            sender_address = datagram.senderAddress()
            sender_port = datagram.senderPort()
            data = datagram.data().data().decode("utf-8")

            logger.debug(
                f"Received data from {sender_address.toString()}:{sender_port}"
            )

            discover_pattern = next(
                (pattern for pattern in self.DISCOVER_PATTERNS if pattern in data), None
            )
            if discover_pattern and 'man: "ssdp:discover"' in data.lower():
                mx_value = 0.0
                mx_line = next(
                    (
                        line
                        for line in str(data).splitlines()
                        if line.startswith("MX: ")
                    ),
                    None,
                )
                if mx_line:
                    mx_str = mx_line.split()[-1]
                    if mx_str.replace(".", "", 1).isnumeric():
                        mx_value = float(mx_str)
                self.respond_to_search(
                    sender_address, sender_port, discover_pattern, mx_value
                )

    def respond_to_search(
        self,
        sender_address: QHostAddress,
        sender_port: int,
        discover_pattern: str,
        mx_value: float = 0.0,
    ):
        date_str = formatdate(timeval=None, localtime=False, usegmt=True)
        for device in self._devices:
            name = device["name"]
            ip_address = device["ip_address"]
            port = device["port"]

            location = f"http://{ip_address}:{port}/setup.xml"
            logger.debug(f"Location: {location}")
            serial = make_serial(name)
            usn = f"uuid:Socket-1_0-{serial}::" f'{discover_pattern.lstrip("ST: ")}'

            response = (
                NEW_LINE.join(
                    [
                        "HTTP/1.1 200 OK",
                        "CACHE-CONTROL: max-age=86400",
                        f"DATE: {date_str}",
                        "EXT:",
                        f"LOCATION: {location}",
                        'OPT: "http://schemas.upnp.org/upnp/1/0/"; ns=01',
                        f"01-NLS: {uuid.uuid4()}",
                        "SERVER: Jemo, UPnP/1.0, Unspecified",
                        f"{discover_pattern}",
                        f"USN: {usn}",
                    ]
                )
                + 2 * NEW_LINE
            )

            logger.debug(
                f"Sending response to {sender_address.toString()}:{sender_port} "
                f"with mx {mx_value}:\n{response!r}"
            )
            datagram = QNetworkDatagram(
                response.encode("utf8"), sender_address, sender_port
            )  # type:ignore

            if self._socket:
                QTimer.singleShot(
                    int(random() * max(0, min(5, int(mx_value)))) * 1000,
                    partial(self._socket.writeDatagram, datagram),  # type:ignore
                )


def main(config_file_path: str):
    if not os.path.exists(config_file_path):
        raise Exception(f"Config file '{config_file_path}' does not exist!")

    try:
        config = load_config_file(config_file_path)
    except Exception as exc:
        raise Exception(f"Unable to load config from '{config_file_path}'!") from exc

    logger.debug(f"Config: {config}")
    if "jemo" not in config:
        raise Exception("No 'jemo' section found in config")

    application = QApplication(sys.argv)

    def signal_handler(_, __):
        logger.debug("Attempting clean exit...")
        application.quit()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    jemo_config = config["jemo"]
    jemo_ip = jemo_config.get("ip_address", "auto")
    jemo_ip = get_local_ip(jemo_ip)

    try:
        plugins = jemo_config["plugins"]
    except KeyError as exc:
        raise Exception("No 'plugins' found in 'jemo' config") from exc

    ssdp_server = SSDPServer()
    jemo_devices: List[JemoDevice] = []
    plugin_module = importlib.import_module(f"{__package__}.plugins")
    for plugin, plugin_config in plugins.items():
        logger.debug(f"Loading plugin: {plugin}")

        PluginClass = getattr(plugin_module, plugin)  # pylint:disable=invalid-name
        if not issubclass(PluginClass, PluginBase):
            raise TypeError(f"Plugins must inherit from {repr(PluginBase)}")

        plugin_vars = {
            k: v for k, v in plugin_config.items() if k not in ("devices", "path")
        }
        logger.debug(f"{plugin} vars: {plugin_vars}")

        try:
            devices = plugin_config["devices"]
        except KeyError as exc:
            raise Exception(f"No 'devices' configured for {plugin}!") from exc

        for device in devices:
            logger.debug(f"{plugin} device config: {repr(device)}")

            device_plugin = PluginClass(**plugin_vars, **device)
            jemo_device = JemoDevice(device_plugin.name, device_plugin)
            jemo_device.start_server(jemo_ip, device_plugin.port)
            jemo_devices.append(jemo_device)
            ssdp_server.add_device(device_plugin.name, jemo_ip, device_plugin.port)

    ssdp_server.start_server()

    sys.exit(application.exec())
