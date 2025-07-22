"""Panel client socket management"""

from collections import deque
import socket
import logging
from typing import Optional, List
import traceback
import time
import select
import datetime

from . import message_parser
from . import events
from .ac import ACs
from . import blocks
from . import pt

CLIENT_PROTOCOL_VERSION = '1.1'
SOCKET_TIMEOUT = 10  # seconds
UPDATE_PERIOD = 1  # seconds

panel_socket: Optional[socket.socket] = None


class DisconnectedError(Exception):
    pass


class OutdatedVersionError(Exception):
    pass


def _listen(sock: socket.socket) -> None:
    next_update = datetime.datetime.now() + \
                  datetime.timedelta(seconds=UPDATE_PERIOD)

    try:
        while True:
            readable, writable, exceptional = select.select(
                [sock], [], [sock], UPDATE_PERIOD
            )

            if sock in exceptional:
                raise DisconnectedError('Socket exception!')

            if sock in readable:
                _handle_ready_read(sock)

            if datetime.datetime.now() > next_update:
                next_update = datetime.datetime.now() + \
                              datetime.timedelta(seconds=UPDATE_PERIOD)
                for ac_ in ACs.values():
                    try:
                        ac_.on_update()
                    except Exception:
                        traceback.print_exc()
                events.call(events.evs_on_update)

    except Exception as e:
        logging.error(f'Connection error: {e}')


def _handle_ready_read(sock: socket.socket) -> None:
    data = sock.recv(2048)
    if not data:
        raise DisconnectedError('Disconnected from server!')

    recv = data.decode('utf-8').replace('\r', '')

    if '\n' not in recv:
        return

    q = deque(recv.splitlines(keepends=True))

    while q:
        item = q.popleft()
        logging.debug(f'> {item.strip()}')

        if item.endswith('\n'):
            try:
                _process_message(sock, item.strip())
            except Exception as e:
                logging.warning(f'Message processing error: {str(e)}!')
                traceback.print_exc()


def send(message: str, sock: Optional[socket.socket] = None) -> None:
    """Send message to server."""
    if sock is None:
        global panel_socket
        sock = panel_socket
    assert sock is not None

    try:
        logging.debug(f'< {message}')
        sock.send((message + '\n').encode('UTF-8'))

    except Exception as e:
        logging.error(f'Connection exception: {e}')


def _process_message(sock: socket.socket, message: str) -> None:
    parsed = message_parser.parse(message, ';')
    if len(parsed) < 2:
        return

    parsed[1] = parsed[1].upper()
    if len(parsed) > 3:
        parsed[3] = parsed[3].upper()

    if parsed[1] == 'HELLO':
        _process_hello(parsed)
    elif (parsed[1] == 'PING' and len(parsed) > 2 and
          parsed[2].upper() == 'REQ-RESP'):
        if len(parsed) > 3:
            send(f'-;PONG;{parsed[3]}', sock)
        else:
            send('-;PONG', sock)
    elif (len(parsed) >= 4 and parsed[0] == '-' and parsed[1] == 'AC'):
        if parsed[2] != '-':
            ACs[parsed[2]].on_message(parsed)
        elif parsed[2] == '-' and parsed[3].upper() == 'BLOCKS':
            blocks.on_message(parsed)


def _process_hello(parsed: List[str]) -> None:
    version = float(parsed[2])
    logging.info(f'Server version: {version}')

    if version < 1:
        raise OutdatedVersionError(f'Outdated version of server protocol: {version}!')

    for ac_ in ACs.values():
        try:
            ac_.on_connect()
        except Exception:
            traceback.print_exc()
    events.call(events.evs_on_connect)
    blocks._send_all_registrations()


def _connect(server: str, port: int) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(SOCKET_TIMEOUT)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 1)
    sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 1)
    sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 5)
    sock.connect((server, port))
    sock.setblocking(False)

    return sock


def init(server: str, port: int, app_name: str = '') -> None:
    """
    Infinite function to open & keep open socket with Panel server.
    Tries to restore connection in case of connection loss.
    """
    global panel_socket
    pt.server = server

    while True:
        connected = False
        try:
            logging.info(f'Initializing connection to {server}:{port}...')
            sock = _connect(server, port)
            connected = True
            logging.info('Socket opened')
            panel_socket = sock
            send(f'-;HELLO;{CLIENT_PROTOCOL_VERSION};{app_name}', sock)
            _listen(sock)
        except DisconnectedError:
            logging.info('Disconnected from server')
        except socket.timeout:
            logging.info('Unable to connect to server')
        except OSError as e:
            logging.info(e)
            time.sleep(9)

        if connected:
            for ac_ in ACs.values():
                try:
                    ac_.on_disconnect()
                except Exception:
                    traceback.print_exc()
            events.call(events.evs_on_disconnect)
        time.sleep(1)
