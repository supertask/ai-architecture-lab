[🇯🇵 日本語](AI_GUIDE.md) | 🇺🇸 English

# AI_GUIDE: guide for AI agents reproducing this experiment

You (an AI agent) use this folder (the **kit**) to reproduce, together with an architect user:
"have an AI build a Rhino model from one exterior image only (A) / image + drawings (B), and compare each with the correct model by overlap ratio".
The human-facing description is [README.en.md](README.en.md). Everything an AI needs (files, commands, what was actually done in the experiment, troubleshooting) is in this file.

## 1. How to work

**The procedure lives in the prompt files in `prompts/`.** At each step the user pastes a line of the form
"Read `<prompt file>` and follow its instructions." (or the Japanese 「`<file>` を読んで、指示どおりに作業してください」).
The kit's step prompts are in Japanese; follow them as written, but **reply to the user in the user's language** and give the next line in that language.
If the user asks without naming a prompt file, determine the current step from the table below (read `work/progress.md` if it exists), then read that step's prompt file and proceed.

## 2. Most important rule: you, with the kit open, never build the models

The kit contains the answer (`outputs/reference_v14.py`, `scripts/draw_v14.py`, `outputs/`, `run2_recorded/outputs/`, `results/`).
The A and B models are built by an AI in **a new conversation** in separate folders containing only the inputs (`ai-run-A`, `ai-run-B`). Your job is preparation, capture, scoring and explanation. Never tell the user or the model-building AI anything from the answer files (dimensions etc.).

## 3. Steps and prompt files

| Step | Working folder | File in the user's one-liner | Content |
| --- | --- | --- | --- |
| 0 | kit | `prompts/00_prepare_A.md` | Decide the form (build in Rhino / script only); create `../ai-run-A` with `prepare_run.py A` |
| 1 | ai-run-A (new conversation) | `prompt.md` | Build the model (the experiment's verbatim prompt; the kit's AI is not involved) |
| 2 | kit | `prompts/00_prepare_B.md` | Create `../ai-run-B` |
| 3 | ai-run-B (new conversation) | `prompt.md` | Build the model |
| 4 | kit | `prompts/10_shoot_and_score.md` | Collect the models into `work/mine/`, `make_rhino_runner.py` → capture in Rhino → `metrics.py --out work/results_mine` |
| — | kit | `prompts/11_check_scoring.md` | Without Rhino, recompute the recorded run's numbers from the bundled silhouettes (`metrics_live.py --out work/results_check`) |

- Give the step 1/3 conversations nothing about the kit and no other material (it would change the conditions). Run A and B in separate conversations with the same AI model.

## 4. Rules for every step

1. **The user is an architect, not a programmer.** Reply in the user's language, briefly, in architectural terms. Do not show commands, paths or jargon (JSON, IoU, Python, MCP…) — say "overlap ratio" for IoU.
2. **You run all commands.** Ask permission before installing Python or image-processing packages.
3. **Ask the user only to start new conversations and to do things in the Rhino GUI.** Say exactly what to paste where.
4. **Only one AI sends commands to Rhino at a time.** While a model-building conversation is using Rhino, send nothing to Rhino.
5. **Never overwrite the published results (`results/`, `run2_recorded/results/`, `outputs/`).** Write your results under `work/`.
6. **Never fabricate results.** Explain failures plainly and propose the next move.
7. If the connection is missing, point the user to the setup page (English https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T#en / Japanese https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T#ja).
8. `vision_analyze` (look at an image) and `execute_rhino_code` (run Python in Rhino) in the prompts are tool names of the experiment's agent (Hermes Agent). Map them to the tools with the same function in other agents (image reading, the Rhino connection's execute tool).

## 5. Files and scripts

