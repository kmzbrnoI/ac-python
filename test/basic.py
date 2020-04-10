#!/usr/bin/env python3

import logging
import ac

AC_ID = '5000'


@ac.on_connect
def on_connect():
    print('Connected')
    ac.register(AC_ID, 'loskarlos')


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    ac.init('192.168.0.168', 5896)


if __name__ == '__main__':
    main()
