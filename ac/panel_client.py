from collections import deque
import socket
import logging
from typing import Optional, List
import traceback

from .message_parser import parse

CLIENT_PROTOCOL_VERSION = '1.1'

panel_socket: Optional[socket.socket] = None


class DisconnectedError(Exception):
    pass


class OutdatedVersionError(Exception):
    pass


def _listen(sock: socket.socket) -> None:
    previous = ''

    try:
        while sock:
            data = sock.recv(2048)
            if not data:
                raise DisconnectedError('Disconnected from server!')

            recv = previous + data.decode('utf-8').replace('\r', '')
            previous = ''

            if '\n' not in recv:
                previous = recv
                continue

            q = deque(recv.splitlines(keepends=True))

            while q:
                item = q.popleft()
                logging.debug('> {0}'.format(item.strip()))

                if item.endswith('\n'):
                    try:
                        _process_message(sock, item.strip())
                    except Exception as e:
                        logging.warning('Message processing error: '
                                        '{0}!'.format(str(e)))
                        traceback.print_exc()
                else:
                    previous = item

    except Exception as e:
        logging.error('Connection error: {0}'.format(e))


def _send(message: str, sock: Optional[socket.socket] = None) -> None:
    if sock is None:
        sock = panel_socket
    assert sock is not None

    try:
        logging.debug('< {0}'.format(message))
        sock.send((message + '\n').encode('UTF-8'))

    except Exception as e:
        logging.error('Connection exception: {0}'.format(e))


def _process_message(sock: socket.socket, message: str) -> None:
    parsed = parse(message, ';')
    if len(parsed) < 2:
        return

    parsed[1] = parsed[1].upper()

    if parsed[1] == 'HELLO':
        _process_hello(parsed)
    elif (parsed[1] == 'PING' and len(parsed) > 2 and
          parsed[2].upper() == 'REQ-RESP'):
        if len(parsed) > 3:
            _send('-;PONG;{0}'.format(parsed[3]), sock)
        else:
            _send('-;PONG', sock)
    else:
        pass


def _process_hello(parsed: List[str]) -> None:
    version = float(parsed[2])
    logging.info('Server version: {0}.'.format(version))

    if version < 1:
        raise OutdatedVersionError('Outdated version of server protocol: '
                                   '{0}!'.format(version))


def _connect(server: str, port: int) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(50)
    sock.connect((server, port))
    return sock


def init(server: str, port: int) -> None:
    logging.debug(f'Initializing connection to {server}:{port}...')
    sock = _connect(server, port)
    logging.debug('Socket opened')
    panel_socket = sock

    _send('-;HELLO;{0}'.format(CLIENT_PROTOCOL_VERSION), sock)
    _listen(sock)
