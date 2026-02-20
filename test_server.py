from nitrodump.client import CodeiumClient
client = CodeiumClient()
for pid in [1478, 2291]:
    token = client._extract_csrf_token(pid)
    port = client._find_server_port(pid)
    print(f"PID: {pid}, Token: {token}, Port: {port}")
