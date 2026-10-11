# NOTES 2026-10-10 — RTAB-Map on sim (Stingray / LinuxBox)

Machine: LinuxBox (laptop), Ubuntu 24.04, ROS2 Jazzy. Sim = Gazebo (gz sim v8.15),
world `pretty_lawn` / `test_robot_world.sdf`. Robot model: stingray.

## Goal
Pick up from 2026-10-09: confirm `/camera` and `/depth_camera` publish rates, then
launch RTAB-Map remapped to the sim topics.

## Result — SUCCESS
RTAB-Map runs against the sim topics and maps. Working memory (WM) grew to 46 nodes
while driving via teleop, with odom + RGB-D synced and no "Did not receive data"
warnings.

## Startup sequence that worked (after a disconnect)
1. Bounce the ros2 daemon to clear a stuck CLI, then confirm:
   `ros2 daemon stop; sleep 2; ros2 daemon start; sleep 1; ros2 topic list`
2. Terminal 1: `ros2 launch articubot_one rsp.launch.py robot_model:=stingray use_sim_time:=true`
3. Terminal 2: `ros2 launch articubot_one drive_sim.launch.py robot_model:=stingray`
   (Gazebo + RViz + twist_mux + EKF; spawns robot; diff_cont + joint_broad activate.)
4. Terminal 3: RTAB-Map (see command below).
5. Terminal 4: teleop (see below).

Remember to `export DISPLAY=:0` and
`export XAUTHORITY=/run/user/1000/.mutter-Xwaylandauth.UTHMW3` in any terminal that
launches a GUI (Gazebo, RViz, RTAB-Map viz).

## The working RTAB-Map launch (note the qos:=2)
```
ros2 launch articubot_one rtabmap.launch.py \
  rgb_topic:=/camera depth_topic:=/depth_camera camera_info_topic:=/camera_info \
  odom_topic:=/odometry/local frame_id:=base_link \
  use_sim_time:=true approx_sync:=true qos:=2 \
  delete_db_on_start:=true publish_tf_map:=true
```
Confirmed in log:
```
rtabmap subscribed to (approx sync):
   /odometry/local  /camera  /depth_camera  /camera_info
qos_image=2 qos_camera_info=2 qos_odom=2
rtabmap (N): Rate=1.00s ... (local map=1, WM=1..46)
```

## KEY LESSON 1 — QoS mismatch (the big time sink)
The cameras looked dead but were NOT. The `ros_gz_bridge` publishes image/sensor
topics as **BEST_EFFORT**. Default subscribers are **RELIABLE**, which is
*incompatible* with a best-effort publisher, so they receive **zero** messages.
- `ros2 topic hz /camera` (default reliable) = nothing.
- `ros2 topic echo /camera --qos-profile sensor_data` (best effort) = frames.
- `/clock` worked with default QoS because the clock bridge is reliable.
Fix for RTAB-Map: `qos:=2` (0=system, 1=reliable, 2=best effort). A best-effort
subscriber is compatible with BOTH best-effort (cameras) and reliable (odom) pubs,
so qos:=2 for everything is the safe choice.

Verify a bridged sensor topic with the MATCHING QoS, e.g.:
```
timeout 10 ros2 topic echo /camera --field width --qos-profile sensor_data > /tmp/cam.txt 2>&1
grep -c '^400' /tmp/cam.txt   # frames in 10s
```

## KEY LESSON 2 — "rcl node's context is invalid" gremlin
Recurring error: `Failed to create subscription: rcl node's context is invalid,
at ./src/rcl/node.c:404`. Triggers: (a) Ctrl-C'ing a launch, and (b) chaining several
`timeout N ros2 topic hz ...` calls in one line — the first behaves oddly and the next
fails. Fix: `ros2 daemon stop && ros2 daemon start`, then run ONE hz at a time, never
chained. Also, piping `timeout ... ros2 topic echo | grep -c` can swallow the count on
SIGTERM — capture to a file, then `grep -c` the file.

## KEY LESSON 3 — low real-time factor / teleop lag
Wall-clock frame rates look tiny (~1.3 Hz for a 30 Hz sim camera) ONLY because the sim
runs at ~4% real-time: Gazebo is rendering 2x 400x400 cameras + lidar. Everything uses
`use_sim_time:=true`, so RTAB-Map (1 Hz of SIM time) maps correctly, just slowly in
wall-clock. Side effect: heavy teleop lag and turn overshoot.
Drive teleop with stamped velocities (twist_mux/diff_cont expect TwistStamped):
```
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true
```

## Topic facts (sim)
- Camera bridges (LAZY 0 = always on): gz_camera->/camera, gz_camera_info->/camera_info
  (RGB), gz_depth_camera->/depth_camera. Images 400x400, ~30 Hz in sim time.
- `/camera_info` on the ROS graph has ONE publisher (RGB via bridge). The depth
  sensor's camera_info stays on the Gazebo side (`/camera_info` gz topic, NOT bridged),
  so there is NO ROS-side conflict.
- Odom: EKF publishes `/odometry/local` (reliable QoS). Also `/odometry/global`,
  `/diff_cont/odom`.

## Next time / TODO
- To reduce teleop lag, lower camera load in the stingray sim description (camera
  update_rate and/or 400x400 resolution), then relaunch drive_sim.
- Optionally silence the one-time depth-compression warning:
  `Mem/DepthCompressionFormat=.png` (or `Mem/SaveDepth16Format=true`).
- Continue driving to build out the map; then save/inspect the RTAB-Map DB
  (`~/.ros/rtabmap.db`).
