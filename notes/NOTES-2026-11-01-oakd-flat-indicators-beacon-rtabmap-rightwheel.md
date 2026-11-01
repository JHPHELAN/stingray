# NOTES 2026-11-01 — OAK-D flat (wedge removed), indicators beacon self-test, RTAB-Map g2o re-run aborted by right-wheel setscrew

Machine: HankRearden (Windows laptop), AI session driving the Stingray Pi over SSH.
Rebooting HankRearden; this is the handoff. Today's robot-code commits are on
articubot_one exploration; docs/notes on stingray main. All pushed (see below).

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

## 1. OAK-D wedge REMOVED — camera now mounted FLAT (pitch=0)
Decision (user): the original flat position is the sweet spot, so pull the wedge.
Geometry: OAK-D depth min range ~0.20 m; depth V-FOV 50 deg -> the bottom-edge ray sits
25 deg below the (now horizontal) optical axis; 0.20*sin25 = 8.5 cm drop ~= the 9 cm lens
height, so the floor lands right at the camera's minimum range with NO wedge. The 25 deg
wedge over-tilted (RGB bottom edge ~14 deg ABOVE horizontal -> blind to the near floor).
User also pulled a shrink-tube shim so the camera is physically flat (no residual nose-down).

Robot code (articubot_one exploration, 917019c):
- robot.urdf.xacro: dropped the oakd_wedge include + call; restored the base_link->oakd joint
  at pitch=0 (this also drops the old ~1.55 deg nose-down floor-flatness cal, pitch 0.027).
- Deleted description/oakd_wedge.xacro and assets/meshes/oakd_wedge.stl.
- Footprint reverted to pre-wedge: nav2 front vertices 0.1457 -> 0.123 in nav2_params /
  nav2_params_mapping / nav2_params_sim; robot_core.xacro oakd_x_length 0.0582 -> 0.033.
- colcon built clean; user launch-tested, RViz looked good (camera flat, robot renders).
Docs (stingray main, 54f2915):
- README wedge section -> short "tried then removed, and why" retrospective + a flat-vs-wedged
  floor-view comparison (kept images/OAK-D view from dock wedged.png for the comparison per
  user; dropped the wedge-era USB cable note per user).
- Removed 4 wedge build photos + CAD/3D Print/oakd_tilt_wedge_25deg.step + CAD/CorelDraw/
  01 OAK-D Center Plate Wedge.cdr. context.txt OAK-D fact rewritten to the flat mount.

## 2. Indicators boot BEACON self-test added (articubot_one exploration, e6139d5)
indicators_node.py previously boot-tested only the headlights (headlights_startup_on_sec, 3 s).
Added a parallel beacon self-test so the amber beacon is exercised at startup too:
- new param beacon_startup_on_sec (default 3.0) in the node + indicators.yaml.
- _tick: during the boot window (one-shot, mirrors the headlights test) force beacon_should_be_on
  True so the amber LED blinks AND the beacon WAV (klingon_alert.wav, already the beacon_sound_path)
  plays once; then off + log "Boot beacon self-test ended".
- _maybe_play_sound(now, force=False): new force flag bypasses the _sound_enabled gate so the
  klingon clip sounds even though beacon sound defaults OFF at runtime.
Built + user tested: "Perfect!". Set beacon_startup_on_sec: 0.0 to disable.

## 3. PR #4 roboclaw_driver — signed off, waiting on Mike (no action on user)
wimblerobotics/roboclaw_driver PR #4 (your main_battery_scale/offset calibration). Mike reviewed,
caught a real bug (your unconditional calibration re-applied the offset to the stale voltage on
FAILED reads -> monotonic drift on CRC errors / -1.525 V at startup), and pushed fix 117dbc2
("Calibrate only successful battery reads": read_successful out-ref + local raw buffer, commit
raw*scale+offset only on success). You already approved the direction 2026-10-01 (GitHub blocks
self-approve on an authored PR). PR is OPEN, dormant ~31 days -> ball is on MIKE to merge. Your
robot's local/stingray branch already carries the work, so nothing is blocked. You deleted the
nag emails. (Fetched via public GitHub REST API + curl; gh CLI not installed on HankRearden,
github-mcp-server failed to connect this session.)

