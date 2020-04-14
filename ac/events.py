"""Package event definitions. This file implements decorators to easily
register events. See examples below."""

import traceback
from typing import Callable, List

evs_on_connect: List[Callable[[], None]] = []
evs_on_disconnect: List[Callable[[], None]] = []
evs_on_update: List[Callable[[], None]] = []


def on_connect(func: Callable[[], None]) -> Callable[[], None]:
    evs_on_connect.append(func)
    return func


def on_disconnect(func: Callable[[], None]) -> Callable[[], None]:
    evs_on_disconnect.append(func)
    return func


def on_update(func: Callable[[], None]) -> Callable[[], None]:
    evs_on_update.append(func)
    return func


def call(events: List[Callable[[], None]]) -> None:
    for event in events:
        try:
            event()
        except Exception:
            traceback.print_exc()
