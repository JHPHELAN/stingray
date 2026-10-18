# NOTES 2026-10-18 — HankRearden->LinuxBox SSH, repo reconcile, RViz/nav2 cleanup

Machine: HankRearden (Windows laptop), local VSCode window on the stingray doc repo
(C:\...\stingray-repo = JHPHELAN/stingray). Robot-code edits were made on LinuxBox over
SSH (JHPHELAN/articubot_one, branch exploration). This is a CHECKPOINT note written
mid-session (user asked to save NOTES in case VSCode crashes); session may continue.

## SESSION ROUTINES — do these EVERY session (carry this block forward)
The "Read, Recall, Pull" (open) and "Recap, Remember, Push" (close) rituals.

### OPEN — "Read, Recall, Pull" (first thing)
1. READ: .github/copilot-instructions.md AND context.txt (both canonical in THIS repo,
   JHPHELAN/stingray root) — specs, dialog rules, preflight.
2. RECALL: read the NEWEST notes/NOTES-YYYY-MM-DD-*.md BY DATE (not an older one), state
   back where we left off + open items, wait for the user to confirm alignment.
   Skills are Pi-local (/home/ubuntu/.copilot/skills) — not visible from this Windows window.
3. PULL: git pull --ff-only on the repo(s) you'll touch (stingray main; articubot_one
   exploration). NO cross-machine AI memory — orientation travels ONLY through committed
   files + the Pi skills folder.

### CLOSE — "Recap, Remember, Push" (end of session)
1. RECAP what changed and what was learned.
2. REMEMBER: write a NEW notes/NOTES-YYYY-MM-DD-*.md (Goal, Result, What changed, Key
   facts/lessons, State at end, NEXT TIME/TODO) AND update context.txt. Carry THIS block forward.
3. PUSH to the correct repo/branch (notes/context -> JHPHELAN/stingray main; robot code ->
   JHPHELAN/articubot_one exploration). Session-state copies are DRAFTS only — unpushed = invisible next time.

## Goal
Work the TODO list left by the 2026-10-17 note. Picked off #2, #3, #4, #5.

## RESULT — all four done and pushed
- #2 SSH keys HankRearden->LinuxBox: DONE (passwordless key auth works).
- #3 Reconcile LinuxBox's pre-existing uncommitted work: DONE (commit 4c59181).
- #4 Remove stale slam_toolbox RViz panel from config/main.rviz: DONE (commit 23b68b2).
- #5 Tidy stale inline comments in nav2_params_sim.yaml: DONE (commit bd18a37).

## What changed / how

### #2 — HankRearden -> LinuxBox passwordless SSH (NEW CAPABILITY)
- HankRearden already had ~/.ssh/id_ed25519(.pub) and an SSH config with a `Host LinuxBox`
  entry (HostName LinuxBox, User ubuntu). `AddressFamily inet` forces IPv4; name resolves
  to 192.168.68.99 (wired). No config change needed.
- Installed HankRearden's pubkey into LinuxBox ~/.ssh/authorized_keys (user ran a one-liner
  that prompted once for the LinuxBox password; I cannot type interactive passwords).
- Verified: `ssh -o BatchMode=yes LinuxBox "..."` works non-interactively. I can now drive
  LinuxBox directly from this Windows window for all robot-code work.
