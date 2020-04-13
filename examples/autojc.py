#!/usr/bin/env python3

"""
Automatically process predefined JCs.

Usage:
  autojc.py [options] <block-id> <password> JCS ...
  autojc.py --version

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
import ac.blocks
from ac import ACs, AC
from typing import Any, Dict, List

JC = Dict[str, Any]
Block = Dict[str, Any]


class JCAC(AC):
    """
    This AC is supposed to process entered JCs as soon as all their tracks
    are free.
    """

    def __init__(self, id_: str, password: str, to_process: List[int]) -> None:
        AC.__init__(self, id_)
        self.password = password
        self.to_process = to_process
        self.jcs_remaining: Dict[int, JC] = {}

    def on_start(self) -> None:
        logging.info('Start')
        self.jcs_remaining = jcs(self.to_process)
        self.statestr = ''

        self.filter_done_jcs()
        self.process_free_jcs()

        for jc in self.jcs_remaining.values():
            ac.blocks.register(jc['useky'])

    def on_resume(self) -> None:
        self.set_color(0xFFFF00)
        self.on_start()

    def filter_done_jcs(self) -> None:
        remaining = {}
        for jc in self.jcs_remaining.values():
            if not jc['staveni']['postaveno']:
                remaining[jc['id']] = jc
            else:
                self.statestr_add(f'JC {jc["nazev"]} již postavena, nestavím.')
        self.statestr_send()
        self.jcs_remaining = remaining

    def process_free_jcs(self) -> None:
        self.process_jcs(free_jcs(list(self.jcs_remaining.values())))

        if not self.jcs_remaining:
            self.done()
            logging.info(f'All JCs processed.')

    def process_jcs(self, jcs: List[JC]) -> None:
        for jc in jcs:
            logging.info(f'Processing JC {jc["nazev"]}...')
            result = self.pt_put(f'/jc/{jc["id"]}/stav', {'ab': True})
            if result['success']:
                self.statestr_add(f'Postavena JC {jc["nazev"]}.')
                logging.info('ok')
                ac.blocks.unregister(jc['useky'])
            else:
                self.statestr_add(f'Nelze postavit JC {jc["nazev"]}.')
                self.disp_error(f'Nelze postavit JC {jc["nazev"]}')
                logging.error(f'Unable to process JC {jc["nazev"]}: ' +
                              str(result['bariery']))
                self.set_color(0xFF0000)

            del self.jcs_remaining[jc['id']]
            self.statestr_send()


def jcs(ids: List[int]) -> Dict[int, JC]:
    return {jc_id: ac.pt.get(f'/jc/{jc_id}?stav=true')['jc'] for jc_id in ids}


def free_jcs(jcs: List[JC]) -> List[JC]:
    result = []
    for jc in jcs:
        free = all([blocks_state(track_id)['stav'] == 'uvolneno'
                    for track_id in jc['useky']])
        if free:
            result.append(jc)

    return result


@ac.on_connect
def _on_connect() -> None:
    for ac_ in ACs.values():
        ac_.register(ac.password)


def blocks_state(id_: int) -> Dict[int, Any]:
    if id_ not in blocks_state.state:
        blocks_state.state[id_] = ac.pt.get(f'/blokStav/{id_}')['blokStav']
    return blocks_state.state[id_]


blocks_state.state: Dict[str, Block] = {}


@ac.blocks.on_block_change()
def _on_block_change(block: ac.Block) -> None:
    blocks_state.state[block['id']] = block['blokStav']

    for ac_ in ACs.values():
        if isinstance(ac_, JCAC):
            ac_.process_free_jcs()


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
    jcs_ = map(int, args['JCS'])
    ACs[args['<block-id>']] = JCAC(
        args['<block-id>'], args['<password>'], jcs_
    )
    ac.init(args['-s'], int(args['-p']))
