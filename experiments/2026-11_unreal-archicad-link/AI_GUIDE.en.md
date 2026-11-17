# AI_GUIDE — procedure for the layout agent

You (Claude Code, Codex or any agent that can run shell commands) take a free-text request,
**read the room that is open in Archicad, design the arrangement yourself, check it against the rules and apply it to Archicad**.
Unreal follows by itself through the follower a person started there (`ue/ue_follow.py`); do not touch Unreal, and do not run or edit the files in `ue/`.

Your working folder is the folder this `AI_GUIDE.en.md` is in (called `<KIT>` below); run every command here.

## 0. First-time setup and connection check (only the first time, or when asked)

1. The Tapir add-on must be installed and running in Archicad (if not, point the person to the setup page https://claude.ai/artifact/UwQrsxsWJztdwNVAd93t8T#en).
2. `uv` must be available (`uv --version`); install it if missing. The libraries (numpy / matplotlib / shapely) are installed on the first `uv run`.
3. Adapt `config.json` to the model open in Archicad (decide together with the person):
   - `room_zone_name`: zone name of the target room (e.g. "LDK"); the room is assumed to be drawn as a Zone
   - `kinds`: library-part name -> furniture kind (common Japanese and English names are included)
   - `kind_by_guid`: stand-ins (e.g. a stool part standing in for a lamp)
   - `keep_out`: rectangles kept free of furniture (`reach: true` also makes it a main-path destination, e.g. a stair landing)
   - `fixtures`: equipment that is not modelled (e.g. a kitchen counter)
   - the values shipped are those of the fictional house used in the experiment
4. Connection check: run `uv run read_room.py` once, confirm the furniture list prints and no piece has kind `other` (id `obj…`), and show the list to the person.
5. Unreal Engine is the person's job (`ue/README.en.md`). You do not operate Unreal Engine.

`recorded/` holds the arrangements the AI wrote in the experiment, `examples/` holds development test records. Both are answers: do not read or reuse them.

## The loop (every time, in this order; never reuse a ready-made arrangement)

1. **Read the room** — `uv run read_room.py`
   - Writes `room.json`. Read the printed furniture list (id, kind, size, centre, facing) and in `room.json`:
     `room.polygon`, `openings` (window sill height `sill_m`, door `clear_zone`), `entries`, `keep_out` (stairs …),
     `fixtures` (e.g. a kitchen that is not modelled).
   - Re-read for every request (the previous request may have moved things).
2. **Design** — restate the request as one sentence of intent, then write `layouts/<short-name>.json` (format below).
   - **Make it clearly different.** Moving the main groups (sofa group, dining, TV) 3–5 m is normal.
     A few tens of centimetres is not a new layout (see `moved ... max` in the checker output).
   - List only the pieces you move; the others stay where they are.
   - Handy sizes: against a wall the centre is depth/2 from it; dining chairs sit at table edge + chair depth/2;
     rug centre = coffee table centre; TV = same centre and facing as the TV unit; sofa→TV 2.0–3.6 m.
3. **Check** — `uv run check_layout.py layouts/<name>.json`
   - Prints `PASS` or a numbered list (`[rule] what -> how to fix`), and a top-down PNG with the same name.
   - Fix and re-run, **at most 3 times**. If it still fails, do not apply; tell the user in 1–2 lines what cannot be satisfied together.
   - Stuck on paths? Add `--paths` to draw the reachable floor (dark green 0.8 m / light green 0.6 m).
4. **Apply** — `uv run apply_layout.py layouts/<name>.json`
   - Refuses anything that has not passed. Moves all pieces in one Tapir call and prints one JSON line
     (`pieces`, `tapir_modify_s`, `since_read_room_s`, `max_error_mm`, `undo` file).
5. **Reply in one line** — what changed + time, e.g.
   `Sofa moved under the south window as café booth seating, dining turned east (17 pieces, Archicad 0.6 s, 2 min 10 s since reading the room)`

Undo: `uv run apply_layout.py undo/<time>.json` (apply saves the previous positions automatically).

## Layout JSON

```json
{
  "request": "the user's sentence",
  "title": "short title (used as the drawing heading)",
  "concept": "intent in 1-2 sentences",
  "pieces": {
    "<piece id>": [x, y, facing],
    "sofa": [10.3, -1.14, 90]
  },
  "exceptions": [
    {"rule": "sofa_faces_tv", "piece": "sofa", "reason": "café seats face each other, not the TV"}
  ]
}
```

- Metres in Archicad plan coordinates; `[x, y]` is the **centre** of the piece.
- `facing` in degrees: 0 = +x (east), 90 = +y (north), 180 = west, -90 = south — the side people **sit on / use**
  (where a seated person looks, the TV screen, the open side of a shelf).
- Piece ids are the ones printed by `read_room.py` (`sofa`, `lounge1`, `dchair3` …); unknown ids fail.
- `exceptions` declare a deliberate break of a **soft** rule only, with a reason; drawings and output mark them.

## Rules (check_layout.py)

| Type | Rule id | Meaning |
|---|---|---|
| hard | inside_room | inside the room outline (zone) |
| hard | keep_out | not on stairs / `keep_out` / kitchen counter + 0.9 m in front / 0.8 m in front of doors (rugs may lie in those strips) |
| hard | overlap | no overlaps (chairs at the table and TV on its unit excepted) |
| hard | tv_on_unit | TV stands on the TV unit, same facing |
| hard | tv_on_solid_wall | unit back on a wall with no window/door lower than TV top + 0.3 m behind it (high windows above are fine) |
| hard | dining_chairs | chairs face the table, symmetric per side, 0.6 m pull-out room |
| hard | dining_near_kitchen | dining table within 2.5 m of the kitchen counter |
| hard | main_path | 0.8 m path from the entry to the kitchen front, every door, other entries and `reach` zones (stair landing) |
| hard | secondary_path | 0.6 m path to every seat, every chair (pulled out) and shelves |
| soft | sofa_faces_tv / sofa_tv_distance | sofa faces the TV ±15°, 2.0–3.6 m |
| soft | rug_centred / rug_under_seats / rug_not_under_tv_unit | rug centred on the coffee table; front legs of seats within 2 m on it; not under the TV unit |
| soft | lounge_to_centre | lounge chairs near the coffee table turn to the conversation centre ±25° |
| soft | wall_aligned | parallel to the walls; give a reason for any angle |
| soft | plant_place / side_table_by_seat / lamp_by_seat / shelf_on_wall | plants in a corner or beside furniture, side tables and lamp beside a seat, shelf on a wall |
| soft | chair_at_table | dining chairs tucked at the table |

Also reported: pieces moved and distances (those ≥ 3 m), the largest clear floor circle (use it for "clear the middle"),
sofa–TV distance, dining–kitchen distance.

## Do not

- Edit `room.json` by hand. `config.json` belongs to the human (say why if you change it).
- Write to Archicad in any other way (no create/delete/save/RebuildView). One apply per request.
- Touch Unreal, or reuse the arrangements in examples/ or recorded/ (they are a test record; design from the current room every time).

## Example requests (no answers — design them yourself)

1. "Make a reading corner by the window; we don't need the TV."
2. "Dinner for six guests — make the dining table the centre of the room."
3. "Stop arranging around the TV; set it up for conversation."
4. "Clear as much floor as possible so the kids can run around."
