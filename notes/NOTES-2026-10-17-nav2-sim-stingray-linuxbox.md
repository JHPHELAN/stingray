# NOTES 2026-10-17 — Nav2 on sim (Stingray / LinuxBox)

Machine: LinuxBox (laptop), Ubuntu 24.04, ROS2 Jazzy. Sim = Gazebo (gz-sim 8, Harmonic).
World now = `warehouse` (assets/worlds/warehouse.sdf). Robot model: stingray.
Map = saved RTAB-Map DB `~/.ros/rtabmap.db` (167 MB, built yesterday in warehouse).

## SESSION ROUTINES — do these EVERY session (carry this block forward)
The "Read, Recall, Pull" (open) and "Recap, Remember, Push" (close) rituals. Copy this
block into each new handoff note so the next session executes it correctly.

### OPEN — "Read, Recall, Pull" (first thing)
1. READ: context.txt (specs, dialog rules, preflight) AND the LATEST handoff note.
   - Latest = the newest NOTES-YYYY-MM-DD-*.md by DATE. Do NOT grab an older one.
     (2026-10-17 lesson: today's whole re-tread came from reading the 2026-10-10 note
     instead of the 2026-10-16 one, so we re-derived Force3DoF, scan-grid, XAUTHORITY,
     the filters:[] fix, etc. that were already solved.)
   - Canonical location (per JHPHELAN/stingray .github/copilot-instructions.md):
     the articubot_one repo, branch `exploration` — context.txt at
     robots/stingray/context.txt and prior write-ups at robots/stingray/NOTES-*.md.
     On LinuxBox/Pi: /home/ubuntu/robot_ws/src/articubot_one/robots/stingray/.
     Skills: /home/ubuntu/.copilot/skills. NO cross-machine AI memory — orientation
     travels ONLY through these committed files + the Pi skills folder.
2. RECALL: read that note's "NEXT TIME / TODO", state back where we left off and the
   open items, and wait for the user to confirm alignment before acting.
3. PULL: on LinuxBox, `git pull --ff-only` articubot_one (branch `exploration`) and any
   other repo you'll touch, so launch/config/params match the committed source of truth —
   this is what prevents re-deriving fixes already made. Then run the preflight.

### CLOSE — "Recap, Remember, Push" (end of session)
1. RECAP: summarize what was done, what works, what is still open.
2. REMEMBER: write a robots/stingray/NOTES-YYYY-MM-DD-*.md in the standard format (Goal,
   Result, What changed, Key facts/lessons, State at end, NEXT TIME/TODO) AND update
   robots/stingray/context.txt. Carry THIS routines block forward. Record config facts so
   they are not rediscovered (e.g. "Reg/Force3DoF already true").
3. PUSH: commit + push to the correct repo/branch (articubot_one `exploration`) so the
   next session's PULL sees them. Session-state copies are DRAFTS only.

### Why today drifted (the real fix)
Orientation is ALREADY defined (JHPHELAN/stingray .github/copilot-instructions.md). Today
drifted because OPEN read a Windows-local OneDrive copy of context.txt plus an OLD
session-state note (2026-10-10) instead of PULLing articubot_one and reading
robots/stingray/'s LATEST note (2026-10-16) — so we re-derived Force3DoF, scan-grid,
XAUTHORITY auto-discover, and the filters:[] fix the 16th already had. Fix: DO the ritual
against the repo, not local copies.

## Goal
Bring up Nav2 against the saved warehouse map and drive autonomous goals. Starting
point was adjusting `nav2_params_sim.yaml` and it snowballed into fixing GUI,
localization-pose delivery, a cmd_vel feedback loop, and sim timeouts.

## RESULT — SUCCESS
Autonomous navigation works. Goals to both "pesky corners" succeeded ("Goal reached").
Localization via RViz 2D Pose Estimate now relocalizes directly (through a small relay).

