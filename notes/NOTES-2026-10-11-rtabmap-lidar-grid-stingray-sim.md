# NOTES 2026-10-11 — RTAB-Map lidar 2D grid + sim speed-up (Stingray / sim)

Machines today: HankRearden (Windows laptop, the Copilot/VS Code side) and LinuxBox
(Ubuntu 24.04, ROS2 Jazzy) reached over PuTTY/SSH. No physical Stingray RPi robot —
sim only. Sim = Gazebo (gz sim v8.15), world test_robot_world.sdf, robot model stingray.

## Goal
Pick up from 2026-10-10 (RTAB-Map mapping the sim). Today: get a CLEAN 2D occupancy
grid, inspect it, and speed up the slow sim.

## Result — SUCCESS
- 2D occupancy grid now built from the LD19 lidar instead of the depth camera: clean
  thin black walls + white free-space wedges + gray unknown, instead of yesterday's
  ugly depth "blob".
- Fixed a real bug: the sim lidar published /scan stamped with a nonexistent TF frame.
- Sim real-time factor roughly doubled (~8% -> ~18%) by shrinking the sim cameras.
- Saved + backed up the database. WM reached 29 nodes on a short drive.

## The map was fine; the SETUP had two problems we fixed permanently.

### FIX 1 (the blocker) — lidar /scan was stamped with a nonexistent frame
Symptom in RTAB-Map when subscribe_scan:=true:
```
"laser_frame" passed to lookupTransform argument target_frame does not exist.
Could not convert laser scan msg! Aborting rtabmap update...
```
Root cause: the stingray lidar's gazebo sensor set its published frame to "laser_frame",
but the robot's TF tree only has "ldlaser_frame" (and an empty "base_laser"). RViz also
showed scans under frame 'laser_frame'. The scan's claimed frame simply did not exist.
TF frames present (from `ros2 topic echo /tf_static --once | grep child_frame_id`):
...ldlaser_frame, base_laser, ldlidar_support_link... (NO laser_frame).

File: robots/stingray/description/ldlidar.xacro
The `<link name="ldlaser_frame">` and `<sensor name="ldlaser_frame">` (pose 0 0 0),
but lines 70-71 published the wrong frame:
  line 70 before: <gz_frame_id>laser_frame</gz_frame_id>
  line 70 after:  <gz_frame_id>ldlaser_frame</gz_frame_id>
  line 71 before: <frame_id>laser_frame</frame_id>
  line 71 after:  <frame_id>ldlaser_frame</frame_id>
After rebuild+relaunch, /scan is stamped ldlaser_frame, RViz shows the lidar, and
RTAB-Map consumes the scan with no "Could not convert laser scan" error.

NOTE: a quick (non-permanent) band-aid would have been an identity static transform:
`ros2 run tf2_ros static_transform_publisher --frame-id ldlaser_frame --child-frame-id laser_frame`
We chose the permanent xacro fix instead.
Also note: the generic description/lidar.xacro and robots/stingray/OBSOLETE/ydlidar.xacro
use "laser_frame" — the stingray does NOT include those, so ignore them.

### FIX 2 (speed) — shrink the sim cameras
Sim was ~8% real-time because gz renders the cameras + lidar each frame; RTAB-Map only
needs ~1 Hz. File: description/oakd.xacro. Only TWO sensors are actually rendered by gz:
`oakd_rgb_<mount>` (type camera) and `oakd_depth_<mount>` (type depth). The 1200x800
`multicamera` stereo block above them uses the old Gazebo-Classic plugin
`libgazebo_ros_multicamera.so`, which gz sim does NOT load — so it is not rendered;
leave it alone. For EACH of the two active sensors:
  update_rate: 30 -> 15
  <width>:  400 -> 200
  <height>: 400 -> 200
Result: ~8% -> ~18% RTF (about 2x). Depth cam is now only used for RGB-D features + 3D
cloud (the 2D grid comes from the lidar), so 200x200 is plenty. Backups saved as
*.xacro.bak next to each edited file.

## Rebuild + relaunch recipe (after editing xacro)
```
cd ~/robot_ws
source /opt/ros/jazzy/setup.bash
colcon build --packages-select articubot_one
```
Then STOP the whole stack and relaunch fresh (new description won't load into running
nodes). Clean-slate check:
```
pgrep -af 'rsp.launch|drive_sim|gz sim|ros_gz|rtabmap|robot_state_publisher|ekf_node|twist_mux|teleop_twist|parameter_bridge|rviz2' || true
```
In every GUI terminal:
```
export DISPLAY=:0
export XAUTHORITY=/run/user/1000/.mutter-Xwaylandauth.UTHMW3
```
(Yesterday's bug: XAUTHORITY was set but NOT exported in T1/T2, so Gazebo/RViz didn't
inherit it and the controller spawner timed out / no GUI. Always `export` both.)

