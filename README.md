# CS480 Hotel Management App

A Flask + PostgreSQL web application for the CS480 hotel management project.

---

## Prerequisites

- [Postgres.app](https://postgresapp.com/) — download, install, and click **Start** to run the server
- Python 3 installed

---

## First-time setup

### 1. Add psql to your terminal path
```bash
sudo mkdir -p /etc/paths.d
echo /Applications/Postgres.app/Contents/Versions/latest/bin | sudo tee /etc/paths.d/postgresapp
```
Close and reopen Terminal, then verify:
```bash
psql --version
```

### 2. Create the database
```bash
psql postgres
```
Inside psql:
```sql
CREATE USER postgres WITH PASSWORD 'postgres123';
CREATE DATABASE hotel_db OWNER postgres;
GRANT ALL PRIVILEGES ON DATABASE hotel_db TO postgres;
\q
```

### 3. Load the schema
```bash
psql -U postgres -d hotel_db -f hotel_schema_1.sql
```
Expected output:
```
BEGIN
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
COMMIT
```

### 4. Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 5. Install dependencies
```bash
pip install -r requirements.txt
```

### 6. Run the app
```bash
python app.py
```
Then open http://127.0.0.1:5000 in your browser.

---

## Reset the database (wipe all data and reload fresh)
```bash
psql -U postgres -d hotel_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
psql -U postgres -d hotel_db -f hotel_schema_1.sql
```

---

## Project structure
```
hotel_app/
├── app.py                  # App factory, config, blueprint registration
├── db.py                   # Database connection + query helper
├── requirements.txt
├── hotel_schema_1.sql      # PostgreSQL schema (relational schema submission)
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

---

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

---