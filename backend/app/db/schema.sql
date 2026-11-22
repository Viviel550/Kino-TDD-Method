-- TABLES

CREATE TABLE genres (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE COLLATE NOCASE CHECK (length(trim(name)) > 0)
);

CREATE TABLE films (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    description TEXT,
    duration_min INTEGER NOT NULL CHECK (duration_min > 0),
    age_rating INTEGER NOT NULL DEFAULT 0 CHECK (age_rating BETWEEN 0 AND 18),
    poster_url TEXT,
    trailer_url TEXT,
    release_date TEXT CHECK (release_date IS NULL OR date(release_date) IS release_date),  -- YYYY-MM-DD format
    deleted_at INTEGER  -- soft delete
);

CREATE TABLE film_genres (
    film_id INTEGER NOT NULL REFERENCES films(id) ON DELETE CASCADE,
    genre_id INTEGER NOT NULL REFERENCES genres(id) ON DELETE RESTRICT,
    PRIMARY KEY (film_id, genre_id)
) WITHOUT ROWID;

CREATE TABLE rooms (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    cleaning_buffer_min INTEGER NOT NULL DEFAULT 15 CHECK (cleaning_buffer_min >= 0)
);

CREATE TABLE seats (
    id INTEGER PRIMARY KEY,
    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE RESTRICT,
    row_no INTEGER NOT NULL CHECK (row_no > 0),
    seat_no INTEGER NOT NULL CHECK (seat_no > 0),
    UNIQUE (room_id, row_no, seat_no)
);

CREATE TABLE screenings (
    id INTEGER PRIMARY KEY,
    film_id INTEGER NOT NULL REFERENCES films(id) ON DELETE RESTRICT,
    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE RESTRICT,
    start_time INTEGER NOT NULL,
    end_time INTEGER NOT NULL,  -- end_time = start_time + (duration_min + cleaning_buffer_min) * 60
    base_price_grosze INTEGER NOT NULL CHECK (base_price_grosze > 0),
    CHECK (end_time > start_time)
),

CREATE TABLE reservations (
    id TEXT PRIMARY KEY CHECK (  -- UUID v7 format
        length(id) = 36
        AND id NOT GLOB '*[^0-9a-f-]*'
        AND id GLOB '????????-????-7???-[89ab]???-????????????'
        ),
    screening_id INTEGER NOT NULL REFERENCES screenings(id) ON DELETE RESTRICT,
    customer_name TEXT NOT NULL CHECK (length(trim(customer_name)) > 0),
    email TEXT NOT NULL CHECK (email LIKE '_%@_%.__%' AND email NOT LIKE '% %'),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'expired')),
    confirmed INTEGER NOT NULL DEFAULT 0 CHECK (confirmed IN (0, 1)),
    created_at INTEGER NOT NULL,
    cancelled_at INTEGER,
    UNIQUE (id, screening_id),
    CHECK ((status = 'cancelled') = (cancelled_at IS NOT NULL))
) WITHOUT ROWID;

CREATE TABLE reservation_seats (
    reservation_id TEXT NOT NULL,
    screening_id INTEGER NOT NULL,
    seat_id INTEGER NOT NULL REFERENCES seats(id) ON DELETE RESTRICT,
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    PRIMARY KEY (reservation_id, seat_id),
    FOREIGN KEY (reservation_id, screening_id) REFERENCES reservations (id, screening_id) ON DELETE RESTRICT
) WITHOUT ROWID;

CREATE TABLE admin_accounts (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE CHECK (length(trim(username)) > 0),
    email TEXT NOT NULL UNIQUE COLLATE NOCASE CHECK (email LIKE '_%@_%.__%' AND email NOT LIKE '% %'),
    password_hash TEXT NOT NULL,
    created_at INTEGER NOT NULL
);

CREATE TABLE admin_sessions (
    token_hash TEXT PRIMARY KEY,  -- SHA-256 hash of the session token
    admin_id INTEGER NOT NULL REFERENCES admin_accounts(id) ON DELETE CASCADE,
    created_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    CHECK (expires_at > created_at)
) WITHOUT ROWID;


-- INDEXES

CREATE UNIQUE INDEX ux_active_seat_per_screening
    ON reservation_seats (screening_id, seat_id) WHERE active = 1;

