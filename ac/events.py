"""Package event definitions. This file implements decorators to easily
register events. See examples below."""

from typing import Callable
from .ac import AC

ACEvent = Callable[[AC], None]
ACDecorator = Callable[[ACEvent], ACEvent]
ev_on_connect = None
ev_on_disconnect = None


def on_connect(func: Callable[[], None]) -> Callable[[], None]:
    global ev_on_connect
    ev_on_connect = func
    return func


def on_disconnect(func: Callable[[], None]) -> Callable[[], None]:
    global ev_on_disconnect
    ev_on_disconnect = func
    return func
