"""Minimal client for Archicad JSON API + Tapir add-on commands (read/write on a given port).

default_port(): env ARCHICAD_PORT -> archicad_port.txt (written by check_connection.py --scan; looked up
next to this file and in <kit>/work/) -> 19723.
"""
import json, os, urllib.request


def default_port():
    if os.environ.get('ARCHICAD_PORT'):
        return int(os.environ['ARCHICAD_PORT'])
    here = os.path.dirname(os.path.abspath(__file__))
    for p in (os.path.join(here, 'archicad_port.txt'), os.path.join(os.path.dirname(here), 'work', 'archicad_port.txt')):
        if os.path.exists(p):
            try:
                return int(open(p, encoding='utf-8').read().strip())
            except ValueError:
                pass
    return 19723


def call(port, cmd, params=None, timeout=120):
    body = {"command": "API.ExecuteAddOnCommand",
            "parameters": {"addOnCommandId": {"commandNamespace": "TapirCommand", "commandName": cmd},
                           "addOnCommandParameters": params or {}}}
    req = urllib.request.Request(f"http://127.0.0.1:{port}", json.dumps(body).encode("utf-8"),
                                 {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    if not r.get("succeeded"):
        raise RuntimeError(r)
    res = r["result"]["addOnCommandResponse"]
    if isinstance(res, dict) and res.get("error"):
        raise RuntimeError(res)
    return res


def api(port, cmd, params=None, timeout=120):
    body = {"command": cmd}
    if params is not None: body["parameters"] = params
    req = urllib.request.Request(f"http://127.0.0.1:{port}", json.dumps(body).encode("utf-8"),
                                 {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=timeout))
