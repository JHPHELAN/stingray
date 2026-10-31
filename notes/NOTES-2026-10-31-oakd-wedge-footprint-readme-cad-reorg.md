# NOTES 2026-10-31 — OAK-D wedge footprint, README wedge section, CAD folder reorg

Machine: HankRearden (Windows laptop), driving the Stingray Pi over SSH for the
robot-code half and editing the local stingray doc repo for the docs half.

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
   context.txt = STABLE facts only (hardware/software/environment/procedure). Day-to-day
   activity belongs in NOTES-, NOT context.txt (scope rule added to context.txt this session).
3. PUSH (notes/context -> JHPHELAN/stingray main; robot code -> JHPHELAN/articubot_one exploration).
   Session-state copies are DRAFTS only — unpushed = invisible next time.

## Lane A — robot code (articubot_one exploration), pushed as 48a2968
Updated the robot's forward outline to match the physical 25 deg OAK-D wedge
(added to the URDF last session, NOTES-2026-10-28). The up-tilt swings the
OAK-D's bottom-front corner forward, so the robot now reaches further ahead.

Derivation (base_link frame): OAK-D link origin (its front face) sits at
x=0.12841, z=0.02679, pitched 25 deg nose-UP. The OAK-D collision housing spans
x_local -0.033..0 and z_local -0.0409..+0.0136. Rotating the bottom-front corner
(x_local=0, z_local=-0.0409) by the up-tilt:
  x_forward = 0.12841 + cos(25)*0 - sin(25)*(-0.0409) = 0.12841 + 0.01728 = 0.1457 m.
So the true forward-most point moved from ~+0.12 to +0.1457. Tilting the camera
UP pushes its bottom-front edge ~25 mm FORWARD (counter-intuitive but correct).

Edits:
- robots/stingray/description/robot_core.xacro: oakd_x_length 0.033 -> 0.0582
  (sole consumer is the base_footprint "shadow" box). Box front edge 0.1205 ->
  0.1457; rear edge unchanged at -0.2345 (the term cancels in the rear calc).
  xacro expands clean (XACRO OK).
- nav2 costmap footprint polygon front vertices [0.123, +/-0.06] -> [0.1457, +/-0.06]
  in nav2_params.yaml (lines 219/324), nav2_params_mapping.yaml (223/322), and
  nav2_params_sim.yaml (219/323). True computed value, NOT padded (user choice).
  All three YAML still parse.
- DELETED robots/stingray/config/local_costmap.yaml — dead "old fork" leftover
  (commit 7208720), referenced by no launch/py/yaml. Was a rectangle front +0.10.

NOT yet colcon-built. nav2 params load from install/share, so the new footprint
takes effect only after a `colcon build` on the Pi — pairs with the RTAB-Map
re-run chat below.

## Lane B — docs (stingray main), pushed as e6dc5c2, 83d767c, a243ee2
README wedge section + CAD folder reorg.

