# NOTES 2026-10-28 — OAK-D 25 deg tilt wedge added to the Stingray URDF

Machine: HankRearden (Windows laptop) driving the Stingray Pi and LinuxBox over SSH.
Robot-code work (articubot_one exploration); the wedge CAD lives in the sibling
...\Stingray\CAD (not in git). Pushed and previewed OK.

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

## What we did
Modeled the finalized 3D-printed OAK-D tilt wedge (NOTES-2026-10-26-oakd-tilt-wedge-nub-spacing)
in the robot URDF so the camera now sits on a wedge instead of floating on a hand-tuned joint.
The wedge inserts into the kinematic chain between the chassis front plate and the OAK-D and
tilts the camera up a pure 25 deg (= 1/2 the stereo-depth V-FOV).

Pushed to articubot_one exploration as dd6c8ab; previewed in RViz on LinuxBox (looks right);
LinuxBox pulled + colcon-built so the new mesh is properly installed there too.

## Files (articubot_one, branch exploration)
- NEW description/oakd_wedge.xacro — macro `oakd_wedge params="parent mount_point"`. Builds:
  * link oakd_wedge_${mount_point}: simplified mesh visual (material "gray" for RViz),
    box collision 0.024984 x 0.050 x 0.045, inertial_box 40 g; + Gazebo/Grey material and
    preserveFixedJoint on both joints.
  * joint base_link -> oakd_wedge_${mount_point}: xyz (front_panel_offset=0.090, 0, 0), rpy 0.
    Flat robot-facing face centered in y and z on the front plate.
  * joint oakd_wedge_${mount_point} -> oakd_${mount_point}: xyz (0.03841, 0, 0.02679),
    rpy (0, -0.4363323, 0) = pure 25 deg nose-UP (negative pitch = nose-up).
- NEW assets/meshes/oakd_wedge.stl — SIMPLIFIED body-only wedge (trapezoidal prism, no
  counterbore / inserts / nubs), 12 triangles, authored directly in the wedge-link frame in
  METERS (so the URDF visual needs NO origin transform). Generator is a pure-python ASCII-STL
  writer (no cadquery/trimesh dep): local gen_wedge_mesh.py, also /tmp/gen_wedge_mesh.py on the Pi.
  bbox x[0,0.025] y[-0.025,0.025] z[-0.0225,0.0225] m.
- EDIT robots/stingray/description/robot.urdf.xacro — include oakd_wedge.xacro after oakd.xacro;
  keep xacro:oakd_link; REPLACED the old `xacro:oakd_joint x=0.023 y=0.01 z=0.030 pitch=0.027`
  call with `xacro:oakd_wedge parent="base_link" mount_point="front_panel"`.
- EDIT robots/stingray/description/robot_core.xacro — descriptive header comment (user's change,
  committed in the same commit).

## Geometry / derivation (wedge-link frame: origin at robot-face center, x fwd, y left, z up)
- The wedge CAD frame (wedge.py) is X=depth(robot face X=0), Y=height(0=bottom), Z=width. Mapped
  to the ROS link frame by x=X, z=Y-22.5mm, y=-(Z-25mm) (robot-face center -> link origin).
- Tripod hole on the camera face: CAD (16.11, 19.03, 25) mm = link (0.016109, 0, -0.003468) m.
- Camera-face normal n=(0.9063,0,0.4226); up-slope uhat=(-0.4226,0,0.9063) (both y=0).
- OAK-D optical center = tripod + 0.033 m along n (OAK-D depth, back face -> front optical center)
  + 0.018 m along uhat (42.5 mm optical height minus 24.5 mm tripod height above the OAK-D bottom)
  = (0.03841, 0, 0.02679) in the wedge-link frame.
- NET optical center in base_link = (0.12841, 0, 0.02679), tilted 25 deg up. (Old hand-tuned was
  (0.123, 0, 0.030) tilted ~1.5 deg DOWN — so position barely moved, tilt flipped to the real 25 up.)
- Front plate is at x = front_panel_offset = 0.090 m ahead of base_link; chassis is centered on
  base_link in y and z, so the front-plate center is (0.090, 0, 0). User-supplied inputs: tripod
  socket 24.5 mm and optical/mount point 42.5 mm above the OAK-D bottom, wedge tilt 25 deg.

## KEY LESSON — RViz resolves meshes LOCALLY; the /robot_description topic does NOT ship geometry
Split setup: robot_state_publisher runs on the PI, rviz2 runs on LinuxBox. First preview showed
the camera in the right spot but NO wedge. Cause: /robot_description carries only the URDF XML
(mesh filename REFERENCES like package://articubot_one/assets/meshes/oakd_wedge.stl), never the
triangle data. RViz resolves each package:// URI against ITS OWN local ament index -> install/share
and loads the file from the LOCAL disk. The chassis (Stingray.stl) and camera (OAK-D.dae) rendered
because those were already installed on LinuxBox; only the brand-new oakd_wedge.stl was absent, so
only the wedge was invisible. => Any machine that RUNS RViz needs the mesh file installed there
(normally via colcon build of the package on that machine). Pre-push shortcut was to scp the STL to
LinuxBox + symlink into install; the permanent fix is push -> pull -> colcon build on LinuxBox
(done). Also: RViz does NOT re-fetch meshes on its own after the file appears — toggle the
RobotModel display off/on to reload.

## Verify / preview
- xacro expands clean on the Pi: `xacro robot.urdf.xacro sim_mode:=false` => XACRO OK; generated
  chain base_link -> oakd_wedge_front_panel -> oakd_front_panel confirmed with the numbers above.
- RViz on LinuxBox (robot_state_publisher from the Pi): wedge now renders between the front plate
  and the camera; user confirmed "Perfect".

## Still parked / next
- FLOOR-FLATNESS CAL: the old pitch 0.027 rad (~1.55 deg nose-DOWN) floor-flatness calibration was
  intentionally DROPPED for the physical 25 deg wedge. Re-run the floor-flatness probe on CLEAN
  floor (no table ahead) with the real wedge mounted and re-add a small residual pitch to
  oakd_joint if the costmap still sees a sloped floor. See the old cal note preserved in
  NOTES-2026-10-03-low-obstacle-detection / the removed robot.urdf.xacro comment.
- Collision is a simple box envelope (0.025 x 0.050 x 0.045) around the wedge; fine for a static
  mount, slightly over-covers the tapered top-front. Revisit only if it ever matters.
- wifi v2 limitations to report to Mike (passive = associated-AP only; zero-dBm glitch) — unchanged
  from NOTES-2026-10-26-wifi-logger-v2-install.
- Loose right-wheel setscrew (NOTES-2026-10-19) reported fixed/tight. Mapping-run tuning values in
  exploration (inflation_radius 0.30, oak_points off, goal_timeout 60) are TEST values, not baseline.
