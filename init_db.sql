-- ============================================================
-- E-shop Test Database: Schema + Seed Data
-- ============================================================

DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS users;

-- Tabulka uživatelů
CREATE TABLE users (
    id         SERIAL PRIMARY KEY,
    email      VARCHAR(255) NOT NULL UNIQUE,
    role       VARCHAR(20)  NOT NULL CHECK (role IN ('customer', 'admin')),
    phone      VARCHAR(20),                    -- záměrně nullable (scénář 5)
    created_at TIMESTAMP    NOT NULL DEFAULT now()
);

-- Tabulka rezervací
CREATE TABLE bookings (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER      NOT NULL REFERENCES users(id),
    item       VARCHAR(255) NOT NULL,
    price      NUMERIC(10,2) NOT NULL CHECK (price > 0),
    status     VARCHAR(20)  NOT NULL CHECK (status IN ('confirmed', 'pending', 'cancelled')),
    created_at TIMESTAMP    NOT NULL DEFAULT now()
);

-- ============================================================
-- Seed Data: 10 uživatelů, 15 rezervací
-- ============================================================

-- Users 3, 7 mají NULL phone (scénář 5)
-- Users 9, 10 nemají žádnou rezervaci (scénář 2)
INSERT INTO users (email, role, phone) VALUES
('alice@example.com',   'customer', '+420-111-0101'),
('bob@example.com',     'customer', '+420-111-0102'),
('carol@example.com',   'customer', NULL),
('dave@example.com',    'admin',    '+420-111-0104'),
('eve@example.com',     'customer', '+420-111-0105'),
('frank@example.com',   'customer', '+420-111-0106'),
('grace@example.com',   'customer', NULL),
('heidi@example.com',   'admin',    '+420-111-0108'),
('ivan@example.com',    'customer', '+420-111-0109'),
('judy@example.com',    'customer', '+420-111-0110');

-- 15 rezervací pro users 1-8 (users 9, 10 záměrně bez rezervací)
-- Ceny: 4× pod 100, 7× v rozsahu 100-500, 2× nad 500
INSERT INTO bookings (user_id, item, price, status) VALUES
(1, 'City Tour',         45.00,  'confirmed'),
(1, 'Museum Pass',      120.00,  'pending'),
(2, 'Boat Cruise',      350.00,  'confirmed'),
(2, 'Wine Tasting',      75.00,  'cancelled'),
(3, 'Helicopter Ride',  850.00,  'confirmed'),
(3, 'Cooking Class',    200.00,  'pending'),
(4, 'Spa Package',      450.00,  'confirmed'),
(5, 'Ski Lesson',       300.00,  'pending'),
(5, 'Skydiving',        600.00,  'confirmed'),
(5, 'Yoga Retreat',     180.00,  'cancelled'),
(6, 'Surf Lesson',       90.00,  'pending'),
(6, 'Scuba Diving',     400.00,  'confirmed'),
(7, 'Art Workshop',     150.00,  'pending'),
(8, 'Golf Round',       250.00,  'confirmed'),
(8, 'Tennis Lesson',     60.00,  'cancelled');
