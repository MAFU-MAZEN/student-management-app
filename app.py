import streamlit as st
import base64
import json
import os
import time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
from typing import List, Dict, Any, Optional
from auth import init_auth_session_state, require_auth, show_auth_page, logout

# ------------------- Background -------------------
def set_background(image_path):
    with open(image_path, "rb") as img:
        encoded = base64.b64encode(img.read()).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background:
                linear-gradient(rgba(0,0,0,0.55), rgba(0,0,0,0.55)),
                url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_background("hubei.jpg")


# ------------------- Check if running correctly -------------------
def check_streamlit_running() -> bool:
    """Check if the app is being run with streamlit run command"""
    if "streamlit" in sys.modules:
        try:
            # Try to get Streamlit context - if it fails, we're in bare mode
            from streamlit.runtime.scriptrunner import get_script_run_ctx
            if get_script_run_ctx() is None:
                return False
            return True
        except:
            return False
    return False




# ------------------- Constants -------------------
DATA_FILE = "students.json"


# ------------------- Session State Initialization -------------------
def init_session_state() -> None:
    """Initialize session state variables"""
    if 'reset_confirmed' not in st.session_state:
        st.session_state.reset_confirmed = False
    if 'delete_confirmed' not in st.session_state:
        st.session_state.delete_confirmed = False
    if 'last_action' not in st.session_state:
        st.session_state.last_action = None
    if 'action_message' not in st.session_state:
        st.session_state.action_message = ""
    if 'show_reset_modal' not in st.session_state:
        st.session_state.show_reset_modal = False
    if 'student_to_delete' not in st.session_state:
        st.session_state.student_to_delete = None


# ------------------- Initialize Data File -------------------
def init_data_file() -> None:
    """Initialize the data file if it doesn't exist"""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)


# ------------------- Grade Calculation -------------------
def calculate_grade(marks: float) -> str:
    if marks >= 90:
        return "A"
    elif marks >= 80:
        return "B"
    elif marks >= 70:
        return "C"
    elif marks >= 60:
        return "D"
    else:
        return "F"


# ------------------- Load & Save -------------------
def load_students() -> List[Dict]:
    """
    Loads students from JSON and makes sure every record has a grade.
    """
    init_data_file()  # Ensure file exists

    students: List[Dict] = []
    try:
        with open(DATA_FILE, "r", encoding='utf-8') as f:
            students = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        students = []

    # Auto-backfill missing grades and registered_courses
    rerecord = False
    for s in students:
        if "grade" not in s and "marks" in s:
            try:
                s["grade"] = calculate_grade(float(s["marks"]))
                rerecord = True
            except (ValueError, TypeError):
                s["grade"] = "F"
                rerecord = True
        if "registered_courses" not in s:
            s["registered_courses"] = []
            rerecord = True

    if rerecord:
        save_students(students)

    return students


def save_students(students: List[Dict]) -> None:
    with open(DATA_FILE, "w", encoding='utf-8') as f:
        json.dump(students, f, indent=4)


def load_data(filename: str) -> List[Dict]:
    """Load data from JSON file"""
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, "r", encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def calculate_attendance_percentage(student: Dict) -> float:
    """Calculate attendance percentage for a student"""
    # Placeholder implementation - in a real app, this would calculate from attendance records
    return 85.0  # Default attendance percentage





def attendance_tracking() -> None:
    st.header("📋 Attendance Tracking")

    # Load data
    students = load_students()
    courses = load_data("courses.json")
    attendance_data = load_data("attendance.json")

    if not students:
        st.info("No student records found.")
        return

    if not courses:
        st.info("No courses available for attendance tracking.")
        return

    # Create tabs for different attendance operations
    tab1, tab2, tab3, tab4 = st.tabs(["📋 View Attendance", "✅ Mark Attendance", "📋 Attendance Reports", "📈 Analytics"])

    with tab1:
        st.subheader("📋 View Student Attendance")

        # Select student
        student_options = {f"{s['roll_no']} - {s['name']}": s for s in students}
        selected_student_key = st.selectbox("Select Student", list(student_options.keys()), key="view_attendance_student_select")

        if selected_student_key:
            student = student_options[selected_student_key]

            st.write("**Student Information:**")
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"Name: {student['name']}")
            with col2:
                st.info(f"Roll No: {student['roll_no']}")

            # Show attendance records from attendance.json
            student_attendance = [a for a in attendance_data if a["roll_no"] == student["roll_no"]]

            if student_attendance:
                st.subheader("📅 Attendance History")

                # Convert to dataframe for display
                attendance_display_data = []
                for record in student_attendance:
                    course_info = next((c for c in courses if c["course_id"] == record["course_id"]), None)
                    course_name = course_info["course_name"] if course_info else record["course_id"]

                    attendance_display_data.append({
                        "Course": course_name,
                        "Date": record["date"],
                        "Status": record["status"]
                    })

                if attendance_display_data:
                    df = pd.DataFrame(attendance_display_data)
                    df["Date"] = pd.to_datetime(df["Date"])
                    df = df.sort_values("Date", ascending=False)

                    st.dataframe(df, use_container_width=True, hide_index=True)

                    # Summary statistics
                    total_classes = len(df)
                    present_count = len(df[df["Status"] == "Present"])
                    late_count = len(df[df["Status"] == "Late"])
                    absent_count = len(df[df["Status"] == "Absent"])
                    attendance_percentage = ((present_count + late_count) / total_classes * 100) if total_classes > 0 else 0

                    st.subheader("📊 Attendance Summary")
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric("Total Classes", total_classes)
                    with col2:
                        st.metric("Present", present_count)
                    with col3:
                        st.metric("Late", late_count)
                    with col4:
                        st.metric("Absent", absent_count)
                    with col5:
                        st.metric("Attendance %", f"{attendance_percentage:.1f}%")
                else:
                    st.info("No attendance records found.")
            else:
                st.info("No attendance records found for this student.")

    with tab2:
        st.subheader("✅ Mark Attendance")

        # Select course
        course_options = {f"{c['course_id']} - {c['course_name']}": c for c in courses}
        selected_course_key = st.selectbox("Select Course", list(course_options.keys()), key="mark_attendance_course_select")

        if selected_course_key:
            selected_course = course_options[selected_course_key]

            st.write("**Course Information:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"Course: {selected_course['course_name']}")
            with col2:
                st.info(f"Instructor: {selected_course['instructor']}")
            with col3:
                st.info(f"Room: {selected_course.get('room', 'N/A')}")

            # Date selection
            attendance_date = st.date_input("Select Date", key="attendance_date")

            # Get registered students for this course
            registered_students = [s for s in students if selected_course["course_id"] in s.get("registered_courses", [])]

            if registered_students:
                st.subheader(f"📝 Mark Attendance for {len(registered_students)} Students")

                # Bulk attendance marking
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Mark All Present", type="primary", key="mark_all_present"):
                        for student in registered_students:
                            mark_attendance(student, selected_course["course_id"], str(attendance_date), "Present")
                        st.success(f"✅ Marked all {len(registered_students)} students as present!")
                        st.rerun()

                with col2:
                    if st.button("Mark All Absent", type="secondary", key="mark_all_absent"):
                        for student in registered_students:
                            mark_attendance(student, selected_course["course_id"], str(attendance_date), "Absent")
                        st.success(f"✅ Marked all {len(registered_students)} students as absent!")
                        st.rerun()

                # Individual attendance marking
                st.subheader("Individual Attendance")

                # Select specific student
                student_options = {f"{s['roll_no']} - {s['name']}": s for s in registered_students}
                selected_student_key = st.selectbox("Select Student for Individual Attendance", list(student_options.keys()), key="individual_student_select")

                if selected_student_key:
                    selected_student = student_options[selected_student_key]

                    st.write("**Selected Student:**")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"Name: {selected_student['name']}")
                    with col2:
                        st.info(f"Roll No: {selected_student['roll_no']}")

                    # Attendance checkboxes for selected student
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write("**Mark Attendance:**")
                    with col2:
                        present = st.checkbox("Present", key=f"present_{selected_student['roll_no']}", value=True)
                    with col3:
                        absent = st.checkbox("Absent", key=f"absent_{selected_student['roll_no']}", value=False)

                    # Determine status
                    if present and not absent:
                        attendance_status = "Present"
                    elif absent and not present:
                        attendance_status = "Absent"
                    else:
                        attendance_status = "Not Marked"

                    if st.button("Submit Individual Attendance", type="primary", key="submit_individual_attendance"):
                        if attendance_status != "Not Marked":
                            mark_attendance(selected_student, selected_course["course_id"], str(attendance_date), attendance_status)
                            st.success(f"✅ Attendance marked for {selected_student['name']}: {attendance_status}!")
                            st.rerun()
                        else:
                            st.warning("Please select either Present or Absent.")
                else:
                    st.info("Please select a student to mark individual attendance.")
            else:
                st.info("No students registered for this course.")

    with tab3:
        st.subheader("📊 Attendance Reports")

        # Select course for report
        course_options = {f"{c['course_id']} - {c['course_name']}": c for c in courses}
        selected_course_key = st.selectbox("Select Course for Report", list(course_options.keys()), key="report_course_select")

        if selected_course_key:
            selected_course = course_options[selected_course_key]

            # Get attendance data for this course
            course_attendance = []
            for student in students:
                if selected_course["course_id"] in student.get("registered_courses", []):
                    attendance_records = student.get("attendance", {}).get(selected_course["course_id"], [])
                    present_count = sum(1 for r in attendance_records if r["status"] == "Present")
                    total_count = len(attendance_records)
                    attendance_pct = (present_count / total_count * 100) if total_count > 0 else 0

                    course_attendance.append({
                        "Name": student["name"],
                        "Roll No": student["roll_no"],
                        "Total Classes": total_count,
                        "Present": present_count,
                        "Absent": total_count - present_count,
                        "Attendance %": f"{attendance_pct:.1f}%"
                    })

            if course_attendance:
                df = pd.DataFrame(course_attendance)
                df = df.sort_values("Attendance %", ascending=False)

                st.dataframe(df, use_container_width=True, hide_index=True)

                # Export option
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Attendance Report",
                    data=csv_data,
                    file_name=f"attendance_report_{selected_course['course_id']}.csv",
                    mime="text/csv",
                    key="download_attendance_report"
                )

                # Summary
                st.subheader("📊 Course Attendance Summary")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Students", len(df))
                with col2:
                    avg_attendance = df["Attendance %"].str.rstrip('%').astype(float).mean()
                    st.metric("Average Attendance", f"{avg_attendance:.1f}%")
                with col3:
                    high_attendance = df["Attendance %"].str.rstrip('%').astype(float).max()
                    st.metric("Highest Attendance", f"{high_attendance:.1f}%")
                with col4:
                    low_attendance = df["Attendance %"].str.rstrip('%').astype(float).min()
                    st.metric("Lowest Attendance", f"{low_attendance:.1f}%")
            else:
                st.info("No attendance data available for this course.")

    with tab4:
        st.subheader("📈 Attendance Analytics")

        # Overall attendance analytics
        all_attendance = []
        for student in students:
            attendance_records = student.get("attendance", {})
            total_present = 0
            total_classes = 0

            for course_records in attendance_records.values():
                for record in course_records:
                    total_classes += 1
                    if record["status"] == "Present":
                        total_present += 1

            attendance_pct = (total_present / total_classes * 100) if total_classes > 0 else 0

            all_attendance.append({
                "Name": student["name"],
                "Roll No": student["roll_no"],
                "Total Classes": total_classes,
                "Present": total_present,
                "Attendance %": attendance_pct
            })

        if all_attendance:
            df = pd.DataFrame(all_attendance)
            df = df[df["Total Classes"] > 0]  # Only show students with attendance records

            if not df.empty:
                # Attendance distribution
                st.subheader("📊 Attendance Distribution")

                fig, ax = plt.subplots(figsize=(10, 6))
                attendance_ranges = pd.cut(df["Attendance %"], bins=[0, 50, 60, 70, 80, 90, 100],
                                         labels=['0-50%', '50-60%', '60-70%', '70-80%', '80-90%', '90-100%'])
                attendance_counts = attendance_ranges.value_counts().sort_index()
                attendance_counts.plot(kind='bar', ax=ax)
                ax.set_title("Attendance Percentage Distribution")
                ax.set_xlabel("Attendance Range")
                ax.set_ylabel("Number of Students")
                plt.xticks(rotation=45)
                st.pyplot(fig)

                # Top and bottom performers
                st.subheader("🏆 Attendance Leaders")
                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Highest Attendance**")
                    top_attendance = df.nlargest(5, "Attendance %")[["Name", "Roll No", "Attendance %"]]
                    st.dataframe(top_attendance, use_container_width=True, hide_index=True)

                with col2:
                    st.write("**Lowest Attendance**")
                    bottom_attendance = df.nsmallest(5, "Attendance %")[["Name", "Roll No", "Attendance %"]]
                    st.dataframe(bottom_attendance, use_container_width=True, hide_index=True)

                # Summary metrics
                st.subheader("📈 Overall Statistics")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Students with Records", len(df))
                with col2:
                    avg_attendance = df["Attendance %"].mean()
                    st.metric("Average Attendance", f"{avg_attendance:.1f}%")
                with col3:
                    high_attendance = df["Attendance %"].max()
                    st.metric("Highest Attendance", f"{high_attendance:.1f}%")
                with col4:
                    low_attendance = df["Attendance %"].min()
                    st.metric("Lowest Attendance", f"{low_attendance:.1f}%")
            else:
                st.info("No attendance records found.")
        else:
            st.info("No attendance data available.")


