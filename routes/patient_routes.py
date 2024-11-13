from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import mysql
import pymysql

from routes.admin_classes_routes import manage_notification

# Create the Blueprint for patient-related routes
patient_bp = Blueprint('patient', __name__, url_prefix='/patient')

# Patient Dashboard
@patient_bp.route('/dashboard')
def patient_dashboard():
    """Displays the patient's dashboard."""
    if 'role' not in session or session['role'] != 'patient':
        return redirect(url_for('auth.login'))  # Redirect to login if not authenticated as patient

    user_id = session.get('user_id')

    # Get the patient's information and notifications from the database
    cur = mysql.connection.cursor(pymysql.cursors.DictCursor)

    try:
        # Fetch the patient's information
        cur.execute("SELECT * FROM patients WHERE user_id = %s", (user_id,))
        patient = cur.fetchone()
        if not patient:
            flash("Patient not found!", "danger")
            return redirect(url_for('home'))

        # Fetch unread notifications for the patient
        cur.execute("""
            SELECT notification_id, notification_type, message, notification_status, notification_date
            FROM notifications
            WHERE patient_id = %s AND notification_status != 'Read'
            ORDER BY notification_date DESC
            LIMIT 5
        """, (patient['patient_id'],))
        notifications = cur.fetchall()
    except pymysql.err.ProgrammingError as e:
        print("Error:", e)
        flash("An error occurred while fetching data.", "danger")
        return redirect(url_for('home'))
    finally:
        cur.close()

    return render_template('patient_dashboard.html', patient=patient, notifications=notifications)


@patient_bp.route('/mark_notification_as_read/<int:notification_id>', methods=['POST'])
def mark_notification_as_read(notification_id):
    """Marks a notification as read."""
    manage_notification(action='mark_as_read', notification_id=notification_id)
    return redirect(url_for('patient.patient_dashboard'))


