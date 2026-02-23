import sys
import traceback
from nitrodump.client import CodeiumClient

try:
    client = CodeiumClient()
    response = client.get_user_status()
    print("Success:")
    print(response.model_dump_json(indent=2))
except Exception as e:
    print("Caught Exception:", file=sys.stderr)
    traceback.print_exc()
