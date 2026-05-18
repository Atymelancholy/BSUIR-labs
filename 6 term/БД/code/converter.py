import psycopg2
import json
import os
import subprocess
import sys
from datetime import datetime, date, time
from decimal import Decimal

DB_PARAMS = {
    'dbname': 'animal_shelter',
    'user': 'postgres',
    'password': 'atymelancholy',
    'host': 'localhost',
    'port': '5432'
}

# Каталог относительно этого файла — чтобы работало и из IDE, и при вызове из GUI
_ROOT = os.path.dirname(os.path.abspath(__file__))
BERKELEY_DIR = os.path.join(_ROOT, "berkeley_export")


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, time):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, bytes):
            return obj.decode('utf-8', errors='ignore')
        return super().default(obj)


def _find_berkeley_tool(exe_name: str):
    possible_paths = [
        rf"C:\Program Files\Oracle\Berkeley DB 12cR1 6.0.30\bin\{exe_name}",
        rf"C:\Program Files\Oracle\Berkeley DB 12cR1 6.0.20\bin\{exe_name}",
        rf"C:\Program Files\Oracle\Berkeley DB 12cR1 6.0.18\bin\{exe_name}",
        rf"C:\Program Files (x86)\Oracle\Berkeley DB 12cR1 6.0.30\bin\{exe_name}",
        rf"C:\Program Files (x86)\Oracle\Berkeley DB 12cR1 6.0.20\bin\{exe_name}",
        rf"C:\Program Files (x86)\Oracle\Berkeley DB 12cR1 6.0.18\bin\{exe_name}",
        rf"C:\BerkeleyDB\bin\{exe_name}",
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    try:
        result = subprocess.run(["where.exe", exe_name], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().splitlines()[0].strip()
    except Exception:
        pass
    return None


def get_berkeley_tools():
    db_load = _find_berkeley_tool("db_load.exe")
    db_dump = _find_berkeley_tool("db_dump.exe")
    if not db_load:
        print("[ERROR] Не найден db_load.exe. Установите Berkeley DB (утилиты db_load/db_dump) и повторите запуск.")
        sys.exit(1)
    print(f"[OK] Найден db_load.exe: {db_load}")
    if db_dump:
        print(f"[OK] Найден db_dump.exe: {db_dump}")
    else:
        print("[WARN] db_dump.exe не найден (проверка результата будет пропущена).")
    return db_load, db_dump


class PostgresToBerkeleyConverter:
    def __init__(self, db_load_path: str, db_dump_path: str | None):
        self.db_load_path = db_load_path
        self.db_dump_path = db_dump_path
        self.pg_conn = None
        self.berkeley_dir = BERKELEY_DIR

    def connect_postgres(self):
        try:
            self.pg_conn = psycopg2.connect(**DB_PARAMS)
            print("[OK] Подключение к PostgreSQL успешно")
        except Exception as e:
            print(f"[ERROR] Ошибка подключения к PostgreSQL: {e}")
            sys.exit(1)

    def get_table_names(self):
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """
        with self.pg_conn.cursor() as cursor:
            cursor.execute(query)
            return [row[0] for row in cursor.fetchall()]

    def get_table_columns(self, table_name):
        query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """
        with self.pg_conn.cursor() as cursor:
            cursor.execute(query, (table_name,))
            return [row[0] for row in cursor.fetchall()]

    def get_primary_keys(self, table_name):
        query = """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                 ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_name = %s
                 AND tc.constraint_type = 'PRIMARY KEY'
            ORDER BY kcu.ordinal_position
        """
        with self.pg_conn.cursor() as cursor:
            cursor.execute(query, (table_name,))
            result = cursor.fetchall()
            if result:
                return [row[0] for row in result]
            # fallback (если PK не определён, но столбец id есть)
            return ['id']

    def get_table_data(self, table_name, columns):
        columns_str = ', '.join(columns)
        query = f'SELECT {columns_str} FROM "{table_name}"'
        with self.pg_conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    def create_berkeley_database_dir(self):
        if not os.path.exists(self.berkeley_dir):
            os.makedirs(self.berkeley_dir)
            print(f"[INFO] Создана директория: {self.berkeley_dir}")

    def convert_value(self, value):
        if value is None:
            return None
        elif isinstance(value, (datetime, date)):
            return value.isoformat()
        elif isinstance(value, time):
            return value.isoformat()
        elif isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, (int, float, str, bool)):
            return value
        elif isinstance(value, bytes):
            return value.decode('utf-8', errors='ignore')
        else:
            return str(value)

    @staticmethod
    def _escape_for_db_load_text(s: str) -> str:
        """
        db_load -T использует простой escape-механизм через '\'.
        Экранируем '\' и перевод строки/CR, чтобы не ломать формат "key\nvalue\n".
        """
        s = s.replace("\\", "\\\\")
        s = s.replace("\r", "\\0d")
        s = s.replace("\n", "\\0a")
        return s

    def _make_key(self, row, columns, pk_columns):
        parts = []
        for pk_col in pk_columns:
            idx = columns.index(pk_col)
            parts.append(str(self.convert_value(row[idx])))
        return "_".join(parts)

    def convert_table(self, table_name):
        print(f"\n[INFO] Конвертация таблицы: {table_name}")
        columns = self.get_table_columns(table_name)
        primary_keys = self.get_primary_keys(table_name)
        print(f"   Столбцы: {columns}")
        print(f"   Первичные ключи: {primary_keys}")

        data = self.get_table_data(table_name, columns)
        print(f"   Записей: {len(data)}")

        db_path = os.path.join(self.berkeley_dir, f"{table_name}.db")
        temp_load_path = os.path.join(self.berkeley_dir, f"temp_{table_name}.load.txt")

        # Готовим key/value пары для db_load (формат: key \n value \n)
        # СТРОГО по ТЗ: ключ (PK) должен быть уникальным. Дубликаты PK считаем ошибкой.
        records_count = 0
        kv_by_key = {}

        try:
            for row in data:
                try:
                    key_raw = self._make_key(row, columns, primary_keys)
                    key = self._escape_for_db_load_text(key_raw)

                    # Значение = JSON всех столбцов, КРОМЕ PK (как в табл. 2.1 методички)
                    row_dict = {}
                    for i, column in enumerate(columns):
                        if column in primary_keys:
                            continue
                        row_dict[column] = self.convert_value(row[i])

                    value_json = json.dumps(row_dict, ensure_ascii=False, cls=JSONEncoder)
                    value = self._escape_for_db_load_text(value_json)

                    if key in kv_by_key:
                        raise ValueError(f"Duplicate PK detected for key: {key_raw}")
                    kv_by_key[key] = value
                except Exception as e:
                    # В строгом режиме любая проблема с ключом/данными прерывает конвертацию таблицы
                    raise

            with open(temp_load_path, "w", encoding="utf-8", newline="\n") as f:
                for key, value in kv_by_key.items():
                    f.write(f"{key}\n{value}\n")
                    records_count += 1

            if records_count == 0:
                print("   [WARN] Нет записей для сохранения.")
                return

            # Создаём BerkeleyDB BTREE: key/value
            result = subprocess.run(
                [self.db_load_path, "-T", "-t", "btree", "-f", temp_load_path, db_path],
                capture_output=True,
                text=True
            )

            if result.returncode == 0 and os.path.exists(db_path):
                print(f"   [OK] Успешно: {records_count} записей -> {db_path}")
            else:
                stderr = (result.stderr or "").strip()
                stdout = (result.stdout or "").strip()
                print("   [ERROR] Ошибка db_load.")
                if stdout:
                    print(f"   STDOUT: {stdout}")
                if stderr:
                    print(f"   STDERR: {stderr}")
                return

            # Проверка результата db_dump (если доступна)
            if self.db_dump_path:
                dump_path = os.path.join(self.berkeley_dir, f"dump_{table_name}.txt")
                dump = subprocess.run([self.db_dump_path, "-p", db_path], capture_output=True, text=True)
                if dump.returncode == 0 and dump.stdout:
                    with open(dump_path, "w", encoding="utf-8") as df:
                        df.write(dump.stdout)
                    print(f"   [INFO] Dump сохранён: {dump_path}")
                else:
                    print("   [WARN] Не удалось получить db_dump для проверки.")
        finally:
            try:
                if os.path.exists(temp_load_path):
                    os.remove(temp_load_path)
            except Exception:
                pass

    def convert_all_tables(self):
        self.create_berkeley_database_dir()

        # Очищаем директорию от старых результатов
        if os.path.exists(self.berkeley_dir):
            for file in os.listdir(self.berkeley_dir):
                full_path = os.path.join(self.berkeley_dir, file)
                try:
                    if file.endswith(".db") or file.startswith("dump_") or file.startswith("temp_"):
                        os.remove(full_path)
                        continue
                    if file.endswith(".db-journal") and os.path.isdir(full_path):
                        # journaling каталоги от BDB SQL/SQLite интерфейса нам не нужны
                        for root, dirs, files in os.walk(full_path, topdown=False):
                            for name in files:
                                os.remove(os.path.join(root, name))
                            for name in dirs:
                                os.rmdir(os.path.join(root, name))
                        os.rmdir(full_path)
                except Exception:
                    continue

        tables = self.get_table_names()
        print(f"[INFO] Найдены таблицы: {tables}")
        converted = 0
        for table in tables:
            self.convert_table(table)
            converted += 1

        try:
            db_files = [f for f in os.listdir(self.berkeley_dir) if f.endswith(".db")]
        except Exception:
            db_files = []

        print(
            "[INFO] Итог: таблиц найдено = {found}, успешно сконвертировано = {converted}, файлов .db создано = {dbs}".format(
                found=len(tables),
                converted=converted,
                dbs=len(db_files),
            )
        )

    def close_connections(self):
        if self.pg_conn:
            self.pg_conn.close()
            print("[INFO] Соединение с PostgreSQL закрыто")


def main():
    db_load_path, db_dump_path = get_berkeley_tools()
    converter = PostgresToBerkeleyConverter(db_load_path, db_dump_path)
    try:
        converter.connect_postgres()
        converter.convert_all_tables()
        print("\n[OK] Конвертация завершена!")
    except Exception as e:
        print(f"\n[ERROR] Критическая ошибка: {e}")
        raise
    finally:
        converter.close_connections()


if __name__ == "__main__":
    main()