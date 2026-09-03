#!/usr/bin/env python3
"""
Axiom OpenVPN HTTP Payload Injection Proxy
Modernized for Python 3.14+ supporting custom payload headers for OpenVPN.
"""

import logging
import select
import socket
import sys
import threading

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AxiomOpenVPNProxy")

BUFLEN = 65536
TIMEOUT = 60
MSG = "Welcome to Axiom"
DEFAULT_TARGET = "127.0.0.1:1194"
DEFAULT_HOST = "127.0.0.1:1194"
RESPONSE = f"HTTP/1.1 200 Connection Established\r\n\r\n<!-- <font color=\"cyan\">{MSG}</font> -->\r\n\r\n".encode()


class OpenVPNConnectionHandler(threading.Thread):
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
            request = self.client_sock.recv(BUFLEN)
            if not request:
                self.close()
                return

            target_host, target_port = self.target_str.split(":", 1)
            self.target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.target_sock.settimeout(TIMEOUT)
            self.target_sock.connect((target_host, int(target_port)))

            # Respond with 200 OK
            self.client_sock.sendall(RESPONSE)

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
            logger.debug("OpenVPN proxy error for %s: %s", self.client_addr, e)
        finally:
            self.close()


class OpenVPNProxyServer:
    def __init__(self, bind_host: str = "0.0.0.0", bind_port: int = 80, target: str = DEFAULT_TARGET):
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
        logger.info("Axiom OpenVPN Proxy listening on %s:%d -> %s", self.bind_host, self.bind_port, self.target)

        try:
            while self.running:
                try:
                    client_sock, client_addr = self.server_sock.accept()
                    handler = OpenVPNConnectionHandler(client_sock, client_addr, self.target)
                    handler.start()
                except Exception as e:
                    if self.running:
                        logger.error("OpenVPN proxy accept error: %s", e)
        except KeyboardInterrupt:
            logger.info("Stopping OpenVPN proxy...")
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
    port = 80
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.error("Invalid port specified: %s", sys.argv[1])
            sys.exit(1)

    target = DEFAULT_TARGET
    if len(sys.argv) > 2:
        target = sys.argv[2]

    server = OpenVPNProxyServer(bind_port=port, target=target)
    server.start()


if __name__ == "__main__":
    main()