# Edit Patient Profile
@patient_bp.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    """Allows patients to edit their profile information, except for mobility level."""
    if 'role' not in session or session['role'] != 'patient':
        return redirect(url_for('auth.login'))  # Redirect to login if not authenticated as patient

    user_id = session.get('user_id')

    if request.method == 'POST':
        # Retrieve form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        dob = request.form.get('dob')
        gender = request.form.get('gender')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        emergency_contact_name = request.form.get('emergency_contact_name')
        emergency_contact_phone = request.form.get('emergency_contact_phone')
        health_condition = request.form.get('health_condition')

        # Validate required fields
        if not first_name or not last_name or not email:
            flash("First Name, Last Name, and Email are required.", "danger")
            return redirect(url_for('patient.edit_profile'))

        # Update the database
        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                UPDATE patients
                SET first_name = %s, last_name = %s, dob = %s, gender = %s, phone = %s,
                    email = %s, address = %s, emergency_contact_name = %s,
                    emergency_contact_phone = %s, health_condition = %s
                WHERE user_id = %s
            """, (first_name, last_name, dob, gender, phone, email, address,
                  emergency_contact_name, emergency_contact_phone, health_condition,
                  user_id))
            mysql.connection.commit()
            flash("Profile updated successfully!", "success")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
        finally:
            cur.close()

        return redirect(url_for('patient.patient_dashboard'))

    # Retrieve current profile info
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM patients WHERE user_id = %s", (user_id,))
    patient = cur.fetchone()
    cur.close()

    return render_template('edit_profile.html', patient=patient)


# View Patient Appointments
@patient_bp.route('/view_appointments')
def view_appointments():
    """Displays all booked classes for the patient."""
    if 'role' not in session or session['role'] != 'patient':
        return redirect(url_for('auth.login'))

    user_id = session.get('user_id')

    # Retrieve the patient's booked classes using patient_classes
    cur = mysql.connection.cursor(pymysql.cursors.DictCursor)
    try:
        cur.execute("""
            SELECT c.class_name, c.description, c.class_date, c.start_time, c.end_time, 
                   c.location, c.instructor
            FROM classes c
            INNER JOIN patient_classes pc ON c.class_id = pc.class_id
            WHERE pc.patient_id = %s
            ORDER BY c.class_date ASC, c.start_time ASC
        """, (user_id,))
        booked_classes = cur.fetchall()

        # Debug: Log fetched classes
        print(f"Booked classes for patient {user_id}: {booked_classes}")

    except Exception as e:
        flash(f"Error retrieving booked classes: {e}", "danger")
        print(f"Error retrieving booked classes: {e}")
        booked_classes = []
    finally:
        cur.close()

    return render_template('patient_view_appointments.html', appointments=booked_classes)






# View Available Classes
@patient_bp.route('/view_classes', methods=['GET'])
def view_classes():
    """Displays a list of available classes."""
    if 'role' not in session or session['role'] != 'patient':
        return redirect(url_for('auth.login'))

    user_id = session.get('user_id')

    # Fetch classes and check if the patient is enrolled
    cur = mysql.connection.cursor(pymysql.cursors.DictCursor)
    cur.execute("""
        SELECT c.*,
               CASE WHEN pc.patient_id IS NOT NULL THEN TRUE ELSE FALSE END AS booked,
               c.capacity AS remaining_capacity
        FROM classes c
        LEFT JOIN patient_classes pc ON c.class_id = pc.class_id AND pc.patient_id = %s
    """, (user_id,))
    classes = cur.fetchall()
    cur.close()

    return render_template('patient_view_classes.html', classes=classes)



# Book a Class
@patient_bp.route('/book_class', methods=['POST'])
def book_class():
    """Allows a patient to book a class and decreases the class capacity."""
    if 'role' not in session or session['role'] != 'patient':
        flash("Unauthorized access. Please log in as a patient.", "danger")
        return redirect(url_for('auth.login'))

    try:
        patient_id = session.get('user_id')
        class_id = request.form.get('class_id')

        # Debugging: Log patient_id and class_id
        print(f"Attempting to book: patient_id={patient_id}, class_id={class_id}")

        if not patient_id or not class_id:
            flash("Invalid request. Missing patient or class information.", "danger")
            return redirect(url_for('patient.view_classes'))

        cur = mysql.connection.cursor()

        # Check if the class is already booked
        cur.execute("SELECT * FROM patient_classes WHERE patient_id = %s AND class_id = %s", (patient_id, class_id))
        existing_booking = cur.fetchone()

        if existing_booking:
            flash("You have already booked this class.", "info")
            print(f"Class {class_id} already booked by patient {patient_id}")
            return redirect(url_for('patient.view_classes'))

        # Check class capacity
        cur.execute("SELECT capacity FROM classes WHERE class_id = %s", (class_id,))
        class_info = cur.fetchone()

        if not class_info or class_info['capacity'] <= 0:
            flash("The class is fully booked.", "danger")
            return redirect(url_for('patient.view_classes'))

        # Insert the booking into the database
        cur.execute("INSERT INTO patient_classes (patient_id, class_id) VALUES (%s, %s)", (patient_id, class_id))
        cur.execute("UPDATE classes SET capacity = capacity - 1 WHERE class_id = %s", (class_id,))
        mysql.connection.commit()

        flash("Class booked successfully!", "success")
        print(f"Class {class_id} successfully booked by patient {patient_id}")

    except Exception as e:
        flash(f"An error occurred: {e}", "danger")
        print(f"Error booking class: {e}")
    finally:
        cur.close()

    return redirect(url_for('patient.view_classes'))







# Cancel a Class Booking
@patient_bp.route('/cancel_booking', methods=['POST'])
def cancel_booking():
    """Allows a patient to cancel a class booking and increases the class capacity."""
    if 'role' not in session or session['role'] != 'patient':
        return redirect(url_for('auth.login'))

    patient_id = session.get('user_id')
    class_id = request.form.get('class_id')

    cur = mysql.connection.cursor()
    try:
        # Remove the booking from the database and increase class capacity
        cur.execute("DELETE FROM patient_classes WHERE patient_id = %s AND class_id = %s", (patient_id, class_id))
        cur.execute("UPDATE classes SET capacity = capacity + 1 WHERE class_id = %s", (class_id,))
        mysql.connection.commit()
        flash("Class reservation canceled successfully!", "success")
    except Exception as e:
        flash(f"Error canceling reservation: {str(e)}", "danger")
    finally:
        cur.close()

    return redirect(url_for('patient.view_classes'))


# Track Symptoms
@patient_bp.route('/track_symptoms', methods=['GET', 'POST'])
def track_symptoms():
    """Allows patients to track symptoms and view their history."""
    if 'role' not in session or session['role'] != 'patient':
        return redirect(url_for('auth.login'))  # Redirect to login if not authenticated as patient

    user_id = session.get('user_id')

    if request.method == 'POST':
        symptom = request.form.get('symptom')
        severity = request.form.get('severity')
        notes = request.form.get('notes')
        start_date = request.form.get('start_date')

        # Validate inputs
        if not symptom or not severity or not start_date:
            flash("Symptom, severity, and start date are required.", "danger")
            return redirect(url_for('patient.track_symptoms'))

        # Insert the symptom into the database
        cur = mysql.connection.cursor(pymysql.cursors.DictCursor)
        try:
            cur.execute("""
                INSERT INTO symptoms (user_id, symptom, severity, notes, start_date, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (user_id, symptom, severity, notes, start_date))
            mysql.connection.commit()
            flash("Symptom tracked successfully!", "success")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
        finally:
            cur.close()

        return redirect(url_for('patient.track_symptoms'))

    # Retrieve symptom history for the patient
    cur = mysql.connection.cursor(pymysql.cursors.DictCursor)
    cur.execute("""
        SELECT symptom, severity, notes, start_date, created_at
        FROM symptoms
        WHERE user_id = %s
        ORDER BY start_date DESC
    """, (user_id,))
    symptom_history = cur.fetchall()
    cur.close()

    return render_template('patient_track_symptoms.html', symptom_history=symptom_history)


