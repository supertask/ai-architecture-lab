[🇯🇵 日本語](TECHNICAL.md) | 🇺🇸 English

# Technical notes: from a blank Archicad project to 8 sheets (for advanced users)

The architect-facing description is in [README.en.md](README.en.md), the index for AIs in [AI_GUIDE.en.md](AI_GUIDE.en.md), and each step's procedure in [prompts/](prompts/).
This file covers the file list, the order actually followed in the experiment, the model fix, where the scripts came from, and how paths are handled.

House: the fictional "Fair-faced Concrete and Water Basin House" (2-storey RC, 18,000 × 11,100, grid X1–X6 / Y1–Y4).

## What you need to run it

- Archicad (the experiment used the Japanese version; some scripts use template material names such as "コンクリート" = concrete) and the Tapir add-on
  - Tapir is an add-on that adds commands to Archicad's JSON API. The kit only sends commands from Python over HTTP (port 19723); it does not use MCP. Any AI agent that can write and run Python can drive it.
- Python 3 (most scripts use only the standard library; `export_png.py` needs Pillow and numpy; `prepare_workdir.py` makes real PNGs if Pillow is present)
- The Archicad template is the Japanese standard one. `fixA_comps.py` selects building materials **by index**, and `fixA_found.py` / `fixA_slabs.py` by the name "コンクリート". With another language/template, the indexed materials will be different ones, or the name will not be found and the script stops. In that case edit the indices/names at the top of those scripts to match your template's materials.
- An AI agent that can write and run Python (the experiment used Claude Opus 5.5)
- bash to run `run_sheets.sh` (on Windows, e.g. Git Bash)

