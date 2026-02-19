# Setup Guide

Complete guide to installing and configuring nitrodump on macOS.

## Prerequisites

- macOS ARM64 (Apple Silicon)
- Python 3.12 or later
- A Codeium-based IDE (Antigravity, VS Code + Codeium extension, etc.)
- [`uv`](https://github.com/astral-sh/uv) package manager (recommended) or pip

## Installation

### Step 1: Install uv (recommended)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or with Homebrew:

```bash
brew install uv
```

### Step 2: Install nitrodump

Choose one of the following methods:

#### Option A: Install as a uv tool (recommended)

Best for CLI usage - installs globally and updates automatically:

```bash
cd /path/to/nitrodump
uv tool install
```

The `nitrodump` command is now available globally.

#### Option B: Editable install

Good for development:

```bash
cd /path/to/nitrodump
uv pip install -e .
```

Or with pip:

```bash
pip install -e /path/to/nitrodump
```

### Step 3: Verify installation

```bash
nitrodump --help
```

You should see the help output with available commands.

## Quick Start

### One-time status check

```bash
nitrodump
```

### Set up scheduled monitoring

```bash
# Check every 30 minutes
nitrodump schedule set 30m
```

You'll receive a macOS notification and see logs at `~/nitrodump.log`.

## Configuration

### Default behavior

- Process name: `language_server_macos_arm`
- IDE name: `antigravity`
- Log file: `~/nitrodump.log`
- LaunchAgent label: `com.nitrodump.scheduler`

No configuration file is needed - nitrodump auto-discovers the running Codeium server.

### Customization (advanced)

You can modify defaults in `src/nitrodump/client.py`:

```python
class CodeiumClient:
    PROCESS_NAME = "language_server_macos_arm"  # Change for other platforms
    DEFAULT_IDE = "antigravity"  # Change for other IDEs
```

## Schedule Management

### Setting up a schedule

```bash
nitrodump schedule set <interval>
```

Valid intervals:
- `30m` to `12h` range
- Format: `<number><unit>` where unit is `m` (minutes) or `h` (hours)
- Examples: `30m`, `1h`, `2h`, `6h`, `12h`

### Checking schedule status

```bash
nitrodump schedule status
```

Example output:

```
Scheduled: ✓ Yes
Interval:  every 2 hours
Status:    Running (loaded in launchd)
Log file:  /Users/you/nitrodump.log
Last run:  2026-02-19 14:30:00
```

### Viewing logs

```bash
# Last 20 entries
nitrodump schedule logs

# Last 50 entries
nitrodump schedule logs -n 50

# Or use tail directly
tail -n 50 ~/nitrodump.log
```

### Removing a schedule

```bash
nitrodump schedule remove
```

## How Scheduling Works

nitrodump uses **macOS launchd** (not cron) for reliable scheduling:

1. A LaunchAgent plist is created at:
   ```
   ~/Library/LaunchAgents/com.nitrodump.scheduler.plist
   ```

2. A wrapper script is created that:
   - Runs `nitrodump`
   - Logs output with timestamps
   - Sends macOS notifications

3. The job is loaded via `launchctl load`

4. The job survives system reboots

### Manual launchd management

If you need to manually manage the LaunchAgent:

```bash
# Load the agent
launchctl load ~/Library/LaunchAgents/com.nitrodump.scheduler.plist

# Unload the agent
launchctl unload ~/Library/LaunchAgents/com.nitrodump.scheduler.plist

# List all loaded agents
launchctl list | grep nitrodump

# View agent info
launchctl print user/$(id -u)/com.nitrodump.scheduler
```

## Troubleshooting

### "nitrodump: command not found"

**Solution**: Make sure the bin directory is in your PATH.

For uv tools:

```bash
# Add to ~/.zshrc or ~/.bash_profile
export PATH="$HOME/.local/bin:$PATH"
```

Then reload:

```bash
source ~/.zshrc
```

### "Codeium language server is not running"

**Cause**: The Codeium language server isn't running.

**Solution**:
1. Open your IDE (Antigravity, VS Code, etc.)
2. Make sure the Codeium extension is active
3. Try again

### Schedule not running

**Check 1**: Verify the LaunchAgent is loaded:

```bash
launchctl list | grep nitrodump
```

If not found, reload:

```bash
nitrodump schedule set 2h
```

**Check 2**: Check for errors in stderr log:

```bash
cat ~/nitrodump.err
```

**Check 3**: Manually run the wrapper script:

```bash
bash ~/Library/LaunchAgents/nitrodump_wrapper.sh
```

### Notifications not appearing

**Cause**: Script Editor (osascript) doesn't have notification permissions.

**Solution**:
1. Open System Settings → Notifications
2. Find "Script Editor" or your terminal app
3. Enable "Allow Notifications"

### "uv tool install" fails

**Solution**: Make sure you have the latest uv:

```bash
uv self-update
```

Or use pip instead:

```bash
pip install -e /path/to/nitrodump
```

## Uninstallation

### Remove the tool

```bash
# If installed with uv tool
uv tool uninstall nitrodump

# If installed with pip
pip uninstall nitrodump
```

### Remove schedule

```bash
nitrodump schedule remove
```

### Clean up files

```bash
# Remove log files
rm ~/nitrodump.log ~/nitrodump.err

# Remove LaunchAgent (if it still exists)
rm ~/Library/LaunchAgents/com.nitrodump.scheduler.plist
rm ~/Library/LaunchAgents/nitrodump_wrapper.sh
```

## Development Setup

For contributing to nitrodump:

```bash
# Clone the repo
git clone <repo-url>
cd nitrodump

# Install with dev dependencies
uv sync --group dev

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=nitrodump --cov-report=term-missing

# Format code
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

## Next Steps

- See [README.md](../README.md) for usage examples
- See [api.md](api.md) for API documentation
- See [architecture.md](architecture.md) for technical details
