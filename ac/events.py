from typing import Callable, Dict

ev_on_connect = None
ev_on_register: Dict[str, Callable[[str], None]] = {}
ev_on_unregister: Dict[str, Callable[[str], None]] = {}
ev_on_start: Dict[str, Callable[[str], None]] = {}
ev_on_stop: Dict[str, Callable[[str], None]] = {}
ev_on_resumt: Dict[str, Callable[[str], None]] = {}
ev_on_pause: Dict[str, Callable[[str], None]] = {}


def call(event: Dict[str, Callable[[str], None]], id_: str) -> None:
    if id_ in event.keys():
        event[id_](id_)


def on_connect(func: Callable[[], None]) -> Callable[[], None]:
    global ev_on_connect
    ev_on_connect = func
    return func


def on_register(id_: str) -> Callable[[str], None]:
    def decorate(function: Callable[[str], None]):
        global ev_on_register
        ev_on_register[id_] = function
        return function

    return decorate


def on_unregister(id_: str) -> Callable[[str], None]:
    def decorate(function: Callable[[str], None]):
        global ev_on_unregister
        ev_on_unregister = function
        return function

    return decorate


def on_start(id_: str) -> Callable[[str], None]:
    def decorate(function: Callable[[str], None]):
        global ev_on_start
        ev_on_start = function
        return function

    return decorate
