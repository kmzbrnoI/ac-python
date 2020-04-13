"""Blocks cache helper"""

from typing import Dict, Any

import ac
import ac.blocks


Block = Dict[str, Any]
blocks_state: Dict[int, Block] = {}


def state(id_: int) -> Dict[str, Any]:
    if id_ not in blocks_state:
        blocks_state[id_] = ac.pt.get(f'/blokStav/{id_}')['blokStav']
    return blocks_state[id_]


@ac.blocks.on_block_change()
def _on_block_change(block: ac.Block) -> None:
    blocks_state[block['id']] = block['blokStav']
