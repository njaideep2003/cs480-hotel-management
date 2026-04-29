from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import query, get_db
import psycopg2
from functools import wraps
from datetime import date

client_bp = Blueprint('client', __name__)

def client_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'client':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

# ── Dashboard ──────────────────────────────────────────────────────────────────

@client_bp.route('/')
@client_required
def dashboard():
    return render_template('client/dashboard.html')

# ── Profile ────────────────────────────────────────────────────────────────────

@client_bp.route('/profile', methods=['GET', 'POST'])
@client_required
def profile():
    email = session['email']
    if request.method == 'POST':
        name = request.form['name'].strip()
        try:
            query('UPDATE client SET name=%s WHERE email=%s', (name, email), commit=True)
            session['name'] = name
            flash('Name updated.', 'success')
        except Exception as e:
            get_db().rollback()
            flash(f'Error: {e}', 'error')
        return redirect(url_for('client.profile'))
    client   = query('SELECT * FROM client WHERE email=%s', (email,), one=True)
    addresses = query('SELECT * FROM client_address WHERE client_email=%s', (email,))
    cards    = query('SELECT * FROM credit_card WHERE client_email=%s', (email,))
    return render_template('client/profile.html', client=client, addresses=addresses, cards=cards)

@client_bp.route('/profile/add-address', methods=['POST'])
@client_required
def add_address():
    email  = session['email']
    sn     = request.form['street_name'].strip()
    snum   = request.form['street_number'].strip()
    city   = request.form['city'].strip()
    conn   = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute('''INSERT INTO address (street_name, street_number, city)
                           VALUES (%s,%s,%s) ON CONFLICT DO NOTHING''', (sn, snum, city))
            cur.execute('''INSERT INTO client_address (client_email, street_name, street_number, city)
                           VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING''', (email, sn, snum, city))
        conn.commit()
        flash('Address added.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error: {e}', 'error')
    return redirect(url_for('client.profile'))

@client_bp.route('/profile/remove-address', methods=['POST'])
@client_required
def remove_address():
    email = session['email']
    sn    = request.form['street_name']
    snum  = request.form['street_number']
    city  = request.form['city']
    count = query('SELECT COUNT(*) AS cnt FROM client_address WHERE client_email=%s', (email,), one=True)
    if count['cnt'] <= 1:
        flash('You must keep at least one address.', 'error')
        return redirect(url_for('client.profile'))
    try:
        query('''DELETE FROM client_address
                 WHERE client_email=%s AND street_name=%s AND street_number=%s AND city=%s''',
              (email, sn, snum, city), commit=True)
        flash('Address removed.', 'success')
    except Exception as e:
        get_db().rollback()
        flash(f'Error: {e}', 'error')
    return redirect(url_for('client.profile'))

@client_bp.route('/profile/add-card', methods=['POST'])
@client_required
def add_card():
    email  = session['email']
    card   = request.form['card_number'].strip()
    sn     = request.form['street_name'].strip()
    snum   = request.form['street_number'].strip()
    city   = request.form['city'].strip()
    conn   = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute('''INSERT INTO address (street_name, street_number, city)
                           VALUES (%s,%s,%s) ON CONFLICT DO NOTHING''', (sn, snum, city))
            cur.execute('''INSERT INTO credit_card (card_number, client_email, street_name, street_number, city)
                           VALUES (%s,%s,%s,%s,%s)''', (card, email, sn, snum, city))
        conn.commit()
        flash('Card added.', 'success')
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        flash('That card number is already registered.', 'error')
    except Exception as e:
        conn.rollback()
        flash(f'Error: {e}', 'error')
    return redirect(url_for('client.profile'))

@client_bp.route('/profile/remove-card', methods=['POST'])
@client_required
def remove_card():
    email = session['email']
    card  = request.form['card_number']
    count = query('SELECT COUNT(*) AS cnt FROM credit_card WHERE client_email=%s', (email,), one=True)
    if count['cnt'] <= 1:
        flash('You must keep at least one credit card.', 'error')
        return redirect(url_for('client.profile'))
    try:
        query('DELETE FROM credit_card WHERE card_number=%s AND client_email=%s',
              (card, email), commit=True)
        flash('Card removed.', 'success')
    except Exception as e:
        get_db().rollback()
        flash(f'Error: {e}', 'error')
    return redirect(url_for('client.profile'))

