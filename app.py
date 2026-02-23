from flask import Flask, render_template, request, redirect, url_for, jsonify
import qrcode
import os
import random
import string
import base64
import sqlite3
import numpy as np
import cv2
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from face_attendance import scan_and_mark_attendance, recognize_from_frame_db, extract_face_roi

app = Flask(__name__)
DB_PATH = "database.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_face_registry():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS face_registry (
            roll TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            face_blob BLOB NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


init_face_registry()

# ======================================================
# LOGIN
# ======================================================
USER_ID = "tharunreddy@12"
PASSWORD = "REDDY"

remedial_attendance = []
students_list = [
    {"roll": "CS2024001", "name": "Sudheer", "parent": "9999999991"},
    {"roll": "CS2024002", "name": "Supreet Reddy", "parent": "9999999992"},
    {"roll": "CS2024003", "name": "Karthik", "parent": "9999999993"},
    {"roll": "CS2024004", "name": "Prasanth Reddy", "parent": "9999999994"},
    {"roll": "CS2024005", "name": "Tharun", "parent": "9999999995"},
]

# ======================================================
# SMART FOOD DATA
# ======================================================
food_menu = {
    "Pizza": 120,
    "Burger": 80,
    "Sandwich": 60,
    "Juice": 40,

    "Crispy Veg Double Patty + Fries (M)": 189,
    "Whopper Chicken (XL)": 209,
    "Korean Spicy Paneer Burgers": 399,
    "Korean Spicy Chicken Burgers": 399,
    "Crispy Chicken Burger": 99
}

time_slots = {
    "10:30 - 10:45": {"capacity": 5, "booked": 0},
    "12:30 - 12:45": {"capacity": 5, "booked": 0},
    "3:00 - 3:15": {"capacity": 5, "booked": 0}
}

orders = []
transactions = []

# =====================================================
# CAMPUS RESOURCE DATA
# =====================================================

# Blocks
blocks = [
    {"name": "Block A"},
    {"name": "Block B"}
]

# Classrooms
classrooms = [
    {"block": "Block A", "room": "A101", "capacity": 60},
    {"block": "Block A", "room": "A102", "capacity": 50},
    {"block": "Block B", "room": "B201", "capacity": 40}
]

# Faculty
faculty = [
    {"name": "Dr. Kumar"},
    {"name": "Dr. Reddy"},
    {"name": "Dr. Sharma"}
]

# Courses
# ================= SEMESTER DATA =================

# ================= SEMESTER DATA (8 SEMESTERS) =================

semester_data = {
    "1-1": [
        {"name": "Mathematics-I", "faculty": "Dr. Kumar", "students": 60},
        {"name": "Physics", "faculty": "Dr. Reddy", "students": 55}
    ],

    "1-2": [
        {"name": "Mathematics-II", "faculty": "Dr. K.S Reddy", "students": 58},
        {"name": "Chemistry", "faculty": "Dr. Priya", "students": 52}
    ],

    "2-1": [
        {"name": "Data Structures", "faculty": "Dr. Vikash", "students": 65},
        {"name": "Digital Logic", "faculty": "Dr. Mahesh", "students": 50}
    ],

    "2-2": [
        {"name": "OOP", "faculty": "Dr. Mohan", "students": 60},
        {"name": "Computer Organization", "faculty": "Dr. Vijay", "students": 48}
    ],

    "3-1": [
        {"name": "DBMS", "faculty": "Dr. Vinay", "students": 70},
        {"name": "Operating Systems", "faculty": "Dr. Reddy", "students": 60}
    ],

    "3-2": [
        {"name": "Software Engineering", "faculty": "Dr. Manu", "students": 62},
        {"name": "Computer Networks", "faculty": "Dr. Ajay", "students": 55}
    ],

    "4-1": [
        {"name": "Machine Learning", "faculty": "Dr. Himanth", "students": 68},
        {"name": "Cloud Computing", "faculty": "Dr. Satish", "students": 58}
    ],

    "4-2": [
        {"name": "Artificial Intelligence", "faculty": "Dr. Suresh", "students": 72},
        {"name": "Project Work", "faculty": "Dr. Surendra", "students": 65}
    ]
    
}
# ================== STORAGE ==================
makeup_classes = []          # Stores scheduled classes
remedial_attendance = []     # Stores remedial attendance

classrooms = [
    {"room_no": "A101", "type": "Classroom", "capacity": 60, "semester": "1-1"},
    {"room_no": "A102", "type": "Classroom", "capacity": 50, "semester": "1-2"},
    {"room_no": "A103", "type": "Classroom", "capacity": 40, "semester": "1-1"},
]



courses = [
    {"code": "CSE101", "name": "DSA", "semester": "1-1"},
    {"code": "CSE102", "name": "C++", "semester": "1-1"},
    {"code": "CSE103", "name": "Python", "semester": "1-2"},
]

