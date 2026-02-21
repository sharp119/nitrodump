import sys
from nitrodump.client import CodeiumClient
from nitrodump.notifier import send_success_notification, send_notification

status = CodeiumClient().get_user_status().user_status
plan = status.plan_status.plan_info.plan_name

model_texts = []
for config in status.cascade_model_config_data.client_model_configs:
    name = config.label
    short_name = name[:10]
    pct = config.quota_info.remaining_percent
    model_texts.append(f"{short_name}:{pct}%")

models_str = ", ".join(model_texts)
message = f"Plan: {plan}\n{models_str}"
script = f'display notification "{message}" with title "Nitrodump" sound name "Glass"'
print(repr(script))

import subprocess
try:
    result = subprocess.run(["osascript", "-e", script], capture_output=True, check=True)
    print("Success")
except subprocess.CalledProcessError as e:
    print("Error code:", e.returncode)
    print("Stderr:", e.stderr)