def mark_attendance(student: Dict, course_id: str, date: str, status: str) -> None:
    """Mark attendance for a student in a course"""
    if "attendance" not in student:
        student["attendance"] = {}

    if course_id not in student["attendance"]:
        student["attendance"][course_id] = []

    # Check if attendance already marked for this date
    existing_record = next((r for r in student["attendance"][course_id] if r["date"] == date), None)

    if existing_record:
        existing_record["status"] = status
        existing_record["time"] = pd.Timestamp.now().strftime("%H:%M:%S")
    else:
        student["attendance"][course_id].append({
            "date": date,
            "status": status,
            "time": pd.Timestamp.now().strftime("%H:%M:%S")
        })


def course_registration() -> None:
    st.header("📚 Course Registration")

    # Load data
    students = load_students()
    courses = load_data("courses.json")

    if not students:
        st.info("No student records found.")
        return

    if not courses:
        st.info("No courses available for registration.")
        return

    # Create tabs for different registration operations
    tab1, tab2, tab3, tab4 = st.tabs(["📋 View Available Courses", "➕ Register for Course", "➖ Drop Course", "👤 My Registered Courses"])

    with tab1:
        st.subheader("📋 Available Courses")

        # Display courses with capacity information
        course_data = []
        for course in courses:
            # Count current registrations
            registered_count = sum(1 for student in students if course["course_id"] in student.get("registered_courses", []))

            course_data.append({
                "Course ID": course["course_id"],
                "Course Name": course["course_name"],
                "Instructor": course["instructor"],
                "Credits": course["credits"],
                "Max Students": course["max_students"],
                "Registered": registered_count,
                "Available Spots": max(0, course["max_students"] - registered_count),
                "Status": "Full" if registered_count >= course["max_students"] else "Available",
                "Schedule": course.get("schedule", "N/A"),
                "Room": course.get("room", "N/A")
            })

        if course_data:
            df = pd.DataFrame(course_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Summary statistics
            st.subheader("📋 Course Registration Summary")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Courses", len(courses))
            with col2:
                available_courses = sum(1 for c in course_data if c["Status"] == "Available")
                st.metric("Available Courses", available_courses)
            with col3:
                full_courses = sum(1 for c in course_data if c["Status"] == "Full")
                st.metric("Full Courses", full_courses)
            with col4:
                total_capacity = sum(c["Max Students"] for c in course_data)
                total_registered = sum(c["Registered"] for c in course_data)
                st.metric("Total Capacity Used", f"{total_registered}/{total_capacity}")
        else:
            st.info("No courses available.")

    with tab2:
        st.subheader("➕ Register for Course")

        # Select student
        student_options = {f"{s['roll_no']} - {s['name']}": s for s in students}
        selected_student_key = st.selectbox("Select Student", list(student_options.keys()), key="register_student_select")

        if selected_student_key:
            student = student_options[selected_student_key]

            st.write("**Student Information:**")
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"Name: {student['name']}")
            with col2:
                st.info(f"Roll No: {student['roll_no']}")

            # Show current registrations
            current_registrations = student.get("registered_courses", [])
            if current_registrations:
                st.write("**Currently Registered Courses:**")
                for course_id in current_registrations:
                    course_info = next((c for c in courses if c["course_id"] == course_id), None)
                    if course_info:
                        st.write(f"- {course_info['course_name']} ({course_id})")
            else:
                st.info("No courses currently registered.")

            # Select course to register
            available_courses = []
            for course in courses:
                registered_count = sum(1 for s in students if course["course_id"] in s.get("registered_courses", []))
                if registered_count < course["max_students"] and course["course_id"] not in current_registrations:
                    available_courses.append(course)

            if available_courses:
                course_options = {f"{c['course_id']} - {c['course_name']}": c for c in available_courses}
                selected_course_key = st.selectbox("Select Course to Register", list(course_options.keys()), key="register_course_select")

                if selected_course_key:
                    selected_course = course_options[selected_course_key]

                    st.write("**Course Details:**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.info(f"Course: {selected_course['course_name']}")
                    with col2:
                        st.info(f"Instructor: {selected_course['instructor']}")
                    with col3:
                        st.info(f"Credits: {selected_course['credits']}")

                    if st.button("Register for Course", type="primary", key="register_course_btn"):
                        # Add course to student's registered courses
                        if "registered_courses" not in student:
                            student["registered_courses"] = []
                        student["registered_courses"].append(selected_course["course_id"])

                        save_students(students)
                        st.success(f"✅ Successfully registered {student['name']} for {selected_course['course_name']}!")
                        st.rerun()
            else:
                st.info("No available courses for registration.")

    with tab3:
        st.subheader("➖ Drop Course")

        # Select student
        student_options = {f"{s['roll_no']} - {s['name']}": s for s in students}
        selected_student_key = st.selectbox("Select Student", list(student_options.keys()), key="drop_student_select")

        if selected_student_key:
            student = student_options[selected_student_key]

            # Show current registrations
            current_registrations = student.get("registered_courses", [])
            if current_registrations:
                st.write("**Currently Registered Courses:**")
                course_options = {}
                for course_id in current_registrations:
                    course_info = next((c for c in courses if c["course_id"] == course_id), None)
                    if course_info:
                        course_options[f"{course_id} - {course_info['course_name']}"] = course_id

                if course_options:
                    selected_course_key = st.selectbox("Select Course to Drop", list(course_options.keys()), key="drop_course_select")

                    if selected_course_key:
                        course_to_drop = course_options[selected_course_key]
                        course_info = next((c for c in courses if c["course_id"] == course_to_drop), None)

                        st.warning(f"Are you sure you want to drop **{course_info['course_name']}**?")

                        if st.button("Drop Course", type="primary", key="drop_course_btn"):
                            student["registered_courses"].remove(course_to_drop)
                            save_students(students)
                            st.success(f"✅ Successfully dropped {course_info['course_name']} for {student['name']}!")
                            st.rerun()
                else:
                    st.info("No courses to drop.")
            else:
                st.info("Student has no registered courses.")

    with tab4:
        st.subheader("👤 My Registered Courses")

        # Select student
        student_options = {f"{s['roll_no']} - {s['name']}": s for s in students}
        selected_student_key = st.selectbox("Select Student", list(student_options.keys()), key="view_registered_student_select")

        if selected_student_key:
            student = student_options[selected_student_key]

            current_registrations = student.get("registered_courses", [])

            if current_registrations:
                st.write(f"**Registered Courses for {student['name']}:**")

                registered_course_data = []
                for course_id in current_registrations:
                    course_info = next((c for c in courses if c["course_id"] == course_id), None)
                    if course_info:
                        registered_course_data.append({
                            "Course ID": course_info["course_id"],
                            "Course Name": course_info["course_name"],
                            "Instructor": course_info["instructor"],
                            "Credits": course_info["credits"],
                            "Schedule": course_info.get("schedule", "N/A"),
                            "Room": course_info.get("room", "N/A")
                        })

                if registered_course_data:
                    df = pd.DataFrame(registered_course_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)

                    # Summary
                    total_credits = sum(c["Credits"] for c in registered_course_data)
                    st.metric("Total Registered Courses", len(registered_course_data))
                    st.metric("Total Credits", total_credits)
                else:
                    st.info("No course details available.")
            else:
                st.info(f"{student['name']} has no registered courses.")


def grade_management() -> None:
    st.header("📝 Grade Management")

    # Load data
    students = load_students()
    courses = load_data("courses.json")

    if not students:
        st.info("No student records found.")
        return

    # Create tabs for different grade management operations
    tab1, tab2, tab3, tab4 = st.tabs(["📊 View Grades", "✏️ Update Grades", "📈 Bulk Operations", "📋 Grade Reports"])

    with tab1:
        st.subheader("📊 Student Grades Overview")

        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            grade_filter = st.multiselect("Filter by Grade", ["A", "B", "C", "D", "F"], default=["A", "B", "C", "D", "F"], key="grade_filter_gm")
        with col2:
            course_filter = st.multiselect("Filter by Course", [c["course_id"] for c in courses] if courses else [], key="course_filter_gm")
        with col3:
            min_marks = st.slider("Min Marks", 0, 100, 0, key="min_marks_gm")

        # Display grades table
        grade_data = []
        for student in students:
            if student["grade"] in grade_filter and student["marks"] >= min_marks:
                # Check course filter
                if course_filter and not any(course in student.get("registered_courses", []) for course in course_filter):
                    continue

                grade_data.append({
                    "Name": student["name"],
                    "Roll No": student["roll_no"],
                    "Overall Grade": student["grade"],
                    "Overall Marks": f"{student['marks']:.2f}",
                    "Registered Courses": ", ".join(student.get("registered_courses", [])),
                    "Attendance %": calculate_attendance_percentage(student)
                })

        if grade_data:
            df = pd.DataFrame(grade_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Summary statistics
            st.subheader("📊 Grade Summary")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Students", len(df))
            with col2:
                avg_marks = df["Overall Marks"].astype(float).mean()
                st.metric("Average Marks", f"{avg_marks:.2f}")
            with col3:
                grade_counts = df["Overall Grade"].value_counts()
                pass_rate = (grade_counts.get("A", 0) + grade_counts.get("B", 0) + grade_counts.get("C", 0)) / len(df) * 100
                st.metric("Pass Rate", f"{pass_rate:.1f}%")
            with col4:
                top_grade = grade_counts.idxmax() if not grade_counts.empty else "N/A"
                st.metric("Most Common Grade", top_grade)
        else:
            st.info("No students match the selected filters.")

    with tab2:
        st.subheader("✏️ Update Student Grades")

        # Select student
        student_options = {f"{s['roll_no']} - {s['name']}": s for s in students}
        selected_student_key = st.selectbox("Select Student", list(student_options.keys()), key="select_student_update")

        if selected_student_key:
            student = student_options[selected_student_key]

            st.write("**Current Information:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"Name: {student['name']}")
            with col2:
                st.info(f"Roll No: {student['roll_no']}")
            with col3:
                st.info(f"Current Grade: {student['grade']} ({student['marks']:.2f})")

            # Update overall marks
            st.subheader("Update Overall Grade")
            new_marks = st.number_input("New Marks", 0.0, 100.0, float(student['marks']), 0.5, key="new_overall_marks")

            if new_marks != student['marks']:
                new_grade = calculate_grade(new_marks)
                st.success(f"New Grade: {new_grade}")

            # Course-specific grades
            st.subheader("Course-Specific Grades")
            registered_courses = student.get("registered_courses", [])
            course_grades = student.get("course_grades", {})

            if registered_courses:
                for course_id in registered_courses:
                    course_info = next((c for c in courses if c["course_id"] == course_id), None)
                    course_name = course_info["course_name"] if course_info else course_id

                    current_course_marks = course_grades.get(course_id, 0.0)
                    new_course_marks = st.number_input(
                        f"{course_name} ({course_id})",
                        0.0, 100.0, float(current_course_marks), 0.5,
                        key=f"course_marks_{course_id}"
                    )

                    if new_course_marks != current_course_marks:
                        course_grades[course_id] = new_course_marks

                # Update button
                if st.button("Update Grades", type="primary", key="update_grades_btn"):
                    # Update overall marks
                    if new_marks != student['marks']:
                        student['marks'] = new_marks
                        student['grade'] = calculate_grade(new_marks)

                    # Update course grades
                    student['course_grades'] = course_grades

                    # Recalculate overall marks if course grades exist
                    if course_grades:
                        avg_course_marks = sum(course_grades.values()) / len(course_grades)
                        student['marks'] = avg_course_marks
                        student['grade'] = calculate_grade(avg_course_marks)

                    save_students(students)
                    st.success("✅ Grades updated successfully!")
                    st.rerun()
            else:
                st.info("No registered courses for this student.")

    with tab3:
        st.subheader("📈 Bulk Grade Operations")

        st.info("Bulk operations for updating multiple student grades at once.")

        # Bulk update by grade range
        st.subheader("Bulk Update by Grade Range")
        col1, col2, col3 = st.columns(3)
        with col1:
            min_range = st.number_input("Min Marks", 0.0, 100.0, 0.0, key="bulk_min_range")
        with col2:
            max_range = st.number_input("Max Marks", 0.0, 100.0, 100.0, key="bulk_max_range")
        with col3:
            bulk_adjustment = st.number_input("Adjustment (+/-)", -50.0, 50.0, 0.0, key="bulk_adjustment")

        if st.button("Apply Bulk Adjustment", type="primary", key="bulk_adjust_btn"):
            updated_count = 0
            for student in students:
                if min_range <= student['marks'] <= max_range:
                    new_marks = max(0.0, min(100.0, student['marks'] + bulk_adjustment))
                    if new_marks != student['marks']:
                        student['marks'] = new_marks
                        student['grade'] = calculate_grade(new_marks)
                        updated_count += 1

            if updated_count > 0:
                save_students(students)
                st.success(f"✅ Updated grades for {updated_count} students!")
                st.rerun()
            else:
                st.info("No students found in the specified range.")

        # Bulk update by course
        st.subheader("Bulk Update by Course")
        if courses:
            selected_course = st.selectbox("Select Course", [c["course_id"] for c in courses], key="bulk_course_select")
            course_adjustment = st.number_input("Course Grade Adjustment (+/-)", -50.0, 50.0, 0.0, key="course_adjustment")

            if st.button("Apply Course Adjustment", type="primary", key="course_adjust_btn"):
                updated_count = 0
                for student in students:
                    course_grades = student.get("course_grades", {})
                    if selected_course in course_grades:
                        new_course_marks = max(0.0, min(100.0, course_grades[selected_course] + course_adjustment))
                        if new_course_marks != course_grades[selected_course]:
                            course_grades[selected_course] = new_course_marks
                            student["course_grades"] = course_grades

                            # Recalculate overall marks
                            if course_grades:
                                avg_marks = sum(course_grades.values()) / len(course_grades)
                                student['marks'] = avg_marks
                                student['grade'] = calculate_grade(avg_marks)

                            updated_count += 1

                if updated_count > 0:
                    save_students(students)
                    st.success(f"✅ Updated course grades for {updated_count} students!")
                    st.rerun()
                else:
                    st.info("No students found with this course.")

    with tab4:
        st.subheader("📋 Grade Reports")

        # Generate grade report
        if st.button("Generate Grade Report", type="primary", key="generate_report_btn"):
            report_data = []

            for student in students:
                course_grades = student.get("course_grades", {})
                attendance_pct = calculate_attendance_percentage(student)

                report_data.append({
                    "Name": student["name"],
                    "Roll No": student["roll_no"],
                    "Overall Grade": student["grade"],
                    "Overall Marks": f"{student['marks']:.2f}",
                    "Courses Registered": len(student.get("registered_courses", [])),
                    "Courses Graded": len(course_grades),
                    "Attendance %": f"{attendance_pct:.1f}",
                    "Performance Status": "Excellent" if student["grade"] == "A" else
                                        "Good" if student["grade"] == "B" else
                                        "Average" if student["grade"] == "C" else
                                        "Needs Improvement" if student["grade"] == "D" else "Critical"
                })

            df_report = pd.DataFrame(report_data)

            # Display report
            st.dataframe(df_report, use_container_width=True, hide_index=True)

            # Export options
            csv_data = df_report.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV Report",
                data=csv_data,
                file_name="grade_report.csv",
                mime="text/csv",
                key="download_report"
            )


def student_performance_analytics() -> None:
    st.header("📈 Student Performance Analytics")

    # Load all data
    students = load_students()
    courses = load_data("courses.json")
    attendance_data = load_data("attendance.json")

    if not students:
        st.info("No student data available for analytics.")
        return

    # Create tabs for different analytics views
    tab1, tab2, tab3 = st.tabs([
        "📊 Overview", "📈 Performance Trends", "🎯 Top Performers"
    ])

    with tab1:
        st.subheader("📊 Performance Overview")

        # Convert to DataFrame for analysis
        df_students = pd.DataFrame(students)

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Students", len(df_students))
        with col2:
            avg_marks = df_students['marks'].mean()
            st.metric("Average Marks", f"{avg_marks:.1f}")
        with col3:
            pass_rate = (df_students['grade'] != 'F').sum() / len(df_students) * 100
            st.metric("Pass Rate", f"{pass_rate:.1f}%")
        with col4:
            excellence_rate = (df_students['grade'] == 'A').sum() / len(df_students) * 100
            st.metric("A Grade Rate", f"{excellence_rate:.1f}%")

        # Grade distribution
        st.subheader("📊 Grade Distribution")
        grade_counts = df_students['grade'].value_counts().sort_index()

        col1, col2 = st.columns([2, 1])
        with col1:
            fig, ax = plt.subplots(figsize=(10, 6))
            colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99','#ff99cc']
            grade_counts.plot(kind='pie', autopct='%1.1f%%', colors=colors, ax=ax)
            ax.set_title("Grade Distribution")
            ax.set_ylabel("")
            st.pyplot(fig)

        with col2:
            st.write("**Grade Breakdown:**")
            for grade, count in grade_counts.items():
                percentage = (count / len(df_students)) * 100
                st.write(f"**{grade}:** {count} students ({percentage:.1f}%)")

        # Performance ranges
        st.subheader("📊 Performance Ranges")
        ranges = pd.cut(df_students['marks'],
                       bins=[0, 40, 60, 70, 80, 90, 100],
                       labels=['0-40 (Fail)', '40-60 (Poor)', '60-70 (Average)',
                              '70-80 (Good)', '80-90 (Very Good)', '90-100 (Excellent)'])
        range_counts = ranges.value_counts().sort_index()

        fig, ax = plt.subplots(figsize=(12, 6))
        range_counts.plot(kind='barh', color='skyblue', ax=ax)
        ax.set_title("Student Performance Ranges")
        ax.set_xlabel("Number of Students")
        plt.tight_layout()
        st.pyplot(fig)

    with tab2:
        st.subheader("📈 Performance Trends & Correlations")

        # Marks distribution histogram
        st.subheader("Marks Distribution")
        fig, ax = plt.subplots(figsize=(10, 6))
        df_students['marks'].plot(kind='density', ax=ax, color='skyblue')
        ax.set_title("Distribution of Student Marks")
        ax.set_xlabel("Marks")
        ax.set_ylabel("Density")
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)

        # Attendance vs Performance correlation
        st.subheader("📈 Attendance vs Performance Correlation")

        # Calculate attendance percentage for each student
        attendance_stats = {}
        for record in attendance_data:
            roll_no = record['roll_no']
            if roll_no not in attendance_stats:
                attendance_stats[roll_no] = {'present': 0, 'total': 0}
            attendance_stats[roll_no]['total'] += 1
            if record['status'] in ['Present', 'Late']:
                attendance_stats[roll_no]['present'] += 1

        # Add attendance data to students
        attendance_percentages = []
        student_marks = []
        student_names = []
        valid_students = []

        for student in students:
            roll_no = student['roll_no']
            if roll_no in attendance_stats:
                total = attendance_stats[roll_no]['total']
                present = attendance_stats[roll_no]['present']
                attendance_pct = (present / total * 100) if total > 0 else 0
            else:
                attendance_pct = 0

            if attendance_pct > 0:  # Only include students with attendance records
                attendance_percentages.append(attendance_pct)
                student_marks.append(student['marks'])
                student_names.append(student['name'])
                valid_students.append(student)

        if len(attendance_percentages) > 3:  # Need at least 4 points for meaningful correlation
            # Create correlation dataframe
            corr_df = pd.DataFrame({
                'Attendance %': attendance_percentages,
                'Marks': student_marks,
                'Name': student_names
            })

            col1, col2 = st.columns([2, 1])

            with col1:
                # Enhanced scatter plot with regression line
                fig, ax = plt.subplots(figsize=(12, 8))

                # Scatter plot
                scatter = ax.scatter(attendance_percentages, student_marks,
                                   alpha=0.7, c=student_marks, cmap='RdYlGn', s=100, edgecolors='black')

                # Add regression line
                try:
                    from scipy import stats
                    slope, intercept, r_value, p_value, std_err = stats.linregress(attendance_percentages, student_marks)
                    line_x = np.array([min(attendance_percentages), max(attendance_percentages)])
                    line_y = slope * line_x + intercept
                    ax.plot(line_x, line_y, 'r-', linewidth=2, alpha=0.8, label=f'Regression Line (R² = {r_value**2:.3f})')
                    ax.legend()
                except ImportError:
                    # Fallback to numpy polyfit if scipy not available
                    try:
                        coeffs = np.polyfit(attendance_percentages, student_marks, 1)
                        line_x = np.array([min(attendance_percentages), max(attendance_percentages)])
                        line_y = coeffs[0] * line_x + coeffs[1]
                        ax.plot(line_x, line_y, 'r-', linewidth=2, alpha=0.8, label='Trend Line')
                        ax.legend()
                    except:
                        pass

                ax.set_xlabel("Attendance Percentage (%)", fontsize=12)
                ax.set_ylabel("Academic Marks", fontsize=12)
                ax.set_title("Attendance vs Academic Performance Correlation", fontsize=14, fontweight='bold')
                ax.grid(True, alpha=0.3)
                ax.set_xlim(0, 100)
                ax.set_ylim(0, 100)

                # Add colorbar
                cbar = plt.colorbar(scatter, ax=ax)
                cbar.set_label('Academic Performance', fontsize=10)

                st.pyplot(fig)

            with col2:
                # Correlation statistics
                correlation = np.corrcoef(attendance_percentages, student_marks)[0, 1]

                # Calculate correlation strength
                corr_strength = abs(correlation)
                if corr_strength >= 0.8:
                    strength_text = "Very Strong"
                    strength_color = "🟢"
                elif corr_strength >= 0.6:
                    strength_text = "Strong"
                    strength_color = "🟡"
                elif corr_strength >= 0.3:
                    strength_text = "Moderate"
                    strength_color = "🟠"
                else:
                    strength_text = "Weak"
                    strength_color = "🔴"

                st.metric("Correlation Coefficient", f"{correlation:.3f}")
                st.metric("Correlation Strength", f"{strength_text} {strength_color}")

                # Statistical significance (approximate)
                n = len(attendance_percentages)
                if n > 10:
                    # Approximate t-statistic
                    t_stat = correlation * np.sqrt((n - 2) / (1 - correlation**2))
                    # For large n, t > 1.96 is significant at 95% confidence
                    is_significant = abs(t_stat) > 1.96
                    if is_significant:
                        st.success("✅ Statistically Significant")
                    else:
                        st.warning("⚠️ Not Statistically Significant")

                # Performance insights based on correlation
                st.subheader("Correlation Insights")

                if correlation > 0.5:
                    st.success("🎯 Strong positive correlation: Better attendance leads to higher academic performance!")
                elif correlation > 0.3:
                    st.info("📈 Moderate positive correlation: Attendance positively impacts academic performance.")
                elif correlation > 0:
                    st.info("🔄 Weak positive correlation: Some relationship between attendance and performance.")
                elif correlation > -0.3:
                    st.warning("⚠️ Weak negative correlation: Attendance may not strongly predict performance.")
                else:
                    st.error("📉 Negative correlation: Higher attendance associated with lower performance (investigate further).")

                # Attendance impact analysis
                high_attendance = corr_df[corr_df['Attendance %'] >= 80]
                low_attendance = corr_df[corr_df['Attendance %'] < 60]

                if not high_attendance.empty and not low_attendance.empty:
                    high_avg_marks = high_attendance['Marks'].mean()
                    low_avg_marks = low_attendance['Marks'].mean()
                    difference = high_avg_marks - low_avg_marks

                    st.metric("Performance Gap", f"{difference:+.1f} marks",
                             delta=f"{difference:+.1f}",
                             delta_color="normal" if difference > 0 else "inverse")

                    if difference > 10:
                        st.success("🌟 High attendance students perform significantly better!")
                    elif difference < -10:
                        st.warning("⚠️ Attendance pattern needs investigation.")

            # Additional correlation analysis
            st.subheader("🔍 Detailed Correlation Analysis")

            # Quartile analysis
            try:
                corr_df['Attendance_Quartile'] = pd.qcut(corr_df['Attendance %'], q=4, duplicates='drop',
                                                        labels=['Q1 (Lowest)', 'Q2', 'Q3', 'Q4 (Highest)'])
            except ValueError:
                # Fallback to pd.cut with fixed bins if qcut fails due to too many duplicates
                bins = [0, 25, 50, 75, 100]
                corr_df['Attendance_Quartile'] = pd.cut(corr_df['Attendance %'], bins=bins,
                                                       labels=['Q1 (Lowest)', 'Q2', 'Q3', 'Q4 (Highest)'],
                                                       include_lowest=True)

            quartile_stats = corr_df.groupby('Attendance_Quartile')['Marks'].agg(['mean', 'std', 'count']).round(2)

            col1, col2 = st.columns(2)

            with col1:
                st.write("**Performance by Attendance Quartile:**")
                st.dataframe(quartile_stats, use_container_width=True)

            with col2:
                # Visualize quartile performance
                fig, ax = plt.subplots(figsize=(8, 6))
                quartile_stats['mean'].plot(kind='bar', ax=ax, color='skyblue', alpha=0.8)
                ax.set_title("Average Marks by Attendance Quartile")
                ax.set_xlabel("Attendance Quartile")
                ax.set_ylabel("Average Marks")
                ax.grid(True, alpha=0.3)
                plt.xticks(rotation=45)
                st.pyplot(fig)

            # Top and bottom performers correlation
            st.subheader("🏆 Performance Extremes Analysis")

            # Students with highest attendance but low performance
            high_attendance_low_perf = corr_df[
                (corr_df['Attendance %'] >= 80) &
                (corr_df['Marks'] < corr_df['Marks'].quantile(0.3))
            ]

            # Students with low attendance but high performance
            low_attendance_high_perf = corr_df[
                (corr_df['Attendance %'] < 60) &
                (corr_df['Marks'] > corr_df['Marks'].quantile(0.7))
            ]

            col1, col2 = st.columns(2)

            with col1:
                if not high_attendance_low_perf.empty:
                    st.warning(f"⚠️ {len(high_attendance_low_perf)} students with high attendance but low performance:")
                    for _, student in high_attendance_low_perf.iterrows():
                        st.write(f"• {student['Name']}: {student['Attendance %']:.1f}% attendance, {student['Marks']:.1f} marks")
                else:
                    st.success("✅ No students with high attendance and low performance found.")

            with col2:
                if not low_attendance_high_perf.empty:
                    st.info(f"🌟 {len(low_attendance_high_perf)} high-performing students with low attendance:")
                    for _, student in low_attendance_high_perf.iterrows():
                        st.write(f"• {student['Name']}: {student['Attendance %']:.1f}% attendance, {student['Marks']:.1f} marks")
                else:
                    st.info("No exceptional cases found.")

        else:
            st.warning("📊 Insufficient attendance data for correlation analysis. Need at least 4 students with attendance records.")

    with tab3:
        st.subheader("🎯 Top & Bottom Performers")

        # Top performers
        st.subheader("🏆 Top 10 Performers")
        top_performers = df_students.nlargest(10, 'marks')[['name', 'roll_no', 'marks', 'grade']]
        st.dataframe(top_performers, use_container_width=True, hide_index=True)

        # Bottom performers
        st.subheader("📉 Bottom 10 Performers")
        bottom_performers = df_students.nsmallest(10, 'marks')[['name', 'roll_no', 'marks', 'grade']]
        st.dataframe(bottom_performers, use_container_width=True, hide_index=True)

        # Grade-specific analysis
        st.subheader("📊 Grade-wise Performance Leaders")

        col1, col2 = st.columns(2)
        with col1:
            st.write("**A Grade Students:**")
            a_students = df_students[df_students['grade'] == 'A'][['name', 'marks']].sort_values('marks', ascending=False)
            if not a_students.empty:
                st.dataframe(a_students.head(5), use_container_width=True, hide_index=True)
            else:
                st.info("No A grade students found.")

        with col2:
            st.write("**Failing Students (F Grade):**")
            f_students = df_students[df_students['grade'] == 'F'][['name', 'marks']].sort_values('marks')
            if not f_students.empty:
                st.dataframe(f_students.head(5), use_container_width=True, hide_index=True)
            else:
                st.info("No failing students found.")


def document_management() -> None:
    st.header("📄 Document Management")

    # Load data
    students = load_students()
    documents = load_data("documents.json")

    if not students:
        st.info("No student records found.")
        return

    # Create tabs for different document operations
    tab1, tab2, tab3 = st.tabs(["📤 Upload Document", "👀 View Documents", "🗑️ Delete Document"])

    with tab1:
        st.subheader("📤 Upload Student Document")

        # Select student
        student_options = {f"{s['roll_no']} - {s['name']}": s for s in students}
        selected_student_key = st.selectbox("Select Student", list(student_options.keys()), key="upload_doc_student_select")

        if selected_student_key:
            student = student_options[selected_student_key]

            st.write("**Student Information:**")
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"Name: {student['name']}")
            with col2:
                st.info(f"Roll No: {student['roll_no']}")

            # Document type selection
            document_types = ["Certificate", "Transcript", "ID Card", "Passport", "Medical Record", "Other"]
            doc_type = st.selectbox("Document Type", document_types, key="doc_type_select")

            # Additional description
            description = st.text_input("Document Description (optional)", placeholder="e.g., Degree Certificate, Semester 1 Transcript", key="doc_description")

            # File upload
            uploaded_file = st.file_uploader(
                "Choose document file",
                type=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'],
                help="Upload PDF, image, or document files",
                key="doc_file_uploader"
            )

            if uploaded_file and st.button("Upload Document", type="primary", key="upload_doc_btn"):
                # Create documents directory if it doesn't exist
                os.makedirs("documents", exist_ok=True)

                # Generate unique filename
                file_extension = os.path.splitext(uploaded_file.name)[1]
                unique_filename = f"{student['roll_no']}_{doc_type.replace(' ', '_')}_{int(time.time())}{file_extension}"
                file_path = os.path.join("documents", unique_filename)

                # Save file
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Save metadata
                if documents is None:
                    documents = []

                doc_record = {
                    "id": len(documents) + 1,
                    "roll_no": student["roll_no"],
                    "student_name": student["name"],
                    "document_type": doc_type,
                    "description": description or "",
                    "filename": unique_filename,
                    "original_filename": uploaded_file.name,
                    "upload_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "file_size": len(uploaded_file.getbuffer())
                }

                documents.append(doc_record)

                # Save to file
                with open("documents.json", "w", encoding='utf-8') as f:
                    json.dump(documents, f, indent=4)

                st.success(f"✅ Document '{uploaded_file.name}' uploaded successfully for {student['name']}!")
                st.rerun()

    with tab2:
        st.subheader("👀 View Student Documents")

        if not documents:
            st.info("No documents uploaded yet.")
            return

        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            student_filter = st.selectbox("Filter by Student", ["All Students"] + [f"{s['roll_no']} - {s['name']}" for s in students], key="view_doc_student_filter")
        with col2:
            type_filter = st.selectbox("Filter by Type", ["All Types"] + list(set(d["document_type"] for d in documents)), key="view_doc_type_filter")
        with col3:
            search_term = st.text_input("Search documents", "", key="view_doc_search")

        # Apply filters
        filtered_docs = documents.copy()

        if student_filter != "All Students":
            roll_no = student_filter.split(" - ")[0]
            filtered_docs = [d for d in filtered_docs if d["roll_no"] == roll_no]

        if type_filter != "All Types":
            filtered_docs = [d for d in filtered_docs if d["document_type"] == type_filter]

        if search_term:
            filtered_docs = [d for d in filtered_docs if search_term.lower() in d["description"].lower() or search_term.lower() in d["original_filename"].lower()]

        if filtered_docs:
            st.subheader(f"📋 Documents ({len(filtered_docs)} found)")

            # Display documents
            for doc in filtered_docs:
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

                    with col1:
                        st.write(f"**{doc['student_name']}** ({doc['roll_no']})")

                    with col2:
                        st.write(f"**{doc['document_type']}**")
                        if doc['description']:
                            st.caption(doc['description'])

                    with col3:
                        st.write(f"📅 {doc['upload_date']}")
                        st.caption(f"📎 {doc['original_filename']}")

                    with col4:
                        file_path = os.path.join("documents", doc["filename"])
                        if os.path.exists(file_path):
                            with open(file_path, "rb") as f:
                                file_data = f.read()
                            st.download_button(
                                label="📥 Download",
                                data=file_data,
                                file_name=doc["original_filename"],
                                mime="application/octet-stream",
                                key=f"download_{doc['id']}"
                            )
                        else:
                            st.error("File not found")

                    st.divider()
        else:
            st.info("No documents match the selected filters.")

    with tab3:
        st.subheader("🗑️ Delete Student Documents")

        if not documents:
            st.info("No documents available for deletion.")
            return

        # Select document to delete
        doc_options = {f"{d['id']}: {d['student_name']} ({d['roll_no']}) - {d['document_type']} - {d['original_filename']}": d for d in documents}
        selected_doc_key = st.selectbox("Select Document to Delete", list(doc_options.keys()), key="delete_doc_select")

        if selected_doc_key:
            selected_doc = doc_options[selected_doc_key]

            st.warning("**Document Details:**")
            st.write(f"- **Student:** {selected_doc['student_name']} ({selected_doc['roll_no']})")
            st.write(f"- **Type:** {selected_doc['document_type']}")
            st.write(f"- **File:** {selected_doc['original_filename']}")
            st.write(f"- **Uploaded:** {selected_doc['upload_date']}")
            if selected_doc['description']:
                st.write(f"- **Description:** {selected_doc['description']}")

            # Confirmation
            confirm = st.checkbox("I confirm I want to delete this document", key="confirm_delete_doc")

            if st.button("Delete Document", type="primary", disabled=not confirm, key="delete_doc_btn"):
                # Remove file
                file_path = os.path.join("documents", selected_doc["filename"])
                if os.path.exists(file_path):
                    os.remove(file_path)

                # Remove from documents list
                documents.remove(selected_doc)

                # Save updated documents
                with open("documents.json", "w", encoding='utf-8') as f:
                    json.dump(documents, f, indent=4)

                st.success(f"✅ Document '{selected_doc['original_filename']}' deleted successfully!")
                st.rerun()






