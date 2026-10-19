# NOTES 2026-10-19 — First REAL robot / REAL house RTAB-Map + Nav2 + explore run; delocalized + erratic-drive abort

Machine: HankRearden (Windows laptop), local VSCode window on the stingray doc repo
(C:\...\stingray-repo = JHPHELAN/stingray). All robot work driven from here over passwordless
SSH: hardware + Nav2 on the Stingray Pi (`ssh ubuntu@192.168.68.66`), and RTAB-Map + map_relay +
explorer + RViz on LinuxBox (`ssh LinuxBox`), both on JHPHELAN/articubot_one branch `exploration`.
This executes the 2026-10-18 DECISION to pivot from the sim to the real robot in the real house.

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
Bring up the full explore stack on the REAL robot in the REAL house (real texture should make
RTAB-Map loop closures accept, unlike the texture-poor sim), and autonomously map the house.

## Architecture this session (split across two machines)
- Stingray Pi: T1 hardware (new stingray.hardware.launch.py) + T3 Nav2 (navigation_launch.py).
  Nav2 runs ON the robot so the cmd_vel control loop and /scan stay local (safe over WiFi; only
  /map crosses in, goals cross in — both small).
- LinuxBox: T2 RTAB-Map (MAPPING) + a local RGB republisher + T4 scripts/map_relay.py +
  T5 explore.launch.py + RViz. Heavy perception/planning offloaded here; Pi has headroom because
  RTAB-Map is NOT local (vs the normal stack's slam_toolbox).

## COMMITTED this session (articubot_one exploration: 5bf48bf -> bdc9f57 -> ade00cc)
- robots/stingray/launch/stingray.hardware.launch.py (NEW): hardware-only bringup =
  rsp + stingray.drive + stingray.sensors, with NO localizer (slam_toolbox) and NO built-in Nav2.
  Needed because stingray.launch.py is a FULL stack (it starts slam_toolbox + Nav2 internally,
  no flag to disable), which would fight an external RTAB-Map for the map->odom TF.
- launch/rtabmap.launch.py: now forwards `compressed` / `rgb_image_transport` /
  `depth_image_transport` to the upstream rtabmap_launch (defaults off). Upstream `compressed:=true`
  spins its OWN republishers that pull <rgb>/compressed + <depth>/compressedDepth and decompress
  locally — the clean way to feed a REMOTE RTAB-Map over WiFi. (We did NOT end up using it this
  run; see WiFi-image note below.)
- robots/stingray/config/nav2_params_mapping.yaml (NEW): EXACT copy of the tuned nav2_params.yaml
  with ONLY: (a) KeepoutFilter removed from both costmaps, (b) inflation_radius 0.50->0.30,
  (c) oak_points dropped from both costmaps' observation_sources. Proven by `diff` to be otherwise
  byte-identical to the house-tuned nav2_params.yaml. NOT a generic yaml. (b)/(c) are TONIGHT'S
  real-house TEST values — revisit, see "tuning" below.
- robots/stingray/config/explore.yaml: use_sim_time true->false (CRITICAL real-robot bug — see
  below) and goal_timeout_sec 180->60.

## THE real-robot BRING-UP RECIPE (what actually worked)
Stingray (T1, T3):
  T1: ros2 launch articubot_one stingray.hardware.launch.py
  T3: ros2 launch articubot_one navigation_launch.py autostart:=true \
        params_file:=/home/ubuntu/robot_ws/src/articubot_one/robots/stingray/config/nav2_params_mapping.yaml
LinuxBox (RGB republisher, T2, T4, T5, RViz):
  RGB decompress (raw RGB will NOT cross WiFi — see below), run on LinuxBox:
    ros2 run image_transport republish --ros-args -p in_transport:=compressed -p out_transport:=raw \
      -r in/compressed:=/oak/rgb/image_raw/compressed -r out:=/oak/rgb/image_raw_uncompressed
  T2: ros2 launch articubot_one rtabmap.launch.py rgb_topic:=/oak/rgb/image_raw_uncompressed \
        depth_topic:=/oak/stereo/image_raw camera_info_topic:=/oak/rgb/camera_info \
        odom_topic:=/odometry/local frame_id:=base_link approx_sync:=true qos:=2 \
        localization:=false delete_db_on_start:=true publish_tf_map:=true subscribe_scan:=true \
        scan_topic:=/scan rtabmap_args:="--RGBD/NeighborLinkRefining true --RGBD/ProximityBySpace true --Reg/Strategy 0 --Grid/FromDepth false --Grid/3D false --Grid/RayTracing true"
  T4: python3 /home/ubuntu/robot_ws/src/articubot_one/scripts/map_relay.py
  T5: ros2 launch articubot_one explore.launch.py \
        params_file:=/home/ubuntu/robot_ws/src/articubot_one/robots/stingray/config/explore.yaml
  RViz: rviz2 -d ~/robot_ws/src/articubot_one/config/main.rviz   (Fixed Frame = map)
Real sensor topics (confirmed live): /odometry/local (EKF, ~20 Hz), /scan (LD19, ~11 Hz),
  /imu/data, /oak/rgb/image_raw(+/compressed), /oak/rgb/image_rect(+/compressed),
  /oak/stereo/image_raw (depth, aligned to RGB, 400P, capped ~3 m), /oak/rgb/camera_info,
  /oak/points (Nav2 local only).

## KEY LESSONS / FACTS (don't re-chase)
- RAW IMAGES DO NOT CROSS WiFi to a remote RTAB-Map. The big raw rectified RGB from the
  rectify node (reliable QoS) never reached LinuxBox, while best-effort depth + camera_info did.
  FIX: feed RTAB-Map the COMPRESSED RGB and decompress locally (image_transport republish on
  LinuxBox; validated 5 Hz). depth stays raw and crosses fine (~2.5 MB/s). The upstream
  `compressed:=true` would do both rgb(compressed)+depth(compressedDepth) itself, but depth has
  no compressedDepth publisher in our OAK config and we did not pursue adding it.
- OAK-D is fragile to reconfig AND I wrongly blamed it for a "crash": when I added compressedDepth
  to the stereo whitelist and T1 was restarted, I saw no OAK topics and concluded the driver
  crashed. FACTS corrected it: /scan, /imu, /odom were ALSO silent at that moment — T1 was simply
  down (user was reconfiguring), not a driver crash. Lesson: check whether the WHOLE stack is down
  before blaming one node. OAK config was restored to known-good (rgb raw+compressed, stereo
  raw+compressed) and came back fine.
- explore.yaml use_sim_time:true (set during the sim sessions) = FROZEN explorer on the real
  robot. /clock exists only because the explorer SUBSCRIBES to it (0 publishers); with sim time
  the explorer's timers never fire -> "it just sits there". Set use_sim_time:false for real.
- RViz display: LinuxBox auto-logs-in a GNOME Wayland session on seat0 => DISPLAY=:0 is the
  PHYSICAL desktop (user runs RViz directly there). The sim-era `export DISPLAY=:0` habit is fine
  on the physical desktop. (I initially mis-guessed a NoMachine :1001 virtual display — WRONG;
  user corrected: he is on the physical desktop.)
- Nav2 "intimidated by a tight costmap" indoors: inflation_radius 0.50 was too fat for ~0.8-1.0 m
  hallways (whole corridor high-cost) -> MPPI dithered/retreated and the explorer rejected
  corridor paths (cost 96/99 pinch). Dropping to 0.30 gave a low-cost lane; footprint collision
  checking (consider_footprint:true) keeps it safe.
- "Non-existent obstacles" = OAK-D stereo (oak_points) PHANTOMS (the config comments already warn
  about carpet/grout/dust phantoms marked into the GLOBAL costmap). RTAB-Map's grid is lidar-based
  (Grid/FromDepth false), so the static map was clean; the phantoms were the live Nav2 obstacle
  layer. Dropped oak_points from both costmaps -> lidar-only. Trade-off: no low/overhang obstacle
  coverage; re-enable with tighter filtering later if wanted.
- goal_timeout 180 was a slow-sim value. Real robot moves at real speed; 60 s gives ~3x faster
  self-recovery when MPPI wedges (Nav2 does NOT self-abort a wedged doorway goal).

## THE INCIDENT — delocalized, then erratic drive, RoboClaw kill switch
Progression: Stormy explored MOST of the house (overall map "fairly accurate but ragged/
incomplete"), with occasional doorway wedges the user joysticked out of. Then RTAB-Map DELOCALIZED
(local map skewed; a lethal cell appeared right at the robot (-0.24,1.18) so EVERY frontier path
was rejected and the planner returned status 6). Shortly after, Stormy "had a stroke" and drove
erratically; user pulled the RoboClaw kill switch.
LOG FORENSICS (what the logs DO show): NOTHING crashed or faulted. Hardware run 14-09-19:
roboclaw_driver, ldlidar, bno08x (respawn-enabled, never respawned), EKF, OAK all started cleanly
and only stopped on the 15:21 Ctrl-C. Nav2 run 15-05-27: all servers finished cleanly on shutdown.
No CRC / overcurrent / timeout / respawn / segfault anywhere. The user also ruled out physical
faults (no thrown wheel, no axle hairball). => The erratic drive was NOT a hardware or software
fault; it was Nav2 COMMANDING bad velocities against a scrambled pose (robot's map-position wrong
-> controller drives the "map robot" to the goal -> erratic in the real world). Kill switch was
correct.
WHAT THE LOGS CANNOT SHOW: WHY RTAB-Map delocalized. RTAB-Map/Nav2 node output was output='screen'
(terminal only); the per-run ~/.ros/log dirs hold only launch.log, so there is NO file record of
the loop-closure / odometry event that scrambled the pose. The pose graph IS still in
~/.ros/rtabmap.db on LinuxBox for offline inspection (rtabmap-databaseViewer). Unproven hypothesis:
doorway wedging -> wheel slip -> EKF odom error -> RTAB-Map couldn't loop-close -> pose jump.

## ROOT CAUSE FOUND (post-session, user) — LOOSE RIGHT-WHEEL SETSCREW
After the run, on a fresh normal-stack ("stingln"/stingray.launch.py) bringup, a joystick "forward"
made Stormy drive in a BACKWARD circle pivoting on the right wheel. The right wheel was LOOSE on the
motor shaft (classic loose setscrew; hadn't fallen off yet). This is THE root cause and it explains
everything cleanly: the encoder reads the MOTOR shaft, so when the wheel slips on a loose hub the
encoders/EKF report motion that the robot isn't actually making -> odometry is a LIE -> RTAB-Map's
pose jumps (delocalizes) -> Nav2 drives erratically to reconcile a phantom pose. The clean logs
(no software/driver fault) fit perfectly: nothing was broken in software; the hardware fed false
encoder data. The earlier "wheel slip -> odom error -> delocalization" hypothesis was correct — just
MECHANICAL (loose setscrew), not traction slip.
"Why backward?" — with a loose setscrew the right side's real ground motion is indeterminate (slip +
intermittent catch + rotational lash), so net motion is unpredictable; a reverse arc is just how it
manifested. Don't over-derive it. TEST after tightening (blue Loctite if it keeps backing out): drive
a slow forward. Tracks straight => it was 100% the wheel. STILL arcs backward with a solid wheel =>
a real sign problem (inverted motor or swapped encoder channel on the right side) to chase in
BasicMicro Motion Studio / roboclaw.yaml, separately.

## DECISIONS / NEXT TIME (user)
- FIRST: FIX THE RIGHT WHEEL — tighten the loose setscrew (blue Loctite), then re-test a slow
  joystick forward for straight tracking before any mapping. This is the confirmed root cause of the
  delocalization/erratic-drive; most of the "diagnose the delocalization" work below is now ANSWERED.
  If it still arcs backward with a solid wheel, chase a right-side motor/encoder sign issue in
  BasicMicro Motion Studio / roboclaw.yaml.
- NO explore / NO autonomy next session. DRIVE BY HAND (teleop) in a LIMITED area while RTAB-Map
  builds the map. This removes Nav2-on-bad-pose as a danger and isolates variables.
- Enable FILE logging for rtabmap next run (e.g. --ros-args --log-level ... and/or redirect
  terminal to a file) so the loop-closure/odom event that delocalizes is actually recorded.
- Diagnose the delocalization offline from ~/.ros/rtabmap.db (NOT snapshotted this run — map was
  scrambled, not worth saving as-is). Consider: is EKF odom glitching on wheel slip? Are visual
  loop closures accepting at all on the real OAK, or is it scan/odom-only?
- Tuning to re-evaluate once localization is trusted: inflation_radius 0.30 (vs tuned 0.50),
  oak_points off (vs on), goal_timeout 60. These live in nav2_params_mapping.yaml / explore.yaml,
  committed, but are "mapping-run test values", NOT necessarily the normal-stack baseline.
- Normal stack (stingray.launch.py = slam_toolbox + Nav2, keepout ON via nav2_params.yaml) is
  UNTOUCHED and still available; user was bringing it up to check Stormy's baseline behavior.

## State at end
- Robot code COMMITTED + PUSHED: articubot_one exploration 5bf48bf..ade00cc (explore.yaml fixes
  bdc9f57; hardware launch + rtabmap compressed args + nav2_params_mapping.yaml ade00cc). Both the
  Pi and LinuxBox checkouts are synced at ade00cc.
- Backups left on the machines: Stingray /tmp/*.bak + /tmp/*.compressedbak + /tmp/*.inflbak +
  /tmp/*.oakbak; LinuxBox /tmp/explore.yaml.simbak + /tmp/explore.yaml.timeoutbak. oakd_nav_slim.yaml
  was restored to committed state (net no change).
- Untracked on LinuxBox: config/main.rviz has an unrelated working-tree change (left uncommitted);
  config/main.rviz.bak and launch/drive_sim.launch.py.bak are stray (clean up).
- Sim stack from 10-18 unchanged; sim skew still unresolved (parked).
- stingray repo (HankRearden): this note + context.txt update pushed to main.
