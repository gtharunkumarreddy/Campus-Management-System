import sqlite3

# Connect to SQLite database (creates database.db if not exists)
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# =========================
# CREATE FACULTY TABLE
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS faculty (
    faculty_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

# =========================
# CREATE STUDENT TABLE
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    roll_no TEXT UNIQUE NOT NULL,
    parent_email TEXT NOT NULL
)
""")

# =========================
# CREATE ATTENDANCE TABLE
# =========================
cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    date TEXT,
    status TEXT,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
)
""")

# =========================
# INSERT SAMPLE FACULTY
# =========================
cursor.execute("""
INSERT OR IGNORE INTO faculty (name, email, password)
VALUES ('Admin Faculty', 'admin@lpu.in', 'admin123')
""")

# =========================
# INSERT SAMPLE STUDENTS
# =========================
students_data = [
    ('Rahul Sharma', 'LPU101', 'parent1@gmail.com'),
    ('Priya Verma', 'LPU102', 'parent2@gmail.com'),
    ('Amit Kumar', 'LPU103', 'parent3@gmail.com'),
    ('Sneha Reddy', 'LPU104', 'parent4@gmail.com')
]

cursor.executemany("""
INSERT OR IGNORE INTO students (name, roll_no, parent_email)
VALUES (?, ?, ?)
""", students_data)

# Save changes and close connection
conn.commit()
conn.close()

print("✅ Database created successfully!")
print("✅ Faculty, Students, and Attendance tables are ready.")
print("✅ Sample data inserted.")
