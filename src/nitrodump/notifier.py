"""Notification utilities for macOS."""

import subprocess
from typing import Optional


def send_notification(
    title: str, message: str, subtitle: Optional[str] = None, sound: str = "Glass"
) -> bool:
    """Send a macOS desktop notification.

    Args:
        title: Notification title.
        message: Notification body text.
        subtitle: Optional notification subtitle.
        sound: System sound to play (default: Glass).

    Returns:
        True if successful, False otherwise.
    """
    if subtitle:
        script = f'display notification "{message}" with title "{title}" subtitle "{subtitle}" sound name "{sound}"'
    else:
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


def send_success_notification(status) -> bool:
    """Send a success notification with status info.

    Args:
        status: UserStatus object containing plan and model quotas.

    Returns:
        True if successful, False otherwise.
    """
    try:
        plan = status.plan_status.plan_info.plan_name
    except AttributeError:
        plan = "Unknown"

    # Format model summaries compactly: "Opus:100%, Sonnet:100%"
    model_texts = []
    if status.cascade_model_config_data and status.cascade_model_config_data.client_model_configs:
        for config in status.cascade_model_config_data.client_model_configs:
            name = config.label

            # Create a short alias manually for common models
            if "Opus" in name:
                short_name = "Opus"
            elif "Sonnet" in name:
                short_name = "Sonnet"
            elif "GPT-OSS" in name:
                short_name = "GPT"
            elif "Flash" in name:
                short_name = "Flash"
            elif "Gemini 3 Pro (High)" in name:
                short_name = "G3P(H)"
            elif "Gemini 3 Pro (Low)" in name:
                short_name = "G3P(L)"
            elif "Gemini 3.1 Pro (High)" in name:
                short_name = "G3.1P(H)"
            elif "Gemini 3.1 Pro (Low)" in name:
                short_name = "G3.1P(L)"
            else:
                short_name = name[:7]

            # Calc remaining percent
            pct = config.quota_info.remaining_percent
            if pct < 100:
                model_texts.append(f"⚠️ {short_name}:{pct}%")
            else:
                model_texts.append(f"{short_name}:{pct}%")

    if model_texts:
        models_str = " • ".join(model_texts)
        subtitle = f"Plan: {plan}"
        message = models_str
    else:
        subtitle = None
        message = f"Plan: {plan}"

    return send_notification("Nitrodump", message, subtitle=subtitle)
