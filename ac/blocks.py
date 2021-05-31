"""Panel server block interaction (on_change)"""

from typing import Dict, Any, Callable, List, Iterable, Union, Set, Tuple
from collections import defaultdict
import logging

from . import panel_client
from . import pt


Block = Dict[str, Any]
BlockEvent = Callable[[Block], None]
BlockDecorator = Callable[[BlockEvent], BlockEvent]
events: Dict[str, Set[BlockEvent]] = defaultdict(set)
global_events: Set[BlockEvent] = set()


def on_block_change(*args: Union[int, str],
                    **kwargs: Dict[str, Any]) -> BlockDecorator:
    """
    Decorate any function to receive changes of (specific) block(s).

    Examples:
     * @ac.blocks.on_block_change(id1, id2, ..., idn)  # Specific blocks
       def my_event(self, block: Block):
     * @ac.blocks.on_block_change()  # All blocks
       def my_event(self, block: Block):

    Warning: this decorator DOES NOT register events to server.
    You must manually call register to `register` events on server
    (atfer you have PanelServer connection and usually after you AC has
    started).
    """
    def decorate(function: BlockEvent) -> BlockEvent:
        global events
        global global_events

        for block_id in args:
            events[str(block_id)].add(function)
        if not args:
            global_events.add(function)

        return function

    return decorate


def register_change(func: BlockEvent, *args: Union[int, str],
                    **kwargs: Tuple[str, Any]) -> None:
    """
    Register change event to function & server.

    Do not call `register` when using this function.

    Example:
    def on_start(self):
        ac.blocks.register_change(self.on_block_change, 12, 24)
    """
    global events, global_events

    for block_id in args:
        if func not in events[str(block_id)]:
            events[str(block_id)].add(func)
    register(args)
    if not args:
        if func not in global_events:
            global_events.add(func)


def unregister_change(func: BlockEvent, *args: Union[int, str],
                      **kwargs: Tuple[str, Any]) -> None:

    """Unregister change event to function & server."""
    global events, global_events

    for block_id in args:
        if func in events[str(block_id)]:
            events[str(block_id)].remove(func)
    unregister(args)
    if not args:
        if func in global_events:
            global_events.remove(func)


def register(blocks: Iterable[Union[str, int]]) -> None:
    """
    Register event on server.

    This function should be called when using event handing via decorators.
    """
    _send('register', blocks)


def unregister(blocks: Iterable[Union[str, int]]) -> None:
    _send('unregister', blocks)


def _send(command: str, blocks: Iterable[Union[str, int]]) -> None:
    _blocks = map(str, blocks)
    panel_client.send('-;AC;-;BLOCKS;' + command.upper() +
                      ';{' + (','.join(_blocks))+'}')


def _send_all_registrations() -> None:
    global events

    all_ = set(list(events.keys()))
    if all_:
        register(all_)


def on_message(parsed: List[str]) -> None:
    assert len(parsed) >= 5
    parsed[4] = parsed[4].upper()

    if parsed[4] == 'REGISTER':
        assert len(parsed) >= 7
        if parsed[6].upper() == 'ERR':
            message = f': {parsed[7]}' if len(parsed) >= 8 else ''
            logging.error(f'Block {parsed[5]} register error: {message}')
    elif parsed[4] == 'CHANGE':
        _call_change(parsed[5])
    elif parsed[4] == 'LIST':
        pass  # TODO if needed


def _call_change(id_: str) -> None:
    pt_block = pt.get(f'/blocks/{id_}?state=true')['block']
    for event in global_events:
        event(pt_block)
    for event in events[id_]:
        event(pt_block)


def dict(state: bool = False) -> Dict[str, Block]:
    url = '/blocks'
    if state:
        url += '?state=true'
    return {
        int(block['id']): block
        for block in pt.get(url)['blocks']
    }
