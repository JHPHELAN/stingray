# NOTES 2026-11-01 (session 2) — RTAB-Map g2o re-run SUCCEEDED; office map is the keeper, ready to expand

Machine: HankRearden (Windows laptop), AI session driving the Stingray Pi over SSH.
Second note dated 2026-11-01. The first (…-oakd-flat-indicators-beacon-rtabmap-rightwheel)
ended with the g2o run ABORTED mid-drive. This session the user re-ran it to completion and
asked the AI to read the resulting db. It worked.

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

## What the user did (this run)
Launched stingray.hardware.launch.py + the RTAB-Map g2o recipe, hand-drove the Study office:
spun slowly in place with small joystick nudges, drove ~18 in (one floor tile), spun again,
drove around the desk and back, another spin, another trip around the desk to dock, then Ctrl-C.
"Almost 300 data points." Db finalized on Ctrl-C at ~/.ros/rtabmap.db.

## THE RESULT — g2o FIXED the optimizer (the 10-31 / first-11-01 failure is gone)
Read from ~/.ros/rtabmap.db via rtabmap-info (1 session):
- Nodes: 804 LTM / 298 WM. The "almost 300 data points" = the 298 WM nodes.
- Drive: 912 s (~15 min), only 8.635 m total odometry — the low distance is all the in-place
  spinning (neighbor links avg 0.03 m/hop). Consistent with the drive narrative.
- Loop closures: GlobalClosure 125, LocalSpaceClosure 83. (10-31 had exactly 1 global closure
  that got rejected every cycle.) 200+ closure links detected AND accepted — dock/desk returns
  registered.
- Optimizer stored: Optimizer/Strategy=1 (g2o), GravitySigma stayed 0.3 (did NOT need the
  fallback --Optimizer/GravitySigma 0), Reg/Force3DoF=true, Reg/Strategy=0.
- Optimized graph: 298 poses, bounded to a few meters — NO 1e7 blow-up.
- rtabmap-export --map SUCCEEDED: "Full global optimization… done (0.029 s, poses=298)", NO
  "Indeterminant linear system" warning, wrote a real rtabmap.pgm/.yaml. (10-31 aborted here
  with "optimized graph is empty".)
- Map: 264x145 cells @ 0.05 m, origin (-3.407, -2.149). A coherent office occupancy grid —
  free space, a distinct desk obstacle cluster, real walls. The free-space FAN streaking off to
  the right is NOT an artifact: per user it is the view out the Study door into the hallway.
  (Grid/RangeMax=0 unlimited + RayTracing on paints the long free beams down the open doorway;
  cap Grid/RangeMax ~5.0 next run if the streak bothers you — cosmetic.)
User viewed the preview PNG and called it "good enough to expand on."

## TWO CORRECTIONS the user made this session (now fixed in context.txt)
1. The first-11-01 abort was NOT a setscrew problem. The wheels were TIGHT; the "circling around
   the right wheel" was never diagnosed and did NOT recur on this mapping run. context.txt
   right-wheel block rewritten: setscrew loose 2x (10-19, 10-28), and the undiagnosed circling
   split out as a separate, unexplained, intermittent event to watch for.
2. The map's right-side free-space fan = out the Study door into the hallway (real open space),
   not a ray-trace artifact.

## KEEPER saved (md5 == live ~/.ros/rtabmap.db; db NOT in git, too big)
On the Pi (home dir), timestamp 20261101-183405:
  ~/rtabmap-final-20261101-183405.db   220 MB  (THE MAP — the keeper)
  ~/rtabmap-final-20261101-183405.pgm / .yaml  (exported occupancy grid)
  ~/rtabmap-final-20261101-183405.png  (preview render the AI viewed)
TODO (user, Windows side): FileZilla-pull the .db (+ .png) to
  C:\…\Robotics\Parallax\Stingray\Maps\  (lives with the other Stormy maps).
The live ~/.ros/rtabmap.db is UNTOUCHED and equals the keeper — this is what the next run expands.

## >>> NEXT SESSION <<< — EXPAND this map (multi-session mapping)
Goal: add to the existing map, do NOT start over. Key change vs the finalize recipe:
delete_db_on_start:=false (load + extend ~/.ros/rtabmap.db) and keep localization:=false
(stay in SLAM/mapping mode). Everything else identical (g2o already in the args).
Operational: start the drive where the robot can RECOGNIZE mapped space — the DOCK is the most
loop-closed spot — and drive gently there a few seconds until it re-localizes (map->odom snaps
into alignment, GlobalClosure ticks up) BEFORE heading into new territory (e.g. out the Study
door into the hallway). Finalize the SAME way: Ctrl-C to flush the SQLite db, then copy to a new
timestamped keeper before the next run. SAFETY NET: if a session goes bad, restore
~/.ros/rtabmap.db from the 183405 keeper and nothing is lost.

RE-RUN / EXPAND RECIPE (rtabmap ON THE PI) — each line its own terminal; source ros2 jazzy +
~/robot_ws/install/setup.bash first:
  T1 (Pi): ros2 launch articubot_one stingray.hardware.launch.py
  T2 (Pi): ros2 launch articubot_one rtabmap.launch.py \
      rgb_topic:=/oak/rgb/image_rect depth_topic:=/oak/stereo/image_raw \
      camera_info_topic:=/oak/rgb/camera_info odom_topic:=/odometry/local \
      frame_id:=base_link approx_sync:=true qos:=2 localization:=false \
      delete_db_on_start:=false publish_tf_map:=true subscribe_scan:=true scan_topic:=/scan \
      rtabmap_args:="--RGBD/NeighborLinkRefining true --RGBD/ProximityBySpace true \
      --Reg/Strategy 0 --Grid/FromDepth false --Grid/3D false --Grid/RayTracing true \
      --Optimizer/Strategy 1"
    (delete_db_on_start:=false = APPEND to the existing map. NO compressed:=true on-Pi.
     --Optimizer/Strategy 1 = g2o, the proven fix. Optionally add --Grid/RangeMax 5.0 to tame
     the hallway ray-trace streak.)
  T3 (Pi): python3 ~/robot_ws/src/articubot_one/scripts/map_relay.py
  RViz (LinuxBox): rviz2 -d ~/robot_ws/src/articubot_one/config/main.rviz   (Fixed Frame = map)
  Joystick (LinuxBox): ros2 launch articubot_one joystick.launch.py

## Parked (carry)
- Right-wheel "circling" event: undiagnosed, intermittent; diagnose if it returns (NOT the setscrew).
- Grid/RangeMax cap (5.0) to tame hallway ray-trace streaks — optional cosmetic.
- PR #4 roboclaw_driver: ball on Mike to merge; nothing blocked locally.
- keepout: use alias launchkeepout for house nav; stingln bare otherwise.
- FLOOR-FLATNESS CAL: moot now the camera is flat (pitch=0); only re-probe if costmap sloped.
- wifi v2 limitations to report to Mike (passive=associated-AP only; zero-dBm glitch), from 10-26.
- ros2-testing -> stable ros2 channel migration still TODO (context.txt).

## Commits this session
- stingray main: this note + context.txt (right-wheel block corrected: setscrew 2x not 3x,
  undiagnosed circling split out). No robot-code changes.