faculty_list = [
    {"id": "F01", "name": "Dr. Kumar", "course": "DSA", "semester": "1-1"},
    {"id": "F02", "name": "Dr. Reddy", "course": "C++", "semester": "1-1"},
    {"id": "F03", "name": "Dr. Sharma", "course": "Python", "semester": "1-2"},
]

students_list = [

    # -------- Semester 1-1 --------
    {"roll": "CS001", "name": "Sudheer", "course": "DSA", "semester": "1-1"},
    {"roll": "CS002", "name": "Karthik", "course": "C++", "semester": "1-1"},
    {"roll": "CS003", "name": "Arshu", "course": "Python", "semester": "1-1"},

    # -------- Semester 1-2 --------
    {"roll": "CS004", "name": "Prasanth", "course": "DBMS", "semester": "1-2"},
    {"roll": "CS005", "name": "Himanth", "course": "Operating Systems", "semester": "1-2"},
    {"roll": "CS006", "name": "Varun", "course": "Java", "semester": "1-2"},

    # -------- Semester 2-1 --------
    {"roll": "CS007", "name": "Rahul", "course": "Computer Networks", "semester": "2-1"},
    {"roll": "CS008", "name": "Ajay", "course": "Python", "semester": "2-1"},
    {"roll": "CS009", "name": "Vamsi", "course": "DSA", "semester": "2-1"},

    # -------- Semester 2-2 --------
    {"roll": "CS010", "name": "Sandeep", "course": "DBMS", "semester": "2-2"},
    {"roll": "CS011", "name": "Chaitanya", "course": "C++", "semester": "2-2"},
    {"roll": "CS012", "name": "Rohith", "course": "Operating Systems", "semester": "2-2"},

    # -------- Semester 3-1 --------
    {"roll": "CS013", "name": "Kiran", "course": "Machine Learning", "semester": "3-1"},
    {"roll": "CS014", "name": "Teja", "course": "Artificial Intelligence", "semester": "3-1"},
    {"roll": "CS015", "name": "Harsha", "course": "Cloud Computing", "semester": "3-1"},

    # -------- Semester 3-2 --------
    {"roll": "CS016", "name": "Naveen", "course": "Cyber Security", "semester": "3-2"},
    {"roll": "CS017", "name": "Manoj", "course": "Big Data", "semester": "3-2"},
    {"roll": "CS018", "name": "Abhishek", "course": "DevOps", "semester": "3-2"},

    # -------- Semester 4-1 --------
    {"roll": "CS019", "name": "Tarun", "course": "Blockchain", "semester": "4-1"},
    {"roll": "CS020", "name": "Lokesh", "course": "IoT", "semester": "4-1"},
    {"roll": "CS021", "name": "Sai", "course": "Data Science", "semester": "4-1"},

    # -------- Semester 4-2 --------
    {"roll": "CS022", "name": "Deepak", "course": "Project Work", "semester": "4-2"},
    {"roll": "CS023", "name": "Praveen", "course": "Internship", "semester": "4-2"},
    {"roll": "CS024", "name": "Charan", "course": "Full Stack Development", "semester": "4-2"},
]

# Generate 6-digit remedial code
def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


# ======================================================
# LOGIN ROUTE
# ======================================================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["userid"] == USER_ID and request.form["password"] == PASSWORD:
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid Credentials")
    return render_template("login.html")

# ======================================================
# DASHBOARD
# ======================================================
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# ======================================================
# FOOD PAGE
# ======================================================
@app.route("/food")
def food():
    return render_template("food.html", menu=food_menu, time_slots=time_slots)

# ======================================================
# PLACE ORDER
# ======================================================
@app.route("/place_order", methods=["POST"])
def place_order():
    item = request.form["item"]
    quantity = int(request.form["quantity"])
    slot = request.form["slot"]

    if time_slots[slot]["booked"] + quantity > time_slots[slot]["capacity"]:
        return render_template("food.html",
                               menu=food_menu,
                               time_slots=time_slots,
                               error="❌ Slot Full! Choose another time.")

    total_price = food_menu[item] * quantity

    return render_template("payment.html",
                           item=item,
                           quantity=quantity,
                           slot=slot,
                           total_price=total_price)

# ======================================================
# GENERATE QR WITH DYNAMIC AMOUNT
# ======================================================
@app.route("/confirm_payment", methods=["POST"])
def confirm_payment():
    item = request.form["item"]
    quantity = int(request.form["quantity"])
    slot = request.form["slot"]

    total_price = food_menu[item] * quantity

    upi_id = "tharunreddy153-1@okaxis"
    name = "Tharun Reddy"

    upi_string = f"upi://pay?pa={upi_id}&pn={name}&am={total_price}&cu=INR"

    qr = qrcode.make(upi_string)

    if not os.path.exists("static"):
        os.makedirs("static")

    qr_path = "static/dynamic_qr.png"
    qr.save(qr_path)

    return render_template("qr_payment.html",
                           item=item,
                           quantity=quantity,
                           slot=slot,
                           total_price=total_price,
                           qr_image="dynamic_qr.png")

