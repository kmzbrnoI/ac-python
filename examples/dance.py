#!/usr/bin/env python3

"""
Automatically process predefined JCs.

Usage:
  dance.py [options] <block-id> <password>
  dance.py --version

Options:
  -s <servername>    Specify hJOPserver address [default: localhost]
  -p <port>          Specify hJOPserver port [default: 5896]
  -l <loglevel>      Specify loglevel (python logging package) [default: info]
  -h --help          Show this screen.
  --version          Show version.
"""

import logging
from docopt import docopt
from typing import Dict
import datetime

import ac
from ac import ACs
from utils.dancer import Step, StepJC, StepWaitForBlock, StepDelay, DanceAC

STEPS: Dict[int, Step] = {
    1: StepJC('Klb S1 > Klb PriblL'),
    2: StepWaitForBlock('Klb K1',
                        lambda block: block['blokStav']['stav'] == 'obsazeno'),
    3: StepDelay(datetime.timedelta(seconds=5)),
}


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
    ACs[args['<block-id>']] = DanceAC(
        args['<block-id>'], args['<password>'], STEPS
    )
    ac.init(args['-s'], int(args['-p']))
