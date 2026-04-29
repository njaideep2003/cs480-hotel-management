from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import query, get_db
import psycopg2

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form['role']
        if role == 'manager':
            ssn = request.form['ssn'].strip()
            manager = query('SELECT * FROM manager WHERE ssn = %s', (ssn,), one=True)
            if manager:
                session['role'] = 'manager'
                session['ssn']  = manager['ssn']
                session['name'] = manager['name']
                return redirect(url_for('manager.dashboard'))
            flash('Manager SSN not found.', 'error')
        else:
            email = request.form['email'].strip()
            client = query('SELECT * FROM client WHERE email = %s', (email,), one=True)
            if client:
                session['role']  = 'client'
                session['email'] = client['email']
                session['name']  = client['name']
                return redirect(url_for('client.dashboard'))
            flash('Client email not found.', 'error')
    return render_template('login.html')

@auth_bp.route('/register/manager', methods=['GET', 'POST'])
def register_manager():
    if request.method == 'POST':
        ssn   = request.form['ssn'].strip()
        name  = request.form['name'].strip()
        email = request.form['email'].strip()
        try:
            query('INSERT INTO manager (ssn, name, email) VALUES (%s, %s, %s)',
                  (ssn, name, email), commit=True)
            flash('Manager registered. Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except psycopg2.errors.UniqueViolation:
            get_db().rollback()
            flash('That SSN is already registered.', 'error')
    return render_template('register_manager.html')

@auth_bp.route('/register/client', methods=['GET', 'POST'])
def register_client():
    if request.method == 'POST':
        email        = request.form['email'].strip()
        name         = request.form['name'].strip()
        street_name  = request.form['street_name'].strip()
        street_number= request.form['street_number'].strip()
        city         = request.form['city'].strip()
        card_number  = request.form['card_number'].strip()
        bill_street  = request.form['bill_street'].strip()
        bill_number  = request.form['bill_number'].strip()
        bill_city    = request.form['bill_city'].strip()

        conn = get_db()
        try:
            with conn.cursor() as cur:
                # Insert client
                cur.execute('INSERT INTO client (email, name) VALUES (%s, %s)', (email, name))
                # Ensure address exists
                cur.execute('''INSERT INTO address (street_name, street_number, city)
                               VALUES (%s, %s, %s) ON CONFLICT DO NOTHING''',
                            (street_name, street_number, city))
                # Link client to address
                cur.execute('''INSERT INTO client_address (client_email, street_name, street_number, city)
                               VALUES (%s, %s, %s, %s)''',
                            (email, street_name, street_number, city))
                # Ensure billing address exists
                cur.execute('''INSERT INTO address (street_name, street_number, city)
                               VALUES (%s, %s, %s) ON CONFLICT DO NOTHING''',
                            (bill_street, bill_number, bill_city))
                # Insert credit card
                cur.execute('''INSERT INTO credit_card (card_number, client_email, street_name, street_number, city)
                               VALUES (%s, %s, %s, %s, %s)''',
                            (card_number, email, bill_street, bill_number, bill_city))
            conn.commit()
            flash('Account created. Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            flash('That email or card number is already registered.', 'error')
        except Exception as e:
            conn.rollback()
            flash(f'Registration failed: {e}', 'error')
    return render_template('register_client.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