# ======================================================
# COMPLETE PAYMENT + STORE HISTORY
# ======================================================
@app.route("/complete_payment", methods=["POST"])
def complete_payment():
    item = request.form["item"]
    quantity = int(request.form["quantity"])
    slot = request.form["slot"]

    total_price = food_menu[item] * quantity

    time_slots[slot]["booked"] += quantity

    order_data = {
        "item": item,
        "quantity": quantity,
        "slot": slot,
        "amount": total_price
    }

    orders.append(order_data)
    transactions.append(order_data)

    return redirect(url_for("generate_invoice",
                            item=item,
                            quantity=quantity,
                            slot=slot,
                            amount=total_price))

# ======================================================
# GENERATE INVOICE PDF
# ======================================================
@app.route("/generate_invoice")
def generate_invoice():
    item = request.args.get("item")
    quantity = request.args.get("quantity")
    slot = request.args.get("slot")
    amount = request.args.get("amount")

    filename = "static/invoice.pdf"

    doc = SimpleDocTemplate(filename)
    elements = []

    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>Smart Campus Food Invoice</b>", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))

    data = [
        ["Item", item],
        ["Quantity", quantity],
        ["Slot", slot],
        ["Total Amount", f"₹{amount}"]
    ]

    table = Table(data, colWidths=[2*inch, 3*inch])
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
    ]))

    elements.append(table)

    doc.build(elements)

    return render_template("invoice_success.html",
                           invoice_file="invoice.pdf")

# ======================================================
# TRANSACTION HISTORY
# ======================================================
@app.route("/transactions")
def transactions_page():
    return render_template("transactions.html",
                           transactions=transactions)

# ======================================================
# FOOD ANALYTICS
# ======================================================
@app.route("/food_analytics")
def food_analytics():
    slot_demand = {}
    total_orders = 0

    for order in orders:
        slot = order["slot"]
        qty = order["quantity"]
        total_orders += qty
        slot_demand[slot] = slot_demand.get(slot, 0) + qty

    return render_template("food_analytics.html",
                           demand=slot_demand,
                           total_orders=total_orders)

# =====================================================
# CAMPUS RESOURCE HOME PAGE
# =====================================================

@app.route("/resource")
def resource():

    selected_sem = request.args.get("semester", "1-1")

    # Filter Data by Semester
    filtered_classrooms = [r for r in classrooms if r["semester"] == selected_sem]
    filtered_faculty = [f for f in faculty_list if f["semester"] == selected_sem]
    filtered_courses = [c for c in courses if c["semester"] == selected_sem]
    filtered_students = [s for s in students_list if s["semester"] == selected_sem]

    total_capacity = sum(r["capacity"] for r in filtered_classrooms)
    total_students = len(filtered_students)
    utilization = round((total_students / total_capacity) * 100, 2) if total_capacity else 0

    return render_template(
        "resource.html",
        semester=selected_sem,
        classrooms=filtered_classrooms,
        faculty=filtered_faculty,
        courses=filtered_courses,
        students=filtered_students,
        total_capacity=total_capacity,
        total_students=total_students,
        utilization=utilization
    )






makeup_classes = []

@app.route("/remedial", methods=["GET", "POST"])
def remedial():

    if request.method == "POST":
        subject = request.form["subject"]
        faculty = request.form["faculty"]
        date = request.form["date"]

        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        makeup_classes.append({
            "subject": subject,
            "faculty": faculty,
            "date": date,
            "code": code
        })

        return render_template(
            "remedial_success.html",
            code=code,
            subject=subject,
            faculty=faculty,
            date=date
        )

    return render_template("remedial.html")

@app.route("/student_remedial", methods=["GET", "POST"])
def student_remedial():

    message = ""

    if request.method == "POST":
        roll = request.form["roll"]
        entered_code = request.form["code"]

        valid_class = next(
            (c for c in makeup_classes if c["code"] == entered_code),
            None
        )

        if valid_class:
            remedial_attendance.append({
                "roll": roll,
                "subject": valid_class["subject"]
            })
            message = "Attendance Marked Successfully ✅"
        else:
            message = "Invalid Code ❌"

    return render_template("student_remedial.html", message=message)


@app.route("/view_remedial_attendance")
def view_remedial_attendance():
    return render_template("view_remedial_attendance.html", records=remedial_attendance)


def _normalize_name(name):
    return (name or "").strip().lower()


