#!/usr/bin/env python3

import logging
import ac
import ac.blocks
from ac import ACs, AC, State

AC_ID = '5000'


@ac.on_connect
def on_connect():
    logging.info('connected')
    ACs[AC_ID].register('loskarlos')
    ac.blocks.register([5, 6, 7])


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


@ac.blocks.on_block_change()
def on_block_change(block: ac.Block) -> None:
    print(f'Changed: {block}')


@ac.blocks.on_block_change(1, 2)
def on_block_change(block: ac.Block) -> None:
    print(f'Changed 1|2: {block}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    ac.init('192.168.0.168', 5896)