# ── Room search ────────────────────────────────────────────────────────────────

@client_bp.route('/search', methods=['GET', 'POST'])
@client_required
def search():
    rooms = []
    start = end = ''
    if request.method == 'POST':
        start = request.form['start_date']
        end   = request.form['end_date']
        if start < str(date.today()):
            flash('Start date cannot be in the past.', 'error')
            return render_template('client/search.html', rooms=[], start=start, end=end)
        if end < start:
            flash('End date must be on or after start date.', 'error')
            return render_template('client/search.html', rooms=[], start=start, end=end)
        rooms = query('''SELECT r.hotel_id, h.name AS hotel_name, r.room_number,
                                r.num_windows, r.access_type, r.last_renovation_year
                         FROM room r
                         JOIN hotel h ON h.hotel_id = r.hotel_id
                         WHERE NOT EXISTS (
                             SELECT 1 FROM booking b
                             WHERE b.hotel_id    = r.hotel_id
                               AND b.room_number = r.room_number
                               AND daterange(b.start_date, b.end_date, '[]')
                                   && daterange(%s::date, %s::date, '[]')
                         )
                         ORDER BY h.name, r.room_number''', (start, end))
    return render_template('client/search.html', rooms=rooms, start=start, end=end)

# ── Book a room ────────────────────────────────────────────────────────────────

