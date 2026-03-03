from http.server import BaseHTTPRequestHandler
import json
import time

colabs = {}
assignments = {}
bot_counter = 0

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        global bot_counter
        
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode())
        
        meeting_id = data.get('meeting_id')
        passcode = data.get('passcode', '')
        bot_count = int(data.get('bot_count', 10))
        duration = int(data.get('duration', 60))
        
        # Find available colabs
        available = [c for c in colabs.keys() if colabs[c]['busy_workers'] < 10]
        
        if not available:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'No colabs available'}).encode())
            return
        
        # Simple distribution
        assignments_list = []
        per_colab = bot_count // len(available)
        remainder = bot_count % len(available)
        
        for i, colab_id in enumerate(available):
            count = per_colab + (1 if i < remainder else 0)
            if colab_id not in assignments:
                assignments[colab_id] = []
                
            for j in range(count):
                bot_counter += 1
                bot_id = f"bot_{bot_counter}"
                
                assignments[colab_id].append({
                    'bot_id': bot_id,
                    'meeting_id': meeting_id,
                    'passcode': passcode,
                    'duration': duration,
                    'assigned_at': time.time()
                })
                
                colabs[colab_id]['busy_workers'] = colabs[colab_id].get('busy_workers', 0) + 1
                colabs[colab_id]['status'] = 'busy'
                assignments_list.append(bot_id)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            'status': 'launched',
            'bot_count': len(assignments_list),
            'bots': assignments_list
        }
        self.wfile.write(json.dumps(response).encode())
        return
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        return