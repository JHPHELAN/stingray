# NOTES 2026-10-18 (PM) — House explore stack bring-up; the Force3DoF root cause

Machine: HankRearden (Windows laptop), local VSCode window on the stingray doc repo
(C:\...\stingray-repo = JHPHELAN/stingray). All robot-code work was done on **LinuxBox**
over passwordless SSH (JHPHELAN/articubot_one, branch exploration), driven from here via the
base64 remote-exec pattern, and later handed to the user to run segment-by-segment in PuTTY.
This continues TODO #0 from NOTES-2026-10-18-ssh-reconcile-rviz-nav2-cleanup.md. CHECKPOINT
note (session was long; written before close). Robot code edits are UNCOMMITTED on LinuxBox —
see "COMMIT THESE" below.

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

## Goal
Bring up the full sim explore stack in the AWS small_house world on LinuxBox and autonomously
map the house with frontier_explorer; tune explore.yaml for the sim house.

## RESULT — explore stack RUNS autonomously in the house (headless)
End state: rsp + drive_sim(small_house, headless) + RTAB-Map(MAPPING, 2D-locked) + Nav2 +
/map relay + frontier_explorer, all live. Robot spawns at the door, autonomously picks
frontier goals, Nav2 drives it, RTAB-Map builds the grid. Verified: goals COMPLETE (reached
goal 1, navigated to goal 2), robot moves (~0.08 m/s sim), Reg/Force3DoF=true, map->odom z=0.
It maps slowly (RTF ~0.22 headless) but correctly. explore.yaml scoring needed NO change —
the real-house tuning carried over; earlier "bad goals" were corrupted localization, not bad
frontier choice.

