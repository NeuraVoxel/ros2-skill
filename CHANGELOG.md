# Changelog

All notable changes to ros2-skill will be documented in this file.

## [1.0.4] - 2026-03-13

Added launch and run commands for running ROS 2 launch files and executables in tmux sessions.

### Launch Commands

- `launch new <package> <launch_file> [args...]` — run a ROS 2 launch file in a tmux session
- `launch new --timeout SECONDS` — timeout for launch to start (default: 30)
- `launch list` — list running launch sessions in tmux
- `launch kill <session>` — kill a running launch session
- `launch restart <session>` — restart any launch session
- `launch foxglove [port]` — launch foxglove_bridge (port defaults to 8765)

### Run Commands

- `run new <package> <executable> [args...]` — run a ROS 2 executable in a tmux session
- `run new --presets <preset>` — apply preset parameters before running
- `run new --params "key:=value"` — set inline parameters (comma-separated, supports key:=value and key:value)
- `run new --config-path PATH` — path to config directory (auto-discovers yaml files and passes as --params-file)
- `run list` — list running run sessions in tmux
- `run kill <session>` — kill a running run session
- `run restart <session>` — restart a run session (preserves original parameters)

### TF2 Transform Commands

- `tf list` — list all coordinate frames
- `tf lookup <source> <target>` — query transform between frames
- `tf echo <source> <target> [--once] [--count N]` — echo transforms; `--once` echoes a single transform
- `tf monitor <frame>` — monitor transform updates for a frame
- `tf static --from <f> --to <t> --xyz x y z --rpy r p y` — publish static transform (named form)
- `tf static x y z roll pitch yaw from_frame to_frame` — publish static transform (positional form)
- `tf euler-from-quaternion` / `tf e2q` / `tf quat2euler` — convert quaternion to Euler (radians)
- `tf quaternion-from-euler` / `tf q2e` / `tf euler2quat` — convert Euler to quaternion (radians)
- `tf euler-from-quaternion-deg` / `tf e2qdeg` — convert quaternion to Euler (degrees)
- `tf quaternion-from-euler-deg` / `tf q2edeg` — convert Euler to quaternion (degrees)
- `tf transform-point` / `tf tp` / `tf point` — transform a point between frames
- `tf transform-vector` / `tf tv` / `tf vector` — transform a vector between frames

### Skill

- Launch argument validation: fetches real args via `--show-args`; fuzzy-matches close names; drops unknown args without failing the launch
- Executable auto-detect: fuzzy-matches executable names (e.g. "teleop" → "teleop_node")
- Workspace sourcing: `launch` and `run` auto-source local ROS 2 workspaces; searches `ROS2_LOCAL_WS`, `~/ros2_ws`, `~/colcon_ws`, `~/dev_ws`, `~/workspace`, `~/ros2` in order
- Package cache auto-refreshes when a package is not found; no manual `--refresh` needed
- Session management: fails if session exists; restart preserves original parameters
- Rule 0: mandatory pre-flight introspection before every publish/call/send — never assume topic names, types, or node names
- Rule 0.1: mandatory session-start checks — `doctor` health check, simulated time / `/clock` liveness, lifecycle node state verification
- Rule 0.5: never hallucinate commands or flags; verify in COMMANDS.md first, then run `--help` on the exact subcommand before constructing any call, then ask; mandatory for any rotation command before using `--rotate`
- COMMANDS.md: added `--help Quick Reference` section at the top listing `--help` invocations for every subcommand; agents should run these before using any unfamiliar flag
- Movement Case B: explicit mandatory `--help` step inline before constructing any `publish-until --rotate` command
- Rule 5: execute immediately on clear intent; ask only when genuinely ambiguous
- Rule 6: minimal reporting by default; verbose only on explicit request
- Movement: mandatory parameter introspection before any velocity command — discover controller nodes, list params, get velocity/angular limits, cap commanded velocity; conservative defaults if no limits found
- Movement: pre-motion check — read odom twist fields; abort and `estop` if robot is already moving
- Movement: odometry rate check (`topics hz`) before closed-loop — fall back to open-loop if rate < 5 Hz
- Movement: velocity topic disambiguation when both Twist and TwistStamped exist — prefer subscribed topic, then `cmd_vel` naming, then TwistStamped
- Movement: confirm Twist vs TwistStamped via `topics type` after discovery; verify controller active and odometry live before moving; capture start and end pose; report actual distance/angle
- Distance/angle commands always use `publish-until` with odometry; `publish-sequence` only for open-ended movement or no-odometry fallback
- All examples use `<VEL_TOPIC>` / `<ODOM_TOPIC>` placeholders; no hardcoded topic or service names anywhere