## 4. keepout / stingln aliases — no change made
stingln alone complains when keepout isn't running (nav2_params.yaml hard-wires
filters: ["keepout_filter"] on BOTH costmaps -> each KeepoutFilter waits forever for
/costmap_filter_info). There is no "warn once" in Nav2's C++ plugin. We discussed an auto-detect
launch change but DROPPED it: you already have alias launchkeepout="keepout & stingln" which does
exactly "keepout first, then the stack". USE launchkeepout for house nav; stingln bare for
no-keepout (just ignore the one-time complaint, don't use it alone). Aliases live in
~/.bash_aliases on the Pi (unchanged; I briefly edited stingln then reverted it). Tip: run
`alias <name>` to print an alias's expansion.

## 5. RTAB-Map g2o re-run — OAK USB fault fixed, run then ABORTED by the right wheel
### 5a. OAK-D was not streaming -> ROOT CAUSE: USB cable not fully snapped into the OAK-D
Symptom: /oak node + oak_container up, but /oak/rgb/image_rect at 0 Hz and NO /oak/stereo/image_raw
or /oak/rgb/camera_info. dmesg showed the Movidius (03e7:2485 bootloader) stuck in an
enumerate -> "error -71" -> disconnect loop, enumerating at FULL-SPEED (USB 1.1!) on a USB2 bus;
both USB3 (5000M) buses empty. Fix: reseated; user then switched to the shorter cable (now reaches
with the wedge gone) in a BLUE USB3 port -> device booted 2485->f63b on Bus 005 (5000M USB3),
streaming rgb 3.9 Hz / stereo 5.0 Hz / camera_info 5.0 Hz (odom 20, scan 10). Added as a stable
OAK-D USB troubleshooting line to context.txt.
### 5b. g2o optimizer fix looked PROMISING (not yet validated through loop closures)
Launched rtabmap ON THE PI with the recipe + the fix --Optimizer/Strategy 1 (GTSAM -> g2o).
Startup HEALTHY: synced data (no "did not receive data"), and crucially NO "Indeterminant linear
system" warning (the GTSAM failure from 10-31). Only benign param-migration WARNs
(Grid/FromDepth->Grid/Sensor; Optimizer/Slam2D->Reg/Force3DoF=true, which confirms the 2D lock).
map_relay (/rtabmap/map -> /map latched) + RViz up. BUT we never reached return-to-dock loop
closures, so g2o is not yet proven on the hard case.
### 5c. ABORTED mid-drive: right-wheel setscrew loose AGAIN
During the hand-drive Stormy started circling AROUND the right wheel = right wheel not driving
(left wheel pushes, pivots around the dead right wheel). This is the recurring right-wheel
setscrew (loose 3x now: delocalized 10-19, "fixed" 10-28, loose again 11-01). The encoder keeps
counting so odom LIES -> map is garbage. Run ABANDONED, db NOT saved. Stack cleanly killed with
pkill (one SSH exit-255 mid-kill was just a WiFi blip; reconnect confirmed ALL STOPPED). Robot safe.

## >>> NEXT SESSION <<<
1. FIX the right-wheel setscrew. Use blue Loctite 242 — friction alone has not held it (3x).
   Confirm the wheel is seated flush on the shaft flat.
2. RE-VERIFY ODOMETRY TRUTHFUL before mapping: slow straight-line forward + a turn, check
   /odometry/local heading and displacement track reality (like the 10-31 sanity test).
3. CONFIRM OAK STREAMING (reseat check): lsusb shows 03e7:f63b on a 5000M bus; /oak/stereo/image_raw
   ~5 Hz. If it loops/error-71, reseat firmly into a blue USB3 port.
4. RE-RUN the SAME RTAB-Map command below (the g2o fix is already in it; no config changes). Drive
   a LIMITED area, gentle, loop back toward the dock. Watch the rtabmap terminal: NO "Indeterminant
   linear system" and GlobalClosure climbing (>1) in rtabmap-info before trusting the map. If g2o
   STILL throws indeterminant on a loop closure, add --Optimizer/GravitySigma 0. Finalize: Ctrl-C
   rtabmap to flush the SQLite db, THEN copy it (delete_db_on_start overwrites ~/.ros/rtabmap.db
   next run); pull the keeper to HankRearden ...\Stingray\Maps\.

## RE-RUN RECIPE (rtabmap ON THE PI) — carry forward
Each line its own terminal; source ros2 jazzy + ~/robot_ws/install/setup.bash first.
  T1 (Pi): ros2 launch articubot_one stingray.hardware.launch.py
    (hardware-only: rsp + drive + sensors + EKF, NO slam_toolbox / NO Nav2, so rtabmap owns the
     map. Do NOT use the full stingln here. The robot "vanishing" at Fixed Frame=map until rtabmap
     publishes map->odom is EXPECTED, not a bug.)
  T2 (Pi): ros2 launch articubot_one rtabmap.launch.py \
      rgb_topic:=/oak/rgb/image_rect depth_topic:=/oak/stereo/image_raw \
      camera_info_topic:=/oak/rgb/camera_info odom_topic:=/odometry/local \
      frame_id:=base_link approx_sync:=true qos:=2 localization:=false \
      delete_db_on_start:=true publish_tf_map:=true subscribe_scan:=true scan_topic:=/scan \
      rtabmap_args:="--RGBD/NeighborLinkRefining true --RGBD/ProximityBySpace true \
      --Reg/Strategy 0 --Grid/FromDepth false --Grid/3D false --Grid/RayTracing true \
      --Optimizer/Strategy 1"
    (NO compressed:=true on-Pi. --Optimizer/Strategy 1 = g2o is THE fix for the 10-31 GTSAM
     indeterminant failure. Add --Optimizer/GravitySigma 0 only if g2o still fails.)
  T3 (Pi): python3 ~/robot_ws/src/articubot_one/scripts/map_relay.py
  RViz (LinuxBox): rviz2 -d ~/robot_ws/src/articubot_one/config/main.rviz   (Fixed Frame = map)
  Joystick (LinuxBox): ros2 launch articubot_one joystick.launch.py

## Parked (carry)
- FLOOR-FLATNESS CAL: now largely moot — the camera is flat (pitch=0). Only re-probe clean floor
  and re-add a small residual pitch to the oakd_joint if the costmap shows a sloped floor.
- wifi v2 limitations to report to Mike (passive = associated-AP only; zero-dBm glitch), from 10-26.
- ros2-testing -> stable ros2 channel migration still TODO (context.txt).

## Commits pushed this session
- articubot_one exploration: 917019c (OAK-D flat, wedge removed), e6139d5 (indicators beacon self-test).
- stingray main: 54f2915 (README/context OAK-D flat), plus this note + context.txt (right-wheel
  setscrew + OAK-D USB stable facts).