T1: `ros2 launch articubot_one rsp.launch.py robot_model:=stingray use_sim_time:=true`
T2: `ros2 launch articubot_one drive_sim.launch.py robot_model:=stingray`
    (Gazebo + RViz + twist_mux + EKF; spawns robot; diff_cont + joint_broad activate.)
T3: RTAB-Map with LIDAR grid (see below)
T4: `ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true`

## The working RTAB-Map launch — LIDAR-sourced 2D grid
```
ros2 launch articubot_one rtabmap.launch.py \
  rgb_topic:=/camera depth_topic:=/depth_camera camera_info_topic:=/camera_info \
  odom_topic:=/odometry/local frame_id:=base_link \
  use_sim_time:=true approx_sync:=true approx_sync_max_interval:=0.1 qos:=2 \
  delete_db_on_start:=false publish_tf_map:=true \
  subscribe_scan:=true scan_topic:=/scan \
  rtabmap_args:="--RGBD/NeighborLinkRefining true --RGBD/ProximityBySpace true --Reg/Strategy 0 --Grid/FromDepth false --Grid/3D false --Grid/RayTracing true"
```
Key differences vs 2026-10-10:
- subscribe_scan:=true scan_topic:=/scan   (feed the LD19 scan)
- --Grid/FromDepth false  (2D grid from the LIDAR, not the depth camera)
  (rtabmap migrates this to Grid/Sensor internally; harmless WARN about the migration)
- approx_sync_max_interval:=0.1  (comfortable match for 15 Hz cameras + 10 Hz scan)

## KEY LESSON — occupancy grids are baked per-node; switching sensor needs a FRESH db
RTAB-Map stores each node's local 2D grid at creation time using whatever sensor was
configured THEN. Nodes made with the depth camera keep their ugly depth grids forever;
the old scans aren't stored, so they can't be regenerated. To get a fully clean
lidar map we started a FRESH database (delete_db_on_start:=true) for the switch.

## KEY LESSON — delete_db_on_start
- true  = wipe ~/.ros/rtabmap.db at launch (fresh map). Used ONCE today to switch the
          grid source cleanly.
- false = load + extend the existing map. This is the NORMAL day-to-day setting.
MUST remember: use delete_db_on_start:=false to avoid losing the map. Tomorrow use
false to keep building on today's lidar map.

## Carried-over QoS lesson (still true)
ros_gz_bridge publishes sensor topics (camera, depth, scan) BEST_EFFORT. Default
RELIABLE subscribers get ZERO messages. Use qos:=2 (best effort) for everything, and
echo bridged topics with `--qos-profile sensor_data`.

## Saving / backup
Clean Ctrl-C of the rtabmap node flushes the db:
```
rtabmap: 2D occupancy grid map saved.
rtabmap: Saving database/long-term memory...done! (/home/ubuntu/.ros/rtabmap.db, 16 MB)
```
Dated backup made so a stray delete_db_on_start can't wipe it:
```
cp ~/.ros/rtabmap.db ~/.ros/rtabmap_stingray_sim_2026-10-11.db
```
Files: ~/.ros/rtabmap.db (live) and ~/.ros/rtabmap_stingray_sim_2026-10-11.db (17 MB each).

## Map facts today
- /rtabmap/map = nav_msgs/OccupancyGrid, latched (RViz Map display needs Durability =
  Transient Local). Earlier snapshot: 0.05 m/cell, 280x246 cells (~14.0 x 12.3 m).
- Short drive => WM=29 nodes, local map=29. Grid shape = white free-space wedges bounded
  by thin black walls on gray unknown — correct lidar map.

## Next time / TODO
- Relaunch with delete_db_on_start:=false and keep driving to close the map / loops.
- If more sim speed is wanted: lower lidar <samples> (currently 360) or drop camera res
  again; physics + lidar are now the main cost, not the cameras.
- Optionally silence the one-time depth-compression warning with
  Mem/DepthCompressionFormat=.png (or Mem/SaveDepth16Format=true).
- Consider aligning sim scan frame with the real robot's convention: real LD19 node
  publishes /scan in base_laser; sim now uses ldlaser_frame. Fine for sim, but if exact
  parity is wanted later, reconcile base_laser vs ldlaser_frame.
