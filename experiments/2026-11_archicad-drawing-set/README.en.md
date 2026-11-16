[🇯🇵 日本語](README.md) | 🇺🇸 English

# One line at a time: an AI builds a house in a blank Archicad project and draws 8 sheets

This is the record of an experiment in which an AI built a fictional house — the "Fair-faced Concrete and Water Basin House" (2-storey RC) — in a blank Archicad project and drew 8 sheets: 2 floor plans, 2 sections and 4 elevations.
Everything you need to try it yourself is in this folder.

**You do not need to write any code.** After a one-time setup, you just paste the "one line" from the table below into the AI, step by step.

![The house and the drawings — all drawn by the AI in Archicad (the 8 sheets)](images/summary.jpg)

## What you get

- A house model built from scratch: walls, slabs, roof, windows, doors, partitions, stair, rooms (zones). Walls and slabs get layered build-ups and foundations so the sections read properly.
- 8 sheets: ground- and first-floor plans, sections A-A and B-B, and the north/south/east/west elevations.

**Giving the AI "drawing rules" brings the sheets closer to professional practice.** Top: without rules; bottom: with rules (the same south elevation, of a slightly earlier version of the house).
With the rules, levels are written uniformly as "▽2FL=GL+3250", grid bubbles appear, and dimensions are measured from the grid lines.

![South elevation without rules (top) and with rules (bottom)](results/noskill_vs_skill.jpg)

## What you need

- **Archicad** (tested with the Japanese version and its standard template — see "What will not be identical")
- **An AI**, one of these (both are paid plans):
  - a paid Claude plan + Claude Code (desktop app)
  - a paid ChatGPT plan + Codex (desktop app)
- **One-time setup (30–60 min)**: copy the "prompt for the AI" from the setup page below and paste it into the AI. The AI installs and connects what is needed to drive Archicad from the AI (the Tapir add-on, etc.).
  - Setup page: https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T#en
  - Workshop slides (Japanese): https://docs.google.com/presentation/d/11fd7nvZPuE5BPmIBTQYlUanp_OZPNibPhbAnpD_UStg/edit?usp=sharing
- **You do not need Rhino.** The house data is written as a Rhino script, but the AI only reads the numbers in it.

## Getting started (once)

1. **Get this folder**: on this GitHub page, click the green "Code" button → "Download ZIP". Unzip it and put the folder "experiments" → "2026-11_archicad-drawing-set" somewhere easy to find. (You can also ask the AI: "Download supertask/ai-architecture-lab from GitHub".)
2. **Start Archicad and open a new, empty project** (File › New).
3. **In the AI app, choose the folder from step 1 as the working folder** (apps call it "Open folder", "Add project", etc.). Always start your conversations in this folder.

## How to run it: paste one line per step

In the experiment, too, every step was run by **pasting a single line — "Read <file>.md and follow its instructions" — into a fresh AI conversation**. The only difference is that the experiment used the Hermes Agent AI agent; you use Claude Code or Codex.
Start a **new conversation** for each step and paste the line below (so the AI does not reuse values from the previous sheet). At the end of each step, the AI tells you the next line to paste.

