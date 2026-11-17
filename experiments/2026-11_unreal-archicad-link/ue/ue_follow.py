# -*- coding: utf-8 -*-
"""ue_follow.py - keep Unreal (Datasmith Direct Link actors) and Archicad (Tapir add-on) furniture in step.

Runs INSIDE the Unreal editor (Python Editor Script Plugin):
    py "<KIT>/ue/ue_follow.py"          start (or restart)
    py "<KIT>/ue/ue_follow.py" stop     stop
    py "<KIT>/ue/ue_follow.py" status   print what is followed

What it does
- Finds every Datasmith actor tagged Archicad.Element.Type.<type> (config: element_types) and maps it to its
  Archicad element by GUID (Datasmith_UniqueId user data, or the tag Archicad.Element.UniqueID.<GUID>).
  No hand-made mapping table.
- Archicad -> Unreal: every pull_dt seconds ONE Tapir GetDetailsOfElements call reads all mapped elements;
  changed ones are moved in Unreal.
- Unreal -> Archicad: while the mouse is held (gizmo drag) every drag_dt seconds ONE Tapir ModifyObjects call
  sends all pieces that are moving; after release + settle_s a final absolute send (skipped when already in sync).
- Echo suppression: values we send become the pull baseline, pull pauses for the dragged pieces (hold_s), and a
  pulled move is never treated as a user move.
- Re-scans when actors appear/disappear (Direct Link reimport, level change) and when actor wrappers go stale
  (e.g. after File > Save Current Level As).

Thread rule (crash lesson): the worker thread does only HTTP + float maths on plain values. Every unreal.* call
happens on the editor thread in the slate post-tick callback. This script never assigns materials
(a per-slot set_material loop crashed the editor repeatedly; use ue_material_swap.py, asset level).

Calibration: when a piece is first seen, its offset between the Archicad origin and the Unreal pivot is
measured, assuming Unreal and Archicad agree at that moment (do one Direct Link sync first).
Settings: ue/config.json (falls back to ../config.json for the Archicad port).
"""
import builtins, json, math, os, queue, sys, threading, time, urllib.request
import unreal

TAG_TYPE = 'Archicad.Element.Type.'
TAG_GUID = 'Archicad.Element.UniqueID.'


# ----------------------------- settings (no absolute paths) -----------------------------
def _here():
    f = globals().get('__file__')
    if f and os.path.isfile(f):
        return os.path.dirname(os.path.abspath(f))
    d = os.environ.get('LAYOUT_KIT_UE')
    if d and os.path.isdir(d):
        return d
    raise RuntimeError('ue_follow: cannot find the ue/ folder. Run it as  py "<path>/ue/ue_follow.py"  '
                       'or set the environment variable LAYOUT_KIT_UE to that folder.')


HERE = _here()
KIT = os.path.dirname(HERE)
DEFAULTS = {'archicad_port': None, 'element_types': ['Object'], 'settle_s': 0.3, 'pull': True, 'pull_dt': 0.2,
            'drag': True, 'drag_dt': 0.3, 'hold_s': 1.2, 'tol_m': 0.003, 'tol_rad': 0.002, 'rebuild': False,
            'rescan_s': 1.5, 'mark_dirty': True, 'log': 'logs/follow.jsonl'}


