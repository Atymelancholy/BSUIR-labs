import sys
from typing import List

import psycopg2


DB_PARAMS = {
    "dbname": "animal_shelter",
    "user": "postgres",
    "password": "atymelancholy",
    "host": "localhost",
    "port": "5432",
}


def get_table_names(conn) -> List[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
        )
        return [r[0] for r in cur.fetchall()]


def get_primary_keys(conn, table_name: str) -> List[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                 ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.table_schema = 'public'
              AND tc.table_name = %s
              AND tc.constraint_type = 'PRIMARY KEY'
            ORDER BY kcu.ordinal_position
            """,
            (table_name,),
        )
        return [r[0] for r in cur.fetchall()]


def has_column(conn, table_name: str, column_name: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
              AND column_name = %s
            """,
            (table_name, column_name),
        )
        return cur.fetchone() is not None


def count_pk_duplicates(conn, table_name: str, pk_cols: List[str]) -> int:
    pk_expr = ", ".join([f'"{c}"' for c in pk_cols])
    sql = f"""
        SELECT COALESCE(SUM(cnt - 1), 0) AS extra_rows
        FROM (
            SELECT COUNT(*) AS cnt
            FROM "public"."{table_name}"
            GROUP BY {pk_expr}
            HAVING COUNT(*) > 1
        ) t
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        return int(cur.fetchone()[0])


def delete_pk_duplicates(conn, table_name: str, pk_cols: List[str]) -> int:
    """
    Удаляет дубликаты PK, оставляя одну строку на ключ.
    Выбор "какую оставить" делаем по системному столбцу ctid: оставляем максимальный ctid.
    """
    pk_expr = ", ".join([f'"{c}"' for c in pk_cols])
    sql = f"""
        WITH ranked AS (
            SELECT
                ctid,
                ROW_NUMBER() OVER (PARTITION BY {pk_expr} ORDER BY ctid DESC) AS rn
            FROM "public"."{table_name}"
        )
        DELETE FROM "public"."{table_name}" t
        USING ranked r
        WHERE t.ctid = r.ctid
          AND r.rn > 1
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        return cur.rowcount


def main() -> None:
    try:
        conn = psycopg2.connect(**DB_PARAMS)
    except Exception as e:
        print(f"[ERROR] Не удалось подключиться к PostgreSQL: {e}")
        sys.exit(1)

    try:
        tables = get_table_names(conn)
        print(f"[INFO] Таблиц найдено: {len(tables)}")

        total_deleted = 0
        touched_tables = 0

        for table in tables:
            pk_cols = get_primary_keys(conn, table)
            if not pk_cols and has_column(conn, table, "id"):
                # fallback: если PK не определён (или это view), используем id как "псевдо-PK"
                pk_cols = ["id"]
            if not pk_cols:
                continue

            extra = count_pk_duplicates(conn, table, pk_cols)
            if extra <= 0:
                continue

            print(f"[WARN] {table}: найдено лишних строк из-за дублей PK = {extra} (PK={pk_cols})")
            deleted = delete_pk_duplicates(conn, table, pk_cols)
            conn.commit()
            print(f"[OK] {table}: удалено строк = {deleted}")

            total_deleted += deleted
            touched_tables += 1

        if touched_tables == 0:
            print("[OK] Дубликатов PK не найдено.")
        else:
            print(f"[OK] Готово. Таблиц затронуто: {touched_tables}, всего удалено строк: {total_deleted}")

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Ошибка при удалении дублей PK: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()

