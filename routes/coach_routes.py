from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from flask_mysqldb import MySQL

from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from flask_mysqldb import MySQL
from datetime import datetime
import pymysql

# Initialize blueprint and MySQL connection
coach_bp = Blueprint('coach', __name__, url_prefix='/coach')
mysql = MySQL()

@coach_bp.route('/submit_assessment', methods=['POST'])
def submit_assessment():
    """Handles the submission of an assessment."""
    # Extract form data
    assessment_data = request.form.get('assessment_data')
    patient_id = request.form.get('patient_id')
    document_id = request.form.get('document_id')  # Use document_id from the dropdown

    # Get the coach's user_id from the session
    coach_id = session.get('user_id')

    # Get the current timestamp for submission
    submitted_at = datetime.now()

    # Insert the assessment into the database
    cur = mysql.connection.cursor()
    try:
        cur.execute(
            """
            INSERT INTO assessments (assessment_data, patient_id, coach_id, submitted_at, document_id)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (assessment_data, patient_id, coach_id, submitted_at, document_id)
        )
        mysql.connection.commit()
        flash('Assessment submitted successfully!', 'success')
    except pymysql.MySQLError as e:
        flash(f'An error occurred: {e}', 'danger')
    finally:
        cur.close()

    return redirect(url_for('coach.coach_dashboard'))

@coach_bp.route('/coach_dashboard')
def coach_dashboard():
    """Displays the coach's dashboard."""
    coach_id = session.get('user_id')
    if not coach_id:
        return redirect(url_for('auth.login'))

    # Retrieve assessments associated with this coach
    cur = mysql.connection.cursor()
    try:
        cur.execute(
            """
            SELECT a.id, a.assessment_data, a.submitted_at, a.document_id, p.first_name, p.last_name
            FROM assessments a
            JOIN patients p ON a.patient_id = p.patient_id
            WHERE a.coach_id = %s
            """,
            (coach_id,)
        )
        assessments = cur.fetchall()
    finally:
        cur.close()

    return render_template('coach_dashboard.html', assessments=assessments)
