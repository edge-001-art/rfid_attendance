from flask import Flask, render_template, redirect, url_for, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import csv
import random
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rfid.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ------------------ MODEL ------------------
class RFIDScan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag_id = db.Column(db.String(100))
    student_name = db.Column(db.String(100))
    grade = db.Column(db.String(10))
    scan_time = db.Column(db.DateTime, default=datetime.utcnow)

# ------------------ LOAD STUDENTS ------------------
def load_students():
    students = {}
    file_path = os.path.join(os.getcwd(), "data", "students.csv")

    if os.path.exists(file_path):
        with open(file_path, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                students[row["tag_id"]] = {
                    "name": row["student_name"],
                    "grade": row["grade"]
                }

    return students

STUDENTS = load_students()

# ------------------ LOGIN ------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "1234":
            session["user"] = username
            return redirect(url_for("dashboard"))

    return render_template("login.html")

# ------------------ DASHBOARD ------------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")

# ------------------ LIVE DATA API ------------------
@app.route("/api/scans")
def api_scans():
    scans = RFIDScan.query.order_by(RFIDScan.scan_time.desc()).all()

    data = []
    for scan in scans:
        data.append({
            "student_name": scan.student_name,
            "tag_id": scan.tag_id,
            "grade": scan.grade,
            "scan_time": scan.scan_time.strftime("%Y-%m-%d %H:%M:%S")
        })

    return jsonify(data)

# ------------------ AUTO SIMULATE ------------------
@app.route("/auto_simulate")
def auto_simulate():
    if not STUDENTS:
        return jsonify({"status": "no students"})

    tag_id = random.choice(list(STUDENTS.keys()))
    student = STUDENTS[tag_id]

    new_scan = RFIDScan(
        tag_id=tag_id,
        student_name=student["name"],
        grade=student["grade"]
    )

    db.session.add(new_scan)
    db.session.commit()

    return jsonify({"status": "added"})

# ------------------ LOGOUT ------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ------------------ RUN ------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
if __name__ == "__main__":
    app.run()