def _read_json(p):
    try:
        with open(p, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def load_cfg():
    cfg = dict(DEFAULTS)
    cfg.update({k: v for k, v in _read_json(os.path.join(HERE, 'config.json')).items()
                if k in DEFAULTS})
    if cfg['archicad_port'] is None and os.environ.get('ARCHICAD_PORT'):
        cfg['archicad_port'] = int(os.environ['ARCHICAD_PORT'])
    if cfg['archicad_port'] is None:
        cfg['archicad_port'] = _read_json(os.path.join(KIT, 'config.json')).get('archicad_port')
    return cfg


CFG = load_cfg()
LOG = os.path.normpath(CFG['log'] if os.path.isabs(CFG['log']) else os.path.join(HERE, CFG['log']))
os.makedirs(os.path.dirname(LOG), exist_ok=True)


# ----------------------------- worker side: plain Python only -----------------------------
def _post(port, body, timeout):
    req = urllib.request.Request('http://127.0.0.1:%d' % port, json.dumps(body).encode('utf-8'),
                                 {'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def tapir(port, cmd, params, timeout=10):
    r = _post(port, {'command': 'API.ExecuteAddOnCommand',
                     'parameters': {'addOnCommandId': {'commandNamespace': 'TapirCommand', 'commandName': cmd},
                                    'addOnCommandParameters': params}}, timeout)
    if not r.get('succeeded'):
        raise RuntimeError(r)
    return r['result']['addOnCommandResponse']


def alive(port):
    try:
        return bool(_post(port, {'command': 'API.IsAlive'}, 1.0).get('result', {}).get('isAlive'))
    except Exception:
        return False


def rot(a, x, y):
    c, s = math.cos(a), math.sin(a)
    return c * x - s * y, s * x + c * y


def mouse_down():
    """Left or right mouse button held (Windows). Elsewhere: never (then only the release send is used)."""
    try:
        import ctypes
        k = ctypes.windll.user32.GetAsyncKeyState
        return bool((k(0x01) | k(0x02)) & 0x8000)
    except Exception:
        return False


def write_log(d):
    d['t'] = round(time.time(), 3)
    try:
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(d, ensure_ascii=False) + '\n')
    except Exception:
        pass


class Worker(threading.Thread):
    """Owns all HTTP. Input: jobs queue of plain tuples. Output: out queue of plain dicts."""

    def __init__(self, cfg, jobs, out):
        super().__init__(daemon=True)
        self.cfg, self.jobs, self.out = cfg, jobs, out
        self.alive = True
        self.port = None
        self.guids = ()
        self.busy = set()     # guids with a final send in flight
        self.last = {}        # guid -> (x, y, angle) last known in Archicad (pull baseline)
        self.z = {}           # guid -> Archicad z
        self.hold = {}        # guid -> time until which pull must not read it back (live drag)
        self.rebuild_due = 0.0
        self.last_rebuild = 0.0

    def call(self, cmd, params, timeout=10):
        return tapir(self.port, cmd, params, timeout)

    def details(self, guids):
        """ONE GetDetailsOfElements for many GUIDs -> {guid: ((x, y, z), angle)} (missing elements left out)."""
        res = self.call('GetDetailsOfElements', {'elements': [{'elementId': {'guid': g}} for g in guids]})
        out = {}
        for g, r in zip(guids, res.get('detailsOfElements', [])):
            d = (r or {}).get('details')
            if not d or 'origin' not in d:
                continue
            o = d['origin']
            out[g] = ((float(o['x']), float(o['y']), float(o.get('z', 0.0))), float(d.get('angle', 0.0)))
        return out

    def find_port(self):
        p = self.cfg.get('archicad_port')
        if p and alive(int(p)):
            return int(p)
        found = [q for q in range(19723, 19744) if alive(q)]
        if len(found) == 1:
            return found[0]
        self.out.put({'ev': 'port_err', 'found': found,
                      'err': 'no Archicad with Tapir found' if not found else
                      'several Archicad instances: set archicad_port in ue/config.json'})
        return None

    def run(self):
        next_pull = 0.0
        while self.alive:
            if self.port is None:
                self.port = self.find_port()
                if self.port is None:
                    time.sleep(5.0)          # worker thread: sleeping here does not block the editor
                    continue
                self.out.put({'ev': 'port', 'port': self.port})
            try:
                job = self.jobs.get(timeout=0.05)
            except queue.Empty:
                job = None
            try:
                if job is not None:
                    self.handle(job)
                now = time.time()
                if self.rebuild_due and now >= self.rebuild_due:
                    self.rebuild_due = 0.0
                    try:
                        self.call('RebuildView', {'regenerate': True}, timeout=20)
                    except Exception as e:
                        self.out.put({'ev': 'rebuild_err', 'err': repr(e)})
                    self.last_rebuild = time.time()
                if self.cfg['pull'] and now >= next_pull and not any(v > now for v in self.hold.values()):
                    next_pull = now + self.cfg['pull_dt']
                    self.pull()
            except Exception as e:
                self.out.put({'ev': 'worker_err', 'err': repr(e)})
                if isinstance(e, OSError):   # Archicad closed or port changed -> find it again
                    self.port = None

    def handle(self, job):
        kind = job[0]
        if kind == 'guids':
            self.guids = tuple(job[1])
            self.last = {g: v for g, v in self.last.items() if g in self.guids}
        elif kind == 'calib':                      # ('calib', [(guid, ue_x, ue_y), ...])  one Tapir call
            items = job[1]
            det = self.details([g for g, _, _ in items])
            L = {}
            for g, ux, uy in items:
                if g not in det:
                    continue
                (ox, oy, oz), ang = det[g]
                L[g] = list(rot(-ang, ux / 100.0 - ox, -uy / 100.0 - oy))
                self.z[g] = oz
                self.last[g] = (round(ox, 4), round(oy, 4), round(ang, 4))
            self.out.put({'ev': 'calib', 'L': L, 'missing': [g for g, _, _ in items if g not in det]})
        elif kind == 'batch':                      # ('batch', [(guid, L, cur), ...], ev)  live drag
            self.batch(job[1], job[2])
        elif kind == 'commit':                     # ('commit', guid, L, cur, ev)  after release
            _, guid, L, cur, ev = job
            self.busy.add(guid)
            try:
                self.commit(guid, L, cur, ev)
            finally:
                self.busy.discard(guid)

    def want(self, L, cur, z):
        """Unreal pivot (cm, yaw deg) -> Archicad origin (m) and angle (rad)."""
        a = math.radians(-cur[3]) % (2 * math.pi)
        lx, ly = rot(a, L[0], L[1])
        return {'x': cur[0] / 100.0 - lx, 'y': -cur[1] / 100.0 - ly, 'z': z}, a

    def commit(self, guid, L, cur, ev):
        t0 = time.time()
        det = self.details([guid])
        if guid not in det:
            ev.update({'ev': 'missing'}); self.out.put(ev); return
        (ox, oy, oz), ang = det[guid]
        w, wa = self.want(L, cur, oz)
        dpos = math.hypot(w['x'] - ox, w['y'] - oy)
        dang = abs(((wa - ang + math.pi) % (2 * math.pi)) - math.pi)
        if dpos < self.cfg['tol_m'] and dang < self.cfg['tol_rad']:
            ev['ev'] = 'in_sync'
            self.last[guid] = (round(ox, 4), round(oy, 4), round(ang, 4))
        else:
            try:
                self.call('ModifyObjects', {'objectsWithDetails': [
                    {'elementId': {'guid': guid}, 'coordinates': w, 'angle': wa}]})
                self.last[guid] = (round(w['x'], 4), round(w['y'], 4), round(wa, 4))   # echo baseline
                ev.update({'ev': 'sent', 'dpos_m': round(dpos, 4), 'dang_rad': round(dang, 4)})
                if self.cfg['rebuild']:
                    self.rebuild_due = max(time.time(), self.last_rebuild + 1.0)
            except Exception as e:
                ev.update({'ev': 'error', 'err': repr(e)})
        ev['ms'] = round((time.time() - t0) * 1000, 1)
        self.out.put(ev)

    def batch(self, items, ev):
        now = time.time()
        missing = [g for g, _, _ in items if g not in self.z]
        if missing:
            for g, (o, _a) in self.details(missing).items():
                self.z[g] = o[2]
        objs, wants = [], {}
        for guid, L, cur in items:
            if guid not in self.z:
                continue
            w, wa = self.want(L, cur, self.z[guid])
            objs.append({'elementId': {'guid': guid}, 'coordinates': w, 'angle': wa})
            wants[guid] = (round(w['x'], 4), round(w['y'], 4), round(wa, 4))
            self.hold[guid] = now + self.cfg['hold_s']
        t0 = time.time()
        try:
            if objs:
                self.call('ModifyObjects', {'objectsWithDetails': objs})
            for g, k in wants.items():
                self.last[g] = k
                self.hold[g] = time.time() + self.cfg['hold_s']
            ev.update({'ev': 'batch', 'n': len(objs), 'ms': round((time.time() - t0) * 1000, 1)})
        except Exception as e:
            ev.update({'ev': 'batch_err', 'err': repr(e)})
        self.out.put(ev)

    def pull(self):
        now = time.time()
        gs = [g for g in self.guids if g not in self.busy and self.hold.get(g, 0) <= now]
        if not gs:
            return
        for g, ((ox, oy, oz), ang) in self.details(gs).items():   # ONE call for all
            self.z[g] = oz
            key = (round(ox, 4), round(oy, 4), round(ang, 4))
            if g in self.last and self.last[g] != key:
                self.out.put({'ev': '_pull', 'guid': g, 'o': [ox, oy, oz], 'ang': ang})
            self.last[g] = key


# ----------------------------- editor-thread side: all unreal.* here -----------------------------
def actor_guid(a, tags):
    g = ''
    try:
        g = unreal.DatasmithContentLibrary.get_datasmith_user_data_value_for_key(a, 'Datasmith_UniqueId')
    except Exception:
        pass
    if not g:
        g = next((t[len(TAG_GUID):] for t in tags if t.startswith(TAG_GUID)), '')
    return str(g) if g else ''


class Follow:
    def __init__(self, cfg):
        self.cfg = cfg
        self.types = {TAG_TYPE + t for t in cfg['element_types']}
        self.jobs, self.out = queue.Queue(), queue.Queue()
        self.track = {}       # guid -> state dict (plain values + L)
        self.actors = {}      # guid -> actor (editor thread only)
        self.n_seen = -1
        self.handle = None
        self.prev_down = False
        self.inflight = set()
        self.t_rescan = 0.0
        self.t_drag = 0.0
        self.drag_inflight = False
        self.worker = Worker(cfg, self.jobs, self.out)

    def log(self, d, show=True):
        write_log(d)
        if show:
            unreal.log('[ue_follow] ' + json.dumps(d, ensure_ascii=False)[:300])

    def linked(self):
        eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        for a in eas.get_all_level_actors():
            tags = [str(t) for t in a.tags]
            if self.types.intersection(tags):
                yield a, tags

    def scan(self):
        self.actors, found, calib = {}, {}, []
        for a, tags in self.linked():
            g = actor_guid(a, tags)
            if not g:
                continue
            l = a.get_actor_location(); yaw = float(a.get_actor_rotation().yaw)
            old = self.track.get(g)
            self.actors[g] = a
            found[g] = dict(label=str(a.get_actor_label()), last=(float(l.x), float(l.y), float(l.z), yaw),
                            moving=False, t_change=0.0, down=False, sent=None,
                            L=old['L'] if old else None)
            if found[g]['L'] is None:
                calib.append((g, float(l.x), float(l.y)))
        self.track = found
        self.n_seen = len(found)
        self.jobs.put(('guids', tuple(found)))
        if calib:
            self.jobs.put(('calib', calib))
        self.log({'ev': 'scan', 'n': len(found), 'calibrating': len(calib)})

    def rescan_if_changed(self):
        n = sum(1 for _ in self.linked())
        if n != self.n_seen:
            self.scan()

    def tick(self, dt):
        try:
            self._tick()
        except Exception as e:      # typically stale actor wrappers after Save Level As -> rebuild on next tick
            self.actors = {}
            self.n_seen = -2
            self.t_rescan = 0.0
            self.log({'ev': 'tick_error', 'err': repr(e)[:200]})

    def _tick(self):
        now = time.time()
        down = mouse_down()
        self.prev_down = down
        for _ in range(50):
            try:
                d = self.out.get_nowait()
            except queue.Empty:
                break
            ev = d.get('ev')
            if ev == 'calib':
                for g, L in d['L'].items():
                    if g in self.track:
                        self.track[g]['L'] = tuple(L)
                self.log({'ev': 'calib', 'n': len(d['L']), 'missing': d['missing']})
            elif ev == '_pull':
                self.apply_pull(d)
            elif ev in ('batch', 'batch_err'):
                self.drag_inflight = False
                self.log(d, show=(ev == 'batch_err'))
            else:
                if 'guid' in d:
                    self.inflight.discard(d['guid'])
                self.log(d)
        if not down and now - self.t_rescan > self.cfg['rescan_s']:
            self.t_rescan = now
            self.rescan_if_changed()
        for g, s in list(self.track.items()):
            a = self.actors.get(g)
            if a is None or not unreal.SystemLibrary.is_valid(a):
                self.n_seen = -2; self.t_rescan = 0.0
                continue
            l = a.get_actor_location(); yaw = float(a.get_actor_rotation().yaw)
            cur = (float(l.x), float(l.y), float(l.z), yaw)
            if any(abs(c - p) > 1e-3 for c, p in zip(cur, s['last'])):
                if not s['moving']:
                    s['moving'] = True; s['down'] = down
                s['down'] = s['down'] or down
                s['last'] = cur; s['t_change'] = now
                continue
            if (s['moving'] and not down and now - s['t_change'] >= self.cfg['settle_s']
                    and g not in self.inflight and s['L'] is not None):
                s['moving'] = False; s['sent'] = None
                self.inflight.add(g)
                self.jobs.put(('commit', g, tuple(s['L']), cur, {'guid': g, 'label': s['label'],
                                                                 'ue': [round(v, 2) for v in cur]}))
        if self.cfg['drag'] and down and not self.drag_inflight and now - self.t_drag >= self.cfg['drag_dt']:
            items = []
            for g, s in self.track.items():
                if s['moving'] and s['L'] is not None and g not in self.inflight and s['sent'] != s['last']:
                    items.append((g, tuple(s['L']), tuple(s['last']))); s['sent'] = s['last']
            if items:
                self.t_drag = now; self.drag_inflight = True
                self.jobs.put(('batch', items, {'labels': [self.track[g]['label'] for g, _, _ in items]}))

    def apply_pull(self, d):
        g = d['guid']
        s = self.track.get(g); a = self.actors.get(g)
        if (not s or s['moving'] or s['L'] is None or g in self.inflight or a is None
                or not unreal.SystemLibrary.is_valid(a)):
            return
        ox, oy, _ = d['o']; ang = d['ang']
        lx, ly = rot(ang, s['L'][0], s['L'][1])
        nx, ny, nyaw = (ox + lx) * 100.0, -(oy + ly) * 100.0, -math.degrees(ang)
        l = a.get_actor_location(); r = a.get_actor_rotation()
        if abs(nx - l.x) + abs(ny - l.y) < 0.05 and abs(((nyaw - r.yaw + 180) % 360) - 180) < 0.05:
            return
        if self.cfg['mark_dirty']:
            a.modify()                    # so File > Save really writes the level
        a.set_actor_location_and_rotation(unreal.Vector(nx, ny, l.z), unreal.Rotator(r.roll, r.pitch, nyaw),
                                          False, False)
        nl = a.get_actor_location()
        s['last'] = (float(nl.x), float(nl.y), float(nl.z), float(a.get_actor_rotation().yaw))  # not a user move
        self.log({'ev': 'pulled', 'label': s['label']}, show=False)

    def status(self):
        n_cal = sum(1 for s in self.track.values() if s['L'] is not None)
        return {'running': self.handle is not None, 'port': self.worker.port, 'followed': len(self.track),
                'calibrated': n_cal, 'labels': sorted(s['label'] for s in self.track.values())}

    def start(self):
        self.scan()
        self.worker.start()
        self.handle = unreal.register_slate_post_tick_callback(self.tick)
        self.log({'ev': 'started', 'cfg': {k: v for k, v in self.cfg.items() if k != 'log'}})

    def stop(self):
        if self.handle is not None:
            unreal.unregister_slate_post_tick_callback(self.handle)
            self.handle = None
        self.worker.alive = False
        self.log({'ev': 'stopped'})


def main(argv):
    cmd = argv[0].lower() if argv else 'start'
    cur = getattr(builtins, '_layout_kit_follow', None)
    if cmd == 'status':
        print(json.dumps(cur.status() if cur else {'running': False}, ensure_ascii=False))
        return
    if cur:
        cur.stop()
        builtins._layout_kit_follow = None
    if cmd == 'stop':
        print('ue_follow stopped')
        return
    f = Follow(load_cfg())
    builtins._layout_kit_follow = f
    f.start()
    print('ue_follow running: %d actors (log: %s)' % (len(f.track), LOG))


_argv = [a for a in (sys.argv[1:] if len(getattr(sys, 'argv', [])) > 1 else [])
         if os.path.basename(a) != os.path.basename(globals().get('__file__', '') or '?')]
main(_argv)
