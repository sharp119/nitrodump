"""Command-line interface for nitrodump."""

import argparse
import json
import sys
from datetime import datetime

from nitrodump.client import CodeiumClient, CodeiumServerError
from nitrodump.formatter import format_full_status
from nitrodump import scheduler


def cmd_run(args) -> int:
    """Run the status check command.

    Args:
        args: Parsed arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    client = CodeiumClient()

    try:
        # Raw mode - output the raw network response
        if getattr(args, 'raw', False):
            data, response = client.get_user_status(return_raw=True)
            print(json.dumps(data, indent=2))
            return 0

        # JSON mode - output structured JSON from Pydantic model
        elif getattr(args, 'json', False):
            response = client.get_user_status()
            print(response.model_dump_json(indent=2))
            return 0

        # Default - formatted table output
        else:
            response = client.get_user_status()
            print(format_full_status(response.user_status))
            return 0

    except CodeiumServerError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


def cmd_schedule(args) -> int:
    """Handle schedule-related commands.

    Args:
        args: Parsed arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    if args.action == "set":
        try:
            scheduler.schedule(args.interval)
            interval_desc = _describe_interval(args.interval)
            print(f"✓ Scheduled nitrodump to run every {interval_desc}")
            print(f"  Log file: {scheduler.get_log_path()}")
            print(f"\nTo check status: nitrodump schedule status")
            print(f"To stop: nitrodump schedule remove")
            return 0
        except (ValueError, RuntimeError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            return 1

    elif args.action == "remove":
        try:
            scheduler.unschedule()
            print("✓ Scheduled job removed")
            return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    elif args.action == "status":
        try:
            info = scheduler.status()

            if not info["scheduled"]:
                print("No scheduled job found.")
                print("\nTo set up a schedule:")
                print("  nitrodump schedule set <interval>")
                print("\nExamples:")
                print("  nitrodump schedule set 30m   # Every 30 minutes")
                print("  nitrodump schedule set 2h    # Every 2 hours")
                print("  nitrodump schedule set 12h   # Every 12 hours")
                return 0

            # Print status
            print(f"Scheduled: ✓ Yes")
            print(f"Interval:  every {info['interval']}")

            if info["loaded"]:
                print(f"Status:    Running (loaded in launchd)")
            else:
                print(f"Status:    Scheduled but not loaded")

            print(f"Log file:  {info['log_file']}")

            if info["last_run"]:
                print(f"Last run:  {info['last_run']}")

            return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    elif args.action == "logs":
        try:
            logs = scheduler.show_logs(tail=args.lines)
            print(logs)
            return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    return 1


def _describe_interval(interval: str) -> str:
    """Get a human-readable description of an interval.

    Args:
        interval: Interval string like '30m', '2h'.

    Returns:
        Human-readable description.
    """
    interval = interval.strip().lower()
    unit = interval[-1]
    value = int(interval[:-1])

    unit_names = {
        "s": ("second", "seconds"),
        "m": ("minute", "minutes"),
        "h": ("hour", "hours"),
    }

    singular, plural = unit_names.get(unit, ("unit", "units"))
    unit_name = singular if value == 1 else plural

    return f"{value} {unit_name}"


def parse_args(argv=None):
    """Parse command-line arguments.

    Args:
        argv: Arguments to parse (defaults to sys.argv[1:]).

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        prog="nitrodump",
        description="Quick dump of Antigravity/Codeium account status and rate limits.",
    )

    # Output format flags
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--json",
        action="store_true",
        help="Output as structured JSON",
    )
    output_group.add_argument(
        "--raw",
        action="store_true",
        help="Output raw network response JSON",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Default status command (no arguments needed)
    parser.set_defaults(func=cmd_run)

    # Schedule subcommand
    schedule_parser = subparsers.add_parser(
        "schedule",
        help="Manage scheduled status checks",
    )
    schedule_subparsers = schedule_parser.add_subparsers(dest="action", help="Schedule actions")

    # schedule set
    set_parser = schedule_subparsers.add_parser("set", help="Set up a schedule")
    set_parser.add_argument(
        "interval",
        help="Interval between runs (e.g., 30m, 2h, 12h). Min: 30m, Max: 12h",
    )
    set_parser.set_defaults(func=cmd_schedule)

    # schedule remove
    remove_parser = schedule_subparsers.add_parser("remove", help="Remove the schedule")
    remove_parser.set_defaults(func=cmd_schedule)

    # schedule status
    status_parser = schedule_subparsers.add_parser("status", help="Show schedule status")
    status_parser.set_defaults(func=cmd_schedule)

    # schedule logs
    logs_parser = schedule_subparsers.add_parser("logs", help="Show recent logs")
    logs_parser.add_argument(
        "-n",
        "--lines",
        type=int,
        default=20,
        help="Number of lines to show (default: 20)",
    )
    logs_parser.set_defaults(func=cmd_schedule)

    return parser.parse_args(argv)


def main(argv=None) -> int:
    """Run the CLI.

    Args:
        argv: Arguments to parse (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 for success, 1 for error).
    """
    args = parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