# Messages (Patient to Coach Communication)
@patient_bp.route('/messages', methods=['GET', 'POST'])
def messages():
    """Allows patients to view and send messages."""
    if 'role' not in session or session['role'] != 'patient':
        return redirect(url_for('auth.login'))  # Redirect to login if not authenticated as patient

    user_id = session.get('user_id')

    cur = mysql.connection.cursor(pymysql.cursors.DictCursor)

    if request.method == 'POST':
        coach_id = request.form['coach_id']
        message_content = request.form['message']

        # Validate inputs
        if not coach_id or not message_content:
            flash("Both coach and message content are required.", "danger")
            return redirect(url_for('patient.messages'))

        # Insert the message into the database
        try:
            cur.execute("""
                INSERT INTO messages (sender_id, receiver_id, message_content, sent_at)
                VALUES (%s, %s, %s, NOW())
            """, (user_id, coach_id, message_content))
            mysql.connection.commit()
            flash("Message sent successfully!", "success")
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")

    # Retrieve messages for the patient
    cur.execute("""
        SELECT messages.message_content, messages.sent_at,
               users.username AS sender
        FROM messages
        JOIN users ON messages.sender_id = users.user_id
        WHERE receiver_id = %s
        ORDER BY messages.sent_at DESC
    """, (user_id,))
    received_messages = cur.fetchall()

    # Fetch the list of coaches for messaging
    cur.execute("""
        SELECT user_id, username FROM users WHERE role = 'coach'
    """)
    coaches = cur.fetchall()
    cur.close()

    return render_template('patient_messages.html', messages=received_messages, coaches=coaches)
