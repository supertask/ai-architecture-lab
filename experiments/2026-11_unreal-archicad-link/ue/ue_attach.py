# -*- coding: utf-8 -*-
"""ue_attach.py - put real furniture meshes on the Archicad furniture in Unreal, as CHILDREN of the Datasmith actors.

Runs INSIDE the Unreal editor:   py "<KIT>/ue/ue_attach.py"
Settings: "attach" in ue/config.json (kinds and front_axis come from ../config.json).

Why children: the Datasmith actor keeps its GUID, so ue_follow.py and Direct Link still move it;
the child mesh rides along. The boxy Archicad mesh is hidden (hide_parent).

Rules for the meshes you use (import them into the project first):
- upright, real size (cm), front facing mesh_front in the mesh's own axes (+Y for most Poly Haven models).
  Image-to-3D output must be normalised (upright, front, real size) before import; this script does not guess.
- fit: none = keep real size (best for normalised meshes) | uniform = scale to fit the Archicad box in plan |
  box = stretch each axis to the Archicad box | height = scale uniformly to the Archicad box height (plants).
Placement: centred on the Archicad box in plan, standing on its bottom (on_top: on its top), optional offset_cm.
Idempotent: children are named LK_<parent label>_<item no.>_<mesh no.>; run it again after every Direct Link reimport.
No material assignment here (bulk set_material loops crashed the editor). Give the mesh asset its materials,
or use ue_material_swap.py.
"""
import json, math, os
import unreal

TAG_TYPE = 'Archicad.Element.Type.'
TAG_GUID = 'Archicad.Element.UniqueID.'
TAG_LIB = 'Archicad.Element.LibPart.Name.'


def _here():
    f = globals().get('__file__')
    if f and os.path.isfile(f):
        return os.path.dirname(os.path.abspath(f))
    d = os.environ.get('LAYOUT_KIT_UE')
    if d and os.path.isdir(d):
        return d
    raise RuntimeError('ue_attach: run it as  py "<path>/ue/ue_attach.py"  or set LAYOUT_KIT_UE')


