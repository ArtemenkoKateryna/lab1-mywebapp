from __future__ import annotations

import logging
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import BaseServer, ThreadingMixIn
from typing import Any

from mywebapp.application import InventoryApplication


LOGGER = logging.getLogger(__name__)


class ThreadingInventoryHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

    def __init__(self, server_address: tuple[str, int], handler_cls: type[BaseHTTPRequestHandler], application: InventoryApplication):
        self.application = application
        super().__init__(server_address, handler_cls)


class InheritedSocketHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, sock: socket.socket, handler_cls: type[BaseHTTPRequestHandler], application: InventoryApplication):
        self.application = application
        self.socket = sock
        self.server_address = sock.getsockname()
        BaseServer.__init__(self, self.server_address, handler_cls)
        self.server_name = socket.getfqdn(self.server_address[0])
        self.server_port = self.server_address[1]


class InventoryRequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:
        self._dispatch()

    def do_POST(self) -> None:
        self._dispatch()

    def _dispatch(self) -> None:
        content_length = int(self.headers.get("Content-Length", "0") or 0)
        body = self.rfile.read(content_length) if content_length else b""
        response = self.server.application.handle_request(
            method=self.command,
            target=self.path,
            headers=self.headers,
            body=body,
        )
        self.send_response(response.status_code)
        for key, value in response.headers.items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(response.body)))
        self.end_headers()
        if response.body:
            self.wfile.write(response.body)

    def log_message(self, fmt: str, *args: Any) -> None:
        LOGGER.info("%s - - %s", self.client_address[0], fmt % args)


def run_server(host: str, port: int, application: InventoryApplication, listen_fd: int | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if listen_fd is None:
        server = ThreadingInventoryHTTPServer((host, port), InventoryRequestHandler, application)
    else:
        inherited_socket = socket.fromfd(listen_fd, socket.AF_INET, socket.SOCK_STREAM)
        inherited_socket.setblocking(True)
        server = InheritedSocketHTTPServer(inherited_socket, InventoryRequestHandler, application)
    try:
        server.serve_forever()
    finally:
        server.server_close()