How to connect the AI to Archicad: the setup page (https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T#en) and
the slides (Japanese, https://docs.google.com/presentation/d/11fd7nvZPuE5BPmIBTQYlUanp_OZPNibPhbAnpD_UStg/edit?usp=sharing).
Paste the distributed prompt into ChatGPT Codex (desktop); the AI installs and configures the connection to Rhino / Grasshopper or Archicad, and builds the Barcelona Pavilion as a connection test.

## Procedure (commands)

The order of steps, the human GUI actions and saving are in the table in [README.en.md](README.en.md). The script-only prompts (`00_prepare`, `05_sections`, `06_fix_model`, `18_export`) just run the commands below in order and show the output, so running them by hand is the same.
Overview (in the kit folder): GUI: open an empty project → `check_connection.py --scan` → `prepare_workdir.py` → `setup_stories.py work/house_from_scratch.pln` → prompts `01_`, `02_` → `make_sections.py create` → GUI: open each of the 6 section windows once → `fixA_snapshot.py` → `fixA_comps.py` → `fixA_walls.py` → `fixA_slabs.py --apply` → `fixA_found.py` → `fixA_raise.py` → `fixA_del2d.py --apply` → prompts `12_`→`13_`→`14_`→`15_`→`16_`→`17_`→`10_`→`11_` (each in a new conversation; save after each; `run_sheets.sh` does the same) → GUI: Reference IDs to A/B → `layer_found.py` → `export_png.py` → (review and fixes).

`run_sheets.sh`: pass a non-interactive "run once" agent command, e.g. `AGENT_CMD='claude -p --dangerously-skip-permissions' bash scripts/run_sheets.sh`. By default it runs the 8 prompts of step 7 in the experiment's order, each in a new process, and sends SaveProject after each (stops if saving fails). You can also name prompts, e.g. `SHEETS='20_fix_SA_round2'`.

### Running the prompts with your own agent

The prompt files (`prompts/*.md`) are plain prose (Japanese), not tied to any agent. Start the agent **in the kit folder** and type only this one line into a new conversation (only the first, `prompts/00_prepare.md`, is in the kit's prompts; after that, `work/prompts/…`):

> "Read `work/prompts/01_model_M.md` and follow its instructions."

- The experiment ran the same way (one line "Read ….md and …" in a new conversation). The experiment's agent was Hermes Agent.
- `work/prompts/` is created by `prepare_workdir.py`: copies with `<KIT>` (work folder), `<KITROOT>` (kit) and "port は 19723" replaced by real values. Without `prepare_workdir.py`, replace these by hand.
- Start the next prompt only after the previous one has finished. A new conversation per prompt prevents reuse of values from the previous sheet (the experiment used 1 prompt = 1 new conversation).
- Examples (not what the experiment used; ways to do the same thing):
  - Claude Code: start `claude` in the kit folder and type the line above. For batch runs, `AGENT_CMD='claude -p --dangerously-skip-permissions'`
  - Codex: start `codex` in the kit folder and type the line above. For batch runs, `AGENT_CMD='codex exec --full-auto'`
  - Hermes Agent or other agents: type the line interactively. For batch runs, put that agent's "run once and exit" command in `AGENT_CMD`
  - Use permission-skipping settings only on the premise that the agent touches only the work folder and Archicad. Check each agent's documentation for the exact syntax.
- "Do not use session_search, honcho, delegate" in the prompts are tool names of the experiment's agent. For other agents read it as "do not use memory or past conversations" (ignoring it also works).
- Operating tips and the review procedure are in `skills/` ([skills/README.en.md](skills/README.en.md), including how to hand them to an agent).

### Time taken (from the experiment logs; estimates)

| Step | Time | Source |
| --- | --- | --- |
| Build the house (`01_`) | ~14 min | screen recording |
| Layout and grid (`02_`) | ~18 min | batch-run log (start/end times) |
| Draw 8 sheets (`10_`–`17_`) | ~2 h 50 min (sections 30–35 min each, elevations 14–19, plans 12–26) | same |
| One round of fixes | 5–30 min per sheet; ~1–1.5 h per round | same; a plan once stopped at the 30-min cap |
| Model fix | each script a few seconds to tens of seconds | — |

Most of the time is the AI thinking. More rule items make it longer.

## Contents

- `README.md` / `README.en.md` (for architects), `AI_GUIDE.md` / `AI_GUIDE.en.md` (index for AIs), `TECHNICAL.md` / `TECHNICAL.en.md` (this file)
- `inputs/`
  - `rhino_house.py`: the source house (a Rhino script, units mm). Same house as the previous experiment "[Exterior image only vs image + drawings](../2026-11_image-vs-drawing-3d/README.en.md)", with windows and finishes added
  - `rhino_house.jpg`: what it looks like
  - `layout_1F.jpg`, `layout_2F.jpg`: layout drawings (fictional; used by the prompt that adds partitions, rooms and the stair)
- `prompts/`
  - The experiment's prompts (`01_`, `02_`, `03_`, `04_`, `10_`–`17_`, `20_`–`25_`): exactly the files given as one line to a new conversation in the experiment. The only differences: the experiment's folder location replaced by `<KIT>/`, and the Archicad version number removed (see "Check against the original prompts" below)
  - Script-only prompts (`00_prepare`, `05_sections`, `06_fix_model`, `18_export`): added for the public kit. They only run the scripts the experimenter's AI ran directly, in the same order with the same arguments, show the output, and stop on error (`check_connection.py` and `prepare_workdir.py` in `00_prepare` are scripts newly written for the kit)
  - `30_inspect_and_fix`: added (not used in the experiment). Puts into words the review and fix-prompt writing the experimenter's AI did
- `rules/`: drawing rules (elevation, plan, section; in Japanese — see [rules/README.en.md](rules/README.en.md)). The AI drew using only these and information readable from Archicad
- `skills/`: knowledge handed to AI agents (guide to the drawing rules, [Archicad operating tips](skills/archicad-operation.md), [how to review and write fix prompts](skills/inspection.md))
- `scripts/`
  - `tapir_http.py`: minimal client sending Archicad JSON API + Tapir commands
  - Setup and running: `check_connection.py` (connection check; `--scan` to find the port; `--count` to check the project is blank; `--save`), `prepare_workdir.py` (work folder), `setup_stories.py` (stories), `make_sections.py` (elevation/section lines; `shoot` exports the 6 views), `run_sheets.sh` (hands prompts one by one to a fresh agent and saves)
  - Model fix (same order as the experiment): `fixA_snapshot.py` → `fixA_comps.py` → `fixA_walls.py` → `fixA_slabs.py --apply` → `fixA_found.py` → `fixA_raise.py` → `fixA_del2d.py --apply`. `layer_found.py` comes after the 8 sheets, before export
  - Export: `export_png.py` (8 sheets as high-res PNG and text; hides the below-ground layer for elevations and plans)
  - Added (not used in the experiment): `check_levels.py` (checks level notation), `check_grid.py` (checks the grid file and normalizes its format). Used by `30_inspect_and_fix`
  - `grid.json`: grid lines the AI fixed in the layout step of the experiment (record; can be put into the work folder with `prepare_workdir.py --with-grid`)
  - `record/walls_before_fixA.json`: the experiment model's wall snapshot before the fix (record; element IDs are specific to that model and cannot be used for another)
- `results/`: the final 8 sheets (`1_P1`–`8_EW`), section before/after (`sa_before_after.jpg`), south elevation without/with skill (`noskill_vs_skill.jpg`; 14 November, slightly earlier house)
- `images/`: README images (`step_house_data.jpg` = the inputs side by side; `step_sheet_detail.jpg` = a crop of `results/3_SA.jpg`)

### Where the scripts came from

| Script | Origin |
| --- | --- |
| `fixA_comps.py`, `fixA_walls.py`, `fixA_found.py`, `tapir_http.py` | Used in the experiment (only paths and port generalized) |
| `layer_found.py` | Used in the experiment, plus "move slabs, site and basin to the same layer" which was later done with short commands, merged into one |
| `make_sections.py`, `export_png.py`, `setup_stories.py`, `fixA_del2d.py` | Generalized from scripts used before/after the experiment (find windows by name instead of ID; paths and capture range as arguments; the plan part of `fixA_del2d.py` reconstructed) |
| `fixA_snapshot.py`, `fixA_raise.py` | Run as short commands in the experiment; extracted from the logs into files (only the choice of slabs to restore changed from IDs to a rule) |
| `fixA_slabs.py` | Reconstructed. The original specified slabs by element ID; this applies the same classification with height/extent rules (verified to give the same classification on the logged values) |
| `run_sheets.sh` | The experiment's batch-run script, made usable with any agent |
| `check_connection.py`, `prepare_workdir.py`, `check_levels.py`, `check_grid.py` | Newly written for publication |

The rewritten scripts have only been syntax-checked and test-run in the parts that do not use Archicad (work-folder creation, plan display, text matching, grid-file normalization). They have not been run against Archicad.

## Used

- Archicad
- Tapir (Archicad add-on adding commands to the JSON API; port 19723)
- AI: Claude Opus 5.5 (run in the AI agent Hermes Agent)
- Dates: 15–16 November 2026
- Image post-processing: Python 3 + Pillow

## Flow (the order actually followed)

| # | What was done | Prompt | Recording / time |
| --- | --- | --- | --- |
| 1 | In a blank Archicad project, read the Rhino house (script and image) and build exterior walls, slabs, roof, windows and doors one by one | `01_model_M.md` | recorded, ~14 min |
| 2 | Add partitions, interior doors, stair and rooms; fix one set of grid lines (`grid.json`) | `02_interior_I.md` | not recorded |
| 3 | Finish the south elevation with the drawing rules, including lines and fills | `03_south_elevation_recorded.md` + `rules/作図ルール_立面.md` (version at that time) | recorded, ~10 min |
| 4 | Draw the remaining sheets. Midway, fix a partition that pierced the roof, delete the 2D and redraw | `04_fix_partition_F.md` | not recorded |
| 5 | Sections were weak, so Hermes fixed the model (see "Model fix" below). Order: wall snapshot → `fixA_comps` → `fixA_walls` → `fixA_slabs` → `fixA_found` → whole house +0.1 (`fixA_raise`) → save → delete the earlier round's 2D (`fixA_del2d`) | `scripts/` | not recorded; ~12 min in all |
| 6 | Write new section rules and redraw the 8 sheets, each in a new conversation, in the order A-A → B-B → south → north → east → west → ground floor → first floor; SaveProject from outside after each | `12_sheet_SA.md` → … → `11_sheet_P2.md` | not recorded; ~2 h 50 min |
| 7 | Export and review. Below-ground lines showed in elevations/plans, so `layer_found.py` moved them to their own layer and the sheets were exported again | `scripts/` | not recorded |
| 8 | Compare with the actual office drawings; Hermes wrote fix prompts and gave them to the AI (between the 3rd and 4th round, the section markers' Reference IDs were changed to A/B in the GUI) | `20_`–`25_` (examples) | not recorded |

The kit's steps (the table in the README) are this flow without 3 and 4 (drawing before the model fix, and the fix made during it). In the experiment, the blank project was the previous model of this house saved under a new name and emptied; its stories (1FL/2FL/RFL) and elevation/section lines were reused. The kit creates the same stories with `setup_stories.py` and the same lines with `make_sections.py create` (both generalized from the commands sent in that earlier round).

### Check against the original prompts

`01_`, `02_`, `03_`, `04_`, `10_`–`17_` and `20_`–`25_` were compared character by character with the prompt files actually given in the experiment. The only two differences:
- the experiment's folder location (a path on the PC) is replaced by `<KIT>/` (`prepare_workdir.py` puts the work folder's location back);
- the version number after "Archicad" in the first lines is removed.

### Number of fix rounds

- Sections and elevations: 3 (2nd, 3rd and 4th = last; west elevation only 2). The three rounds for section A-A are included as examples (`20_`–`22_`).
- Plans: 2 (2nd and last). The ground-floor plan's 2nd round timed out midway, so it was redone once (`24_`). The ground-floor plan's rounds are included as examples (`23_`–`25_`).
- The fix prompts were written by Hermes after reviewing the sheets by image and numbers, and given to the AI as-is (procedure in [skills/inspection.md](skills/inspection.md)).
- Done by Hermes directly in the Archicad GUI: renamed the section markers to A / B; hid the below-ground (foundation) layer when exporting elevations and plans; removed the small-room area labels the AI had added (which made the sheet harder to read).

### Model fix (flow step 5)

The first sections were weak: the roof was a ~1 m thick block, no foundations, no wall layers (`results/sa_before_after.jpg`).

| Part | After the fix |
| --- | --- |
| Exterior walls | RC150 + insulation 35 + PB (orientation set by detecting the room side) |
| Partitions | PB12.5 + LGS95 + PB12.5 |
| Roof | Split into a slab of protective concrete 60 + insulation 30 + waterproofing 10 + RC200, with separate ceiling and parapet walls |
| First floor | Flooring 15 + raised floor 85 + RC200 |
| Ground floor | Flooring 15 + insulation 85 + RC slab-on-grade 150 + crushed stone 100 (carport: plain concrete slab) |
| Foundations | Stem walls and footings under the exterior walls (bottom GL-850) |
| Heights | All stories raised by 100 so 1FL = GL+100 (site and basin unchanged) |

Heights: 1FL = GL+100, 1CL = GL+2850, 2FL = GL+3250, 2CL = GL+6600, eaves = GL+6900, max height = GL+7600.

## What cannot be reproduced (details)

- **AI output differs every time**: with the same prompts and the same model, lines, text positions and layout details change from run to run. You will not get the same sheets as `results/`. The fix prompts (`20_`–`25_`) were written for the experiment's sheets, so parts will not apply to yours (use them as examples of the format).
- **The professional reference drawings are not published**: the human-drawn drawings used for the rules and the review comparisons cannot be released. For review, use your own office's drawings or the drawing rules in `rules/` as the reference ([skills/inspection.md](skills/inspection.md)).
- **Some steps are GUI-only**: opening a newly created section window once (depending on the version), changing a section marker's Reference ID, choosing whether to restore after a crash.
- **Archicad version/template differences**: material names (e.g. "コンクリート"), layers and pens, and how section windows are named may change with version, language and template. The scripts use the names of the Japanese default template.
- **Judgement in writing fix prompts**: the review procedure is written down, but what counts as serious depends on the reference and on the reviewer (the AI).

## Honest notes (details)

- Only flow step 1 (~14 min) and the south elevation of step 3 (~10 min) were screen-recorded and timed. Other rounds were not recorded. The other values in the time table are estimates from the batch-run logs (start/end times of each round).
- The recorded south elevation is the version before the model fix (before flow step 5). `results/5_ES.jpg` was redrawn after the fix and differs from the recorded sheet.
- All fix prompts were written by Hermes (an AI). To reach the current 8 sheets, sections/elevations were fixed 3 times and plans twice.
- Remaining weak points: the carport wall looks doubled (the model has two walls 0.3 m apart) / slab-corner arcs visible in places on the ground-floor plan / a small white gap at the beam in section A-A / a gap in the foundation at X6.
- Dimensions are 2D lines and text and do not follow model changes (dealt with in the next round).
- Archicad crashed twice while the 8 sheets were drawn in a row. As countermeasures, the project is saved after every sheet and the prompts avoid `GetElementsInDrawOrder`.
- The drawing rules summarize the drafting conventions of professional drawings; no shapes, layouts or numbers were copied. In the public version, the number of source drawings and internal file names were removed (the content of the conventions is the same). The recorded south-elevation round used the version of `rules/作図ルール_立面.md` before the final section "rules added in the 11/16 review".
- The house is fictional. Each was a single trial; results change with other AIs or more runs.
- The script-only prompts (00, 05, 06, 18) and `30_inspect_and_fix` were written for publication. The flow in the README table has not yet been run from start to finish from the public kit.

## Paths

- In the prompts, read `<KIT>/` as the work folder (where the files the prompts read are placed) and `<KITROOT>/` as the kit folder (where `scripts/` is). `python scripts/prepare_workdir.py` creates `work/` inside the kit and does the replacement (safe to rerun; it does not delete `grid.json`, `progress.md` or the saved `.pln`).
- To replace by hand, put the contents of `scripts/tapir_http.py`, `rules/*.md` and `inputs/` directly in one folder and replace `<KIT>/` in the prompts with that folder. The prompts mention `rhino_house.png` and `layout_1F.png`; in this public version they are `.jpg`, so convert them or adjust the names.
- The scripts read and write files in their own folder such as `tapir_http.py`, `fixA_comps.json`, `walls_before_fixA.json` (created when run; listed in `.gitignore`). Exports go to `<KITROOT>/out/` (the `out` folder in the kit).
- Port: taken from the environment variable `ARCHICAD_PORT` → `work/archicad_port.txt` (written by `check_connection.py --scan` with the port it found) → 19723 (`tapir_http.default_port()`). `prepare_workdir.py` replaces "port は 19723" in the prompts with this number.
- `prepare_workdir.py` also creates `work/progress.md` (a progress note). Only `30_inspect_and_fix` uses it.
