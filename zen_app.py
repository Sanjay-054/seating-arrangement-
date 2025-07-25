from flask import Flask,render_template, request, redirect, url_for, send_from_directory
import sqlite3
from zen2 import run, write, missing, read, write_to_excel
import os
from werkzeug.security import generate_password_hash
import random

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Simulating a database with a list
generated_subjects = []

# Database connection function
def get_db_connection():
    conn = sqlite3.connect("room_details.db")
    conn.row_factory = sqlite3.Row
    return conn

# Route for home page
@app.route("/")
def home():
    return render_template("home.html")

# Route for about page
@app.route("/About")
def about():
    return render_template("about.html")

# Route for login page
@app.route("/login", methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email').strip()
        password = request.form.get('psw').strip()
        if email == "admin" and password == "admin":
            return redirect(url_for('admin'))
        elif email == "student" and password == "student":
            return redirect(url_for('student'))
        else:
            error = "INVALID DETAILS"
    return render_template("login.html", error=error)

# Route for register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('psw', '')
        confirm_password = request.form['psw-repeat']
        if not email or not password or not confirm_password:
            error = "All fields are required"
        elif password != confirm_password:
            error = "password do not match"
        else:
            hashed_password = generate_password_hash(password)
            conn = get_db_connection()
            conn.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed_password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
    return render_template('register.html', error=error)

# Route for contact page
@app.route("/contact", methods=['GET','POST'])
def contact():
    message= None
    first_name=last_name=subject=""
    if request.method == 'POST':
        first_name=request.form.get('firstname').strip()
        last_name=request.form.get('lastname').strip()
        subject=request.form.get('subject').strip()
        
    if not first_name or not last_name or not subject:
         message="all fields are required !"  
    else:
          print(f"Message from {first_name} {last_name}: {subject}")
          message = "Thank you! Your message has been received."
    return render_template("contact.html",message=message)

# Route for admin page
@app.route("/admin")
def admin():
    conn = get_db_connection()
    data = conn.execute("SELECT * FROM room").fetchall()
    conn.close()
    return render_template("admin.html", data=data)

# Route for student page
@app.route("/student")
def student():
    conn = get_db_connection()
    data = conn.execute("SELECT * FROM room").fetchall()
    conn.close()
    return render_template("student.html", data=data)

# Route for add room page
@app.route("/addroom", methods=['GET', 'POST'])
def addroom():
    data = None
    error = None
    if request.method == 'POST':
        room_no = request.form['room_no']
        row = request.form['row']
        col = request.form['col']
        seat = request.form['seat']
        conn = get_db_connection()
        if int(seat) <= int(row) * int(col):
            existing_room = conn.execute("SELECT * FROM room WHERE room_no = ?", (room_no,)).fetchone()
            if existing_room is None:
                conn.execute("INSERT INTO room (room_no, col, row, seat) VALUES (?, ?, ?, ?)", (room_no, col, row, seat))
                conn.commit()
                error = room_no + " is added"
            else:
                error = room_no + " is already exist"
        else:
            error = "Invalid number of seat"
        conn.close()
    return render_template("addroom.html", error=error, data=data)

# Route for generate page
@app.route("/Generate", methods=['GET', 'POST'])
def generate():
    conn = get_db_connection()
    room_no = conn.execute("SELECT room_no FROM room").fetchall()
    conn.close()
    room_no = [r[0] for r in room_no]

    if request.method == 'POST':
        form_data = request.form
        room_no = int(form_data.get('room', 0))
        session = form_data.get('session', 'N/A')
        
        # ✅ Get date and shift from the form
        date = form_data.get('date', 'N/A')  # Example format: YYYY-MM-DD
        shift = form_data.get('shift', 'N/A')  # Example: "Morning" or "Afternoon"

        subject_code_bca = form_data.get('subject_code_bca', 'N/A')
        subject_code_bsc = form_data.get('subject_code_bsc', 'N/A')
        subject_code_bcom = form_data.get('subject_code_bcom', 'N/A')
        subject_code_bba = form_data.get('subject_code_bba', 'N/A')

        bca_start, bca_end = int(form_data.get('bca_start', 0)), int(form_data.get('bca_end', 0))
        bsc_start, bsc_end = int(form_data.get('bsc_start', 0)), int(form_data.get('bsc_end', 0))
        bcom_start, bcom_end = int(form_data.get('bcom_start', 0)), int(form_data.get('bcom_end', 0))
        bba_start, bba_end = int(form_data.get('bba_start', 0)), int(form_data.get('bba_end', 0))

        r_missing = form_data.get('missing', '').strip()
        r_missing = [int(x) for x in r_missing.split() if x.isdigit()] if r_missing else []

        conn = get_db_connection()
        result = conn.execute("SELECT row, col, seat FROM room WHERE room_no = ?", (room_no,)).fetchone()
        conn.close()

        if not result:
            return "Error: Room not found", 400

        row, col, seat = result  

        def filter_students(start, end, missing_list):
            return [i for i in range(start, end + 1) if i not in missing_list]

        bca_list = filter_students(bca_start, bca_end, r_missing)
        bsc_list = filter_students(bsc_start, bsc_end, r_missing)
        bcom_list = filter_students(bcom_start, bcom_end, r_missing)
        bba_list = filter_students(bba_start, bba_end, r_missing)

        all_students = bca_list + bsc_list + bcom_list + bba_list
        random.shuffle(all_students)

        departments = {
            "BCA": bca_list,
            "BSc": bsc_list,
            "BCom": bcom_list,
            "BBA": bba_list,
        }
        active_departments = [key for key, lst in departments.items() if lst]
        num_departments = len(active_departments)

        chunk_size = len(all_students) // num_departments if num_departments > 0 else 1

        for idx, dept in enumerate(active_departments):
            start, end = idx * chunk_size, (idx + 1) * chunk_size
            departments[dept] = all_students[start:end]

        if remaining_students := all_students[num_departments * chunk_size:]:
            for i, student in enumerate(remaining_students):
                dept = active_departments[i % num_departments]
                departments[dept].append(student)

        data = run(
            departments.get("BCom", []), departments.get("BSc", []), 
            departments.get("BCA", []), departments.get("BBA", []),
            row, col, subject_code_bca, subject_code_bsc, subject_code_bcom, subject_code_bba
        )

        if not isinstance(data, dict) or "row" not in data or "col" not in data:
            return "Error: Invalid seating arrangement output", 500

        # ✅ Pass `date` and `shift` to write_to_excel
        filename = write_to_excel(data, room_no, session, date, shift)
        
        return send_from_directory(directory="static/excel", path=filename, as_attachment=True)

    return render_template("generate.html", room_no=room_no)

# Route for result page
@app.route('/result', methods=['GET', 'POST'])
def show_admin():
    data = None
    filename = None
    db_file = "room_details.db"
    excel_dir="static/excel"
    conn = get_db_connection()
    excel_dir = "static/excel"
    room_no = conn.execute("SELECT DISTINCT room_no,session FROM room").fetchall()
    session=list(set(row[1]for row in room_no))
    conn.close()
    session=["FN","AN"]
    if request.method == 'POST':
        room_no_selected = request.form.get('room_no')
        session_selected =request.form.get('session')
        if not room_no_selected or not session_selected:
            return "Error: Missing room number or session", 400  # Return error message
        data = read(room_no_selected,session_selected)
        data = data.to_html(classes="table table-stripped")
        filename = f'/{excel_dir}/{room_no}.xlsx'
        filename = f'{excel_dir}/seating_{room_no}_{session}.xlsx'
        filename = f"static/excel/seating_{room_no_selected}_{session_selected}.xlsx"

    return render_template("show_result.html", data=data, room_no=room_no, filename=filename)

# Route for show page
@app.route('/show', methods=['GET', 'POST'])
def show_student():
    data = None
    filename = None
    db_file = "room_details.db"
    conn = get_db_connection()
    excel_dir = "static/excel"
    room_data = conn.execute("SELECT DISTINCT room_no FROM room").fetchall()
    conn.close()
    room_data=[r[0]for r in room_data]
    if request.method == 'POST':
        room_no = request.form['room_no']
        session=request.form['session']
        data=read(room_no,session)
        data=data.to_html(classes="table table-stripped")
    return render_template("show_result2.html", data=data, room_data=room_data)

# Route for delete page
@app.route('/delete/<int:id>', methods=['GET'])
def delete_room(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM room WHERE room_no = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/save/<id>', methods=['POST'])
def save_room(id):
    conn = get_db_connection()
    room_no=request.form.get('room_no')
    col = request.form.get('col')
    row = request.form.get('row')
    seat = request.form.get('seat')

    conn.execute(
        "UPDATE room SET col = ?, row = ?, seat = ? WHERE room_no = ?",
        (col, row, seat, room_no))
    conn.commit()
    conn.close()

    return redirect(url_for('admin')) 


# Route for edit page
@app.route('/edit/<id>', methods=['GET', 'POST'])
def edit_room(id):
    conn = get_db_connection()

    if request.method == 'POST':
        data = request.json
        room_no = data['room_no']
        row = data['row']
        col = data['col']
        seat = data['seat']

        conn.execute(
            "UPDATE room SET room_no = ?, col = ?, row = ?, seat = ? WHERE room_no = ?", 
            (room_no, col, row, seat, id)
        )
        conn.commit()
        conn.close()

        return redirect(url_for('admin'))
    

    data = conn.execute("SELECT * FROM room WHERE room_no = ?", (id,)).fetchone()
    conn.close()

    return render_template("edit_room.html", data=data)
if __name__ == "__main__":
    app.run(debug=True)