- `README.md` / `README.en.md`: for people (architects). `AI_GUIDE.md` / `AI_GUIDE.en.md`: this file
- `inputs/house_v6C.png`: the exterior (AI image, fictional house)
- `inputs/drawing_v14.png`: the drawings refined with a human via Figma (ground-floor plan, front, left side, first-floor plan; 1 grid square = 1 m). The public version only removes a personal name from the title (content is the same as given to B)
- `prompts/A_image_only_prompt.md`, `prompts/B_image_plus_drawing_prompt.md`: the verbatim prompts given to the model-building AI in the 1st run (see "9")
- `prompts/00_prepare_A.md`, `00_prepare_B.md`, `10_shoot_and_score.md`, `11_check_scoring.md`: the prompts the AI reads at each README step (written for publication)
- `prompts/textures.md`: texture prompts and post-processing
- `outputs/A/`, `outputs/B/`: the 1st run's model scripts `model.py`, assumed dimensions `params.json`, notes `notes.md`. **Not the answer, but published results — do not overwrite**
- `outputs/reference_v14.py`: the correct model (as per the drawings). **Never show it to the model-building AI**
- `run2_recorded/`: prompts (`prompts/A_prompt.md`, `B_prompt.md`), outputs and results of the 2nd run (recorded; built by sending parts to Rhino)
- `results/`: comparison images, `metrics.json`, silhouettes from verification `silhouettes/`
- `tex/`: textures used in the comparison (fair-faced concrete, black mortar, rammed earth, wood; colour, normal, roughness, AO), settings `materials.json`, and how the exterior-matched concrete was made `concrete_v6_src/`
- `skills/`: working procedures ([skills/README.en.md](skills/README.en.md))
- `images/`: README images
- `scripts/`:

| Script | Purpose |
| --- | --- |
| `prepare_run.py A` / `B` `--out <folder> [--live]` | Creates a clean work folder with only the inputs and puts `prompt.md` in it. `--live` uses the 2nd-run prompt (build part by part in Rhino) |
| `make_rhino_runner.py [--only A]` | Creates `work/run_mine_here.py`, a Rhino file that captures the models in `work/mine/A/`, `B/` under the same conditions as the correct model (kit location written in) |
| `run_compare.py`, `run_all_in_rhino.py` | Run models in Rhino and capture them under identical conditions (for re-capturing the published models; edit `KIT` at the top) |
| `metrics.py`, `metrics_live.py` | Overlap ratio (IoU) from silhouettes (1st run / 2nd run). Arguments `[silhouette folder] [--out folder] [--tags …]` |
| `sheets.py` | Makes the comparison sheets |
| `draw_v14.py` | The script that drew `inputs/drawing_v14.png` (running it gives the same image except the title line; verified). **Part of the answer — never show it to the model-building AI** |
| `comfy_wf.py`, `seam.py`, `deepbump.py`, `make_pbr.py`, `common.py` | Texture generation and PBR conversion |
| `make_tex.py` | Adjusts the textures' look for the comparison |
| `fontutil.py` | Finds a Japanese font per OS |

Requirements: Rhino (capture; run as RhinoCommon Python scripts), Python 3 + Pillow + NumPy (installed into a temporary environment with `uv run --with …`).

## 6. Connecting the AI to Rhino

