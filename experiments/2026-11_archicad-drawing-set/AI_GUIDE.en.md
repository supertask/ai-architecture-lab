[🇯🇵 日本語](AI_GUIDE.md) | 🇺🇸 English

# AI_GUIDE: guide for AI agents reproducing this experiment

You (an AI agent) use this folder (the **kit**) to reproduce, together with an architect user:
"build a house in a blank Archicad project, draw 8 sheets following the drawing rules, then review and fix them".
The human-facing description is [README.en.md](README.en.md). Everything an AI needs (files, commands, what was actually done in the experiment, troubleshooting) is in this file.

House: the fictional "Fair-faced Concrete and Water Basin House" (2-storey RC, 18,000 × 11,100, grid X1–X6 / Y1–Y4).

## 1. How to work

**The procedure lives in the prompt files in `prompts/`.** At each step the user pastes a line of the form
"Read `<prompt file>` and follow its instructions." (or the Japanese 「`<file>` を読んで、指示どおりに作業してください」) into a new conversation.
Do only what the prompt file says. The order of steps, saving, and the next line to paste are handled by the user from the table in [README.en.md](README.en.md) (they are not in the prompt files).
The prompt files are in Japanese; follow them as written, but reply to the user in the user's language.
If the user asks without naming a prompt file, show them the README table and ask which step to start from.

