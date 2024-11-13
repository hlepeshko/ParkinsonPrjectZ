import MySQLdb
import bcrypt
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import generate_password_hash
from app import mysql
from routes.auth_routes import is_valid_username, is_valid_email, is_strong_password


admin_classes_bp = Blueprint('admin_classes', __name__, url_prefix='/admin_classes')

@admin_classes_bp.route('/classes', methods=['GET', 'POST'])
def manage_classes():
    # Ensure the user is an admin
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("You must be an admin to access this page.", "warning")
        return redirect(url_for('auth.login'))

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Check if the request is for adding a class or registering a patient
    if request.method == 'POST':
        if 'add_class' in request.form:  # Adding a new class

            class_name = request.form['class_name']
            description = request.form['description']
            level = request.form['level']
            duration = request.form['duration']
            start_time = request.form['start_time']
            capacity = request.form['capacity']
            coach_id = request.form.get('coach_id') or None # Optional

            # Validate required fields
            if not class_name or not level or not duration or not start_time or not capacity:
                flash("Please fill in all required fields.", "danger")
                return redirect(url_for('admin_classes.manage_classes'))

            # Insert the new class with the selected coach
            try:
                cur.execute("""
                    INSERT INTO classes (class_name, description, level, duration, start_time, capacity, coach_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (class_name, description, level, duration, start_time, capacity, coach_id))
                mysql.connection.commit()
                flash("Class added successfully!", "success")
            except Exception as e:
                mysql.connection.rollback()
                flash("An error occurred while adding the class.", "danger")
                print("Error:", e)

        elif 'edit_class' in request.form:  # Editing an existing class
            class_id = request.form['class_id']
            class_name = request.form['class_name']
            description = request.form['description']
            level = request.form['level']
            duration = request.form['duration']
            start_time = request.form['start_time']
            capacity = request.form['capacity']
            coach_id = request.form.get('coach_id')  # Coach selection

            # Update the class with the new details
            try:
                cur.execute("""
                            UPDATE classes 
                            SET class_name = %s, description = %s, level = %s, 
                                duration = %s, start_time = %s, capacity = %s, coach_id = %s
                            WHERE class_id = %s
                        """, (class_name, description, level, duration, start_time, capacity, coach_id, class_id))
                mysql.connection.commit()
                flash("Class updated successfully!", "success")

            except Exception as e:
                mysql.connection.rollback()
                flash("An error occurred while updating the class.", "danger")
                print("Error:", e)
            # Redirect to ensure a page reload with updated data
            return redirect(url_for('admin_classes.manage_classes'))

        elif 'delete_class' in request.form:
            # Deleting a class
            class_id = request.form['class_id']

            try:
                # Step 1: Remove all patient registrations for this class
                cur.execute("DELETE FROM patient_classes WHERE class_id = %s", (class_id,))
                mysql.connection.commit()

                # Step 2: Set `coach_id` to NULL in classes for this class, if necessary
                cur.execute("UPDATE classes SET coach_id = NULL WHERE class_id = %s", (class_id,))
                mysql.connection.commit()

                # Step 3: Delete the class itself
                cur.execute("DELETE FROM classes WHERE class_id = %s", (class_id,))
                mysql.connection.commit()

                flash("Class and associated data deleted successfully!", "success")

            except Exception as e:
                mysql.connection.rollback()
                flash("An error occurred while deleting the class and its dependencies.", "danger")
                print("Error:", e)

            manage_notification(
                action='delete',
                notification_id=5
            )


        # Registering a patient to a class
        elif 'register_patient' in request.form:
            patient_id = request.form['patient_id']
            class_id = request.form['class_id']

            # Check if the patient is already registered
            cur.execute("""
                    SELECT * FROM patient_classes WHERE patient_id = %s AND class_id = %s
                """, (patient_id, class_id))
            if cur.fetchone():
                flash("Patient is already registered for this class.", "info")
            else:
                #Insert registration into `patient_classes`
                try:
                    cur.execute("""
                        INSERT INTO patient_classes (patient_id, class_id)
                        VALUES (%s, %s)
                    """, (patient_id, class_id))
                    mysql.connection.commit()
                    flash("Patient successfully registered to the class!", "success")
                except Exception as e:
                    mysql.connection.rollback()
                    flash("An error occurred while registering the patient.", "danger")
                    print("Error:", e)

            # After registering the patient to a class
            # Fetch the class name and start time for the notification message
            cur.execute("SELECT class_name, start_time FROM classes WHERE class_id = %s", (class_id,))
            class_info = cur.fetchone()
            class_name = class_info['class_name']
            start_time = class_info['start_time']

            # Send a notification to the patient
            manage_notification(
                action='send',
                patient_id=patient_id,
                class_id=class_id,
                notification_type='Reminder',
                message=f"You have been registered for the class {class_name} on {start_time}."
            )

        #assign a coach to a class
        elif 'assign_coach' in request.form:
            coach_id = request.form['coach_id']
            class_id = request.form['class_id']

            # Verify the `coach_id` exists in the `coach` table
            cur.execute("SELECT coach_id FROM coach WHERE coach_id = %s", (coach_id,))
            coach_exists = cur.fetchone()

            if not coach_exists:
                flash("The selected coach does not exist.", "danger")
                return redirect(url_for('admin_classes.manage_classes'))

            # Check if the class already has this coach assigned
            cur.execute("SELECT coach_id FROM classes WHERE class_id = %s", (class_id,))
            current_assignment = cur.fetchone()

            if current_assignment and current_assignment['coach_id'] == coach_id:
                flash("Coach is already assigned for this class.", "info")
            else:
                # Update the `coach_id` for the existing class
                try:
                    cur.execute("""
                                    UPDATE classes
                                    SET coach_id = %s
                                    WHERE class_id = %s
                                """, (coach_id, class_id))
                    mysql.connection.commit()
                    flash("Coach successfully assigned to the class!", "success")
                except Exception as e:
                    mysql.connection.rollback()
                    flash("An error occurred", "danger")
                    print("Error:", e)

            manage_notification(
                action='update',
                notification_id=5,
                message="The class timing has changed to 10:00 AM."
            )

    # Fetch all classes
    cur.execute("SELECT * FROM classes")
    classes = cur.fetchall()

    # Fetch all patients for the registration dropdown
    cur.execute("""
            SELECT patients.patient_id, users.username, users.email, patients.first_name, patients.dob, 
            patients.gender, patients.phone, patients.mobility_level
            FROM patients
            JOIN users ON patients.user_id = users.user_id
            WHERE users.role = 'patient'
            """)
    patients = cur.fetchall()

    # Fetch all users with the role 'coach' for the coach dropdown
    cur.execute("""
            SELECT users.user_id AS coach_id, users.username, users.email, coach.first_name, coach.last_name, 
            coach.specialization, coach.phone
            FROM users
            JOIN coach ON users.user_id = coach.coach_id
            WHERE users.role = 'coach'
            """)
    coaches = cur.fetchall()

    # Fetch registered patients for each class
    class_registrations = {}
    for class_info in classes:
        cur.execute("""
            SELECT patients.first_name, patients.last_name 
            FROM patient_classes
            JOIN patients ON patient_classes.patient_id = patients.patient_id
            WHERE patient_classes.class_id = %s
        """, (class_info['class_id'],))
        class_registrations[class_info['class_id']] = cur.fetchall()

    cur.close()

    return render_template('classes.html', classes=classes, patients=patients,
                           class_registrations=class_registrations, coaches=coaches)


def manage_notification(action, patient_id=None, class_id=None, notification_type=None, message=None,
                        notification_id=None):
    """
    Manage notifications by performing different actions:
    - 'send': Send a notification to a patient
    - 'update': Update the content of a notification
    - 'mark_as_read': Mark a notification as read
    - 'delete': Delete a notification
    """
    cur = mysql.connection.cursor()

    try:
        if action == 'send':
            # Send a new notification
            if patient_id and class_id and notification_type and message:
                cur.execute("""
                    INSERT INTO notifications (patient_id, class_id, notification_type, message, notification_status)
                    VALUES (%s, %s, %s, %s, 'Pending')
                """, (patient_id, class_id, notification_type, message))
                flash("Notification sent successfully!", "success")
            else:
                flash("Missing data to send notification.", "danger")

        elif action == 'update':
            # Update an existing notification's message or status
            if notification_id and (message or notification_type):
                query = "UPDATE notifications SET "
                values = []

                if message:
                    query += "message = %s, "
                    values.append(message)
                if notification_type:
                    query += "notification_type = %s, "
                    values.append(notification_type)

                # Remove trailing comma and add WHERE clause
                query = query.rstrip(', ') + " WHERE notification_id = %s"
                values.append(notification_id)

                cur.execute(query, values)
                flash("Notification updated successfully!", "success")
            else:
                flash("Missing data to update notification.", "danger")

        elif action == 'mark_as_read':
            # Mark a notification as read
            if notification_id:
                cur.execute("""
                    UPDATE notifications
                    SET notification_status = 'Read'
                    WHERE notification_id = %s
                """, (notification_id,))
                flash("Notification marked as read.", "success")
            else:
                flash("Notification ID is required to mark as read.", "danger")

        elif action == 'delete':
            # Delete a notification
            if notification_id:
                cur.execute("DELETE FROM notifications WHERE notification_id = %s", (notification_id,))
                flash("Notification deleted successfully!", "success")
            else:
                flash("Notification ID is required to delete.", "danger")

        else:
            flash("Invalid action provided for notification management.", "danger")

        # Commit the transaction if all is well
        mysql.connection.commit()

    except Exception as e:
        mysql.connection.rollback()
        flash("An error occurred with notification management.", "danger")
        print("Error:", e)

    finally:
        cur.close()
