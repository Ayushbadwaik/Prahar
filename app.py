import datetime
import io
import requests
from flask import Flask, render_template, request, jsonify, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "prahar_secret"

login_manager = LoginManager(app)

ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "Ayush"

class User(UserMixin):
    def __init__(self, uid):
        self.id = uid

@login_manager.user_loader
def load_user(uid):
    if uid == ADMIN_EMAIL:
        return User(uid)
    return None

TELEGRAM_TOKEN = "YOUR_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

def send_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
    except Exception as e:
        print("Telegram error:", e)

available_networks = []
attack_log = []
attack_status = "Normal"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    if request.form["email"] == ADMIN_EMAIL and request.form["password"] == ADMIN_PASSWORD:
        login_user(User(ADMIN_EMAIL))
        return {"status": "success"}
    return {"status": "error"}

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return {"status": "logout"}

@app.route("/api/networks", methods=["GET","POST"])
def networks():
    global available_networks
    if request.method == "POST":
        available_networks = request.json.get("networks", [])
        return {"ok": True}
    return jsonify(available_networks)

@app.route("/api/detect", methods=["POST"])
def detect():
    global attack_status, attack_log

    data = request.json or {}

    # Only detect if frames high
    if data.get("frames",0) < 300:
        return {"ignored": True}

    entry = {
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "type": data.get("type"),
        "victim_ssid": data.get("victim_ssid","-"),
        "victim_ip": data.get("victim_ip","-"),
        "victim_bssid": data.get("victim_bssid","-"),
        "attacker_ip": data.get("attacker_ip","-"),
        "attacker_bssid": data.get("attacker_bssid","-"),
        "frames": data.get("frames")
    }

    attack_log.append(entry)
    attack_status = entry["type"]

    send_telegram(
        f"⚠ {entry['type']}\nVictim: {entry['victim_ssid']} ({entry['victim_ip']})\nAttacker: {entry['attacker_ip']}"
    )

    return {"detected": True}

@app.route("/api/status")
def status():
    return {"status": attack_status}

@app.route("/api/logs")
def logs():
    if attack_status == "Normal":
        return []
    return attack_log

@app.route("/api/graph")
def graph():
    return {
        "time":[x["time"] for x in attack_log],
        "frames":[x["frames"] for x in attack_log]
    }

@app.route("/download")
@login_required
def download():
    if not attack_log:
        return {"error":"No attacks recorded"}

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.setFont("Helvetica",9)

    y = 800
    pdf.drawString(50,y,"PRAHAR Attack Report")
    y -= 20

    for log in attack_log:
        line = f"{log['time']} | {log['type']} | Victim {log['victim_ssid']} | Attacker {log['attacker_ip']}"
        pdf.drawString(50,y,line)
        y -= 15
        if y < 40:
            pdf.showPage()
            pdf.setFont("Helvetica",9)
            y = 800

    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="report.pdf")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
