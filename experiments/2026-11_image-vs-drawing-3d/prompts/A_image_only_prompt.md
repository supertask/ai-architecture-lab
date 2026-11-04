# A：外観だけ — AI に渡した指示（原文そのまま）

- 実行：Hermes Agent のサブエージェント（会話の文脈なし）、モデル Claude Opus 5.5、2026-11-04
- 入力：外観画像 1 枚（`inputs/house_v6C.png`）
- AI が使えた道具：画像を見る（vision）、Python で画像を切り抜く。Rhino は実行させない（スクリプトを書くだけ）

## Goal
Build a 3D massing model of a house from ONE exterior image only, as a RhinoCommon Python script (do not run Rhino).

## Context
Language for notes: Japanese.
This is a controlled experiment: you get ONLY one exterior perspective image of a fictional 2-storey house and must infer the 3D form as accurately as you can.

INPUT (the ONLY file you may open or analyze): <KIT>/inputs/house_v6C.png
Use vision_analyze on it as many times as you like (crops welcome: copy it to your output folder and crop with python+pillow via `uv run -q --with pillow python file.py`; write scripts to files, inline `python -c` multi-line fails on this Windows bash).
STRICT: do NOT open, list, or search any other file or folder under <WORKDIR> (especially nothing under base-house/, drafting/, model_*/, VERSIONS.md, Figma, Notion). Using other material would invalidate the experiment. Do NOT run Rhino or any MCP rhino tool; do NOT use ComfyUI or paid tools.

OUTPUT folder: <KIT>/outputs/A/
Write:
1. model.py - an IronPython/CPython-compatible RhinoCommon script (import Rhino, Rhino.Geometry as G, System, math). It must: get d = Rhino.RhinoDoc.ActiveDoc; delete all existing objects; build Breps (boxes, extrusions of polylines incl. arc points for rounded corners, Boolean differences with G.Brep.CreateBooleanDifference(a,b,tol)) and add them with d.Objects.AddBrep(brep, attrs) on layers named exactly: M_Concrete (walls/slabs), M_Glass (all glazing, thin solid ~20mm), M_Wood (timber mullions, soffits, bands), M_Water (pool water surface), M_Paving (ground/sidewalk), M_Asphalt (road). Create layers if missing using d.Layers.FindByFullPath(name,-1) then Add. Units mm. Coordinate convention: Z up; the street is on the -Y side (building front faces -Y); X increases to the right as seen from the street; put the bottom-left-front corner of the overall building footprint near the origin. Include: all volumes and heights, roof/parapet edges, rounded corners (as arcs in plan), the recess and what is wall vs glass inside it, the slit window, the ribbon window, carport/canopy, pool, ground, road, and your best guess of the hidden sides (back/right) - keep hidden guesses simple. End the script with: result = 'ok'.
2. params.json - every dimension you assumed (name, value_mm, how you estimated it, confidence high/med/low).
3. notes.md - short Japanese notes: what you could read from the image, what you had to guess, what is invisible.
Work carefully; estimate scale from cues (car ~4.5m long, storey ~3m, door, people/kerb). Check the script for Python syntax errors (e.g. `python -X utf8 -m py_compile model.py`). Return a short summary with the output paths and the 10 most uncertain assumptions.

## 実行時に Hermes が直した所（1 か所だけ）
`prism()` の面の向きが内向きのソリッドになり、くり抜き（ブール演算）で壁が消えていたので、内向きなら反転する 3 行を足した。寸法の数値は変えていない（`outputs/A/model.py` に `[Hermes 実行時の修正]` と注記）。
