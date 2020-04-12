#!/usr/bin/env python3

"""
Automatically process predefined JCs.
Note: this scipt is quite ugly, it uses many global variables etc.
"""

import logging
import ac
import ac.blocks
from ac import ACs, AC
from typing import Any, Dict, List, Union

HOSTNAME = '192.168.0.168'
PORT = 5896
AC_ID = '5000'

JC = Dict[str, Any]

JC_IDS: List[int] = [104, 105]
jc_ids_remaining: List[str] = []
jcs: Dict[str, JC] = {}
_blocks_state: Dict[str, Dict[str, Any]] = {}


def blocks_state(ac: AC, id_: Union[str, int]) -> Dict[str, Any]:
    global _blocks_state
    if id_ not in _blocks_state:
        _blocks_state[str(id_)] = ac.pt_get(f'/blokStav/{id_}')['blokStav']
    return _blocks_state[str(id_)]


def get_jcs(ac: AC) -> None:
    global jcs
    for jc_id in jc_ids_remaining:
        jcs[jc_id] = ac.pt_get(f'/jc/{jc_id}?stav=true')['jc']


def filter_done_jcs() -> None:
    global jc_ids_remaining
    remaining = []
    for jc_id in jc_ids_remaining:
        if not jcs[jc_id]['staveni']['postaveno']:
            remaining.append(jc_id)
    jc_ids_remaining = remaining


def process_free_jcs(ac: AC) -> None:
    free = free_jcs(ac)
    process_jcs(ac, free)

    if not jc_ids_remaining:
        ac.done()
        logging.info(f'All JCs processed.')


def free_jcs(ac: AC) -> List[JC]:
    result = []
    for jc_id in jc_ids_remaining:
        jc = jcs[jc_id]
        free = all([blocks_state(ac, track_id)['stav'] == 'uvolneno'
                    for track_id in jc['useky']])
        if free:
            result.append(jc)

    return result


def process_jcs(ac_: AC, jcs: List[JC]) -> None:
    global js_ids_remaining

    for jc in jcs:
        logging.info(f'Processing JC {jc["nazev"]}...')
        result = ac_.pt_put(f'/jc/{jc["id"]}/stav', {'ab': True})
        if result['success']:
            logging.info('ok')
            ac.blocks.unregister(jc['useky'])
        else:
            ac_.disp_error(f'Nelze postavit JC {jc["nazev"]}')
            logging.error(f'Unable to process JC {jc["nazev"]}: ' +
                          str(result['bariery']))
        jc_ids_remaining.remove(str(jc['id']))


def register_jc_tracks_change(ac_: AC) -> None:
    for jc_id in jc_ids_remaining:
        jc = jcs[jc_id]
        ac.blocks.register(jc['useky'])


@ac.on_connect
def _on_connect() -> None:
    ACs[AC_ID].register('loskarlos')


@ac.on_resume(AC_ID)
@ac.on_start(AC_ID)
def _on_start(ac: AC) -> None:
    global jc_ids_remaining

    logging.info('Start')
    jc_ids_remaining = list(map(str, JC_IDS))

    get_jcs(ac)
    filter_done_jcs()
    process_free_jcs(ac)
    register_jc_tracks_change(ac)


@ac.blocks.on_block_change()
def _on_block_change(block: ac.Block) -> None:
    global _blocks_state
    _blocks_state[str(block['id'])] = block['blokStav']
    process_free_jcs(ACs[AC_ID])


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    ac.init(HOSTNAME, PORT)
