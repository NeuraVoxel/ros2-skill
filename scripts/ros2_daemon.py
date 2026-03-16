#!/usr/bin/env python3
"""ROS 2 daemon management commands.

Implements daemon status, start, and stop using the ros2cli Python API where
available, with a PID-file + SIGTERM fallback.

No rclpy or live ROS 2 graph is required.  The ROS 2 daemon is a background
service that caches DDS discovery results (nodes, topics, services) to speed
up CLI queries.  It is not required for ros2_cli.py to function — it only
affects the responsiveness of raw 'ros2' CLI commands.

Domain ID is always read from the ROS_DOMAIN_ID environment variable
(default: 0), mirroring the behaviour of the 'ros2 daemon' CLI.
"""

import os
import pathlib
import signal
import time

from ros2_utils import output


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_domain_id() -> int:
    """Return the active ROS_DOMAIN_ID (default 0)."""
    try:
        return int(os.environ.get("ROS_DOMAIN_ID", 0))
    except (ValueError, TypeError):
        return 0


def _find_pid_files() -> list:
    """Find daemon PID files in ~/.ros/ matching standard name patterns."""
    ros_dir = pathlib.Path.home() / ".ros"
    if not ros_dir.is_dir():
        return []
    return list(ros_dir.glob("daemon_*.pid"))


def _read_pid(pid_file) -> int | None:
    """Read an integer PID from *pid_file*; return None on any error."""
    try:
        return int(pathlib.Path(pid_file).read_text().strip())
    except Exception:
        return None


def _pid_alive(pid: int) -> bool:
    """Return True if a process with *pid* is currently running.

    Uses os.kill(pid, 0) — signal 0 never actually kills the process; it
    only checks whether the target PID exists.  EPERM means the process
    exists but we lack permission to signal it — that still means alive.
    ProcessLookupError (ESRCH) means the PID does not exist.
    """
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except OSError:
        # EPERM — process exists but we don't have permission to signal it.
        return True


def _daemon_status_native(domain_id: int) -> dict | None:
    """Query daemon status via the ros2cli Python API.

    Returns a dict with a 'running' key, or None if ros2cli is not
    installed or the API is unavailable on this distribution.
    """
    try:
        from ros2cli.daemon import is_daemon_running  # type: ignore[import]
        running = is_daemon_running(domain_id=domain_id)
        return {"running": bool(running)}
    except ImportError:
        return None
    except Exception:
        return None


def _daemon_pid_status(domain_id: int) -> dict:
    """Determine daemon status via PID file discovery.

    Returns a status dict compatible with the command output schema.
    """
    pid_files = _find_pid_files()

    if not pid_files:
        return {"status": "not_running", "domain_id": domain_id}

    for pf in pid_files:
        pid = _read_pid(pf)
        if pid is not None and _pid_alive(pid):
            return {"status": "running", "domain_id": domain_id, "pid": pid}

    # All PID files were stale.
    return {
        "status": "not_running",
        "domain_id": domain_id,
        "note": "Stale PID file(s) found — daemon is not running",
    }


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_daemon_status(args):
    """Check whether the ROS 2 daemon is running.

    Reads domain ID from ROS_DOMAIN_ID (default 0).  Tries the ros2cli
    Python API first; falls back to PID file discovery.
    """
    try:
        domain_id = _get_domain_id()
        native = _daemon_status_native(domain_id)

        if native is not None:
            # Native API gave us a definitive answer.  Enrich with PID if
            # the daemon is running and we can find it in the PID files.
            result = {
                "status": "running" if native["running"] else "not_running",
                "domain_id": domain_id,
            }
            if native["running"]:
                pid_info = _daemon_pid_status(domain_id)
                if "pid" in pid_info:
                    result["pid"] = pid_info["pid"]
        else:
            # ros2cli not available — use PID file fallback.
            result = _daemon_pid_status(domain_id)

        output(result)

    except Exception as exc:
        output({"error": str(exc)})


def cmd_daemon_start(args):
    """Start the ROS 2 daemon if it is not already running.

    Uses the ros2cli Python API (spawn_daemon).  Idempotent: if the daemon
    is already running, returns immediately without spawning a second copy.
    """
    try:
        domain_id = _get_domain_id()

        # --- Early exit if already running -----------------------------------
        native = _daemon_status_native(domain_id)
        already_running = (native is not None and native["running"])

        if not already_running:
            # Also check PID files in case native API is absent.
            pid_info = _daemon_pid_status(domain_id)
            already_running = (pid_info["status"] == "running")

        if already_running:
            result = {"status": "already_running", "domain_id": domain_id}
            if native is None:
                result["pid"] = pid_info.get("pid")
            else:
                pid_check = _daemon_pid_status(domain_id)
                if "pid" in pid_check:
                    result["pid"] = pid_check["pid"]
            output(result)
            return

        # --- Spawn -----------------------------------------------------------
        try:
            from ros2cli.daemon import spawn_daemon  # type: ignore[import]
            spawn_daemon()
        except ImportError:
            output({
                "error": "ros2cli Python package not available",
                "hint":  "Install ros2cli or run 'ros2 daemon start' in a shell",
                "domain_id": domain_id,
            })
            return

        # Brief pause then verify via PID files.
        time.sleep(0.5)
        pid_info = _daemon_pid_status(domain_id)
        result = {"status": "started", "domain_id": domain_id}
        if "pid" in pid_info:
            result["pid"] = pid_info["pid"]

        output(result)

    except Exception as exc:
        output({"error": str(exc)})


def cmd_daemon_stop(args):
    """Stop the ROS 2 daemon.

    Tries the ros2cli Python API (shutdown_daemon) first.  Falls back to
    SIGTERM if ros2cli is unavailable.  Idempotent: no-op if the daemon is
    not running.
    """
    try:
        domain_id = _get_domain_id()

        # --- Check if running -----------------------------------------------
        pid_info = _daemon_pid_status(domain_id)
        if pid_info["status"] == "not_running":
            output({"status": "not_running", "domain_id": domain_id})
            return

        # --- Stop via native API or SIGTERM ----------------------------------
        stopped_via_api = False
        try:
            from ros2cli.daemon import shutdown_daemon  # type: ignore[import]
            shutdown_daemon(domain_id=domain_id)
            stopped_via_api = True
        except ImportError:
            pass

        if not stopped_via_api:
            pid = pid_info.get("pid")
            if pid:
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    output({"status": "not_running", "domain_id": domain_id})
                    return

        # Brief pause then verify.
        time.sleep(0.5)
        post = _daemon_pid_status(domain_id)

        if post["status"] == "not_running":
            output({"status": "stopped", "domain_id": domain_id})
        else:
            output({
                "status": "stop_requested",
                "domain_id": domain_id,
                "note": "Daemon may take a moment to exit",
                "pid": post.get("pid"),
            })

    except Exception as exc:
        output({"error": str(exc)})