# ------------------- Core Functionalities -------------------
def add_student(name: str, roll_no: str, marks: float) -> None:
    students = load_students()

    # Validation
    if not name.strip():
        st.error("Name cannot be empty!")
        return
    if not roll_no.strip():
        st.error("Roll number cannot be empty!")
        return
    if marks < 0 or marks > 100:
        st.error("Marks must be between 0 and 100!")
        return

    # Check for duplicates
    for student in students:
        if student["roll_no"] == roll_no.strip():
            st.warning(f"⚠️ Roll number {roll_no} already exists for student: {student['name']}")
            return

    # Add student
    students.append({
        "name": name.strip(),
        "roll_no": roll_no.strip(),
        "marks": float(marks),
        "grade": calculate_grade(marks),
    })

    save_students(students)
    st.session_state.last_action = "add"
    st.session_state.action_message = f"✅ Student '{name}' added successfully!"
    st.success(st.session_state.action_message)
    st.balloons()


def upload_file(uploaded_file: Any) -> None:
    if uploaded_file is None:
        return

    try:
        # Read file based on extension
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        elif uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            st.error("❌ Unsupported file type. Please upload .csv or .xlsx files.")
            return
    except Exception as e:
        st.error(f"❌ Failed to read file: {str(e)}")
        return

    # Check required columns
    required_columns = {"name", "roll_no", "marks"}
    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        st.error(f"❌ Missing required columns: {', '.join(missing)}")
        return

    # Clean and validate data
    df = df[["name", "roll_no", "marks"]].copy()
    df.dropna(inplace=True)

    # Convert marks to numeric
    df["marks"] = pd.to_numeric(df["marks"], errors='coerce')
    df.dropna(subset=["marks"], inplace=True)

    # Filter valid marks
    df = df[(df["marks"] >= 0) & (df["marks"] <= 100)]

    if df.empty:
        st.warning("⚠️ No valid records found in the file.")
        return

    # Calculate grades
    df["grade"] = df["marks"].apply(calculate_grade)

    # Load existing students
    existing_students = load_students()
    existing_rolls = {s["roll_no"] for s in existing_students}

    # Process records
    added = 0
    skipped = 0
    errors = []

    for index, row in df.iterrows():
        roll_no = str(row["roll_no"]).strip()

        if roll_no in existing_rolls:
            skipped += 1
            continue

        try:
            existing_students.append({
                "name": str(row["name"]).strip(),
                "roll_no": roll_no,
                "marks": float(row["marks"]),
                "grade": row["grade"]
            })
            added += 1
        except Exception as e:
            errors.append(f"Row {index + 2}: {str(e)}")

    # Save and show results
    if added > 0:
        save_students(existing_students)
        st.session_state.last_action = "upload"
        st.session_state.action_message = f"📥 File processed successfully!\nAdded: {added} students | Skipped (duplicates): {skipped}"
        st.success(f"📥 File processed successfully!")
        st.info(f"**Results:**\n- Added: {added} students\n- Skipped (duplicates): {skipped}")
    else:
        st.warning("No new students were added.")

    if errors:
        with st.expander("Show Errors", expanded=False):
            for error in errors:
                st.error(error)


