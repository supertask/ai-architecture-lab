[🇯🇵 日本語](README.md) | 🇺🇸 English

# rules: drafting rules (how the drawings should be drawn)

These are the "drawing rules" given to the AI. They are **plain Japanese prose**, not code. They summarize only the drafting conventions (manners) of real-world Japanese practice drawings; no shapes, plans or dimensions were copied.

**They stay in Japanese on purpose.** They describe Japanese drafting conventions (level marks such as `▽2FL=GL+3250`, room labels with area in ㎡ and tatami mats 帖, grid bubbles X1/Y1, Japanese material names). The AI reads Japanese fine, so the kit works as-is for English-speaking users. If you work in another drafting tradition, treat these files as a template: ask the AI to rewrite them in your language and to your office's conventions (see "Use it in your own office" in [../README.en.md](../README.en.md)).

| File | What it covers | Used by |
| --- | --- | --- |
| [作図ルール_平面.md](作図ルール_平面.md) (floor plans) | Grid lines and bubbles, two-tier perimeter dimensions (grid-to-grid + overall), room labels (name / area ㎡ / tatami), door & window tags, light floor fills, drawing title, how to produce them in Archicad, checklist | `10_sheet_P1`, `11_sheet_P2`, `23_`–`25_` |
| [作図ルール_断面.md](作図ルール_断面.md) (sections) | Ten must-have items (levels, dimensions, build-up notes for each layer, ground hatch, waterproofing line…), line weights and colours, avoiding overlaps, numeric self-checks, "previous mistakes" | `12_sheet_SA`, `13_sheet_SB`, `20_`–`22_` |
| [作図ルール_立面.md](作図ルール_立面.md) (elevations) | How to build fills (painter's algorithm), annotation placement, Archicad methods verified in the experiment, level/height notation (shared by all sheets), rules added after the 11/16 review | `03_`, `14_`–`17_` |

- Each drawing prompt points the AI to exactly one of these files (rules are followed better when the AI gets only the ones for the sheet type it is drawing).
- `scripts/prepare_workdir.py` copies these files into the work folder (`work/`). If you edit a rule, rerun step 0 or copy the file into `work/` too.
- "Growing" the rules: after each review, the AI appends each mistake as one line "what it did → what is correct" to the "前回の失敗" (previous mistakes) section, or "11/16 の点検で足した決まり" for elevations.

Example (section rule, translated):

> **Levels** — Format: ▽Name=GL+number (no comma, no unit). GL is written △GL. For ▽ (tops: max height, eaves, each FL) the text sits above the line; for △ (ceiling CL and GL) below the line.
> **Ground** — GL as a thin solid line extending well beyond both sides of the building. Outside the building only, a ~1 m wide band of earth hatching below GL (none under the building).
