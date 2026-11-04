Goal: Build a 3D massing model of a house from one exterior image PLUS a drawing sheet (plans/elevations), LIVE in Rhino (this run is screen-recorded).

Language: Japanese for notes and for your short progress lines.
This is a controlled experiment: you get one exterior perspective image of a fictional 2-storey house AND a drawing sheet (1F plan, front elevation directly below it, left side elevation to the right, 2F plan at the bottom; 1 grid square = 1 m; blue = glass/windows; grey = concrete; green = edge of the roof above; Japanese labels with heights in metres). The drawing was made by iterating with the owner on Figma and is the authority for shape and dimensions; the image is for appearance/materials and anything the drawing does not show.

INPUTS (the ONLY files you may open or analyze):
- Exterior image: C:/rec/house_v6C.png
- Drawing sheet (Figma export): C:/rec/drawing_v14.png (1935x2480 px; 50 px = 1 m; read coordinates from the grid)
Use vision_analyze as many times as you like, and crop/zoom with python+pillow (`uv run -q --with pillow python file.py` into the output folder; write scripts to files). You may also measure pixel colours of the drawing in code (e.g. find blue window lines, grey fills) to get exact dimensions.
STRICT: do NOT open, list, or search any other file or folder on this PC. Do NOT use skills, memory, session_search, honcho, delegate_task, Notion, Figma, ComfyUI or paid tools. Using other material would invalidate the experiment.

BUILD LIVE IN RHINO (Rhino is open; use the rhino MCP tool execute_rhino_code, IronPython, no f-strings):
- First call: delete all existing objects, create layers, set the Perspective view to Shaded.
- Then build the house in about 6-10 separate calls, one part per call, in this order: ground & road -> main volumes (with rounded corners as arcs in plan) -> recess (which faces are wall vs glass exactly per the drawing) -> slit window -> front ribbon window wrapping the rounded corner -> back windows -> timber parts -> carport / 1F-only part -> pool.
- Before each call, write ONE short Japanese line saying what you are about to build and the key dimensions and where they came from (e.g. 「左の箱：幅7.5m 高さ7.5m（図面の正面図から）」).
- At the end of each call: d.Views.Redraw() and zoom extents in the Perspective view (view.ActiveViewport.ZoomExtents()).
- Layers named exactly: M_Concrete (walls/slabs), M_Glass (glazing, thin solid ~20mm), M_Wood (timber mullions, soffits, bands), M_Water (pool water surface), M_Paving (ground/sidewalk), M_Asphalt (road). Units mm. Z up; the street is on the -Y side (building front faces -Y); X increases to the right as seen from the street; use the drawing's grid origin (x=0 at the left edge of the left box, y=0 per the plan grid).
- Breps: boxes, extrusions of polylines incl. arc points, G.Brep.CreateBooleanDifference(a,b,tol). Make sure closed solids are outward-oriented before booleans (if SolidOrientation is Inward, Flip()).

OUTPUT folder: C:/rec/B_out/
Write at the end:
1. model.py - one combined RhinoCommon script that rebuilds exactly what you built (ends with result = 'ok').
2. params.json - every dimension (name, value_mm, source: drawing/image/guess, confidence).
3. notes.md - short Japanese notes: what came from the drawing, what from the image, what was still guessed.
Finish with a short Japanese summary and the remaining uncertain assumptions.
