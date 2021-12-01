import uuid
from typing import Optional

from PyQt6.QtNetwork import QHostInfo, QUdpSocket

from . import logger


def get_local_ip(ip_address: Optional[str] = None) -> str:
    if not ip_address or ip_address.lower() == "auto":
        logger.debug("Attempting to get IP address automatically")

        logger.debug(f"Host name: {QHostInfo.localHostName()}")
        host_name = QHostInfo.localHostName()
        host_info = QHostInfo.fromName(host_name)
        host_address = host_info.addresses()[0].toString()

        if host_address in ("127.0.1.1", "127.0.0.1", "localhost", "unknown"):
            logger.debug("(Damn you linux!)")

            udp_socket = QUdpSocket()
            udp_socket.connectToHost("8.8.8.8", 80)
            if not udp_socket.waitForConnected():
                raise Exception("Unable to determine IP address!")
            host_address = udp_socket.localAddress().toString()

        logger.debug(f"Using IP address: {host_address}")
        return host_address
    return ip_address


def make_serial(name: str) -> str:
    return str(uuid.uuid3(uuid.NAMESPACE_X500, name))
