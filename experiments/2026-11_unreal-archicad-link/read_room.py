# -*- coding: utf-8 -*-
"""Step 1 — read the room from Archicad (Tapir) and write room.json.

usage:  uv run read_room.py [--port N] [--config config.json] [--out room.json]

What it reads (all live from the open Archicad project):
  - the room outline: the Zone named config.room_zone_name (polygon, story, floor level)
  - walls, windows, doors on that story near the outline (3D bounding boxes, sill/head heights)
  - keep-out areas: zones whose name matches config.keep_out_zone_names (stairs, voids) + config.keep_out
  - fixtures that are not modelled (config.fixtures, e.g. an assumed kitchen counter)
  - entries: parts of the outline with no wall (auto) or config.entries
  - every Object inside the room: GUID, library part, kind, size, centre, facing, height
Coordinates are metres in the project plan. facing: 0 = +x (east), 90 = +y (north) = the side people use.
"""
import json, math, os, sys, time
KIT = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, KIT)
from tapir import call, api, load_config, find_port

ID_PREFIX = {'sofa': 'sofa', 'lounge_chair': 'lounge', 'coffee_table': 'coffee', 'side_table': 'side', 'rug': 'rug', 'pouf': 'pouf',
             'tv_unit': 'tvunit', 'tv': 'tv', 'shelf': 'shelf', 'dining_table': 'dtable', 'dining_chair': 'dchair', 'bench': 'bench',
             'plant': 'plant', 'floor_lamp': 'lamp', 'stool': 'stool', 'other': 'obj'}


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


# ---------------------------------------------------------------- small 2D helpers (stdlib only)
def pip(p, poly):
    x, y = p; inside = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def seg_dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def poly_dist(p, poly):
    return min(seg_dist(p, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def box_dist(p, b):
    dx = max(b[0] - p[0], 0, p[0] - b[2]); dy = max(b[1] - p[1], 0, p[1] - b[3])
    return math.hypot(dx, dy)


def clean(poly):
    out = []
    for p in poly:
        p = (round(p[0], 4), round(p[1], 4))
        if not out or math.dist(out[-1], p) > 1e-4:
            out.append(p)
    if len(out) > 1 and math.dist(out[0], out[-1]) < 1e-4:
        out.pop()
    return out


def boundary_samples(poly, step=0.05):
    """points along the outline with inward unit normal"""
    area = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly))) / 2
    ccw = area > 0
    out = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        L = math.dist(a, b)
        if L < 1e-6: continue
        tx, ty = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        n = (-ty, tx) if ccw else (ty, -tx)
        k = max(1, int(L / step))
        for j in range(k):
            t = (j + 0.5) / k
            out.append({'p': (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])), 'n': n, 'edge': i, 'len': L / k})
    return out


def kind_of(lib, guid, A, cfg):
    if guid in cfg.get('kind_by_guid', {}):
        return cfg['kind_by_guid'][guid]
    for rule in cfg['kinds']:
        key, kind = rule[0], rule[1]
        if key.lower() in lib.lower():
            if len(rule) > 2 and 'min_width' in rule[2] and A < rule[2]['min_width']:
                return rule[2]['else']
            return kind
    return 'other'


