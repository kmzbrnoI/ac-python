#!/usr/bin/env python3

"""
Describe your project here

Usage:
  template.py [options] <block-id> <password>
  template.py --version

Options:
  -s <servername>    Specify hJOPserver address [default: localhost]
  -p <port>          Specify hJOPserver port [default: 5896]
  -l <loglevel>      Specify loglevel (python logging package) [default: info]
  -h --help          Show this screen.
  --version          Show version.
"""

import logging
from docopt import docopt

import ac
from ac import ACs, AC


class MySpecificAC(AC):
    def __init__(self, id_: str, password: str) -> None:
        AC.__init__(self, id_, password)

    def on_start(self) -> None:
        logging.info('Start')

    def on_resume(self) -> None:
        self.set_color(0xFFFF00)
        self.on_start()


if __name__ == '__main__':
    args = docopt(__doc__)

    loglevel = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL,
    }.get(args['-l'], logging.INFO)

    logging.basicConfig(level=loglevel)
    ACs[args['<block-id>']] = MySpecificAC(
        args['<block-id>'], args['<password>']
    )
    ac.init(args['-s'], int(args['-p']))
