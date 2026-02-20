import sys
from nitrodump.client import CodeiumClient
try:
    c = CodeiumClient()
    print("PID:", c.pid)
    print("Port:", c.port)
    print("Token:", c.token)
    status = c.get_user_status(return_raw=True)
    print(status[0])
except Exception as e:
    print(repr(e))
    import traceback
    traceback.print_exc()