### publish-until --rotate Fix

- Fixed: `--rotate` rejected negative values (CW rotation) — guard changed from `<= 0` to `== 0`; zero is the only invalid rotation angle
- Fixed: rotation monitor was direction-blind — used `abs(delta_yaw)` which could never distinguish CW from CCW
- Fixed: rotation monitor used a single snapshot yaw delta instead of accumulated integration — failed for angles > 180° and multi-turn rotations
- Fixed: rotation monitor now integrates incremental steps (`normalize_angle(current_yaw - last_yaw)`) and compares signed accumulated total against signed target
- Fixed: output block reported `args.rotate` (raw degrees when `--degrees` used) instead of the converted `rotate_angle` in radians — now always reports in radians
- Fixed: documentation had CW example using positive `--rotate` with negative `angular.z` — this would never stop (monitor waits CCW, robot spins CW); corrected to `--rotate -45 --degrees` + `angular.z: -0.5`
- Supports: positive angles (CCW), negative angles (CW), angles > 360°, multi-turn, any sign combination
- Rule: `--rotate` sign and `angular.z` sign must always match; direction table added to SKILL.md Case B, Rule 0 checklist, FAQ, and COMMANDS.md

### Docs / Skill — Audit fixes

- Fixed: all 11 tf alias parsers (`e2q`, `quat2euler`, `q2e`, `euler2quat`, `e2qdeg`, `q2edeg`, `tp`, `point`, `tv`, `vector`, `get`) were bare `add_parser()` with no arguments — now have full `add_argument()` definitions and would no longer reject positional args at runtime
- Fixed: `actions find` and `topics find` argparse missing `--timeout` argument — now accepted and documented
- Fixed: `--type twist` / `--type odom` in COMMANDS.md examples → `--msg-type twist` / `--msg-type odom` (flag did not exist)
- Fixed: `doctor check` in decision table → `doctor` (subcommand does not exist)
- Fixed: `launch`/`run` JSON output examples contained spurious `new` in the `command` field — removed
- Fixed: `launch` / `run` section headings omitted required `new` subcommand — added
- Fixed: `topics find` and `actions find` missing `--timeout` from docs — added
- Fixed: `tf echo` missing `--once` from docs — added
- Fixed: `quat2euler` / `euler2quat` aliases not in tf section headings — added
- Fixed: hardcoded `/odom` in COMMANDS.md discovery workflow step 3 → `<ODOM_TOPIC>`
- Fixed: launch argument validation section wording clarified — script does fuzzy-matching automatically; agent should not fuzzy-match itself
- Fixed: 6 `nargs="?"` positional args missing `help=` strings — added for `hz`, `find`, `bw`, `delay`, `actions type`, `actions cancel`
- Fixed: services `find` example had `std srvs/Empty` (space) → `std_srvs/Empty`

### Skill — Gap resolutions (G1, G2, G7, G10, G11, G16)

