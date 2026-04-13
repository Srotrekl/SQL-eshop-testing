"""
E-shop SQL testy — 10 scénářů pro praktické procvičení SQL.

Každý test běží ve vlastní transakci, která se po testu rollbackne.
Seed data tak zůstávají vždy v původním stavu.
"""

import psycopg2
import pytest


# ──────────────────────────────────────────────
# SCÉNÁŘ 1: Vytvoření rezervace
# SQL koncepty: INSERT, RETURNING, parametrizované dotazy
# ──────────────────────────────────────────────
def test_create_booking(db):
    with db.cursor() as cur:
        # Vlož nového uživatele
        cur.execute(
            """
            INSERT INTO users (email, role, phone)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            ("newuser@example.com", "customer", "+420-999-0001"),
        )
        user_id = cur.fetchone()[0]

        # Vlož rezervaci pro tohoto uživatele
        cur.execute(
            """
            INSERT INTO bookings (user_id, item, price, status)
            VALUES (%s, %s, %s, %s)
            RETURNING id, status, created_at
            """,
            (user_id, "Test Activity", 199.99, "confirmed"),
        )
        booking = cur.fetchone()
        booking_id, status, created_at = booking

        assert booking_id is not None, "ID rezervace by mělo být vygenerováno"
        assert status == "confirmed", "Status by měl být 'confirmed'"
        assert created_at is not None, "created_at by měl mít DEFAULT hodnotu"

        # Ověř že rezervace skutečně existuje v databázi
        cur.execute(
            "SELECT item, price, status FROM bookings WHERE id = %s",
            (booking_id,),
        )
        row = cur.fetchone()
        assert row[0] == "Test Activity"
        assert float(row[1]) == 199.99
        assert row[2] == "confirmed"


# ──────────────────────────────────────────────
# SCÉNÁŘ 2: Uživatelé bez rezervace
# SQL koncepty: LEFT JOIN, IS NULL na pravé tabulce
# ──────────────────────────────────────────────
def test_users_without_bookings(db):
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT u.id, u.email
            FROM users u
            LEFT JOIN bookings b ON u.id = b.user_id
            WHERE b.id IS NULL
            ORDER BY u.id
            """
        )
        rows = cur.fetchall()
        emails = [row[1] for row in rows]

        # V seed datech mají users 9 (ivan) a 10 (judy) nulové rezervace
        assert len(rows) == 2, f"Očekáváno 2 uživatelé bez rezervací, nalezeno {len(rows)}"
        assert "ivan@example.com" in emails
        assert "judy@example.com" in emails


# ──────────────────────────────────────────────
# SCÉNÁŘ 3: Filtrování podle ceny
# SQL koncepty: CASE, GROUP BY, COUNT, MIN, MAX, BETWEEN
# ──────────────────────────────────────────────
def test_price_filtering_and_statistics(db):
    with db.cursor() as cur:
        # Rozděl rezervace do cenových kategorií a spočítej statistiky
        cur.execute(
            """
            SELECT
                CASE
                    WHEN price < 100 THEN 'budget'
                    WHEN price BETWEEN 100 AND 500 THEN 'standard'
                    ELSE 'premium'
                END AS tier,
                COUNT(*)   AS cnt,
                MIN(price) AS min_price,
                MAX(price) AS max_price
            FROM bookings
            GROUP BY tier
            ORDER BY min_price
            """
        )
        rows = cur.fetchall()
        tiers = {row[0]: {"cnt": row[1], "min": float(row[2]), "max": float(row[3])} for row in rows}

        # Ověř že existují všechny tři cenové kategorie
        assert "budget" in tiers, "Měla by existovat kategorie 'budget' (pod 100)"
        assert "standard" in tiers, "Měla by existovat kategorie 'standard' (100-500)"
        assert "premium" in tiers, "Měla by existovat kategorie 'premium' (nad 500)"

        # Budget: všechny ceny musí být pod 100
        assert tiers["budget"]["max"] < 100, "Max cena v budget kategorii musí být pod 100"

        # Standard: ceny musí být v rozsahu 100-500
        assert tiers["standard"]["min"] >= 100, "Min cena v standard kategorii musí být >= 100"
        assert tiers["standard"]["max"] <= 500, "Max cena v standard kategorii musí být <= 500"

        # Premium: všechny ceny musí být nad 500
        assert tiers["premium"]["min"] > 500, "Min cena v premium kategorii musí být nad 500"

        # Celkový počet musí odpovídat 15 rezervacím
        total = sum(t["cnt"] for t in tiers.values())
        assert total == 15, f"Celkový počet rezervací by měl být 15, je {total}"