def download_csv() -> bytes:
    students = load_students()
    if not students:
        return b""
    df = pd.DataFrame(students)
    return df.to_csv(index=False).encode('utf-8')


def view_students() -> None:
    students = load_students()
    if students:
        # Add attendance and grades data to students
        for student in students:
            # Calculate attendance percentage
            student["attendance_percentage"] = calculate_attendance_percentage(student)

        df = pd.DataFrame(students)

        # Add search functionality
        st.subheader("🔍 Search Students")
        search_col1, search_col2 = st.columns([3, 1])
        with search_col1:
            search_term = st.text_input("Search by Name or Roll Number", "", key="search_students")
        with search_col2:
            search_by = st.selectbox("Search by", ["Both", "Name", "Roll No"], key="search_by")

        if search_term:
            if search_by == "Name":
                mask = df['name'].str.contains(search_term, case=False, na=False)
            elif search_by == "Roll No":
                mask = df['roll_no'].str.contains(search_term, case=False, na=False)
            else:  # Both
                mask = df['name'].str.contains(search_term, case=False, na=False) | \
                       df['roll_no'].str.contains(search_term, case=False, na=False)
            df = df[mask]

        # Display with formatting
        st.subheader(f"📋 Student Records ({len(df)} found)")

        if len(df) > 0:
            st.dataframe(
                df.style.format({'marks': '{:.2f}', 'attendance_percentage': '{:.1f}%'}),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "name": "Name",
                    "roll_no": "Roll No",
                    "marks": "Marks",
                    "grade": "Grade",
                    "attendance_percentage": "Attendance %"
                }
            )

            # Show summary
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Students", len(df))
            with col2:
                avg_marks = df['marks'].mean() if not df.empty else 0
                st.metric("Average Marks", f"{avg_marks:.2f}")
            with col3:
                top_grade = df['grade'].value_counts().idxmax() if not df.empty else "N/A"
                st.metric("Most Common Grade", top_grade)
            with col4:
                avg_attendance = df['attendance_percentage'].mean() if not df.empty else 0
                st.metric("Average Attendance", f"{avg_attendance:.1f}%")
        else:
            st.info("No students found matching your search.")
    else:
        st.info("📭 No student records found.")