@client_bp.route('/book', methods=['POST'])
@client_required
def book():
    email       = session['email']
    hotel_id    = request.form['hotel_id']
    room_number = request.form['room_number']
    start       = request.form['start_date']
    end         = request.form['end_date']
    ppd         = request.form.get('price_per_day', '100.00')

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute('''SELECT 1 FROM booking
                           WHERE hotel_id = %s AND room_number = %s
                             AND start_date <= %s AND end_date >= %s''',
                        (hotel_id, room_number, end, start))
            if cur.fetchone():
                conn.rollback()
                flash('That room is no longer available for the selected dates.', 'error')
                return redirect(url_for('client.search'))
            cur.execute('''INSERT INTO booking (client_email, hotel_id, room_number,
                                                start_date, end_date, price_per_day)
                           VALUES (%s,%s,%s,%s,%s,%s) RETURNING booking_id''',
                        (email, hotel_id, room_number, start, end, ppd))
            new_id = cur.fetchone()[0]
        conn.commit()
        flash(f'Room {room_number} booked successfully! Booking #{new_id}', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Booking failed: {e}', 'error')
    return redirect(url_for('client.search'))

# ── Auto-book ──────────────────────────────────────────────────────────────────

@client_bp.route('/autobook', methods=['GET', 'POST'])
@client_required
def autobook():
    hotels = query('SELECT hotel_id, name FROM hotel ORDER BY name')
    result = None
    alternatives = []
    if request.method == 'POST':
        email    = session['email']
        hotel_id = int(request.form['hotel_id'])
        start    = request.form['start_date']
        end      = request.form['end_date']

        if start < str(date.today()):
            flash('Start date cannot be in the past.', 'error')
            return render_template('client/autobook.html', hotels=hotels, result=None, alternatives=[])
        if end < start:
            flash('End date must be on or after start date.', 'error')
            return render_template('client/autobook.html', hotels=hotels, result=None, alternatives=[])

        # Find first available room in requested hotel
        available = query('''SELECT r.room_number
                             FROM room r
                             WHERE r.hotel_id = %s
                               AND NOT EXISTS (
                                   SELECT 1 FROM booking b
                                   WHERE b.hotel_id    = r.hotel_id
                                     AND b.room_number = r.room_number
                                     AND daterange(b.start_date, b.end_date, '[]')
                                         && daterange(%s::date, %s::date, '[]')
                               )
                             LIMIT 1''', (hotel_id, start, end))

        if available:
            room_number = available[0]['room_number']
            conn = get_db()
            try:
                with conn.cursor() as cur:
                    cur.execute('''SELECT 1 FROM booking
                                   WHERE hotel_id = %s AND room_number = %s
                                     AND start_date <= %s AND end_date >= %s''',
                                (hotel_id, room_number, end, start))
                    if cur.fetchone():
                        conn.rollback()
                        flash('Race condition — please try again.', 'error')
                        return redirect(url_for('client.autobook'))
                    cur.execute('''INSERT INTO booking (client_email, hotel_id, room_number,
                                                        start_date, end_date, price_per_day)
                                   VALUES (%s,%s,%s,%s,%s,%s) RETURNING booking_id''',
                                (email, hotel_id, room_number, start, end, 100.00))
                    new_id = cur.fetchone()[0]
                conn.commit()
                hotel = query('SELECT name FROM hotel WHERE hotel_id=%s', (hotel_id,), one=True)
                result = {'room': room_number, 'hotel': hotel['name'],
                          'start': start, 'end': end, 'booking_id': new_id}
            except Exception as e:
                conn.rollback()
                flash(f'Booking failed: {e}', 'error')
        else:
            # Suggest alternative hotels
            alternatives = query('''SELECT DISTINCT h.hotel_id, h.name
                                    FROM hotel h
                                    JOIN room r ON r.hotel_id = h.hotel_id
                                    WHERE h.hotel_id != %s
                                      AND NOT EXISTS (
                                          SELECT 1 FROM booking b
                                          WHERE b.hotel_id    = r.hotel_id
                                            AND b.room_number = r.room_number
                                            AND daterange(b.start_date, b.end_date, '[]')
                                                && daterange(%s::date, %s::date, '[]')
                                      )
                                    ORDER BY h.name''', (hotel_id, start, end))
            flash('No rooms available at that hotel for those dates.', 'error')

    return render_template('client/autobook.html', hotels=hotels,
                           result=result, alternatives=alternatives)

# ── My bookings ────────────────────────────────────────────────────────────────

@client_bp.route('/bookings')
@client_required
def bookings():
    email = session['email']
    rows  = query('''SELECT b.booking_id, h.name AS hotel_name, b.room_number,
                            b.start_date, b.end_date, b.price_per_day,
                            b.price_per_day * (b.end_date - b.start_date + 1) AS total_cost
                     FROM booking b
                     JOIN hotel h ON h.hotel_id = b.hotel_id
                     WHERE b.client_email = %s
                     ORDER BY b.start_date DESC''', (email,))
    return render_template('client/bookings.html', bookings=rows)

# ── Reviews ────────────────────────────────────────────────────────────────────

@client_bp.route('/reviews', methods=['GET', 'POST'])
@client_required
def reviews():
    email  = session['email']
    if request.method == 'POST':
        hotel_id = request.form['hotel_id']
        message  = request.form['message'].strip()
        rating   = request.form['rating']
        has_stayed = query('''SELECT 1 FROM booking
                              WHERE client_email = %s AND hotel_id = %s
                                AND end_date <= CURRENT_DATE''',
                           (email, hotel_id), one=True)
        if not has_stayed:
            flash('You can only review hotels where you have completed a stay.', 'error')
            return redirect(url_for('client.reviews'))
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute('''INSERT INTO review (hotel_id, client_email, message, rating)
                               VALUES (%s,%s,%s,%s)''',
                            (hotel_id, email, message, rating))
            conn.commit()
            flash('Review submitted!', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error: {e}', 'error')

    # Hotels the client has stayed at (completed bookings)
    stayed_at = query('''SELECT DISTINCT h.hotel_id, h.name
                         FROM booking b
                         JOIN hotel h ON h.hotel_id = b.hotel_id
                         WHERE b.client_email = %s AND b.end_date <= CURRENT_DATE
                         ORDER BY h.name''', (email,))
    my_reviews = query('''SELECT r.hotel_id, h.name AS hotel_name, r.message, r.rating
                          FROM review r
                          JOIN hotel h ON h.hotel_id = r.hotel_id
                          WHERE r.client_email = %s
                          ORDER BY r.hotel_id''', (email,))
    return render_template('client/reviews.html', stayed_at=stayed_at, my_reviews=my_reviews)