e6dc5c2 — wedge docs + CAD reorg:
- CAD folder reorg so it can hold multiple CAD types:
    kicad/           -> CAD/KiCAD/         (git renames, history preserved)
    NEW CAD/CorelDraw/   (01 OAK-D Center Plate Wedge.cdr)
    NEW CAD/3D Print/    (oakd_tilt_wedge_25deg.step)
  Added .gitattributes marking *.step/*.stp/*.cdr as binary (verbatim store, no
  CRLF munging — a STEP file is ASCII so git otherwise treats it as text).
- README: new "### OAK-D 25° tilt wedge" section under ## Camera, with the
  verbatim header line "Created 25 deg wedge to tilt OAK-D upward ½ the vertical
  Field of View to minimize ground artifact", before/after dock views, four
  wedge build photos, and a USB-cable note. Repointed the KiCad links from
  kicad/ to CAD/KiCAD/. Added 7 images.

83d767c — dropped the oversized USB-cable photo (unnecessary), kept the note +
Amazon product link (B0CLXZT6FT) as one line. (Blob still in history from
e6dc5c2; no history rewrite — fine for a docs repo.)

a243ee2 — section anchors + CorelDRAW .cdr relocation:
- Converted 3 bold pseudo-headings to real Markdown headings so GitHub shows the
  hover link/anchor icon: `## Stormy full schematic (KiCad 10.0, 2026-10-14)`,
  `### Download the editable KiCad 10.0 project`, `#### CorelDRAW 2018 CAD
  drawings for laser cutting`. (GitHub auto-anchors real headings only, NOT bold
  text or HTML. VSCode markdown preview = Ctrl+Shift+V, or Ctrl+K V to the side.)
- Moved the 3 laser-cut .cdr drawings images/ -> CAD/CorelDraw/ (git renames) and
  repointed the README download links. NOTE the gotcha: first attempt I staged
  new differently-named .cdr; user instead MOVED the originals from images/ and
  deleted my adds. Reconciled with `git reset` then re-add so git recorded clean
  renames with the ORIGINAL filenames (Stingray Bottom Plate.cdr, Stingray Top
  Plate.cdr, Stingray Side Panel Blank.cdr). Side-panel caption "Blank example
  showing the fuse-holder hole" stays accurate (nothing renamed).

## context.txt updates this session (stable facts)
- Added the SCOPE rule at top: context.txt = stable facts only; day-to-day -> NOTES-.
- Repo-structure line now describes CAD/ (KiCAD/ CorelDraw/ 3D Print/) + .gitattributes.
- KiCad source path updated kicad/ -> CAD/KiCAD/.

## Parked / next
### >>> NEXT CHAT: RTAB-Map re-run, OAK-D wedged, DRIVE BY HAND <<<
Goal: remap a limited area with the physical 25 deg wedge in place, hand-driven
(NO explore / NO autonomy), and confirm the new footprint + the wedge camera
behave. Recipe distilled from NOTES-2026-10-19 (the last real-house RTAB-Map run)
and context.txt; both repos are at HankRearden, driven over SSH.

FIRST, on the Pi (this session's footprint/base_footprint edits are committed as
articubot_one 48a2968 but NOT yet built):
  ssh ubuntu@192.168.68.66
  cd ~/robot_ws && colcon build && source install/setup.bash
  (nav2 params + URDF load from install/share, so the +0.1457 footprint only
   applies after this build.)
Run OPEN ritual first (Read/Recall/Pull); git pull --ff-only articubot_one
exploration before building in case the separate chat or LinuxBox moved it.

Bring-up (each line its own terminal; source ros2 jazzy + install/setup.bash):
  Stingray T1: ros2 launch articubot_one stingray.hardware.launch.py
    (hardware-only: rsp + drive + sensors, NO slam_toolbox, NO Nav2 — that is
     why rtabmap can own the map. Do NOT use the full stingray.launch.py here.)
  LinuxBox RGB decompress (raw RGB will NOT cross WiFi):
    ros2 run image_transport republish --ros-args -p in_transport:=compressed -p out_transport:=raw \
      -r in/compressed:=/oak/rgb/image_raw/compressed -r out:=/oak/rgb/image_raw_uncompressed
  LinuxBox T2 (RTAB-Map mapping):
    ros2 launch articubot_one rtabmap.launch.py rgb_topic:=/oak/rgb/image_raw_uncompressed \
      depth_topic:=/oak/stereo/image_raw camera_info_topic:=/oak/rgb/camera_info \
      odom_topic:=/odometry/local frame_id:=base_link approx_sync:=true qos:=2 \
      localization:=false delete_db_on_start:=true publish_tf_map:=true subscribe_scan:=true \
      scan_topic:=/scan rtabmap_args:="--RGBD/NeighborLinkRefining true --RGBD/ProximityBySpace true --Reg/Strategy 0 --Grid/FromDepth false --Grid/3D false --Grid/RayTracing true"
  LinuxBox T4: python3 ~/robot_ws/src/articubot_one/scripts/map_relay.py
  LinuxBox RViz: rviz2 -d ~/robot_ws/src/articubot_one/config/main.rviz   (Fixed Frame = map)
  HAND DRIVE (instead of explore.launch.py): LinuxBox joystick ->
    ros2 launch articubot_one joystick.launch.py   (publishes /cmd_vel)

CRITICAL cautions carried from NOTES-2026-10-19:
  - VERIFY ODOMETRY IS TRUTHFUL before trusting the map. That run DELOCALIZED;
    root cause was odometry lying (encoders/EKF reported motion the robot was not
    making). Loose right-wheel setscrew was reported fixed (NOTES-2026-10-28) —
    re-confirm: joystick a slow straight-line forward and check /odometry/local
    tracks reality before mapping anything.
  - explore.yaml already has use_sim_time:false (the critical real-robot fix).
  - Enable rtabmap FILE logging and SNAPSHOT ~/.ros/rtabmap.db on LinuxBox at the
    end this time (last run's db was scrambled and not saved).
  - Keep the drive to a LIMITED area; no doorway-wedging stress.

### Other parked
- FLOOR-FLATNESS CAL still parked (from NOTES-2026-10-28): the old ~1.5 deg
  nose-down oakd cal was dropped for the physical 25 deg wedge; re-run the probe
  on clean floor with the wedge mounted and re-add a small residual pitch to
  oakd_joint if the costmap sees a sloped floor.
- wifi v2 limitations to report to Mike (passive = associated-AP only; zero-dBm
  glitch) — unchanged from NOTES-2026-10-26.
