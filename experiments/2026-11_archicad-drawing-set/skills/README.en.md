[🇯🇵 日本語](README.md) | 🇺🇸 English

# skills: the "how to draw" and "how to operate" knowledge handed to AI agents

The kit's knowledge is split into three parts. All are Markdown, so any AI agent can read them as-is. The files themselves are in Japanese; AI agents read them fine.

| Content | File | When to give it |
| --- | --- | --- |
| Drawing rules (how to draw) | `../rules/作図ルール_平面.md` (plans), `作図ルール_断面.md` (sections), `作図ルール_立面.md` (elevations) — see [../rules/README.en.md](../rules/README.en.md) | Drawing rounds. Each prompt (`prompts/10_`–`17_`, `20_`–`25_`) names exactly one rule file for its sheet type |
| Archicad operating tips | `archicad-operation.md` | Every round that drives Archicad through the API. Also contains notes for writing your own prompts |
| How to review and write fix prompts | `inspection.md` | Whoever (human or AI) reviews the finished sheets and writes fix prompts (step 7, `prompts/30_inspect_and_fix.md`) |

- The drawing rules stay in `rules/` (the prompts read them from there; `scripts/prepare_workdir.py` copies them into the work folder).
- The drawing rules summarize the drafting conventions of professional drawings. No shapes, layouts or numbers were copied.
- In the experiment's drawing rounds, the agent was restricted to "use only this prompt, the rule file and information readable from Archicad" (no skills, memory or past conversations). What the drawing rounds need from `archicad-operation.md` is written directly in the prompts (e.g. do not use `GetElementsInDrawOrder`). To reproduce under the same conditions, you do not need to give `archicad-operation.md` to drawing rounds.

## How to hand them to an agent

- **Read once**: write "read `<WORK>/skills/archicad-operation.md` first" in the prompt, or type "read this file before working" at the start of the conversation (`<WORK>` = the work folder).
- **Read every time**: put a link to, or the content of, the file into the agent's "always read" instruction file.
  - Claude Code: `CLAUDE.md` in the working folder, or `.claude/skills/<name>/SKILL.md` (format with name and description at the top)
  - Codex: `AGENTS.md` in the working folder
  - Hermes: register it as a skill (`SKILL.md` format)
  Check each agent's documentation for the format. All of them just read Markdown, so the content can stay as it is.
- **Do not overload the context**: do not give all rules at once. Give only the rules for the sheet type being drawn. Too much context, even if relevant, lowers rule compliance.
