from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import query, get_db
import psycopg2
from functools import wraps

manager_bp = Blueprint('manager', __name__)

def manager_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'manager':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

# ── Dashboard ──────────────────────────────────────────────────────────────────

@manager_bp.route('/')
@manager_required
def dashboard():
    return render_template('manager/dashboard.html')

# ── Hotels ─────────────────────────────────────────────────────────────────────

@manager_bp.route('/hotels')
@manager_required
def hotels():
    rows = query('''SELECT h.hotel_id, h.name, h.street_name, h.street_number, h.city
                    FROM hotel h ORDER BY h.hotel_id''')
    return render_template('manager/hotels.html', hotels=rows)

@manager_bp.route('/hotels/add', methods=['GET', 'POST'])
@manager_required
def add_hotel():
    if request.method == 'POST':
        hotel_id      = request.form['hotel_id'].strip()
        name          = request.form['name'].strip()
        street_name   = request.form['street_name'].strip()
        street_number = request.form['street_number'].strip()
        city          = request.form['city'].strip()
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute('''INSERT INTO address (street_name, street_number, city)
                               VALUES (%s, %s, %s) ON CONFLICT DO NOTHING''',
                            (street_name, street_number, city))
                cur.execute('''INSERT INTO hotel (hotel_id, name, street_name, street_number, city)
                               VALUES (%s, %s, %s, %s, %s)''',
                            (hotel_id, name, street_name, street_number, city))
            conn.commit()
            flash('Hotel added.', 'success')
            return redirect(url_for('manager.hotels'))
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            flash('Hotel ID already exists.', 'error')
        except Exception as e:
            conn.rollback()
            flash(f'Error: {e}', 'error')
    return render_template('manager/hotel_form.html', hotel=None)

@manager_bp.route('/hotels/<int:hotel_id>/edit', methods=['GET', 'POST'])
@manager_required
def edit_hotel(hotel_id):
    hotel = query('SELECT * FROM hotel WHERE hotel_id = %s', (hotel_id,), one=True)
    if not hotel:
        flash('Hotel not found.', 'error')
        return redirect(url_for('manager.hotels'))
    if request.method == 'POST':
        name          = request.form['name'].strip()
        street_name   = request.form['street_name'].strip()
        street_number = request.form['street_number'].strip()
        city          = request.form['city'].strip()
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute('''INSERT INTO address (street_name, street_number, city)
                               VALUES (%s, %s, %s) ON CONFLICT DO NOTHING''',
                            (street_name, street_number, city))
                cur.execute('''UPDATE hotel SET name=%s, street_name=%s, street_number=%s, city=%s
                               WHERE hotel_id=%s''',
                            (name, street_name, street_number, city, hotel_id))
            conn.commit()
            flash('Hotel updated.', 'success')
            return redirect(url_for('manager.hotels'))
        except Exception as e:
            conn.rollback()
            flash(f'Error: {e}', 'error')
    return render_template('manager/hotel_form.html', hotel=hotel)

@manager_bp.route('/hotels/<int:hotel_id>/delete', methods=['POST'])
@manager_required
def delete_hotel(hotel_id):
    try:
        query('DELETE FROM hotel WHERE hotel_id = %s', (hotel_id,), commit=True)
        flash('Hotel deleted.', 'success')
    except Exception as e:
        get_db().rollback()
        flash(f'Error: {e}', 'error')
    return redirect(url_for('manager.hotels'))

# ── Rooms ──────────────────────────────────────────────────────────────────────

@manager_bp.route('/rooms')
@manager_required
def rooms():
    rows = query('''SELECT r.hotel_id, h.name AS hotel_name, r.room_number,
                           r.num_windows, r.access_type, r.last_renovation_year,
                           (SELECT COUNT(*) FROM booking b
                            WHERE b.hotel_id = r.hotel_id AND b.room_number = r.room_number) AS booking_count
                    FROM room r
                    JOIN hotel h ON h.hotel_id = r.hotel_id
                    ORDER BY r.hotel_id, r.room_number''')
    return render_template('manager/rooms.html', rooms=rows)

@manager_bp.route('/rooms/add', methods=['GET', 'POST'])
@manager_required
def add_room():
    hotels = query('SELECT hotel_id, name FROM hotel ORDER BY hotel_id')
    if request.method == 'POST':
        hotel_id      = request.form['hotel_id']
        room_number   = request.form['room_number']
        num_windows   = request.form['num_windows']
        access_type   = request.form['access_type']
        renovation    = request.form['last_renovation_year']
        try:
            query('''INSERT INTO room (hotel_id, room_number, num_windows, access_type, last_renovation_year)
                     VALUES (%s, %s, %s, %s, %s)''',
                  (hotel_id, room_number, num_windows, access_type, renovation), commit=True)
            flash('Room added.', 'success')
            return redirect(url_for('manager.rooms'))
        except psycopg2.errors.UniqueViolation:
            get_db().rollback()
            flash('That room number already exists in this hotel.', 'error')
        except Exception as e:
            get_db().rollback()
            flash(f'Error: {e}', 'error')
    return render_template('manager/room_form.html', room=None, hotels=hotels)

