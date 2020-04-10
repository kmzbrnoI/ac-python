#!/usr/bin/env python3

import logging
import ac
from ac import ACs, AC, State

AC_ID = '5000'


@ac.on_connect
def on_connect():
    logging.info('connected')
    ACs[AC_ID].register('loskarlos')


@ac.on_register(AC_ID)
def on_register(ac: AC):
    logging.info(f'{ac.id}: registered')


@ac.on_resume(AC_ID)
@ac.on_start(AC_ID)
def on_start(ac: AC):
    logging.info(f'{ac.id}: start')
    assert ac.state == State.RUNNING


@ac.on_stop(AC_ID)
def on_stop(ac: AC):
    logging.info(f'{ac.id}: stop')
    assert ac.state == State.STOPPED


@ac.on_pause(AC_ID)
def on_pause(ac: AC):
    logging.info(f'{ac.id}: pause')
    assert ac.state == State.PAUSED


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    ac.init('192.168.0.168', 5896)


if __name__ == '__main__':
    main()
