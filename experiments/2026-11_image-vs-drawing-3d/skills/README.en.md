[🇯🇵 日本語](README.md) | 🇺🇸 English

# Skills (procedure documents for AI agents)

The working procedures the AI used in this experiment, written so they do not depend on a particular environment.
Any agent — Claude Code, Codex, Hermes Agent, etc. — can use them if you say "read this file before working". The files are in Japanese; AI agents read them fine.

| File | When to use |
| --- | --- |
| [input-comparison-experiment.md](input-comparison-experiment.md) | Running and scoring this experiment itself (image only vs image + drawings) fairly |
| [image-to-massing.md](image-to-massing.md) | Building a Rhino volume model from an exterior image (AI image or photo) |
| [figma-drawing-markup-loop.md](figma-drawing-markup-loop.md) | The loop where the AI puts a drawing draft on Figma, a human marks it up with a pen, and the AI draws the next version |
| [pbr-texture-pipeline.md](pbr-texture-pipeline.md) | Generating material colour with an image-generation AI and completing normal / roughness / AO maps (with tips to hide repetition) |

## How to use

- If your agent has a "skills" feature (Claude Code skills, Hermes skills, etc.), put the files in that folder.
- If not, start the instruction with "Read `skills/image-to-massing.md` before working".
- **When running the A/B comparison, do not give skills to the AI that builds the models** (it changes the conditions). Skills are for the AI that prepares, scores, or makes the drawings.

## Notes

- Tool names in the files (`execute_rhino_code`, Figma's `use_figma`, etc.) differ depending on how you connect. Map them to the tools with the same function in your environment.
- Procedures verified with the AI of November 2026 (Claude Opus 5.5).
