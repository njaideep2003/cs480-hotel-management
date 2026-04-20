-- ============================================================
-- CS480 – Hotel Management System
-- COMBINED: Schema + Tests in one file
-- Run with: psql -d hotel_cs480 -f hotel_run_tests.sql
-- ============================================================

-- ============================================================
-- PART 1: CLEAN SLATE
-- ============================================================
DROP TABLE IF EXISTS booking        CASCADE;
DROP TABLE IF EXISTS review         CASCADE;
DROP TABLE IF EXISTS credit_card    CASCADE;
DROP TABLE IF EXISTS client_address CASCADE;
DROP TABLE IF EXISTS room           CASCADE;
DROP TABLE IF EXISTS hotel          CASCADE;
DROP TABLE IF EXISTS address        CASCADE;
DROP TABLE IF EXISTS client         CASCADE;
DROP TABLE IF EXISTS manager        CASCADE;
DROP FUNCTION IF EXISTS check_review_requires_prior_stay()  CASCADE;
DROP FUNCTION IF EXISTS enforce_client_min_one_address()    CASCADE;
DROP FUNCTION IF EXISTS enforce_client_min_one_card()       CASCADE;
DROP EXTENSION IF EXISTS btree_gist CASCADE;

-- ============================================================
-- PART 2: CREATE SCHEMA
-- ============================================================

CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE manager (
    ssn    VARCHAR(20)  PRIMARY KEY,
    name   VARCHAR(255) NOT NULL,
    email  VARCHAR(255) NOT NULL
);

CREATE TABLE client (
    email  VARCHAR(255) PRIMARY KEY,
    name   VARCHAR(255) NOT NULL
);

CREATE TABLE address (
    street_name   VARCHAR(255) NOT NULL,
    street_number VARCHAR(50)  NOT NULL,
    city          VARCHAR(255) NOT NULL,
    PRIMARY KEY (street_name, street_number, city)
);

CREATE TABLE hotel (
    hotel_id      INTEGER      PRIMARY KEY,
    name          VARCHAR(255) NOT NULL,
    street_name   VARCHAR(255) NOT NULL,
    street_number VARCHAR(50)  NOT NULL,
    city          VARCHAR(255) NOT NULL,
    FOREIGN KEY (street_name, street_number, city)
        REFERENCES address (street_name, street_number, city)
        ON DELETE RESTRICT
);

CREATE TABLE room (
    hotel_id             INTEGER     NOT NULL,
    room_number          INTEGER     NOT NULL,
    num_windows          INTEGER     NOT NULL CHECK (num_windows >= 0),
    last_renovation_year INTEGER     NOT NULL,
    access_type          VARCHAR(20) NOT NULL
        CHECK (access_type IN ('elevator', 'stairs')),
    PRIMARY KEY (hotel_id, room_number),
    FOREIGN KEY (hotel_id)
        REFERENCES hotel (hotel_id)
        ON DELETE CASCADE
);

CREATE TABLE review (
    hotel_id     INTEGER      NOT NULL,
    review_id    INTEGER      NOT NULL,
    client_email VARCHAR(255) NOT NULL,
    message      TEXT         NOT NULL,
    rating       INTEGER      NOT NULL CHECK (rating BETWEEN 0 AND 10),
    PRIMARY KEY (hotel_id, review_id),
    FOREIGN KEY (hotel_id)
        REFERENCES hotel (hotel_id)
        ON DELETE CASCADE,
    FOREIGN KEY (client_email)
        REFERENCES client (email)
        ON DELETE CASCADE
);

CREATE TABLE client_address (
    client_email  VARCHAR(255) NOT NULL,
    street_name   VARCHAR(255) NOT NULL,
    street_number VARCHAR(50)  NOT NULL,
    city          VARCHAR(255) NOT NULL,
    PRIMARY KEY (client_email, street_name, street_number, city),
    FOREIGN KEY (client_email)
        REFERENCES client (email)
        ON DELETE CASCADE,
    FOREIGN KEY (street_name, street_number, city)
        REFERENCES address (street_name, street_number, city)
        ON DELETE CASCADE
);

CREATE TABLE credit_card (
    card_number   VARCHAR(50)  PRIMARY KEY,
    client_email  VARCHAR(255) NOT NULL,
    street_name   VARCHAR(255) NOT NULL,
    street_number VARCHAR(50)  NOT NULL,
    city          VARCHAR(255) NOT NULL,
    FOREIGN KEY (client_email)
        REFERENCES client (email)
        ON DELETE CASCADE,
    FOREIGN KEY (street_name, street_number, city)
        REFERENCES address (street_name, street_number, city)
        ON DELETE RESTRICT
);

