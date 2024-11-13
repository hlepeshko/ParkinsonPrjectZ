# Authentication routes (login, logout)
import MySQLdb
import bcrypt
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import re
from app import mysql

# Create the Blueprint for auth routes
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


# Regular expressions for validation
def is_valid_username(username: str) -> bool:
    """Check if the username is alphanumeric and between 3 and 15 characters."""
    return bool(re.match(r'^[a-zA-Z0-9]{3,15}$', username))


def is_valid_email(email: str) -> bool:
    """Check if the email address is valid."""
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))


def is_strong_password(password: str) -> bool:
    """Check if the password is strong (at least 8 characters, contains a number, a letter, and a special character)."""
    return bool(re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password))


# Login Route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Debugging: print the login attempt details
        print(f"Login attempt for username: {username}")

        # Check if username exists in the database
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone() # This will be a dictionary
        # Close the cursor
        cur.close()

        if user:
            # Check if the password matches
            if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                # Set session and redirect based on the role
                # Debugging: print user and session info
                print(f"User authenticated: {user['username']}")
                session['user_id'] = user['user_id']
                session['role'] = user['role']
                session['username'] = user['username']

                if user['role'] == 'admin':
                    return redirect(url_for('admin.admin_dashboard'))
                elif user['role'] == 'coach':
                    return redirect(url_for('coach.coach_dashboard'))
                else:
                    return redirect(url_for('patient.patient_dashboard'))
            else:
                flash('Invalid credentials', 'danger')
        else:
            flash('User not found', 'danger')
    return render_template('login.html')

# Registration Route
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handles user registration."""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if the username already exists in the database
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cur.fetchone()

        if existing_user:
            flash('Username already exists. Please choose another one.', 'danger')
            return redirect(url_for('auth.register'))
        #Hash the password before storing it
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Check if there is an admin in the database
        cur.execute("SELECT * FROM users WHERE role = 'admin'")
        admin_exists = cur.fetchone()

        # If no admin exists, make this user the admin
        if not admin_exists:
            role = 'admin'
        else:
            role = 'patient'

            # Validate input using regular expressions
        if not is_valid_username(username):
            flash("Invalid username! It should be alphanumeric and between 3 to 15 characters.", "danger")
            return redirect(url_for('auth.register'))

        if not is_valid_email(email):
            flash("Invalid email format!", "danger")
            return redirect(url_for('auth.register'))

        if not is_strong_password(password):
            flash(
                "Password is too weak! It should be at least 8 characters long, contain a number, and a special character.",
                "danger")
            return redirect(url_for('auth.register'))

        # Insert user into the database
        #cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("INSERT INTO users (username, password, email, role) VALUES (%s, %s, %s, %s)",
                        (username, hashed_pw.decode('utf-8'), email, role))  # Role 'patient' by default for simplicity
        # Get the user_id of the newly created user
        user_id = cur.lastrowid
        mysql.connection.commit()
        # After inserting into the users table, also insert into the patients table
        cur.execute("INSERT INTO patients (user_id,username, password, email) VALUES (%s, %s, %s,%s)",
                        (user_id,username, hashed_pw.decode('utf-8'), email))

        mysql.connection.commit()
        cur.close()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('auth.login'))

    return render_template('register.html')


# Logout Route
@auth_bp.route('/logout')
def logout():
    """Handles user logout."""
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

# New route to inform users about role assignment
@auth_bp.route('/no_role')
def no_role():
    return render_template('no_role.html')
