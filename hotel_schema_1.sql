-- ============================================================
-- CS480 – Hotel Management System
-- Phase 2: Relational Schema (PostgreSQL)
-- Translated from ER model per project spec
-- ============================================================

BEGIN;

-- ============================================================
-- STEP 1: STRONG ENTITIES
-- ============================================================

-- Manager: identified by SSN
CREATE TABLE manager (
    ssn    VARCHAR(20)  PRIMARY KEY,
    name   VARCHAR(255) NOT NULL,
    email  VARCHAR(255) NOT NULL
);

-- Client: identified by email (spec: "email address must be unique")
CREATE TABLE client (
    email  VARCHAR(255) PRIMARY KEY,
    name   VARCHAR(255) NOT NULL
);

-- Address: spec gives only street_name, street_number, city — no separate ID.
-- Composite PK is (street_name, street_number, city) per spec definition.
CREATE TABLE address (
    street_name   VARCHAR(255) NOT NULL,
    street_number VARCHAR(50)  NOT NULL,
    city          VARCHAR(255) NOT NULL,
    PRIMARY KEY (street_name, street_number, city)
);

-- Hotel: identified by hotel_id, has exactly one address (1:1 total)
CREATE TABLE hotel (
    hotel_id      INTEGER      PRIMARY KEY,
    name          VARCHAR(255) NOT NULL,
    -- Address stored inline via FK (hotel has exactly one address)
    street_name   VARCHAR(255) NOT NULL,
    street_number VARCHAR(50)  NOT NULL,
    city          VARCHAR(255) NOT NULL,
    FOREIGN KEY (street_name, street_number, city)
        REFERENCES address (street_name, street_number, city)
        ON DELETE RESTRICT
);

-- ============================================================
-- STEP 2: WEAK ENTITIES
-- ============================================================

-- Room: weak entity, identified by (hotel_id, room_number)
-- Spec: "A room is uniquely identified by the hotel and room number"
-- access_type: spec says "elevator or stairs"
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

-- Review: weak entity, identified by (hotel_id, review_id)
-- Spec: "A review is uniquely identified by a hotel and a reviewid"
-- Stores client_email because client writes the review (1:1 from review side)
-- Rating: spec says "integer from 0 to 10"
CREATE TABLE review (
    hotel_id     INTEGER      NOT NULL,
    review_id    SERIAL       NOT NULL,
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

-- ============================================================
-- STEP 3: RELATIONSHIPS WITH ADDRESS
-- ============================================================

-- Client HAS Address (1:N from client, 0:N from address)
-- Spec: "Each client should have at least one address, possibly multiple"
-- Modeled as junction table to support multiple addresses per client
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

-- Credit Card: belongs to exactly one client, has exactly one billing address
-- Spec: "A credit card belongs to exactly one client"
-- Spec: "Each credit card has exactly one billing address"
CREATE TABLE credit_card (
    card_number   VARCHAR(50)  PRIMARY KEY,
    client_email  VARCHAR(255) NOT NULL,
    -- Billing address stored inline via FK (1:1 mandatory)
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

-- ============================================================
-- STEP 4: BOOKING
-- ============================================================

-- Booking: strong entity, identified by its own unique booking_id
-- Spec: "associated with exactly one client and exactly one hotel room"
-- Stores (hotel_id, room_number) as composite FK to room
CREATE TABLE booking (
    booking_id    SERIAL         PRIMARY KEY,
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

-- Business rule: no two bookings for the same room may overlap.
-- This should be checked in application logic or with advanced database constraints.

COMMIT;
