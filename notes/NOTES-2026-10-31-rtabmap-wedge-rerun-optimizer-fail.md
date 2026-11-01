# NOTES 2026-10-31 — RTAB-Map wedge re-run: pipeline fixed, odom truthful, GTSAM optimize FAILED

Machine: HankRearden (Windows laptop), AI session driving the Stingray Pi over SSH.
This is the second note dated 2026-10-31 (the first was the OAK-D wedge footprint /
README / CAD reorg). This one executes the parked "RTAB-Map wedge re-run, DRIVE BY
HAND" task from that note.

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
   activity belongs in NOTES-, NOT context.txt.
3. PUSH (notes/context -> JHPHELAN/stingray main; robot code -> JHPHELAN/articubot_one exploration).
   Session-state copies are DRAFTS only — unpushed = invisible next time.

## What we did
colcon build of articubot_one was done (user) so last session's wedge/footprint edits
(48a2968) are now live from install/share. Then ran the hand-driven RTAB-Map re-run.

## Finding 1 — "robot vanishes" in RViz with stingray.hardware.launch.py is EXPECTED
With the full stingray.launch.py, RViz at Fixed Frame=map shows the robot. With
stingray.hardware.launch.py the robot disappears and RViz throws many TF errors; at
Fixed Frame=base_link the robot renders fine and the only complaint is missing
map->base_link. This is NOT a wedge/URDF problem. Both launch files run the IDENTICAL
rsp.launch.py + drive + sensors; the ONLY difference is that stingray.launch.py also
starts the localizers (slam_toolbox) + Nav2. slam_toolbox is what publishes map->odom.
hardware-only OMITS it ON PURPOSE so RTAB-Map can own the map. Once RTAB-Map runs and
publishes map->odom, the robot reappears at Fixed Frame=map. Red herring resolved.

## Finding 2 — RTAB-Map "did not receive data" ROOT CAUSE: compressed:=true on-Pi
rtabmap was launched this time ON THE PI with compressed:=true (copied from the old
LinuxBox recipe). That inserts two image_transport republish/decompress nodes:
  republish_rgb:   /oak/rgb/image_rect/compressed      -> /oak/rgb/image_rect_relay
  republish_depth: /oak/stereo/image_raw/compressedDepth -> /oak/stereo/image_raw_relay
The depth side is FATAL: there is no /oak/stereo/image_raw/compressedDepth topic. The
OAK publishes depth only as /oak/stereo/image_raw/compressed (plain compressed), so
republish_depth waits forever, /oak/stereo/image_raw_relay stays empty, and the
approx-sync (which needs ALL inputs) never fires -> "did not receive data since 5s".
Diagnosis trail: topic info showed publishers present but the two *_relay topics at 0 Hz;
camera_info (RELIABLE) arrived but the images (via dead relays) did not; node info showed
republish_* subscribed to the compressed sources; ps showed the full launch args.

FIX (applied, worked): relaunch WITHOUT compressed:=true, feeding the raw topics directly
(/oak/rgb/image_rect 5 Hz, /oak/stereo/image_raw ~4.7 Hz). No republish nodes; rtabmap
subscribes to the raw images. compressed:=true is ONLY for running rtabmap REMOTELY on
LinuxBox (images must cross WiFi compressed, decompressed on the far side). On-Pi = raw
direct. (Added as a stable procedure line to context.txt.)

## Finding 3 — ODOMETRY IS TRUTHFUL (the 10-19 delocalization is NOT recurring)
Sanity-checked /odometry/local before mapping (the 10-19 run delocalized on lying odom /
loose right-wheel setscrew):
  Forward test: user turned ~45 deg left then drove straight; odom reported +46 deg
    heading (matches physical turn) and 117 cm vs 122 cm real straight-line (~4% short).
  Reverse test: drove straight back; heading held (-0.7 deg), displacement anti-parallel
    to heading (no sideways slide), ended within ~3 cm of origin/dock.