- G7 (coord frame for distance): Case A switched from `--field pose.pose.position.x` to `--euclidean --field pose.pose.position` — Euclidean distance is frame-independent; works correctly after any prior rotation; `--delta` sign note added (Euclidean is always positive; direction set by velocity sign)
- G2 (estop on timeout): error recovery row for `publish-until` timeout now mandates immediate `estop` as the first action, then odom check to confirm motion has stopped before any retry
- G1 (obstacle avoidance): Case A now documents `--monitor <SCAN_TOPIC> --field ranges.0 --below 0.5` as the obstacle-avoidance pattern; also documents the one-monitor limitation and when to choose scan vs odom
- G10 (action feedback): Actions section now mandates `actions echo` immediately after every `actions send`; no-feedback handling linked to G16 action preemption table
- G11 (param readback): Params section now mandates `params get` after every `params set` to confirm nodes accepted the change (some silently reject out-of-range or read-only changes)
- G16 (cancel vs estop): new "Action Preemption" decision table added to Error Recovery — defines when to use `actions cancel`, when to use `estop` first, and the invariant: if in doubt, `estop` first then cancel



Added parameter preset commands, diagnostics monitoring, battery monitoring, and global timeout/retry configuration.

### Global Options

- `--timeout SECONDS` — override the per-command timeout for every ROS 2 call in the session; accepted before any subcommand (e.g. `--timeout 10 params get /node param`)
- `--retries N` — total number of attempts before giving up (default: `1`, i.e. no retry); applies to `wait_for_service`, `wait_for_server`, and async call spin loops across all command handlers
- `_apply_global_overrides(args)` propagates the global values onto per-command `timeout`/`retries` attributes after argparse; commands that have no `--timeout` arg (e.g. `topics list`) are explicitly guarded with `hasattr`

### Internal — Retry hardening

- `future.cancel()` is now called before every retry `continue` in all spin loops (18 sites across `ros2_action`, `ros2_control`, `ros2_lifecycle`, `ros2_param`, `ros2_service`) — prevents stale futures from a timed-out attempt delivering results to the next attempt
- `cmd_actions_send`: moved `wait_for_server` inside the retry loop so server unavailability is actually retried
- `cmd_actions_cancel`: added full retry loop (was missing entirely)

### Topics — Diagnostics

- `topics diag-list` — list all topics publishing `DiagnosticArray` messages, discovered by **type** (not by name); works with `/diagnostics`, `<node>/diagnostics`, `<namespace>/diagnostics`, or any other convention
- `topics diag` — subscribe to all discovered diagnostic topics simultaneously (or a specific `--topic`); returns parsed status with `level_name` (OK/WARN/ERROR/STALE), `name`, `message`, `hardware_id`, and key-value `values`; supports `--duration` + `--max-messages` for multi-message collection and `--timeout` for one-shot mode

### Parameters — Presets

- `params preset-save <node> <preset>` — save the current live parameters of a node to `.presets/{preset}.json`; uses `ListParameters` + `GetParameters` and writes a plain `{param_name: value}` JSON file
- `params preset-load <node> <preset>` — restore a named preset onto a node via `SetParameters`; reports per-parameter success and failure reasons
- `params preset-list` — list all saved presets from `.presets/`; no arguments; no running ROS 2 graph required
- `params preset-delete <preset>` — remove a saved preset file by name only (no node arg needed); no running ROS 2 graph required
- Presets stored flat as `.presets/{preset}.json` beside the skill directory; use descriptive names like `turtlesim_indoor` to identify node and configuration

### Internal

- Refactored `cmd_params_dump`: extracted `_dump_params(node_name, timeout) -> dict | None` helper so preset-save can reuse the dump logic without going through `output()`
- `resolve_output_path()` now writes to `.artifacts/` (hidden) instead of `artifacts/`

---

## [1.0.2] - 2026-03-07

Added `doctor`, `wtf`, `multicast`, and `interface` commands for ROS 2 system health checking, UDP multicast diagnostics, and interface type discovery.

### Interface

