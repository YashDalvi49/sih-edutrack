import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

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

# --- APP LAYOUT ---
st.set_page_config(page_title="EduTrack - SIH Prototype", page_icon="🎓", layout="wide")

st.title("🎓 EduTrack")
st.subheader("Curriculum Activity & Attendance Management System (SIH Prototype)")
st.write("---")

# Sidebar Navigation
menu = ["📊 Dashboard", "📅 Mark Attendance", "🏆 Log Activity", "👥 Manage Students"]
choice = st.sidebar.selectbox("Navigation Menu", menu)

# --- 1. DASHBOARD VIEW ---
if choice == "📊 Dashboard":
    st.header("School/College Analytics Dashboard")
    
    conn = get_db_connection()
    
    # Quick metrics
    total_students = pd.read_sql_query("SELECT COUNT(*) as count FROM students", conn).iloc[0]['count']
    total_activities = pd.read_sql_query("SELECT COUNT(*) as count FROM activities", conn).iloc[0]['count']
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Enrolled Students", total_students)
    col2.metric("Total Activities Logged", total_activities)
    col3.metric("Platform Status", "Online ✅")
    
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
        
    st.write("### Overall Attendance Sheet")
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

# --- 2. MARK ATTENDANCE ---
elif choice == "📅 Mark Attendance":
    st.header("Daily Attendance Marker")
    
    conn = get_db_connection()
    students_df = pd.read_sql_query("SELECT * FROM students", conn)
    conn.close()
    
    if students_df.empty:
        st.warning("Please add students first!")
    else:
        date_input = st.date_input("Select Date", datetime.now()).strftime('%Y-%m-%d')
        
        st.write("Mark **Present (P)** or **Absent (A)** for each student:")
        
        # Create a form to submit attendance all at once
        with st.form("attendance_form"):
            attendance_status = {}
            for index, row in students_df.iterrows():
                col_name, col_status = st.columns([3, 1])
                col_name.write(f"**{row['name']}** ({row['roll_no']}) - {row['branch']}")
                attendance_status[row['roll_no']] = col_status.selectbox(
                    "Status", ["Present", "Absent"], key=row['roll_no']
                )
            
            submitted = st.form_submit_button("Save Attendance")
            if submitted:
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    for roll_no, status in attendance_status.items():
                        # Check if already marked for today to prevent duplicates
                        cursor.execute(
                            "SELECT id FROM attendance WHERE roll_no = ? AND date = ?", 
                            (roll_no, date_input)
                        )
                        existing = cursor.fetchone()
                        
                        if existing:
                            cursor.execute(
                                "UPDATE attendance SET status = ? WHERE id = ?", 
                                (status, existing[0])
                            )
                        else:
                            cursor.execute(
                                "INSERT INTO attendance (roll_no, date, status) VALUES (?, ?, ?)", 
                                (roll_no, date_input, status)
                            )
                    conn.commit()
                    st.success("Attendance successfully updated!")
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    conn.close()

# --- 3. LOG CURRICULUM ACTIVITY ---
elif choice == "🏆 Log Activity":
    st.header("Record Extra-Curricular & Academic Activities")
    
    conn = get_db_connection()
    students = pd.read_sql_query("SELECT roll_no, name FROM students", conn)
    conn.close()
    
    if students.empty:
        st.warning("No students available to log activities for.")
    else:
        # Create a dictionary for dropdown display
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
                cursor = cursor = conn.cursor()
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
    
    # Form to add a new student
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
                    
    # Display list of existing students
    st.write("### Enrolled Students")
    conn = get_db_connection()
    students_df = pd.read_sql_query("SELECT * FROM students", conn)
    conn.close()
    
    st.dataframe(students_df, use_container_width=True)