- **Never fabricate results.** If a script fails, show its output as-is and stop.
- **One command stream to Archicad at a time.** Never send from two scripts/agents at once.
- "Do not use session_search, honcho, delegate" inside the prompts are tool names of the agent used in the experiment (Hermes Agent). Read it as "do not use memory, past conversations, or hand the work to another AI" (ignore it if you have no such tools).
- If Archicad cannot be reached or Tapir is missing, point the user to the setup page (English https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T#en / Japanese https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T#ja) and stop.

## 2. Steps and prompt files

| Step (README table) | File | Content | In the experiment |
| --- | --- | --- | --- |
| 0 | (person: File › New in Archicad) | Open an empty project | Done by hand |
| 1 | `prompts/00_prepare.md` | Only runs `check_connection.py --scan` → `prepare_workdir.py` → `setup_stories.py work/house_from_scratch.pln` | Added (not used) |
| 2 | `work/prompts/01_model_M.md` | Build the massing | Same prompt, run as-is |
| 3 | `work/prompts/02_interior_I.md` | Layout and grid lines (`work/grid.json`) | Same prompt, run as-is |
| 4 | `work/prompts/05_sections.md` | Only runs `make_sections.py create` | Same scripts run (prompt newly added) |
| 5 | (person: open the 6 section windows once each) | S-south, S-east, S-north, S-west, A-A, B-B | Done by hand |
| 6 | `work/prompts/06_fix_model.md` | Only runs `fixA_snapshot` → `fixA_comps` → `fixA_walls` → `fixA_slabs --apply` → `fixA_found` → `fixA_raise` → `fixA_del2d --apply` | Same scripts run (prompt newly added) |
| 7 | `work/prompts/12_sheet_SA` → `13_sheet_SB` → `14_sheet_ES` → `15_sheet_EN` → `16_sheet_EE` → `17_sheet_EW` → `10_sheet_P1` → `11_sheet_P2` | Draw one sheet each (each in a new conversation, save after each) | Same prompt, run as-is (this order) |
| 8 | (person: section markers' Reference IDs to A/B) | Rename "S-01 A-A" / "S-01 B-B" in the Navigator | Done by hand |
| 9 | `work/prompts/18_export.md` | Only runs `layer_found.py` → `export_png.py` | Same scripts run (prompt newly added) |
| 10 | `work/prompts/30_inspect_and_fix.md` | Review, write fix prompts, fix | Added (not used) |
| record | `03_south_elevation_recorded`, `04_fix_partition_F` | Records of experiment rounds (not in the normal order) | Same prompt, run as-is |
| record | `20_`–`25_` | Records of the experiment's fixes (written for the mistakes of that run; they often will not apply to your result; use them as examples of the format) | Same prompt, run as-is |

- `work/prompts/` is created by `prepare_workdir.py` in step 1. It replaces `<KIT>` (work folder), `<KITROOT>` (kit) and "port は 19723" in the prompts with real values. The originals in the kit's `prompts/` are never modified.
- The script-only prompts (`00_prepare`, `05_sections`, `06_fix_model`, `18_export`) just run the commands in "4. Command order" below and show the output. Running them by hand is the same.

## 3. Files and scripts

- `README.md` / `README.en.md`: for people (architects). `AI_GUIDE.md` / `AI_GUIDE.en.md`: this file
- `inputs/`
  - `rhino_house.py`: the source house (a Rhino script, units mm). The AI only reads the numbers; Rhino is not needed. Same house as the previous experiment "[Exterior image only vs image + drawings](../2026-11_image-vs-drawing-3d/README.en.md)", with windows and finishes added
  - `rhino_house.jpg`: what it looks like
  - `layout_1F.jpg`, `layout_2F.jpg`: layout drawings (fictional; used by `02_interior_I`)
- `prompts/`: the prompt files in the table above
- `rules/`: drawing rules (elevation, plan, section; in Japanese — see [rules/README.en.md](rules/README.en.md)). The drawing AI uses only these and information readable from Archicad
- `skills/`: knowledge handed to AI agents ([skills/README.en.md](skills/README.en.md), [Archicad operating tips](skills/archicad-operation.md), [how to review and write fix prompts](skills/inspection.md))
- `results/`: the experiment's final 8 sheets (`1_P1`–`8_EW`), section before/after (`sa_before_after.jpg`), south elevation without/with drawing rules (`noskill_vs_skill.jpg`; slightly earlier house). **Published results — do not overwrite.**
- `images/`: README images
- `scripts/`:

| Script | Purpose |
| --- | --- |
| `tapir_http.py` | Minimal client sending Archicad JSON API + Tapir commands over HTTP (no MCP). `default_port()` picks the port |
| `check_connection.py` | Connection check. `--scan` finds the port and writes `work/archicad_port.txt`; `--count` checks the project is blank; `--save` saves |
| `prepare_workdir.py` | Creates `work/`, with `work/prompts/` (`<KIT>`, `<KITROOT>`, port replaced) and `work/progress.md`. `--with-grid` also copies the recorded `grid.json` |
| `setup_stories.py <pln>` | Sets stories to 1FL/2FL/RFL and saves to the given path |
| `make_sections.py create` / `shoot` | `create`: 4 elevation lines and section lines A-A / B-B (`--aa-y`, `--bb-x`, `--margin`). `shoot`: exports the 6 views as images |
| `fixA_snapshot.py` | Takes the pre-fix wall snapshot `walls_before_fixA.json`. Run once, before `fixA_walls.py` (stops if it exists) |
| `fixA_comps.py` | Creates the layered composites. Selects building materials **by index** |
| `fixA_walls.py` | Converts exterior walls/partitions to layered composites and orients the room side |
| `fixA_slabs.py --apply` | Assigns floor/roof slabs to layered composites (without `--apply` it only shows the plan). Material name "コンクリート" |
| `fixA_found.py` | Adds foundations (stem walls and footings) under the exterior walls. Material name "コンクリート" |
| `fixA_raise.py [m]` | Raises the whole house (default 0.1); puts site and basin slabs back. **Running it twice raises twice** |
| `fixA_del2d.py --apply` | Deletes the earlier round's 2D (lines, text) (without `--apply` it only lists) |
| `layer_found.py` | Moves below-ground elements to their own layer and lowers the ground-floor exterior walls' bottom to GL. `hide` / `show` toggles that layer. **Running it twice lowers the wall bottoms twice** |
| `export_png.py` | Exports the 8 sheets as high-res PNG and text (hides the below-ground layer automatically for elevations/plans). Output in `<KITROOT>/out/` |
| `run_sheets.sh` | Hands step-7 prompts one by one to a fresh agent, saving after each (see "5" below) |
| `check_levels.py` | Checks level notation (used by `30_inspect_and_fix`; not used in the experiment) |
| `check_grid.py [path]` | Checks the grid file and normalizes its format (default `work/grid.json`; used by `30_inspect_and_fix`; not used in the experiment) |
| `grid.json` | Grid lines the AI fixed in the experiment's layout step (record) |
| `record/walls_before_fixA.json` | The experiment model's pre-fix wall snapshot (record; element IDs are specific to that model and cannot be used for another) |

Requirements: Python 3 (mostly standard library; `export_png.py` needs Pillow and numpy; `prepare_workdir.py` makes real PNGs if Pillow is present); bash for `run_sheets.sh` (on Windows, e.g. Git Bash).

## 4. Command order

In the kit folder ("person" = an action in the Archicad GUI, "prompt" = one line in a new conversation):

1. Person: open an empty project
2. `python scripts/check_connection.py --scan`
3. `python scripts/prepare_workdir.py`
4. `python scripts/setup_stories.py work/house_from_scratch.pln`
5. Prompt `01_model_M` → save → prompt `02_interior_I` → save
6. `python scripts/make_sections.py create`
7. Person: open each of the 6 section windows once → save
8. `python scripts/fixA_snapshot.py` → `fixA_comps.py` → `fixA_walls.py` → `fixA_slabs.py --apply` → `fixA_found.py` → `fixA_raise.py` → `fixA_del2d.py --apply` → save
9. Prompts `12_`→`13_`→`14_`→`15_`→`16_`→`17_`→`10_`→`11_` (each in a new conversation; save after each; `run_sheets.sh` does the same)
10. Person: Reference IDs to A/B → save
11. `python scripts/layer_found.py` → `python scripts/export_png.py`
12. Prompt `30_inspect_and_fix` (review and fix; stop after 2–3 rounds)

## 5. Using run_sheets.sh

Hands step 7 (or any prompts) one by one to an agent in a new process (= a new conversation) and sends SaveProject from outside after each. Same shape as the experiment's batch run. After step 1, with `work/prompts/` present, from the kit folder:

```
AGENT_CMD='claude -p --dangerously-skip-permissions' bash scripts/run_sheets.sh
AGENT_CMD='codex exec --full-auto' bash scripts/run_sheets.sh
SHEETS='12_sheet_SA 13_sheet_SB' AGENT_CMD='...' bash scripts/run_sheets.sh      # only some
SHEETS='20_fix_SA_round2' AGENT_CMD='...' bash scripts/run_sheets.sh             # fix prompts work too
```

| Variable | Meaning |
| --- | --- |
| `AGENT_CMD` | Required. A non-interactive command that takes one prompt as its last argument and returns when done. The two above are examples (the experiment used Hermes Agent). Check each agent's documentation for the syntax |
| `WORK` | Work folder (default `<KIT>/work`). The agent starts here and receives "`prompts/<name>.md` を読んで、指示どおりに作業してください。" |
| `SHEETS` | Prompts to run (names without `.md`). Default: the 8 sheets in the experiment's order (A-A → B-B → south → north → east → west → ground floor → first floor) |
| `MAX_SEC` | Time cap per prompt in seconds (default 2400 = 40 min). No cap if there is no `timeout` command |
| `PY` | Python (default `python`) |

- Logs go to `work/logs/<name>.txt`.
- Stops if saving fails (Archicad may have crashed).
- Use permission-skipping settings only on the premise that the agent touches only the work folder and Archicad.

## 6. Running the prompts with your own agent

The prompt files (`prompts/*.md`, Japanese) are plain prose, not tied to any agent. Start the agent **in the kit folder** and type one line into a new conversation (only the first, `prompts/00_prepare.md`, is in the kit's prompts; after that, `work/prompts/…`).

- Start the next prompt only after the previous one has finished. A new conversation per prompt prevents reuse of values from the previous sheet (the experiment used 1 prompt = 1 new conversation; its agent was Hermes Agent).
- Examples: Claude Code — start `claude` in the kit folder and type the line. Codex — start `codex` and type it. For batch runs see "5" above.
- Operating tips and the review procedure are in `skills/` (how to hand them to an agent: [skills/README.en.md](skills/README.en.md)).

## 7. Paths and port

- In the prompts, `<KIT>/` is the work folder (where the files the prompts read are placed) and `<KITROOT>/` is the kit folder (where `scripts/` is). `python scripts/prepare_workdir.py` creates `work/` inside the kit and does the replacement (safe to rerun; it does not delete `grid.json`, `progress.md` or the saved `.pln`).
- To replace by hand without `prepare_workdir.py`, put the contents of `scripts/tapir_http.py`, `rules/*.md` and `inputs/` directly in one folder and replace `<KIT>/` in the prompts with that folder. The prompts mention `rhino_house.png` and `layout_1F.png`; in this public version they are `.jpg`, so convert them or adjust the names.
- The scripts read and write files in their own folder such as `tapir_http.py`, `fixA_comps.json`, `walls_before_fixA.json` (created when run; in `.gitignore`). Exports go to `<KITROOT>/out/`.
- Port: environment variable `ARCHICAD_PORT` → `work/archicad_port.txt` (written by `check_connection.py --scan`) → 19723 (`tapir_http.default_port()`). `prepare_workdir.py` replaces "port は 19723" in the prompts with this number.
- `work/progress.md` (a progress note) is used only by `30_inspect_and_fix`.

## 8. What was actually done in the experiment

Dates: 15–16 November 2026. AI: Claude Opus 5.5 (run in Hermes Agent). Archicad (Japanese version, standard template) + Tapir (port 19723).

| # | What was done | Prompt |
| --- | --- | --- |
| 1 | In a blank Archicad project, read the Rhino house (script and image) and build exterior walls, slabs, roof, windows and doors one by one | `01_model_M.md` |
| 2 | Add partitions, interior doors, stair and rooms; fix one set of grid lines (`grid.json`) | `02_interior_I.md` |
| 3 | Finish the south elevation with the drawing rules, including lines and fills (the `rules/作図ルール_立面.md` of that time, before the final section "rules added in the 11/16 review") | `03_south_elevation_recorded.md` |
| 4 | Draw the remaining sheets. Midway, fix a partition that pierced the roof, delete the 2D and redraw | `04_fix_partition_F.md` |
| 5 | Sections were weak, so the experimenter's AI fixed the model: wall snapshot → `fixA_comps` → `fixA_walls` → `fixA_slabs` → `fixA_found` → whole house +0.1 (`fixA_raise`) → save → delete the earlier round's 2D (`fixA_del2d`) | `scripts/` |
| 6 | Write new section rules and redraw the 8 sheets, each in a new conversation (A-A → B-B → south → north → east → west → ground floor → first floor; SaveProject from outside after each) | `12_sheet_SA.md` → … → `11_sheet_P2.md` |
| 7 | Export and review. Below-ground lines showed in elevations/plans, so `layer_found.py` moved them to their own layer and the sheets were exported again | `scripts/` |
| 8 | Compare with the drafting conventions of professional drawings; the experimenter's AI wrote fix prompts and gave them to the drawing AI (between the 3rd and 4th round, the section markers' Reference IDs were changed to A/B in the GUI) | `20_`–`25_` (examples) |

- The kit's steps (README table) are this flow without 3 and 4.
- The experiment's blank project was the previous model of this house saved under a new name and emptied; its stories (1FL/2FL/RFL) and elevation/section lines were reused. The kit creates the same stories with `setup_stories.py` and the same lines with `make_sections.py create` (both generalized from the commands sent in that earlier round).
- Archicad crashed twice while the 8 sheets were drawn in a row. Countermeasures: save after every sheet, and the prompts avoid `GetElementsInDrawOrder`.

### Check against the original prompts

`01_`, `02_`, `03_`, `04_`, `10_`–`17_` and `20_`–`25_` were compared character by character with the prompt files actually given in the experiment. The only three differences:
1. The experiment's folder location (a path on the PC) is replaced by `<KIT>/` (`prepare_workdir.py` puts the work folder's location back).
2. The version number after "Archicad" in the first lines is removed.
3. In `20_`, `23_` and `24_`, the sentence naming what the sheet is compared with was generalized ("実務の図面の描き方（作法）と比べて" = "compared with the drafting conventions of professional drawings").

The script-only prompts (`00_prepare`, `05_sections`, `06_fix_model`, `18_export`) were added for the public kit. They only run the scripts the experimenter's AI ran directly, in the same order with the same arguments, show the output, and stop on error. `30_inspect_and_fix` puts into words the review and fix-prompt writing the experimenter's AI did (not used in the experiment).

### Number of fix rounds

- Sections and elevations: 3 (2nd, 3rd and 4th = last; west elevation only 2). The three rounds for section A-A are included as examples (`20_`–`22_`).
- Plans: 2 (2nd and last). The ground-floor plan's 2nd round timed out midway, so it was redone once (`24_`). The ground-floor plan's rounds are included as examples (`23_`–`25_`).
- The fix prompts were written by the experimenter's AI after reviewing the sheets by image and numbers, and given to the drawing AI as-is (procedure in [skills/inspection.md](skills/inspection.md)).
- Done by the experimenter's AI directly in the Archicad GUI: renamed the section markers to A / B; hid the below-ground (foundation) layer when exporting elevations and plans; removed the small-room area labels the drawing AI had added (which made the sheet harder to read).

### Model fix (inside step 6)

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

Heights after the fix (use them when checking levels): 1FL = GL+100, 1CL = GL+2850, 2FL = GL+3250, 2CL = GL+6600, eaves = GL+6900, max height = GL+7600.

### Weak points left in the experiment's result

If review finds these, they were in the experiment's sheets too: the carport wall looks doubled (the model has two walls 0.3 m apart) / slab-corner arcs visible in places on the ground-floor plan / a small white gap at the beam in section A-A / a gap in the foundation at X6. Dimensions are 2D lines and text and do not follow model changes.

## 9. Script changes for the public kit, and what is untested

| Script | Origin |
| --- | --- |
| `fixA_comps.py`, `fixA_walls.py`, `fixA_found.py`, `tapir_http.py` | Used in the experiment (only paths and port generalized) |
| `layer_found.py` | Used in the experiment, plus "move slabs, site and basin to the same layer" which was later done with short commands, merged into one |
| `make_sections.py`, `export_png.py`, `setup_stories.py`, `fixA_del2d.py` | Generalized from scripts used before/after the experiment (find windows by name instead of ID; paths and capture range as arguments; the plan part of `fixA_del2d.py` reconstructed) |
| `fixA_snapshot.py`, `fixA_raise.py` | Run as short commands in the experiment; extracted from the logs into files (only the choice of slabs to restore changed from IDs to a rule) |
| `fixA_slabs.py` | Reconstructed. The original specified slabs by element ID; this applies the same classification with height/extent rules (verified to give the same classification on the logged values) |
| `run_sheets.sh` | The experiment's batch-run script, made usable with any agent |
| `check_connection.py`, `prepare_workdir.py`, `check_levels.py`, `check_grid.py` | Newly written for publication |

**Untested**
- The rewritten scripts have only been syntax-checked and test-run in the parts that do not use Archicad (work-folder creation, plan display, text matching, grid-file normalization). They have not been run against Archicad.
- The prompts `00_prepare`, `05_sections`, `06_fix_model`, `18_export` and `30_inspect_and_fix` have not been run in this form. The README table's flow has not yet been run from start to finish from the public kit.
- Doing the by-hand steps (0, 5, 8) via the AI's screen control has not been tried either.

If something fails, assume it may be in an untested part: show the output as-is, stop, and confirm with the user how far it got.

## 10. Troubleshooting (what the AI does)

| Situation | What to do |
| --- | --- |
| Cannot connect / wrong port | Have the user confirm Archicad is running with a project open, then rerun `check_connection.py --scan`. If it still fails, point to the setup page and stop |
| Material not found / wrong material | The template is not the Japanese standard one. `fixA_comps.py` selects materials **by index**; `fixA_found.py` and `fixA_slabs.py` by the name "コンクリート". With the user's permission, edit the indices/names at the top of those scripts to match the template's materials |
| Cannot open a section window (ChangeWindow fails) | In some versions a newly created section window cannot be opened by the AI. Check that step 5 (the person opens the 6 windows once in the GUI) was done |
| Need to change a section marker's Reference ID | Not possible from the AI. Ask the user to do step 8 |
| Archicad crashed | Have the user reopen "house_from_scratch" in `work` (answer "No" to restore). Continue from the last save. When drawing in a row, save after every sheet and do not use `GetElementsInDrawOrder` |
| A script failed midway | Before rerunning, check how much was applied. Do not rerun `fixA_raise.py` (raises twice) or `layer_found.py` (lowers wall bottoms twice) |
| `fixA_snapshot.py` stops with "already exists" | Keeping the earlier snapshot is correct. Never retake it after `fixA_walls.py` has run (`--force` only if the fix has not started) |
| A prompt cannot find `rhino_house.png` etc. | The public version has `.jpg`. Adjust the name or convert |
| Below-ground lines appear in exported elevations/plans | Check that `layer_found.py` was run (`layer_found.py hide` hides the layer) |
| Review finds a weak point that was in the experiment too | See "Weak points left in the experiment's result" above. Decide with the user whether to fix it |

## 11. References

- Operating tips (sending commands without crashing, how to write commands): [skills/archicad-operation.md](skills/archicad-operation.md) (Japanese)
- How to review and write fix prompts: [skills/inspection.md](skills/inspection.md) (Japanese)
- How to hand the knowledge (rules, skills) to an agent: [skills/README.en.md](skills/README.en.md)
- Drawing rules: [rules/README.en.md](rules/README.en.md)
