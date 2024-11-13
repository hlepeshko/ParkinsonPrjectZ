from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from flask_mysqldb import MySQL

coach_bp = Blueprint('coach', __name__, url_prefix='/coach')
mysql = MySQL()

# Coach Dashboard Route
@coach_bp.route('/dashboard')
def coach_dashboard():
    """Displays the coach's dashboard."""
    if 'role' not in session or session['role'] != 'coach':
        return redirect(url_for('auth.login'))  # Redirect to login if not authenticated as coach

    coach_id = session.get('user_id')

    # Get the coach's information from the database
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM coach WHERE coach_id = %s", (coach_id,))
    coach = cur.fetchone()

    if not coach:
        flash("Coach not found!", "danger")
        return redirect(url_for('home'))

    return render_template('coach_dashboard.html', coach=coach)

# Submit Assessment Route
@coach_bp.route('/submit_assessment', methods=['POST'])
def submit_assessment():
    """Handles the submission of the assessment form."""
    if 'role' not in session or session['role'] != 'coach':
        return redirect(url_for('auth.login'))  # Redirect to login if not authenticated as coach

    # Get form data
    assessment_name = request.form['assessment_name']
    assessment_data = request.form['assessment_data']
    coach_id = session.get('user_id')

    # Save assessment data to the database
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO assessments (assessment_name, assessment_data, coach_id) VALUES (%s, %s, %s)",
                (assessment_name, assessment_data, coach_id))
    mysql.connection.commit()

    flash('Assessment submitted successfully!', 'success')
    return redirect(url_for('coach.coach_dashboard'))  # Redirect back to the coach dashboard

# Optional: Route for Logging Out
@coach_bp.route('/logout')
def logout():
    """Logs the user out."""
    session.clear()  # Clear the session data
    return redirect(url_for('auth.login'))  # Redirect to login page
