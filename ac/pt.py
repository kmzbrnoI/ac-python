"""
Utils for interaction with PT server. These functions should not be used by
user. User should interact through instance of AC.
"""

import urllib.request
import json
from typing import Dict, Any
import base64
import logging

server = ''
PORT = 5823


def _send(path: str, method: str, req_data: Dict[str, Any],
          user: str = '', password: str = '') -> Dict[str, Any]:
    if not path.startswith('/'):
        path = '/' + path

    base64string = base64.b64encode(('%s:%s' % (user, password)).
                                    encode('utf-8')).decode('utf-8')
    req = urllib.request.Request(
        f'http://{server}:{PORT}{path}',
        headers={
            'Authorization': f'Basic {base64string}',
            'Content-type': 'application/json',
        },
        method=method,
        data=json.dumps(req_data).encode('utf-8'),
    )
    with urllib.request.urlopen(req) as response:
        data = response.read().decode('utf-8')
    return json.loads(data)  # type: ignore


def get(path: str) -> Dict[str, Any]:
    logging.debug(f'PT GET {path}')
    return _send(path, 'GET', {})


def put(path: str, req_data: Dict[str, Any], username: str,
        password: str) -> Dict[str, Any]:
    logging.debug(f'PT PUT {path}')
    return _send(path, 'PUT', req_data, username, password)
