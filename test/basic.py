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


class MyAC(AC):
    def on_register(self) -> None:
        logging.info(f'{self.id}: registered')

    def on_start(self) -> None:
        logging.info(f'{self.id}: start')
        assert self.state == State.RUNNING
        assert 'blokStav' in self.pt_put('/blokStav/1', {'blokStav': {}})

    def on_stop(self) -> None:
        logging.info(f'{self.id}: stop')
        assert self.state == State.STOPPED

    def on_pause(self) -> None:
        logging.info(f'{self.id}: pause')
        assert self.state == State.PAUSED


@ac.blocks.on_block_change()
def _on_block_change(block: ac.Block) -> None:
    print(f'Changed: {block["nazev"]}')


@ac.blocks.on_block_change(1, 2)
def _on_block_change_(block: ac.Block) -> None:
    print(f'Changed 1|2: {block["nazev"]}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    ACs[AC_ID] = MyAC(AC_ID)
    ac.init(HOSTNAME, PORT)
