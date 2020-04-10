from typing import List

from . import panel_client
from . import events


def register(_id: str, password: str) -> None:
    panel_client.send(f'-;AC;{_id};LOGIN;{password}')


def unregister(_id: str) -> None:
    panel_client.send(f'-;AC;{_id};LOGOUT')


def on_register_message(parsed: List[str]):
    if len(parsed) < 5:
        return

    if parsed[4] == 'ok':
        events.call(events.ev_on_register, parsed[2])
    elif parsed[4] == 'nok':
        # TODO
        pass
    elif parsed[4] == 'logout':
        if events.ev_on_unregister:
            events.ev_on_unregister(parsed[2])
