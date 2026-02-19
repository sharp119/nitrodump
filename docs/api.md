# API Documentation

## `nitrodump.client`

### `CodeiumServerError`

Exception raised when the Codeium server cannot be found or contacted.

```python
class CodeiumServerError(Exception):
    pass
```

---

### `CodeiumClient`

Main client for interacting with the Codeium language server.

#### Constructor

```python
CodeiumClient(ide_name: str = "antigravity")
```

Initialize the client.

- **`ide_name`**: The IDE name to report to the server (default: "antigravity")

#### Methods

##### `get_user_status() -> GetUserStatusResponse`

Get the current user status from the Codeium server.

**Returns**: `GetUserStatusResponse` - User status with plan info, credits, and model quotas

**Raises**:
- `CodeiumServerError`: If the server cannot be contacted

#### Properties

- **`pid`**: `Optional[int]` - The server process ID (discovered lazily)
- **`port`**: `Optional[int]` - The server port (discovered lazily)
- **`token`**: `Optional[str]` - The CSRF token (discovered lazily)

---

## `nitrodump.models`

### Data Models

All models use Pydantic for validation and field aliasing (camelCase to snake_case).

#### `GetUserStatusResponse`

Root response wrapper.

```python
class GetUserStatusResponse(BaseModel):
    user_status: UserStatus  # Field(alias="userStatus")
```

#### `UserStatus`

Complete user status response.

```python
class UserStatus(BaseModel):
    name: str
    email: str
    plan_status: PlanStatus  # Field(alias="planStatus")
    user_tier: UserTier  # Field(alias="userTier")
    available_prompt_credits: Optional[int] = None  # Field(alias="availablePromptCredits")
    available_flow_credits: Optional[int] = None  # Field(alias="availableFlowCredits")
    cascade_model_config_data: Optional[CascadeModelConfigData] = None  # Field(alias="cascadeModelConfigData")
```

#### `UserTier`

User tier information.

```python
class UserTier(BaseModel):
    id: str
    name: str
    description: str
```

#### `PlanStatus`

Plan status information.

```python
class PlanStatus(BaseModel):
    plan_info: PlanInfo  # Field(alias="planInfo")
```

#### `PlanInfo`

Plan details.

```python
class PlanInfo(BaseModel):
    teams_tier: str  # Field(alias="teamsTier")
    plan_name: str  # Field(alias="planName")
    monthly_prompt_credits: Optional[int] = None  # Field(alias="monthlyPromptCredits")
    monthly_flow_credits: Optional[int] = None  # Field(alias="monthlyFlowCredits")
```

#### `CascadeModelConfigData`

Model configuration container.

```python
class CascadeModelConfigData(BaseModel):
    client_model_configs: List[ClientModelConfig]  # Field(alias="clientModelConfigs")
```

#### `ClientModelConfig`

Configuration for a single AI model.

```python
class ClientModelConfig(BaseModel):
    label: str
    model_or_alias: ModelOrAlias  # Field(alias="modelOrAlias")
    supports_images: Optional[bool] = None  # Field(alias="supportsImages")
    is_recommended: Optional[bool] = None  # Field(alias="isRecommended")
    quota_info: QuotaInfo  # Field(alias="quotaInfo")
```

#### `ModelOrAlias`

Model identifier.

```python
class ModelOrAlias(BaseModel):
    model: str
```

#### `QuotaInfo`

Rate limit quota information.

```python
class QuotaInfo(BaseModel):
    remaining_fraction: float  # Field(alias="remainingFraction")
    reset_time: str  # Field(alias="resetTime")

    @property
    def remaining_percent(self) -> int:
        """Return remaining quota as a percentage (0-100)."""
        return int(self.remaining_fraction * 100)
```

---

## `nitrodump.formatter`

### Formatters

#### `format_user_status(status: UserStatus) -> str`

Format user status as a human-readable string.

**Parameters**:
- **`status`**: `UserStatus` - The user status to format

**Returns**: Formatted string with user and plan information

**Example output**:
```
User: Jane Doe (jane@example.com)
Plan: Google AI Pro
Prompt: 450 / 50000
Flow:   95 / 150000
```

#### `format_model_table(configs: List[ClientModelConfig]) -> str`

Format model rate limits as a bordered Unicode table.

**Parameters**:
- **`configs`**: `List[ClientModelConfig]` - Model configurations to format

**Returns**: Formatted table with model rate limits

**Example output**:
```
┌─────────────────────────────┬───────────┬─────────────────────┐
│ Model                       │ Remaining │ Reset Time          │
├─────────────────────────────┼───────────┼─────────────────────┤
│ Claude Opus 4.6 (Thinking)  │ 80%       │ 2026-02-19T12:04:51Z│
└─────────────────────────────┴───────────┴─────────────────────┘
```