| Step | Line to paste | What happens | What you do | Time |
| --- | --- | --- | --- | --- |
| 0 | `Read prompts/00_prepare.md and follow its instructions.` | Checks the connection, creates the work folder, sets the stories (1FL/2FL/RFL) and saves | Open an empty project if asked | a few min |
| 1 | `Read work/prompts/01_model_M.md and follow its instructions.` | Places exterior walls, slabs, roof, windows and doors one by one | Wait | ~14 min |
| 2 | `Read work/prompts/02_interior_I.md and follow its instructions.` | Partitions, doors, stair, rooms; fixes one set of grid lines | Wait | ~18 min |
| 3 | `Read work/prompts/05_sections.md and follow its instructions.` | Creates the 4 elevation and 2 section lines | **Open each of the 6 section windows once** (the AI tells you how) | 5–10 min |
| 4 | `Read work/prompts/06_fix_model.md and follow its instructions.` | Layered walls/slabs/roof, foundations, 1FL = GL+100 | Wait | 5–15 min |
| 5 | `Read work/prompts/10_all_sheets.md and follow its instructions.` | Draws the 8 sheets one at a time, saving after each | Wait (reopen Archicad if it crashes) | ~3 h |
| 6 | `Read work/prompts/18_rename_and_export.md and follow its instructions.` | Renames the section markers to A/B, exports the 8 sheets as images | **Rename the section markers** (the AI tells you how) | 5–10 min |
| 7 | `Read work/prompts/30_inspect_and_fix.md and follow its instructions.` | Reviews the sheets, writes fix instructions, fixes them (one round) | Add anything you noticed; 2–3 rounds | ~1–1.5 h per round |

- Step 5 can also be done one sheet at a time: `work/prompts/10_sheet_P1.md` → `11_sheet_P2` → `12_sheet_SA` → `13_sheet_SB` → `14_sheet_ES` → `15_sheet_EN` → `16_sheet_EE` → `17_sheet_EW` (each as "Read … and follow its instructions."). That is how the experiment ran.
- In step 7, add what you noticed in plain words after the line. Example: `Read work/prompts/30_inspect_and_fix.md and follow its instructions. In section A-A, the blue waterproofing line runs up over the parapet coping.`
- The experiment's prompts (01, 02, 10–17 and the fix examples 20–25) are kept verbatim (in Japanese — the AI reads them fine), with a "kit additions" section appended at the end (pre-checks, saving, the next line). The prompts for steps 0, 3, 4, 5 (all sheets), 6 and 7 (00, 05, 06, 10_all_sheets, 18, 30) were written for the public kit: they put into words what the experimenter's AI did directly, so that one line is enough. **This new chain of prompts has not yet been run end-to-end** (see "Honest notes").

## What happens in each step

### ① Build the house (steps 0–2)

The house data the AI reads is in the `inputs` folder: left, the exterior (a house built in Rhino); middle and right, the ground- and first-floor layout drawings (all fictional).

![House data the AI reads: exterior and the two floor layouts](images/step_house_data.jpg)

- **What the AI does**: in step 0 it checks that Archicad is connected, creates the work folder (`work`), sets the stories to 1FL/2FL/RFL and saves the project as "house_from_scratch". In step 1 it reads the numbers in the house data and places, one at a time: ground-floor walls → first-floor walls → slabs/roof/ground → windows/doors. In step 2 it looks at the layout drawings, adds partitions, doors, the stair and rooms, then fixes one set of grid lines and writes them to a file.
- **What you see**: in Archicad's 3D window the house goes up piece by piece. The AI prints one line per stage, e.g. "Creating the ground-floor walls".
- **How to tell it finished correctly**
  - [ ] In 3D you see exterior walls, the first-floor slab, roof, windows, entrance door, carport and ground (step 1)
  - [ ] The floor plan shows partitions, doors, the stair and room names (step 2)
  - [ ] The AI wrote "完了" (done) and told you the next line

### ② Draw the sheets (steps 3–6)

![Section before (top) and after (bottom) the model fix. Step 4 adds layers and foundations before drawing](results/sa_before_after.jpg)

- **What the AI does**: step 3 draws four elevation lines outside the building plus section lines A-A and B-B. Step 4 turns walls, slabs and roof into layered (composite) elements, adds foundations, and raises the whole house by 100 so that 1FL = GL+100 (figure above — in the experiment the roof was first a ~1 m thick solid block with no foundations, a "stage prop"). Step 5 reads the drawing rules for each sheet type and draws grid lines, dimensions, levels, room labels, fills and so on. Step 6 renames the section markers on the plans to A/B and exports the 8 sheets as images.
- **What you see**: Archicad switches between section/elevation windows and plans; lines and texts are added type by type. Below is part of the finished section A-A.