- `interface list` — list all installed interface types across all packages; output groups by `messages`, `services`, `actions` with a `total` count; reads from the ament resource index, no running ROS 2 graph required
- `interface show <type>` — show the field structure of any message, service, or action type; accepts canonical formats (`pkg/msg/Name`, `pkg/srv/Name`, `pkg/action/Name`) and shorthand (`pkg/Name`); output includes `"kind"` (`message`/`service`/`action`) and the appropriate field dicts (`fields` for messages, `request`/`response` for services, `goal`/`result`/`feedback` for actions)
- `interface proto <type>` — show a default-value prototype of any message, service, or action type; unlike `show` (type strings), `proto` instantiates the type so output contains actual default values — useful as a copy-paste template for publish payloads; nested messages are recursively expanded
- `interface packages` — list all packages that define at least one interface type
- `interface package <pkg>` — list all interface types (messages, services, actions) for a specific package

### Doctor / Wtf

- `doctor` — run ROS 2 system health checks via `ros2doctor` entry-point checkers; outputs JSON summary with `passed/failed/warned` counts and per-checker `status` (`PASS`/`WARN`/`FAIL`)
- `doctor hello` — check cross-host connectivity: publishes a `std_msgs/String` on a configurable topic (default `/canyouhearme`) and sends UDP multicast packets to `225.0.0.1:49150`; reports which remote hosts replied via ROS and multicast
- `wtf` — exact alias for `doctor`; same flags (`--report`, `--report-failed`, `--exclude-packages`, `--include-warnings`) and same `hello` subcommand
- Flags: `--report` / `-r` (all reports), `--report-failed` / `-rf` (failed-checker reports only), `--exclude-packages` / `-ep` (skip package checks), `--include-warnings` / `-iw` (treat warnings as failures)

### Multicast

- `multicast send [--group GROUP] [--port PORT]` — send one UDP multicast datagram to the specified group and port (defaults: `225.0.0.1:49150`); returns JSON with `sent` details
- `multicast receive [--group GROUP] [--port PORT] [--timeout SEC]` — listen for UDP multicast packets and return all received within the timeout window (default: 5 s); returns JSON with `received` list, `total`, `group`, `port`, and `timeout`
- Flags: `--group` / `-g` (multicast group, default: `225.0.0.1`), `--port` / `-p` (UDP port, default: `49150`), `--timeout` / `-t` (receive only, default: `5.0`)

---

## [1.0.1] - 2026-03-07

Refactored the CLI into separate domain modules and added two new command domains: lifecycle (managed node introspection and control) and control (ros2_control controller manager operations).

### Architecture

- Decomposed `ros2_cli.py` into domain modules (`ros2_topic.py`, `ros2_node.py`, `ros2_param.py`, `ros2_service.py`, `ros2_action.py`, `ros2_lifecycle.py`, `ros2_control.py`) with shared utilities in `ros2_utils.py`; `ros2_cli.py` now acts as the dispatcher and argument parser only

### Topics

- `topics capture-image` — capture a single frame from a ROS 2 image topic (compressed or raw), save to `.artifacts/`; optional Discord send via `--channel-id` and `--config`

### Lifecycle

- `lifecycle nodes` — list all managed (lifecycle) nodes by scanning for `/get_state` services
- `lifecycle list` / `ls` — list available states and transitions for one or all managed nodes
- `lifecycle get` — get the current lifecycle state of a managed node
- `lifecycle set` — trigger a lifecycle state transition by label (e.g. `configure`, `activate`) or numeric ID

### Control

- `control list-controller-types` / `lct` — list controller plugin types available in the pluginlib registry
- `control list-controllers` / `lc` — list loaded controllers, their type, and current state
- `control list-hardware-components` / `lhc` — list hardware components (actuator, sensor, system) and their lifecycle state
- `control list-hardware-interfaces` / `lhi` — list all command and state interfaces
- `control load-controller` / `load` — load a controller plugin by name
- `control unload-controller` / `unload` — unload a stopped controller
- `control reload-controller-libraries` / `rcl` — reload controller plugin libraries; `--force-kill` stops running controllers first
- `control set-controller-state` / `scs` — activate or deactivate a single controller via `SwitchController`
- `control set-hardware-component-state` / `shcs` — drive a hardware component through its lifecycle (`unconfigured`, `inactive`, `active`, `finalized`)
- `control switch-controllers` / `sc` — atomically activate and/or deactivate multiple controllers in a single `SwitchController` call; `--strictness STRICT|BEST_EFFORT`
- `control view-controller-chains` / `vcc` — generate a Graphviz DOT diagram of loaded chained controllers, render to PDF in `.artifacts/`, optionally send to Discord
- `control configure-controller` / `cc` — explicitly configure a loaded controller (`unconfigured → inactive`) via the `ConfigureController` service; surfaces `on_configure()` errors that `SwitchController`'s silent auto-configure hides

