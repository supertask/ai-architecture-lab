[🇯🇵 日本語](AI_GUIDE.md) | 🇺🇸 English

# AI_GUIDE: index for AI agents reproducing this experiment

You (an AI agent) use this folder (the **kit**) to reproduce, together with an architect user:
"have an AI build a Rhino model from one exterior image only (A) / image + drawings (B), and compare each with the correct model by overlap ratio".

**The procedure lives in the prompt files in `prompts/`.** At each step the user pastes a line of the form
"Read `<prompt file>` and follow its instructions." (or the Japanese 「`<file>` を読んで、指示どおりに作業してください」).
The kit's step prompts are in Japanese; follow them as written, but **reply to the user in the user's language** and give the next line in that language.
If the user asks without naming a prompt file, determine the current step from the table below (read `work/progress.md` if it exists), then read that step's prompt file and proceed.

## Most important rule: you, with the kit open, never build the models

The kit contains the answer (`outputs/reference_v14.py`, `scripts/draw_v14.py`, `outputs/`, `run2_recorded/outputs/`, `results/`).
The A and B models are built by an AI in **a new conversation** in separate folders containing only the inputs (`ai-run-A`, `ai-run-B`). Your job is preparation, capture, scoring and explanation. Never tell the user or the model-building AI anything from the answer files (dimensions etc.).

## Steps and prompt files

| Step | Working folder | File in the user's one-liner | Content |
| --- | --- | --- | --- |
| 0 | kit | `prompts/00_prepare_A.md` | Decide the form (build in Rhino / script only); create `../ai-run-A` with `prepare_run.py A` |
| 1 | ai-run-A (new conversation) | `prompt.md` | Build the model (the experiment's verbatim prompt; the kit's AI is not involved) |
| 2 | kit | `prompts/00_prepare_B.md` | Create `../ai-run-B` |
| 3 | ai-run-B (new conversation) | `prompt.md` | Build the model |
| 4 | kit | `prompts/10_shoot_and_score.md` | Collect the models into `work/mine/`, `make_rhino_runner.py` → capture in Rhino → `metrics.py --out work/results_mine` |
| — | kit | `prompts/11_check_scoring.md` | Without Rhino, recompute the recorded run's numbers from the bundled silhouettes (`metrics_live.py --out work/results_check`) |

## Rules for every step

1. **The user is an architect, not a programmer.** Reply in the user's language, briefly, in architectural terms. Do not show commands, paths or jargon (JSON, IoU, Python, MCP…) — say "overlap ratio" for IoU.
2. **You run all commands.** Ask permission before installing Python or image-processing packages.
3. **Ask the user only to start new conversations and to do things in the Rhino GUI.** Say exactly what to paste where.
4. **Only one AI sends commands to Rhino at a time.** While a model-building conversation is using Rhino, send nothing to Rhino.
5. **Never overwrite the published results (`results/`, `run2_recorded/results/`, `outputs/`).** Write your results under `work/`.
6. **Never fabricate results.** Explain failures plainly and propose the next move.
7. If the connection is missing, point the user to the setup page (English https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T#en / Japanese https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T#ja).
8. `vision_analyze` (look at an image) and `execute_rhino_code` (run Python in Rhino) in the prompts are tool names of the experiment's agent (Hermes Agent). Map them to the tools with the same function in other agents.

## Other requests

- **Remake the facade textures**: [skills/pbr-texture-pipeline.md](skills/pbr-texture-pipeline.md) and "Facade textures" in TECHNICAL.en.md. This uses an image-generation service (ComfyUI cloud), so tell the user it costs money and get permission first.
- **Make drawings via the Figma loop**: [skills/figma-drawing-markup-loop.md](skills/figma-drawing-markup-loop.md). It needs human mark-ups; ask for one concrete thing at a time.
- **Build a model from the user's own exterior rendering or sketch**: [skills/image-to-massing.md](skills/image-to-massing.md). There is no correct model, so no scoring; return the assumed dimensions with confidence levels.
- Fairness rules of the experiment (splitting A/B, scoring, capture pitfalls): [skills/input-comparison-experiment.md](skills/input-comparison-experiment.md)
- File list and details: [TECHNICAL.en.md](TECHNICAL.en.md)