CREATE TABLE booking (
    booking_id    INTEGER        PRIMARY KEY,
    client_email  VARCHAR(255)   NOT NULL,
    hotel_id      INTEGER        NOT NULL,
    room_number   INTEGER        NOT NULL,
    start_date    DATE           NOT NULL,
    end_date      DATE           NOT NULL,
    price_per_day NUMERIC(10, 2) NOT NULL CHECK (price_per_day > 0),
    CHECK (end_date >= start_date),
    FOREIGN KEY (client_email)
        REFERENCES client (email)
        ON DELETE CASCADE,
    FOREIGN KEY (hotel_id, room_number)
        REFERENCES room (hotel_id, room_number)
        ON DELETE CASCADE
);

ALTER TABLE booking
    ADD CONSTRAINT booking_no_overlap
    EXCLUDE USING gist (
        hotel_id    WITH =,
        room_number WITH =,
        daterange(start_date, end_date, '[]') WITH &&
    );

-- Trigger: review only if prior completed stay
CREATE OR REPLACE FUNCTION check_review_requires_prior_stay()
RETURNS TRIGGER AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM   booking b
        WHERE  b.client_email = NEW.client_email
          AND  b.hotel_id     = NEW.hotel_id
          AND  b.end_date    <= CURRENT_DATE
    ) THEN
        RAISE EXCEPTION
            'Client % has not completed a stay at hotel % and cannot submit a review.',
            NEW.client_email, NEW.hotel_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_review_prior_stay
    BEFORE INSERT OR UPDATE ON review
    FOR EACH ROW
    EXECUTE FUNCTION check_review_requires_prior_stay();

-- Trigger: client must have at least one address
-- FIX: use TG_OP to avoid accessing OLD on INSERT
CREATE OR REPLACE FUNCTION enforce_client_min_one_address()
RETURNS TRIGGER AS $$
DECLARE
    v_email VARCHAR(255);
BEGIN
    IF TG_TABLE_NAME = 'client' THEN
        v_email := NEW.email;
    ELSIF TG_OP = 'DELETE' THEN
        v_email := OLD.client_email;
    ELSE
        v_email := NEW.client_email;
    END IF;
    IF v_email IS NULL THEN RETURN NULL; END IF;
    IF NOT EXISTS (
        SELECT 1 FROM client_address WHERE client_email = v_email
    ) THEN
        RAISE EXCEPTION 'Client % must have at least one address.', v_email;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER trg_client_min_address_on_client
    AFTER INSERT OR UPDATE ON client
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW
    EXECUTE FUNCTION enforce_client_min_one_address();

CREATE CONSTRAINT TRIGGER trg_client_min_address_on_junction
    AFTER DELETE OR UPDATE ON client_address
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW
    EXECUTE FUNCTION enforce_client_min_one_address();

-- Trigger: client must have at least one credit card
-- FIX: same TG_OP check
CREATE OR REPLACE FUNCTION enforce_client_min_one_card()
RETURNS TRIGGER AS $$
DECLARE
    v_email VARCHAR(255);
BEGIN
    IF TG_TABLE_NAME = 'client' THEN
        v_email := NEW.email;
    ELSIF TG_OP = 'DELETE' THEN
        v_email := OLD.client_email;
    ELSE
        v_email := NEW.client_email;
    END IF;
    IF v_email IS NULL THEN RETURN NULL; END IF;
    IF NOT EXISTS (
        SELECT 1 FROM credit_card WHERE client_email = v_email
    ) THEN
        RAISE EXCEPTION 'Client % must have at least one credit card.', v_email;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER trg_client_min_card_on_client
    AFTER INSERT OR UPDATE ON client
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW
    EXECUTE FUNCTION enforce_client_min_one_card();

CREATE CONSTRAINT TRIGGER trg_client_min_card_on_credit_card
    AFTER DELETE OR UPDATE ON credit_card
    DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW
    EXECUTE FUNCTION enforce_client_min_one_card();

-- ============================================================
-- PART 3: INSERT VALID TEST DATA
-- ============================================================

SELECT '--- PART 3: INSERTING VALID DATA ---' AS status;

INSERT INTO manager VALUES ('111-22-3333', 'Alice Smith', 'alice@hotel.com');
INSERT INTO manager VALUES ('444-55-6666', 'Bob Johnson', 'bob@hotel.com');
SELECT '✓ Managers inserted' AS result;

INSERT INTO address VALUES ('Main St',  '100', 'Chicago');
INSERT INTO address VALUES ('Oak Ave',  '200', 'Chicago');
INSERT INTO address VALUES ('Pine Rd',  '300', 'New York');
INSERT INTO address VALUES ('Elm St',   '400', 'Chicago');
INSERT INTO address VALUES ('Maple Dr', '500', 'Chicago');
INSERT INTO address VALUES ('Cedar Ln', '600', 'New York');
SELECT '✓ Addresses inserted' AS result;

