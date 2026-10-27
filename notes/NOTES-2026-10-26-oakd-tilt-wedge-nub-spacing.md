# NOTES 2026-10-26 — OAK-D tilt wedge FINALIZED (fit-tested PERFECT): nubs 25 mm + flipped, 3rd insert, 9 mm counterbore

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
counterbore square to the bolt on the robot side), 3x 6-32 heat-set inserts in the robot face
(anti-rotation of the wedge), and 2x blunt tapered nubs that drop into the OAK-D cooling-fin
channels at the two upper phillips screws (anti-rotation of the CAMERA about the 1/4-20).

## OUTCOME: FINALIZED — wedge fit-tests PERFECT (user confirmed 2026-10-26 ~20:54)
Took THREE PETG fit prints this session to converge. Final verified STL/STEP:
CAD\oakd_tilt_wedge_25deg.stl (130984 bytes) / .step. Mesh-measured correct: nubs Z=17.5
(left/closer) & 42.5 (right/further); all 3 inserts present (10,13),(40,13),(25,28); counterbore
8.99 mm deep; watertight single body.

## FINAL parameters (wedge.py)
- WIDTH 50, HEIGHT 45, TILT 25 deg, TOP_THICKNESS 4; BASE_DEPTH auto 24.98.
- TRIPOD 1/4-20 clear hole 7.0, centered width (Z=25), 21 mm up-slope; COUNTERBORE 19.5 dia x
  9 deep coaxial/square to bolt (deepened 6->9 for a fatter-than-normal screw head; ~8.8 mm wall
  left to camera face).
- INSERTS 6-32: 5.16 dia x 6.5 deep. Two at 1/5 & 4/5 width (INSERT_Y 13) + a THIRD
  (INSERT3_ENABLE True) centered Z=25 raised to Y=28 (isosceles apex toward the narrow top).
- NUBS: NUB_Z_OFFSETS (7.5,-17.5) = 25 mm apart, FLIP_LR = TRUE -> centers Z=17.5 & 42.5, Y~38.3.
  base 8.5 x 6 -> top 6 x 4, height 10, 21.25 mm above tripod.

## What changed this session + the fixes (in order)
1. Nubs too close (24 mm) -> widened to 25 mm (NUB_Z_OFFSETS 7/-17 -> 7.5/-17.5).
2. Nubs MIRRORED -> FLIP_LR = True (left nub Z=17.5 closer to midline, right Z=42.5 further,
   viewed from the robot-attach back with the narrow end up). Settled; leave True.
3. Middle (3rd) heat-set insert MISSING -> restored (INSERT3_ENABLE True).
4. Tripod screw head fatter than normal -> counterbore 6 -> 9 mm deep.

## TWO LESSONS (don't repeat these)
- DIVERGENT GENERATOR COPIES. wedge.py existed in 3 places (Copilot session-state files/,
  CAD\wedge.py, CAD\src\wedge.py) and had silently diverged: the session copy I was editing had
  only 2 inserts while the CAD copies had the 3rd. Regenerating from the stale session copy
  DROPPED the middle insert. FIX: all three wedge.py are now byte-identical (verified by hash).
  Treat them as ONE file; if you edit one, re-sync the others.
- STALE SLICER PROJECTS (.3mf) EMBED THE MESH. Several bad prints happened because the slicer
  re-opened/re-sent an OLD .3mf project (1026a/1026b/10.26c) whose embedded mesh predated the
  fixes — the corrected STL on disk was never imported. A correct STL is not enough. ALWAYS:
  start a NEW slicer project and File>Import the fresh CAD\oakd_tilt_wedge_25deg.stl; never
  reprint an old .3mf. Those stale exports (CAD\Old Scans) were DELETED this session so none can
  be re-sliced by accident.

## Generator + toolchain (Windows, HankRearden)
- Generator wedge.py (source of truth) is identical in Copilot session-state files/,
  CAD\wedge.py, and CAD\src\wedge.py. Build output: CAD\oakd_tilt_wedge_25deg.step/.stl.
  (CAD is the sibling ...\Stingray\CAD, NOT inside this git repo.)
- Python 3.13; cadquery 2.8.0 (+ cadquery-ocp), trimesh, numpy, scipy, pillow, matplotlib, rtree.
  Rebuild: python wedge.py. Verify: python render.py ; python section.py (watertight + previews),
  or probe the STL with trimesh.contains for insert/counterbore/nub positions.
- Full design rationale, calipered OAK-D back values, and open items are in the session-state
  draft NOTES-2026-10-14-oakd-tilt-wedge.md.

## Also this session — repo housekeeping (GitHub pull + KiCAD upload + .gitignore)
- PULLED to HankRearden the user's new schematic + Dual MOSFET switch work from GitHub
  (README + images/Dual MOSFET Switches.png, MOSFET Dual High Power.png, Schematic Full
  20261026.png). It arrived via a rebase over an incoming push; `git pull --ff-only` is clean.
- UPLOADED updated KiCAD source into the repo kicad/ folder from the live WORKING COPY at
  C:\Users\jhphe\OneDrive\Documents\KiCad\10.0\projects\Stingray. The only real content change
  was Stingray.kicad_sch (dual MOSFET high-power switches) + Stingray.kicad_pro. The repo kicad/
  tracks the Stingray project plus a Dual Power Input sub-project. KEEP that KiCad-10.0 working
  copy and the repo kicad/ in sync — there are OLDER Stingray KiCAD projects under KiCad\8.0 and
  9.0 and a stingray-builders-manual\kicad copy; the 10.0 one is the source of truth.
- GITIGNORE: added *.kicad_prl and untracked the two committed .prl files (per-user UI state,
  not design data; local copies kept). repo kicad/ now tracks only .kicad_pro/.sch/.pcb/.sym +
  sym-lib-table.
- GOTCHA: git autocrlf flips LF<->CRLF, so KiCAD .prl/.pro looked "modified" purely on line
  endings until git normalized them; the real diffs were only Stingray.kicad_sch + .kicad_pro.

## Still parked (robot side, from NOTES-2026-10-19) — NOT touched this session
The real-house RTAB-Map/Nav2/explore delocalization was root-caused to a LOOSE RIGHT-WHEEL
SETSCREW (encoder reads the motor, wheel slipped -> odometry lied -> pose jumped). Next robot
session: FIX THE WHEEL FIRST (tighten + blue Loctite, re-test straight tracking), then NO autonomy
— drive by hand while RTAB-Map maps, with rtabmap FILE logging on. Mapping-run tuning
(inflation_radius 0.30, oak_points off, goal_timeout 60) is committed in articubot_one exploration
but is test-value, not the normal-stack baseline. See NOTES-2026-10-19 for full detail.
