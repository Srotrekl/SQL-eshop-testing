# SQL Testovací Prostředí — E-shop

Praktické procvičení SQL dotazů pomocí pytest testů proti reálné PostgreSQL databázi.

## Prerekvizity

- Python 3.10+
- PostgreSQL běžící na localhost:5432

## Setup

### 1. Vytvoř databázi

```bash
createdb -U postgres eshop_test
```

Nebo v psql:

```sql
CREATE DATABASE eshop_test;
```

### 2. Nastav heslo (pokud se liší od "postgres")

Windows CMD:
```cmd
set PGPASSWORD=tvojeheslo
```

PowerShell:
```powershell
$env:PGPASSWORD="tvojeheslo"
```

Linux/Mac:
```bash
export PGPASSWORD=tvojeheslo
```

### 3. Nainstaluj závislosti

```bash
pip install -r requirements.txt
```

### 4. Inicializuj databázi

```bash
psql -U postgres -d eshop_test -f init_db.sql
```

### 5. Spusť testy

```bash
pytest test_db.py -v
```

## Struktura projektu

| Soubor | Popis |
|--------|-------|
| `init_db.sql` | Schéma tabulek + testovací data (10 uživatelů, 15 rezervací) |
| `conftest.py` | Pytest fixtures — připojení k DB, automatický ROLLBACK po každém testu |
| `test_db.py` | 5 testovacích scénářů |
| `requirements.txt` | Python závislosti |

## Testovací scénáře

| # | Scénář | SQL koncepty |
|---|--------|-------------|
| 1 | Vytvoření rezervace | `INSERT`, `RETURNING`, parametrizované dotazy |
| 2 | Uživatelé bez rezervace | `LEFT JOIN`, `IS NULL` na pravé tabulce |
| 3 | Filtrování podle ceny | `CASE`, `GROUP BY`, `COUNT`, `MIN`, `MAX`, `BETWEEN` |
| 4 | Zrušení rezervace | `UPDATE`, `WHERE`, `RETURNING`, `LIMIT` |
| 5 | Chybějící telefon | `IS NULL`, `IS NOT NULL`, `COALESCE`, `COUNT(*)` vs `COUNT(column)` |

## Jak to funguje

- `conftest.py` spustí `init_db.sql` jednou na začátku session (vytvoří tabulky + vloží data)
- Každý test dostane vlastní DB spojení v transakci
- Po skončení testu se provede `ROLLBACK` — seed data zůstanou nedotčená
- Testy se navzájem neovlivňují
