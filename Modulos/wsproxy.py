#!/usr/bin/env python3
"""
Axiom WebSocket (HTTP/1.1 101 Switching Protocols) Tunnel Proxy
Modernized for Python 3.14+ supporting custom CDN headers and payload upgrades.
"""

import logging
import select
import socket
import sys
import threading

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AxiomWSProxy")

BUFLEN = 65536
TIMEOUT = 60
DEFAULT_TARGET = "127.0.0.1:22"
WS_RESPONSE = (
    b"HTTP/1.1 101 Switching Protocols\r\n"
    b"Upgrade: websocket\r\n"
    b"Connection: Upgrade\r\n"
    b"Sec-WebSocket-Accept: AxiomTunnel\r\n\r\n"
)


class WSConnectionHandler(threading.Thread):
    def __init__(self, client_sock: socket.socket, client_addr: tuple, target_str: str = DEFAULT_TARGET):
        super().__init__(daemon=True)
        self.client_sock = client_sock
        self.client_addr = client_addr
        self.target_str = target_str
        self.target_sock: socket.socket | None = None
        self.running = True

    def close(self):
        self.running = False
        for s in (self.client_sock, self.target_sock):
            if s:
                try:
                    s.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                try:
                    s.close()
                except Exception:
                    pass

    def run(self):
        try:
            self.client_sock.settimeout(TIMEOUT)
            header_data = b""
            while b"\r\n\r\n" not in header_data:
                chunk = self.client_sock.recv(4096)
                if not chunk:
                    self.close()
                    return
                header_data += chunk
                if len(header_data) > 65536:
                    self.close()
                    return

            target_host, target_port = self.target_str.split(":", 1)
            self.target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.target_sock.settimeout(TIMEOUT)
            self.target_sock.connect((target_host, int(target_port)))

            # Respond with 101 Switching Protocols
            self.client_sock.sendall(WS_RESPONSE)

            # Bidirectional pipe
            sockets = [self.client_sock, self.target_sock]
            while self.running:
                readable, _, exceptional = select.select(sockets, [], sockets, 3)
                if exceptional:
                    break
                for s in readable:
                    data = s.recv(BUFLEN)
                    if not data:
                        self.running = False
                        break
                    if s is self.client_sock:
                        self.target_sock.sendall(data)
                    else:
                        self.client_sock.sendall(data)
        except Exception as e:
            logger.debug("WS Proxy error for %s: %s", self.client_addr, e)
        finally:
            self.close()


class WSProxyServer:
    def __init__(self, bind_host: str = "0.0.0.0", bind_port: int = 8080, target: str = DEFAULT_TARGET):
        self.bind_host = bind_host
        self.bind_port = bind_port
        self.target = target
        self.server_sock: socket.socket | None = None
        self.running = False

    def start(self):
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind((self.bind_host, self.bind_port))
        self.server_sock.listen(128)
        self.running = True
        logger.info("Axiom WebSocket Proxy listening on %s:%d -> %s", self.bind_host, self.bind_port, self.target)

        try:
            while self.running:
                try:
                    client_sock, client_addr = self.server_sock.accept()
                    handler = WSConnectionHandler(client_sock, client_addr, self.target)
                    handler.start()
                except Exception as e:
                    if self.running:
                        logger.error("WS accept error: %s", e)
        except KeyboardInterrupt:
            logger.info("Stopping WebSocket proxy...")
        finally:
            self.stop()

    def stop(self):
        self.running = False
        if self.server_sock:
            try:
                self.server_sock.close()
            except Exception:
                pass


def main():
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.error("Invalid port specified: %s", sys.argv[1])
            sys.exit(1)

    target = DEFAULT_TARGET
    if len(sys.argv) > 2:
        target = sys.argv[2]

    server = WSProxyServer(bind_port=port, target=target)
    server.start()


if __name__ == "__main__":
    main()
