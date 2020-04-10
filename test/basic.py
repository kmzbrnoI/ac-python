#!/usr/bin/env python3

import logging
import ac
from ac import ACs

AC_ID = '5000'


@ac.on_connect
def on_connect():
    print('Connected')
    ACs[AC_ID].register('loskarlos')


@ac.on_register(AC_ID)
def on_register(id_: str):
    print(f'Registered {id_}')


@ac.on_start(AC_ID)
def on_start(id_: str):
    print(f'Start {id_}')


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    ac.init('192.168.0.168', 5896)


if __name__ == '__main__':
    main()