#### `format_full_status(status: UserStatus) -> str`

Format complete status including user info and model limits.

**Parameters**:
- **`status`**: `UserStatus` - The user status to format

**Returns**: Complete formatted status report

---

## `nitrodump.scheduler`

### Scheduling Functions

#### `schedule(interval: str) -> bool`

Schedule nitrodump to run at the specified interval.

**Parameters**:
- **`interval`**: Interval string like '30m', '2h', '12h' (min: 30m, max: 12h)

**Returns**: `True` if successful

**Raises**:
- `RuntimeError`: If nitrodump executable is not found
- `ValueError`: If interval format is invalid or out of range

**Example**:
```python
scheduler.schedule("2h")  # Schedule every 2 hours
```

#### `unschedule() -> bool`

Remove the scheduled nitrodump job.

**Returns**: `True` if successful

#### `status() -> dict`

Get the status of the scheduled job.

**Returns**: Dictionary with keys:
- `scheduled` (bool): Whether a schedule exists
- `loaded` (bool): Whether loaded in launchd
- `interval` (str): Human-readable interval (e.g., "2h")
- `interval_seconds` (int): Interval in seconds
- `log_file` (str): Path to log file
- `log_exists` (bool): Whether log file exists
- `last_run` (str | None): Timestamp of last run

#### `show_logs(tail: int = 20) -> str`

Show recent log entries.

**Parameters**:
- **`tail`**: Number of recent lines to show (default: 20)

**Returns**: Log content or error message

### Utility Functions

#### `interval_to_seconds(interval: str) -> int`

Convert interval string to seconds.

**Parameters**:
- **`interval`**: Interval string like '30m', '2h', '1d'

**Returns**: Interval in seconds

**Raises**:
- `ValueError`: If interval format is invalid

**Examples**:
```python
interval_to_seconds("30m")  # 1800
interval_to_seconds("2h")   # 7200
```

#### `get_log_path() -> Path`

Get the log file path (`~/nitrodump.log`).

**Returns**: Path to log file

#### `get_plist_path() -> Path`

Get the LaunchAgent plist file path.

**Returns**: Path to plist file

---

## `nitrodump.notifier`

### Notification Functions

#### `send_notification(title: str, message: str, sound: str = "Glass") -> bool`

Send a macOS desktop notification.

**Parameters**:
- **`title`**: Notification title
- **`message`**: Notification message body
- **`sound`**: Notification sound name (default: "Glass")

**Returns**: `True` if successful

**Example**:
```python
send_notification("Nitrodump", "Plan: Pro - Prompt: 450/50000")
```

#### `send_error_notification(message: str) -> bool`

Send an error notification.

**Parameters**:
- **`message`**: Error message

**Returns**: `True` if successful

#### `send_success_notification(status_info: dict) -> bool`

Send a success notification with status info.

**Parameters**:
- **`status_info`**: Dictionary with status information

**Returns**: `True` if successful

---

## `nitrodump.cli`

### Command-line Interface

#### `main(argv=None) -> int`

Run the CLI.

**Parameters**:
- **`argv`**: Arguments to parse (defaults to `sys.argv[1:]`)

**Returns**: Exit code (0 for success, 1 for error)

### Commands

| Command | Description |
|---------|-------------|
| `nitrodump` | Run one-time status check |
| `nitrodump schedule set <interval>` | Create/update schedule |
| `nitrodump schedule remove` | Remove schedule |
| `nitrodump schedule status` | Show schedule info |
| `nitrodump schedule logs [-n N]` | View log entries |

---

## Example Usage

### As a library

```python
from nitrodump.client import CodeiumClient
from nitrodump.formatter import format_full_status

# Create client
client = CodeiumClient()

# Get user status
response = client.get_user_status()
status = response.user_status

# Format and print
print(format_full_status(status))

# Or access data directly
print(f"User: {status.name}")
print(f"Plan: {status.user_tier.name}")

for model in status.cascade_model_config_data.client_model_configs:
    print(f"{model.label}: {model.quota_info.remaining_percent}% remaining")
```

### Scheduling programmatically

```python
from nitrodump import scheduler

# Set up schedule
scheduler.schedule("2h")

# Check status
info = scheduler.status()
print(f"Scheduled: {info['scheduled']}")
print(f"Interval: {info['interval']}")

# View logs
logs = scheduler.show_logs(tail=50)
print(logs)

# Remove schedule
scheduler.unschedule()
```
