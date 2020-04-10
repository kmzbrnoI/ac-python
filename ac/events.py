from typing import Callable

ev_on_disconnect = None
ev_on_start = None
ev_on_connect = None
ev_on_stop = None
ev_on_resumt = None
ev_on_pause = None


def on_start(func: Callable[[], None]) -> Callable[[], None]:
    ev_on_start = func
    return func
