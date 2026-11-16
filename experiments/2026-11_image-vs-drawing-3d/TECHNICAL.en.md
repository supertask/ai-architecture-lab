[🇯🇵 日本語](TECHNICAL.md) | 🇺🇸 English

# Technical notes: exterior only vs exterior + drawings (for advanced users)

The architect-facing description is in [README.en.md](README.en.md), the index for AIs in [AI_GUIDE.en.md](AI_GUIDE.en.md), and each step's procedure in [prompts/](prompts/).
This file covers the file list, procedure details, capture and scoring, textures and paths.

## Connecting the AI to Rhino

- Setup guide: https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T#en
- Workshop slides (Japanese): https://docs.google.com/presentation/d/11fd7nvZPuE5BPmIBTQYlUanp_OZPNibPhbAnpD_UStg/edit?usp=sharing
  - Open Codex in the ChatGPT desktop app (execution permission "Full access") → paste the prompt from the setup page → let the AI install and configure the connection to Rhino/Grasshopper (or Archicad) as it guides you → have it build the "Barcelona Pavilion" as a connection test.
- The connection used in this experiment was an MCP server for Rhino ([supertask/rhino-mcp](https://github.com/supertask/rhino-mcp); lets the AI run Python inside Rhino). Anything with the same function will do.
- **In the first form (the AI only writes a script), no AI–Rhino connection is needed.** For capture, run `work/run_mine_here.py` created by `scripts/make_rhino_runner.py` (or `scripts/run_all_in_rhino.py`) yourself in Rhino's ScriptEditor.

## Procedure (commands)

### 1. Giving the prompt to your own agent

Same for Claude Code, Codex or Hermes Agent.

1. So the AI cannot see the answer, create a separate folder containing only the inputs (never start the model-building AI inside the kit folder: `outputs/reference_v14.py` and `scripts/draw_v14.py` are the answer itself):
   ```
   python scripts/prepare_run.py A --out D:/ai-run/A          # image only
   python scripts/prepare_run.py B --out D:/ai-run/B          # image + drawings
   # add --live to have the AI send parts to Rhino one by one (form of the 2nd, recorded run)
   ```
   (With the README's step 0/2 line "Read `prompts/00_prepare_A.md` and follow its instructions." the AI creates these as `../ai-run-A` / `../ai-run-B`.)
2. Start a **new conversation** in that folder (no past conversations, memory or skills) and type only this one sentence:
   "Read `prompt.md` and follow its instructions."
   - The experiment (recorded run) used the same form: just one line "Read (work folder)/A_prompt.md and follow its instructions" in a new conversation. The experiment's agent was Hermes Agent.
   - Claude Code: start `claude` in the folder and type it. Codex: add the folder in the desktop app and type it. Hermes Agent: start it in a terminal and type it.
   - `vision_analyze` (look at an image) and `execute_rhino_code` (run Python in Rhino) in the prompt are Hermes tool names. Other agents use tools with the same function (image reading, the Rhino connection's execute tool).
3. Run A and B in separate conversations with the same AI model. Copy the resulting `model.py` (and `params.json`, `notes.md`) to `work/mine/A/` and `work/mine/B/`, and create the capture file with `python scripts/make_rhino_runner.py` (do not overwrite the published `outputs/`).
   - Output locations: first form `<out>/outputs/A/`, `--live` `<out>/A_out/` (both with `model.py`, `params.json`, `notes.md`).

### 2. Capture and scoring

With the README's step-4 line (`prompts/10_shoot_and_score.md`) the AI does: collect the models into `work/mine/A|B/` → `python scripts/make_rhino_runner.py` (creates `work/run_mine_here.py` with the kit location written in) → run it in Rhino → `metrics.py work/compare --out work/results_mine`.
To re-capture the published models, do it by hand like this:

1. Replace `KIT = 'C:/path/to/kit/'` at the top of `scripts/run_compare.py` and `scripts/run_all_in_rhino.py` with the absolute path of this folder.
2. Run `scripts/run_all_in_rhino.py` in Rhino (open and run it in ScriptEditor, or tell the AI "run this file in Rhino") → silhouettes and comparison images in `work/compare/<name>/`. **Do not resize the Rhino window during the run** (it changes the scale).
3. Scoring: `uv run -q --with pillow --with numpy python scripts/metrics.py` (1st run) / `scripts/metrics_live.py` (2nd run) → `results/`, `run2_recorded/results/`. Add `--out <folder>` to write elsewhere without overwriting the published results; `--tags A_image_only,B_image_plus_drawing` limits which models are scored.
4. Comparison sheets: `uv run -q --with pillow python scripts/sheets.py`.

**Checking only the scoring, without Rhino**: the silhouettes captured during verification are in `results/silhouettes/`.
`uv run -q --with pillow --with numpy python scripts/metrics_live.py results/silhouettes --out work/results_check` gives the same numbers as the published 2nd run (`run2_recorded/results/metrics_live.json`) (verified; takes a few minutes; for the 1st run see "What cannot be reproduced" below). The README line "Read `prompts/11_check_scoring.md` and follow its instructions." does the same.

### Procedure (what happens inside)

1. Give the AI only the `prompts/A_…md` prompt and the exterior image, and have it write `model.py` (it does not run Rhino).
2. In a separate conversation, give the `prompts/B_…md` prompt with the image + drawings and have it write the same way.
3. Run `scripts/run_all_in_rhino.py` in Rhino (it calls `run(path of model.py, name, ALIGN, ('concrete','black_mortar','rammed_earth'))`).
   - Build the model → replace ground and road with common ones → apply common materials → capture with the same cameras (same angle as the exterior image, back left/right, right front, oblique top; for the shape comparison, parallel projections from top, front, right side and back).
   - A's origin is aligned to "the left end and front-most point of the building" (ALIGN=True, since the image alone does not define an origin). The correct model and B use ALIGN=False.
4. `scripts/metrics.py`: overlays the parallel-projection silhouettes, shifts to the best-overlapping position within ±3 m, then computes the overlap ratio (IoU), missing ratio and extra ratio.
5. `scripts/sheets.py`: makes the comparison images.

## What cannot be reproduced (details)

- **AI answers change every time.** Even with the same prompt and model, assumed dimensions (eye height etc.) change, and A's overlap moves a few points per run. Look at the trend (A around 70–80%, B in the 90s).
- **AI models get updated.** Results with Claude Opus 5.5 on 4–5 November 2026.
- **The drawing loop is human judgement itself.** The mark-up process can be viewed on the Figma board, but doing the loop yourself gives different drawings. To test B under the same conditions, use `inputs/drawing_v14.png` as is.
- **Image generation does not reproduce the same pixels.** The exterior image (`inputs/house_v6C.png`) is bundled as generated (no procedure to regenerate it is included). Textures also change with cloud-side model updates even with the same prompt and seed. The textures used for the comparison (`tex/`) are bundled.
- **The 1st-run numbers differ by up to 0.5 points when recomputed from the bundled silhouettes**, because the correct model's silhouettes were re-captured after the 1st scoring (the 2nd run matches exactly).
- Screen recordings exist only as posted on X; recording/editing procedures are not included.

## Contents

- `README.md` / `README.en.md` (for architects), `AI_GUIDE.md` / `AI_GUIDE.en.md` (index for AIs), `TECHNICAL.md` / `TECHNICAL.en.md` (this file)
- `inputs/house_v6C.png`: the exterior (AI image, fictional house)
- `inputs/drawing_v14.png`: the drawings refined with a human via Figma (ground-floor plan, front, left side, first-floor plan; 1 grid square = 1 m) (the public version only removes a personal name from the title; content is the same as given to B)
  - The loop (human mark-ups r1–r9 and AI exports v7–v14) can be viewed on the Figma board (view only): https://www.figma.com/board/Fajd8nO7JFtNX5Ty2JOus4
- `prompts/A_image_only_prompt.md`, `prompts/B_image_plus_drawing_prompt.md`: prompts given to the AI (verbatim; `prepare_run.py` replaces locations and appends one sentence "tell the user to go back to the first conversation" to make `prompt.md`)
- `prompts/00_prepare_A.md`, `00_prepare_B.md`, `10_shoot_and_score.md`, `11_check_scoring.md`: the prompts the AI reads at each README step (written for publication; they describe the preparation, capture and scoring the experimenter's AI did directly; apart from the scoring in `11_`, not run in this form)
- `prompts/textures.md`: texture prompts and post-processing
- `outputs/A/`, `outputs/B/`: the model scripts written by the AI `model.py`, assumed dimensions `params.json`, notes `notes.md`
- `outputs/reference_v14.py`: the correct model (as per the drawings)
- `run2_recorded/`: prompts, outputs and results of the 2nd run (recorded; built by sending parts to Rhino)
- `scripts/`
  - `prepare_run.py`: creates the clean work folder handed to the AI
  - `make_rhino_runner.py`: creates `work/run_mine_here.py`, a Rhino file that captures your own A/B models (`work/mine/`) under the same conditions as the correct model (kit location written in)
  - `run_compare.py`, `run_all_in_rhino.py`: run models in Rhino and capture them under identical conditions
  - `metrics.py`, `metrics_live.py`: compute the overlap ratio (IoU). `sheets.py`: comparison sheets
  - `draw_v14.py`: the script that drew `inputs/drawing_v14.png` (running it produces the same image except the title line; verified)
  - `comfy_wf.py`, `seam.py`, `deepbump.py`, `make_pbr.py`, `common.py`: texture generation and PBR conversion. `make_tex.py`: adjusts the look for the comparison
  - `fontutil.py`: finds a Japanese font per OS
- `tex/`: textures used in the comparison (fair-faced concrete, black mortar, rammed earth, wood; colour, normal, roughness, AO), settings `materials.json`, and how the exterior-matched concrete was made `concrete_v6_src/`
- `results/`: comparison images, `metrics.json`, silhouettes from verification `silhouettes/`
- `images/`: README images (`inputs_A_B.jpg` = the exterior image and the drawings side by side)
- `skills/`: this experiment's procedures in a form any agent can use ([skills/README.en.md](skills/README.en.md))

## Used

- AI: Claude Opus 5.5 (via Hermes Agent; 1st run as a sub-agent, 2nd run in a new conversation; neither received prior conversation)
- Rhino + RhinoCommon (run as Python scripts). In the 2nd run the AI drove Rhino through an MCP server for Rhino
- Drawings: Figma (FigJam) + iPad
- Textures: ComfyUI (Comfy Cloud) Qwen-Image 2.1 t2i → seam → DeepBump → make_pbr
- Image processing: Python 3 + Pillow + NumPy (installed into a temporary environment with `uv run --with …`)

## Result details

### 1st run (script-writing run, 2026-11-04, one trial each)

Result table in [README.en.md](README.en.md). Numbers in `results/metrics.json`.

Honest notes: A's `model.py` as written made the walls disappear (faces pointed inward). Only 3 lines fixing the orientation were added before running (dimensions unchanged). The correct model is built from the drawings, so the comparison favours B. One trial each. The house is fictional (made from an AI image).

### 2nd run (recorded run, 2026-11-04)

The same comparison was repeated with the AI sending parts to Rhino one by one, and the screen was recorded. The headline numbers in the note article (image only 68–80%, with drawings 96–100%) are from this run.

- Prompts: `run2_recorded/prompts/A_prompt.md`, `B_prompt.md` (same text as the 1st run plus "build part by part in Rhino"; input/output folders replaced by `<REC>/` for publication)
- AI: Hermes Agent (Claude Opus 5.5) started in a terminal; in a new conversation, only "Read (work folder)/A_prompt.md and follow its instructions" was typed. The same preparation: `python scripts/prepare_run.py A --live --out <folder>`
- Outputs: `run2_recorded/outputs/A`, `B`; results: `run2_recorded/results/` (`metrics_live.json`, `overlap_sheet_live.png`, `cmp_live.jpg`)
- A's scale assumption (camera height) changed from 2.1 m in the 1st run to 1.62 m in the 2nd, and the shape changed each time.
- B was accurate in both runs wherever the drawings said something; the deviations were where the drawings said nothing (around the single-storey part at the right end, the recess ceiling material).

## Facade textures

- The 3 types used in the comparison + wood: using `tex/materials.json` (prompts, seeds, physical values), generate colour with ComfyUI → `seam.py config` → `deepbump.py --config` → `make_pbr.py` (output in `work/materials/`) → adjust for the comparison with `make_tex.py` into `tex/`. Details in [skills/pbr-texture-pipeline.md](skills/pbr-texture-pipeline.md).
- The grey fair-faced concrete matched to the exterior, `tex/concrete_v6_src/`: 6 base images made with ComfyUI's Qwen-Image 2.1 (image editing, input = the exterior image), the original prompts (`PROMPTS.md`), and the assembly script `make_concrete_v6.py`
  - `uv run --with pillow --with numpy python tex/concrete_v6_src/make_concrete_v6.py` creates a seamless 14.4 m square, 4096 px texture (basecolor / normal / roughness / AO / height) in `tex/concrete_v6/`. The output is large, so it is not in the repository.

## Paths

- Read `C:/path/to/kit/` in the scripts as the location of this folder (top of `run_compare.py`, `run_all_in_rhino.py`, `outputs/reference_v14.py`). `make_rhino_runner.py` writes the real location for you.
- `<KIT>` and `<REC>` in the prompts are replaced with the work-folder path by `scripts/prepare_run.py`.
- Capture saves Rhino's Rendered view with `ViewCapture`. Resizing the Rhino window changes the scale of the parallel projections, so capture all models with the same window state.
- Generated files (`work/`) and the DeepBump program itself (`tools/`) are excluded from the repository via `.gitignore`.