- SHELL-QUOTING LESSON (Windows): PowerShell -> ssh.exe -> remote bash mangles embedded
  quotes (double quotes get stripped by native-arg passing; heredocs break). RELIABLE
  pattern for complex remote commands: build the bash script in a PowerShell single-quoted
  here-string, strip CR (`$s = $s -replace "`r",""`), base64-encode
  (`[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($s))`), then run
  `ssh LinuxBox "echo <b64> | base64 -d | bash"`. base64 is alnum+/=, nothing to mangle.
  Simple commit messages via `cat > /tmp/f <<'MSG' ... MSG` inside a single-quoted arg also work.

### #3 — reconcile uncommitted LinuxBox work (commit 4c59181, pushed 77dc083..4c59181)
These were UNCOMMITTED working-tree edits, so they were ACTIVE during the successful
2026-10-16/17 warehouse sim + Nav2 runs. Committing preserves the known-good state.
- COMMITTED (modified, all sim-only effect, real robot unaffected):
  - robots/stingray/description/ldlidar.xacro: sim lidar sensor frame_id laser_frame ->
    ldlaser_frame. BUG FIX: the lidar LINK is ldlaser_frame throughout the file, but the gz
    sensor published the nonexistent frame 'laser_frame'. Now /scan header.frame_id is a real
    TF link. (Side note: nav2_params.yaml + nav2_params_sim.yaml still say
    scan_frame_id: "laser_frame" — left alone; nav worked. Worth a look someday.)
  - description/oakd.xacro: sim OAK-D RGB+depth 800x800@30Hz -> 200x200@15Hz (sim RTF perf;
    gazebo sensor block is sim-only; real camera untouched).
  - launch/joystick.launch.py: boolean launch args 'True'/'False' -> lowercase 'true'/'false'.
  - scripts/WiFiQuality.xml (NEW): PlotJuggler layout for wifi link quality.
- DELETED: description/oakd.xacro.bak, robots/stingray/description/ldlidar.xacro.bak,
  and the 11.6 MB robots/stingray/stingray_log.rtf (WordPerfect "Stingray Experience"
  running log; does not belong in the code repo, lives on HankRearden).
- GITIGNORED: robots/stingray/date_index.txt (17 KB scratch index of date markers from the
  RTF log) — added to .gitignore (anchored /robots/stingray/date_index.txt).

WiFiQuality.xml USAGE (so we don't rediscover): run `scripts/wifi_publisher.py` (tracked;
publishes /wifi/<iface>/signal_dbm + quality/noise/bitrate/freq via `iw dev`, fallback
/proc/net/wireless), then in PlotJuggler: Layout -> Load Layout -> scripts/WiFiQuality.xml
to chart signal_dbm for the USB dongle + wlan0 over time. Also loads in Foxglove.

### #4 — remove stale slam_toolbox RViz panel (commit 23b68b2, pushed 4c59181..23b68b2)
- config/main.rviz Panels list had a `slam_toolbox::SlamToolboxPlugin` panel — leftover from
  the retired SLAM-Toolbox workflow (we now map/localize with RTAB-Map). Even when NOT
  visible, a panel listed in Panels is INSTANTIATED on RViz load, so it (1) spammed
  "Waiting for slam_toolbox node configuration" and (2) was the lone RELIABLE subscriber on
  /initialpose, causing the QoS-incompatible warning vs the BEST_EFFORT 2D Pose Estimate
  tool (real relocalization goes through the relay to /rtabmap/initialpose).
- Removed the Panels entry (2 lines) AND its Window Geometry "collapsed" key (2 lines) = 4
  lines total. Content-matched sed, backup at config/main.rviz.bak (UNTRACKED, not committed
  — consistent with our no-.bak-in-git policy; delete it once RViz is confirmed clean).
- Leftover 2 (intentionally left): the dock name is still encoded inside the QMainWindow
  State hex blob. That blob is Qt's binary saveState (dock sizes/positions); do NOT hand-edit
  it (length-prefixed, snipping corrupts offsets). It is harmless (RViz ignores dock data for
  panels not in the Panels list) and clears itself on the next RViz File -> Save Config.
- Re-add the panel any time: RViz Panels -> Add New Panel -> SlamToolboxPlugin.

### #5 — tidy stale nav2_params_sim.yaml comments (commit bd18a37, pushed 23b68b2..bd18a37)
The 2026-10-17 slow-sim tuning changed values but left comments describing the OPPOSITE:
- L19 bt_loop_duration: 20 — old comment "Reduced for quicker decision-making" was wrong; it
  was RAISED 5->20 ms to tolerate slow sim RTF (fewer missed BT loops). Comment fixed.
- L62 controller_frequency: 5.0 — old comment "Was 5.0 - increased for finer heading control"
  was doubly wrong; it was LOWERED 10.0->5.0 Hz to avoid "control loop missed its desired
  rate of 10 Hz" under ~40% RTF. Comment fixed.
- Comment-only edits; parameter values unchanged; real robot nav2_params.yaml untouched.

## House-world idea (user, 2026-10-18) — evaluate replacing warehouse for house nav
User (correctly) thinks the warehouse is a poor proxy for in-house navigation. Candidate:
AWS RoboMaker Small House World — github.com/aws-robotics/aws-robomaker-small-house-world
(branches: ros1, ros2, archive, gzweb, fix-models, add_inertial_all_models, ...). It is
`worlds/small_house.world` + `models/` of static .DAE meshes/textures, built for Gazebo
CLASSIC 7/9 (ROS Kinetic/Melodic), uses GAZEBO_MODEL_PATH + model:// URIs. Unsupported, ROS1.

My assessment (see chat): GOOD fit for house nav, worth trying. ROS1/unsupported is fine —
we only want the world/models, not their ROS1 launch glue (we'll point our own gz bringup at
it, like drive_sim). Harmonic (gz-sim 8) compatibility is NOT plug-and-play; expect to reuse
the warehouse port fixes:
  1. Set GZ_SIM_RESOURCE_PATH to the models/ dir so model:// resolves (like our drive_sim
     GZ_SIM_RESOURCE_PATH mesh fix).
  2. Replace the classic `<gui>` block with a modern gz-gui MinimalScene block (exactly the
     warehouse.sdf FIX 1 from 2026-10-17).
  3. Watch classic OGRE `<material><script>` refs that ogre2/Harmonic can't render (surfaces
     go grey) — DAE-embedded textures usually render; floors/walls sometimes use material
     scripts and need converting.
  4. Bump/clean SDF tags; strip any gazebo-classic plugins (a static house likely has none).
