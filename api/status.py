from http.server import BaseHTTPRequestHandler
import json
import os
import requests

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):

        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }

        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/colabs?select=*",
            headers=headers
        )

        rows = response.json()

        colabs = {}
        for row in rows:
            colabs[row["colab_id"]] = {
                "status": "online",
                "busy_workers": 0,
                "ram": row["ram"],
                "slots": row["slots"]
            }

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        self.wfile.write(json.dumps({
            "colabs": colabs,
            "bots": {}
        }).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