def _read_json(p):
    try:
        with open(p, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


HERE = _here()
UCFG = _read_json(os.path.join(HERE, 'config.json'))
KCFG = _read_json(os.path.join(os.path.dirname(HERE), 'config.json'))
ACFG = UCFG.get('attach', {})
TYPES = {TAG_TYPE + t for t in UCFG.get('element_types', ['Object'])}
AXIS = {'+x': (1, 0), '-x': (-1, 0), '+y': (0, 1), '-y': (0, -1)}


def axis_deg(name, archicad):
    x, y = AXIS[name.lower()]
    if archicad:            # Archicad y is flipped in Unreal
        y = -y
    return math.degrees(math.atan2(y, x))


def kind_of(lib, guid, width_m):
    """Same rule as read_room.py: kind_by_guid first, then the first 'kinds' entry contained in the part name."""
    if guid in KCFG.get('kind_by_guid', {}):
        return KCFG['kind_by_guid'][guid]
    for rule in KCFG.get('kinds', []):
        if rule[0].lower() in lib.lower():
            if len(rule) > 2 and 'min_width' in rule[2] and width_m < rule[2]['min_width']:
                return rule[2]['else']
            return rule[1]
    return 'other'


def mesh_bounds(meshes):
    mn, mx = [1e18] * 3, [-1e18] * 3
    for m in meshes:
        b = m.get_bounding_box()
        for i, (lo, hi) in enumerate(((b.min.x, b.max.x), (b.min.y, b.max.y), (b.min.z, b.max.z))):
            mn[i] = min(mn[i], lo); mx[i] = max(mx[i], hi)
    return mn, mx


def main():
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    eal = unreal.EditorAssetLibrary
    acts = eas.get_all_level_actors()
    by_label = {str(a.get_actor_label()): a for a in acts}
    parents = []
    for a in acts:
        tags = [str(t) for t in a.tags]
        if not TYPES.intersection(tags) or not isinstance(a, unreal.StaticMeshActor):
            continue
        g = ''
        try:
            g = str(unreal.DatasmithContentLibrary.get_datasmith_user_data_value_for_key(a, 'Datasmith_UniqueId') or '')
        except Exception:
            pass
        g = g or next((t[len(TAG_GUID):] for t in tags if t.startswith(TAG_GUID)), '')
        lib = next((t[len(TAG_LIB):] for t in tags if t.startswith(TAG_LIB)), '')
        sm = a.static_mesh_component.static_mesh
        if not g or sm is None:
            continue
        b = sm.get_bounding_box()
        parents.append(dict(actor=a, guid=g, lib=lib, label=str(a.get_actor_label()),
                            mn=[b.min.x, b.min.y, b.min.z], mx=[b.max.x, b.max.y, b.max.z]))
    for p in parents:
        p['kind'] = kind_of(p['lib'], p['guid'], (p['mx'][0] - p['mn'][0]) / 100.0)

    parent_front = axis_deg(KCFG.get('front_axis', '+y'), archicad=True)
    KW = unreal.AttachmentRule.KEEP_WORLD
    DK = unreal.DetachmentRule.KEEP_WORLD
    done, missing_mesh, unmatched = 0, set(), []
    for n_item, item in enumerate(ACFG.get('items', [])):
        m = item.get('match', {})
        hits = [p for p in parents
                if ('guid' in m and p['guid'].lower() == str(m['guid']).lower())
                or ('kind' in m and p['kind'] == m['kind'])
                or ('libpart' in m and str(m['libpart']).lower() in p['lib'].lower())]
        if not hits:
            unmatched.append(m); continue
        paths = item['mesh'] if isinstance(item['mesh'], list) else [item['mesh']]
        meshes = [eal.load_asset(x) if eal.does_asset_exist(x) else None for x in paths]
        if any(x is None or not isinstance(x, unreal.StaticMesh) for x in meshes):
            missing_mesh.update(x for x, y in zip(paths, meshes) if y is None or not isinstance(y, unreal.StaticMesh))
            continue
        mn, mx = mesh_bounds(meshes)
        cs = [mx[i] - mn[i] for i in range(3)]
        cc = [(mn[i] + mx[i]) / 2 for i in range(3)]
        mfront = axis_deg(item.get('mesh_front', ACFG.get('mesh_front', '+Y')), archicad=False)
        rel = (parent_front - mfront + float(item.get('yaw', 0.0))) % 360.0
        q = rel / 90.0
        right_angle = abs(q - round(q)) < 1e-6
        odd = right_angle and int(round(q)) % 2 == 1
        ew, ed = (cs[1], cs[0]) if odd else (cs[0], cs[1])     # mesh size seen along the parent's X / Y
        fit = item.get('fit', 'none')
        for p in hits:
            pmn, pmx = p['mn'], p['mx']
            ps = [pmx[i] - pmn[i] for i in range(3)]
            pc = [(pmn[i] + pmx[i]) / 2 for i in range(3)]
            if fit == 'box' and right_angle:
                sx, sy = ps[0] / max(ew, 1e-3), ps[1] / max(ed, 1e-3)
                if odd:
                    sx, sy = sy, sx
                S = [sx, sy, ps[2] / max(cs[2], 1e-3)]
            elif fit in ('box', 'uniform'):
                k = min(ps[0] / max(ew, 1e-3), ps[1] / max(ed, 1e-3)); S = [k, k, k]
            elif fit == 'height':
                k = ps[2] / max(cs[2], 1e-3); S = [k, k, k]
            else:
                S = [1.0, 1.0, 1.0]
            a = math.radians(rel); ca, sa = math.cos(a), math.sin(a)
            sx_, sy_ = S[0] * cc[0], S[1] * cc[1]
            off = item.get('offset_cm', [0, 0, 0])
            rx = pc[0] - (ca * sx_ - sa * sy_) + off[0]
            ry = pc[1] - (sa * sx_ + ca * sy_) + off[1]
            rz = (pmx[2] if item.get('on_top') else pmn[2]) - S[2] * mn[2] + off[2]
            par = p['actor']
            for j, (path, mesh) in enumerate(zip(paths, meshes)):
                lab = 'LK_%s_%d_%d' % (p['label'], n_item, j)
                c = by_label.get(lab)
                if c is None or not unreal.SystemLibrary.is_valid(c):
                    c = eas.spawn_actor_from_object(mesh, par.get_actor_location())
                    c.set_actor_label(lab); by_label[lab] = c
                elif c.static_mesh_component.static_mesh != mesh:
                    c.static_mesh_component.set_static_mesh(mesh)
                c.modify()
                if c.get_attach_parent_actor() != par:
                    c.detach_from_actor(DK, DK, DK)
                    c.attach_to_actor(par, '', KW, KW, KW, False)
                c.set_actor_relative_scale3d(unreal.Vector(*S))
                c.set_actor_relative_rotation(unreal.Rotator(0.0, 0.0, rel), False, False)
                c.set_actor_relative_location(unreal.Vector(rx, ry, rz), False, False)
            if ACFG.get('hide_parent', True) and not item.get('on_top'):
                par.modify()
                par.static_mesh_component.set_visibility(False, False)
            done += 1
            print('attached', p['label'], p['kind'], 'yaw', round(rel, 1), 'scale', [round(v, 3) for v in S])
    print('ue_attach: %d attached' % done)
    if missing_mesh:
        print('  meshes not found (import them, or fix the paths in ue/config.json):', sorted(missing_mesh))
    if unmatched:
        print('  no Archicad actor matched:', unmatched)
    kinds = sorted({p['kind'] for p in parents})
    print('  kinds present:', kinds)


main()
