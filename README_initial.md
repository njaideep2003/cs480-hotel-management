
# cs480-hotel-management

A hotel management database system built for CS480 (Database Systems) at UIC.  
This repository contains the ER model and relational schema for the project.
 
---
 
## Project Overview
 
The system supports two roles — **managers** and **clients**.
 
- **Managers** can add/remove hotels and rooms, manage clients, and run reports
- **Clients** can search available rooms, make bookings, manage addresses and credit cards, and write reviews

## Phase 1 — ER Model (`final_ER.pdf`)

For Phase 1, we created an ER diagram based on the given entities, attributes, and their relationships.  
The initial version of the ER diagram had some issues, which were identified through feedback from the professor.  

We revised the diagram accordingly, and the updated version is provided here:  
[final_ER.pdf](final_ER.pdf)


## Phase 2 — Relational Schema (`hotel_schema.sql`)

For Phase 2, we translated the ER model into a relational schema using PostgreSQL.

- The final schema implementation is available here:  
  [hotel_schema.sql](hotel_schema.sql)

- We also created a test script to validate the correctness of the schema and ensure that all constraints and business rules are properly enforced:  
  [hotel_run_tests.sql](hotel_run_tests.sql)

The test results confirm that the schema behaves as expected and satisfies all specified requirements.

## Prerequisites
 
- [PostgreSQL](https://www.postgresql.org/) installed  
- On Mac: [Postgres.app](https://postgresapp.com/) is recommended  
- Terminal access to `psql`
### Set up psql on Mac (Postgres.app)
 
```bash
sudo mkdir -p /etc/paths.d
echo /Applications/Postgres.app/Contents/Versions/latest/bin | sudo tee /etc/paths.d/postgresapp
```
 
Then close and reopen Terminal. Verify with:
 
```bash
psql --version
```
 
---
 
## How to Run
 
### Step 1 — Create the database
 
```bash
psql postgres
```
 
Inside psql:
 
```sql
CREATE DATABASE hotel_cs480;
\q
```
 
### Step 2 — Load the schema
 
```bash
psql -d hotel_cs480 -f hotel_schema.sql
```
 
Expected output:
```
BEGIN
CREATE EXTENSION
CREATE TABLE       (x9)
ALTER TABLE
CREATE FUNCTION    (x3)
CREATE TRIGGER     (x5)
COMMIT
```
 
### Step 3 — Run constraint tests
 
```bash
psql -d hotel_cs480 -f hotel_run_tests.sql
```
 
All 10 tests should print `PASS`.
 
### Step 4 — Run full verification (optional)
 
```bash
psql -d hotel_cs480 -f hotel_full_verify.sql
```
 
This runs the schema, all constraint tests, structural checks, and all spec queries in one shot.
 
### Reset and rerun from scratch
 
```bash
psql -d hotel_cs480 -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
psql -d hotel_cs480 -f hotel_schema.sql
psql -d hotel_cs480 -f hotel_run_tests.sql
```
 
---

## Test Results
 
All 10 constraint tests verified:
 
| Test | Constraint tested | Result |
|---|---|---|
| A | Overlapping booking (same room) | ✅ PASS |
| B | Exact same date range overlap | ✅ PASS |
| C | Review without prior stay | ✅ PASS |
| D | Rating > 10 | ✅ PASS |
| E | Rating < 0 | ✅ PASS |
| F | Invalid access_type | ✅ PASS |
| G | Client min-address trigger exists (deferrable) | ✅ PASS |
| H | Client min-credit-card trigger exists (deferrable) | ✅ PASS |
| I | Room referencing non-existent hotel | ✅ PASS |
| J | end_date before start_date | ✅ PASS |
 
Tests G and H were additionally verified manually at the `psql` prompt by committing transactions without addresses/cards — both correctly failed at `COMMIT` time.
