"""Notification utilities for macOS."""

import subprocess
from typing import Optional


def send_notification(title: str, message: str, sound: str = "Glass") -> bool:
    """Send a macOS desktop notification.

    Args:
        title: Notification title.
        message: Notification message body.
        sound: Notification sound name (default: 'Glass').

    Returns:
        True if successful, False otherwise.
    """
    script = f'display notification "{message}" with title "{title}" sound name "{sound}"'

    try:
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def send_error_notification(message: str = "Failed to get Codeium status") -> bool:
    """Send an error notification.

    Args:
        message: Error message.

    Returns:
        True if successful, False otherwise.
    """
    return send_notification("Nitrodump Error", message, sound="Basso")


def send_success_notification(status_info: dict) -> bool:
    """Send a success notification with status info.

    Args:
        status_info: Dictionary with status information.

    Returns:
        True if successful, False otherwise.
    """
    plan = status_info.get("plan", "Unknown")
    prompt_credits = status_info.get("prompt_credits")

    if prompt_credits:
        message = f"Plan: {plan}\nPrompt Credits: {prompt_credits}"
    else:
        message = f"Plan: {plan}"

    return send_notification("Nitrodump", message)
