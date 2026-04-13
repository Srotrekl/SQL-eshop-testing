# SQL Testovací Prostředí — E-shop

![Tests](https://github.com/Srotrekl/SQL-eshop-testing/actions/workflows/tests.yml/badge.svg)

Praktické procvičení SQL dotazů pomocí pytest testů proti reálné PostgreSQL databázi.

## Stack

- **PostgreSQL** — databázový server
- **pytest** — automatické testy
- **psycopg2** — Python konektor pro PostgreSQL
- **GitHub Actions** — CI/CD pipeline (testy se spustí při každém push)
- **DBeaver** — GUI nástroj pro průzkum a ladění dat

## Prerekvizity

- Python 3.10+
- PostgreSQL běžící na localhost:5432

## Setup

### 1. Vytvoř databázi

```bash
createdb -U postgres eshop_test
```

### 2. Zkopíruj `.env.example` jako `.env` a nastav heslo

```bash
cp .env.example .env
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
| `conftest.py` | Pytest fixtures — připojení k DB přes `.env`, automatický ROLLBACK po každém testu |
| `test_db.py` | 10 testovacích scénářů |
| `requirements.txt` | Python závislosti |
| `.env.example` | Šablona konfigurace DB připojení |
| `.github/workflows/tests.yml` | CI/CD pipeline — automatické spuštění testů na GitHubu |

## Testovací scénáře

| # | Scénář | SQL koncepty |
|---|--------|-------------|
| 1 | Vytvoření rezervace | `INSERT`, `RETURNING`, parametrizované dotazy |
| 2 | Uživatelé bez rezervace | `LEFT JOIN`, `IS NULL` na pravé tabulce |
| 3 | Filtrování podle ceny | `CASE`, `GROUP BY`, `COUNT`, `MIN`, `MAX`, `BETWEEN` |
| 4 | Zrušení rezervace | `UPDATE`, `WHERE`, `RETURNING`, `LIMIT` |
| 5 | Chybějící telefon | `IS NULL`, `IS NOT NULL`, `COALESCE`, `COUNT(*)` vs `COUNT(column)` |
| 6 | Zákazníci s vysokými výdaji | `SUM`, `GROUP BY`, `HAVING`, `JOIN` |
| 7 | Nejdražší zákazník | subquery, `ORDER BY`, `LIMIT`, `MAX` |
| 8 | Porušení UNIQUE constraintu | integritní omezení, zpracování výjimek v pytest |
| 9 | Přehled rezervací podle statusu | `GROUP BY`, `COUNT`, `ORDER BY` na aliasu |
| 10 | Admini a jejich rezervace | `LEFT JOIN`, `WHERE role`, `COUNT`, `GROUP BY` |

## Jak to funguje

- `conftest.py` spustí `init_db.sql` jednou na začátku session (vytvoří tabulky + vloží data)
- Každý test dostane vlastní DB spojení v transakci
- Po skončení testu se provede `ROLLBACK` — seed data zůstanou nedotčená
- Testy se navzájem neovlivňují
- Při každém `git push` GitHub Actions automaticky spustí celou testovací sadu
