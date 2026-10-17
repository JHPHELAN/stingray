# Copilot orientation — Stingray (Stormy) documentation repo

This repository (`JHPHELAN/stingray`) is the **hardware / build documentation** for
Stormy the Stingray: `README.md`, `images/`, the BOM, and CAD (`.cdr`). It is primarily
edited here on **HankRearden** (Windows). New photos are staged from:
`C:\Users\jhphe\OneDrive\Documents\My Downloads\Robotics\Parallax\Stingray\Photos`

## The robot's code lives elsewhere

The ROS 2 workspace and robot code are in a **separate** repo, `JHPHELAN/articubot_one`
(working branch `exploration`), checked out on the Stingray Raspberry Pi at
`/home/ubuntu/robot_ws/src/articubot_one`.

## Full orientation / AI "memory"

The authoritative orientation file is **`context.txt`** — now CANONICAL in **THIS**
repo (JHPHELAN/stingray) at the repo root: `context.txt` (moved here 2026-10-17 from
articubot_one so this Windows-local window can see it). A synced cc copy lives on the
Pi at articubot_one `robots/stingray/context.txt` for Remote-SSH sessions. It covers
robot identity, the home LAN, hardware preflight, recovery, and the session rituals
below. Prior session write-ups (handoff notes) are committed in **THIS** repo at
`notes/NOTES-YYYY-MM-DD-*.md` — HankRearden is the note-exchange point. A Pi-local
skills library lives at `/home/ubuntu/.copilot/skills`.

There is **no cross-machine AI memory** — orientation travels only through these
committed files plus the Pi-local skills folder. This window's workspace IS this repo,
so `context.txt` and this file are directly readable; read them first.

## Session rituals

- **Startup = Read, Recall, Pull**: Read THIS file (`.github/copilot-instructions.md`)
  AND `context.txt`; Recall skills + the NEWEST `notes/NOTES-*.md` BY DATE (not an older
  one); Pull latest on the repo(s) you will touch (`git pull --ff-only`). Do this even if
  the VS Code window opened on a different folder than this repo.
- **Shutdown = Recap, Remember, Push**: Recap what changed and what was learned;
  Remember it in a NEW `notes/NOTES-YYYY-MM-DD-*.md` in THIS repo and update `context.txt`;
  Push to the correct repo/branch (notes -> JHPHELAN/stingray `main`; robot code ->
  JHPHELAN/articubot_one `exploration`). Session-state copies are DRAFTS only — if a note
  isn't pushed here, the next session can't see it (this is what broke 2026-10-11..10-16).

## Working style (user preference)

- One step at a time; wait for the user's "done" before giving more directions.
- Plain text in chat (no markdown bullets/headings) so it can be pasted into notes.
- When editing files, state which file, which line(s), and the before/after.