# ──────────────────────────────────────────────
# SCÉNÁŘ 4: Zrušení rezervace
# SQL koncepty: UPDATE, WHERE, RETURNING, LIMIT
# ──────────────────────────────────────────────
def test_cancel_booking(db):
    with db.cursor() as cur:
        # Najdi jednu potvrzenou rezervaci
        cur.execute(
            """
            SELECT id, status FROM bookings
            WHERE status = 'confirmed'
            LIMIT 1
            """
        )
        booking_id, original_status = cur.fetchone()
        assert original_status == "confirmed"

        # Změň status na 'cancelled'
        cur.execute(
            """
            UPDATE bookings
            SET status = 'cancelled'
            WHERE id = %s
            RETURNING id, status
            """,
            (booking_id,),
        )
        updated = cur.fetchone()
        assert updated[1] == "cancelled", "RETURNING by měl vrátit nový status"

        # Ověř že se status opravdu změnil v databázi (ne jen v RETURNING)
        cur.execute(
            "SELECT status FROM bookings WHERE id = %s",
            (booking_id,),
        )
        assert cur.fetchone()[0] == "cancelled", "Status v databázi se musí změnit"


# ──────────────────────────────────────────────
# SCÉNÁŘ 5: Chybějící telefon (NULL handling)
# SQL koncepty: IS NULL, IS NOT NULL, COALESCE, COUNT(*) vs COUNT(column)
# ──────────────────────────────────────────────
def test_null_phone_handling(db):
    with db.cursor() as cur:
        # 1) Najdi uživatele s NULL phone — musí se použít IS NULL, ne = NULL
        cur.execute(
            """
            SELECT id, email FROM users
            WHERE phone IS NULL
            ORDER BY id
            """
        )
        null_phone_users = cur.fetchall()
        assert len(null_phone_users) == 2, "Dva uživatelé by měli mít NULL phone"

        # 2) IS NOT NULL správně vyřadí uživatele bez telefonu
        cur.execute(
            """
            SELECT COUNT(*) FROM users
            WHERE phone IS NOT NULL
            """
        )
        with_phone = cur.fetchone()[0]
        assert with_phone == 8, "8 uživatelů by mělo mít vyplněný telefon"

        # 3) COALESCE nahradí NULL výchozí hodnotou
        cur.execute(
            """
            SELECT email, COALESCE(phone, 'N/A') AS phone_display
            FROM users
            ORDER BY id
            """
        )
        rows = cur.fetchall()
        for email, phone_display in rows:
            assert phone_display is not None, "COALESCE by měl zaručit, že žádná hodnota není NULL"

        # 4) COUNT(*) vs COUNT(column) — klasický SQL gotcha
        #    COUNT(*) počítá VŠECHNY řádky, COUNT(phone) jen ty kde phone IS NOT NULL
        cur.execute("SELECT COUNT(*) FROM users")
        total = cur.fetchone()[0]

        cur.execute("SELECT COUNT(phone) FROM users")
        count_phone = cur.fetchone()[0]

        assert total == 10, "COUNT(*) musí vrátit všech 10 uživatelů"
        assert count_phone == 8, "COUNT(phone) musí vrátit jen 8 (ignoruje NULL)"
        assert count_phone == total - 2, "Rozdíl mezi COUNT(*) a COUNT(phone) = počet NULL"


