# -*- coding: utf-8 -*-
"""Minimal client for the Archicad JSON API + Tapir add-on (stdlib only).

call(port, 'TapirCommand', params)  -> Tapir add-on command (e.g. GetDetailsOfElements, ModifyObjects)
api(port, 'API.Command', params)     -> Archicad built-in command (e.g. API.Get3DBoundingBoxes)
find_port(cfg)                       -> port from --port / env ARCHICAD_PORT / config, else scans 19723-19743
"""
import json, os, sys, urllib.request

KIT = os.path.dirname(os.path.abspath(__file__))


def _post(port, body, timeout=60):
    req = urllib.request.Request(f'http://127.0.0.1:{port}', json.dumps(body).encode('utf-8'), {'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def call(port, cmd, params=None, timeout=60):
    r = _post(port, {'command': 'API.ExecuteAddOnCommand',
                     'parameters': {'addOnCommandId': {'commandNamespace': 'TapirCommand', 'commandName': cmd},
                                    'addOnCommandParameters': params or {}}}, timeout)
    if not r.get('succeeded'):
        raise RuntimeError(r)
    res = r['result']['addOnCommandResponse']
    if isinstance(res, dict) and res.get('error'):
        raise RuntimeError(res)
    return res


def api(port, cmd, params=None, timeout=60):
    body = {'command': cmd}
    if params is not None:
        body['parameters'] = params
    r = _post(port, body, timeout)
    if not r.get('succeeded'):
        raise RuntimeError(r)
    return r.get('result')


def load_config(path=None):
    path = path or os.path.join(KIT, 'config.json')
    return json.load(open(path, encoding='utf-8'))


def alive(port):
    try:
        return bool(_post(port, {'command': 'API.IsAlive'}, 2).get('result', {}).get('isAlive'))
    except Exception:
        return False


def find_port(cfg, argv=None):
    argv = argv if argv is not None else sys.argv
    if '--port' in argv:
        return int(argv[argv.index('--port') + 1])
    if os.environ.get('ARCHICAD_PORT'):
        return int(os.environ['ARCHICAD_PORT'])
    p = cfg.get('archicad_port')
    if p and alive(p):
        return int(p)
    found = [q for q in range(19723, 19744) if alive(q)]
    if len(found) == 1:
        return found[0]
    if not found:
        sys.exit('Archicad not found on ports 19723-19743 (is Archicad open with the Tapir add-on?)')
    sys.exit(f'several Archicad instances {found}: pass --port N (or set archicad_port in config.json)')
