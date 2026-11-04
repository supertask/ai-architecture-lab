Goal: Build a 3D massing model of a house from ONE exterior image only, LIVE in Rhino (this run is screen-recorded).

Language: Japanese for notes and for your short progress lines.
This is a controlled experiment: you get ONLY one exterior perspective image of a fictional 2-storey house and must infer the 3D form as accurately as you can.

INPUT (the ONLY file you may open or analyze): C:/rec/house_v6C.png
Use vision_analyze on it as many times as you like (crops welcome: crop with python+pillow via `uv run -q --with pillow python file.py` into the output folder; write scripts to files).
STRICT: do NOT open, list, or search any other file or folder on this PC. Do NOT use skills, memory, session_search, honcho, delegate_task, Notion, Figma, ComfyUI or paid tools. Using other material would invalidate the experiment.

BUILD LIVE IN RHINO (Rhino is open; use the rhino MCP tool execute_rhino_code, IronPython, no f-strings):
- First call: delete all existing objects, create layers, set the Perspective view to Shaded.
- Then build the house in about 6-10 separate calls, one part per call, in this order: ground & road -> main volumes (with rounded corners as arcs in plan) -> recess (wall vs glass inside it) -> slit window -> ribbon window -> timber parts -> carport/canopy -> pool -> hidden back/right sides (keep simple).
- Before each call, write ONE short Japanese line saying what you are about to build and the key dimensions you chose (e.g. 「左の箱：幅7.0m 奥行8.0m 高さ7.0m（車の長さ4.5mから推定）」).
- At the end of each call: d.Views.Redraw() and zoom extents in the Perspective view (view.ActiveViewport.ZoomExtents()).
- Layers named exactly: M_Concrete (walls/slabs), M_Glass (glazing, thin solid ~20mm), M_Wood (timber mullions, soffits, bands), M_Water (pool water surface), M_Paving (ground/sidewalk), M_Asphalt (road). Units mm. Z up; the street is on the -Y side (building front faces -Y); X increases to the right as seen from the street; put the bottom-left-front corner of the overall building footprint near the origin.
- Breps: boxes, extrusions of polylines incl. arc points, G.Brep.CreateBooleanDifference(a,b,tol). Make sure closed solids are outward-oriented before booleans (if SolidOrientation is Inward, Flip()).

OUTPUT folder: C:/rec/A_out/
Write at the end:
1. model.py - one combined RhinoCommon script that rebuilds exactly what you built (ends with result = 'ok').
2. params.json - every dimension you assumed (name, value_mm, how you estimated it, confidence high/med/low).
3. notes.md - short Japanese notes: what you could read from the image, what you had to guess, what is invisible.
Estimate scale from cues (car ~4.5m long, storey ~3m, door, kerb). Finish with a short Japanese summary and the 5 most uncertain assumptions.