def update_student_marks() -> None:
    st.subheader("✏️ Update Student Marks")

    students = load_students()
    if not students:
        st.info("No students to update.")
        return

    # Select student from dropdown
    student_options = {f"{s['roll_no']} - {s['name']}": s['roll_no'] for s in students}
    selected = st.selectbox("Select Student", list(student_options.keys()), key="select_update_student")

    if selected:
        roll_no = student_options[selected]

        # Find current marks
        current_student = next((s for s in students if s["roll_no"] == roll_no), None)
        if current_student:
            current_marks = current_student["marks"]
            current_grade = current_student["grade"]

            st.info(
                f"**Current Details:**\n- Name: {current_student['name']}\n- Roll No: {roll_no}\n- Current Marks: **{current_marks}**\n- Current Grade: **{current_grade}**")

            # Input for new marks
            col1, col2 = st.columns(2)
            with col1:
                new_marks = st.number_input("New Marks", 0.0, 100.0, float(current_marks), 0.5, key="new_marks_input")
            with col2:
                if new_marks != current_marks:
                    new_grade = calculate_grade(new_marks)
                    st.info(f"**New Grade:** {new_grade}")

            if st.button("Update Marks", type="primary", key="update_marks_button"):
                if new_marks != current_marks:
                    current_student["marks"] = new_marks
                    current_student["grade"] = calculate_grade(new_marks)
                    save_students(students)
                    st.session_state.last_action = "update"
                    st.session_state.action_message = f"✅ Updated {current_student['name']}'s marks to {new_marks} (Grade: {current_student['grade']})"
                    st.success(st.session_state.action_message)
                    st.rerun()
                else:
                    st.info("Marks unchanged.")