![Part of the finished section A-A (build-up notes, levels, dimensions)](images/step_sheet_detail.jpg)

- **What you do (twice, a few minutes each)**: the AI asks you, with the exact menu path. Reply "done" when finished.
  - Step 3: in the Navigator, Project Map → Sections, double-click each of the 6 sections (S南 = south, S東 = east, S北 = north, S西 = west, A-A, B-B) once to open it
  - Step 6: right-click "A-A" / "B-B" → rename the section and set the Reference ID to A / B
- **How to tell it finished correctly**
  - [ ] After step 4, the A-A section image the AI shows has layer lines in roof, slabs and walls, and foundations are visible
  - [ ] Each of the 8 sheets reported "完了" (the AI tells you after each sheet)
  - [ ] The folder `out` → `png` contains the 8 images `hi_P1.png` … `hi_EW.png`; levels read like "▽2FL=GL+3250"; grid bubbles with names are present

### ③ Review and fix (step 7)

- **What the AI does**: checks the 8 sheets by image and by numbers (do the level numbers match the model, do the dimension strings add up to the overall length, do texts overlap). It compares them with the drawing rules, writes fix instructions per sheet and fixes them one at a time. Each mistake found is added to the "previous mistakes" section of the drawing rules.
- **What you do**: add, in plain words, what you want fixed. Read the report and decide whether to do another round.
- **How to tell it finished correctly**
  - [ ] The report separates "fixed" from "remaining"; what remains is only matters of taste or minor items
  - [ ] Stop after 2–3 rounds (each round introduces new small shifts)

## Troubleshooting (what to tell the AI)

| Situation | What to say / do |
| --- | --- |
| The AI says "Archicad not found" or mentions a "port" | Make sure Archicad is running with a project open, then paste the same line again. If it still fails, the one-time setup (setup page) is not done yet. |
| Archicad crashed | Restart Archicad and open "house_from_scratch" in the `work` folder (answer "No" if asked to restore). Paste the same line in a new conversation. It continues from the last save. |
| Texts or lines overlap on a sheet | Add the location and what you see after the step-7 line. Example: "On the ground-floor plan, the carport area text overlaps grid line X5." |
| The AI stopped midway / hit its usage limit | Wait, then paste the same line in a new conversation. Finished parts are skipped using the log (`work/progress.md`). |
| Continuing the next day | Open "house_from_scratch" in Archicad and paste the last line the AI gave you into a new conversation. If you lost track, ask: "Read work/progress.md and tell me the next line to paste." |
| The AI asks "may I run this command?" | It is asking permission to run working programs inside this folder. Review and allow. |

## Time and cost

| Request | AI working time (from the experiment logs) |
| --- | --- |
| ① Build the house | Massing ~14 min + layout ~18 min |
| ② Draw the sheets | Lines and layer/foundation fix 10–25 min + 8 sheets ~2 h 50 min (sections 30–35 min each, elevations 14–19 min, plans 12–26 min) |
| ③ Review and fix | ~1–1.5 h per round (5–30 min per sheet); 2–3 rounds in the experiment |

Most of the time is the AI thinking; you just wait. The AI runs within your Claude or ChatGPT plan. The work is long, so depending on your plan you may hit the usage limit midway; if so, wait and paste the same line again.

## What will not be identical

- **AI answers differ every time.** Positions of lines and texts, and layout details, change from run to run. You will not get the same sheets as shown here.
- **The professional drawings used as references are not published.** Only the text of the "drawing rules" distilled from them is included.
- **A different Archicad language or template may stop the run.** Material names (e.g. "コンクリート", concrete) are those of the Japanese standard template.

## Use it in your own office

The drawing rules given to the AI are **plain Japanese prose** in the `rules` folder — not code ([rules/README.en.md](rules/README.en.md) explains each file in English). For example, the section rule says (translated):

