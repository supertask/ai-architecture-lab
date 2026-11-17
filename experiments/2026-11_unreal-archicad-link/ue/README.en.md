# Unreal Engine side (furniture moving together with Archicad)

Mirror the Archicad furniture in Unreal Engine so that moving it in either program moves it in the other.
Datasmith Direct Link carries shapes and materials from Archicad; `ue_follow.py` carries furniture positions both ways.

| File | Role |
|---|---|
| `ue_follow.py` | the follower: keeps Archicad and Unreal Engine furniture positions in step, both directions |
| `ue_attach.py` | attaches ready-made furniture meshes as children of the Archicad (Datasmith) actors |
| `ue_material_swap.py` | restyles the material assets Datasmith created (asset level) |
| `ue_mark_dirty.py` | marks the level as changed before saving |
| `config.json` | Unreal Engine-side settings (no paths; the scripts find their own folder) |

All of these are Python scripts that run inside the Unreal Engine editor, not from a terminal.

## 1. First-time setup

1. Install the **Datasmith Archicad Exporter** (by Epic Games, Direct Link version) into Archicad.
2. Create a new Unreal Engine 5 project (architecture template or blank).
3. Edit → Plugins: enable **Python Editor Script Plugin** and **Datasmith Importer**, then restart the editor.
4. (optional) Edit → Project Settings → Python: enable Developer Mode for readable errors.

## 2. Connect Archicad (Direct Link)

1. Open the project in Archicad and show Window → Palettes → Datasmith.
2. Bring Archicad's 3D window to the front (Direct Link only sends while the 3D window is in front).
3. In Unreal Engine: toolbar "+" (Quick Add) → Datasmith → Direct Link Import, pick the Archicad source.
4. In the Content Browser right-click the imported scene asset → enable "Direct Link Auto-Reimport".
5. Nudge a piece in Archicad and check it arrives in Unreal Engine (Sync / AutoSync in Archicad's Datasmith palette).

## 3. Start the follower (ue_follow.py)

1. Make sure the **Tapir add-on** is running in Archicad (same as the main kit setup).
2. Sync once with Direct Link so that Unreal Engine and Archicad agree (the follower measures each piece when it first sees it).
3. In Unreal Engine's Output Log set the input box to "Cmd" and type `py "<KIT>/ue/ue_follow.py"` (`<KIT>` = where you put this kit folder) (or File → Execute Python Script).
4. The log shows `ue_follow running: N actors`; N is the number of Archicad objects (furniture).
5. Drag a piece with the gizmo in Unreal Engine: the Archicad plan follows during the drag (batched sends about every 0.3 s).
6. Move a piece in Archicad, or let the AI agent apply a layout with the kit: Unreal Engine follows in about 0.2–0.4 s.
7. Stop: `py ".../ue/ue_follow.py" stop`   Status: `py ".../ue/ue_follow.py" status`

To start it automatically: Edit → Project Settings → Plugins → Python → Startup Scripts, add the full path of `ue_follow.py` (it waits for Archicad and looks for it every 5 s).

- The mapping is automatic: each Datasmith actor carries its Archicad GUID (`Datasmith_UniqueId`), so there is no table to keep.
- With several Archicad windows open, set `archicad_port` in `config.json`.
- Log: `ue/logs/follow.jsonl`.
- Measured (2026-11-17, 21 pieces): move in Archicad -> Unreal Engine follows in about 0.6 s. Drag a gizmo in Unreal Engine for 2.5 s -> 5 batched sends during the drag (0.28-0.37 s each), so the plan moves while you drag. Applying a kit layout (17 pieces) and undoing it -> every piece follows, 0 cm difference.
- Check it is working: `status` shows `followed` and `calibrated` equal to your furniture count. The log shows `batch` (sends during a drag) and `pulled` (moves received from Archicad).

## 4. Real furniture (ue_attach.py, optional)

Archicad furniture arrives as boxy shapes. Swap only the look: a ready-made mesh is attached as a child, while the Datasmith actor (the thing that moves) stays, so the follower and Direct Link keep working.

1. Import furniture meshes into the project (e.g. Poly Haven CC0 FBX), upright and real size. Normalise image-to-3D output (upright, front, real size) before import.
2. In `config.json` → `attach.items` write which piece gets which mesh. `match` is `kind` (kind names from the kit's `config.json`, e.g. `sofa`), `libpart` (part of the library part name) or `guid`.
3. Set `mesh_front` to the direction the meshes face (`+Y` for most Poly Haven models). If one faces backwards, add `"yaw": 180` to its item.
4. Choose `fit`: `none` = real size (recommended), `uniform` = scaled evenly to fit the Archicad box in plan, `box` = stretched to the box, `height` = scaled evenly to the box height (plants).
5. Run `py ".../ue/ue_attach.py"`. Children are named `LK_<piece>_<n>` and the box is hidden. Re-running gives the same result.

## 5. Materials (ue_material_swap.py, optional)

1. Make your own materials (material or material instance).
2. In `config.json` → `material_swap.map` write "your material path → names of the Datasmith-created materials".
3. Run `py ".../ue/ue_material_swap.py" check` to see what matches, then run it without `check`.

## 6. Saving

1. Run `py ".../ue/ue_mark_dirty.py"` and check the level tab shows `*`.
2. File → Save Current Level (or Save All).

## Known pitfalls

| What happens | What to do |
|---|---|
| A Python loop assigning materials per mesh slot crashes the editor seconds to minutes later | Swap materials at asset level (`ue_material_swap.py`); never loop `set_material` over actors or slots |
| Every Direct Link reimport puts the Datasmith materials back | After a reimport run `ue_material_swap.py` and `ue_attach.py` again (both are safe to re-run) |
| After an editor restart "Direct Link Auto-Reimport" is off and Archicad changes silently stop arriving | Re-enable it on the scene asset after every start; nudge a piece to check |
| File → Save writes nothing after Python moved actors | Run `ue_mark_dirty.py` first. The follower marks the actors it moves itself |
| Saving or Save As from Python can crash the editor | Save from the File menu |
| After Save As the follower holds stale actors | It re-grabs them automatically (`tick_error` then `scan` in the log); if it persists, run `ue_follow.py` again |
| Pieces follow with a constant offset of tens of cm | Unreal Engine and Archicad disagreed when the follower started. Sync with Direct Link, then run `ue_follow.py` again (re-measures) |
| Direct Link sends nothing while Archicad's plan window is in front | Positions still travel through the follower; for shape or material changes bring the 3D window to the front and sync |
| Reimporting the Direct Link scene from Python deletes all child actors | Leave reimports to "Direct Link Auto-Reimport" (GUI) |
| Unreal Engine stops redrawing its viewport when it is behind other windows | Keep Unreal Engine in front when showing the motion |
| The gizmo is not drawn in Game View (G) | Leave Game View (G) to drag with the mouse |
