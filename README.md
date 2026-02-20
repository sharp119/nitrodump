# nitrodump

A Python CLI tool to quickly dump Antigravity/Codeium account status, credits, and AI model rate limits. Features built-in scheduling for automated monitoring on macOS.

## Features

- **Auto-discovery**: Finds the running Codeium language server process automatically
- **Dynamic extraction**: Extracts authentication tokens and ports dynamically
- **Account info**: Displays user account info and plan details
- **Credit tracking**: Shows available prompt and flow credits
- **Model rate limits**: Lists all AI models with current rate limit status and reset times
- **Multiple output formats**: Table, JSON, or raw network response
- **Scheduled monitoring**: Built-in scheduler for automatic status checks (30min to 12hr intervals)
- **Desktop notifications**: macOS notifications with status updates
- **Logging**: Timestamped logs of all scheduled runs

## Requirements

- Python 3.12+
- macOS ARM64 (currently supports `language_server_macos_arm`)
- Codeium language server running locally (started automatically by your IDE)
- Works with Antigravity (Google's AI IDE) and other Codeium-based editors

## Installation

### Option 1: Install from source (editable)

```bash
cd /path/to/nitrodump
uv pip install -e .
```

Or with pip:

```bash
pip install -e /path/to/nitrodump
```

### Option 2: Install as a uv tool (recommended for CLI)

```bash
cd /path/to/nitrodump
uv tool install .
```

This installs the `nitrodump` command globally.

## Usage

### Output Formats

```bash
# Default: formatted table output
nitrodump

# Structured JSON (from Pydantic model, snake_case keys)
nitrodump --json

# Raw network response (direct from API, camelCase keys)
nitrodump --raw
```

### Default Output (Table)

```bash
nitrodump
```

Example output:

```
User: Jane Doe (jane@example.com)
Plan: Google AI Pro
Prompt: 450 / 50000
Flow:   95 / 150000

┌─────────────────────────────┬───────────┬─────────────────────┐
│ Model                       │ Remaining │ Reset Time          │
├─────────────────────────────┼───────────┼─────────────────────┤
│ Claude Opus 4.6 (Thinking)  │ 80%       │ 2026-02-19T12:04:51Z│
│ Claude Sonnet 4.5           │ 80%       │ 2026-02-19T12:04:51Z│
│ Gemini 3 Flash              │ 100%      │ 2026-02-19T14:28:40Z│
│ Gemini 3 Pro (High)         │ 100%      │ 2026-02-19T14:28:40Z│
└─────────────────────────────┴───────────┴─────────────────────┘
```

### JSON Output (`--json`)

Clean, structured JSON from the validated Pydantic model:

```bash
nitrodump --json
```

```json
{
  "user_status": {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "user_tier": {
      "id": "g1-pro-tier",
      "name": "Google AI Pro"
    },
    "plan_status": {
      "plan_info": {
        "plan_name": "Pro",
        "monthly_prompt_credits": 50000,
        "monthly_flow_credits": 150000
      }
    },
    "available_prompt_credits": 450,
    "available_flow_credits": 95,
    "cascade_model_config_data": {
      "client_model_configs": [
        {
          "label": "Claude Opus 4.6 (Thinking)",
          "quota_info": {
            "remaining_fraction": 0.8,
            "reset_time": "2026-02-19T12:04:51Z"
          }
        }
      ]
    }
  }
}
```

### Raw Output (`--raw`)

The raw network response from the Codeium API (camelCase keys, all fields):

```bash
nitrodump --raw
```

```json
{
  "userStatus": {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "disableTelemetry": true,
    "planStatus": {
      "planInfo": {
        "teamsTier": "TEAMS_TIER_PRO",
        "planName": "Pro",
        "monthlyPromptCredits": 50000,
        "hasAutocompleteFastMode": true,
        "cascadeWebSearchEnabled": true
      },
      "availablePromptCredits": 450
    },
    "cascadeModelConfigData": {
      "clientModelConfigs": [...]
    }
  }
}
```

Use `--raw` to see **all** available fields from the API, including those not shown in the default output.

### Scheduled Monitoring

Set up automatic status checks at regular intervals:

```bash
# Schedule every 30 minutes
nitrodump schedule set 30m

# Schedule every 2 hours
nitrodump schedule set 2h

# Schedule every 12 hours (maximum interval)
nitrodump schedule set 12h
```

When scheduled, nitrodump will:
- Run automatically at the specified interval
- Log results to `~/nitrodump.log`
- Send a macOS desktop notification with each run

#### Schedule Commands

| Command | Description |
|---------|-------------|
| `nitrodump schedule set <interval>` | Create/update a schedule |
| `nitrodump schedule status` | Show current schedule info |
| `nitrodump schedule logs` | View recent log entries |
| `nitrodump schedule logs -n 50` | View last 50 log lines |
| `nitrodump schedule remove` | Remove the schedule |

#### Interval Format

- `30m` = 30 minutes (minimum)
- `1h` = 1 hour
- `2h` = 2 hours
- `12h` = 12 hours (maximum)

#### Checking Schedule Status

```bash
$ nitrodump schedule status
Scheduled: ✓ Yes
Interval:  every 2 hours
Status:    Running (loaded in launchd)
Log file:  /Users/you/nitrodump.log
Last run:  2026-02-19 14:30:00
```

#### Viewing Logs

```bash
# View last 20 log entries (default)
nitrodump schedule logs

# View last 50 entries
nitrodump schedule logs -n 50

# Or view the log file directly
tail -n 50 ~/nitrodump.log
```

Log format:

```
[2026-02-19 14:30:00]
User: Jane Doe (jane@example.com)
Plan: Google AI Pro
Prompt: 450 / 50000
Flow:   95 / 150000
...
```

#### Removing the Schedule

```bash
nitrodump schedule remove
✓ Scheduled job removed
```

## How It Works

### One-Time Check

1. Finds the Codeium server process using `pgrep`
2. Extracts the CSRF token from the process command line
3. Finds the local HTTPS port using `lsof`
4. Makes a gRPC-web request to the `GetUserStatus` endpoint
5. Parses the JSON response and displays formatted output

### Scheduled Checks

The scheduler uses **macOS launchd** (more reliable than cron):

1. Creates a LaunchAgent plist at `~/Library/LaunchAgents/com.nitrodump.scheduler.plist`
2. Generates a wrapper script that:
   - Runs `nitrodump` and captures output
   - Appends timestamped results to `~/nitrodump.log`
   - Sends a macOS notification with plan/credits info
3. Loads the agent via `launchctl`
4. Survives system reboots

## Development

Install development dependencies:

```bash
uv sync --group dev
```

Run tests:

```bash
uv run pytest
```

Run tests with coverage:

```bash
uv run pytest --cov=nitrodump --cov-report=term-missing
```

Format code:

```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

## Project Structure

```
nitrodump/
├── src/
│   └── nitrodump/
│       ├── __init__.py      # Package init
│       ├── cli.py           # Command-line interface
│       ├── client.py        # API client for Codeium server
│       ├── formatter.py     # Output formatting
│       ├── models.py        # Pydantic data models
│       ├── scheduler.py     # macOS launchd scheduler
│       └── notifier.py      # macOS notification utilities
├── tests/
│   ├── conftest.py          # Pytest config
│   ├── test_client.py       # Client tests
│   ├── test_formatter.py    # Formatter tests
│   ├── test_models.py       # Model tests
│   └── test_scheduler.py    # Scheduler tests
├── docs/
│   ├── api.md               # API documentation
│   ├── architecture.md      # Architecture overview
│   └── setup.md             # Setup guide
├── pyproject.toml           # Project config
└── README.md                # This file
```

## Troubleshooting

### "Codeium language server is not running"

Make sure your IDE (Antigravity, VS Code with Codeium, etc.) is open and the Codeium extension is active.

### Schedule not running

Check if the LaunchAgent is loaded:

```bash
launchctl list | grep nitrodump
```

If not loaded, try:

```bash
launchctl load ~/Library/LaunchAgents/com.nitrodump.scheduler.plist
```

### Notifications not appearing

Check System Settings → Notifications → Script Editor (osascript) is allowed to send notifications.

## License

MIT
