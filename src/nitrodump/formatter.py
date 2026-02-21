"""Formatters for displaying Antigravity/Codeium status information."""

from typing import List

from nitrodump.models import ClientModelConfig, UserStatus


def format_user_status(status: UserStatus) -> str:
    """Format user status as a human-readable string.

    Args:
        status: The user status to format.

    Returns:
        A formatted string with user and plan information.
    """
    lines = [
        f"User: {status.name} ({status.email})",
        f"Plan: {status.user_tier.name}",
    ]

    # Add credits if available
    if status.available_prompt_credits is not None:
        prompt_credits = status.available_prompt_credits
        max_prompt = status.plan_status.plan_info.monthly_prompt_credits or "N/A"
        flow_credits = status.available_flow_credits or "N/A"
        max_flow = status.plan_status.plan_info.monthly_flow_credits or "N/A"

        lines.extend(
            [
                f"Prompt: {prompt_credits} / {max_prompt}",
                f"Flow:   {flow_credits} / {max_flow}",
            ]
        )

    return "\n".join(lines)


def format_model_table(configs: List[ClientModelConfig]) -> str:
    """Format model rate limits as a bordered table.

    Args:
        configs: List of model configurations to format.

    Returns:
        A formatted table with model rate limits.
    """
    if not configs:
        return ""

    # Sort by label for consistent output
    sorted_configs = sorted(configs, key=lambda c: c.label)

    # Define columns
    headers = ["Model", "Remaining", "Reset Time"]

    # Calculate column widths
    model_width = max(len(headers[0]), max(len(c.label) for c in sorted_configs))
    remaining_width = max(len(headers[1]), 5)  # at least "100%" (4 chars)
    reset_width = max(len(headers[2]), max(len(c.quota_info.reset_time) for c in sorted_configs))

    # Add padding
    model_padding = 2
    remaining_padding = 2
    reset_padding = 2

    total_width = (
        model_width
        + model_padding
        + remaining_width
        + remaining_padding
        + reset_width
        + reset_padding
        + 4  # borders: │ │ │
    )

    # Helper to create separator row
    def separator(aligns: str = "llr") -> str:
        parts = ["┼"]
        for i, width in enumerate([model_width, remaining_width, reset_width]):
            align = aligns[i] if i < len(aligns) else "l"
            if align == "r":
                parts.append("─" * (width + 2))
            else:
                parts.append("─" * (width + 2))
            parts.append("┼")
        return "".join(parts)

    # Helper to create data row
    def data_row(model: str, remaining: str, reset: str, aligns: str = "lll") -> str:
        parts = ["│"]
        # Model column (left aligned)
        parts.append(f" {model.ljust(model_width)} │")
        # Remaining column (left aligned)
        parts.append(f" {remaining.ljust(remaining_width)} │")
        # Reset Time column (left aligned)
        parts.append(f" {reset.ljust(reset_width)} │")
        return "".join(parts)

    # Build table
    lines = []

    # Top border
    lines.append(
        "┌"
        + "─" * (model_width + 2)
        + "┬"
        + "─" * (remaining_width + 2)
        + "┬"
        + "─" * (reset_width + 2)
        + "┐"
    )

    # Header row
    lines.append(data_row(headers[0], headers[1], headers[2]))

    # Header separator
    lines.append(
        "├"
        + "─" * (model_width + 2)
        + "┼"
        + "─" * (remaining_width + 2)
        + "┼"
        + "─" * (reset_width + 2)
        + "┤"
    )

    # Data rows
    for config in sorted_configs:
        remaining = f"{config.quota_info.remaining_percent}%"
        reset = config.quota_info.reset_time
        lines.append(data_row(config.label, remaining, reset))

    # Bottom border
    lines.append(
        "└"
        + "─" * (model_width + 2)
        + "┴"
        + "─" * (remaining_width + 2)
        + "┴"
        + "─" * (reset_width + 2)
        + "┘"
    )

    return "\n".join(lines)


def format_full_status(status: UserStatus) -> str:
    """Format complete status including user info and model limits.

    Args:
        status: The user status to format.

    Returns:
        A complete formatted status report.
    """
    output = [format_user_status(status)]

    if status.cascade_model_config_data:
        configs = status.cascade_model_config_data.client_model_configs
        if configs:
            output.append("")
            output.append(format_model_table(configs))

    return "\n".join(output)
