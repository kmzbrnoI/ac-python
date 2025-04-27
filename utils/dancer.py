"""Library for executing a user-defined predefined steps ("dance")."""

import logging
from typing import Any, Dict, Optional, Callable
import datetime

import ac
import ac.blocks
from ac import ACs, AC

JC = Dict[str, Any]


class DanceStartException(Exception):
    pass


class Step:
    """Base class for all specific dance steps."""

    def update(self, acn: AC) -> None:
        pass

    def on_start(self, acn: AC) -> None:
        pass

    def disp_str(self) -> str:
        return ''


class JCNotFoundException(DanceStartException):
    pass


class StepJC(Step):
    """
    Process jc 'name'. If processed already, skip processing and continue.
    """
    name_to_id: Dict[str, int] = {}

    def __init__(self, name: str, type_: str = 'VC') -> None:
        self.jc: Optional[JC] = None
        self.type = type_
        self.name = name

    def update(self, acn: AC) -> None:
        assert isinstance(acn, DanceAC)
        if self.jc is None:
            jcid = self.get_jc_id(self.name, acn)
            self.jc = acn.pt_get(f'/jc/{jcid}?state=true')['jc']

        if self.jc['state']['active']:
            self.jc = None
            acn.step_done()
            return

        result = acn.pt_put(f'/jc/{self.jc["id"]}/state', {})
        if result['success']:
            self.jc = None
            acn.step_done()

    def on_start(self, acn: AC) -> None:
        self.get_jc_id(self.name, acn)

    def get_jc_id(self, name: str, acn: AC) -> int:
        if not StepJC.name_to_id:
            jcs = acn.pt_get('/jc')['jc']
            StepJC.name_to_id = {
                jc['name']: jc['id']
                for jc in jcs if jc['type'] == self.type
            }
        if name not in StepJC.name_to_id.keys():
            raise JCNotFoundException(f'Jízdní cesta {self.name} neexistuje!')
        return StepJC.name_to_id[name]

    def disp_str(self) -> str:
        return f'Stavění JC {self.name}'


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

    def disp_str(self) -> str:
        return f'Čekání {self.delay}'


class BlockNotFoundException(DanceStartException):
    pass


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
            blockid = self.get_block_id(self.name, acn)
            self.block = acn.pt_get(f'/blocks/{blockid}?state=true')['block']
            if self.checker(self.block):
                self.block = None
                acn.step_done()
            else:
                ac.blocks.register([self.block['id']])

    def on_start(self, acn: AC) -> None:
        self.get_block_id(self.name, acn)

    def on_block_change(self, acn: AC, block: ac.Block) -> None:
        assert isinstance(acn, DanceAC)
        if self.block is None or block['id'] != self.block['id']:
            return
        if self.checker(block):
            ac.blocks.unregister([self.block['id']])
            self.block = None
            acn.step_done()

    def get_block_id(self, name: str, acn: AC) -> int:
        if not StepWaitForBlock.name_to_id:
            blocks = acn.pt_get('/blocks')['blocks']
            StepWaitForBlock.name_to_id = {
                block['name']: block['id'] for block in blocks
            }
        if name not in StepWaitForBlock.name_to_id.keys():
            raise BlockNotFoundException(f"Blok {self.name} neexistuje!")
        return StepWaitForBlock.name_to_id[name]

    def disp_str(self) -> str:
        return f'Čekání na stav bloku {self.name}'


def track_is_occupied(block: ac.Block) -> bool:
    return bool(block['blockState']['state'] == 'occupied')


class DanceAC(AC):
    """This AC executes predefined steps."""

    def __init__(self, id_: str, password: str,
                 steps: Dict[int, Step]) -> None:
        AC.__init__(self, id_, password)
        self.steps = steps
        self.stepi = 0

    def on_start(self) -> None:
        logging.info('Start')

        for stepi, step in self.steps.items():
            try:
                step.on_start(self)
            except DanceStartException as e:
                self.disp_error(f'Krok {stepi}: '+str(e))
                self.done()
                return

        self.stepi = 1
        self.send_step()
        self.on_update()

    def on_stop(self) -> None:
        self.statestr = ''
        self.statestr_send()

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
        self.send_step()
        self.on_update()

    def send_step(self) -> None:
        if self.stepi in self.steps.keys():
            if self.running():
                description = self.steps[self.stepi].disp_str()
                self.statestr = f'Aktuální krok: {self.stepi}: {description}'
            self.statestr_send()

    def on_block_change(self, block: ac.Block) -> None:
        if (self.running() and
                isinstance(self.steps[self.stepi], StepWaitForBlock)):
            self.steps[self.stepi].on_block_change(self, block)  # type: ignore


@ac.blocks.on_block_change()
def _on_block_change(block: ac.Block) -> None:
    for acn in ACs.values():
        if isinstance(acn, DanceAC):
            acn.on_block_change(block)
