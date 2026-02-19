import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ================= DATABASE CONFIG =================
database_url = os.environ.get("DATABASE_URL")

if database_url:
    database_url = database_url.replace("postgres://", "postgresql://")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url if database_url else "sqlite:///rfid.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ================= MODELS =================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default="user")
    approved = db.Column(db.Boolean, default=False)
    balance = db.Column(db.Float, default=2000)


class VehicleLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    rfid_type = db.Column(db.String(50))
    vehicle_type = db.Column(db.String(50))
    plate_number = db.Column(db.String(50))
    driver = db.Column(db.String(100))
    department = db.Column(db.String(100))
    travel_date = db.Column(db.String(20))
    from_location = db.Column(db.String(100))
    to_location = db.Column(db.String(100))
    rfid_location = db.Column(db.String(100))
    amount = db.Column(db.Float)
    remaining_balance = db.Column(db.Float)


# ================= CREATE DATABASE =================
with app.app_context():
    db.create_all()

    if not User.query.filter_by(email="admin@gmail.com").first():
        admin = User(
            email="admin@gmail.com",
            password="admin123",
            role="admin",
            approved=True,
            balance=0
        )
        db.session.add(admin)
        db.session.commit()


# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email, password=password).first()

        if user:
            if not user.approved:
                flash("Account pending admin approval.")
                return redirect(url_for("login"))

            session["user_id"] = user.id
            session["role"] = user.role
            return redirect(url_for("dashboard"))

        flash("Invalid login.")

    return render_template("login.html")


# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if User.query.filter_by(email=email).first():
            flash("Email already exists.")
            return redirect(url_for("register"))

        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash("Registered! Wait for admin approval.")
        return redirect(url_for("login"))

    return render_template("register.html")


# ================= DASHBOARD =================
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))
    # ================= ADMIN =================
    if session["role"] == "admin":

        logs_query = VehicleLog.query

        # FILTERS (ADMIN ONLY)
        search = request.args.get("search")
        rfid_filter = request.args.get("rfid")
        vehicle_filter = request.args.get("vehicle_filter")

        if search:
            logs_query = logs_query.filter(
                VehicleLog.plate_number.ilike(f"%{search}%")
            )

        if rfid_filter and rfid_filter != "All":
            logs_query = logs_query.filter(
                VehicleLog.rfid_type == rfid_filter
            )

        if vehicle_filter and vehicle_filter != "All":
            logs_query = logs_query.filter(
                VehicleLog.vehicle_type == vehicle_filter
            )

        logs = logs_query.all()

        total = sum(log.amount for log in logs)

        users = User.query.filter_by(approved=False).all()
        all_users = User.query.filter_by(role="user").all()

        return render_template(
            "admin_dashboard.html",
            logs=logs,
            total=total,
            users=users,
            all_users=all_users
        )

    # ================= USER =================
    user = User.query.get(session["user_id"])

    if request.method == "POST":

        amount = float(request.form.get("amount"))

        if user.balance < amount:
            flash("Not enough RFID balance!")
            return redirect(url_for("dashboard"))

        user.balance -= amount

        new_log = VehicleLog(
            user_id=user.id,
            rfid_type=request.form.get("rfid_type"),
            vehicle_type=request.form.get("vehicle_type"),
            plate_number=request.form.get("plate_number"),
            driver=request.form.get("driver"),
            department=request.form.get("department"),
            travel_date=request.form.get("travel_date"),
            from_location=request.form.get("from_location"),
            to_location=request.form.get("to_location"),
            rfid_location=request.form.get("rfid_location"),
            amount=amount,
            remaining_balance=user.balance
        )

        db.session.add(new_log)
        db.session.commit()

        flash("Transaction saved successfully!")
        return redirect(url_for("dashboard"))

    logs = VehicleLog.query.filter_by(user_id=user.id).all()

    return render_template(
        "user_dashboard.html",
        logs=logs,
        balance=user.balance
    )



# ================= EDIT =================
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    log = VehicleLog.query.get_or_404(id)

    if request.method == "POST":
        log.travel_date = request.form.get("travel_date")
        log.department = request.form.get("department")
        log.rfid_type = request.form.get("rfid_type")
        log.vehicle_type = request.form.get("vehicle_type")
        log.plate_number = request.form.get("plate_number")
        log.driver = request.form.get("driver")
        log.from_location = request.form.get("from_location")
        log.to_location = request.form.get("to_location")
        log.rfid_location = request.form.get("rfid_location")
        log.amount = float(request.form.get("amount"))

        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("edit.html", log=log)


# ================= APPROVE =================
@app.route("/approve/<int:id>", methods=["POST"])
def approve(id):
    if session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    user = User.query.get_or_404(id)
    user.approved = True
    db.session.commit()
    return redirect(url_for("dashboard"))


# ================= REJECT =================
@app.route("/reject/<int:id>", methods=["POST"])
def reject(id):
    if session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for("dashboard"))


# ================= RELOAD =================
@app.route("/reload/<int:id>", methods=["POST"])
def reload_balance(id):
    if session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    user = User.query.get_or_404(id)
    amount = float(request.form.get("amount"))

    user.balance += amount
    db.session.commit()
    return redirect(url_for("dashboard"))


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


if __name__ == "__main__":
    app.run(debug=True, port=5500)