## Working bring-up sequence (4 terminals + relay)
Every GUI terminal needs:
```
export DISPLAY=:0
export XAUTHORITY=$(ls /run/user/1000/.mutter-Xwaylandauth.*)   # filename rotates each login
```
1. rsp:
   `ros2 launch articubot_one rsp.launch.py robot_model:=stingray use_sim_time:=true`
2. drive_sim (Gazebo warehouse + RViz + EKF + spawn):
   `ros2 launch articubot_one drive_sim.launch.py robot_model:=stingray robot_world:=warehouse use_sim_time:=true`
3. RTAB-Map localization (loads existing DB, publishes /rtabmap/map + map->odom):
```
ros2 launch articubot_one rtabmap.launch.py \
  rgb_topic:=/camera depth_topic:=/depth_camera camera_info_topic:=/camera_info \
  odom_topic:=/odometry/local frame_id:=base_link \
  use_sim_time:=true approx_sync:=true qos:=2 \
  localization:=true publish_tf_map:=true \
  initial_pose:="0.638 1.802 0.0 0.0 0.0 -1.197"
```
   (initial_pose = Stormy's spawn pose in the map; see "Startup pose" below.
    From a true at-spawn capture; may still need a tiny manual nudge some bringups.)
4. Nav2 — launch the STOCK bringup directly (NOT the wrapper, see LESSON 2):
```
ros2 launch articubot_one navigation_launch.py \
  use_sim_time:=true autostart:=true \
  params_file:=/home/ubuntu/robot_ws/src/articubot_one/robots/stingray/config/nav2_params_sim.yaml
```
Relay: now AUTO-STARTS with drive_sim (see "Relay auto-start" below). Manual fallback:
   `python3 ~/robot_ws/relay_initialpose.py`

## Relocalizing in sim
RViz "2D Pose Estimate" -> set tool Topic to `/initialpose` in **Tool Properties**
(NOT the Displays panel). Click-drag on the map; the relay forwards it to RTAB-Map.
Trust the CORNERS over shelf walls when aligning (corners pin x/y/yaw; long walls slide).

## FIX 1 — warehouse GUI (right column, no corner RTF)
Cause: warehouse.sdf `<gui>` used the legacy Ignition plugins (`GzScene3D`,
`<ignition-gui>` tags). gz-sim 8 (Harmonic) can't load that scene plugin, so it
DISCARDS the whole `<gui>` and falls back to its default docked layout (right column).
test_robot_world.sdf works because it uses modern `MinimalScene` + `<gz-gui>`.
Fix: replaced warehouse.sdf `<gui>` with a modern gz-gui block sourced from
test_robot_world.sdf, minus EntityTree/ComponentInspector/ImageDisplay/NavSatMap.
Backups: warehouse.sdf.bak, warehouse.sdf.bak2.
Note: install/share/.../warehouse.sdf is a SYMLINK to src, so editing src takes effect.