Conclusion: encoder odometry truthful both directions, negligible drift. Good to map.

## Finding 4 — MAP QUALITY: optimization FAILED (the real problem this run)
Hand-drove ~32 min, 1681 nodes. BUT the map is NOT usable:
  - rtabmap terminal spammed GTSAM "Indeterminant linear system detected / underconstrained
    variables" every cycle; each optimize failure REJECTED the loop closure being added
    (1679->1628, 1680->1623, 1681->1610, ... all near the dock on return).
  - rtabmap-info: only 1 successful GlobalClosure; "optimized graph" poses flung to ~1e7+
    meters (garbage); 1 session, 1681 LTM / 191 WM nodes.
  - rtabmap-export --map aborts: "The optimized graph is empty!? Aborting".
So loop closures WERE being detected (robot correctly recognized the dock area), but the
pose-graph optimizer could not solve the graph, so none were applied and the global map
never corrected drift. Data/drive are fine; this is a pure OPTIMIZER/CONFIG failure, NOT
the wedge, footprint, compressed-fix, or odometry.
Stored config (from the db): Optimizer/Strategy=2 (GTSAM), Optimizer/GravitySigma=0.3,
Reg/Force3DoF=true, Optimizer/Robust=false, Optimizer/Iterations=20, RGBD/OptimizeMaxError=3.0.
GTSAM + IMU gravity constraints (GravitySigma=0.3) under forced-2D (Force3DoF=true) is a
classic trigger for exactly this indeterminant/underconstrained failure.

## DB saved (ritual worked this time — last run's was scrambled/unsaved)
Ctrl-C rtabmap to FINALIZE (closes/flushes the SQLite db), THEN copy. Note
delete_db_on_start:=true overwrites ~/.ros/rtabmap.db on the next run, so copy first.
On the Pi:
  ~/rtabmap-final-20261031-212639.db   353 MB  (clean Ctrl-C finalize — the KEEPER)
  ~/rtabmap-snapshot-20261031-212530.db 340 MB  (insurance copy taken while still running)
Pulled the final db to HankRearden (NOT in git — too big; lives with the other Stormy maps):
  C:\...\Robotics\Parallax\Stingray\Maps\rtabmap-final-20261031-212639.db

## Correct launch recipe (rtabmap ON THE PI) — carry forward
Each line its own terminal; source ros2 jazzy + install/setup.bash first.
  T1 (Pi): ros2 launch articubot_one stingray.hardware.launch.py
  T2 (Pi): ros2 launch articubot_one rtabmap.launch.py \
      rgb_topic:=/oak/rgb/image_rect depth_topic:=/oak/stereo/image_raw \
      camera_info_topic:=/oak/rgb/camera_info odom_topic:=/odometry/local \
      frame_id:=base_link approx_sync:=true qos:=2 localization:=false \
      delete_db_on_start:=true publish_tf_map:=true subscribe_scan:=true scan_topic:=/scan \
      rtabmap_args:="--RGBD/NeighborLinkRefining true --RGBD/ProximityBySpace true \
      --Reg/Strategy 0 --Grid/FromDepth false --Grid/3D false --Grid/RayTracing true"
    (NO compressed:=true on-Pi. compressed:=true is LinuxBox-remote ONLY.)
  map_relay (Pi): python3 ~/robot_ws/src/articubot_one/scripts/map_relay.py
  RViz: rviz2 -d ~/robot_ws/src/articubot_one/config/main.rviz   (Fixed Frame = map)
  Joystick (LinuxBox): ros2 launch articubot_one joystick.launch.py

## >>> NEXT CHAT: RTAB-Map re-run with OPTIMIZER FIX <<<
Everything else is good (wedge, footprint, compressed-omitted launch, odometry). Only the
pose-graph optimize failed. On the re-run, add to rtabmap_args:
  PRIMARY: --Optimizer/Strategy 1      (switch GTSAM -> g2o; g2o/TORO tolerate the
                                         conditioning that made GTSAM indeterminant)
  IF STILL FAILING: --Optimizer/GravitySigma 0   (drop the IMU gravity constraints that
                                         are redundant/conflicting under Reg/Force3DoF)
  Optionally --Optimizer/Robust true only if it does not conflict with Force3DoF.
