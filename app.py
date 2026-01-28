import requests
import json
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, session, jsonify, redirect, url_for

app = Flask(__name__)
# ใช้ Secret Key สำหรับจัดการ Session (เปลี่ยนได้ตามต้องการ)
app.secret_key = 'shinobi_ultra_key_2026'

# --- CONFIG ---
DB_FILE = 'database.json'
# Webhook สำหรับแจ้งเตือนการเข้าใช้งานผ่าน Discord
WEBHOOK_URL = 'https://ptb.discord.com/api/webhooks/1465811458200834209/pu_ZLiGP6nwCjcSGDv5PCnmQbrwcmy8-HOfJc768W-9sDfu0qe_2tIQGMVEHVsbFp1SS'

def load_db():
    """โหลดข้อมูลจากฐานข้อมูล JSON"""
    if not os.path.exists(DB_FILE):
        # สร้างแอดมินเริ่มต้นถ้ายังไม่มีไฟล์
        init = {"shinobi2023": {"password": "shinobima", "role": "admin", "expire": "2099-12-31"}}
        save_db(init)
        return init
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"shinobi2023": {"password": "shinobima", "role": "admin", "expire": "2099-12-31"}}

def save_db(data):
    """บันทึกข้อมูลลงฐานข้อมูล JSON"""
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def send_to_webhook(username, status, ip):
    """ส่งการแจ้งเตือนไปที่ Discord"""
    if not WEBHOOK_URL: return
    # สีเขียวสำหรับสำเร็จ (65280), สีแดงสำหรับล้มเหลว (16711680)
    color = 65280 if status == "SUCCESS" else 16711680
    payload = {
        "embeds": [{
            "title": f"🔐 Login Monitoring: {status}",
            "color": color,
            "fields": [
                {"name": "👤 User", "value": f"`{username}`", "inline": True},
                {"name": "🌐 IP", "value": f"`{ip}`", "inline": True},
                {"name": "⏰ Time", "value": f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
            ],
            "footer": {"text": "X-VISION PRO SECURITY SYSTEM"}
        }]
    }
    try:
        requests.post(WEBHOOK_URL, json=payload, timeout=5)
    except:
        pass

@app.route('/')
def index():
    """หน้าแรก: ถ้าล็อกอินแล้วไป Dashboard ถ้ายังไป Login"""
    return redirect(url_for('dashboard')) if 'user' in session else render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    """ระบบตรวจสอบการล็อกอิน"""
    data = request.get_json()
    u, p = data.get('u'), data.get('p')
    db = load_db()
    
    # ดึง IP Address (รองรับกรณีรันผ่าน Proxy)
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # ตรวจสอบชื่อผู้ใช้และรหัสผ่าน
    if u in db and str(db[u]['password']) == str(p):
        # ตรวจสอบวันหมดอายุ
        exp_date = datetime.strptime(db[u]['expire'], '%Y-%m-%d')
        if datetime.now() > exp_date:
            send_to_webhook(u, "EXPIRED", user_ip)
            return jsonify({"status": "err", "m": "Account Expired (รหัสหมดอายุ)"}), 403
            
        # สร้าง Session
        session['user'] = u
        session['role'] = db[u]['role']
        
        send_to_webhook(u, "SUCCESS", user_ip)
        return jsonify({"status": "ok"})
    
    # กรณีล็อกอินไม่สำเร็จ
    send_to_webhook(u, "FAILED", user_ip)
    return jsonify({"status": "err", "m": "Access Denied (รหัสไม่ถูกต้อง)"}), 401

@app.route('/dashboard')
def dashboard():
    """หน้า Dashboard หลัก"""
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', role=session['role'], user=session['user'])

@app.route('/api/search', methods=['POST'])
def api_search():
    """ระบบค้นหาข้อมูลผ่าน API ต่างๆ"""
    if 'user' not in session:
        return jsonify({"status": "err"}), 403
        
    req_data = request.get_json()
    mode, value = req_data.get('m'), req_data.get('v')
    
    # รายการ API ปลายทาง
    endpoints = {
        "dopa": f"http://85.203.4.103:6868/api/v1/whoshop-ssf?pid={value}&api_key=TRUE-AFYX83CWIS8H",
        "nhso": f"http://85.203.4.103:6969/api/v1/whoshop?pid={value}&api_key=NHSO-FN2P7BQ46UH6",
        "trans": f"https://slumzick.xyz/api12.php?token=Kill221&value={value}",
        "true": f"https://apitu.psnw.xyz/index.php?type=phone&mode=sff&value={value}"
    }
    
    try:
        response = requests.get(endpoints.get(mode), timeout=15)
        return jsonify({"status": "ok", "data": response.json()})
    except Exception as e:
        return jsonify({"status": "err", "m": "Connection Error"}), 500

@app.route('/admin/action', methods=['POST'])
def admin_action():
    """ส่วนจัดการของแอดมิน (เพิ่ม/ลบ ยูสเซอร์)"""
    if session.get('role') != 'admin':
        return jsonify({"status": "denied"}), 403
        
    req = request.get_json()
    act, db = req.get('act'), load_db()
    
    if act == 'add':
        u, p, d = req['u'], req['p'], int(req['d'])
        # คำนวณวันหมดอายุจากจำนวนวันที่ระบุ
        db[u] = {
            "password": p, 
            "role": "user", 
            "expire": (datetime.now() + timedelta(days=d)).strftime('%Y-%m-%d')
        }
        save_db(db)
    elif act == 'del' and req['u'] != 'shinobi2023':
        db.pop(req['u'], None)
        save_db(db)
    elif act == 'list':
        return jsonify({"status": "ok", "db": db})
        
    return jsonify({"status": "ok", "db": db})

@app.route('/logout')
def logout():
    """ล้าง Session และออกจากระบบ"""
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    # รันบน Port 10000 ตามที่คุณกำหนด
    app.run(debug=True, host='0.0.0.0', port=10000)