## FIX 2 — Nav2 wrapper ignores params_file (used wrong file / crashed)
`launch/navigation.launch.py` (the "generic wrapper") HARDCODES its params path to
`robots/<robot_model>/config/nav2_params.yaml` and ignores the `params_file` arg. With
no robot_model it resolved to `robots/config/nav2_params.yaml` (missing) and errored;
even with robot_model it would load nav2_params.yaml, never nav2_params_sim.yaml.
Workaround: launch the stock `navigation_launch.py` directly with params_file (above).
(Downside: lost the wrapper's integration — but the stock file plus our fixes is enough.)

## FIX 3 — cmd_vel feedback loop (robot crept at ~0.02 m/s, then aborted)
Symptom: angular OK (~0.4 rad/s) but linear strangled to ~0.
Cause: a loop on /cmd_vel_nav.
  - navigation_launch.py remaps controller_server, behavior_server AND velocity_smoother
    `('cmd_vel','cmd_vel_nav')`, so velocity_smoother SUBSCRIBES to /cmd_vel_nav.
  - collision_monitor param `cmd_vel_out_topic: "cmd_vel_nav"` (nav2_params_sim.yaml ~L529)
    PUBLISHES back to /cmd_vel_nav.
  => /cmd_vel_nav had 7 pubs (controller + 5 behavior + collision_monitor) and 2 subs
     (velocity_smoother + twist_mux): collision_monitor -> velocity_smoother ->
     cmd_vel_smoothed -> collision_monitor ... loop compounds the slowdown factor,
     killing forward speed. twist_mux's actual input never got a clean command.
Correct chain: controller/behaviors -> cmd_vel_raw -> velocity_smoother ->
cmd_vel_smoothed -> collision_monitor -> cmd_vel_nav -> twist_mux -> diff_cont.
Fix: in `launch/navigation_launch.py`, changed all 6 internal remaps
`('cmd_vel', 'cmd_vel_nav')` -> `('cmd_vel', 'cmd_vel_raw')`
(controller_server, behavior_server, velocity_smoother; standalone + composable sections).
This reserves /cmd_vel_nav for collision_monitor's checked output into twist_mux.
Verify: `ros2 topic info /cmd_vel_nav` -> Publisher 1 (collision_monitor), Subscriber 1 (twist_mux).
Backup: launch/navigation_launch.py.bak.
NOTE: Stormy's copy presumably already had this (or equivalent) — LinuxBox's launch had
drifted. Reconcile robot vs LinuxBox navigation_launch.py.

## FIX 4 — BT timeout aborts under heavy sim (~40% RTF)
Symptom: robot turned ~30 deg, then "Timed out while waiting for action server to
acknowledge goal request for compute_path_to_pose" -> "Goal failed". Also repeated
"Control loop missed its desired rate of 10 Hz".
Cause: BT/server timeouts too tight for the slow sim.
Fix in `nav2_params_sim.yaml` (sim file only; robot nav2_params.yaml untouched):
  - L19 bt_loop_duration: 5 -> 20 (ms)
  - L20 default_server_timeout: 20 -> 250 (ms)   <-- the key one
  - L62 controller_frequency: 10.0 -> 5.0 (Hz)   (left L564 vision 18.0 alone)
Backup: nav2_params_sim.yaml.bak.

## Earlier param cleanup (start of session)
- Removed stray empty `filters: []` lines from nav2_params_sim.yaml.
- keepout_filter: enabled: false (line ~335) — explicitly off; it wasn't in the
  global_costmap plugins list anyway. map_topic stays /rtabmap/map (transient_local).

## KEY LESSONS
1. QoS mismatch bites again. RViz 2D Pose Estimate publishes BEST_EFFORT; RTAB-Map's
   /rtabmap/initialpose sub is RELIABLE -> messages dropped, robot won't relocalize.
   Also /initialpose's only sub was a leftover SlamToolbox RViz panel, not RTAB-Map.
   Workaround = relay_initialpose.py (best_effort /initialpose -> reliable /rtabmap/initialpose).
   To hand a pose from CLI (reliable by default):
   `ros2 topic pub --once /rtabmap/initialpose geometry_msgs/msg/PoseWithCovarianceStamped "{header: {frame_id: map}, pose: {pose: {position: {x: X, y: Y, z: 0.0}, orientation: {x:0,y:0,z:QZ,w:QW}}, covariance: [0.0,0,0,0,0,0, 0,0.0,0,0,0,0, 0,0,0.0,0,0,0, 0,0,0,0.0,0,0, 0,0,0,0,0.0,0, 0,0,0,0,0,0.0]}}"`
2. map frame vs odom frame are NOT aligned here — feeding odom numbers as a map pose
   rotated the robot ~90 deg. Use the RViz click (map frame) for the initial pose.
3. install/share launch + world files are SYMLINKS to src, so src edits take effect
   (no rebuild needed for launch/world). Configs likewise symlinked.
4. The warehouse map is thin/warped in two corners (built from limited views). Lidar
   matched Gazebo ground truth there, not the map -> the MAP is wrong, not the pose.

## Startup pose — stop re-doing 2D Pose Estimate every bringup (2026-10-17)
Problem: RTAB-Map localization mode resumes at the LAST pose saved in the DB
(~2.22, 3.35, -118deg), NOT where Stormy spawns. So every bringup came up delocalized
and needed a manual 2D Pose Estimate. (Nav2 does NOT own the pose — it just reads
RTAB-Map's map->odom; the fix belongs to RTAB-Map.)
Fix: pass `initial_pose:="x y z roll pitch yaw"` to rtabmap.launch.py = Stormy's spawn
pose in the map (base_link in map at spawn). Captured via `tf2_echo map base_link`
right after a good relocalization AT SPAWN (before driving):
  x=0.736, y=1.981, yaw=-1.148 rad. Heading was a hair CW, so nudged to yaw=-1.19.
  Next bringup a true at-spawn capture gave x=0.638, y=1.802, yaw=-1.197 (the two eyeball
  captures vary ~0.2 m / few deg). Current value:
  => initial_pose:="0.638 1.802 0.0 0.0 0.0 -1.197"
  Gets RTAB-Map close enough to start; a tiny manual 2D Pose Estimate may still be needed
  some bringups (RTAB-Map doesn't fully refine heading in the aisle; eyeball captures vary).
  Pixel-perfect would need the sim ground-truth spawn pose (Gazebo model pose vs map origin).
Notes:
- Value is base_link-in-map (map->base_link), NOT map->odom. RTAB-Map applies it as the
  robot's map pose at startup and derives map->odom internally.
- Capture it only when Stormy is AT SPAWN (odom fresh). After he drives, map->base_link
  is his current spot, not spawn.
- Spawn is deterministic, so this constant is reusable. Keep it a sim command-line arg
  (do NOT bake into rtabmap.launch.py default — would wrongly affect the real robot).
- If heading still a touch off next bringup, nudge yaw by +/-0.02 rad.

## RTAB-Map mapping config facts (so we STOP rediscovering these) — 2026-10-17
- Reg/Force3DoF is ALREADY true in the running rtabmap (confirmed: `ros2 param get
  /rtabmap/rtabmap Reg/Force3DoF` -> true). It is set by the stingray rtabmap launch/config,
  NOT by the rtabmap.launch.py default rtabmap_args string (that default has only
  NeighborLinkRefining/ProximityBySpace/Reg-Strategy-0/Grid flags). Do NOT re-chase it.
- Occupancy grid: launch default builds the grid from DEPTH (--Grid/FromDepth true) and does
  NOT subscribe to the lidar. For a clean 2D warehouse grid, launch with:
    subscribe_scan:=true scan_topic:=/scan
    rtabmap_args:="... --Grid/FromDepth false ..."  (grid from LD19 scan, not depth noise)
- IMU: rtabmap imu_topic default is /imu/data (gz_bridge, RELIABLE). It is redundant here:
  ekf_filter_node_odom already fuses /imu/data into /odometry/local, which is rtabmap's
  odom source (rgbd odometry off). The per-frame "IMU won't be added to graph" warning is
  harmless (rtabmap's own visual-inertial odom is unused). Silence with imu_topic:="" if desired.
- GTSAM "Indeterminant linear system ... loop closure NNN->MMM rejected": occasional = normal
  (rtabmap refusing a bad loop closure). Only a concern if it fires on nearly every closure.
- Mapping launch used (fresh map, lidar grid):
```
ros2 launch articubot_one rtabmap.launch.py \
  rgb_topic:=/camera depth_topic:=/depth_camera camera_info_topic:=/camera_info \
  odom_topic:=/odometry/local frame_id:=base_link \
  use_sim_time:=true approx_sync:=true qos:=2 \
  localization:=false delete_db_on_start:=true publish_tf_map:=true \
  subscribe_scan:=true scan_topic:=/scan \
  rtabmap_args:="--RGBD/NeighborLinkRefining true --RGBD/ProximityBySpace true --Reg/Strategy 0 --Grid/FromDepth false --Grid/3D false --Grid/RayTracing true"
```
  (old warehouse DB backed up: ~/.ros/rtabmap_warehouse_2026-10-16.db.bak)

## Relay auto-start (DONE 2026-10-17)
Baked relay_initialpose.py into the sim bringup so it auto-starts with drive_sim:
- Copied script to `articubot_one/scripts/relay_initialpose.py`.
- Edited `launch/drive_sim.launch.py`:
  - added `import os` (top) and `ExecuteProcess` to the launch.actions import,
  - inserted as first item of `return LaunchDescription([...])`:
    `ExecuteProcess(cmd=["python3", os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "scripts", "relay_initialpose.py")], name="initialpose_relay", output="screen")`
  - path resolves via the launch file's own location (realpath follows the install symlink), so no rebuild.
  Backup: launch/drive_sim.launch.py.bak.
- On next drive_sim launch you'll see "initialpose relay up ..." in that terminal.
  ~/robot_ws/relay_initialpose.py is now redundant (kept as a manual fallback).

## Map cleanup session (afternoon) — IN PROGRESS, not finished
Goal: fix the warped warehouse map. Switched from the stale 167 MB DB to a FRESH SLAM map
(localization:=false, delete_db_on_start:=true) driven by the LD19 scan for the grid
(subscribe_scan:=true, --Grid/FromDepth false) — clean grid, not depth noise.
Confirmed along the way (do NOT re-chase): Reg/Force3DoF already true; IMU already in via
EKF /odometry/local (rtabmap's direct /imu/data is redundant, its "won't be added to graph"
warning is harmless); occasional GTSAM "indeterminant / loop closure rejected" is normal.
Only drove a short seed loop by joystick; coverage INCOMPLETE. Old DB backed up:
~/.ros/rtabmap_warehouse_2026-10-16.db.bak. Nav2 was NOT up this bringup (mapping only).

## Repo / notes / context reconciliation (evening) — DONE
Root cause of today's re-tread: handoff notes weren't being pushed, and context.txt lived
only in articubot_one on the Pi, so the HankRearden local VSCode window started blind and
OPEN read an OLD session-state note (10-10) instead of the committed latest (10-16).
Fixed, single source of truth now:
- stingray repo (JHPHELAN/stingray, HankRearden + GitHub + Pi): canonical context.txt at
  root; .github/copilot-instructions.md hardened (OPEN reads it + context.txt + NEWEST note);
  notes/ holds all 8 handoffs (10-03,10-05x2,10-09 migrated from articubot_one; 10-11/16/17
  backfilled from session-state). Commits e37a27b, f636181, 00d7d11.
- articubot_one (exploration): today's sim code committed (8d38791); robots/stingray/
  context.txt retired to a pointer + its 4 notes removed (77dc083). Pi pulled current.
- Cleaned stale HankRearden copies (2 dead stubs deleted, Code\context.txt -> redirect).

## TODO / next time (pick up refreshed)
1. FINISH THE MAP: drive full warehouse coverage in SLAM mode (lidar grid, Force3DoF on),
   revisit areas for loop closures, then SAVE the DB. Then try simultaneous nav+map via
   Nav2 waypoints (needs planner allow_unknown to push into unmapped aisles).
2. Set up HankRearden->LinuxBox SSH keys so Copilot can drive LinuxBox directly (user: yes).
3. Reconcile LinuxBox's PRE-EXISTING uncommitted work (NOT today's): description/oakd.xacro,
   launch/joystick.launch.py, robots/stingray/description/ldlidar.xacro (+ .bak), and
   untracked robots/stingray/date_index.txt, stingray_log.rtf, scripts/WiFiQuality.xml —
   decide commit vs discard.
4. Remove the stale SlamToolbox panel from config/main.rviz (silences "Waiting for
   slam_toolbox node configuration" spam + the /initialpose QoS-incompatibility warning).
5. Tidy stale inline comments in nav2_params_sim.yaml (L19/L62 wording now wrong).
6. Once the fresh map is solid: delete old DB backups.
