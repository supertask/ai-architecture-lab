[🇯🇵 日本語](AI_GUIDE.md) | 🇺🇸 English

# AI_GUIDE: index for AI agents reproducing this experiment

You (an AI agent) use this folder (the **kit**) to reproduce, together with an architect user:
"build a house in a blank Archicad project, draw 8 sheets following the drawing rules, then review and fix them".

**The procedure lives in the prompt files in `prompts/`.** At each step the user pastes a line of the form
"Read `<prompt file>` and follow its instructions." (or the Japanese 「`<file>` を読んで、指示どおりに作業してください」) into a new conversation.
Do only what the prompt file says. The order of steps, saving, and the next line to paste are handled by the user from the table in [README.en.md](README.en.md) (they are not in the prompt files).
The prompt files are in Japanese; follow them as written, but reply to the user in the user's language.
If the user asks without naming a prompt file, show them the README table and ask which step to start from.

## Prompt files and "In the experiment"

| Step (README table) | File | Content | In the experiment |
| --- | --- | --- | --- |
| 1 | `prompts/00_prepare.md` | Only runs `check_connection.py --scan` → `prepare_workdir.py` → `setup_stories.py work/house_from_scratch.pln` | Added (not used) |
| 2 | `work/prompts/01_model_M.md` | Build the massing | Same prompt, run as-is |
| 3 | `work/prompts/02_interior_I.md` | Layout and grid lines (`work/grid.json`) | Same prompt, run as-is |
| 4 | `work/prompts/05_sections.md` | Only runs `make_sections.py create` | Same scripts run (prompt newly added) |
| 6 | `work/prompts/06_fix_model.md` | Only runs `fixA_snapshot` → `fixA_comps` → `fixA_walls` → `fixA_slabs --apply` → `fixA_found` → `fixA_raise` → `fixA_del2d --apply` | Same scripts run (prompt newly added) |
| 7 | `work/prompts/12_sheet_SA` → `13_sheet_SB` → `14_sheet_ES` → `15_sheet_EN` → `16_sheet_EE` → `17_sheet_EW` → `10_sheet_P1` → `11_sheet_P2` | Draw one sheet each | Same prompt, run as-is |
| 9 | `work/prompts/18_export.md` | Only runs `layer_found.py` → `export_png.py` | Same scripts run (prompt newly added) |
| 10 | `work/prompts/30_inspect_and_fix.md` | Review, write fix prompts, fix | Added (not used) |
| record | `03_south_elevation_recorded`, `04_fix_partition_F` | Records of experiment rounds | Same prompt, run as-is |
| record | `20_`–`25_` | Records of the experiment's fixes (written for the mistakes of that run; they often will not apply to your result) | Same prompt, run as-is |

Steps 0, 5 and 8 are done by a person in the Archicad GUI (open an empty project; open the 6 section windows once; change the section markers' Reference IDs to A/B).

- `work/prompts/` is created by `prepare_workdir.py` in step 1. It replaces `<KIT>` (work folder), `<KITROOT>` (kit) and the port in the prompts with real values. The originals in the kit's `prompts/` are never modified.
- "Do not use session_search, honcho, delegate" inside the prompts are tool names of the agent used in the experiment (Hermes Agent). Read it as "do not use memory, past conversations, or hand the work to another AI".
- Never fabricate results. If a script fails, show its output as-is and stop.
- One command stream to Archicad at a time. Never send from two scripts/agents at once.
- If Archicad cannot be reached or Tapir is missing, point the user to the setup page (English https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T#en / Japanese https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T#ja) and stop.

## References

- Operating tips (sending commands without crashing, how to write prompts): [skills/archicad-operation.md](skills/archicad-operation.md) (Japanese)
- How to review and write fix prompts: [skills/inspection.md](skills/inspection.md) (Japanese)
- How to hand the knowledge (rules, skills) to an agent: [skills/README.en.md](skills/README.en.md)
- File list, the order actually followed, script origins, paths: [TECHNICAL.en.md](TECHNICAL.en.md)
