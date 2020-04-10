from typing import Callable

ev_on_connect = None
ev_on_register = None
ev_on_unregister = None
ev_on_start = None
ev_on_stop = None
ev_on_resumt = None
ev_on_pause = None


def on_start(func: Callable[[str], None]) -> Callable[[], None]:
    global ev_on_start
    ev_on_start = func
    return func


def on_connect(func: Callable[[], None]) -> Callable[[], None]:
    global ev_on_connect
    ev_on_connect = func
    return func


def on_register(func: Callable[[str], None]) -> Callable[[], None]:
    global ev_on_register
    ev_on_register = func
    return func


def on_unregister(func: Callable[[str], None]) -> Callable[[], None]:
    global ev_on_unregister
    ev_on_unregister = func
    return func