> **Levels**
> - Format: ▽Name=GL+number (no comma, no unit). GL is written △GL.
> - For ▽ (tops: max height, eaves, each FL) the text sits above the line; for △ (ceiling CL and GL) below the line.
>
> **Ground**: GL as a thin solid line extending well beyond both sides of the building. Outside the building, a ~1 m wide band of earth hatching below GL (not under the building).

**Rewrite these to match how your office draws, and they become your office's skill (a procedure document for the AI).** You can ask the AI to do the rewriting:

```
Rewrite the section rules in the rules folder to match how this office draws sections, in English. Use the PDF I put in this folder as the reference. Do not copy shapes or layouts — describe only how things are drawn.
```

**Growing the rules**: have the AI draw, review, and append each mistake to the "previous mistakes" section at the end of the rule (in step 7 the AI does this itself). In the experiment, for example, these were added (translated):

> - Drew the blue waterproofing line on top of the parapet coping and on the top of boxes seen beyond. → The blue line goes only on the RC top of the cut roof slab and up the inner face of the parapet; stop below the coping.
> - Small dimensions (300, 400, 100) overlapped the dash-dot level lines. → Pull them out and write them in a free space.

Rules are followed better when the AI gets only the rules for the sheet type it is drawing, rather than all of them at once (each step's prompt does this).

## Honest notes

- **The one-line-per-step flow**: in the experiment, each step was actually run by pasting one line "Read ….md and …" into a fresh conversation of an AI (Hermes Agent + Claude Opus 5.5) — prompts 01, 02, 10–17 and 20–25. The steps added for the public kit (00, 05, 06, 10_all_sheets, 18, 30) put into words work that the experimenter's AI did directly; **they have not been run end-to-end in Archicad in this form**, and have not been tried with Claude Code or Codex. Please tell us where you get stuck.
- Only two parts were screen-recorded and timed: building the massing (~14 min) and one south elevation (~10 min). The other times are estimates from start/end timestamps. The recorded south elevation predates the layer/foundation fix and differs from the south elevation among the 8 sheets above.
- Before the 8 sheets reached their current state, sections and elevations were fixed 3 times and plans twice. They were not right first time.
- The review and fix instructions were written by the AI agent used in the experiment (Hermes Agent — a tool that lets an AI work on a computer). The same AI also did the model fix (layers and foundations).
  Besides the lines drawn by the AI, Hermes changed three things directly in Archicad: renamed the section markers to A/B; hid the below-ground (foundation) layer when exporting elevations and plans; removed area labels the AI had added to small rooms (which made them harder to read).
- Remaining weak points: the carport wall looks doubled / slab-corner arcs are visible on the ground-floor plan / a small white gap at the beam in section A-A / a gap in the foundation at grid X6.
- Dimensions are drawn as lines and text; they do not follow model changes (the next experiment deals with this).
- Archicad crashed twice while drawing the 8 sheets in a row. That is why the project is saved after every sheet.
- The drawing rules summarize only drafting conventions of professional drawings; no shapes, plans or numbers were copied. The house is fictional. Each was a single trial; results change with other AIs or more runs.
- Used: AI Claude Opus 5.5 (via Hermes Agent); software Archicad and Tapir. 15–16 November 2026.

## For advanced users and AIs

- [AI_GUIDE.en.md](AI_GUIDE.en.md): index for AI agents (prompt files per step and shared rules)
- [prompts/](prompts/): the prompt for each step (the files the AI reads from the one-liners above; in Japanese)
- [TECHNICAL.en.md](TECHNICAL.en.md): file list, step details, how the model was fixed, where the scripts (small programs written by the AI) came from
- [skills/](skills/README.en.md): tips for driving Archicad and how to review drawings (for AIs)
- [rules/](rules/README.en.md): drawing rules (plans, sections, elevations)
- Draft of the explanatory article (Japanese): [docs/2026-11-16-archicad-drawing-set.md](../../docs/2026-11-16-archicad-drawing-set.md)
