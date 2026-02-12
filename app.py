import os
from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# SECRET KEY (safe for demo)
app.secret_key = os.environ.get("SECRET_KEY", "schoolprojectkey")

# DATABASE CONFIG
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    "DATABASE_URL",
    "sqlite:///vehicles.db"
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ================= DATABASE MODEL =================

class VehicleLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rfid_type = db.Column(db.String(50))
    vehicle_type = db.Column(db.String(100))
    plate_number = db.Column(db.String(50))
    driver = db.Column(db.String(100))
    department = db.Column(db.String(100))
    travel_date = db.Column(db.String(50))
    from_location = db.Column(db.String(100))
    to_location = db.Column(db.String(100))
    rfid_location = db.Column(db.String(100))
    amount = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ================= LOGIN =================

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["role"] = "admin"
            return redirect(url_for("dashboard"))

        elif username == "user" and password == "user123":
            session["role"] = "user"
            return redirect(url_for("dashboard"))

        flash("Invalid Credentials")

    return render_template("login.html")

# ================= FORGOT PASSWORD =================

@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    message = None
    if request.method == "POST":
        username = request.form["username"]

        if username == "admin":
            message = "Admin Password: admin123"
        elif username == "user":
            message = "User Password: user123"
        else:
            message = "Username not found"

    return render_template("forgot_password.html", message=message)

# ================= DASHBOARD =================

@app.route("/dashboard")
def dashboard():
    if "role" not in session:
        return redirect(url_for("login"))

    if session["role"] == "admin":

        filter_type = request.args.get("filter")

        if filter_type and filter_type != "All":
            logs = VehicleLog.query.filter_by(
                rfid_type=filter_type
            ).order_by(VehicleLog.timestamp.desc()).all()
        else:
            logs = VehicleLog.query.order_by(
                VehicleLog.timestamp.desc()
            ).all()

        total = sum(log.amount for log in logs)

        return render_template(
            "admin_dashboard.html",
            logs=logs,
            total=total,
            selected_filter=filter_type
        )

    return render_template("user_dashboard.html")

# ================= RECORD =================

@app.route("/record", methods=["POST"])
def record():
    if "role" not in session:
        return redirect(url_for("login"))

    new_log = VehicleLog(
        rfid_type=request.form["rfid_type"],
        vehicle_type=request.form["vehicle_type"],
        plate_number=request.form["plate_number"],
        driver=request.form["driver"],
        department=request.form["department"],
        travel_date=request.form["travel_date"],
        from_location=request.form["from_location"],
        to_location=request.form["to_location"],
        rfid_location=request.form["rfid_location"],
        amount=float(request.form["amount"])
    )

    db.session.add(new_log)
    db.session.commit()

    return redirect(url_for("dashboard"))

# ================= EDIT =================

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    log = VehicleLog.query.get_or_404(id)

    if request.method == "POST":
        log.rfid_type = request.form["rfid_type"]
        log.vehicle_type = request.form["vehicle_type"]
        log.plate_number = request.form["plate_number"]
        log.driver = request.form["driver"]
        log.department = request.form["department"]
        log.travel_date = request.form["travel_date"]
        log.from_location = request.form["from_location"]
        log.to_location = request.form["to_location"]
        log.rfid_location = request.form["rfid_location"]
        log.amount = float(request.form["amount"])

        db.session.commit()
        return redirect(url_for("dashboard"))

    return render_template("edit.html", log=log)

# ================= DELETE =================

@app.route("/delete/<int:id>")
def delete(id):
    if session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    log = VehicleLog.query.get_or_404(id)
    db.session.delete(log)
    db.session.commit()
    return redirect(url_for("dashboard"))

# ================= LOGOUT =================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ================= START APP =================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT", 5500))
    app.run(host="0.0.0.0", port=port)
