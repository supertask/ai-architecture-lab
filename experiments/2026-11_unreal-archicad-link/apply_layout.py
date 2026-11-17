# -*- coding: utf-8 -*-
"""Step 3 — apply a checked layout to Archicad in ONE Tapir call (ModifyObjects for every moved piece).

usage:  uv run apply_layout.py my_layout.json [--rebuild] [--port N] [--room room.json] [--force]

- Refuses unless check_layout.py wrote my_layout.check.json with status PASS for exactly these pieces (use --force to skip).
- Before moving, it saves the live positions of the same pieces to undo/<time>.json (a normal layout file);
  `uv run apply_layout.py undo/<time>.json` puts them back.
- Unreal follows by itself when the Datasmith Direct Link / watcher is running (it watches the same objects).
Prints one JSON line: pieces, Tapir time, total time, max placement error read back from Archicad.
"""
import hashlib, json, math, os, sys, time
KIT = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, KIT)
from tapir import call, load_config, find_port


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main():
    t_start = time.time()
    cfg = load_config(arg('--config'))
    room = json.load(open(arg('--room', os.path.join(KIT, 'room.json')), encoding='utf-8'))
    path = [a for a in sys.argv[1:] if a.endswith('.json') and a not in (arg('--room'), arg('--config'))][0]
    L = json.load(open(path, encoding='utf-8'))
    pieces = L.get('pieces', {})
    is_undo = bool(L.get('undo'))
    if not is_undo and '--force' not in sys.argv:
        ck = os.path.splitext(path)[0] + '.check.json'
        sha = hashlib.sha256(json.dumps(pieces, sort_keys=True).encode()).hexdigest()
        c = json.load(open(ck, encoding='utf-8')) if os.path.exists(ck) else {}
        if c.get('status') != 'PASS' or c.get('pieces_sha256') != sha:
            sys.exit(f'not applied: run check_layout.py {os.path.basename(path)} until it prints PASS (or use --force)')
    port = find_port(cfg)
    by_id = {f['id']: f for f in room['furniture']}
    front = 90 if cfg.get('front_axis', '+y') == '+y' else 0
    ids = [k for k in pieces if k in by_id]
    # live positions -> undo file (same ids, layout format)
    live = call(port, 'GetDetailsOfElements', {'elements': [{'elementId': {'guid': by_id[k]['guid']}} for k in ids]})['detailsOfElements']
    undo = {'undo': True, 'title': 'undo of ' + os.path.basename(path), 'pieces': {}}
    for k, d in zip(ids, live):
        O = d['details']['origin']; a = d['details']['angle']; lc = by_id[k]['local_center']
        cx = O['x'] + math.cos(a) * lc[0] - math.sin(a) * lc[1]; cy = O['y'] + math.sin(a) * lc[0] + math.cos(a) * lc[1]
        undo['pieces'][k] = [round(cx, 4), round(cy, 4), round((math.degrees(a) + front + 180) % 360 - 180, 3)]
    os.makedirs(os.path.join(KIT, 'undo'), exist_ok=True)
    up = os.path.join(KIT, 'undo', time.strftime('%Y%m%d-%H%M%S') + '.json')
    if not is_undo:
        json.dump(undo, open(up, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    # target origins
    objs = []; want = {}
    for k in ids:
        cx, cy, fdeg = pieces[k]; f = by_id[k]; lc = f['local_center']
        a = math.radians(fdeg - front)
        ox = cx - (math.cos(a) * lc[0] - math.sin(a) * lc[1]); oy = cy - (math.sin(a) * lc[0] + math.cos(a) * lc[1])
        objs.append({'elementId': {'guid': f['guid']}, 'coordinates': {'x': ox, 'y': oy, 'z': f['z_origin']}, 'angle': a})
        want[f['guid']] = (ox, oy, a)
    t0 = time.time()
    res = call(port, 'ModifyObjects', {'objectsWithDetails': objs})
    t1 = time.time()
    if '--rebuild' in sys.argv:
        call(port, 'RebuildView', {'regenerate': True})
    t2 = time.time()
    back = call(port, 'GetDetailsOfElements', {'elements': [{'elementId': o['elementId']} for o in objs]})['detailsOfElements']
    err = 0.0
    for o, d in zip(objs, back):
        w = want[o['elementId']['guid']]; O = d['details']['origin']
        err = max(err, math.hypot(O['x'] - w[0], O['y'] - w[1]))
    bad = [r for r in (res.get('executionResults') or []) if not r.get('success', True)]
    out = {'layout': os.path.basename(path), 'pieces': len(objs), 'failed': len(bad), 'tapir_modify_s': round(t1 - t0, 3),
           'rebuild_s': round(t2 - t1, 3) if '--rebuild' in sys.argv else None, 'total_s': round(time.time() - t_start, 3),
           'max_error_mm': round(err * 1000, 1), 'undo': None if is_undo else os.path.relpath(up, KIT),
           'since_read_room_s': round(time.time() - room['read_epoch'], 1) if room.get('read_epoch') else None}
    print(json.dumps(out, ensure_ascii=False))
    os.makedirs(os.path.join(KIT, 'logs'), exist_ok=True)
    open(os.path.join(KIT, 'logs', 'apply.jsonl'), 'a', encoding='utf-8').write(json.dumps({**out, 't': time.time()}, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
