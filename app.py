from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# ตั้งค่า API Endpoints
API_CONFIG = {
    "logistics": "https://slumzick.xyz/api12.php", # API ตัวใหม่ที่คุณส่งมา
    "true": "https://apitu.psnw.xyz/index.php",
    "dopa": "http://85.203.4.103:6868/api/v1/whoshop-ssf"
}

@app.route('/')
def index():
    # ส่งตัวแปร user และ role ไปที่หน้าเว็บ
    return render_template('index.html', user="ADMIN_ROOT", role="admin")

@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    mode = data.get('m')
    val = data.get('v')
    
    try:
        if mode == 'trans': # โหมดการขนส่ง (API ตัวใหม่)
            params = {"token": "Kill221", "value": val}
            r = requests.get(API_CONFIG['logistics'], params=params, timeout=10)
            return jsonify(r.json())
        
        elif mode == 'true':
            params = {"type": "phone", "value": val, "mode": "sff"}
            r = requests.get(API_CONFIG['true'], params=params, timeout=10)
            return jsonify(r.json())
            
        # กรณีโหมดอื่นๆ (DOPA/NHSO) ให้ใส่ Logic ตามไฟล์ .py ของคุณ
        return jsonify({"status": "error", "message": "Mode not implemented"})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
