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
from typing import Any, Dict, Optional, Callable
import datetime

import ac
import ac.blocks
from ac import ACs, AC

JC = Dict[str, Any]


class DanceAC(AC):
    """This AC executes predefined steps."""

    def __init__(self, id_: str, password: str) -> None:
        AC.__init__(self, id_, password)
        self.step = 0

    def on_start(self) -> None:
        logging.info('Start')
        self.statestr = ''
        self.step = 1

    def on_resume(self) -> None:
        self.set_color(0xFFFF00)
        self.on_start()

    def on_update(self) -> None:
        if not self.running():
            return

        if self.step in STEPS:
            STEPS[self.step].update(self)
        else:
            logging.info('Done')
            self.done()

    def step_done(self) -> None:
        logging.info(f'Step {self.step} done, going to step {self.step+1}...')
        self.step += 1
        self.on_update()

    def on_block_change(self, block: ac.Block) -> None:
        if self.running() and isinstance(STEPS[self.step], StepWaitForBlock):
            STEPS[self.step].on_block_change(self, block)


class Step:
    def update(self, acn: AC) -> None:
        pass


class StepJC(Step):
    name_to_jc: Dict[str, JC] = {}

    def __init__(self, name: str, type_: str = 'VC') -> None:
        self.jc: Optional[JC] = None
        self.type = type_
        self.name = name

    def update(self, acn: AC) -> None:
        assert isinstance(acn, DanceAC)
        if self.jc is None:
            self.jc = self.get_jc(self.name)  # TODO: check it exists on start

        if self.jc['staveni']['postaveno']:
            acn.step_done()
            return

        result = acn.pt_put(f'/jc/{self.jc["id"]}/stav', {})
        if result['success']:
            self.jc['staveni']['postaveno'] = True
            acn.step_done()

    def get_jc(self, name: str) -> JC:
        if not StepJC.name_to_jc:
            jcs = ac.pt.get('/jc?stav=true')['jc']
            StepJC.name_to_jc = {
                jc['nazev']: jc
                for jc in jcs if jc['typ'] == self.type
            }
        return StepJC.name_to_jc[name]


class StepDelay(Step):
    def __init__(self, delay: datetime.timedelta) -> None:
        self.delay = delay
        self.finish: Optional[datetime.datetime] = None

    def update(self, acn: AC) -> None:
        assert isinstance(acn, DanceAC)
        if self.finish is None:
            self.finish = datetime.datetime.now() + self.delay
        if datetime.datetime.now() > self.finish:
            self.finish = None
            acn.step_done()


class StepWaitForBlock(Step):
    name_to_id: Dict[str, int] = {}

    def __init__(self, name: str, checker: Callable[[ac.Block], bool]) -> None:
        self.name = name
        self.checker = checker
        self.block: Optional[ac.Block] = None

    def update(self, acn: AC) -> None:
        assert isinstance(acn, DanceAC)
        if self.block is None:
            blockid = self.get_block_id(self.name)
            self.block = ac.pt.get(f'/bloky/{blockid}?stav=true')['blok']
            if self.checker(self.block):
                self.block = None
                acn.step_done()
            else:
                ac.blocks.register([self.block['id']])

    def on_block_change(self, acn: AC, block: ac.Block) -> None:
        assert isinstance(acn, DanceAC)
        if self.block is None or block['id'] != self.block['id']:
            return
        if self.checker(block):
            ac.blocks.unregister([self.block['id']])
            self.block = None
            acn.step_done()

    def get_block_id(self, name: str) -> int:
        if not StepWaitForBlock.name_to_id:
            blocks = ac.pt.get('/bloky?stav=true')['bloky']
            StepWaitForBlock.name_to_id = {
                block['nazev']: block['id'] for block in blocks
            }
        return StepWaitForBlock.name_to_id[name]


STEPS: Dict[int, Step] = {
    1: StepJC('Klb S1 > Klb PriblL'),
    2: StepWaitForBlock('Klb K1',
                        lambda block: block['blokStav']['stav'] == 'obsazeno'),
    3: StepDelay(datetime.timedelta(seconds=5)),
}


@ac.blocks.on_block_change()
def _on_block_change(block: ac.Block) -> None:
    for acn in ACs.values():
        if isinstance(acn, DanceAC):
            acn.on_block_change(block)


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
        args['<block-id>'], args['<password>']
    )
    ac.init(args['-s'], int(args['-p']))
