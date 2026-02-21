"""Scheduler for running nitrodump at regular intervals on macOS."""

import os
import subprocess
import plistlib
from datetime import datetime
from pathlib import Path
from typing import Optional

# Paths
LAUNCH_AGENTS_DIR = Path.home() / "Library" / "LaunchAgents"
PLIST_NAME = "com.nitrodump.scheduler.plist"
LOG_FILE = Path.home() / "nitrodump.log"

# Label for launchd
LABEL = "com.nitrodump.scheduler"


def get_uid() -> str:
    """Get the current user's UID for launchctl bootout/bootstrap."""
    return str(os.getuid())


def get_log_path() -> Path:
    """Get the log file path."""
    return LOG_FILE


def get_plist_path() -> Path:
    """Get the plist file path for the LaunchAgent."""
    return LAUNCH_AGENTS_DIR / PLIST_NAME


def get_nitrodump_executable() -> Optional[str]:
    """Get the path to the nitrodump executable.

    Returns:
        The executable path if found, None otherwise.
    """
    # Try to find via uv first
    try:
        result = subprocess.run(
            ["uv", "tool", "dir"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            tool_dir = Path(result.stdout.strip())
            bin_path = tool_dir / "bin" / "nitrodump"
            if bin_path.exists():
                return str(bin_path)
    except FileNotFoundError:
        pass

    # Try which
    try:
        result = subprocess.run(
            ["which", "nitrodump"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except FileNotFoundError:
        pass

    return None


def interval_to_seconds(interval: str) -> int:
    """Convert interval string to seconds.

    Args:
        interval: Interval string like '30m', '2h', '1d', etc.

    Returns:
        Interval in seconds.

    Raises:
        ValueError: If interval format is invalid.
    """
    interval = interval.strip().lower()

    if not interval or len(interval) < 2:
        raise ValueError("Invalid interval format")

    unit = interval[-1]
    try:
        value = int(interval[:-1])
    except ValueError:
        raise ValueError("Invalid interval value")

    if value <= 0:
        raise ValueError("Interval must be positive")

    match unit:
        case "s":
            return value
        case "m":
            return value * 60
        case "h":
            return value * 3600
        case _:
            raise ValueError("Invalid interval unit. Use s (seconds), m (minutes), or h (hours)")


def interval_to_cron(interval: str) -> str:
    """Convert interval to cron schedule string.

    Args:
        interval: Interval string like '30m', '2h', etc.

    Returns:
        Cron schedule string (e.g., '*/30 * * * *' for 30m).
    """
    seconds = interval_to_seconds(interval)

    # Calculate minutes and hours
    minutes = seconds // 60
    hours = minutes // 60
    minutes_remaining = minutes % 60

    if minutes_remaining == 0 and hours > 0:
        # Hourly schedule: every N hours
        if hours == 1:
            return "0 * * * *"  # Every hour at :00
        return f"0 */{hours} * * *"  # Every N hours at :00
    elif minutes < 60:
        # Minute schedule: every N minutes
        if minutes == 1:
            return "* * * * *"  # Every minute
        return f"*/{minutes} * * * *"
    else:
        # Complex interval - use the closest minute interval
        cron_minutes = min(minutes, 60)
        if cron_minutes == 60:
            return "0 * * * *"
        return f"*/{cron_minutes} * * * *"


def create_plist(interval_seconds: int, executable: str, log_file: Path) -> dict:
    """Create a LaunchAgent plist configuration.

    Args:
        interval_seconds: Interval in seconds between runs.
        executable: Path to nitrodump executable.
        log_file: Path to log file.

    Returns:
        plist dictionary.
    """
    # Create wrapper script that handles logging and notifications
    wrapper_script = f"""#!/bin/bash
# Nitrodump scheduler wrapper

LOG_FILE="{log_file}"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Run nitrodump with notifications and capture output
OUTPUT=$({executable} --notify 2>&1)

# Add timestamp to output
echo "[$TIMESTAMP]" >> "$LOG_FILE"
echo "$OUTPUT" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
"""

    wrapper_path = LAUNCH_AGENTS_DIR / "nitrodump_wrapper.sh"

    return (
        {
            "Label": LABEL,
            "ProgramArguments": ["/bin/bash", str(wrapper_path)],
            "StartInterval": interval_seconds,
            "RunAtLoad": True,
            "StandardOutPath": str(log_file),
            "StandardErrorPath": str(log_file.with_suffix(".err")),
            "EnvironmentVariables": {
                "PATH": "/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin:/opt/homebrew/sbin",
            },
        },
        wrapper_script,
        wrapper_path,
    )


def schedule(interval: str) -> bool:
    """Schedule nitrodump to run at the specified interval.

    Args:
        interval: Interval string like '30m', '2h', '12h', etc.

    Returns:
        True if successful, False otherwise.

    Raises:
        RuntimeError: If nitrodump executable is not found.
        ValueError: If interval format is invalid.
    """
    executable = get_nitrodump_executable()
    if not executable:
        raise RuntimeError(
            "nitrodump executable not found. Install it first with:\n  uv tool install nitrodump"
        )

    interval_seconds = interval_to_seconds(interval)

    # Validate interval range (1 minute to 12 hours)
    if interval_seconds < 60:
        raise ValueError("Interval must be at least 1 minute (1m)")
    if interval_seconds > 43200:
        raise ValueError("Interval must be at most 12 hours (12h)")

    # Unload any existing schedule first so launchd drops the cached interval
    unschedule()

    # Ensure LaunchAgents directory exists
    LAUNCH_AGENTS_DIR.mkdir(parents=True, exist_ok=True)

    # Create plist and wrapper
    plist_dict, wrapper_script, wrapper_path = create_plist(interval_seconds, executable, LOG_FILE)

    # Write wrapper script
    with open(wrapper_path, "w") as f:
        f.write(wrapper_script)

    # Make wrapper executable
    wrapper_path.chmod(0o755)

    # Write plist
    plist_path = get_plist_path()
    with open(plist_path, "wb") as f:
        plistlib.dump(plist_dict, f)

    # Load the agent using modern bootstrap
    uid = get_uid()
    result = subprocess.run(
        ["launchctl", "bootstrap", f"gui/{uid}", str(plist_path)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0 and "already bootstrapped" not in result.stderr.lower():
        print(f"Warning: Could not load LaunchAgent: {result.stderr}")
        print(f"You may need to run: launchctl bootstrap gui/{uid} {plist_path}")
        return False

    return True


def unschedule() -> bool:
    """Remove the scheduled nitrodump job.

    Returns:
        True if successful (or nothing to remove), False otherwise.
    """
    plist_path = get_plist_path()

    if not plist_path.exists():
        print("No scheduled job found.")
        return True

    # Use modern bootout
    uid = get_uid()
    subprocess.run(
        ["launchctl", "bootout", f"gui/{uid}/{LABEL}"],
        capture_output=True,
        check=False,
    )

    # Remove files
    plist_path.unlink(missing_ok=True)

    wrapper_path = LAUNCH_AGENTS_DIR / "nitrodump_wrapper.sh"
    wrapper_path.unlink(missing_ok=True)

    return True


def status() -> dict:
    """Get the status of the scheduled job.

    Returns:
        Dictionary with status information.
    """
    plist_path = get_plist_path()

    if not plist_path.exists():
        return {
            "scheduled": False,
            "message": "No scheduled job",
        }

    # Read plist to get interval
    with open(plist_path, "rb") as f:
        plist_data = plistlib.load(f)

    interval_seconds = plist_data.get("StartInterval", 0)

    # Convert to human-readable
    hours = interval_seconds // 3600
    minutes = (interval_seconds % 3600) // 60

    if hours > 0 and minutes > 0:
        interval_str = f"{hours}h {minutes}m"
    elif hours > 0:
        interval_str = f"{hours}h"
    else:
        interval_str = f"{minutes}m"

    # Check if loaded
    result = subprocess.run(
        ["launchctl", "list", LABEL],
        capture_output=True,
        text=True,
    )

    is_loaded = result.returncode == 0

    # Check log file
    log_exists = LOG_FILE.exists()
    last_run = None
    if log_exists:
        # Try to get last timestamp from log
        try:
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()
                for line in reversed(lines):
                    if line.startswith("[") and "]" in line:
                        try:
                            timestamp_str = line.split("]")[0].strip("[")
                            last_run = timestamp_str
                            break
                        except Exception:
                            pass
        except Exception:
            pass

    return {
        "scheduled": True,
        "loaded": is_loaded,
        "interval": interval_str,
        "interval_seconds": interval_seconds,
        "log_file": str(LOG_FILE),
        "log_exists": log_exists,
        "last_run": last_run,
    }


def show_logs(tail: int = 20) -> str:
    """Show recent log entries.

    Args:
        tail: Number of recent lines to show.

    Returns:
        Log content or error message.
    """
    if not LOG_FILE.exists():
        return "No log file found. Run nitrodump schedule status first."

    try:
        result = subprocess.run(
            ["tail", "-n", str(tail), str(LOG_FILE)],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return "Error reading log file"
    except FileNotFoundError:
        # tail not available, read with Python
        try:
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()
                return "".join(lines[-tail:])
        except Exception:
            return "Error reading log file"
