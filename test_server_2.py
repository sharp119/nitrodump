import subprocess
pid = 1478
result = subprocess.run(
    ["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"],
    capture_output=True,
    text=True,
    check=False,
)
for line in result.stdout.splitlines():
    parts = line.split()
    if len(parts) >= 2 and parts[1] == str(pid):
        for part in parts:
            if part.startswith("127.0.0.1:"):
                print(int(part.split(":")[1]))