def delete_student() -> None:
    st.subheader("🗑️ Delete Student")

    students = load_students()
    if not students:
        st.info("No students to delete.")
        return

    # Select student from dropdown
    student_options = {f"{s['roll_no']} - {s['name']} (Marks: {s['marks']}, Grade: {s['grade']})": s for s in students}
    selected_display = st.selectbox("Select Student to Delete", list(student_options.keys()),
                                    key="select_delete_student")

    if selected_display:
        selected_student = student_options[selected_display]
        roll_no = selected_student["roll_no"]

        # Display student info
        st.warning(
            f"**Selected Student:**\n- Name: {selected_student['name']}\n- Roll No: {roll_no}\n- Marks: {selected_student['marks']}\n- Grade: {selected_student['grade']}")

        # Confirmation
        confirm = st.checkbox("I confirm I want to delete this student", key="confirm_delete_checkbox")

        if st.button("Delete Student", type="primary", disabled=not confirm, key="delete_student_button"):
            new_students = [s for s in students if s["roll_no"] != roll_no]
            save_students(new_students)
            st.session_state.last_action = "delete"
            st.session_state.action_message = f"✅ Student '{selected_student['name']}' deleted successfully!"
            st.success(st.session_state.action_message)
            st.rerun()


def show_statistics() -> None:
    students = load_students()
    if not students:
        st.info("No data to display.")
        return

    df = pd.DataFrame(students)

    # Key metrics
    st.subheader("📊 Key Statistics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Students", len(df))
    with col2:
        avg_marks = df['marks'].mean()
        st.metric("Average Marks", f"{avg_marks:.2f}")
    with col3:
        highest = df['marks'].max()
        st.metric("Highest Marks", f"{highest:.2f}")
    with col4:
        lowest = df['marks'].min()
        st.metric("Lowest Marks", f"{lowest:.2f}")

    # Pass/Fail Statistics
    st.subheader("📈 Pass/Fail Statistics")
    df['status'] = df['grade'].apply(lambda x: 'Pass' if x != 'F' else 'Fail')
    status_counts = df['status'].value_counts()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Passing Students", f"{status_counts.get('Pass', 0)}")
    with col2:
        st.metric("Failing Students", f"{status_counts.get('Fail', 0)}")

    # Grade distribution
    st.subheader("📊 Grade Distribution")
    grade_counts = df['grade'].value_counts().sort_index()

    col1, col2 = st.columns([2, 1])
    with col1:
        st.bar_chart(grade_counts)
    with col2:
        st.dataframe(grade_counts.rename('Count'), use_container_width=True)

    # Top performers
    st.subheader("🏆 Top 5 Performers")
    top_students = df.nlargest(5, 'marks')[['name', 'roll_no', 'marks', 'grade']]
    st.dataframe(top_students, use_container_width=True, hide_index=True)

    # Bottom performers
    st.subheader("📉 Bottom 5 Performers")
    bottom_students = df.nsmallest(5, 'marks')[['name', 'roll_no', 'marks', 'grade']]
    st.dataframe(bottom_students, use_container_width=True, hide_index=True)


