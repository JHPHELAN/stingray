# NOTES 2026-11-05 — RTAB-Map multi-session EXPAND: Study continue + hallway venture, map fused & growing

Machine: HankRearden (Windows laptop), AI session driving the Stingray Pi over SSH.
Picks up from the 2026-11-01 g2o success. This session proved multi-session mapping
(continue + expand an existing map) and clarified loop-closure visibility.

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

## What the user did (two mapping runs this session, both continuing the 11-01 map)
Run A (continue, same Study): launched hardware + rtabmap with delete_db_on_start:=false,
drove around the Study again and back to dock. WM reached 474.
Run B (expand into the hallway): launched again (continue), ventured out the Study door into
the hallway — advancing one 18" tile diagonally, spinning with small turns, advancing, spinning,
then back to dock. WM reached 708.

## Finding 1 — multi-session continue/EXPAND works with g2o (delete_db_on_start:=false)
Each continue-run loads ~/.ros/rtabmap.db and adds a NEW session (new map id), then FUSES to
the prior map via cross-session loop closures once the robot re-recognizes known space (the dock).
Verified by querying the db Link table for links whose endpoints have different map_id:
  after Run A: 98 global + 184 local-space CROSS-session closures
  after Run B: 106 global + 184 local-space CROSS-session closures
So the sessions are genuinely merged into one connected graph, not floating separately.
Run A map was congruent with 11-01 (same Study, not doubled/ghosted = good re-localization).
Run B GREW the footprint: optimized bbox x=-1->0,y=0->0  ->  x=-1->1,y=0->2; grid 266x144 ->
364x172 cells (~18.2 x 8.6 m). Driving the SAME room only densifies; new geography needs new drive.

## Finding 2 — the db now holds 4 map-sessions; one is a BNO false start (harmless)
rtabmap-info "Maps in graph: 4/4 [0(298),1(1),2(175),3(234)]" (WM counts). By LTM: map 0=804
(the 11-01 base), map 1=113, map 2=744, map 3=412. Map 1 is a BNO085 launch FAILURE: user
launched the stack, got a BNO08x fault, killed it, checked wiring (all good), reassembled,
relaunched -> the real Run A became map 2. "Scared out the gremlin." All 4 are fused; harmless.

## Finding 3 — LOOP-CLOSURE TERMINAL VISIBILITY (user's question, important)
User searched the rtabmap terminal for "closure" and found ONLY rejections, never successes,
and was right to doubt my first answer. Root cause: rtabmap's core logger emits ACCEPTED
closures at INFO ("Loop closure detected! With id=N") but the Pi console runs at WARN, so only
REJECTIONS (WARN, "Loop closure a->b rejected!") print. The "rtabmap (N): Rate=... WM=.." line
you watch is the ROS node's separate logger and never mentions closures. So terminal silence !=
no closures. Confirmed from the binary strings in librtabmap_core.so.
HOW TO ACTUALLY WATCH CLOSURES:
  - ros2 topic echo /rtabmap/info --field loop_closure_id  (nonzero = global closure that cycle;
    proximity_detection_id for proximity). Verified these fields exist in rtabmap_msgs/Info.
  - rtabmap_viz GUI (live, draws links + count).
  - db is ground truth: rtabmap-info GlobalClosure / LocalSpaceClosure counts.
The "2 rejections at the start" the user saw are the NORMAL re-localization handshake on a
continue-run before it locks onto the old map.

## Finding 4 — map health (Run B)
rtabmap-info: 4 sessions, 2073 LTM / 708 WM, GlobalClosure 226, LocalSpaceClosure 227, optimized
graph 708 poses bounded (no 1e7 blow-up). rtabmap-export --map ran full global optimization and
wrote a real grid (no "empty graph"). g2o still solid. Map is coherent: Study block still congruent,
new hallway corridor to the right + a walled region lower-left; streakier in the open hallway
(diagonal advance + spins + open-space ray-tracing) but fine.

