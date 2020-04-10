from typing import Callable
from .ac import ACs

ev_on_connect = None


def on_connect(func: Callable[[], None]) -> Callable[[], None]:
    global ev_on_connect
    ev_on_connect = func
    return func


def on_register(id_: str) -> Callable[[str], None]:
    def decorate(function: Callable[[str], None]):
        ACs[id_].on_register = function
        return function

    return decorate


def on_unregister(id_: str) -> Callable[[str], None]:
    def decorate(function: Callable[[str], None]):
        ACs[id_].on_unregister = function
        return function

    return decorate


def on_start(id_: str) -> Callable[[str], None]:
    def decorate(function: Callable[[str], None]):
        ACs[id_].on_start = function
        return function

    return decorate


def on_stop(id_: str) -> Callable[[str], None]:
    def decorate(function: Callable[[str], None]):
        ACs[id_].on_stop = function
        return function

    return decorate


def on_resume(id_: str) -> Callable[[str], None]:
    def decorate(function: Callable[[str], None]):
        ACs[id_].on_resume = function
        return function

    return decorate


def on_pause(id_: str) -> Callable[[str], None]:
    def decorate(function: Callable[[str], None]):
        ACs[id_].on_pause = function
        return function

    return decorate