@manager_bp.route('/rooms/<int:hotel_id>/<int:room_number>/edit', methods=['GET', 'POST'])
@manager_required
def edit_room(hotel_id, room_number):
    room   = query('SELECT * FROM room WHERE hotel_id=%s AND room_number=%s',
                   (hotel_id, room_number), one=True)
    hotels = query('SELECT hotel_id, name FROM hotel ORDER BY hotel_id')
    if not room:
        flash('Room not found.', 'error')
        return redirect(url_for('manager.rooms'))
    if request.method == 'POST':
        num_windows = request.form['num_windows']
        access_type = request.form['access_type']
        renovation  = request.form['last_renovation_year']
        try:
            query('''UPDATE room SET num_windows=%s, access_type=%s, last_renovation_year=%s
                     WHERE hotel_id=%s AND room_number=%s''',
                  (num_windows, access_type, renovation, hotel_id, room_number), commit=True)
            flash('Room updated.', 'success')
            return redirect(url_for('manager.rooms'))
        except Exception as e:
            get_db().rollback()
            flash(f'Error: {e}', 'error')
    return render_template('manager/room_form.html', room=room, hotels=hotels)

@manager_bp.route('/rooms/<int:hotel_id>/<int:room_number>/delete', methods=['POST'])
@manager_required
def delete_room(hotel_id, room_number):
    try:
        query('DELETE FROM room WHERE hotel_id=%s AND room_number=%s',
              (hotel_id, room_number), commit=True)
        flash('Room deleted.', 'success')
    except Exception as e:
        get_db().rollback()
        flash(f'Error: {e}', 'error')
    return redirect(url_for('manager.rooms'))

# ── Clients ────────────────────────────────────────────────────────────────────

@manager_bp.route('/clients')
@manager_required
def clients():
    rows = query('SELECT email, name FROM client ORDER BY name')
    return render_template('manager/clients.html', clients=rows)

@manager_bp.route('/clients/<path:email>/delete', methods=['POST'])
@manager_required
def delete_client(email):
    try:
        query('DELETE FROM client WHERE email = %s', (email,), commit=True)
        flash('Client removed.', 'success')
    except Exception as e:
        get_db().rollback()
        flash(f'Error: {e}', 'error')
    return redirect(url_for('manager.clients'))

# ── Statistics (§4.1.4 – §4.1.9) ──────────────────────────────────────────────

@manager_bp.route('/stats/top-clients', methods=['GET', 'POST'])
@manager_required
def top_clients():
    results = []
    k = 5
    if request.method == 'POST':
        k = int(request.form.get('k', 5))
        results = query('''SELECT c.name, c.email, COUNT(b.booking_id) AS booking_count
                           FROM client c
                           JOIN booking b ON b.client_email = c.email
                           GROUP BY c.email, c.name
                           ORDER BY booking_count DESC
                           LIMIT %s''', (k,))
    return render_template('manager/top_clients.html', results=results, k=k)

@manager_bp.route('/stats/hotel-summary')
@manager_required
def hotel_summary():
    rows = query('''SELECT h.name,
                           (SELECT COUNT(*) FROM booking b WHERE b.hotel_id = h.hotel_id) AS total_bookings,
                           (SELECT ROUND(AVG(r.rating), 2) FROM review r WHERE r.hotel_id = h.hotel_id) AS avg_rating
                    FROM hotel h
                    ORDER BY h.name''')
    return render_template('manager/hotel_summary.html', rows=rows)

@manager_bp.route('/stats/city-query', methods=['GET', 'POST'])
@manager_required
def city_query():
    results = []
    if request.method == 'POST':
        c1 = request.form['c1'].strip()
        c2 = request.form['c2'].strip()
        results = query('''SELECT DISTINCT c.name, c.email
                           FROM client c
                           JOIN client_address ca ON ca.client_email = c.email
                           JOIN booking b         ON b.client_email  = c.email
                           JOIN hotel h           ON h.hotel_id      = b.hotel_id
                           WHERE ca.city = %s
                             AND h.city  = %s''', (c1, c2))
    return render_template('manager/city_query.html', results=results)

@manager_bp.route('/stats/problematic-hotels')
@manager_required
def problematic_hotels():
    rows = query('''SELECT h.name, h.hotel_id,
                           ROUND(AVG(r.rating), 2) AS avg_rating,
                           COUNT(DISTINCT b.client_email) AS distinct_clients
                    FROM hotel h
                    JOIN review  r ON r.hotel_id = h.hotel_id
                    JOIN booking b ON b.hotel_id = h.hotel_id
                    WHERE h.city = \'Chicago\'
                    GROUP BY h.hotel_id, h.name
                    HAVING AVG(r.rating) < 2
                       AND COUNT(DISTINCT b.client_email) >= 2
                       AND NOT EXISTS (
                           SELECT 1 FROM booking b2
                           JOIN client_address ca ON ca.client_email = b2.client_email
                           WHERE b2.hotel_id = h.hotel_id
                             AND ca.city = \'Chicago\'
                       )
                    ORDER BY avg_rating''')
    return render_template('manager/problematic_hotels.html', rows=rows)

@manager_bp.route('/stats/client-spending')
@manager_required
def client_spending():
    rows = query('''SELECT c.name, c.email,
                           (SELECT COALESCE(SUM(b.price_per_day * (b.end_date - b.start_date + 1)), 0)
                            FROM booking b WHERE b.client_email = c.email) AS total_spent
                    FROM client c
                    ORDER BY total_spent DESC''')
    return render_template('manager/client_spending.html', rows=rows)