- The connection used in the experiment was an MCP server for Rhino ([supertask/rhino-mcp](https://github.com/supertask/rhino-mcp); lets the AI run Python inside Rhino). Anything with the same function will do.
- **In the script-only form (the 1st run's form), no AI–Rhino connection is needed.** Only for capture, ask the user to open and run `work/run_mine_here.py` in Rhino's ScriptEditor.
- The step 0/2 prompts check whether the AI can drive Rhino; if so they create the folder in the "build part by part in Rhino" form (`--live`), otherwise in the script form.

## 7. Command details

### Preparing the model-building folders (steps 0 and 2)

Never start the model-building AI inside the kit folder (`outputs/reference_v14.py` and `scripts/draw_v14.py` are the answer itself). The step 0/2 prompts do this next to the kit (`../ai-run-A`, `../ai-run-B`):

```
python scripts/prepare_run.py A --out ../ai-run-A          # image only
python scripts/prepare_run.py B --out ../ai-run-B          # image + drawings
# add --live to have the AI send parts to Rhino one by one (form of the 2nd, recorded run)
```

- Steps 1/3: start a **new conversation** in that folder (no past conversations, memory or skills) and type only "Read `prompt.md` and follow its instructions." With Claude Code, start `claude` in the folder and type it; with Codex, add the folder in the desktop app and type it.
- Output locations: script form `<out>/outputs/A/`, `--live` `<out>/A_out/` (both with `model.py`, `params.json`, `notes.md`; same for B).

### Capture and scoring (step 4)

What `prompts/10_shoot_and_score.md` does:
1. Collect the models into `work/mine/A/` and `work/mine/B/` (with `params.json`, `notes.md`). Do not overwrite the published `outputs/`.
2. `python scripts/make_rhino_runner.py` → `work/run_mine_here.py`
3. Run `work/run_mine_here.py` in Rhino (you, if connected; otherwise the user in ScriptEditor) → silhouettes and comparison images in `work/compare/<name>/`. **The Rhino window must not be resized during the run** (it changes the scale).
4. `uv run -q --with pillow --with numpy python scripts/metrics.py work/compare --out work/results_mine`

### Checking only the scoring, without Rhino

```
uv run -q --with pillow --with numpy python scripts/metrics_live.py results/silhouettes --out work/results_check
```

Gives the same numbers as the published 2nd run (`run2_recorded/results/metrics_live.json`) (verified; takes a few minutes). Same as `prompts/11_check_scoring.md`. The 1st-run numbers differ by up to 0.5 points when recomputed from the bundled silhouettes (the correct model's silhouettes were re-captured after the 1st scoring; the 2nd run matches exactly).

### Re-capturing the published models (by hand)

1. Replace `KIT = 'C:/path/to/kit/'` at the top of `scripts/run_compare.py` and `scripts/run_all_in_rhino.py` with the kit's absolute path.
2. Run `scripts/run_all_in_rhino.py` in Rhino → `work/compare/<name>/`.
3. Scoring: `uv run -q --with pillow --with numpy python scripts/metrics.py` (1st run) / `scripts/metrics_live.py` (2nd run). **Without `--out <folder>` they overwrite the published `results/` / `run2_recorded/results/`**, so always add `--out work/…`. `--tags A_image_only,B_image_plus_drawing` limits which models are scored.
4. Comparison sheets: `uv run -q --with pillow python scripts/sheets.py`.

## 8. How capture and scoring work

- `run_all_in_rhino.py` calls `run(path of model.py, name, ALIGN, ('concrete','black_mortar','rammed_earth'))` per model.
- Build the model → replace ground and road with common ones → apply common materials → capture with the same cameras (same angle as the exterior image, back left/right, right front, oblique top; for the shape comparison, parallel projections from top, front, right side and back).
- A's origin is aligned to "the left end and front-most point of the building" (ALIGN=True, since the image alone does not define an origin). The correct model and B use ALIGN=False.
- Capture saves Rhino's Rendered view with `ViewCapture`. Resizing the Rhino window changes the scale of the parallel projections, so capture all models with the same window state.
- `metrics.py`: overlays the parallel-projection silhouettes, shifts to the best-overlapping position within ±3 m, then computes the overlap ratio (IoU), missing ratio and extra ratio.

## 9. What was actually done in the experiment

AI: Claude Opus 5.5 (via Hermes Agent). Drawings: Figma (FigJam) + iPad. 4–5 November 2026.

### 1st run (script-writing run, 2026-11-04)

- The model-building AI was a Hermes Agent sub-agent (no prior conversation given). It did not run Rhino; it wrote `model.py`. A got the image only, B the image + drawings. One trial each.
- A's `model.py` as written made the walls disappear (faces pointed inward). Only 3 lines fixing the orientation were added before running (dimensions unchanged).
- Numbers: `results/metrics.json`.

### 2nd run (recorded run, 2026-11-04)

- The same comparison was repeated with the AI sending parts to Rhino one by one, with screen recording. The headline numbers in the note article (image only 68–80%, with drawings 96–100%) are from this run.
- Hermes Agent was started in a terminal; in a new conversation, only "Read (work folder)/A_prompt.md and follow its instructions" was typed. Same preparation: `python scripts/prepare_run.py A --live --out <folder>`.
- Outputs: `run2_recorded/outputs/A`, `B`. Results: `run2_recorded/results/` (`metrics_live.json`, `overlap_sheet_live.png`, `cmp_live.jpg`).
- A's scale assumption (camera height) changed from 2.1 m in the 1st run to 1.62 m in the 2nd, and the shape changed each time. B was accurate in both runs wherever the drawings said something; deviations were where the drawings said nothing (around the single-storey part at the right end, the recess ceiling material).

### Relation to the original prompts

- `prompts/A_image_only_prompt.md`, `B_image_plus_drawing_prompt.md`: verbatim 1st-run prompts (input/output locations are written as `<KIT>` / `<WORKDIR>`; `prepare_run.py` replaces them with the work folder).
- `run2_recorded/prompts/A_prompt.md`, `B_prompt.md`: the 2nd-run originals — the 1st-run text plus "build part by part in Rhino". Input/output folders were replaced by `<REC>/` for publication.
- `prepare_run.py` takes the body of the original, replaces locations with the work folder, and appends one sentence "tell the user to go back to the first conversation" (unrelated to how the model is built) to make `prompt.md`.

### What will differ when reproduced

- AI answers change every time; A's overlap moves a few points per run. Look at the trend (A around 70–80%, B in the 90s).
- The drawing loop (human mark-ups r1–r9 and AI exports v7–v14) is human judgement itself. The process can be viewed on the Figma board (view only) https://www.figma.com/board/Fajd8nO7JFtNX5Ty2JOus4. To test B under the same conditions, use `inputs/drawing_v14.png` as is.
- The exterior image is bundled as generated (no procedure to regenerate it). The correct model is built from the drawings, so the comparison favours B.

## 10. Written for publication, and what is untested

- `prompts/00_prepare_A.md`, `00_prepare_B.md`, `10_shoot_and_score.md`, `11_check_scoring.md` were written for publication (they describe the preparation, capture and scoring the experimenter's AI did directly).
- Verified: the scoring recomputation in `11_check_scoring` (same numbers), and that `draw_v14.py` reproduces the drawing.
- Untested: running steps 0–4 end to end; running with Claude Code or Codex. The `00_` and `10_` prompts have not been run in this form.

If something fails, assume it may be in an untested part: explain plainly and propose the next move.

## 11. Troubleshooting (what the AI does)

| Situation | What to do |
| --- | --- |
| The AI cannot drive Rhino | Proceed in the script form. Only for capture, ask the user to run `work/run_mine_here.py` in ScriptEditor. If they want to connect, point to the setup page |
| Walls disappear / odd shapes | Faces may point inward. In step 4 you may fix only the face orientation (never dimensions; the experiment also added 3 lines to A) |
| Overlap suddenly low (around 30%) | The Rhino window was probably resized during capture. Ask the user to leave the window as is, then redo the capture |
| Model building stopped midway | Have the user type "continue" in that conversation. If that fails, start a new conversation in the same folder with the same line |
| Continue another day | Read `work/progress.md` and tell the user the next line to paste |
| `C:/path/to/kit/` not found | Placeholder at the top of `run_compare.py`, `run_all_in_rhino.py`, `outputs/reference_v14.py`. Replace with the kit's absolute path (not needed for capturing your own models; `make_rhino_runner.py` writes it) |
| 1st-run numbers differ from the published ones by up to 0.5 points | Expected (see "Checking only the scoring, without Rhino"). Verify with the 2nd-run numbers |

## 12. Facade textures

This uses an image-generation service (ComfyUI cloud), so tell the user it costs money and get permission first.

- The 3 types used in the comparison + wood: using `tex/materials.json` (prompts, seeds, physical values), generate colour with ComfyUI (Qwen-Image 2.1 t2i) → `seam.py config` → `deepbump.py --config` → `make_pbr.py` (output in `work/materials/`) → adjust for the comparison with `make_tex.py` into `tex/`. Details in [skills/pbr-texture-pipeline.md](skills/pbr-texture-pipeline.md).
- The grey fair-faced concrete matched to the exterior, `tex/concrete_v6_src/`: 6 base images made with ComfyUI's Qwen-Image 2.1 (image editing, input = the exterior image), the original prompts (`PROMPTS.md`), and the assembly script `make_concrete_v6.py`.
  - `uv run --with pillow --with numpy python tex/concrete_v6_src/make_concrete_v6.py` creates a seamless 14.4 m square, 4096 px texture (basecolor / normal / roughness / AO / height) in `tex/concrete_v6/` (large, so not in the repository).
- Even with the same prompt and seed, cloud-side model updates change the image. The textures used in the comparison are bundled in `tex/`.
- Generated files (`work/`) and the DeepBump program itself (`tools/`) are in `.gitignore`.

## 13. Other requests

- **Make drawings via the Figma loop**: [skills/figma-drawing-markup-loop.md](skills/figma-drawing-markup-loop.md). It needs human mark-ups; ask for one concrete thing at a time.
- **Build a model from the user's own exterior rendering or sketch**: [skills/image-to-massing.md](skills/image-to-massing.md). There is no correct model, so no scoring; return the assumed dimensions with confidence levels.
- **Remake the textures**: "12. Facade textures" above.
- Fairness rules of the experiment (splitting A/B, scoring, capture pitfalls): [skills/input-comparison-experiment.md](skills/input-comparison-experiment.md)