### Fixes

- `control set-hardware-component-state` (`shcs`) — fixed `AttributeError`: response field is `state` (not `actual_state`) in all distros; `actual_state` key still present in JSON output
- `lifecycle set` — four-level fuzzy matching so any short form resolves to a full transition label: (1) exact, (2) suffix (`shutdown` → `unconfigured_shutdown`; `success` → `on_configure_success`), (3) prefix (`unconfigured` → `unconfigured_shutdown`; `on_configure` → `on_configure_success`), (4) substring (`configure` → `on_configure_success`); all four levels are generic for every transition, not only shutdown

### Utilities

- `resolve_output_path()` added to `ros2_utils.py` — shared helper for `--output` arguments; plain filename → `.artifacts/` (created if absent), explicit path → used as-is

---

## [1.0.0] - 2026-03-01

Initial release of ros2-skill — an adaptation of [ros-skill](https://github.com/lpigeon/ros-skill) redesigned for direct local ROS 2 communication via rclpy instead of rosbridge.

### Topics

- `topics list` / `ls` — list all active topics
- `topics type` — get the message type of a topic
- `topics details` / `info` — publishers, subscribers, and QoS for a topic
- `topics message` / `message-structure` / `message-struct` — introspect message field structure
- `topics subscribe` / `echo` / `sub` — collect messages; `--duration` + `--max-messages` for batch collection
- `topics publish` / `pub` / `publish-continuous` — single-shot or timed publish at `--rate` Hz
- `topics publish-sequence` / `pub-seq` — publish a sequence of messages with per-step durations
- `topics publish-until` — publish while monitoring a separate topic; stops when a condition is met (`--delta`, `--above`, `--below`, `--equals`); `--euclidean` for N-dimensional distance across multiple fields
- `topics hz` — measure publish rate (rate, min/max/std_dev of inter-message intervals)
- `topics bw` — measure topic bandwidth (bytes/s, bytes per message)
- `topics delay` — measure end-to-end latency via `header.stamp`
- `topics find` — find all topics publishing a given message type

### Nodes

- `nodes list` / `ls` — list all active nodes
- `nodes details` / `info` — publishers, subscribers, services, action servers, and action clients for a node

### Services

- `services list` / `ls` — list all services
- `services details` / `info` — request and response field structure for a service
- `services call` — call a service with a JSON request
- `services find` — find all services of a given type
- `services echo` — echo service request/response event pairs (requires introspection enabled on the node)

### Parameters

- `params list` / `ls` — list all parameters on a node
- `params get` — get a parameter value
- `params set` — set a parameter value
- `params describe` — describe a parameter (type, constraints, read-only flag)
- `params dump` — bulk-export all parameters for a node as JSON
- `params load` — bulk-set parameters from a JSON string or file
- `params delete` — delete one or more parameters

### Actions

- `actions list` / `ls` — list all action servers
- `actions details` / `info` — goal, result, and feedback structure for an action server
- `actions type` — get the action type of an action server
- `actions send` / `send-goal` — send a goal; `--feedback` streams feedback messages in the output
- `actions find` — find all action servers of a given action type
- `actions echo` — echo live feedback and status messages from an action server
- `actions cancel` — cancel all in-flight goals on an action server

### Utilities

- `version` — detect ROS 2 distro and domain ID
- `estop` — emergency stop; auto-detects velocity topic and publishes zero velocity

---

For the original ros-skill (ROS 1 + ROS 2 via rosbridge), see: [ros-skill](https://github.com/lpigeon/ros-skill)
