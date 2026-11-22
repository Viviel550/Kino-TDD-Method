INSERT INTO genres (name) VALUES
    ('Akcja'), ('Animacja'), ('Dramat'), ('Horror'),
    ('Komedia'), ('Romans'), ('Sci-Fi'), ('Thriller');

INSERT INTO rooms (id, name, cleaning_buffer_min) VALUES
    (1, 'Sala 1', 20),
    (2, 'Sala 2', 15);

WITH RECURSIVE
    rw(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM rw WHERE n < 10),
    st(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM st WHERE n < 12)
INSERT INTO seats (room_id, row_no, seat_no)
SELECT 1, rw.n, st.n FROM rw, st;

WITH RECURSIVE
    rw(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM rw WHERE n < 6),
    st(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM st WHERE n < 10)
INSERT INTO seats (room_id, row_no, seat_no)
SELECT 2, rw.n, st.n FROM rw, st;