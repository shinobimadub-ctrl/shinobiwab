from flask import Flask, render_template, request, jsonify, redirect
import requests, jwt, datetime, csv, io

app = Flask(__name__)
SECRET = "XVISION_JWT_KEY"

API = {
    "trans": "https://slumzick.xyz/api12.php",
    "true": "https://apitu.psnw.xyz/index.php",
    "dopa": "http://85.203.4.103:6868/api/v1/whoshop-ssf"
}

USERS = {"admin":"1234"}

# ---------- JWT ----------
def create_token(user):
    return jwt.encode({
        "user": user,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=6)
    }, SECRET, algorithm="HS256")

def verify(req):
    token = req.headers.get("Authorization")
    if not token: return None
    try:
        return jwt.decode(token, SECRET, algorithms=["HS256"])
    except:
        return None

# ---------- ROUTES ----------
@app.route("/")
def login_page():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    u = request.form.get("username")
    p = request.form.get("password")
    if USERS.get(u) == p:
        return jsonify({"token": create_token(u)})
    return jsonify({"error":"login failed"}),401

@app.route("/dashboard")
def dash():
    return render_template("index.html")

@app.route("/api/search", methods=["POST"])
def search():
    if not verify(request):
        return jsonify({"error":"unauthorized"}),401

    data=request.json
    m=data["m"]
    v=data["v"]

    if m=="trans":
        r=requests.get(API["trans"],params={"token":"Kill221","value":v})
    elif m=="true":
        r=requests.get(API["true"],params={"type":"phone","value":v,"mode":"sff"})
    elif m=="dopa":
        r=requests.post(API["dopa"],json={"keyword":v})
    else:
        return jsonify({"error":"mode error"})

    return jsonify(r.json())

@app.route("/export/csv", methods=["POST"])
def export_csv():
    data=request.json
    output=io.StringIO()
    writer=csv.writer(output)
    writer.writerow(data[0].keys())
    for row in data:
        writer.writerow(row.values())
    return output.getvalue(),200,{"Content-Type":"text/csv"}
