"""Minimal client for Archicad JSON API + Tapir add-on commands (read/write on a given port)."""
import json, urllib.request
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