## Finding 5 — viewing GUIs from the headless Pi
rtabmap-databaseViewer <db> = OFFLINE map inspector. User got it up (after X11 wrangling, below):
default screen = a node PAIR (two images) with many yellow dots = visual feature keypoints (what
gets matched to close loops; many dots = good). Per-image stats = that node's id/pose/feature
bookkeeping. The LOOP CLOSURES are seen via View -> Graph View (trajectory + colored closure links),
or Constraints View to step through them. rtabmap_viz = the LIVE equivalent (run on LinuxBox).
X11 note: PuTTY + XLaunch. "could not connect to display" = PuTTY X11 forwarding not on (DISPLAY
empty). Fix in PuTTY Configuration window (not the live terminal): expand Connection -> SSH -> X11,
tick "Enable X11 forwarding", reconnect. XLaunch already-running is fine (can't start a 2nd on :0).
Server side OK (xauth present, sshd X11Forwarding yes). NoMachine into the Pi is the smoother
alternative (no forwarding fuss). All added as stable facts to context.txt.

## KEEPERS saved this session (db NOT in git; live ~/.ros/rtabmap.db untouched for next continue)
  ~/rtabmap-final-20261105-210632.db  450 MB  (after Run A, Study continue; WM 474)
  ~/rtabmap-final-20261105-215835.db  574 MB  (after Run B, hallway expand; WM 708 — THE KEEPER)
Earlier keepers still present: 20261031-212639 (pre-g2o), 20261101-183405 (first good map).
TODO (user, Windows): FileZilla-pull 20261105-215835.db (+ .png) to
  C:\...\Robotics\Parallax\Stingray\Maps\  — supersedes the 11-01 one.

## >>> NEXT SESSION <<< — keep EXPANDING the house map
Same continue recipe (delete_db_on_start:=false, localization:=false, g2o args). Start at the
DOCK, let it re-localize onto the known map, THEN drive into unmapped rooms (Foyer and beyond).
To WATCH closures this time, open a spare terminal: ros2 topic echo /rtabmap/info --field
loop_closure_id  (or run rtabmap_viz on LinuxBox). Finalize + copy to a new timestamped keeper.
SAFETY NET: if a run corrupts the map, restore ~/.ros/rtabmap.db from the 215835 keeper.
If the BNO085 fault recurs at launch: kill, reseat/reseat wiring, relaunch (it cleared instantly).

## RE-RUN / EXPAND RECIPE (rtabmap ON THE PI) — carry forward
Each line its own terminal; source ros2 jazzy + ~/robot_ws/install/setup.bash first.
  T1 (Pi): ros2 launch articubot_one stingray.hardware.launch.py
  T2 (Pi): ros2 launch articubot_one rtabmap.launch.py \
      rgb_topic:=/oak/rgb/image_rect depth_topic:=/oak/stereo/image_raw \
      camera_info_topic:=/oak/rgb/camera_info odom_topic:=/odometry/local \
      frame_id:=base_link approx_sync:=true qos:=2 localization:=false \
      delete_db_on_start:=false publish_tf_map:=true subscribe_scan:=true scan_topic:=/scan \
      rtabmap_args:="--RGBD/NeighborLinkRefining true --RGBD/ProximityBySpace true \
      --Reg/Strategy 0 --Grid/FromDepth false --Grid/3D false --Grid/RayTracing true \
      --Optimizer/Strategy 1"
    (delete_db_on_start:=false = APPEND/EXPAND. NO compressed:=true on-Pi. g2o already in args.
     Optional --Grid/RangeMax 5.0 to tame open-hallway ray-trace streaks.)
  T3 (Pi): python3 ~/robot_ws/src/articubot_one/scripts/map_relay.py
  WATCH closures (Pi, spare terminal): ros2 topic echo /rtabmap/info --field loop_closure_id
  RViz (LinuxBox): rviz2 -d ~/robot_ws/src/articubot_one/config/main.rviz   (Fixed Frame = map)
  Joystick (LinuxBox): ros2 launch articubot_one joystick.launch.py

## Parked (carry)
- Right-wheel "circling" event: undiagnosed, intermittent, NOT the setscrew (wheels were tight);
  did not recur this session. Diagnose if it returns.
- Grid/RangeMax cap (5.0) to tame hallway ray-trace streaks — optional cosmetic.
- PR #4 roboclaw_driver: ball on Mike to merge; nothing blocked locally.
- keepout: use alias launchkeepout for house nav; stingln bare otherwise.
- FLOOR-FLATNESS CAL: moot now the camera is flat (pitch=0); only re-probe if costmap sloped.
- wifi v2 limitations to report to Mike (passive=associated-AP only; zero-dBm glitch), from 10-26.
- ros2-testing -> stable ros2 channel migration still TODO (context.txt).

## Commits this session
- stingray main: this note + context.txt (added stable facts: g2o optimizer, multi-session
  continue/expand procedure, loop-closure logging visibility, rtabmap GUI viewers + X11 note).
  No robot-code changes.
