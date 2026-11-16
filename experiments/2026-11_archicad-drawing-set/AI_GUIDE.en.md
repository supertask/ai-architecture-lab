[🇯🇵 日本語](AI_GUIDE.md) | 🇺🇸 English

# AI_GUIDE: index for AI agents reproducing this experiment

You (an AI agent) use this folder (the **kit**) to reproduce, together with an architect user:
"build a house in a blank Archicad project, draw 8 sheets following the drawing rules, then review and fix them".

**The procedure lives in the prompt files in `prompts/`.** At each step the user pastes a line of the form
"Read `<prompt file>` and follow its instructions." (or the Japanese 「`<file>` を読んで、指示どおりに作業してください」) into a new conversation.
Each prompt file is self-contained: it checks that the previous step is done, saves, logs, and tells the user the next line to paste.
The prompt files are in Japanese; follow them as written, but **reply to the user in the user's language** (if the user writes in English, answer in English and give the next line in English, e.g. "Read work/prompts/02_interior_I.md and follow its instructions.").
If the user asks without naming a prompt file (e.g. "Read AI_GUIDE and build the house in a blank Archicad"), determine the current step from the table below (read `work/progress.md` if it exists), then read that step's prompt file and proceed.

## Steps and prompt files

| Step | File in the user's one-liner | Content | Human GUI action |
| --- | --- | --- | --- |
| 0 | `prompts/00_prepare.md` | Connection check, create `work/` (`prepare_workdir.py`), set stories and save | Open an empty project (if needed) |
| 1 | `work/prompts/01_model_M.md` | Build the massing (experiment's original prompt + kit additions) | none |
| 2 | `work/prompts/02_interior_I.md` | Layout and grid lines (`work/grid.json`) | none |
| 3 | `work/prompts/05_sections.md` | Elevation and section lines (`make_sections.py`) | Open each of the 6 section windows once |
| 4 | `work/prompts/06_fix_model.md` | Layers, foundations, 1FL = GL+100 (`fixA_*`, `layer_found.py`) | none |
| 5 | `work/prompts/10_all_sheets.md` (or `10_sheet_P1` … `17_sheet_EW` one at a time) | Draw the 8 sheets, saving after each | Reopen Archicad after a crash |
| 6 | `work/prompts/18_rename_and_export.md` | Section marker Reference IDs to A/B; export the 8 sheets (`export_png.py`) | Change the Reference IDs |
| 7 | `work/prompts/30_inspect_and_fix.md` | Review, write fix prompts (`work/prompts/30_fix_*.md`), fix, grow the drawing rules | none (user adds remarks) |

- `work/prompts/` is created by `prepare_workdir.py` in step 0. It replaces `<KIT>` (work folder), `<KITROOT>` (kit) and the port in the prompts with real values. The originals in the kit's `prompts/` are never modified.
- `03_south_elevation_recorded`, `04_fix_partition_F` and `20_`–`25_` are records/examples from the experiment and are not part of the normal sequence (each file explains its use at the end).

## Rules for every step

1. **The user is an architect, not a programmer.** Reply in the user's language, briefly, in architectural terms. Do not show commands, paths or programming jargon (paraphrase when needed).
2. **You run all commands.** Never ask the user to run something.
3. **Ask the user only for GUI actions.** One at a time, with the exact menu path, ending with "Reply 'done' when finished", then wait.
4. **One command stream to Archicad at a time.** Never send from two scripts/agents at once. Ask the user not to touch Archicad while you are sending commands.
5. **Save after every prompt (every sheet)** (`python scripts/check_connection.py --save`) and add one line to `work/progress.md`.
6. **Never fabricate results.** Explain failures plainly and propose the next move.
7. **Touch only the kit and the Archicad project opened for this (house_from_scratch).** `make_sections.py create` deletes every section marker in the project — never run it on another project.
8. "Do not use session_search, honcho, delegate" inside the prompts are tool names of the agent used in the experiment (Hermes Agent). Read it as "do not use memory, past conversations, or hand the work to another AI".
9. If Archicad cannot be reached or Tapir is missing, point the user to the setup page (English https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T#en / Japanese https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T#ja) and stop.

## Resuming

When asked to "continue" or "what's next?", read `work/progress.md`, check the connection with `python scripts/check_connection.py`, then give the user the line for the first unfinished step (or read that prompt and proceed).

## References

- Operating tips (sending commands without crashing, how to write prompts): [skills/archicad-operation.md](skills/archicad-operation.md) (Japanese)
- How to review and write fix prompts: [skills/inspection.md](skills/inspection.md) (Japanese)
- How to hand the knowledge (rules, skills) to an agent: [skills/README.en.md](skills/README.en.md)
- File list, script origins, paths, running by hand: [TECHNICAL.en.md](TECHNICAL.en.md)
