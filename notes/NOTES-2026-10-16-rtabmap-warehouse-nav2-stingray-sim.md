# NOTES 2026-10-16 — Warehouse world + 2D-constrained RTAB-Map + Nav2 bringup (Stingray / sim)

Machines: HankRearden (Windows laptop = Copilot/VS Code side) and LinuxBox (Ubuntu 24.04,
ROS2 Jazzy) reached over SSH. Sim only (no physical Stingray). Sim = Gazebo (gz sim v8.15).
NEW world today: warehouse.sdf. Robot model: stingray.

## Goal
Pick up from 2026-10-11 (clean 2D lidar map in the barren test world). Today:
(1) move to a richer world (warehouse), (2) drive with the real JOYSTICK (joy running on
LinuxBox) to build a good map, (3) start Nav2 so we can navigate the map.

## Result — mostly SUCCESS; stopped one small edit short of a live Nav2
- Warehouse world loads and maps cleanly with the LD19 lidar 2D grid.
- Built a good 2D map by joystick (WM ~155).
- Fixed a MAJOR map defect: the map was floating ~10.8 m below the robot and distorted
  (unconstrained 6-DoF SLAM z-drift). Forced RTAB-Map to 2D -> map now flat (z=0).
- Nav2 brings up all servers EXCEPT it crashed on one params bug (empty `filters: []`).
  The fix is identified and half-applied; FIRST THING TOMORROW is to finish it (below).

## Working startup sequence (warehouse)
All GUI terminals need the env block FIRST (see KEY FIX A):
```
export DISPLAY=:0
export XAUTHORITY=$(ls -t /run/user/1000/.mutter-Xwaylandauth.* 2>/dev/null | head -1)
```
T1 (rsp): `ros2 launch articubot_one rsp.launch.py robot_model:=stingray use_sim_time:=true`
T2 (sim): `ros2 launch articubot_one drive_sim.launch.py robot_model:=stingray robot_world:=warehouse`
   -> Gazebo + RViz + twist_mux + EKF + joystick. (robot_world selects assets/worlds/<name>.sdf)
T3 (RTAB-Map): see 2D-constrained command below.
T4 (drive): the physical joystick (teleop_twist_joy, already running, publishes cmd_vel_joy
   which twist_mux consumes). Keyboard teleop no longer needed.
T5 (Nav2): see Nav2 command below.

## KEY FIX A (big time sink) — stale XAUTHORITY crashed EVERY Gazebo/RViz GUI
Symptom: Gazebo and RViz abort immediately in Qt:
`QGuiApplicationPrivate::createPlatformIntegration ... QMessageLogger::fatal ... Aborted`.
Earlier this looked like "Gazebo won't start / no gz server" because the GUI client crash
takes the bundled server down with it.
Root cause: the mutter Xwayland auth file has a RANDOM suffix that changes every login
(e.g. was `.mutter-Xwaylandauth.UTHMW3` in old notes, now `.I7CNW3`). The hard-coded path
pointed at a file that no longer exists, so Qt could not auth to the X display.
PERMANENT FIX: auto-discover the current auth file every time (survives reboots):
```
export DISPLAY=:0
export XAUTHORITY=$(ls -t /run/user/1000/.mutter-Xwaylandauth.* 2>/dev/null | head -1)
```
Verify the display works: `XAUTHORITY=$(...) DISPLAY=:0 xdpyinfo | head -3`.
NOTE: DISPLAY=:0 renders on LinuxBox's own screen (local), NOT forwarded to HankRearden.

