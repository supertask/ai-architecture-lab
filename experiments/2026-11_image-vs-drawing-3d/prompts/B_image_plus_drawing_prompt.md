# B：外観＋Figma の図面 — AI に渡した指示（原文そのまま）

- 実行：Hermes Agent のサブエージェント（会話の文脈なし）、モデル Claude Opus 5.5、2026-11-04
- 入力：外観画像 1 枚（`inputs/house_v6C.png`）＋図面 1 枚（`inputs/drawing_v14.png`、Figma に置いた図をそのまま書き出したもの）
- AI が使えた道具：画像を見る（vision）、Python で画像を切り抜く・色を測る。Rhino は実行させない（スクリプトを書くだけ）

## Goal
Build a 3D massing model of a house from one exterior image PLUS a drawing sheet (plans/elevations), as a RhinoCommon Python script (do not run Rhino).

## Context
Language for notes: Japanese.
This is a controlled experiment: you get one exterior perspective image of a fictional 2-storey house AND a drawing sheet (1F plan, front elevation directly below it, left side elevation to the right, 2F plan at the bottom; 1 grid square = 1 m; blue = glass/windows; grey = concrete; green = edge of the roof above; Japanese labels with heights in metres). The drawing was made by iterating with the owner on Figma and is the authority for shape and dimensions; the image is for appearance/materials and anything the drawing does not show.

INPUTS (the ONLY files you may open or analyze):
- Exterior image: <KIT>/inputs/house_v6C.png
- Drawing sheet (Figma export): <KIT>/inputs/drawing_v14.png  (1935x2480 px; scale 0.05 px per mm i.e. 50 px = 1 m; read coordinates from the grid)
Use vision_analyze as many times as you like, and crop/zoom with python+pillow (`uv run -q --with pillow python file.py`; write scripts to files, inline `python -c` multi-line fails on this Windows bash). You may also measure pixel colours of the drawing in code (e.g. find blue window lines, grey fills) to get exact dimensions.
STRICT: do NOT open, list, or search any other file or folder under <WORKDIR> (in particular NOT draw_v14.py or any other .py/.json in drafting/, nothing in model_*/, VERSIONS.md, Figma, Notion). Using the source scripts would invalidate the experiment. Do NOT run Rhino or any MCP rhino tool; do NOT use ComfyUI or paid tools.

OUTPUT folder: <KIT>/outputs/B/
Write:
1. model.py - an IronPython/CPython-compatible RhinoCommon script (import Rhino, Rhino.Geometry as G, System, math). It must: get d = Rhino.RhinoDoc.ActiveDoc; delete all existing objects; build Breps (boxes, extrusions of polylines incl. arc points for rounded corners, Boolean differences with G.Brep.CreateBooleanDifference(a,b,tol)) and add them with d.Objects.AddBrep(brep, attrs) on layers named exactly: M_Concrete (walls/slabs), M_Glass (all glazing, thin solid ~20mm), M_Wood (timber mullions, soffits, bands), M_Water (pool water surface), M_Paving (ground/sidewalk), M_Asphalt (road). Create layers if missing using d.Layers.FindByFullPath(name,-1) then Add. Units mm. Coordinate convention: Z up; the street is on the -Y side (building front faces -Y); X increases to the right as seen from the street; use the drawing's grid origin (x=0 at the left edge of the left box, y=0 per the plan grid) so dimensions match the drawing. Include all volumes and heights, rounded corners (as arcs in plan), the recess (which faces are wall vs glass exactly per the drawing), slit window, front ribbon window wrapping the rounded corner, back windows, carport, 1F-only part, pool, ground, road. End the script with: result = 'ok'.
2. params.json - every dimension (name, value_mm, source: drawing/image/guess, confidence).
3. notes.md - short Japanese notes: what came from the drawing, what from the image, what was still guessed.
Check the script for Python syntax errors (`python -X utf8 -m py_compile model.py`). Return a short summary with the output paths and the remaining uncertain assumptions.

## 実行時に Hermes が直した所
なし（そのまま実行）。
