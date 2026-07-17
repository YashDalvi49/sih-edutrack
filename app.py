import streamlit as st
import sqlite3
import pandas as pd
import qrcode
from io import BytesIO
from datetime import datetime
from PIL import Image
from fpdf import FPDF

# --- DATABASE SETUP ---
DB_FILE = "sih_app.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create Students Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            roll_no TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            branch TEXT NOT NULL
        )
    ''')
    
    # Create Attendance Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT,
            date TEXT,
            status TEXT,
            FOREIGN KEY (roll_no) REFERENCES students (roll_no)
        )
    ''')
    
    # Create Curriculum Activities Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT,
            activity_name TEXT,
            category TEXT,
            date TEXT,
            hours_spent INTEGER,
            FOREIGN KEY (roll_no) REFERENCES students (roll_no)
        )
    ''')
    
    # Seed some mock data if empty
    cursor.execute("SELECT COUNT(*) FROM students")
    if cursor.fetchone()[0] == 0:
        mock_students = [
            ("S101", "Aarav Sharma", "Computer Science"),
            ("S102", "Ananya Iyer", "Information Technology"),
            ("S103", "Kabir Singh", "Electronics"),
            ("S104", "Meera Patel", "Computer Science"),
            ("S105", "Rohan Das", "Electrical")
        ]
        cursor.executemany("INSERT INTO students VALUES (?, ?, ?)", mock_students)
        
    conn.commit()
    conn.close()

init_db()

# --- PDF GENERATOR HELPER ---
class StudentReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "EDUTRACK - STUDENT PERFORMANCE REPORT", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "I", 10)
        self.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(10)
        
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} | Smart India Hackathon Prototype", align="C")

def generate_pdf_report(student_info, attendance_records, activity_records):
    pdf = StudentReportPDF()
    pdf.add_page()
    
    # Student Details Box
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "STUDENT PROFILE", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Name: {student_info['name']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Roll Number: {student_info['roll_no']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Branch: {student_info['branch']}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    # Attendance Section
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "ATTENDANCE SUMMARY", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    if attendance_records:
        total = len(attendance_records)
        present = sum(1 for r in attendance_records if r['status'] == "Present")
        pct = (present / total) * 100 if total > 0 else 0
        pdf.cell(0, 8, f"Total Working Days: {total}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f"Days Present: {present} | Days Absent: {total - present}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 8, f"Overall Attendance: {pct:.2f}%", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 8, "No attendance records found.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    # Activities Section
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "EXTRA-CURRICULAR & ACADEMIC ACTIVITIES", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    if activity_records:
        for act in activity_records:
            pdf.cell(0, 8, f"• [{act['date']}] {act['activity_name']} ({act['category']}) - {act['hours_spent']} Hours", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 8, "No curriculum activities registered.", new_x="LMARGIN", new_y="NEXT")
        
    return pdf.output()

# --- APP LAYOUT ---
st.set_page_config(page_title="EduTrack - SIH Pro", page_icon="🎓", layout="wide")

st.title("🎓 EduTrack")
st.subheader("Curriculum Activity, Attendance Tracker & Report Generator")
st.write("---")

# Sidebar Navigation
menu = ["📊 Dashboard", "📅 QR Attendance Portal", "🏆 Log Activity", "👥 Manage Students", "📜 Report Generator"]
choice = st.sidebar.selectbox("Navigation Menu", menu)

# --- 1. DASHBOARD VIEW ---
if choice == "📊 Dashboard":
    st.header("Institution Dashboard")
    
    conn = get_db_connection()
    
    # Quick metrics
    total_students = pd.read_sql_query("SELECT COUNT(*) as count FROM students", conn).iloc[0]['count']
    total_activities = pd.read_sql_query("SELECT COUNT(*) as count FROM activities", conn).iloc[0]['count']
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Enrolled Students", total_students)
    col2.metric("Total Activities Logged", total_activities)
    col3.metric("System Core Status", "Fully Operational ✅")
    
    st.write("### Recent Activity Logs")
    activities_df = pd.read_sql_query("""
        SELECT a.roll_no, s.name, a.activity_name, a.category, a.date, a.hours_spent 
        FROM activities a
        JOIN students s ON a.roll_no = s.roll_no
        ORDER BY a.id DESC LIMIT 5
    """, conn)
    
    if not activities_df.empty:
        st.dataframe(activities_df, use_container_width=True)
    else:
        st.info("No activities logged yet.")
        
    st.write("### Live Attendance Records")
    attendance_df = pd.read_sql_query("""
        SELECT att.date, att.roll_no, s.name, s.branch, att.status 
        FROM attendance att
        JOIN students s ON att.roll_no = s.roll_no
        ORDER BY att.date DESC
    """, conn)
    
    if not attendance_df.empty:
        st.dataframe(attendance_df, use_container_width=True)
    else:
        st.info("No attendance marked yet.")
        
    conn.close()

# --- 2. QR ATTENDANCE PORTAL ---
elif choice == "📅 QR Attendance Portal":
    st.header("⚡ Contactless Smart QR Attendance")
    st.write("Select a student to simulate scanning or view/print their unique verification QR Code.")

    conn = get_db_connection()
    students_df = pd.read_sql_query("SELECT * FROM students", conn)
    conn.close()

    if students_df.empty:
        st.warning("Please add students first!")
    else:
        col_select, col_qr = st.columns([1, 1])

        with col_select:
            student_list = {f"{row['name']} ({row['roll_no']})": row['roll_no'] for _, row in students_df.iterrows()}
            selected_student_lbl = st.selectbox("Select Student", list(student_list.keys()))
            selected_roll = student_list[selected_student_lbl]
            
            date_input = st.date_input("Attendance Date", datetime.now()).strftime('%Y-%m-%d')
            status_input = st.radio("Define Scan Status", ["Present", "Absent"])
            
            # Interactive QR check-in simulation
            if st.button("Simulate Smart QR Scan"):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM attendance WHERE roll_no = ? AND date = ?", (selected_roll, date_input))
                existing = cursor.fetchone()
                
                if existing:
                    cursor.execute("UPDATE attendance SET status = ? WHERE id = ?", (status_input, existing[0]))
                else:
                    cursor.execute("INSERT INTO attendance (roll_no, date, status) VALUES (?, ?, ?)", (selected_roll, date_input, status_input))
                
                conn.commit()
                conn.close()
                st.success(f"🎉 Checked in {selected_student_lbl} as '{status_input}' for {date_input} via QR pipeline!")

        with col_qr:
            st.write("#### Unique Student QR ID")
            # Generate a payload containing unique student data
            qr_payload = f"EDUTRACK-ID: {selected_roll}"
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(qr_payload)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buf = BytesIO()
            img.save(buf, format="PNG")
            st.image(buf.getvalue(), caption=f"Scan to Verify: {selected_student_lbl}", width=250)

# --- 3. LOG CURRICULUM ACTIVITY ---
elif choice == "🏆 Log Activity":
    st.header("Record Extra-Curricular & Academic Activities")
    
    conn = get_db_connection()
    students = pd.read_sql_query("SELECT roll_no, name FROM students", conn)
    conn.close()
    
    if students.empty:
        st.warning("No students available to log activities for.")
    else:
        student_options = {f"{row['name']} ({row['roll_no']})": row['roll_no'] for _, row in students.iterrows()}
        
        selected_student_label = st.selectbox("Select Student", list(student_options.keys()))
        selected_roll_no = student_options[selected_student_label]
        
        activity_name = st.text_input("Activity/Event Name", placeholder="e.g., Smart India Hackathon, Robo-Wars, Web Dev Workshop")
        category = st.selectbox("Category", ["Technical Hackathon", "Cultural Event", "Sports", "Seminar/Webinar", "Social Service/NSS"])
        date = st.date_input("Date of Activity", datetime.now()).strftime('%Y-%m-%d')
        hours = st.number_input("Duration (in Hours)", min_value=1, max_value=100, value=2)
        
        if st.button("Log Activity"):
            if activity_name.strip() == "":
                st.error("Please provide an Activity Name!")
            else:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO activities (roll_no, activity_name, category, date, hours_spent) VALUES (?, ?, ?, ?, ?)",
                    (selected_roll_no, activity_name, category, date, hours)
                )
                conn.commit()
                conn.close()
                st.success(f"Successfully logged '{activity_name}' for {selected_student_label}!")

# --- 4. MANAGE STUDENTS ---
elif choice == "👥 Manage Students":
    st.header("Student Database")
    
    with st.expander("➕ Add New Student", expanded=False):
        new_roll = st.text_input("Roll Number", placeholder="e.g., S106")
        new_name = st.text_input("Full Name", placeholder="e.g., Jane Doe")
        new_branch = st.selectbox("Branch", ["Computer Science", "Information Technology", "Electronics", "Electrical", "Mechanical", "Civil"])
        
        if st.button("Add Student"):
            if not new_roll or not new_name:
                st.error("Roll Number and Name are required!")
            else:
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO students VALUES (?, ?, ?)", (new_roll, new_name, new_branch))
                    conn.commit()
                    st.success(f"Added {new_name} to database!")
                except sqlite3.IntegrityError:
                    st.error("A student with this Roll Number already exists!")
                finally:
                    conn.close()
                    
    st.write("### Enrolled Students")
    conn = get_db_connection()
    students_df = pd.read_sql_query("SELECT * FROM students", conn)
    conn.close()
    
    st.dataframe(students_df, use_container_width=True)

# --- 5. REPORT GENERATOR (PDF) ---
elif choice == "📜 Report Generator":
    st.header("Print Student Portfolio & Performance PDF")
    st.write("Compile all class attendance records and extra-curricular credentials into an official PDF report.")
    
    conn = get_db_connection()
    students = pd.read_sql_query("SELECT * FROM students", conn)
    
    if students.empty:
        st.warning("No student records available.")
        conn.close()
    else:
        student_options = {f"{row['name']} ({row['roll_no']})": row['roll_no'] for _, row in students.iterrows()}
        selected_lbl = st.selectbox("Select Student to Export", list(student_options.keys()))
        selected_roll = student_options[selected_lbl]
        
        # Pull student specific details
        student_info = dict(pd.read_sql_query("SELECT * FROM students WHERE roll_no = ?", conn, params=(selected_roll,)).iloc[0])
        attendance_rec = pd.read_sql_query("SELECT status, date FROM attendance WHERE roll_no = ?", conn, params=(selected_roll,)).to_dict('records')
        activity_rec = pd.read_sql_query("SELECT activity_name, category, date, hours_spent FROM activities WHERE roll_no = ?", conn, params=(selected_roll,)).to_dict('records')
        conn.close()
        
        if st.button("Generate Report Card PDF"):
            try:
                pdf_bytes = generate_pdf_report(student_info, attendance_rec, activity_rec)
                
                st.success("PDF Compiled Successfully!")
                st.download_button(
                    label="⬇️ Download Performance PDF",
                    data=bytes(pdf_bytes),
                    file_name=f"Report_{selected_roll}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Failed to generate PDF: {e}")