Watch the rtabmap terminal for the "Indeterminant linear system" WARN to be GONE and for
GlobalClosure count to climb (>1) in rtabmap-info before trusting the map. Re-drive a
LIMITED area, gentle slow turns (5 Hz camera), pause at corners. Finalize + copy the db
the same way.

## >>> NEW FINDING: the 25 deg wedge is OVER-TILTED — decide new angle tomorrow <<<
User observation after the drive: the 25 deg uptilt DOES kill ground clutter (goal met),
BUT the camera now can't see the near floor — missing low ground obstacles and floor
visual landmarks needed for driving. Lens is only ~95 mm off the floor.
Geometry (user-measured, confirmed): RGB view's LOWER edge is ~10 cm off floor at the
camera and ~20 cm off floor at ~40 cm ahead -> rises 10 cm over 40 cm -> atan(0.25) =
~14 deg ABOVE horizontal. So the RGB bottom edge points 14 deg UP (never sees floor).
Why: wedge_tilt=25 deg was sized as HALF the STEREO-DEPTH V-FOV (~50 deg), which puts the
DEPTH bottom edge at the horizon (that is what removed depth clutter). But the RGB stream
is much NARROWER (user's two points imply RGB V-FOV ~22 deg), so the RGB bottom edge sits
~14 deg higher than the depth bottom edge. Not a miscal — wedge sized to the wide depth FOV.
Core tradeoff (lens 95 mm up): cannot BOTH exclude near-floor clutter AND see near-floor
landmarks/obstacles; wedge angle trades one for the other directly. At 95 mm, reducing the
wedge to W deg gives depth-bottom-edge floor hit at 0.095/tan(25-W) and RGB-bottom-edge at
(W-11) deg above horizon:
  W=25 (now): depth floor at infinity; RGB 14 deg up  (the "blind to floor" state)
  W=15:       depth floor from ~0.55 m; RGB 4 deg up
  W=11:       depth floor from ~0.38 m; RGB bottom exactly at horizon (user's stated target)
  W=8:        depth floor from ~0.31 m; RGB floor from ~1.8 m
  W=0 (none): depth floor from ~0.20 m; RGB floor from ~0.49 m
Reminder: the OAK-D depth was ADDED for LOW-obstacle detection below the lidar plane
(NOTES-2026-10-03); 25 deg uptilt defeats that. A smaller wedge serves the depth's real
job; leftover clutter should be handled by costmap height-filtering, not by blinding the sensor.
DECISION NEEDED (sets the angle): optimize RGB floor view vs depth low-obstacle view, and
target floor distance in front (~0.5 m? ~1 m?). Shim-test first (prop camera to a candidate
angle / pull wedge for the 0 deg extreme, view live /oak + costmap) was deemed mechanically
tricky by user — may just pick an angle and reprint. To change the angle: edit CAD/wedge.py
(stingray repo) tilt, update wedge_tilt in articubot_one description/oakd_wedge.xacro, and
re-export assets/meshes/oakd_wedge.stl + the CAD/3D Print/*.step. This SUPERSEDES/extends the
floor-flatness-cal parked item below (the residual-pitch cal is moot until the wedge angle
is resettled).

## Other parked (unchanged)
- FLOOR-FLATNESS CAL (from NOTES-2026-10-28): re-probe clean floor with the physical 25 deg
  wedge mounted; re-add a small residual pitch to oakd_joint if the costmap sees a sloped floor.
- wifi v2 limitations to report to Mike (passive=associated-AP only; zero-dBm glitch),
  from NOTES-2026-10-26.
- ros2-testing -> stable ros2 channel migration still TODO (context.txt).
