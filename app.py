from flask import Flask, render_template, request, redirect, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from functools import wraps

app = Flask(__name__)
app.secret_key = "hospital_secret_2026"

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["hospitalDB"]

patients     = db["patients"]
doctors      = db["doctors"]
appointments = db["appointments"]
bills        = db["bills"]
users        = db["users"]

# Reset aur naya admin banao
users.delete_many({})
users.insert_one({"username": "admin", "password": "admin123"})

# Auth Guard
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            flash("Please login first.", "warning")
            return redirect('/')
        return f(*args, **kwargs)
    return wrapper


# ══════════════════════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════════════════════

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect('/dashboard')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.find_one({"username": username, "password": password})
        if user:
            session['user'] = username
            return redirect('/dashboard')
        flash("Invalid username or password", "danger")
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ══════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════

@app.route('/dashboard')
@login_required
def dashboard():
    stats = {
        "patients"     : patients.count_documents({}),
        "doctors"      : doctors.count_documents({}),
        "appointments" : appointments.count_documents({}),
        "unpaid_bills" : bills.count_documents({"status": "Unpaid"})
    }
    recent_patients = list(patients.find().sort("_id", -1).limit(5))
    return render_template('dashboard.html', stats=stats, recent=recent_patients)


# ══════════════════════════════════════════════════════════
#  PATIENTS
# ══════════════════════════════════════════════════════════

@app.route('/patients')
@login_required
def view_patients():
    q = request.args.get('q', '')
    if q:
        all_p = list(patients.find({"name": {"$regex": q, "$options": "i"}}))
    else:
        all_p = list(patients.find())
    return render_template('patients.html', patients=all_p, q=q)


@app.route('/patients/add', methods=['GET', 'POST'])
@login_required
def add_patient():
    if request.method == 'POST':
        patients.insert_one({
            "name"   : request.form['name'],
            "age"    : request.form['age'],
            "gender" : request.form['gender'],
            "disease": request.form['disease'],
            "phone"  : request.form['phone'],
            "blood"  : request.form['blood']
        })
        flash("Patient added successfully!", "success")
        return redirect('/patients')
    return render_template('add_patient.html')


@app.route('/patients/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit_patient(id):
    patient = patients.find_one({"_id": ObjectId(id)})
    if request.method == 'POST':
        patients.update_one({"_id": ObjectId(id)}, {"$set": {
            "name"   : request.form['name'],
            "age"    : request.form['age'],
            "gender" : request.form['gender'],
            "disease": request.form['disease'],
            "phone"  : request.form['phone'],
            "blood"  : request.form['blood']
        }})
        flash("Patient updated!", "success")
        return redirect('/patients')
    return render_template('edit_patient.html', patient=patient)


@app.route('/patients/delete/<id>')
@login_required
def delete_patient(id):
    patients.delete_one({"_id": ObjectId(id)})
    flash("Patient deleted.", "info")
    return redirect('/patients')


# ══════════════════════════════════════════════════════════
#  DOCTORS
# ══════════════════════════════════════════════════════════

@app.route('/doctors')
@login_required
def view_doctors():
    all_d = list(doctors.find())
    return render_template('doctors.html', doctors=all_d)


@app.route('/doctors/add', methods=['GET', 'POST'])
@login_required
def add_doctor():
    if request.method == 'POST':
        doctors.insert_one({
            "name"          : request.form['name'],
            "specialization": request.form['specialization'],
            "phone"         : request.form['phone'],
            "schedule"      : request.form['schedule'],
            "fees"          : request.form['fees']
        })
        flash("Doctor added!", "success")
        return redirect('/doctors')
    return render_template('add_doctor.html')


@app.route('/doctors/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit_doctor(id):
    doctor = doctors.find_one({"_id": ObjectId(id)})
    if request.method == 'POST':
        doctors.update_one({"_id": ObjectId(id)}, {"$set": {
            "name"          : request.form['name'],
            "specialization": request.form['specialization'],
            "phone"         : request.form['phone'],
            "schedule"      : request.form['schedule'],
            "fees"          : request.form['fees']
        }})
        flash("Doctor updated!", "success")
        return redirect('/doctors')
    return render_template('edit_doctor.html', doctor=doctor)


@app.route('/doctors/delete/<id>')
@login_required
def delete_doctor(id):
    doctors.delete_one({"_id": ObjectId(id)})
    flash("Doctor deleted.", "info")
    return redirect('/doctors')


# ══════════════════════════════════════════════════════════
#  APPOINTMENTS
# ══════════════════════════════════════════════════════════

@app.route('/appointments')
@login_required
def view_appointments():
    all_a = list(appointments.find().sort("date", 1))
    return render_template('appointments.html', appointments=all_a)


@app.route('/appointments/add', methods=['GET', 'POST'])
@login_required
def book_appointment():
    all_p = list(patients.find())
    all_d = list(doctors.find())
    if request.method == 'POST':
        appointments.insert_one({
            "patient_name": request.form['patient_name'],
            "doctor_name" : request.form['doctor_name'],
            "date"        : request.form['date'],
            "time"        : request.form['time'],
            "status"      : "Pending"
        })
        flash("Appointment booked!", "success")
        return redirect('/appointments')
    return render_template('book_appointment.html', patients=all_p, doctors=all_d)


@app.route('/appointments/status/<id>/<status>')
@login_required
def update_appt_status(id, status):
    appointments.update_one({"_id": ObjectId(id)}, {"$set": {"status": status}})
    flash(f"Status updated to {status}", "success")
    return redirect('/appointments')


@app.route('/appointments/delete/<id>')
@login_required
def delete_appointment(id):
    appointments.delete_one({"_id": ObjectId(id)})
    flash("Appointment removed.", "info")
    return redirect('/appointments')


# ══════════════════════════════════════════════════════════
#  BILLING
# ══════════════════════════════════════════════════════════

@app.route('/bills')
@login_required
def view_bills():
    all_b = list(bills.find())
    return render_template('bills.html', bills=all_b)


@app.route('/bills/add', methods=['GET', 'POST'])
@login_required
def generate_bill():
    all_p = list(patients.find())
    if request.method == 'POST':
        doc   = float(request.form.get('doctor_fees', 0))
        med   = float(request.form.get('medicine', 0))
        lab   = float(request.form.get('lab', 0))
        room  = float(request.form.get('room', 0))
        total = doc + med + lab + room
        bills.insert_one({
            "patient_name": request.form['patient_name'],
            "doctor_fees" : doc,
            "medicine"    : med,
            "lab"         : lab,
            "room"        : room,
            "total"       : total,
            "status"      : request.form['status']
        })
        flash("Bill generated!", "success")
        return redirect('/bills')
    return render_template('generate_bill.html', patients=all_p)


@app.route('/bills/pay/<id>')
@login_required
def mark_paid(id):
    bills.update_one({"_id": ObjectId(id)}, {"$set": {"status": "Paid"}})
    flash("Bill marked as Paid!", "success")
    return redirect('/bills')


@app.route('/bills/delete/<id>')
@login_required
def delete_bill(id):
    bills.delete_one({"_id": ObjectId(id)})
    flash("Bill deleted.", "info")
    return redirect('/bills')


# ══════════════════════════════════════════════════════════
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
    app.run(debug=True, port=5001)