# ──────────────────────────────────────────────
# SCÉNÁŘ 6: Zákazníci s vysokými výdaji
# SQL koncepty: SUM, GROUP BY, HAVING, JOIN
# ──────────────────────────────────────────────
def test_high_value_customers(db):
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT u.email, SUM(b.price) AS total_spent
            FROM users u
            JOIN bookings b ON u.id = b.user_id
            GROUP BY u.id, u.email
            HAVING SUM(b.price) > 500
            ORDER BY total_spent DESC
            """
        )
        rows = cur.fetchall()
        emails = [row[0] for row in rows]
        totals = [float(row[1]) for row in rows]

        # eve: 300+600+180=1080, carol: 850+200=1050
        assert len(rows) == 2, f"Očekáváni 2 zákazníci s výdaji nad 500, nalezeno {len(rows)}"
        assert "eve@example.com" in emails
        assert "carol@example.com" in emails
        assert totals[0] > totals[1], "Výsledky musí být seřazeny sestupně"
        assert totals[0] == 1080.0, f"Nejvyšší útrata musí být 1080, je {totals[0]}"


# ──────────────────────────────────────────────
# SCÉNÁŘ 7: Nejdražší zákazník (subquery)
# SQL koncepty: subquery, SUM, GROUP BY, ORDER BY, LIMIT
# ──────────────────────────────────────────────
def test_top_spender(db):
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT u.email, SUM(b.price) AS total_spent
            FROM users u
            JOIN bookings b ON u.id = b.user_id
            GROUP BY u.id, u.email
            ORDER BY total_spent DESC
            LIMIT 1
            """
        )
        row = cur.fetchone()
        email, total_spent = row[0], float(row[1])

        assert email == "eve@example.com", f"Nejdražší zákazník musí být eve, je {email}"
        assert total_spent == 1080.0, f"Celková útrata musí být 1080, je {total_spent}"

        # Ověř pomocí subquery — jiný způsob stejného výsledku
        cur.execute(
            """
            SELECT u.email
            FROM users u
            JOIN bookings b ON u.id = b.user_id
            GROUP BY u.id, u.email
            HAVING SUM(b.price) = (
                SELECT MAX(user_total)
                FROM (
                    SELECT SUM(price) AS user_total
                    FROM bookings
                    GROUP BY user_id
                ) AS totals
            )
            """
        )
        subquery_row = cur.fetchone()
        assert subquery_row[0] == email, "Subquery musí vrátit stejného zákazníka"


# ──────────────────────────────────────────────
# SCÉNÁŘ 8: Porušení UNIQUE constraintu
# SQL koncepty: databázové integritní omezení, zpracování výjimek
# ──────────────────────────────────────────────
def test_duplicate_email_raises_error(db):
    with db.cursor() as cur:
        # Vloží unikátní email — musí projít
        cur.execute(
            "INSERT INTO users (email, role) VALUES (%s, %s)",
            ("unique@example.com", "customer"),
        )

    # Pokus o druhý INSERT se stejným emailem musí vyhodit výjimku
    with db.cursor() as cur:
        with pytest.raises(psycopg2.errors.UniqueViolation):
            cur.execute(
                "INSERT INTO users (email, role) VALUES (%s, %s)",
                ("unique@example.com", "customer"),
            )


# ──────────────────────────────────────────────
# SCÉNÁŘ 9: Přehled rezervací podle statusu
# SQL koncepty: GROUP BY, COUNT, ORDER BY na aliasu
# ──────────────────────────────────────────────
def test_booking_status_summary(db):
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT status, COUNT(*) AS cnt
            FROM bookings
            GROUP BY status
            ORDER BY cnt DESC
            """
        )
        rows = cur.fetchall()
        summary = {row[0]: row[1] for row in rows}

        assert summary.get("confirmed") == 7, f"Confirmed: očekáváno 7, je {summary.get('confirmed')}"
        assert summary.get("pending") == 5, f"Pending: očekáváno 5, je {summary.get('pending')}"
        assert summary.get("cancelled") == 3, f"Cancelled: očekáváno 3, je {summary.get('cancelled')}"
        assert sum(summary.values()) == 15, "Celkový počet musí být 15"


# ──────────────────────────────────────────────
# SCÉNÁŘ 10: Admini a jejich rezervace
# SQL koncepty: JOIN, WHERE s filtrací role, COUNT, GROUP BY
# ──────────────────────────────────────────────
def test_admin_users_booking_count(db):
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT u.email, COUNT(b.id) AS booking_count
            FROM users u
            LEFT JOIN bookings b ON u.id = b.user_id
            WHERE u.role = 'admin'
            GROUP BY u.id, u.email
            ORDER BY u.email
            """
        )
        rows = cur.fetchall()
        admins = {row[0]: row[1] for row in rows}

        assert len(admins) == 2, f"Očekáváni 2 admini, nalezeno {len(admins)}"
        assert "dave@example.com" in admins
        assert "heidi@example.com" in admins
        assert admins["dave@example.com"] == 1, "Dave má 1 rezervaci (Spa Package)"
        assert admins["heidi@example.com"] == 2, "Heidi má 2 rezervace (Golf Round, Tennis Lesson)"
