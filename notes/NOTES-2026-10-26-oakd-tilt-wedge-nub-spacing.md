# NOTES 2026-10-26 — OAK-D tilt wedge: PETG fit test good; nubs widened 24 -> 25 mm

Machine: HankRearden (Windows laptop), local VSCode window. This is LOCAL CAD work (no robot,
no SSH). The OAK-D tilt-wedge generator and its draft note live in Copilot session-state
(session c3041b93-f85d-4750-940b-f94e1b7ab1bf), files/: wedge.py, render.py, section.py, and
NOTES-2026-10-14-oakd-tilt-wedge.md (the detailed design note). This repo note is the canonical,
pushed handoff; the session-state copies are DRAFTS only.

## SESSION ROUTINES — do these EVERY session (carry this block forward)
### OPEN — "Read, Recall, Pull"
1. READ: .github/copilot-instructions.md AND context.txt (both canonical in THIS repo root).
2. RECALL: read the NEWEST notes/NOTES-YYYY-MM-DD-*.md BY DATE, state back where we left off,
   wait for the user to confirm. Skills are Pi-local (/home/ubuntu/.copilot/skills).
3. PULL: git pull --ff-only on the repo(s) you'll touch (stingray main; articubot_one exploration).
   NO cross-machine AI memory — orientation travels ONLY through committed files + Pi skills.
### CLOSE — "Recap, Remember, Push"
1. RECAP what changed and what was learned.
2. REMEMBER: write a NEW notes/NOTES-*.md AND update context.txt. Carry THIS block forward.
3. PUSH (notes/context -> JHPHELAN/stingray main; robot code -> JHPHELAN/articubot_one exploration).
   Session-state copies are DRAFTS only — unpushed = invisible next time.

## What this wedge is
3D-printed wedge that tilts the OAK-D up 25 deg (= 1/2 the ~50 deg stereo-depth V-FOV) to lift
the lower edge of the vertical FOV off the ground and favor higher landmarks. Wedge robot face
(flat, vertical) bolts to the robot front plate; OAK-D back presses on the 25 deg camera face.
Held by one 1/4-20 into the OAK-D tripod hole (normal to the camera face, recessed washer
counterbore square to the bolt on the robot side), 2x 6-32 heat-set inserts in the robot face
(anti-rotation of the wedge), and 2x blunt tapered nubs that drop into the OAK-D cooling-fin
channels at the two upper phillips screws (anti-rotation of the CAMERA about the 1/4-20).

## This session's change (what + why)
- FIT TEST: first physical print in PETG. Fit is good, handedness correct (FLIP_LR stays False).
- The ONLY issue: the two upper camera-stabilizing nubs needed ~1 mm more spacing.
- FIX: moved each nub 0.5 mm away from center. wedge.py NUB_Z_OFFSETS (7.0, -17.0) -> (7.5, -17.5),
  i.e. nub width centers Z=32.0/8.0 -> Z=32.5/7.5 (tripod/center at Z=25). Now 24 -> 25 mm apart.
- Regenerated the deliverables in place from wedge.py:
    CAD\oakd_tilt_wedge_25deg.step  and  CAD\oakd_tilt_wedge_25deg.stl
  (CAD folder is the sibling ...\Stingray\CAD, NOT inside this git repo; it regenerates from
  wedge.py in session-state — the generator is the source of truth, the STEP/STL are build output.)
- render.py check: watertight True, volume ~30.9 cc, bbox 24.98 x 45 x 50 mm. No other change.
- NEXT: user will reslice + reprint the PETG wedge and re-test the nub fit.

## Toolchain (Windows, HankRearden)
Python 3.13; packages cadquery 2.8.0 (+ cadquery-ocp), trimesh, numpy, scipy, pillow, matplotlib.
Rebuild: python wedge.py  (writes STEP + STL).  Verify: python render.py ; python section.py.
All dims are named parameters at the top of wedge.py. Full design rationale, measured OAK-D back
values (calipers), and remaining open items are in the session-state draft
NOTES-2026-10-14-oakd-tilt-wedge.md.

## Still parked (robot side, from NOTES-2026-10-19) — NOT touched this session
The real-house RTAB-Map/Nav2/explore delocalization was root-caused to a LOOSE RIGHT-WHEEL
SETSCREW (encoder reads the motor, wheel slipped -> odometry lied -> pose jumped). Next robot
session: FIX THE WHEEL FIRST (tighten + blue Loctite, re-test straight tracking), then NO autonomy
— drive by hand while RTAB-Map maps, with rtabmap FILE logging on. Mapping-run tuning
(inflation_radius 0.30, oak_points off, goal_timeout 60) is committed in articubot_one exploration
but is test-value, not the normal-stack baseline. See NOTES-2026-10-19 for full detail.
