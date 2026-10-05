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

The authoritative orientation file is **`context.txt`** in the articubot_one repo:
`robots/stingray/context.txt`. It covers robot identity, the home LAN, hardware
preflight, recovery, and the session rituals below. Prior session write-ups are in
`robots/stingray/NOTES-YYYY-MM-DD-*.md`. A Pi-local skills library lives at
`/home/ubuntu/.copilot/skills`.

There is **no cross-machine AI memory** — orientation travels only through these
committed files plus the Pi-local skills folder. If you (Copilot) cannot see
`context.txt` from this Windows-local window, ask the user to open a Remote-SSH window
into the Pi, or to paste `context.txt`.

## Session rituals

- **Startup = Read, Recall, Pull**: Read `context.txt`; Recall skills + the latest
  `NOTES-*.md`; Pull latest on the repo(s) you will touch (`git pull --ff-only`).
- **Shutdown = Recap, Remember, Push**: Recap what changed and what was learned;
  Remember it in a `NOTES-*.md` and update `context.txt`; Push to the correct
  repo/branch.

## Working style (user preference)

- One step at a time; wait for the user's "done" before giving more directions.
- Plain text in chat (no markdown bullets/headings) so it can be pasted into notes.
- When editing files, state which file, which line(s), and the before/after.
