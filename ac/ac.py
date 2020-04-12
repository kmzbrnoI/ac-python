"""AC class definition & AC storage definition."""

from enum import Enum
from typing import Callable, Optional, List, Any, Dict, TypeVar, DefaultDict
import logging
import traceback

from . import panel_client
from . import pt


class State(Enum):
    STOPPED = 0
    RUNNING = 1
    PAUSED = 2


ACEvent = Callable[['AC'], None]


class AC:
    """
    AC class represents a single AC. It holds its state and allows user
    to call methods on it. Interaction with Panel Server as well as PT Server
    should go throug instance of AC.
    """

    def __init__(self, _id: str) -> None:
        self.id = _id
        self.password = ''
        self.state = State.STOPPED
        self.registered = False
        self.statestr = ''
        self.fg_color = 0xFFFF00

        self.on_register: Optional[ACEvent] = None
        self.on_unregister: Optional[ACEvent] = None
        self.on_start: Optional[ACEvent] = None
        self.on_stop: Optional[ACEvent] = None
        self.on_resume: Optional[ACEvent] = None
        self.on_pause: Optional[ACEvent] = None

    def running(self) -> bool:
        return self.state == State.RUNNING

    def paused(self) -> bool:
        return self.state == State.PAUSED

    def stopped(self) -> bool:
        return self.state == State.STOPPED

    def call(self, event: Optional[ACEvent]) -> None:
        if event is not None:
            try:
                event(self)
            except Exception:
                traceback.print_exc()

    def done(self) -> None:
        panel_client.send(f'-;AC;{self.id};CONTROL;DONE')

    def disp_error(self, message: str) -> None:
        panel_client.send(f'-;AC;{self.id};CONTROL;ERROR;DISPBOTTOM;{message}')

    def register(self, password: str) -> None:
        self.statestr = ''
        self.password = password
        panel_client.send(f'-;AC;{self.id};LOGIN;{password}')

    def unregister(self) -> None:
        self.password = ''
        panel_client.send(f'-;AC;{self.id};LOGOUT')

    def statestr_send(self) -> None:
        assert '{' not in self.statestr and '}' not in self.statestr
        lines = ','.join(['{'+line+'}' for line in self.statestr.split('\n')])
        lines = '{' + lines + '}'
        panel_client.send(f'-;AC;{self.id};CONTROL;STATE;{lines}')

    def statestr_add(self, s: str) -> None:
        assert '{' not in s and '}' not in s
        self.statestr += s + '\n'

    def set_color(self, color: int) -> None:
        self.color = color
        hexcolor = hex(color)[2:].zfill(6)
        panel_client.send(f'-;AC;{self.id};CONTROL;FG-COLOR;{hexcolor}')

    def on_message(self, parsed: List[str]) -> None:
        if parsed[3] == 'AUTH':
            assert len(parsed) >= 5
            if parsed[4] == 'ok':
                self.registered = True
                self.call(self.on_register)
            elif parsed[4] == 'nok':  # TODO
                self.registered = False
                logging.error(f'Registration error {parsed[5]}: {parsed[6]}')
            elif parsed[4] == 'logout':
                self.registered = False
                self.call(self.on_unregister)

        elif parsed[3] == 'CONTROL':
            assert len(parsed) >= 5
            remap = {
                'START': State.RUNNING,
                'STOP': State.STOPPED,
                'PAUSE': State.PAUSED,
                'RESUME': State.RUNNING,
            }
            self.state = remap[parsed[4].upper()]

            if parsed[4].upper() in ['START', 'STOP']:
                self.fg_color = 0xFFFF00

            event = 'on_' + parsed[4].lower()
            if hasattr(self, event):
                self.call(getattr(self, event))

    def pt_get(self, path: str) -> Dict[str, Any]:
        return pt.get(path)

    def pt_put(self, path: str, req_data: Dict[str, Any]) -> Dict[str, Any]:
        return pt.put(path, req_data, self.id, self.password)


KT = TypeVar('KT')
VT = TypeVar('VT')


class keydefaultdict(DefaultDict[KT, VT]):
    def __missing__(self, key: KT) -> VT:
        if self.default_factory is None:
            raise KeyError(key)
        ret = self[key] = self.default_factory(key)  # type: ignore
        return ret


ACs: keydefaultdict[str, AC] = keydefaultdict(AC)  # type: ignore