def show_timetable() -> None:
    st.header("📅 Timetable and Scheduling")

    timetable_data = load_data("timetable.json")
    if not timetable_data:
        st.info("No timetable data available.")
        return

    df = pd.DataFrame(timetable_data)

    # Display timetable overview
    st.subheader("📋 Class Schedule Overview")
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "course_id": "Course ID",
            "day": "Day",
            "time": "Time",
            "room": "Room"
        }
    )

    # Group by day for better visualization
    st.subheader("📅 Schedule by Day")
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    for day in days:
        day_schedule = df[df['day'] == day]
        if not day_schedule.empty:
            with st.expander(f"📅 {day}", expanded=False):
                st.dataframe(
                    day_schedule[['course_id', 'time', 'room']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "course_id": "Course",
                        "time": "Time Slot",
                        "room": "Location"
                    }
                )

    # Summary statistics
    st.subheader("📅 Schedule Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Classes", len(df))
    with col2:
        unique_courses = df['course_id'].nunique()
        st.metric("Unique Courses", unique_courses)
    with col3:
        unique_rooms = df['room'].nunique()
        st.metric("Classrooms Used", unique_rooms)





def search_and_query() -> None:
    st.header("🔍 Search and Query")

    # Select data source
    data_source = st.selectbox(
        "Select data to search:",
        ["Students", "Courses", "Timetable"],
        key="search_data_source"
    )

    if data_source == "Students":
        search_students()
    elif data_source == "Courses":
        search_courses()
    elif data_source == "Timetable":
        search_timetable()


def search_students() -> None:
    st.subheader("👨‍🎓 Search Students")

    students = load_students()
    if not students:
        st.info("No student records found.")
        return

    df = pd.DataFrame(students)

    # Search options
    col1, col2 = st.columns([2, 1])
    with col1:
        search_term = st.text_input("Search term (name, roll number)", "", key="search_students_term")
    with col2:
        search_field = st.selectbox(
            "Search in:",
            ["All Fields", "Name", "Roll Number"],
            key="search_students_field"
        )

    # Advanced filters
    with st.expander("Advanced Filters", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            grade_filter = st.multiselect("Filter by Grade", sorted(df['grade'].unique()), key="grade_filter")
        with col2:
            min_marks = st.number_input("Min Marks", 0.0, 100.0, 0.0, key="min_marks")
            max_marks = st.number_input("Max Marks", 0.0, 100.0, 100.0, key="max_marks")
        with col3:
            status_filter = st.multiselect("Filter by Status", ["Pass", "Fail"], key="status_filter")

    # Apply filters
    filtered_df = df.copy()

    # Text search
    if search_term:
        if search_field == "All Fields":
            mask = df['name'].astype(str).str.contains(search_term, case=False, na=False) | \
                   df['roll_no'].astype(str).str.contains(search_term, case=False, na=False)
            filtered_df = df[mask]
        else:
            field_map = {
                "Name": "name",
                "Roll Number": "roll_no"
            }
            field = field_map[search_field]
            filtered_df = df[df[field].astype(str).str.contains(search_term, case=False, na=False)]

    # Grade filter
    if grade_filter:
        filtered_df = filtered_df[filtered_df['grade'].isin(grade_filter)]

    # Marks range
    if min_marks > 0 or max_marks < 100:
        filtered_df = filtered_df[(filtered_df['marks'] >= min_marks) & (filtered_df['marks'] <= max_marks)]

    # Status filter
    if status_filter:
        status_map = {"Pass": lambda x: x != 'F', "Fail": lambda x: x == 'F'}
        mask = False
        for status in status_filter:
            mask = mask | filtered_df['grade'].apply(status_map[status])
        filtered_df = filtered_df[mask]

    # Display results
    st.subheader(f"📋 Search Results ({len(filtered_df)} found)")

    if len(filtered_df) > 0:
        # Select columns to display
        display_cols = st.multiselect(
            "Select columns to display:",
            ['name', 'roll_no', 'marks', 'grade'],
            default=['name', 'roll_no', 'marks', 'grade'],
            key="display_cols_students"
        )

        st.dataframe(
            filtered_df[display_cols].style.format({'marks': '{:.2f}'}),
            use_container_width=True,
            hide_index=True
        )

        # Summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Found", len(filtered_df))
        with col2:
            avg_marks = filtered_df['marks'].mean()
            st.metric("Average Marks", f"{avg_marks:.2f}")
        with col3:
            if not filtered_df.empty:
                top_grade = filtered_df['grade'].value_counts().idxmax()
                st.metric("Most Common Grade", top_grade)
    else:
        st.info("No students match your search criteria.")


def search_courses() -> None:
    st.subheader("📚 Search Courses")

    courses = load_data("courses.json")
    if not courses:
        st.info("No course records found.")
        return

    df = pd.DataFrame(courses)

    # Search options
    col1, col2 = st.columns([2, 1])
    with col1:
        search_term = st.text_input("Search term (course name, ID, instructor, etc.)", "", key="search_courses_term")
    with col2:
        search_field = st.selectbox(
            "Search in:",
            ["All Fields", "Course ID", "Course Name", "Instructor"],
            key="search_courses_field"
        )

    # Advanced filters
    with st.expander("Advanced Filters", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            min_credits = st.number_input("Min Credits", 0, 10, 0, key="min_credits")
            max_credits = st.number_input("Max Credits", 0, 10, 10, key="max_credits")
        with col2:
            instructor_filter = st.multiselect("Filter by Instructor", sorted(df['instructor'].unique()), key="instructor_filter")

    # Apply filters
    filtered_df = df.copy()

    # Text search
    if search_term:
        if search_field == "All Fields":
            mask = False
            for col in ['course_id', 'course_name', 'instructor', 'description']:
                if col in df.columns:
                    mask = mask | df[col].astype(str).str.contains(search_term, case=False, na=False)
            filtered_df = df[mask]
        else:
            field_map = {
                "Course ID": "course_id",
                "Course Name": "course_name",
                "Instructor": "instructor"
            }
            field = field_map[search_field]
            if field in df.columns:
                filtered_df = df[df[field].astype(str).str.contains(search_term, case=False, na=False)]

    # Credits range
    if min_credits > 0 or max_credits < 10:
        filtered_df = filtered_df[(filtered_df['credits'] >= min_credits) & (filtered_df['credits'] <= max_credits)]

    # Instructor filter
    if instructor_filter:
        filtered_df = filtered_df[filtered_df['instructor'].isin(instructor_filter)]

    # Display results
    st.subheader(f"📋 Search Results ({len(filtered_df)} found)")

    if len(filtered_df) > 0:
        # Select columns to display
        display_cols = st.multiselect(
            "Select columns to display:",
            ['course_id', 'course_name', 'instructor', 'credits', 'max_students', 'description'],
            default=['course_id', 'course_name', 'instructor', 'credits'],
            key="display_cols_courses"
        )

        st.dataframe(
            filtered_df[display_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "course_id": "Course ID",
                "course_name": "Course Name",
                "instructor": "Instructor",
                "credits": "Credits",
                "max_students": "Max Students",
                "description": "Description"
            }
        )

        # Summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Courses", len(filtered_df))
        with col2:
            avg_credits = filtered_df['credits'].mean()
            st.metric("Average Credits", f"{avg_credits:.1f}")
        with col3:
            total_capacity = filtered_df['max_students'].sum()
            st.metric("Total Capacity", total_capacity)
    else:
        st.info("No courses match your search criteria.")


def search_timetable() -> None:
    st.subheader("📅 Search Timetable")

    timetable = load_data("timetable.json")
    if not timetable:
        st.info("No timetable records found.")
        return

    df = pd.DataFrame(timetable)

    # Search options
    col1, col2 = st.columns([2, 1])
    with col1:
        search_term = st.text_input("Search term (course ID, day, room, etc.)", "", key="search_timetable_term")
    with col2:
        search_field = st.selectbox(
            "Search in:",
            ["All Fields", "Course ID", "Day", "Room"],
            key="search_timetable_field"
        )

    # Advanced filters
    with st.expander("Advanced Filters", expanded=False):
        day_filter = st.multiselect("Filter by Day", sorted(df['day'].unique()), key="day_filter")

    # Apply filters
    filtered_df = df.copy()

    # Text search
    if search_term:
        if search_field == "All Fields":
            mask = False
            for col in ['course_id', 'day', 'time', 'room']:
                mask = mask | df[col].astype(str).str.contains(search_term, case=False, na=False)
            filtered_df = df[mask]
        else:
            field_map = {
                "Course ID": "course_id",
                "Day": "day",
                "Room": "room"
            }
            field = field_map[search_field]
            filtered_df = df[df[field].astype(str).str.contains(search_term, case=False, na=False)]

    # Day filter
    if day_filter:
        filtered_df = filtered_df[filtered_df['day'].isin(day_filter)]

    # Display results
    st.subheader(f"📋 Search Results ({len(filtered_df)} found)")

    if len(filtered_df) > 0:
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "course_id": "Course ID",
                "day": "Day",
                "time": "Time",
                "room": "Room"
            }
        )

        # Summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Classes", len(filtered_df))
        with col2:
            unique_courses = filtered_df['course_id'].nunique()
            st.metric("Unique Courses", unique_courses)
        with col3:
            unique_rooms = filtered_df['room'].nunique()
            st.metric("Unique Rooms", unique_rooms)
    else:
        st.info("No timetable entries match your search criteria.")


