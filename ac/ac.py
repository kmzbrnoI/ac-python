"""AC class definition & AC storage definition."""

from enum import Enum
from typing import Callable, List, Any, Dict, TypeVar, DefaultDict
import logging

from . import panel_client
from . import pt


class State(Enum):
    STOPPED = 0
    RUNNING = 1
    PAUSED = 2


ACEvent = Callable[['AC'], None]


class AC:
    """
    AC class is s base class representing a single AC. It holds its state and allows user
    to call methods on it. Interaction with Panel Server as well as with PT Server
    should go throug instance of AC.
    To implement specific AC functionality, one should inherit its own class
    from 'AC' class and implement AC-specific functionality in bodies of 'on_*' methods
    or react to e.g. blocks change (see blocks.py). See examples.
    """

    def __init__(self, id_: str, password: str = '') -> None:
        self.id = id_
        self.password = password
        self.state = State.STOPPED
        self.registered = False
        self.statestr = ''
        self.fg_color = 0xFFFF00

    def on_register(self) -> None:
        """
        This method is called when the instance is registered with the hJOPserver's AC block.
        Body of this method is supposed to be implemented in the derived class.
        """
        pass

    def on_unregister(self) -> None:
        """
        This method is called when the instance is unregistered from the hJOPserver's AC block.
        Body of this method is supposed to be implemented in the derived class.
        """
        pass

    def on_start(self) -> None:
        """
        This method is called when the dispatcher clicks 'START' on the AC block in hJOPpanel.
        Body of this method is supposed to be implemented in the derived class.
        """
        pass

    def on_stop(self) -> None:
        """
        This method is called when the dispatcher clicks 'STOP' on the AC block in hJOPpanel.
        Body of this method is supposed to be implemented in the derived class.
        """
        pass

    def on_pause(self) -> None:
        """
        This method is called when the dispatcher clicks 'PAUZA' on the AC block in hJOPpanel.
        Body of this method is supposed to be implemented in the derived class.
        """
        pass

    def on_resume(self) -> None:
        """
        This method is called when the dispatcher clicks 'POKRAČ' on the AC block in hJOPpanel.
        Body of this method is supposed to be implemented in the derived class.
        """
        pass

    def on_update(self) -> None:
        """Called periodically."""
        if not self.registered:
            self.register(self.password)

    def on_connect(self) -> None:
        """Called when panel client connects to hJOPserver"""
        self.register(self.password)

    def on_disconnect(self) -> None:
        """Called when panel client disconnects from hJOPserver"""
        pass

    def running(self) -> bool:
        return self.state == State.RUNNING

    def paused(self) -> bool:
        return self.state == State.PAUSED

    def stopped(self) -> bool:
        return self.state == State.STOPPED

    def done(self) -> None:
        """Call when you need to signalize that the AC is finished."""
        panel_client.send(f'-;AC;{self.id};CONTROL;DONE')

    def disp_error(self, message: str) -> None:
        """Display error to the dispatcher."""
        panel_client.send(f'-;AC;{self.id};CONTROL;ERROR;DISPBOTTOM;{message}')

    def register(self, password: str) -> None:
        self.statestr = ''
        self.password = password
        panel_client.send(f'-;AC;{self.id};LOGIN;{password}')

    def unregister(self) -> None:
        self.password = ''
        panel_client.send(f'-;AC;{self.id};LOGOUT')

    """
    AC client can send multiline 'state' messages to the server.
    The messages are show in hJOPpanel under 'INFO' option in the AC block's menu.
    """

    def statestr_send(self) -> None:
        """Send whole 'state' string to the hJOPserver."""
        assert '{' not in self.statestr and '}' not in self.statestr
        lines = ','.join(['{'+line+'}' for line in self.statestr.split('\n')])
        lines = '{' + lines + '}'
        panel_client.send(f'-;AC;{self.id};CONTROL;STATE;{lines}')

    def statestr_add(self, s: str) -> None:
        """Add single line to the 'state' string."""
        assert '{' not in s and '}' not in s
        self.statestr += s + '\n'

    def set_color(self, color: int) -> None:
        """Set color of the AC block in hJOPpanel (e.g. to indicate warning/error state)."""
        self.color = color
        hexcolor = hex(color)[2:].zfill(6)
        panel_client.send(f'-;AC;{self.id};CONTROL;FG-COLOR;{hexcolor}')

    def on_message(self, parsed: List[str]) -> None:
        if parsed[3] == 'AUTH':
            assert len(parsed) >= 5
            if parsed[4] == 'ok':
                self.registered = True
                self.on_register()
            elif parsed[4] == 'nok':  # TODO
                self.registered = False
                logging.error(f'Registration error {parsed[5]}: {parsed[6]}')
            elif parsed[4] == 'logout':
                self.registered = False
                self.on_unregister()

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
                getattr(self, event)()

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