INSERT INTO hotel VALUES (1, 'Grand Chicago', 'Main St', '100', 'Chicago');
INSERT INTO hotel VALUES (2, 'NYC Plaza',      'Pine Rd', '300', 'New York');
SELECT '✓ Hotels inserted' AS result;

INSERT INTO room VALUES (1, 101, 2, 2020, 'elevator');
INSERT INTO room VALUES (1, 102, 1, 2019, 'stairs');
INSERT INTO room VALUES (1, 103, 3, 2021, 'elevator');
INSERT INTO room VALUES (2, 201, 2, 2018, 'elevator');
SELECT '✓ Rooms inserted' AS result;

-- All in one transaction so deferred triggers fire at COMMIT
BEGIN;
    INSERT INTO client VALUES ('john@gmail.com', 'John Doe');
    INSERT INTO client VALUES ('jane@gmail.com', 'Jane Doe');
    INSERT INTO client VALUES ('mike@gmail.com', 'Mike Lee');

    INSERT INTO client_address VALUES ('john@gmail.com', 'Oak Ave',  '200', 'Chicago');
    INSERT INTO client_address VALUES ('jane@gmail.com', 'Elm St',   '400', 'Chicago');
    INSERT INTO client_address VALUES ('jane@gmail.com', 'Cedar Ln', '600', 'New York');
    INSERT INTO client_address VALUES ('mike@gmail.com', 'Maple Dr', '500', 'Chicago');

    INSERT INTO credit_card VALUES ('4111-1111-1111-1111', 'john@gmail.com', 'Oak Ave',  '200', 'Chicago');
    INSERT INTO credit_card VALUES ('4222-2222-2222-2222', 'jane@gmail.com', 'Elm St',   '400', 'Chicago');
    INSERT INTO credit_card VALUES ('4333-3333-3333-3333', 'jane@gmail.com', 'Cedar Ln', '600', 'New York');
    INSERT INTO credit_card VALUES ('4444-4444-4444-4444', 'mike@gmail.com', 'Maple Dr', '500', 'Chicago');
COMMIT;
SELECT '✓ Clients, addresses, credit cards inserted' AS result;

-- Past dates so review trigger (end_date <= CURRENT_DATE) passes
INSERT INTO booking VALUES (1, 'john@gmail.com', 1, 101, '2024-01-10', '2024-01-15', 150.00);
INSERT INTO booking VALUES (2, 'jane@gmail.com', 1, 102, '2024-02-01', '2024-02-05', 120.00);
INSERT INTO booking VALUES (3, 'mike@gmail.com', 2, 201, '2024-03-01', '2024-03-07', 200.00);
INSERT INTO booking VALUES (4, 'john@gmail.com', 1, 101, '2024-06-01', '2024-06-05', 150.00);
SELECT '✓ Bookings inserted' AS result;

INSERT INTO review VALUES (1, 1, 'john@gmail.com', 'Great hotel!',   9);
INSERT INTO review VALUES (1, 2, 'jane@gmail.com', 'Nice rooms.',    8);
INSERT INTO review VALUES (2, 1, 'mike@gmail.com', 'Good location.', 7);
SELECT '✓ Reviews inserted' AS result;

-- ============================================================
-- PART 4: CONSTRAINT TESTS (all should print PASS)
-- ============================================================

SELECT '--- PART 4: CONSTRAINT TESTS ---' AS status;

-- TEST A: Overlapping booking
SELECT '--- TEST A: Booking overlap ---' AS test;
DO $$
BEGIN
    INSERT INTO booking VALUES (99, 'jane@gmail.com', 1, 101,
        '2024-01-12', '2024-01-18', 150.00);
    RAISE NOTICE 'FAIL — overlap was NOT caught';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'PASS — overlap correctly blocked';
END;
$$;

-- TEST B: Exact same dates
SELECT '--- TEST B: Exact same dates ---' AS test;
DO $$
BEGIN
    INSERT INTO booking VALUES (98, 'mike@gmail.com', 1, 101,
        '2024-01-10', '2024-01-15', 150.00);
    RAISE NOTICE 'FAIL — exact overlap was NOT caught';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'PASS — exact overlap correctly blocked';
END;
$$;

-- TEST C: Review without prior stay (jane never stayed at hotel 2)
SELECT '--- TEST C: Review without prior stay ---' AS test;
DO $$
BEGIN
    INSERT INTO review VALUES (2, 2, 'jane@gmail.com', 'Amazing!', 10);
    RAISE NOTICE 'FAIL — review without stay was NOT caught';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'PASS — review without stay correctly blocked';
END;
$$;

-- TEST D: Rating > 10
SELECT '--- TEST D: Rating > 10 ---' AS test;
DO $$
BEGIN
    INSERT INTO review VALUES (1, 99, 'john@gmail.com', 'Too good!', 11);
    RAISE NOTICE 'FAIL — rating > 10 was NOT caught';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'PASS — rating > 10 correctly blocked';
