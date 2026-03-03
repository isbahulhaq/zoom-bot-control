from http.server import BaseHTTPRequestHandler
import json
import time

# Global storage (Note: Vercel serverless mein ye reset ho sakta hai)
colabs = {}

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode())
        
        colab_id = data.get('colab_id')
        colabs[colab_id] = {
            'status': 'online',
            'last_seen': time.time(),
            'busy_workers': 0,
            'total_workers': data.get('total_workers', 10),
            'ram': data.get('ram', 'N/A')
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {'status': 'registered', 'colab_id': colab_id}
        self.wfile.write(json.dumps(response).encode())
        return
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        return