def main():
    t0 = time.time()
    cfg = load_config(arg('--config'))
    port = find_port(cfg)
    out_path = arg('--out', os.path.join(KIT, 'room.json'))
    els = lambda t: call(port, 'GetElementsByType', {'elementType': t})['elements']
    det = lambda e: call(port, 'GetDetailsOfElements', {'elements': e})['detailsOfElements'] if e else []
    bbs = lambda e: api(port, 'API.Get3DBoundingBoxes', {'elements': e})['boundingBoxes3D'] if e else []
    stories = call(port, 'GetStories', {})['stories']

    # ---- room zone
    zones = els('Zone'); zd = det(zones)
    room = None; keep = []
    for e, d in zip(zones, zd):
        nm = d['details'].get('name', '')
        if nm == cfg['room_zone_name'] and room is None:
            room = {'guid': e['elementId']['guid'], 'name': nm, 'floorIndex': d['floorIndex'],
                    'polygon': clean([(p['x'], p['y']) for p in d['details']['polygonOutline']])}
    if not room:
        sys.exit(f"zone '{cfg['room_zone_name']}' not found — set room_zone_name in config.json")
    fi = room['floorIndex']
    story = next(s for s in stories if s['index'] == fi)
    floor_z = story['level']; top_z = floor_z + story['height']
    poly = room['polygon']
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    rbb = (min(xs), min(ys), max(xs), max(ys))
    for e, d in zip(zones, zd):
        nm = d['details'].get('name', '')
        if d['floorIndex'] == fi and any(k.lower() in nm.lower() for k in cfg.get('keep_out_zone_names', [])):
            zp = clean([(p['x'], p['y']) for p in d['details']['polygonOutline']])
            if min(poly_dist(q, poly) for q in zp) < 0.3 or any(pip(q, poly) for q in zp):
                keep.append({'name': nm, 'polygon': zp, 'source': 'zone'})
    for k in cfg.get('keep_out', []):
        x0, y0, x1, y1 = k['rect']
        keep.append({'name': k['name'], 'polygon': [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 'source': 'config', 'reach': bool(k.get('reach'))})

    near = lambda b: b['xMax'] > rbb[0] - 0.5 and b['xMin'] < rbb[2] + 0.5 and b['yMax'] > rbb[1] - 0.5 and b['yMin'] < rbb[3] + 0.5 \
        and b['zMax'] > floor_z + 0.05 and b['zMin'] < top_z - 0.05

    # ---- walls / windows / doors
    S = boundary_samples(poly)
    walls, openings = [], []
    for t in ('Wall', 'Window', 'Door'):
        e = els(t)
        if not e: continue
        dd = det(e); bb = bbs(e)
        for ei, d, b in zip(e, dd, bb):
            b = b.get('boundingBox3D')
            if not b or not near(b): continue
            box = [round(b['xMin'], 3), round(b['yMin'], 3), round(b['xMax'], 3), round(b['yMax'], 3)]
            if t == 'Wall':
                walls.append({'guid': ei['elementId']['guid'], 'bb': box, 'z': [round(b['zMin'] - floor_z, 2), round(b['zMax'] - floor_z, 2)]})
            else:
                if not any(box_dist(s['p'], box) < 0.06 for s in S):
                    continue
                openings.append({'type': t.lower(), 'guid': ei['elementId']['guid'], 'lib': d['details'].get('libPart', {}).get('name'),
                                 'bb': box, 'sill_m': round(b['zMin'] - floor_z, 2), 'head_m': round(b['zMax'] - floor_z, 2)})

    # ---- outline classification (wall / open / keep-out) -> openings spans, door clear zones, entries
    for s in S:
        p = s['p']
        s['wall'] = any(box_dist(p, w['bb']) < 0.13 and w['z'][0] < 0.3 and w['z'][1] > 2.0 for w in walls)
        s['keep'] = any(poly_dist(p, k['polygon']) < 0.06 or pip(p, k['polygon']) for k in keep)
    rules = cfg.get('rules', {})
    for o in openings:
        ss = [s for s in S if box_dist(s['p'], o['bb']) < 0.06]
        if not ss:
            o['span'] = None; continue
        o['span'] = [list(map(lambda v: round(v, 3), ss[0]['p'])), list(map(lambda v: round(v, 3), ss[-1]['p']))]
        n = ss[len(ss) // 2]['n']; o['normal_in'] = [round(n[0], 3), round(n[1], 3)]
        if o['type'] == 'door':
            dep = rules.get('door_clear_m', 0.8)
            pts = [s['p'] for s in ss] + [(s['p'][0] + s['n'][0] * dep, s['p'][1] + s['n'][1] * dep) for s in reversed(ss)]
            o['clear_zone'] = [[round(a, 3), round(b, 3)] for a, b in pts[:1] + pts[len(ss) - 1:len(ss) + 1] + pts[-1:]]
            m = ss[len(ss) // 2]
            o['approach_point'] = [round(m['p'][0] + m['n'][0] * 0.45, 3), round(m['p'][1] + m['n'][1] * 0.45, 3)]
    entries = list(cfg.get('entries') or [])
    if not entries:
        run = []
        door_pts = [s for o in openings if o['type'] == 'door' for s in S if box_dist(s['p'], o['bb']) < 0.06]
        for s in S + [None]:
            if s is not None and not s['wall'] and not s['keep'] and s not in door_pts:
                run.append(s); continue
            if run and sum(r['len'] for r in run) >= 0.6:
                m = run[len(run) // 2]
                entries.append({'name': f'入口{len(entries) + 1}', 'point': [round(m['p'][0] + m['n'][0] * 0.4, 3), round(m['p'][1] + m['n'][1] * 0.4, 3)],
                                'width_m': round(sum(r['len'] for r in run), 2), 'source': 'auto: outline without wall'})
            run = []

    # ---- fixtures (assumed, from config)
    fixtures = []
    for f in cfg.get('fixtures', []):
        x0, y0, x1, y1 = f['rect']
        fx = dict(f); fx['polygon'] = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        mids = [((x0 + x1) / 2, y0, (0, -1)), ((x0 + x1) / 2, y1, (0, 1)), (x0, (y0 + y1) / 2, (-1, 0)), (x1, (y0 + y1) / 2, (1, 0))]
        best = max(mids, key=lambda m: poly_dist((m[0] + m[2][0] * 0.3, m[1] + m[2][1] * 0.3), poly) if pip((m[0] + m[2][0] * 0.3, m[1] + m[2][1] * 0.3), poly) else -1)
        n = best[2]; a = rules.get('kitchen_aisle_m', 0.9)
        fx['front_point'] = [round(best[0] + n[0] * 0.45, 3), round(best[1] + n[1] * 0.45, 3)]
        if n[1]:
            yy = best[1] + n[1] * a; fx['aisle'] = [(x0, best[1]), (x1, best[1]), (x1, yy), (x0, yy)]
        else:
            xx = best[0] + n[0] * a; fx['aisle'] = [(best[0], y0), (xx, y0), (xx, y1), (best[0], y1)]
        fixtures.append(fx)

    # ---- furniture
    objs = els('Object'); od = det(objs); ob = bbs(objs)
    furn, skipped, counts = [], [], {}
    rows = []
    for e, d, b in zip(objs, od, ob):
        g = e['elementId']['guid']; dt = d['details']; b = b.get('boundingBox3D')
        if g in cfg.get('ignore_guids', []) or not b: continue
        C = ((b['xMin'] + b['xMax']) / 2, (b['yMin'] + b['yMax']) / 2)
        if d['floorIndex'] != fi or not (pip(C, poly) or poly_dist(C, poly) < 0.2):
            skipped.append({'guid': g, 'lib': dt['libPart']['name'], 'centre': [round(C[0], 2), round(C[1], 2)], 'why': 'not in room'}); continue
        O = dt['origin']; a = dt['angle']
        vx, vy = C[0] - O['x'], C[1] - O['y']
        lc = (math.cos(-a) * vx - math.sin(-a) * vy, math.sin(-a) * vx + math.cos(-a) * vy)
        A, B = dt.get('dimensions', {}).get('x') or 0, dt.get('dimensions', {}).get('y') or 0
        if not A or not B:
            c, s = abs(math.cos(a)), abs(math.sin(a))
            W, D = b['xMax'] - b['xMin'], b['yMax'] - b['yMin']
            A, B = (W, D) if c > 0.99 else (D, W) if s > 0.99 else (W, D)
        lib = dt['libPart']['name']; kind = kind_of(lib, g, A, cfg)
        facing = (math.degrees(a) + (90 if cfg.get('front_axis', '+y') == '+y' else 0)) % 360
        if facing > 180.001: facing -= 360
        facing = round(facing, 2) + 0.0
        rows.append((kind, g, {'kind': kind, 'guid': g, 'lib': lib, 'size': [round(A, 3), round(B, 3), round(b['zMax'] - b['zMin'], 3)],
                               'center': [round(C[0], 3), round(C[1], 3)], 'facing': round(facing, 2),
                               'z_origin': O.get('z', floor_z), 'elev_m': round(b['zMin'] - floor_z, 3),
                               'local_center': [round(lc[0], 4), round(lc[1], 4)]}))
    rows.sort(key=lambda r: (r[0], r[1]))
    n_kind = {}
    for k, _, _ in rows: n_kind[k] = n_kind.get(k, 0) + 1
    for k, g, it in rows:
        counts[k] = counts.get(k, 0) + 1
        pre = ID_PREFIX.get(k, 'obj')
        it['id'] = pre if n_kind[k] == 1 else f'{pre}{counts[k]}'
        furn.append(it)

    out = {
        'about': 'room.json written by read_room.py. Metres, plan coords. facing deg: 0=+x(east) 90=+y(north); the side people sit on / use.',
        'read_at': time.strftime('%Y-%m-%d %H:%M:%S'), 'read_epoch': round(t0, 1), 'port': port,
        'story': {'index': fi, 'name': story['name'], 'floor_z': floor_z, 'height': story['height']},
        'room': {'name': room['name'], 'polygon': [list(p) for p in poly], 'bbox': [round(v, 3) for v in rbb]},
        'walls': walls, 'openings': openings, 'entries': entries, 'keep_out': keep, 'fixtures': fixtures,
        'furniture': furn, 'not_in_room': skipped, 'rules': rules,
    }
    json.dump(out, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"room '{room['name']}' story {story['name']} floor z {floor_z}  bbox {[round(v, 2) for v in rbb]}")
    print(f"walls {len(walls)}  windows {sum(o['type'] == 'window' for o in openings)}  doors {sum(o['type'] == 'door' for o in openings)}  "
          f"entries {[(e['name'], e['point']) for e in entries]}  keep-out {[k['name'] for k in keep]}  fixtures {[f['name'] for f in fixtures]}")
    for o in openings:
        if o['type'] == 'window' and o.get('span'):
            print(f"  window sill {o['sill_m']} m  span {o['span']}")
    print(f'furniture {len(furn)} (not in room: {len(skipped)})')
    for it in furn:
        print(f"  {it['id']:8s} {it['kind']:13s} {it['size'][0]:.2f}x{it['size'][1]:.2f}  at ({it['center'][0]:.2f}, {it['center'][1]:.2f})  facing {it['facing']:.0f}  [{it['lib']}]")
    print(f'-> {out_path}  ({time.time() - t0:.2f} s)')


if __name__ == '__main__':
    main()