## KEY FIX B — warehouse loads slowly => diff_cont spawner loads INACTIVE
The heavy warehouse delays gz's controller_manager, so the controller spawners either die
("Failed to acquire lock" / "Could not contact /controller_manager") or load diff_cont as
INACTIVE. joint_broad usually ends active; diff_cont often inactive (=> no /diff_cont/odom,
robot won't drive). Fix (no relaunch needed) — activate it by hand:
```
ros2 control list_controllers
ros2 control set_controller_state diff_cont active
```
Expect both active afterwards; /diff_cont/odom ~8 Hz (sim time), /odometry/local ~15 Hz.

## Warehouse world needs Fuel models (pre-fetch to avoid a mid-launch "hang")
warehouse.sdf `<include>`s all models from the OLD host fuel.ignitionrobotics.org
(Warehouse building, MovAi shelves/pallets/tugbot/carts). They were NOT cached. The old
host still works. Pre-downloaded with `gz fuel download -u <url>` (quiet success = no
output). Now cached under ~/.gz/fuel/fuel.ignitionrobotics.org/... so future loads are
offline/fast. (`gz sim -s -r -v 4 warehouse.sdf` headless loads the world fine = good
isolation test; the only failure was the GUI = KEY FIX A.)

## KEY FIX C (the important one) — map floating 10.8 m below robot + distorted
Symptom in RViz: RTAB-Map map/cloud ~10.8 m below the robot, perspective distorted, even
though the occupancy grid's own z=0. NOT the OAK-D tilt (that is trivial; the 25-deg wedge
is NOT installed). Diagnosis with tf2_echo:
```
ros2 run tf2_ros tf2_echo map base_link   -> Translation z = 10.488, slight roll/pitch
ros2 run tf2_ros tf2_echo odom base_link  -> Translation z = 0.000 (EKF odom is planar)
```
So ALL the z-drift is in RTAB-Map's map->odom correction = unconstrained 6-DoF SLAM.
The 2026-10-10/11 rtabmap_args never constrained the graph to the ground plane.
FIX: force 2D registration + 2D graph optimization. Add to rtabmap_args:
```
--Reg/Force3DoF true --Optimizer/Slam2D true
```
Needs a FRESH db to drop the already-baked 6-DoF links (delete_db_on_start:=true once).
After fix+short drive, tf2_echo map base_link -> z=0.000, roll=0, pitch=0 (yaw only). Fixed.

### The working 2D-constrained RTAB-Map launch (T3)
```
ros2 launch articubot_one rtabmap.launch.py \
  rgb_topic:=/camera depth_topic:=/depth_camera camera_info_topic:=/camera_info \
  odom_topic:=/odometry/local frame_id:=base_link \
  use_sim_time:=true approx_sync:=true approx_sync_max_interval:=0.1 qos:=2 \
  delete_db_on_start:=false publish_tf_map:=true \
  subscribe_scan:=true scan_topic:=/scan \
  rtabmap_args:="--RGBD/NeighborLinkRefining true --RGBD/ProximityBySpace true --Reg/Strategy 0 --Grid/FromDepth false --Grid/3D false --Grid/RayTracing true --Reg/Force3DoF true --Optimizer/Slam2D true"
```
delete_db_on_start: use TRUE only the first warehouse run (we did, to switch worlds cleanly
AND to drop the 6-DoF graph). Use FALSE from now on to keep extending the warehouse map.

## Carried-over gotchas (still true)
- `ros2 topic hz` zeros are usually the daemon/CLI gremlin, NOT a dead topic. Bounce it and
  run ONE hz at a time: `ros2 daemon stop; sleep 2; ros2 daemon start; sleep 2`.
  (This is how /scan "looked dead" today; it was fine at ~3 Hz sim time.)
- gz lidar publishes on gz topic /gz_scan (+ /gz_scan/points), bridged to ROS /scan,
  frame_id ldlaser_frame (the 2026-10-11 xacro fix). Here the /scan bridge QoS was RELIABLE.
- Cameras bridged BEST_EFFORT: RViz Image display may need Reliability = Best Effort.
  RGB image topic = /camera (200x200 now), depth = /depth_camera.
- RViz is fragile over this display and crashed once. It is only a viewer — relaunch it
  standalone WITHOUT killing T2:
  `ros2 launch articubot_one launch_rviz.launch.py use_sim_time:=true` (set Fixed Frame = map).
  Do NOT kill T2/drive_sim: it holds Gazebo + controllers + EKF + twist_mux + joystick.

## Nav2 bringup (in progress)
Dedicated files exist: robots/stingray/launch/stingray_sim_nav.launch.py (wraps
navigation_launch.py, hard-codes autostart=false + the real nav2_params.yaml) and
robots/stingray/config/nav2_params.yaml. nav2_bringup is installed (/opt/ros/jazzy).