CREATE INDEX ix_screenings_start ON screenings (start_time);
CREATE INDEX ix_screenings_film_start ON screenings (film_id, start_time);
CREATE INDEX ix_screenings_room_time ON screenings (room_id, start_time, end_time);
CREATE INDEX ix_reservations_screening ON reservations (screening_id, status);
CREATE INDEX ix_film_genres_genre ON film_genres (genre_id);
CREATE INDEX ix_sessions_expires ON admin_sessions (expires_at);
CREATE INDEX ix_sessions_admin ON admin_sessions (admin_id);


-- TRIGGERS

-- cannot delete (soft delete) a film with upcoming screenings with active reservations
CREATE TRIGGER trg_films_soft_delete_guard
BEFORE UPDATE OF deleted_at ON films
WHEN NEW.deleted_at IS NOT NULL AND OLD.deleted_at IS NULL
BEGIN
    SELECT RAISE(ABORT, 'FILM_HAS_ACTIVE_RESERVATIONS')
    WHERE EXISTS (
        SELECT 1 FROM screenings sc JOIN reservations r ON r.screening_id = sc.id
        WHERE sc.film_id = OLD.id AND sc.start_time > app_now() AND r.status = 'active');
END;

-- end_time of upcoming screenings depends on the film duration, so it cannot be updated if there are any
CREATE TRIGGER trg_films_duration_guard
BEFORE UPDATE OF duration_min ON films
WHEN NEW.duration_min <> OLD.duration_min
BEGIN
    SELECT RAISE(ABORT, 'FILM_HAS_FUTURE_SCREENINGS')
    WHERE EXISTS (SELECT 1 FROM screenings WHERE film_id = OLD.id AND start_time > app_now());
END;

CREATE TRIGGER trg_rooms_buffer_guard
BEFORE UPDATE OF cleaning_buffer_min ON rooms
WHEN NEW.cleaning_buffer_min <> OLD.cleaning_buffer_min
BEGIN
    SELECT RAISE(ABORT, 'ROOM_HAS_FUTURE_SCREENINGS')
    WHERE EXISTS (SELECT 1 FROM screenings WHERE room_id = OLD.id AND start_time > app_now());
END;

-- screenings
CREATE TRIGGER trg_screenings_bi
BEFORE INSERT ON screenings
BEGIN
    SELECT RAISE(ABORT, 'FILM_DELETED')  -- cannot schedule screenings for deleted films
    WHERE EXISTS (SELECT 1 FROM films WHERE id = NEW.film_id AND deleted_at IS NOT NULL);

    SELECT RAISE(ABORT, 'SCREENING_IN_PAST')  -- cannot schedule screenings in the past
    WHERE NEW.start_time <= app_now();

    SELECT RAISE(ABORT, 'SCREENING_END_MISMATCH')  -- end_time must match start_time + (duration_min + cleaning_buffer_min) * 60
    WHERE NEW.end_time <> NEW.start_time + (
        SELECT (f.duration_min + r.cleaning_buffer_min) * 60
        FROM films f, rooms r WHERE f.id = NEW.film_id AND r.id = NEW.room_id);

    SELECT RAISE(ABORT, 'SCREENING_OVERLAP')  -- cannot schedule overlapping screenings in the same room
    WHERE EXISTS (
        SELECT 1 FROM screenings o
        WHERE o.room_id = NEW.room_id
          AND o.start_time < NEW.end_time
          AND o.end_time > NEW.start_time);
END;

