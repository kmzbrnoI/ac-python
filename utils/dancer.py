"""Library for executing user-defined dance."""

import logging
from typing import Any, Dict, Optional, Callable
import datetime

import ac
import ac.blocks
from ac import ACs, AC

JC = Dict[str, Any]


class Step:
    """Base class for all specific dance steps."""

    def update(self, acn: AC) -> None:
        pass


class StepJC(Step):
    """
    Process jc 'name'. If processed already, skip processing and continue.
    """
    name_to_id: Dict[str, JC] = {}

    def __init__(self, name: str, type_: str = 'VC') -> None:
        self.jc: Optional[JC] = None
        self.type = type_
        self.name = name

    def update(self, acn: AC) -> None:
        assert isinstance(acn, DanceAC)
        if self.jc is None:
            jcid = self.get_jc_id(self.name)  # TODO: check it exists on start
            self.jc = ac.pt.get(f'/jc/{jcid}?stav=true')['jc']

        if self.jc['staveni']['postaveno']:
            self.jc = None
            acn.step_done()
            return

        result = acn.pt_put(f'/jc/{self.jc["id"]}/stav', {})
        if result['success']:
            self.jc = None
            acn.step_done()

    def get_jc_id(self, name: str) -> int:
        if not StepJC.name_to_id:
            jcs = ac.pt.get('/jc')['jc']
            StepJC.name_to_id = {
                jc['nazev']: jc['id']
                for jc in jcs if jc['typ'] == self.type
            }
        return StepJC.name_to_id[name]


class StepDelay(Step):
    """Delay any time."""

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
    """Wait for specific state of any block. See examples below."""
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
            blocks = ac.pt.get('/bloky')['bloky']
            StepWaitForBlock.name_to_id = {
                block['nazev']: block['id'] for block in blocks
            }
        return StepWaitForBlock.name_to_id[name]


class DanceAC(AC):
    """This AC executes predefined steps."""

    def __init__(self, id_: str, password: str,
                 steps: Dict[int, Step]) -> None:
        AC.__init__(self, id_, password)
        self.steps = steps
        self.stepi = 0

    def on_start(self) -> None:
        logging.info('Start')
        self.statestr = ''
        self.stepi = 1
        self.on_update()

    def on_update(self) -> None:
        AC.on_update(self)
        if not self.running():
            return

        if self.stepi in self.steps:
            self.steps[self.stepi].update(self)
        else:
            logging.info('Done')
            self.done()

    def step_done(self) -> None:
        logging.info(f'Step {self.stepi} done, '
                     f'going to step {self.stepi+1}...')
        self.stepi += 1
        self.on_update()

    def on_block_change(self, block: ac.Block) -> None:
        if (self.running() and
                isinstance(self.steps[self.stepi], StepWaitForBlock)):
            self.steps[self.stepi].on_block_change(self, block)


@ac.blocks.on_block_change()
def _on_block_change(block: ac.Block) -> None:
    for acn in ACs.values():
        if isinstance(acn, DanceAC):
            acn.on_block_change(block)
