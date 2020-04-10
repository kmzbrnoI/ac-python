#!/usr/bin/env python3

"""Basic test of ac package."""

import logging
import ac
import ac.blocks
from ac import ACs, AC, State

HOSTNAME = '192.168.0.168'
PORT = 5896
AC_ID = '5000'


@ac.on_connect
def _on_connect() -> None:
    logging.info('connected')
    ACs[AC_ID].register('loskarlos')
    ac.blocks.register([5, 6, 7])


@ac.on_register(AC_ID)
def _on_register(ac: AC) -> None:
    logging.info(f'{ac.id}: registered')


@ac.on_resume(AC_ID)
@ac.on_start(AC_ID)
def _on_start(ac: AC) -> None:
    logging.info(f'{ac.id}: start')
    assert ac.state == State.RUNNING
    assert 'blokStav' in ac.pt_put('/blokStav/1', {'blokStav': {}})


@ac.on_stop(AC_ID)
def _on_stop(ac: AC) -> None:
    logging.info(f'{ac.id}: stop')
    assert ac.state == State.STOPPED


@ac.on_pause(AC_ID)
def _on_pause(ac: AC) -> None:
    logging.info(f'{ac.id}: pause')
    assert ac.state == State.PAUSED


@ac.blocks.on_block_change()
def _on_block_change(block: ac.Block) -> None:
    print(f'Changed: {block["nazev"]}')


@ac.blocks.on_block_change(1, 2)
def _on_block_change_(block: ac.Block) -> None:
    print(f'Changed 1|2: {block["nazev"]}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    ac.init(HOSTNAME, PORT)
