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
- LOOSE RIGHT-WHEEL SETSCREW (from NOTES-2026-10-19): odometry lies -> pose jumps. Setscrew now
  reported fixed; wheels tight. v2 still tags every WiFi reading to the map->base_link pose, so
  localization quality gates data quality.
- DONE THIS SESSION: live run completed (see below).

## Live run + findings (2026-10-26 afternoon)
### How to actually run it (map-first)
Localize on a SAVED map FIRST with AMCL, THEN start the logger. Without a real map loaded the
robot has "nothing to orient to" and delocalizes:
  T1:  ros2 launch articubot_one stingray.launch.py localizer_type:=amcl \
         map:=/home/ubuntu/robot_ws/src/articubot_one/assets/maps/Stormy_merged.yaml
       (set 2D Pose Estimate in RViz; stack delays localizers ~18s, Nav2 ~35s)
  T2:  ros2 launch wifi_logger_visualizer stingray_wifi.launch.py
Fresh DB (archive the old one first):
  D=/home/ubuntu/robot_logs/wifi/stingray_wifi.db; [ -f "$D" ] && \
    mv "$D" "${D%.db}_$(date +%Y%m%d_%H%M%S).db.bak"; rm -f "$D-wal" "$D-shm"

### WRONG MAP was the big gotcha
First AMCL run used Stormy_house_merged_20260426_080607.yaml -> RViz showed "no map", only live
scan + keepout; AMCL delocalized in the Dining Room (NOT the wheel). Cause: that file (and
Stormy_house_extend_20260426_062914) is a SPARSE fragment — 228x114, only ~442 wall px, ~77%
unknown, basically just the Study/dock corner. The COMPLETE house map is Stormy_merged.yaml
(494x309, ~11k wall px, 92k free, origin [-3.475,-8.176]) — and it is the stingray.launch.py
DEFAULT map. Also good: Stormy_blueprint.yaml (~9.9k wall px). Re-pinned v2 map_yaml_path ->
Stormy_merged.yaml (commit 92a5c92). Lesson: GET FACTS FIRST (pixel-histogram the pgm), never guess.
Map-server wiring is fine; map:= is honored (that's why the sparse map loaded + got stored in the DB).

### Good run result
Fresh DB on Stormy_merged: 294 cells over ~20 min, 3 APs heard (all 5 GHz):
  Sewing 7b:c7 (166 cells), Study 7c:17 (72), Master Closet 7c:b3 (54), 2 null. Signal -37..-63 dBm.
The house map renders in the browser viewer (stored in the DB) even though RViz didn't show it
(RViz Map display was correctly transient-local; the sparse map just had ~nothing to draw).

### TWO v2 limitations to flag to Mike
1. PASSIVE = ASSOCIATED-AP ONLY. The logger reads `iw ... link` (the one associated AP), not a
   scan of all APs in range. In a Deco mesh the Realtek wlxUSB is a STICKY client, so it maps
   "attached AP", not "best AP per cell". Breakfast never logged even parked in front of it and
   HEALTHY: its 5 GHz (7a:22:51:ee:92:7f) was heard at -65 dBm while the dongle stayed stuck on
   Study (7c:17) at -42 dBm. Do NOT reset Breakfast — it's fine. True best-AP-per-cell would need
   a SCAN-based logger (v2 deliberately does not scan). Forcing a roam = `sudo iw dev wlxUSB
   disconnect`, but that briefly drops Stingray's only link (WiFi) + ROS comms.
2. ZERO-DBM GLITCH. Some cells store signal_dbm=0 (invalid driver read; 35 of 294 this run).
   v2 is supposed to reject invalid reads. Filter signal_dbm=0; judge coverage by the
   access_point + link-rate browser layers, not raw signal, until fixed.

### Open / next session
- Decide whether "Stormy_merged.yaml is THE canonical full house map" should be promoted into
  context.txt as permanent environment info (left out for now; it was a this-session finding).
- Optional DB tidy: the first (bad-map) run's cells live under a separate map_id in an archived
  .db.bak; the live DB is clean on Stormy_merged.
- Report the two limitations to Mike (wimblerobotics); consider a scan-based coverage mode.
- Browser viewer served fine bound to 0.0.0.0:8088 (open http://192.168.68.66:8088 from HankRearden);
  README recommends 127.0.0.1 + `ssh -L 8088:127.0.0.1:8088` for untrusted nets.

## Repo re-forked onto Mike (2026-10-26 eve)
Problem: JHPHELAN/wifi_logger_visualizer showed "forked from slgrobotics" (all 4 branches) because
the GitHub fork PARENT was Sergei's repo. That label is repo-level metadata only — code already
tracked Mike via the wimble remote — but we wanted provenance to read wimblerobotics.
Constraint: GitHub allows ONE fork per upstream network per account, and our fork was already in
Mike's network, so you cannot fork Mike's alongside it — the old fork must be DELETED first.
Did:
1. Safety first: `git bundle create --all` of the whole repo (all 4 branches) ->
   /home/ubuntu/wifi_logger_visualizer_ALLBRANCHES_20261026_174011.bundle, verified "complete
   history", and scp'd to HankRearden ...\Stingray\backups\ (also verified there). Pi working
   clone still held every branch too.
2. User deleted JHPHELAN/wifi_logger_visualizer, then Forked wimblerobotics/wifi_logger_visualizer
   -> new JHPHELAN fork (now "forked from wimblerobotics"), default main = Mike 770089f.
3. Re-pushed local/stingray-v2 (92a5c92) and local/stingray (501bb67) from the Pi clone to the new
   origin (same URL, creds unchanged). Fixed remotes: removed slgrobotics 'upstream', renamed
   'wimble' -> 'upstream' = wimblerobotics. Realigned local main to origin/main (Mike), deleted the
   now-redundant wimble-v2 branch.
Final: origin = JHPHELAN fork; upstream = wimblerobotics; branches main (Mike v2) /
local/stingray-v2 (ACTIVE overrides) / local/stingray (old backup). Pi checked out local/stingray-v2.
Pull Mike's updates: git fetch upstream && git checkout local/stingray-v2 && git merge upstream/main.
(context.txt WiFi block updated to the new remote topology — that's permanent env info.)
Backup bundle on HankRearden can be kept or deleted; repo + branches are consistent on GitHub.
