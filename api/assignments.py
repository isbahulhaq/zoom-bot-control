from http.server import BaseHTTPRequestHandler
import json
import time

assignments = {}
colabs = {}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Extract colab_id from path
        path = self.path
        colab_id = path.split('/')[-1]
        
        pending = []
        if colab_id in assignments:
            pending = assignments[colab_id]
            assignments[colab_id] = []  # Clear after sending
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {'assignments': pending}
        self.wfile.write(json.dumps(response).encode())
        return
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        return