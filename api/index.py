from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>🤖 Zoom Bot Control Center</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
            <style>
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
                    background: white;
                    padding: 30px;
                    border-radius: 20px;
                    margin-bottom: 30px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
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
                    <h1>🤖 Zoom Bot Command Center (Vercel)</h1>
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
                let colabs = {};
                let bots = {};

                function updateStats() {
                    $('#total-colabs').text(Object.keys(colabs).length);
                    $('#total-bots').text(Object.keys(bots).length);
                    
                    let availableSlots = 0;
                    for(let id in colabs) {
                        availableSlots += (10 - (colabs[id].busy_workers || 0));
                    }
                    $('#available-slots').text(availableSlots);
                    $('#total-ram').text(Object.keys(colabs).length * 12);
                    
                    let colabHtml = '';
                    for(let id in colabs) {
                        let colab = colabs[id];
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
                    $('#colabContainer').html(colabHtml || '<p>No colabs connected</p>');
                    
                    let botHtml = '';
                    for(let id in bots) {
                        let bot = bots[id];
                        botHtml += `
                            <div class="colab-item">
                                <span>🤖 Bot ${id.substring(0,6)}...</span>
                                <span>Meeting: ${bot.meeting_id}</span>
                                <span>${bot.status}</span>
                            </div>
                        `;
                    }
                    $('#botContainer').html(botHtml || '<p>No active bots</p>');
                }

                function refreshStats() {
                    $.get('/api/status', function(data) {
                        colabs = data.colabs || {};
                        bots = data.bots || {};
                        updateStats();
                    });
                }

                $('#botForm').submit(function(e) {
                    e.preventDefault();
                    
                    $.post('/api/launch', {
                        meeting_id: $('#meetingId').val(),
                        passcode: $('#passcode').val(),
                        bot_count: $('#botCount').val(),
                        duration: $('#duration').val(),
                        strategy: $('#strategy').val()
                    }, function(data) {
                        alert(`🚀 Launching ${data.bot_count} bots`);
                    });
                });

                setInterval(refreshStats, 2000);
                refreshStats();
            </script>
        </body>
        </html>
        '''
        
        self.wfile.write(html.encode())
        return