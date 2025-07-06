import os
from dhanhq import dhanhq
from dotenv import load_dotenv

load_dotenv()
class DhanConnecting:
    
    def get_positions(self):
        try:
            client_id = os.environ.get("DHAN_CLIENT_ID")
            access_token = os.environ.get("DHAN_ACCESS_TOKEN")
            if not client_id or not access_token:
                raise ValueError("DHAN_CLIENT_ID or DHAN_ACCESS_TOKEN not set in environment.")
            dhan = dhanhq(client_id, access_token)
            return dhan.get_positions()
        except Exception as e:
            import sys
            print(f"Error: {e}", file=sys.stderr)
            exit(0)