from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO, emit
import threading
import time
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Data store
connected_colabs = {}
active_bots = {}
bot_counter = 0

# HTML template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>🤖 Zoom Bot Control Center</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: auto;
        }
        .header {
            background: rgba(255,255,255,0.95);
            padding: 30px;
            border-radius: 20px;
            margin-bottom: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .header h1 {
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .stat-value {
            font-size: 3em;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        .control-panel {
            background: white;
            padding: 30px;
            border-radius: 20px;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
        }
        input, select {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1em;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            border-radius: 10px;
            font-size: 1.2em;
            cursor: pointer;
            width: 100%;
        }
        .colab-list, .bot-list {
            background: white;
            padding: 30px;
            border-radius: 20px;
            margin-bottom: 30px;
        }
        .colab-item {
            display: flex;
            justify-content: space-between;
            padding: 15px;
            border-bottom: 1px solid #f0f0f0;
        }
        .status-online {
            background: #d4edda;
            color: #155724;
            padding: 5px 10px;
            border-radius: 20px;
        }
        .status-busy {
            background: #fff3cd;
            color: #856404;
            padding: 5px 10px;
            border-radius: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Zoom Bot Command Center</h1>
            <p>Connected Colabs: <span id="total-colabs">0</span> | Active Bots: <span id="total-bots">0</span></p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value" id="available-slots">0</div>
                <div class="stat-label">Free Slots</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="total-ram">0</div>
                <div class="stat-label">Total RAM (GB)</div>
            </div>
        </div>

        <div class="control-panel">
            <h2>🚀 Launch New Bots</h2>
            <form id="botForm">
                <div class="form-group">
                    <label>Meeting ID *</label>
                    <input type="text" id="meetingId" required placeholder="Enter Zoom Meeting ID">
                </div>
                <div class="form-group">
                    <label>Passcode (Optional)</label>
                    <input type="text" id="passcode" placeholder="Enter meeting passcode">
                </div>
                <div class="form-group">
                    <label>Number of Bots *</label>
                    <input type="number" id="botCount" min="1" max="1000" value="10" required>
                </div>
                <div class="form-group">
                    <label>Duration (minutes)</label>
                    <input type="number" id="duration" min="1" value="60">
                </div>
                <div class="form-group">
                    <label>Distribution Strategy</label>
                    <select id="strategy">
                        <option value="balanced">Balanced (Equal distribution)</option>
                        <option value="sequential">Sequential (Fill one by one)</option>
                    </select>
                </div>
                <button type="submit">🚀 Launch Bots</button>
            </form>
        </div>

        <div class="colab-list">
            <h2>📡 Connected Colab Instances</h2>
            <div id="colabContainer">⏳ Waiting for connections...</div>
        </div>

        <div class="bot-list">
            <h2>🤖 Active Bots</h2>
            <div id="botContainer">🤖 No active bots</div>
        </div>
    </div>

    <script>
        const socket = io();
        
        socket.on('connect', function() {
            console.log('Connected to server');
        });

        socket.on('stats_update', function(data) {
            $('#total-colabs').text(data.total_colabs);
            $('#total-bots').text(data.total_bots);
            $('#available-slots').text(data.available_slots);
            $('#total-ram').text(data.total_ram);
            
            let colabHtml = '';
            if (data.colabs && Object.keys(data.colabs).length > 0) {
                for(let id in data.colabs) {
                    let colab = data.colabs[id];
                    let statusClass = colab.status === 'online' ? 'status-online' : 'status-busy';
                    let statusText = colab.status === 'online' ? '🟢 Online' : '🟡 Busy';
                    colabHtml += `
                        <div class="colab-item">
                            <span>💻 Instance: ${id.substring(0,8)}...</span>
                            <span>🤖 Bots: ${colab.busy_workers || 0}/10</span>
                            <span class="${statusClass}">${statusText}</span>
                        </div>
                    `;
                }
            } else {
                colabHtml = '<p style="text-align: center">⏳ No colabs connected yet</p>';
            }
            $('#colabContainer').html(colabHtml);
            
            let botHtml = '';
            if (data.bots && Object.keys(data.bots).length > 0) {
                for(let id in data.bots) {
                    let bot = data.bots[id];
                    botHtml += `
                        <div class="colab-item">
                            <span>🤖 Bot ${id.substring(0,6)}...</span>
                            <span>Meeting: ${bot.meeting_id}</span>
                            <span>${bot.status}</span>
                        </div>
                    `;
                }
            } else {
                botHtml = '<p style="text-align: center">🤖 No active bots</p>';
            }
            $('#botContainer').html(botHtml);
        });

        $('#botForm').submit(function(e) {
            e.preventDefault();
            
            const meetingId = $('#meetingId').val().trim();
            const passcode = $('#passcode').val().trim();
            const botCount = $('#botCount').val();
            const duration = $('#duration').val();
            const strategy = $('#strategy').val();

            socket.emit('launch_bots', {
                meeting_id: meetingId,
                passcode: passcode,
                bot_count: botCount,
                duration: duration,
                strategy: strategy
            });

            alert(`🚀 Launching ${botCount} bots for meeting ${meetingId}`);
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('register_colab')
def handle_register(data):
    colab_id = data.get('colab_id')
    connected_colabs[colab_id] = {
        'status': 'online',
        'last_seen': time.time(),
        'busy_workers': 0,
        'total_workers': data.get('total_workers', 10),
        'ram': data.get('ram', 'N/A'),
        'sid': request.sid
    }
    emit_stats()

@socketio.on('disconnect')
def handle_disconnect():
    # Remove colab on disconnect
    for colab_id in list(connected_colabs.keys()):
        if connected_colabs[colab_id].get('sid') == request.sid:
            del connected_colabs[colab_id]
    emit_stats()

def emit_stats():
    """Broadcast stats to all clients"""
    stats = {
        'total_colabs': len(connected_colabs),
        'total_bots': len(active_bots),
        'available_slots': sum(10 - c.get('busy_workers', 0) for c in connected_colabs.values()),
        'total_ram': len(connected_colabs) * 12,  # Approx 12GB per colab
        'colabs': connected_colabs,
        'bots': active_bots
    }
    socketio.emit('stats_update', stats)

@socketio.on('launch_bots')
def handle_launch_bots(data):
    """Launch bots command"""
    meeting_id = data.get('meeting_id')
    passcode = data.get('passcode', '')
    bot_count = int(data.get('bot_count', 10))
    duration = int(data.get('duration', 60))
    strategy = data.get('strategy', 'balanced')
    
    # Distribute bots to colabs
    distribute_bots(meeting_id, passcode, bot_count, duration, strategy)
    
    emit_stats()

def distribute_bots(meeting_id, passcode, total_bots, duration, strategy):
    """Distribute bots across colabs"""
    global bot_counter
    
    available_colabs = [c for c in connected_colabs.keys() 
                       if connected_colabs[c]['busy_workers'] < 10]
    
    if not available_colabs:
        print("No colabs available")
        socketio.emit('error', {'message': 'No colabs available'})
        return
    
    if strategy == 'balanced':
        # Equal distribution
        per_colab = total_bots // len(available_colabs)
        remainder = total_bots % len(available_colabs)
        
        for i, colab_id in enumerate(available_colabs):
            count = per_colab + (1 if i < remainder else 0)
            if count > 0:
                assign_bots_to_colab(colab_id, count, meeting_id, passcode, duration)
    
    elif strategy == 'sequential':
        # Fill one by one
        remaining = total_bots
        for colab_id in available_colabs:
            if remaining <= 0:
                break
            slots = 10 - connected_colabs[colab_id]['busy_workers']
            assign = min(slots, remaining)
            if assign > 0:
                assign_bots_to_colab(colab_id, assign, meeting_id, passcode, duration)
                remaining -= assign

def assign_bots_to_colab(colab_id, count, meeting_id, passcode, duration):
    """Send bot assignment to specific colab"""
    global bot_counter
    
    for i in range(count):
        bot_counter += 1
        bot_id = f"bot_{bot_counter}"
        
        # Send to colab via socket
        socketio.emit('assign_bot', {
            'bot_id': bot_id,
            'meeting_id': meeting_id,
            'passcode': passcode,
            'duration': duration
        }, room=colab_id)
        
        # Track bot
        active_bots[bot_id] = {
            'colab_id': colab_id,
            'meeting_id': meeting_id,
            'status': 'launching',
            'started_at': datetime.now().isoformat()
        }
        
        # Update colab busy count
        connected_colabs[colab_id]['busy_workers'] = connected_colabs[colab_id].get('busy_workers', 0) + 1
        connected_colabs[colab_id]['status'] = 'busy'

@socketio.on('bot_status')
def handle_bot_status(data):
    """Update bot status from colab"""
    bot_id = data.get('bot_id')
    status = data.get('status')
    
    if bot_id in active_bots:
        active_bots[bot_id]['status'] = status
    
    emit_stats()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)