Two problems with the stock stingray nav2_params.yaml for the sim:
1. Global costmap `static_layer` had no map_topic -> defaults to /map, but RTAB-Map
   publishes /rtabmap/map -> global costmap would be empty.
2. Both costmaps enable `keepout_filter` (filter_info_topic /costmap_filter_info). The mask
   is HOUSE danger zones (needs `ros2 launch articubot_one keepout.launch.py`), meaningless
   in the warehouse and a stall risk if the filter server is absent.

Solution = a SIM-ONLY params copy (leave the real nav2_params.yaml untouched):
`robots/stingray/config/nav2_params_sim.yaml`. Edits applied:
- global `static_layer:` -> added `map_topic: /rtabmap/map`  (DONE, verified line ~342)
- both `filters: ["keepout_filter"]` -> changed to `filters: []`  (DONE but WRONG, see bug)

### NAV2 BUG hit (unfinished) — empty `filters: []` aborts controller+planner
controller_server and planner_server died exit -6 (SIGABRT):
`terminate ... InvalidParameterValueException ... parameter 'filters': No parameter value set`.
Cause: ROS2 parses an empty YAML list `filters: []` as "no value set" -> costmap aborts.
FIX (NOT YET RUN — do this first tomorrow): DELETE the filters lines entirely so the
costmap uses its internal default (no filters):
```
sed -i '/^      filters: \[\]$/d' ~/robot_ws/src/articubot_one/robots/stingray/config/nav2_params_sim.yaml
grep -nE 'filters:|map_topic' ~/robot_ws/src/articubot_one/robots/stingray/config/nav2_params_sim.yaml
```

### The Nav2 launch to use (T5) once the params bug is fixed
navigation_launch.py directly (NOT the wrapper) so we can set autostart:=true — our
standalone RViz has no Nav2 "Startup" panel:
```
ros2 launch articubot_one navigation_launch.py \
  use_sim_time:=true autostart:=true \
  params_file:=/home/ubuntu/robot_ws/src/articubot_one/robots/stingray/config/nav2_params_sim.yaml
```
Expect lifecycle_manager to configure+activate all servers ("Managed nodes are active").

## NEXT TIME / TODO (ordered)
1. Finish KEY NAV2 FIX: run the sed above to delete `filters: []`, verify map_topic present.
2. Relaunch Nav2 (T5 command). Confirm all servers reach ACTIVE (no SIGABRT, no
   "Waiting for service controller_server/get_state" loop).
3. In RViz add Global/Local Costmap + Path displays; confirm the global costmap shows the
   warehouse map (proves static_layer map_topic:=/rtabmap/map works).
4. Send a goal: RViz "2D Goal Pose", or
   `ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose "{...}"`.
   Watch the robot plan + drive. Drive slowly; sim RTF is low.
5. Likely harmless warnings to clean up later:
   - obstacle/voxel `observation_sources` include `oak_points` (topic /oak/points) which
     does not exist in sim -> warnings only; could trim to scan-only in the sim params.
   - line ~618 `scan_frame_id: "laser_frame"` (sim uses ldlaser_frame) — check if the
     collision_monitor cares.
6. Consider folding Reg/Force3DoF + Optimizer/Slam2D into rtabmap.launch.py defaults so the
   z-drift can't recur.
7. From now on launch RTAB-Map with delete_db_on_start:=FALSE to keep extending the map.

## Databases
- Live map NOW = ~/.ros/rtabmap.db = the warehouse 2D map (WM ~155), built with
  Force3DoF/Slam2D. BACK IT UP before any fresh start:
  `cp ~/.ros/rtabmap.db ~/.ros/rtabmap_warehouse_2026-10-16.db`
- Backups: rtabmap_testworld_2026-10-16.db (old barren test world, 17 MB),
  rtabmap_stingray_sim_2026-10-11.db (old test world lidar map).
- TODO (cleanup): the test-world maps are probably not worth keeping; delete the
  rtabmap_testworld / rtabmap_stingray_sim_2026-10-11 backups once the warehouse map is solid.