## THE BIG ONE — Reg/Force3DoF was never persisted (recurring root cause)
Symptom: robot would drive a few metres then "get stuck/trapped" — Nav2 kept issuing new paths
on a visibly clear path, robot crept ~0.01 m/s and went nowhere. NOT a physical pinch (lidar
showed open space) and NOT the control rate.
Data that nailed it: `ros2 run tf2_ros tf2_echo map base_link` -> z = **5.76 m** (robot
"floating"); `ros2 param get /rtabmap/rtabmap Reg/Force3DoF` -> **false**; map->odom z = 6.9 m
with roll/pitch tilt. RTAB-Map was running full 6-DOF SLAM with no 2D constraint, so map->odom
drifted ~7 m up + tilted -> Nav2's robot pose in the map was garbage -> it planned/controlled
against nonsense -> thrash. This also explains the earlier "messy map".
WHY IT NEVER STUCK (the user's question): `grep -rniE "Force3DoF|Slam2D"` across the whole
repo returned NOTHING. It was never in any config/launch/yaml. rtabmap.launch.py (our wrapper)
feeds params to upstream ONLY via the `rtabmap_args` STRING (no params file). The default
rtabmap_args has no Force3DoF, and any caller passing their own rtabmap_args REPLACES the whole
string. So in past sessions Force3DoF was only ever typed on the CLI, confirmed live, written
into notes — and lost when the terminal closed. Every fresh run reverted to RTAB-Map's default
(false).
PERMANENT FIX (committed-worthy): launch/rtabmap.launch.py now ALWAYS APPENDS
`--Reg/Force3DoF true --Optimizer/Slam2D true` to the `args` after the user's rtabmap_args
(later args win in RTAB-Map's parser, so it can't be clobbered). Stingray is a diff-drive
ground robot, so 2D is always correct. Verified live: Force3DoF=true, map->odom z=0, robot
navigates. (Backup /tmp/rtabmap.launch.py.bak.)

## What else changed / how (ALL on LinuxBox articubot_one exploration, UNCOMMITTED)

### assets/worlds/small_house.sdf — two world bugs from the 10-18 AM import
1. MISSING gz-sim SYSTEM PLUGINS. Ported AWS world had ZERO `<plugin>` entries; warehouse/
   test_robot_world have the full set. Without `gz-sim-sensors-system` the lidar/camera/IMU
   produce NO data (/scan had a publisher but 0 msgs; gz side /gz_scan was fine). Added the full
   set (Physics, UserCommands, SceneBroadcaster, Contact, Imu, Magnetometer, AirPressure,
   ApplyLinkWrench, NavSat, Sensors[ogre2]) right after `<world name='default'>`. NOTE: once a
   world lists ANY system plugin, gz stops auto-loading the default server.config set, so you
   must list the COMPLETE set (incl. Physics). (Backup /tmp/small_house.sdf.prebak.)
2. ROBOT INVISIBLE IN GAZEBO GUI (but fine in RViz). World-specific: robot renders in
   test_robot_world, not small_house. Cause: small_house `<gui>` had only a `<camera>`, missing
   the modern gz-gui plugins — crucially **GzSceneManager**, which syncs dynamically-spawned
   entities (our robot, spawned AFTER the 68 house models) into the GUI scene. Replaced the
   camera-only `<gui>` with the full warehouse-style gz-gui block (MinimalScene, EntityContext,
   GzSceneManager, InteractiveViewControl, CameraTracking, WorldControl, WorldStats). The robot
   entity + all visuals exist server-side (gz model --link, scene/info) — it was purely a GUI
   render gap. (We ran HEADLESS in the end, so this is moot for the session but worth keeping.)
   LESSON: do not burn time on the gz GUI robot render — RViz is the real monitor.

### launch/drive_sim.launch.py — headless for RTF
Added ' -s' to gz_args (server-only). RTF: ~0.097 with GUI -> **0.217 headless** (~2.2x).
The gz GUI never showed the robot anyway and we monitor in RViz, so the GUI render budget was
pure waste. (Backup /tmp/drive_sim.launch.py.headlessbak.) WARNING: `pkill "gz sim gui"` kills
the SERVER too (they're one launch) — don't try to restart just the GUI; it serverless-hangs.

### robots/stingray/config/nav2_params_sim.yaml
- allow_unknown false -> **true** (line ~431): so the planner can route to frontier goals at the
  known/unknown boundary (else explorer starves).
- controller_frequency 5.0 -> **3.0** (line 62) for the slow headless sim. BUT MPPI requires
  controller period (1/freq) <= model_dt, so also:
- MPPI model_dt 0.2 -> **0.34** (line 99). 5 Hz gave period 0.2 == model_dt 0.2 exactly; 3 Hz
  (period 0.333) > 0.2 threw `Controller period more then model dt` and Nav2 bringup ABORTED.
  0.34 >= 0.333 satisfies it. (NOTE: the control rate was a RED HERRING for the stall — the real
  stall cause was Force3DoF. These values are still reasonable for low RTF; revisit if twitchy.)

### robots/stingray/config/explore.yaml — sim tuning
- Added `use_sim_time: true` (line ~37). The explorer ran on WALL clock, so its 120 s
  goal_timeout = only ~12 s of robot motion at 0.1 RTF -> every goal timed out. Sim time makes
  the timeout 120 SIM-seconds.
- goal_timeout_sec 120 -> **180** (line ~202) headroom for slow-RTF drives.
- Scoring (goal_max_cost/clearances/distance weights) LEFT ALONE — works as-is in the house.

### /tmp/map_relay.py (NOT yet in repo — MUST be committed to scripts/)
The explorer subscribes /map (volatile); Nav2 reads /rtabmap/map directly. /rtabmap/map is
TRANSIENT_LOCAL (latched) and only re-publishes on map change -> a plain
`ros2 run topic_tools relay /rtabmap/map /map` (volatile) gets 0 msgs while stationary ->
explorer stuck on "Waiting for /map...". Fix = a tiny relay that SUBSCRIBES transient_local
(to get the latched grid) AND re-publishes /map at 1 Hz, latched (so the volatile explorer,
which only catches post-subscribe msgs, always gets it). Lives at /tmp/map_relay.py; should be
moved into scripts/ and ideally auto-started by explore.launch.py (like the initialpose relay).

## Working bring-up sequence (headless) — 6 segments, PuTTY terminals
Every GUI terminal still exports DISPLAY=:0 and XAUTHORITY=$(ls -t /run/user/1000/.mutter-Xwaylandauth.* | head -1).
PuTTY shells source ROS + CycloneDDS via ~/.bashrc automatically.
1. T1 rsp:    ros2 launch articubot_one rsp.launch.py robot_model:=stingray use_sim_time:=true
2. T2 drive:  ros2 launch articubot_one drive_sim.launch.py robot_model:=stingray robot_world:=small_house use_sim_time:=true initial_x:=6.0 initial_y:=-5.0 initial_yaw:=1.5708
   (headless now; RViz opens, NO gz window. Robot spawns at the door.)
   AFTER it loads: controllers lose the 5 s activation race at low RTF -> activate manually:
     ros2 control set_controller_state joint_broad active
     ros2 control set_controller_state diff_cont active
   then reset EKF (clears startup covariance drift):
     ros2 topic pub --once /set_pose geometry_msgs/msg/PoseWithCovarianceStamped "{header: {frame_id: odom}, pose: {pose: {position: {x: 0.0, y: 0.0, z: 0.0}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}}, covariance: [0.01,0,0,0,0,0, 0,0.01,0,0,0,0, 0,0,0.01,0,0,0, 0,0,0,0.01,0,0, 0,0,0,0,0.01,0, 0,0,0,0,0,0.01]}}"
   In RViz set Fixed Frame = odom until RTAB-Map is up, then switch to map.
3. T3 rtabmap (MAPPING; Force3DoF now auto-appended by the launch):
     ros2 launch articubot_one rtabmap.launch.py rgb_topic:=/camera depth_topic:=/depth_camera camera_info_topic:=/camera_info odom_topic:=/odometry/local frame_id:=base_link use_sim_time:=true approx_sync:=true qos:=2 localization:=false delete_db_on_start:=true publish_tf_map:=true subscribe_scan:=true scan_topic:=/scan rtabmap_args:="--RGBD/NeighborLinkRefining true --RGBD/ProximityBySpace true --Reg/Strategy 0 --Grid/FromDepth false --Grid/3D false --Grid/RayTracing true"
4. T4 nav2:   ros2 launch articubot_one navigation_launch.py use_sim_time:=true autostart:=true params_file:=/home/ubuntu/robot_ws/src/articubot_one/robots/stingray/config/nav2_params_sim.yaml
5. T5 relay:  python3 /tmp/map_relay.py     (NOT topic_tools relay — see above)
6. T6 explore: ros2 launch articubot_one explore.launch.py params_file:=/home/ubuntu/robot_ws/src/articubot_one/robots/stingray/config/explore.yaml

Teleport robot back to the door any time (clean restart): then re-do EKF reset + fresh RTAB-Map.
  gz service -s /world/default/set_pose --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean --timeout 3000 --req 'name: "stingray", position: {x: 6.0, y: -5.0, z: 0.1}, orientation: {x: 0, y: 0, z: 0.7071068, w: 0.7071068}'

## Spawn pose (the door)
AWS Door_01_001 is at gz world (6.001, -5.549, yaw 0); house bounds x[-9.4,9.4] y[-5.55,5.60],
so the door is in the SOUTH wall. "Into the house" = facing NORTH (+y) = yaw 1.5708. We spawn
just inside at initial_x:=6.0 initial_y:=-5.0 initial_yaw:=1.5708 (verified via the robot's RGB
cam: dining table/chairs/chandelier/fridge ahead = facing into the open interior).

## Key facts / lessons (don't re-chase)
- RTF: ~0.097 GUI, ~0.217 headless. Still slow; mapping the whole house ~30-60 min wall.
- CycloneDDS: ~/.bashrc sets RMW_IMPLEMENTATION=rmw_cyclonedds_cpp + CYCLONEDDS_URI
  (~/cyclonedds.xml: iface enp3s0f1, AllowMulticast false, unicast Peers .66/.99). Ephemeral
  `ros2 topic hz/echo` CLI nodes take ~10-15 s to discover -> use long timeouts; a reduced env
  that forgets RMW silently talks Fast DDS and sees nothing.
- Controller startup race: at low RTF the ros2_control spawners miss the 5 s switch window ->
  controllers come up INACTIVE -> `ros2 control set_controller_state ... active` after gz loads.
- /tf_static + /tf are fine; "flat wheels / no transforms" in RViz after a restart was just
  Fixed Frame = map before RTAB-Map publishes map -> set Fixed Frame = odom (cosmetic).
- gz model --link shows the reduced SDF (fixed joints lumped into base_link); chassis STL +
  wheels (cylinders in URDF, not STL) + OAK-D all present server-side.

## Overnight run outcome (user, 2026-10-18 PM) — thorough coverage, but map SKEWED
Over dinner Stormy auto-explored the WHOLE house (good coverage). Two problems remain:
- MAP SKEW not corrected: RTAB-Map kept REJECTING loop closures, e.g.
  `Rejected loop closure 1040 -> 2225: Not enough inliers 0/20 (matches=17)`. Visual loop
  closure (Reg/Strategy 0 = vis) isn't matching enough features (likely the 200x200 sim OAK-D
  is too low-res / texture-poor), so the graph never optimizes and the skew persists. Manual
  Nav2 goaling for loop closures did NOT help because the closures get REJECTED, not missed.
- PHANTOM EXTERIOR = SKEW ARTIFACT (user corrected my "frontier-leak" guess): the apparent
  "cracks to outside" are NOT real navigable gaps — the robot can't drive through walls. They
  are unmapped seams plus the SKEW painting content outside the house footprint. That exterior
  junk can NEVER be retraced/cleaned (the robot can't reach it), so it only clears by fixing
  the skew (accepted loop closures) or masking/bounding the map. The explorer did waste goals
  on unreachable exterior "frontiers" (a downstream consequence of the skew), but there is no
  real leak to plug.
- WM (working memory) reached the MID-900s nodes — a big pose graph with no accepted closures
  to tie it together.
User stopped for the night. Full disk backup of HankRearden taken today. Robot code pushed
(articubot_one exploration 5bf48bf).

## State at end
- Robot-code fixes COMMITTED + PUSHED: articubot_one exploration 954796f..5bf48bf
  (6 files + scripts/map_relay.py). The permanent Force3DoF fix is safe on GitHub.
- Backups /tmp/*.bak and untracked config/main.rviz.bak, launch/drive_sim.launch.py.bak left
  on LinuxBox; config/main.rviz had an unstaged working-tree change (not committed).
- Sim stack was left running overnight (or stopped by user); DB at ~/.ros/rtabmap.db NOT yet
  snapshotted (skew unresolved, not worth saving as-is).
- stingray repo (HankRearden): this note + context.txt update pushed to main.

## NEXT TIME / TODO
DECISION (user, 2026-10-18 PM): go with **(B) the REAL robot in the REAL house** next session —
"we've beaten the sim horse sufficiently." Sim stays as-is (skew unresolved, that's fine);
focus shifts to hardware, where real texture should make loop closures accept. Items 4/7
(sim-only fixes) are parked; item 5 is the plan; item 6 (gz world from a real scan) is the
stretch goal once there's a clean real-house map.
0. DONE this session — robot code committed + PUSHED (articubot_one exploration 5bf48bf):
   rtabmap.launch.py (Force3DoF/Slam2D append), small_house.sdf (system plugins + gz-gui),
   drive_sim.launch.py (-s headless), nav2_params_sim.yaml, explore.yaml, scripts/map_relay.py.
   RESIDUAL: auto-start map_relay from explore.launch.py (like the initialpose relay); clean up
   untracked /tmp/*.bak + config/main.rviz.bak on LinuxBox.
1. Decide headless vs GUI as the default for drive_sim (maybe a `headless:=` launch arg instead
   of hardcoding ' -s'), so warehouse/other worlds can still show the GUI.
2. Optional explore.yaml sim tuning: bump distance_score_weight (2.5 -> ~4-5) / drop
   cluster_score_cap (30 -> ~15) so it stops dashing cross-house and maps in shorter legs
   (more efficient at low RTF). Not required — it maps fine as-is.
3. Further RTF: the depth camera is the heaviest sensor; a lidar-only RTAB-Map or reduced
   depth rate would speed things up if full-house coverage is too slow.
4. FIX THE SKEW = make loop closures ACCEPT (they reject: "Not enough inliers 0/20 (matches=17)").
   Visual loop closure is starving on the 200x200 sim OAK-D. Try, in order:
   - lower Vis/MinInliers (default ~20) — we saw matches=17 vs 20, so a small drop may let real
     closures through (cheap first experiment);
   - switch registration to ICP or vis+ICP (Reg/Strategy 1 or 2, tune Icp/*) — the LD19 scan is
     dense + reliable and better suited to this 2D LIDAR robot than pure vision;
   - raise the sim OAK-D resolution (description/oakd.xacro was cut to 200x200@15Hz for RTF) —
     more pixels = more features = more inliers; trade against RTF.
   Skew will NOT clear until closures are accepted; manual Nav2 goaling alone cannot fix it.
5. REAL-ROBOT PIVOT (user idea, likely the better path): tomorrow maybe stop simulating and run
   the REAL robot in the REAL house. Real texture + lighting + the full-res OAK-D should make
   visual loop closures actually ACCEPT — directly fixing tonight's reject problem — instead of
   fighting a texture-poor imaginary house. Use the normal stingray hardware stack + this same
   RTAB-Map(MAPPING, 2D-lock)/Nav2/explore recipe (minus the sim-only bits).
6. BUILD-A-GAZEBO-WORLD-FROM-A-REAL-SCAN (user idea, feasible): make a gz world of the real
   house from an RTAB-Map scan. The DB (~/.ros/rtabmap.db, SQLite) stores RGB+depth keyframes,
   LIDAR scans, the optimized pose graph, and the 2D grid. Path: rtabmap-databaseViewer ->
   File -> "Export 3D clouds/mesh" with meshing + texture ON -> textured OBJ (+ material/PNG);
   import that as a STATIC gz model (mesh <visual>; simplified <collision> from the occupancy
   grid extruded to walls, or convex decomposition — a dense mesh collision is RTF-heavy).
   Real-photo textures = strong features = exactly what the AWS house lacked. Non-trivial (mesh
   holes/noise, collision simplification) but a known, worthwhile workflow.
7. (If staying in sim) bound the explorer to the house footprint / mask the exterior so it stops
   selecting unreachable outside "frontiers"; and add a `headless:=` launch arg to drive_sim
   instead of hardcoding ' -s' (so warehouse/other worlds can still show the GUI).
