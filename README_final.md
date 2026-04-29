# CS480 Hotel Management App

A Flask + PostgreSQL web application for the CS480 hotel management project.

---

## Setup (do this once)

### 1. Create and activate a virtual environment
```bash
cd hotel_app
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up the database
In psql (or pgAdmin), create a database and run your schema:
```sql
CREATE DATABASE hotel_db;
\c hotel_db
\i /path/to/hotel_schema.sql
```

### 4. Configure your database connection
Open `app.py` and update the five lines under `app.config.update(...)`:
```python
DB_NAME='hotel_db',       # your database name
DB_USER='postgres',        # your postgres username
DB_PASSWORD='postgres',    # your postgres password
DB_HOST='localhost',
DB_PORT=5432,
```

### 5. Run the app
```bash
python app.py
```
Then open http://127.0.0.1:5000 in your browser.

---

## Project structure
```
hotel_app/
├── app.py                  # App factory, config, blueprint registration
├── db.py                   # Database connection + query helper
├── requirements.txt
├── routes/
│   ├── auth.py             # Login, logout, registration (manager + client)
│   ├── manager.py          # All §4.1 manager features
│   └── client.py           # All §4.2 client features
└── templates/
    ├── base.html           # Shared layout, nav, flash messages
    ├── login.html
    ├── register_manager.html
    ├── register_client.html
    ├── manager/
    │   ├── dashboard.html
    │   ├── hotels.html / hotel_form.html
    │   ├── rooms.html  / room_form.html
    │   ├── clients.html
    │   ├── top_clients.html
    │   ├── hotel_summary.html
    │   ├── city_query.html
    │   ├── problematic_hotels.html
    │   └── client_spending.html
    └── client/
        ├── dashboard.html
        ├── profile.html
        ├── search.html
        ├── autobook.html
        ├── bookings.html
        └── reviews.html
```

## Feature coverage

### Manager (§4.1)
| # | Feature | Route |
|---|---------|-------|
| 1 | Register + login by SSN | `/register/manager`, `/login` |
| 2 | Insert / update / delete hotels and rooms | `/manager/hotels`, `/manager/rooms` |
| 3 | Remove clients | `/manager/clients` |
| 4 | Top-k clients by bookings | `/manager/stats/top-clients` |
| 5 | All rooms with booking counts | `/manager/rooms` |
| 6 | Per-hotel bookings + avg rating | `/manager/stats/hotel-summary` |
| 7 | City C1/C2 client query | `/manager/stats/city-query` |
| 8 | Problematic Chicago hotels | `/manager/stats/problematic-hotels` |
| 9 | Client total spending | `/manager/stats/client-spending` |

### Client (§4.2)
| # | Feature | Route |
|---|---------|-------|
| 1 | Register with address + card, login by email | `/register/client`, `/login` |
| 2 | Update name, addresses, credit cards | `/client/profile` |
| 3 | Search available rooms by date range | `/client/search` |
| 4 | Book a specific room | `/client/search` (Book button) |
| 5 | Auto-book + alternative suggestions | `/client/autobook` |
| 6 | View all bookings with cost | `/client/bookings` |
| 7 | Submit review (completed stays only) | `/client/reviews` |