CREATE TRIGGER trg_screenings_bu
BEFORE UPDATE OF film_id, room_id, start_time, end_time ON screenings
BEGIN
    SELECT RAISE(ABORT, 'SCREENING_HAS_RESERVATIONS')  -- cannot change film or room of a screening with active reservations
    WHERE (NEW.film_id <> OLD.film_id OR NEW.room_id <> OLD.room_id)
      AND EXISTS (SELECT 1 FROM reservations WHERE screening_id = OLD.id AND status = 'active');

    SELECT RAISE(ABORT, 'FILM_DELETED')  -- cannot change film to a deleted film
    WHERE NEW.film_id <> OLD.film_id
      AND EXISTS (SELECT 1 FROM films WHERE id = NEW.film_id AND deleted_at IS NOT NULL);

    SELECT RAISE(ABORT, 'SCREENING_IN_PAST')  -- cannot change screening start time to the past
    WHERE NEW.start_time <> OLD.start_time AND NEW.start_time <= app_now();

    SELECT RAISE(ABORT, 'SCREENING_END_MISMATCH')  -- end_time must match start_time + (duration_min + cleaning_buffer_min) * 60
    WHERE NEW.end_time <> NEW.start_time + (
        SELECT (f.duration_min + r.cleaning_buffer_min) * 60
        FROM films f, rooms r WHERE f.id = NEW.film_id AND r.id = NEW.room_id);

    SELECT RAISE(ABORT, 'SCREENING_OVERLAP')  -- cannot schedule overlapping screenings in the same room
    WHERE EXISTS (
        SELECT 1 FROM screenings o
        WHERE o.id <> OLD.id
          AND o.room_id = NEW.room_id
          AND o.start_time < NEW.end_time
          AND o.end_time   > NEW.start_time);
END;

-- reservations
CREATE TRIGGER trg_reservations_bi
BEFORE INSERT ON reservations
BEGIN
    SELECT RAISE(ABORT, 'RESERVATION_MUST_START_ACTIVE')  -- new reservations must start as active
    WHERE NEW.status <> 'active';

    SELECT RAISE(ABORT, 'SCREENING_NOT_FOUND')  -- cannot create a reservation for a non-existing screening
    WHERE NOT EXISTS (SELECT 1 FROM screenings WHERE id = NEW.screening_id);

    SELECT RAISE(ABORT, 'SCREENING_NOT_BOOKABLE')  -- cannot create a reservation for a screening in the past, or for a deleted film
    WHERE NOT EXISTS (
        SELECT 1 FROM screenings sc JOIN films f ON f.id = sc.film_id
        WHERE sc.id = NEW.screening_id AND sc.start_time > app_now() AND f.deleted_at IS NULL);
END;

-- can only go from active to cancelled or expired
CREATE TRIGGER trg_reservations_status_guard
BEFORE UPDATE OF status ON reservations
WHEN OLD.status <> 'active'
BEGIN
    SELECT RAISE(ABORT, 'RESERVATION_NOT_ACTIVE');
END;

-- cannot cancel a reservation less than 30 minutes before the screening starts
CREATE TRIGGER trg_reservations_cancel_guard
BEFORE UPDATE OF status ON reservations
WHEN NEW.status = 'cancelled'
BEGIN
    SELECT RAISE(ABORT, 'CANT_CANCEL_LESS_THAN_30_MIN_BEFORE')
    WHERE app_now() + 30 * 60 > (SELECT start_time FROM screenings WHERE id = OLD.screening_id)
END;

CREATE TRIGGER trg_reservations_immutable
BEFORE UPDATE OF id, screening_id, customer_name, email, created_at ON reservations
BEGIN
    SELECT RAISE(ABORT, 'RESERVATION_IMMUTABLE_FIELD');
END;

-- free up seats when a reservation is cancelled or expired
CREATE TRIGGER trg_reservations_sync_active
AFTER UPDATE OF status ON reservations
BEGIN
    UPDATE reservation_seats SET active = (NEW.status = 'active')
    WHERE reservation_id = NEW.id;
END;

CREATE TRIGGER trg_reservations_no_delete
BEFORE DELETE ON reservations
BEGIN
    SELECT RAISE(ABORT, 'HISTORY_IS_PERMANENT');
END;

-- reservation_seats
CREATE TRIGGER trg_rs_bi
BEFORE INSERT ON reservation_seats
BEGIN
    SELECT RAISE(ABORT, 'RESERVATION_NOT_ACTIVE')  -- cannot add seats for a reservation that is not active
    WHERE NEW.active <> 1
       OR NOT EXISTS (SELECT 1 FROM reservations WHERE id = NEW.reservation_id AND status = 'active');

    SELECT RAISE(ABORT, 'SEAT_WRONG_ROOM')  -- cannot add seats that are not in the same room as the screening
    WHERE NOT EXISTS (
        SELECT 1 FROM seats st JOIN screenings sc ON sc.room_id = st.room_id
        WHERE st.id = NEW.seat_id AND sc.id = NEW.screening_id);

    SELECT RAISE(ABORT, 'TOO_MANY_SEATS')  -- cannot add more than 6 seats per reservation
    WHERE (SELECT COUNT(*) FROM reservation_seats WHERE reservation_id = NEW.reservation_id) >= 6;