The ros2 branch is still Classic-oriented (ROS2 wrapper, not Ignition), so it won't save the
Harmonic port work. Fallback if it fights: a Fuel/Ignition-native house or hand-built rooms.

## House world IMPORTED + validated (2026-10-18) — commit 27e9e67 (articubot_one exploration)
Turned out to be an EASY port (predictions mostly held, and better): no OGRE material scripts,
no classic <plugin> tags, and the `<gui>` had only a camera (no legacy GzScene3D), so NO
warehouse-style gui fix was needed. Decision: option B (lean repo).
- assets/worlds/small_house.sdf: AWS world (Apache-2.0; attribution header added). Loads in
  Harmonic gz-sim 8.15.0 — all 68 models resolve, Collada .DAE meshes with embedded materials
  (no grey surfaces), headless load exits 0.
- Harmonic port fixes (Classic tolerated, Harmonic/DART rejects):
  * 29 non-static models marked <static>1</static> (static house scenery).
  * aws_robomaker_residential_ShoeRack_01 inertia bug: duplicate <ixx> + missing <izz> let izz
    default to 1.0, violating the moment-of-inertia triangle inequality -> fixed <izz>0.05</izz>.
  * One harmless residual DART warning "Invalid entry (1,1): 0" on a static body; load still OK.
- MODELS ARE GITIGNORED (option B): assets/models/aws_robomaker_residential_* (~106 MB) NOT
  committed. Regenerate with `python3 scripts/fetch_small_house_world.py` (clones AWS ros1
  branch, copies 68 models, re-applies static + ShoeRack patches) then
  `colcon build --symlink-install --packages-select articubot_one`.
- launch/drive_sim.launch.py: added `assets/models` to GZ_SIM_RESOURCE_PATH so the house
  model:// refs resolve. Backup .bak (untracked).
- Worlds PRUNED (unused, same commit): obstacle.world, obstacle_gz.sdf, obstacle_gz.world,
  obstacles.world, sonoma_racetrack.sdf, phelan.sdf ('pretty_lawn' hand-built test). KEPT:
  test_robot_world.sdf (default), warehouse.sdf (current stingray), empty_world.sdf,
  baylands.sdf (dragger), small_house.sdf.
- Peeked live via `gz sim -r <world>` GUI on LinuxBox (DISPLAY=:0 + mutter XAUTHORITY) — looks good.
- Bring up (once models fetched + built):
  `ros2 launch articubot_one drive_sim.launch.py robot_model:=stingray robot_world:=small_house use_sim_time:=true`
  then rsp + rtabmap + nav2 per the 10-17 note.

## State at end (checkpoint)
- articubot_one (LinuxBox, exploration): HEAD 27e9e67, pushed to origin, working tree clean
  except UNTRACKED config/main.rviz.bak + launch/drive_sim.launch.py.bak (intentional backups).
  Pi can `git pull --ff-only` (then run fetch_small_house_world.py to get the house models).
- stingray repo (HankRearden): this note added + pushed to main.
- Nav2 autonomous nav in warehouse sim = WORKING (from 2026-10-17); not re-run today.
- House world = imported, loads in Harmonic, committed (models fetched separately).
- SSH HankRearden->LinuxBox = working passwordless.

## NEXT TIME / TODO
1. HOUSE WORLD (imported + loads): pick a robot SPAWN POSE inside the house (origin may be in a
   wall) via drive_sim initial_x/y/yaw; then build a FRESH RTAB-Map DB driving the house (lidar
   grid, Force3DoF), SAVE it, and switch sim nav from warehouse to house.
2. FINISH THE MAP (if staying on warehouse): drive full coverage in SLAM mode (lidar grid,
   Force3DoF on), get loop closures, SAVE the DB; then try simultaneous nav+map via Nav2
   waypoints (planner allow_unknown to push into unmapped aisles).
3. Delete old RTAB-Map DB backups once a fresh/solid map exists
   (~/.ros/rtabmap_warehouse_2026-10-16.db.bak etc).
4. Delete config/main.rviz.bak once RViz startup is confirmed clean (no slam_toolbox spam).
5. Someday: reconcile scan_frame_id: "laser_frame" in nav2_params*.yaml vs the ldlaser_frame
   lidar link / base_laser real-robot scan frame.
6. Update context.txt at full CLOSE to record the new HankRearden->LinuxBox SSH capability
   and the Windows base64 remote-exec pattern.
