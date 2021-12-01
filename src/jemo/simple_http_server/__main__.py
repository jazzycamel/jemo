# import argparse
# import json
# import re
# import sys
# from email.utils import formatdate
# from typing import Optional
#
# from PyQt6.QtCore import QObject, pyqtSlot
# from PyQt6.QtNetwork import QHostAddress, QTcpServer, QTcpSocket
# from PyQt6.QtWidgets import QApplication
#
# from .. import logger
#
# NEW_LINE = "\r\n"
# HTTP_REQUEST_RE = re.compile(
#     r"^(?P<method>GET|POST)\s+(?P<path>([^?\s]+)((?:[?&][^&\s]+)*))\s+"
# )
#
#
# class SimpleHTTPServer(QObject):
#     def __init__(self, parent=None, **kwargs):
#         super().__init__(parent, **kwargs)
#
#         self._server: Optional[QTcpServer] = None
#         self._sockets = []
#         self._status = "off"
#
#     def start_server(self, ip_address: str, port: int):
#         self._server = QTcpServer(self, newConnection=self.new_connection)
#         self._server.listen(QHostAddress(ip_address), port)
#         if not self._server.isListening():
#             raise Exception(f"Not able to listen on {ip_address}:{port}")
#         logger.debug(f"Started SimpleHTTPServer listening on {ip_address}:{port}")
#
#     @pyqtSlot()
#     def new_connection(self):
#         socket: QTcpSocket = self._server.nextPendingConnection()
#         socket.readyRead.connect(self.read_data)
#         socket.disconnected.connect(self.remove_socket)
#         self._sockets.append(socket)
#
#     @pyqtSlot()
#     def read_data(self):
#         socket: QTcpSocket = self.sender()
#         message = socket.readAll().data().decode("utf8")
#
#         match = HTTP_REQUEST_RE.match(message)
#         if match:
#             method = match.group("method")
#
#             path = match.group("path")
#             name = f"route_{method.lower()}_{path.split('/',2)[1]}"
#             try:
#                 response = getattr(self, name)()
#                 json_response = json.dumps(response, separators=(",", ":"))
#                 http_response = self.make_http_response(json_response)
#                 socket.write(http_response.encode("utf8"))
#                 socket.waitForBytesWritten()
#             except Exception as exc:  # pylint:disable=broad-except
#                 logger.debug(f"{exc}")
#
#         socket.close()
#
#     def route_post_on(self):
#         logger.debug("Status ON")
#         self._status = "on"
#         return {"status": self._status}
#
#     def route_post_off(self):
#         logger.debug("Status OFF")
#         self._status = "off"
#         return {"status": self._status}
#
#     def route_get_status(self):
#         logger.debug("Status GET")
#         return {"status": self._status}
#
#     @staticmethod
#     def make_http_response(response: str) -> str:
#         date_str = formatdate(timeval=None, localtime=False, usegmt=True)
#         return NEW_LINE.join(
#             [
#                 "HTTP/1.1 200 OK",
#                 f'CONTENT-LENGTH: {len(response.encode("utf8"))}',
#                 "CONTENT-TYPE: application/json",
#                 f"DATE: {date_str}",
#                 "LAST-MODIFIED: Sat, 01 Jan 2000 00:01:15 GMT",
#                 "SERVER: Unspecified, UPnP/1.0, Unspecified",
#                 "X-User-Agent: Jemo",
#                 f"CONNECTION: close{NEW_LINE}",
#                 f"{response}",
#             ]
#         )
#
#     @pyqtSlot()
#     def remove_socket(self):
#         socket: QTcpSocket = self.sender()
#         self._sockets.remove(socket)
#         socket.deleteLater()
#
#
# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="SimpleHTTPServer")
#     parser.add_argument("-H", "--host", required=True)
#     parser.add_argument("-p", "--port", type=int, required=True)
#     parser.add_argument(
#         "-v",
#         "--verbose",
#         help="Increase verbosity (may increase up to -vvv)",
#         action="count",
#         default=0,
#     )
#     args = parser.parse_args()
#
#     # 40-10*0=40==logging.ERROR
#     verbosity = max(40 - 10 * args.verbose, 10)
#     logger.setLevel(verbosity)
#
#     a = QApplication(sys.argv)
#     s = SimpleHTTPServer()
#     s.start_server(args.host, args.port)
#     sys.exit(a.exec())
