"""macOS Menu Bar Launchd Agent Manager."""

import os
import plistlib
import subprocess
from pathlib import Path
from typing import Dict

from .scheduler import get_nitrodump_executable, get_uid

LAUNCH_AGENTS_DIR = Path.home() / "Library" / "LaunchAgents"
LABEL = "com.nitrodump.menubar"
LOG_FILE = Path.home() / "nitrodump_menubar.log"


def get_plist_path() -> Path:
    """Get the path to the LaunchAgent plist file."""
    return LAUNCH_AGENTS_DIR / f"{LABEL}.plist"


def create_plist(executable: str, log_file: Path) -> dict:
    """Create a LaunchAgent plist configuration for the Menu Bar app.

    Args:
        executable: Path to nitrodump executable.
        log_file: Path to log file.

    Returns:
        plist dictionary.
    """
    return {
        "Label": LABEL,
        "ProgramArguments": [executable, "menubar-run"],
        "RunAtLoad": True,
        "KeepAlive": True,
        "StandardOutPath": str(log_file),
        "StandardErrorPath": str(log_file.with_suffix(".err")),
        "EnvironmentVariables": {
            "PATH": "/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin:/opt/homebrew/sbin",
        },
    }


def start() -> bool:
    """Start the menu bar app via launchd."""
    executable = get_nitrodump_executable()
    if not executable:
        raise RuntimeError(
            "nitrodump executable not found. Install it first with:\n  uv tool install nitrodump"
        )

    # Ensure LaunchAgents directory exists
    LAUNCH_AGENTS_DIR.mkdir(parents=True, exist_ok=True)

    # Stop any existing instance first
    stop()

    # Create plist
    plist_dict = create_plist(executable, LOG_FILE)
    plist_path = get_plist_path()

    # Write plist
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
        print(f"Warning: Could not start menu bar app: {result.stderr}")
        return False

    return True


def stop() -> bool:
    """Stop the menu bar app via launchd."""
    plist_path = get_plist_path()
    
    # Use modern bootout if it's currently loaded
    uid = get_uid()
    subprocess.run(
        ["launchctl", "bootout", f"gui/{uid}/{LABEL}"],
        capture_output=True,
        check=False,
    )

    if plist_path.exists():
        try:
            plist_path.unlink()
        except OSError:
            pass

    return True


def status() -> Dict[str, bool]:
    """Get the status of the menu bar app.

    Returns:
        Dictionary with 'running' boolean.
    """
    plist_path = get_plist_path()
    
    if not plist_path.exists():
        return {"running": False}

    # Check if loaded using launchctl print
    uid = get_uid()
    result = subprocess.run(
        ["launchctl", "print", f"gui/{uid}/{LABEL}"],
        capture_output=True,
        text=True,
        check=False,
    )

    is_loaded = result.returncode == 0
    return {"running": is_loaded}
