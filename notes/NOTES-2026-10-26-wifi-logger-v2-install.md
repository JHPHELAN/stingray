# NOTES 2026-10-26 — wifi_logger_visualizer v2 (Mike Wimble) installed on Stingray

Machine: HankRearden (Windows laptop) driving Stingray over SSH (ubuntu@192.168.68.66).
Live run not done yet when this was saved (checkpoint in case of a crash).

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
Switched Stingray from Sergei's fork of wifi_logger_visualizer to Mike Wimble's v2
("version 2 architecture": map-aware persistent coverage, iw not iwconfig, 25 cm cells,
SQLite maps/wifi_cells/wifi_surveys with WAL, explicit survey mode with iperf3, transient-local
RViz MarkerArray, browser viewer, BSSID->room friendly names, no interpolation).

Package dir: /home/ubuntu/robot_ws/src/wifi_logger_visualizer. ROS 2 Jazzy, workspace
/home/ubuntu/robot_ws (colcon --symlink-install, so src edits to launch/config are live after
one rebuild to register new files).

## Branch layout (all pushed to JHPHELAN/wifi_logger_visualizer)
Remotes: origin = JHPHELAN (backup), upstream = slgrobotics (Sergei), wimble = wimblerobotics (Mike).
- local/stingray (501bb67) = OLD Sergei-fork version. Before switching, committed the two
  uncommitted local overrides (db under ~/robot_logs/wifi; .gitignore tools/local/) and pushed,
  so the old version is 100% backed up.
- wimble-v2 (770089f) = PRISTINE mirror of wimble/main. Pull Mike's future updates here with
  `git pull wimble main`; NEVER commit local edits here (keeps pulls conflict-free).
- local/stingray-v2 (17adcfa) = ACTIVE robot override layer. Only TWO added files; Mike's
  launch/config are untouched:
    launch/stingray_wifi.launch.py  — wrapper mirroring Mike's node set; loads his
      config/wifi_logger_config.yaml then our config/stingray_wifi_params.yaml (ours wins).
    config/stingray_wifi_params.yaml — wifi_interface=wlxUSB, cell_size 0.25,
      db_path ~/robot_logs/wifi/stingray_wifi.db, map_yaml_path Stormy_house_merged_20260426_080607,
      /wifi_survey_node target_host 192.168.68.99 (LinuxBox iperf3 -s).

Why the override LAYER instead of editing Mike's files: his launch does parameters=[config, common],
so db_path/map_yaml_path/cell_size/target_host come from launch args and override the YAML; only
wifi_interface (and per-node tuning) comes from the YAML. Editing Mike's launch defaults (first
attempt) would conflict on future pulls, so we reverted that and added a thin wrapper + params file.

## AP friendly names (HOME ONLY — not in git)
Source of truth is ~/ap_map.yaml (verified BSSIDs incl. Breakfast's locally-administered-bit quirk).
Wrote v2-format ~/robot_logs/wifi/access_points.yaml with all 4 Deco units, both bands:
  Master Closet 34:60:f9:5d:7c:b2/b3, Study 34:60:f9:5d:7c:16/17,
  Sewing 34:60:f9:5d:7b:c6/c7, Breakfast 7a:20:51:ee:92:7e / 7a:22:51:ee:92:7f.
Kept OUTSIDE the repo on purpose (home AP MACs); pass to the viewer with --node-names.

## Verified (no motion)
Bare `ros2 launch wifi_logger_visualizer stingray_wifi.launch.py visualization:=false` →
"Passive Wi-Fi monitoring map_id=1, interface=wlxUSB, cell_size=0.25 m"; DB created at
~/robot_logs/wifi/stingray_wifi.db with tables maps/wifi_cells/wifi_surveys; map hashed.
Correctly SKIPS samples while there is no map->base_link TF (robot stack down) — intended v2 behavior.
Deps present: iw, iperf3, matplotlib/numpy/yaml (python3-sqlite3 rosdep key unresolved but harmless,
sqlite3 is stdlib).

## Daily commands
  ros2 launch wifi_logger_visualizer stingray_wifi.launch.py                 # passive, with stack up
  ros2 launch wifi_logger_visualizer stingray_wifi.launch.py survey:=true    # + iperf3/latency (stationary)
  ros2 run wifi_logger_visualizer web_viewer.py \
    --db ~/robot_logs/wifi/stingray_wifi.db \
    --node-names ~/robot_logs/wifi/access_points.yaml --host 127.0.0.1 --port 8088

## Still parked / next
- LOOSE RIGHT-WHEEL SETSCREW (from NOTES-2026-10-19): odometry lies -> pose jumps. FIX THE WHEEL
  FIRST (tighten + blue Loctite, re-test straight tracking) before any mapping/coverage drive, because
  v2 tags every WiFi reading to the map->base_link pose.
- NEXT THIS SESSION: live run of v2 with the robot stack up (hand-drive while RTAB-Map localizes;
  no autonomy), confirm cells populate in the DB / RViz / browser.