# ------------------- Reset Function -------------------
def reset_all_data() -> None:
    """Reset all student data with confirmation"""
    if st.session_state.show_reset_modal:
        st.warning("⚠️ CONFIRM DATA RESET")
        st.error("This action will delete ALL student records permanently!")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes, Reset All Data", type="primary", key="confirm_reset_yes"):
                save_students([])  # Save empty list to file
                st.session_state.show_reset_modal = False
                st.session_state.last_action = "reset"
                st.session_state.action_message = "✅ All student data has been reset successfully!"
                st.success(st.session_state.action_message)
                time.sleep(1)
                st.rerun()
        with col2:
            if st.button("❌ Cancel", key="confirm_reset_no"):
                st.session_state.show_reset_modal = False
                st.info("Reset cancelled.")
                st.rerun()


# ------------------- Streamlit UI -------------------

def main() -> None:

    # Initialize session state
    init_session_state()
    init_auth_session_state()

    # Check authentication
    if not require_auth():
        return

    # Page configuration
    st.set_page_config(
        page_title="Student Management System",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        padding: 1rem;
        margin-bottom: 2rem;
    }
    .stButton>button {
        border-radius: 5px;
        font-weight: bold;
    }
    .success-box {
        background-color: #D4EDDA;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #28A745;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #FFF3CD;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #FFC107;
        margin: 1rem 0;
    }
    .danger-box {
        background-color: #F8D7DA;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #DC3545;
        margin: 1rem 0;
    }
    body {
        background-image: url('background.png');
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("<h1 class='main-header'>🎓 International Student Information Management System</h1>", unsafe_allow_html=True)

    # Show last action message if exists
    if st.session_state.action_message:
        if st.session_state.last_action == "reset":
            st.markdown(f'<div class="danger-box">{st.session_state.action_message}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="success-box">{st.session_state.action_message}</div>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("📋 Navigation")
        menu_option = st.selectbox(
            "Choose an action:",
            ["🏠 Admin Dashboard", "👨‍🎓 Student Profile Management", "📚 Course Registration", "📝 Grade Management", "📤 Upload File", "📅 Timetable and Scheduling", "🔍 Search and Query", "📋 Attendance Tracking", "📈 Student Performance Analytics", "📄 Document Management"]
        )

        # Student Profile Management sub-options
        if menu_option == "👨‍🎓 Student Profile Management":
            student_option = st.radio(
                "Student operations:",
                ["➕ Add Student", "👀 View Students", "🗑️ Delete Student"],
                key="student_radio"
            )
            menu_option = student_option

        st.divider()

        # Reset all data option
        st.header("⚙️ Settings")

        # Mobile access option
        if st.button("📱 Mobile Access", type="secondary", key="mobile_access_button"):
            st.info("📱 Mobile access is enabled. This system is optimized for mobile browsers and can be accessed from smartphones and tablets.")

        # Show reset modal if triggered
        if st.session_state.show_reset_modal:
            reset_all_data()
        else:
            if st.button("🔄 Reset All Data", type="secondary", key="reset_button"):
                st.session_state.show_reset_modal = True
                st.rerun()

        st.divider()

        # System Info
        st.header("ℹ️ System Info")
        students = load_students()
        st.info(f"**Total Students:** {len(students)}")
        if students:
            df = pd.DataFrame(students)
            avg_marks = df['marks'].mean()
            st.info(f"**Average Marks:** {avg_marks:.2f}")

        st.divider()
        st.caption("Can be acceessed with mobile, Developed by Mazen ❤️")



    # Main content based on menu selection
    if menu_option == "🏠 Admin Dashboard":
        st.header("🏢 Admin Dashboard Overview")

        students = load_students()
        if students:
            df = pd.DataFrame(students)

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📈 Quick Stats")

                # Create metrics
                total_students = len(df)
                avg_marks = df['marks'].mean()
                pass_rate = (df['grade'] != 'F').sum() / len(df) * 100
                top_grade = df['grade'].value_counts().idxmax()

                st.metric("Total Students", total_students)
                st.metric("Average Marks", f"{avg_marks:.2f}")
                st.metric("Pass Rate", f"{pass_rate:.1f}%")
                st.metric("Most Common Grade", top_grade)

                # Quick actions
                st.subheader("🚀 Quick Actions")
                if st.button("➕ Add New Student", use_container_width=True):
                    st.session_state.menu_option = "➕ Add Student"
                    st.rerun()
                if st.button("📤 Upload File", use_container_width=True):
                    st.session_state.menu_option = "📤 Upload File"
                    st.rerun()

            with col2:
                st.subheader("📋 Recent Students")
                # Show last 5 added students
                recent = df.tail(5)[['name', 'roll_no', 'marks', 'grade']]
                if not recent.empty:
                    for idx, (_, student) in enumerate(recent.iterrows()):
                        with st.container():
                            col_a, col_b = st.columns([3, 1])
                            with col_a:
                                st.write(f"**{student['name']}** (Roll: {student['roll_no']})")
                            with col_b:
                                st.write(f"**{student['marks']}** ({student['grade']})")
                            if idx < len(recent) - 1:
                                st.divider()
                else:
                    st.info("No recent students to display.")

            st.divider()
            st.subheader("📊 Grade Distribution")
            st.bar_chart(df['grade'].value_counts())



            # File location info
            st.divider()
            st.caption(f"Data file location: `{os.path.abspath(DATA_FILE)}`")
        else:
            st.info("👋 Welcome to International Student Information Management System!")
            st.info("📌 Start by adding your first student or uploading a file.")

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("➕ Add First Student")
                with st.form("quick_add_form"):
                    name = st.text_input("Student Name")
                    roll_no = st.text_input("Roll Number")
                    marks = st.slider("Marks", 0, 100, 75)
                    if st.form_submit_button("Add Student"):
                        if name and roll_no:
                            add_student(name, roll_no, marks)

            with col2:
                st.subheader("📤 Or Upload File")
                uploaded_file = st.file_uploader("Upload CSV/Excel", type=['csv', 'xlsx'])
                if uploaded_file:
                    upload_file(uploaded_file)

    elif menu_option == "➕ Add Student":
        st.header("➕ Add New Student")

        with st.form("add_student_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Full Name", placeholder="Enter student's full name", key="add_name")
                roll_no = st.text_input("Roll Number", placeholder="Enter unique roll number", key="add_roll_no")

            with col2:
                marks = st.number_input("Marks", min_value=0.0, max_value=100.0,
                                        value=0.0, step=0.5, format="%.2f", key="add_marks")
                grade_display = st.empty()
                if marks > 0:
                    grade = calculate_grade(marks)
                    grade_display.info(f"**Grade:** {grade}")

            col3, col4 = st.columns(2)
            with col3:
                submitted = st.form_submit_button("Add Student", type="primary", use_container_width=True)
            with col4:
                if st.form_submit_button("Clear", type="secondary", use_container_width=True):
                    st.rerun()

            if submitted:
                if name.strip() and roll_no.strip():
                    add_student(name, roll_no, marks)
                else:
                    st.error("❌ Please fill in all required fields!")

    elif menu_option == "📤 Upload File":
        st.header("📤 Upload Student Data")

        st.info("""
        **Upload a CSV or Excel file with the following columns:**
        - `name`: Student's full name
        - `roll_no`: Unique roll number
        - `marks`: Numeric marks (0-100)

        **Example CSV format:**
        ```
        name,roll_no,marks
        John Doe,001,85
        Jane Smith,002,92
        ```
        """)

        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['csv', 'xlsx'],
            help="Upload CSV or Excel files only",
            key="file_uploader"
        )

        if uploaded_file:
            with st.spinner("Processing file..."):
                upload_file(uploaded_file)

        # Sample file download
        st.divider()
        st.subheader("📋 Sample Files")

        col1, col2 = st.columns(2)
        with col1:
            # Sample CSV content
            sample_csv = "name,roll_no,marks\nJohn Doe,001,85\nJane Smith,002,92\nBob Johnson,003,78"
            st.download_button(
                label="📥 Download Sample CSV",
                data=sample_csv,
                file_name="sample_students.csv",
                mime="text/csv"
            )

        with col2:
            # Create sample Excel file
            import io
            sample_df = pd.DataFrame({
                'name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
                'roll_no': ['001', '002', '003'],
                'marks': [85, 92, 78]
            })
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                sample_df.to_excel(writer, index=False, sheet_name='Students')
            excel_data = excel_buffer.getvalue()

            st.download_button(
                label="📥 Download Sample Excel",
                data=excel_data,
                file_name="sample_students.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    elif menu_option == "👀 View Students":
        view_students()

    elif menu_option == "✏️ Update Marks":
        update_student_marks()

    elif menu_option == "🗑️ Delete Student":
        delete_student()

    elif menu_option == "📅 Timetable and Scheduling":
        show_timetable()

    elif menu_option == "🔍 Search and Query":
        search_and_query()

    elif menu_option == "📋 Attendance Tracking":
        attendance_tracking()

    elif menu_option == "📚 Course Registration":
        course_registration()

    elif menu_option == "📝 Grade Management":
        grade_management()

    elif menu_option == "📈 Student Performance Analytics":
        student_performance_analytics()

    elif menu_option == "📄 Document Management":
        document_management()




# ------------------- Run the app -------------------
if __name__ == "__main__":
    main()