@app.route("/save_face_capture", methods=["POST"])
def save_face_capture():
    data = request.get_json(silent=True) or {}
    image_data = data.get("image", "")
    roll = (data.get("roll") or "").strip()

    if not image_data or not roll:
        return jsonify({"ok": False, "error": "Image and roll are required"}), 400

    student = next((s for s in students_list if s["roll"] == roll), None)
    if not student:
        return jsonify({"ok": False, "error": "Invalid roll"}), 400

    try:
        encoded_part = image_data.split(",", 1)[1] if "," in image_data else image_data
        raw = base64.b64decode(encoded_part)
        arr = np.frombuffer(raw, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception:
        return jsonify({"ok": False, "error": "Invalid image data"}), 400

    if frame is None:
        return jsonify({"ok": False, "error": "Unable to decode image"}), 400

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    face_roi = extract_face_roi(gray)
    if face_roi is None:
        return jsonify({"ok": False, "error": "No face detected in capture"}), 400

    ok, buffer = cv2.imencode(".png", face_roi)
    if not ok:
        return jsonify({"ok": False, "error": "Face encoding failed"}), 500

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO face_registry (roll, name, face_blob)
        VALUES (?, ?, ?)
        ON CONFLICT(roll) DO UPDATE SET
            name = excluded.name,
            face_blob = excluded.face_blob
        """,
        (student["roll"], student["name"], buffer.tobytes())
    )
    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "message": f"Face stored for {student['name']}",
        "roll": student["roll"],
        "name": student["name"]
    })


@app.route("/recognize_capture", methods=["POST"])
def recognize_capture():
    data = request.get_json(silent=True) or {}
    image_data = data.get("image", "")

    if not image_data:
        return jsonify({"ok": False, "error": "No image received"}), 400

    try:
        encoded_part = image_data.split(",", 1)[1] if "," in image_data else image_data
        raw = base64.b64decode(encoded_part)
        arr = np.frombuffer(raw, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception:
        return jsonify({"ok": False, "error": "Invalid image data"}), 400

    if frame is None:
        return jsonify({"ok": False, "error": "Unable to decode image"}), 400

    conn = get_db_connection()
    rows = conn.execute("SELECT roll, name, face_blob FROM face_registry").fetchall()
    conn.close()

    detected = recognize_from_frame_db(frame, rows)
    if not detected:
        return jsonify({"ok": True, "matched": False, "message": "No known student detected"})

    student = next((s for s in students_list if s["roll"] == detected["roll"]), None)
    if not student:
        return jsonify({"ok": True, "matched": False, "message": "Detected face not found in students list"})

    if not any(r.get("roll") == student["roll"] for r in remedial_attendance):
        remedial_attendance.append({
            "roll": student["roll"],
            "name": student["name"]
        })

    return jsonify({
        "ok": True,
        "matched": True,
        "auto_marked": True,
        "student_name": student["name"],
        "roll": student["roll"]
    })

@app.route("/scan_face")
def scan_face():

    detected_student = scan_and_mark_attendance()

    if detected_student:

        student = next(
            (s for s in students_list if s["name"] == detected_student),
            None
        )

        if student:

            if not any(r["roll"] == student["roll"] for r in remedial_attendance):

                remedial_attendance.append({
                    "roll": student["roll"],
                    "name": student["name"]
                })

        return redirect(url_for("attendance_page"))

    return redirect(url_for("attendance_page"))

@app.route("/attendance")
def attendance_page():

    attendance_report = []

    for student in students_list:

        present = any(
            record["roll"] == student["roll"]
            for record in remedial_attendance
        )

        attendance_report.append({
            "roll": student["roll"],
            "name": student["name"],
            "status": "Present" if present else "Absent"
        })

    total_students = len(students_list)
    total_present = len(remedial_attendance)
    total_absent = total_students - total_present

    return render_template(
        "attendance.html",
        records=attendance_report,
        total_students=total_students,
        total_present=total_present,
        total_absent=total_absent
    )


@app.route("/mark-attendance")
def mark_attendance():
    return render_template(
        "mark_attendance.html",
        students=students_list
    )


@app.route("/student-enrollment")
def student_enrollment():
    return render_template(
        "student_enrollment.html",
        students=students_list
    )

@app.route("/campus")
def campus_dashboard():

    total_classrooms = len([r for r in classrooms if r["type"] == "Classroom"])
    total_cabins = len([r for r in classrooms if r["type"] == "Teacher Cabin"])
    total_courses = len(courses)
    total_students = len(students_list)
    total_faculty = len(faculty_list)

    return render_template(
        "campus_dashboard.html",
        classrooms=classrooms,
        courses=courses,
        faculty=faculty_list,
        students=students_list,
        total_classrooms=total_classrooms,
        total_cabins=total_cabins,
        total_courses=total_courses,
        total_students=total_students,
        total_faculty=total_faculty
    )

# ======================================================
# RUN
# ======================================================
if __name__ == "__main__":
    app.run(debug=True)
