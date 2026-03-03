from http.server import BaseHTTPRequestHandler
import json
import os
import requests
from datetime import datetime

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode())

        colab_id = data.get("colab_id")
        ram = data.get("ram", 12)
        slots = data.get("slots", 5)

        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }

        payload = {
            "colab_id": colab_id,
            "ram": ram,
            "slots": slots,
            "last_heartbeat": datetime.utcnow().isoformat()
        }

        requests.post(
            f"{SUPABASE_URL}/rest/v1/colabs",
            json=payload,
            headers=headers
        )

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        self.wfile.write(json.dumps({"status": "registered"}).encode())
