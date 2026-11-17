# -*- coding: utf-8 -*-
"""ue_mark_dirty.py - mark the linked furniture (and LK_ children) as modified, so File > Save writes the level.

Runs INSIDE the Unreal editor:   py "<KIT>/ue/ue_mark_dirty.py"
Why: moving actors from Python does not mark the level as changed; File > Save then silently writes nothing.
Run this, check the level tab shows *, then save from the File menu (saving from Python crashed the editor).
"""
import unreal

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
n = 0
for a in eas.get_all_level_actors():
    tags = [str(t) for t in a.tags]
    if any(t.startswith('Archicad.Element.Type.') for t in tags) or str(a.get_actor_label()).startswith('LK_'):
        a.modify()
        n += 1
print('ue_mark_dirty: %d actors marked; now File > Save Current Level' % n)