END;

-- cannot change active status of each seat in reservation independently of the reservation status
CREATE TRIGGER trg_rs_active_guard
BEFORE UPDATE OF active ON reservation_seats
WHEN NEW.active <> (SELECT status = 'active' FROM reservations WHERE id = OLD.reservation_id)
BEGIN
    SELECT RAISE(ABORT, 'ACTIVE_FLAG_MANAGED_BY_TRIGGER');
END;

CREATE TRIGGER trg_rs_immutable
BEFORE UPDATE OF reservation_id, screening_id, seat_id ON reservation_seats
BEGIN
    SELECT RAISE(ABORT, 'RESERVATION_IMMUTABLE_FIELD');
END;

CREATE TRIGGER trg_rs_no_delete
BEFORE DELETE ON reservation_seats
BEGIN
    SELECT RAISE(ABORT, 'HISTORY_IS_PERMANENT');
END;


-- VIEWS

CREATE VIEW v_rooms AS
SELECT r.id, r.name, r.cleaning_buffer_min,
       (SELECT COUNT(*) FROM seats s WHERE s.room_id = r.id) AS seat_count
FROM rooms r;

CREATE VIEW v_films_public AS
SELECT f.id, f.title, f.description, f.duration_min, f.age_rating, f.poster_url, f.trailer_url, f.release_date,
       (SELECT group_concat(g.name, ', ')
        FROM film_genres fg JOIN genres g ON g.id = fg.genre_id
        WHERE fg.film_id = f.id) AS genres
FROM films f
WHERE f.deleted_at IS NULL;

CREATE VIEW v_screenings AS
SELECT sc.id AS screening_id, sc.film_id, f.title AS film_title, f.duration_min, f.age_rating,
       sc.room_id, ro.name AS room_name,
       sc.start_time, sc.end_time, datetime(sc.start_time, 'unixepoch') AS start_at_utc,
       sc.base_price_grosze,
       (sc.start_time > app_now()) AS bookable
FROM screenings sc
JOIN films f  ON f.id = sc.film_id AND f.deleted_at IS NULL
JOIN rooms ro ON ro.id = sc.room_id;

CREATE VIEW v_upcoming_screenings AS
SELECT * FROM v_screenings
WHERE start_time > app_now()
ORDER BY start_time;

CREATE VIEW v_seat_map AS
SELECT sc.screening_id, st.id AS seat_id, st.row_no, st.seat_no,
       CASE WHEN rs.seat_id IS NULL THEN 'free' ELSE 'taken' END AS status,
       sc.bookable
FROM v_screenings sc
JOIN seats st ON st.room_id = sc.room_id
LEFT JOIN reservation_seats rs
       ON rs.screening_id = sc.screening_id AND rs.seat_id = st.id AND rs.active = 1;

CREATE VIEW v_reservation_details AS
SELECT r.id AS code, r.status, r.confirmed, r.customer_name, r.email,
       r.created_at, r.cancelled_at,
       sc.id AS screening_id, f.title AS film_title, ro.name AS room_name,
       sc.start_time, datetime(sc.start_time, 'unixepoch') AS start_at_utc,
       (SELECT COUNT(*) FROM reservation_seats x WHERE x.reservation_id = r.id) AS seat_count,
       (SELECT COUNT(*) FROM reservation_seats x WHERE x.reservation_id = r.id) * sc.base_price_grosze AS total_cents
FROM reservations r
JOIN screenings sc ON sc.id = r.screening_id
JOIN films f       ON f.id  = sc.film_id
JOIN rooms ro      ON ro.id = sc.room_id;

CREATE VIEW v_reservation_seats AS
SELECT rs.reservation_id AS code, rs.seat_id, st.row_no, st.seat_no, rs.active
FROM reservation_seats rs JOIN seats st ON st.id = rs.seat_id;


-- VERSION
PRAGMA user_version = 1;
