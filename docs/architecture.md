# Architecture

## Overview

`nitrodump` queries the local Codeium language server to retrieve user account information, available credits, and AI model rate limits. It also supports scheduled monitoring via macOS launchd.

## Components

```
┌─────────────┐      ┌─────────────┐      ┌──────────────────┐
│     CLI     │─────▶│   Client    │─────▶│ Codeium Server   │
│  (cli.py)   │      │ (client.py) │      │  (localhost)     │
└─────────────┘      └─────────────┘      └──────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Models    │
                    │ (models.py) │
                    └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ Formatter   │
                    │(formatter.py)│
                    └─────────────┘
                           │
                           ▼
                    ┌─────────────────────┐
                    │   Scheduler         │
                    │  (scheduler.py)     │
                    │                     │
                    │ ┌─────────────────┐ │
                    │ │  LaunchAgent    │ │
                    │ │  (launchd)      │ │
                    │ └─────────────────┘ │
                    │                     │
                    │ ┌─────────────────┐ │
                    │ │  Wrapper Script │ │
                    │ │  (bash + log)   │ │
                    │ └─────────────────┘ │
                    └─────────────────────┘
```

## Module Responsibilities

### `cli.py`
- Entry point for the command-line interface
- Argument parsing for `schedule` subcommands
- Error handling and exit codes
- Orchestrates client, formatter, and scheduler

### `client.py`
- Process discovery using `pgrep`
- Token extraction from process command line
- Port discovery using `lsof`
- HTTPS request to Codeium gRPC-web endpoint
- Response validation using Pydantic

### `models.py`
- Pydantic models for type-safe data handling
- JSON-to-Python object conversion
- Field aliasing for camelCase JSON to snake_case Python

### `formatter.py`
- Human-readable output formatting
- Unicode table rendering for model limits
- Consistent display of user info and model limits

### `scheduler.py`
- Creates and manages macOS LaunchAgents
- Generates bash wrapper scripts for scheduled runs
- Handles interval parsing (30m, 2h, etc.)
- Loads/unloads launchd jobs
- Log file management

### `notifier.py`
- macOS desktop notification support
- Uses `osascript` for system notifications
- Sound alerts for success/error states

## Data Flow

### One-Time Status Check

1. **Discovery**: Client finds the Codeium server process (`language_server_macos_arm`)
2. **Extraction**: CSRF token is parsed from process arguments
3. **Connection**: Local HTTPS port is discovered via `lsof`
4. **Request**: gRPC-web POST request to `GetUserStatus` endpoint
5. **Parsing**: JSON response is validated by Pydantic models
6. **Output**: Formatted status is displayed to user

### Scheduled Status Check

1. **Launch**: launchd triggers the wrapper script at specified interval
2. **Execution**: Wrapper runs `nitrodump` and captures output
3. **Logging**: Timestamped output is appended to `~/nitrodump.log`
4. **Notification**: macOS notification sent with status summary

## API Endpoint

**URL**: `https://127.0.0.1:{PORT}/exa.language_server_pb.LanguageServerService/GetUserStatus`

**Method**: POST

**Headers**:
- `X-Codeium-Csrf-Token`: Extracted from process
- `Content-Type`: application/json
- `Connect-Protocol-Version`: 1

**Request Body**:
```json
{
  "metadata": {
    "ideName": "antigravity",
    "extensionName": "antigravity",
    "locale": "en"
  }
}
```

## LaunchAgent Configuration

Scheduled jobs use macOS launchd with the following structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.nitrodump.scheduler</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>~/Library/LaunchAgents/nitrodump_wrapper.sh</string>
    </array>
    <key>StartInterval</key>
    <integer>3600</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>~/nitrodump.log</string>
    <key>StandardErrorPath</key>
    <string>~/nitrodump.err</string>
</dict>
</plist>
```

## Security Considerations

- Server uses self-signed certificates (`verify=False` in requests)
- CSRF token required for all requests
- Communication is over localhost only
- No credentials are stored or transmitted beyond the CSRF token
- LaunchAgent runs with user privileges (no root access)

## Platform Support

Currently supports:
- macOS ARM64 (`language_server_macos_arm`)

Future platforms could be added by extending the process discovery logic.
