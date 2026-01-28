import requests
import json
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, session, jsonify, redirect, url_for

app = Flask(__name__)
app.secret_key = 'cyber_ultra_fixed_key_2026'

# --- CONFIG ---
DB_FILE = 'database.json'
WEBHOOK_URL = 'ใส่_URL_WEBHOOK_ของคูณตรงนี้' 

# ฟังก์ชันโหลดข้อมูลจากไฟล์ (ป้องกันรหัสหาย)
def load_db():
    if not os.path.exists(DB_FILE):
        # ถ้าไม่มีไฟล์ ให้สร้าง Admin เริ่มต้น
        init = {"admin": {"password": "1234", "role": "admin", "expire": "2099-12-31"}}
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(init, f, indent=4, ensure_ascii=False)
        return init
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"admin": {"password": "1234", "role": "admin", "expire": "2099-12-31"}}

# ฟังก์ชันเซฟข้อมูลลงไฟล์ทันที
def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def send_to_webhook(username, status, ip):
    if not WEBHOOK_URL or "ใส่_URL" in WEBHOOK_URL: return
    color = 65280 if status == "SUCCESS" else 16711680
    payload = {
        "embeds": [{
            "title": f"🔐 Login Monitoring: {status}",
            "color": color,
            "fields": [
                {"name": "👤 User", "value": f"`{username}`", "inline": True},
                {"name": "🌐 IP", "value": f"`{ip}`", "inline": True},
                {"name": "⏰ Time", "value": f"{datetime.now().strftime('%H:%M:%S')}"}
            ],
            "footer": {"text": "X-VISION SYSTEM LOG"}
        }]
    }
    try: requests.post(WEBHOOK_URL, json=payload, timeout=5)
    except: pass

@app.route('/')
def index():
    return redirect(url_for('dashboard')) if 'user' in session else render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    u, p = data.get('u'), data.get('p')
    db = load_db() # โหลดจากไฟล์ทุกครั้งที่มีคนล็อกอิน
    
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    if u in db and str(db[u]['password']) == str(p):
        exp = datetime.strptime(db[u]['expire'], '%Y-%m-%d')
        if datetime.now() > exp:
            send_to_webhook(u, "EXPIRED", user_ip)
            return jsonify({"status": "err", "m": "รหัสหมดอายุแล้ว"}), 403
        
        session['user'], session['role'] = u, db[u]['role']
        send_to_webhook(u, "SUCCESS", user_ip)
        return jsonify({"status": "ok"})
    
    send_to_webhook(u, "FAILED", user_ip)
    return jsonify({"status": "err", "m": "รหัสผ่านไม่ถูกต้อง"}), 401

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('dashboard.html', role=session['role'], user=session['user'])

@app.route('/api/search', methods=['POST'])
def api_search():
    if 'user' not in session: return jsonify({"status": "err"}), 403
    p = request.get_json()
    m, v = p.get('m'), p.get('v')
    conf = {
        "dopa": f"http://85.203.4.103:6868/api/v1/whoshop-ssf?pid={v}&api_key=TRUE-AFYX83CWIS8H",
        "nhso": f"http://85.203.4.103:6969/api/v1/whoshop?pid={v}&api_key=NHSO-FN2P7BQ46UH6",
        "trans": f"https://slumzick.xyz/api12.php?token=Kill221&value={v}",
        "true": f"https://apitu.psnw.xyz/index.php?type=phone&mode=sff&value={v}"
    }
    try:
        r = requests.get(conf[m], timeout=15).json()
        return jsonify({"status": "ok", "data": r})
    except: return jsonify({"status": "err"})

@app.route('/admin/action', methods=['POST'])
def admin_action():
    if session.get('role') != 'admin': return jsonify({"status": "denied"}), 403
    req = request.get_json()
    act = req.get('act')
    db = load_db()
    
    if act == 'add':
        u, p, d = req['u'], req['p'], int(req['d'])
        db[u] = {
            "password": p, 
            "role": "user", 
            "expire": (datetime.now() + timedelta(days=d)).strftime('%Y-%m-%d')
        }
        save_db(db) # เซฟลงไฟล์ทันที
    elif act == 'del':
        if req['u'] != 'admin': 
            db.pop(req['u'], None)
            save_db(db)
    
    return jsonify({"status": "ok", "db": db})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=10000)