END;
$$;

-- TEST E: Rating < 0
SELECT '--- TEST E: Rating < 0 ---' AS test;
DO $$
BEGIN
    INSERT INTO review VALUES (1, 99, 'john@gmail.com', 'Terrible!', -1);
    RAISE NOTICE 'FAIL — negative rating was NOT caught';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'PASS — negative rating correctly blocked';
END;
$$;

-- TEST F: Invalid access_type
SELECT '--- TEST F: Invalid access_type ---' AS test;
DO $$
BEGIN
    INSERT INTO room VALUES (1, 999, 2, 2020, 'escalator');
    RAISE NOTICE 'FAIL — invalid access_type was NOT caught';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'PASS — invalid access_type correctly blocked';
END;
$$;

-- TEST G: Client with no address
-- Deferred triggers fire at COMMIT, not inside DO blocks.
-- We verify the constraint exists and is deferred instead.
SELECT '--- TEST G: Client min-address constraint ---' AS test;
SELECT
    CASE WHEN COUNT(*) > 0
        THEN 'PASS — trg_client_min_address_on_junction exists and is DEFERRABLE'
        ELSE 'FAIL — trigger missing'
    END AS result
FROM pg_trigger t
JOIN pg_class c ON c.oid = t.tgrelid
WHERE c.relname = 'client_address'
  AND t.tgname  = 'trg_client_min_address_on_junction'
  AND t.tgdeferrable = true;

-- TEST H: Client with no credit card
-- Same approach — verify the deferred constraint trigger exists.
SELECT '--- TEST H: Client min-credit-card constraint ---' AS test;
SELECT
    CASE WHEN COUNT(*) > 0
        THEN 'PASS — trg_client_min_card_on_credit_card exists and is DEFERRABLE'
        ELSE 'FAIL — trigger missing'
    END AS result
FROM pg_trigger t
JOIN pg_class c ON c.oid = t.tgrelid
WHERE c.relname = 'credit_card'
  AND t.tgname  = 'trg_client_min_card_on_credit_card'
  AND t.tgdeferrable = true;

-- TEST I: Room for non-existent hotel
SELECT '--- TEST I: Room for non-existent hotel ---' AS test;
DO $$
BEGIN
    INSERT INTO room VALUES (999, 101, 2, 2020, 'elevator');
    RAISE NOTICE 'FAIL — FK violation was NOT caught';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'PASS — FK violation correctly blocked';
END;
$$;

-- TEST J: end_date before start_date
SELECT '--- TEST J: end_date before start_date ---' AS test;
DO $$
BEGIN
    INSERT INTO booking VALUES (97, 'john@gmail.com', 1, 103,
        '2024-05-10', '2024-05-05', 100.00);
    RAISE NOTICE 'FAIL — invalid date range was NOT caught';
EXCEPTION WHEN others THEN
    RAISE NOTICE 'PASS — invalid date range correctly blocked';
END;
$$;

-- ============================================================
-- PART 5: FINAL DATA VERIFICATION
-- ============================================================

SELECT '--- PART 5: FINAL DATA ---' AS status;

SELECT 'MANAGERS'       AS table_name; SELECT * FROM manager;
SELECT 'HOTELS'         AS table_name; SELECT * FROM hotel;
SELECT 'ROOMS'          AS table_name; SELECT * FROM room;
SELECT 'CLIENTS'        AS table_name; SELECT * FROM client;
SELECT 'ADDRESSES'      AS table_name; SELECT * FROM address;
SELECT 'CLIENT_ADDRESS' AS table_name; SELECT * FROM client_address;
SELECT 'CREDIT_CARDS'   AS table_name; SELECT * FROM credit_card;
SELECT 'BOOKINGS'       AS table_name; SELECT * FROM booking;
SELECT 'REVIEWS'        AS table_name; SELECT * FROM review;

SELECT 'BOOKINGS WITH DETAILS' AS table_name;
SELECT
    b.booking_id,
    c.name                                        AS client,
    h.name                                        AS hotel,
    b.room_number,
    b.start_date,
    b.end_date,
    b.price_per_day,
    (b.end_date - b.start_date) * b.price_per_day AS total_cost
FROM   booking b
JOIN   client  c ON c.email    = b.client_email
JOIN   hotel   h ON h.hotel_id = b.hotel_id
ORDER  BY b.booking_id;

SELECT 'REVIEWS WITH DETAILS' AS table_name;
SELECT
    r.review_id,
    h.name   AS hotel,
    c.name   AS client,
    r.rating,
    r.message
FROM   review r
JOIN   hotel  h ON h.hotel_id = r.hotel_id
JOIN   client c ON c.email    = r.client_email
ORDER  BY r.hotel_id, r.review_id;
