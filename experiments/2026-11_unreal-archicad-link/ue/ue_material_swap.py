# -*- coding: utf-8 -*-
"""ue_material_swap.py - restyle the material ASSETS that Datasmith created from Archicad surfaces.

Runs INSIDE the Unreal editor:   py "<KIT>/ue/ue_material_swap.py"   (add  check  to only list)
Settings: "material_swap" in ue/config.json  ->  {"map": {"<your material or MI path>": ["<Datasmith material name>", ...]}}

How: each matching Datasmith material instance gets your material as its parent, its overrides cleared, updated.
A dozen assets, no loop over actors or material slots (a per-slot set_material loop crashed the editor).
A Direct Link reimport puts the Datasmith parents back: run this again after every reimport.
Names match exactly first; otherwise a name containing the text matches.
"""
import json, os, sys
import unreal


def _here():
    f = globals().get('__file__')
    if f and os.path.isfile(f):
        return os.path.dirname(os.path.abspath(f))
    d = os.environ.get('LAYOUT_KIT_UE')
    if d and os.path.isdir(d):
        return d
    raise RuntimeError('ue_material_swap: run it as  py "<path>/ue/ue_material_swap.py"  or set LAYOUT_KIT_UE')


def main(check):
    with open(os.path.join(_here(), 'config.json'), encoding='utf-8') as f:
        cfg = json.load(f).get('material_swap', {})
    eal = unreal.EditorAssetLibrary
    mel = unreal.MaterialEditingLibrary
    mis = {}                       # asset name -> [package paths]  (listing does not load the assets)
    for path in eal.list_assets(cfg.get('search_root', '/Game'), recursive=True, include_folder=False):
        pkg = str(path).split('.')[0]
        mis.setdefault(pkg.rsplit('/', 1)[-1], []).append(pkg)
    n = 0
    for target_path, names in cfg.get('map', {}).items():
        target = eal.load_asset(target_path) if eal.does_asset_exist(target_path) else None
        if not isinstance(target, unreal.MaterialInterface):
            print('target material not found:', target_path); continue
        for name in names:
            pkgs = mis.get(name) or [p for k, v in mis.items() if name.lower() in k.lower() for p in v]
            pkgs = [p for p in pkgs if p != target_path.split('.')[0]]
            if not pkgs:
                print('no Datasmith material named', name); continue
            for pkg in pkgs:
                mi = eal.load_asset(pkg)
                if not isinstance(mi, unreal.MaterialInstanceConstant):
                    continue
                if check:
                    print('found', pkg, '(parent', mi.get_editor_property('parent').get_name() + ')'); continue
                mi.set_editor_property('parent', target)
                mel.clear_all_material_instance_parameters(mi)
                mel.update_material_instance(mi)
                n += 1
                print('ok', pkg, '->', target_path)
    print('ue_material_swap: %d assets restyled' % n)


main('check' in [a.lower() for a in sys.argv[1:]])
