"""
This file is a parser helper. It allows parsing data from server.
"""

from typing import List


def parse(data: str, separators: str) -> List[str]:
    """
    This function parses string into list of strings based on 'separators'.
    It follows hJOPserver`s PanelServer messages format.
    """
    output: List[str] = []
    item = ''
    escaped_level = 0

    for c in data:
        if c == '{':
            if escaped_level > 0:
                item += c
            escaped_level += 1

        elif (c == '}') and (escaped_level > 0):
            escaped_level -= 1
            if escaped_level > 0:
                item += c
        else:
            if (c in separators) and (escaped_level == 0):
                output.append(item)
                item = ''

            else:
                if (c not in separators) or (escaped_level > 0):
                    item += c

    if item != "":
        output.append(item)

    return output
