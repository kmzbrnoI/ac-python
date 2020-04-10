from enum import Enum
from typing import Callable, Optional, List
from collections import defaultdict
from . import panel_client


class State(Enum):
    STOPPED = 0
    RUNNING = 1
    PAUSED = 2


ACEvent = Callable[['AC'], None]


class AC:
    def __init__(self, _id: str) -> None:
        self.id = _id
        self.state = State.STOPPED

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
            event(self)

    def done(self) -> None:
        panel_client.send(f'-;AC;{self.id};CONTROL:DONE')

    def error(self) -> None:  # TODO
        panel_client.send(f'-;AC;{self.id};CONTROL:ERROR;')

    def register(self, password: str) -> None:
        panel_client.send(f'-;AC;{self.id};LOGIN;{password}')

    def unregister(self) -> None:
        panel_client.send(f'-;AC;{self.id};LOGOUT')

    def on_message(self, parsed: List[str]) -> None:
        if parsed[3] == 'AUTH':
            assert len(parsed) >= 5
            if parsed[4] == 'ok':
                self.call(self.on_register)
            elif parsed[4] == 'nok':  # TODO
                pass
            elif parsed[4] == 'logout':
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

            event = 'on_' + parsed[4].lower()
            if hasattr(self, event):
                self.call(getattr(self, event))


class keydefaultdict(defaultdict):
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        else:
            ret = self[key] = self.default_factory(key)
            return ret


ACs = keydefaultdict(AC)
