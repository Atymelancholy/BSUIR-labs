import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional, Union, Tuple
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Параметры подключения к БД (ИЗМЕНИТЕ ПОД СВОИ!)
DB_PARAMS = {
    'dbname': 'animal_shelter',
    'user': 'postgres',
    'password': 'atymelancholy',
    'host': 'localhost',
    'port': '5432'
}


class DatabaseManager:
    """Класс для управления подключением и запросами к БД"""

    def __init__(self):
        self.connection = None

    def get_connection(self):
        """Устанавливает соединение с базой данных"""
        if not self.connection or self.connection.closed:
            try:
                self.connection = psycopg2.connect(**DB_PARAMS)
                logger.info("✅ Подключение к БД установлено")
            except Exception as e:
                logger.error(f"❌ Ошибка подключения к БД: {e}")
                raise e
        return self.connection

    def close_connection(self):
        """Закрывает соединение с БД"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            logger.info("✅ Подключение к базе данных закрыто")

    def execute_query(self, sql: str, params: Optional[Union[List, Tuple, Dict]] = None, fetch: bool = True) -> List[Dict[str, Any]]:
        """
        Выполняет SQL-запрос и возвращает результат в виде списка словарей
        """
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        result = []

        try:
            logger.info(f"\n⚡ Выполнение SQL: {sql}")
            if params:
                logger.info(f"📦 Параметры: {params}")

            if params and not isinstance(params, (list, tuple, dict)):
                params = [params]

            cursor.execute(sql, params)

            sql_upper = sql.strip().upper()
            if fetch and sql_upper.startswith('SELECT'):
                rows = cursor.fetchall()
                result = [dict(row) for row in rows]
                logger.info(f"✅ Получено записей: {len(result)}")
            elif fetch and 'RETURNING' in sql_upper:
                rows = cursor.fetchall()
                result = [dict(row) for row in rows]
                conn.commit()
                logger.info(f"✅ RETURNING: записей: {len(result)}")
            else:
                conn.commit()
                logger.info(f"✅ Запрос выполнен, затронуто строк: {cursor.rowcount}")
                result = [{"message": "Query executed successfully", "rows_affected": cursor.rowcount}]

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Ошибка выполнения запроса: {e}")
            logger.error(f"❌ SQL: {sql}")
            logger.error(f"❌ Параметры: {params}")
            raise e
        finally:
            cursor.close()

        return result

    def get_table_data(self, table_name: str, filters: Optional[Dict] = None,
                       limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Получает данные из таблицы с возможностью фильтрации
        """
        return self.get_table_data_with_filters(table_name, filters, limit, offset)

    def get_table_data_with_filters(self, table_name: str, filters: Optional[Dict] = None,
                                    limit: int = 100, offset: int = 0,
                                    order_by: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Получает данные из таблицы с фильтрацией (без TRIM для числовых полей)
        """
        query = f'SELECT * FROM "{table_name}"'
        params = []
        where_clauses = []

        if filters:
            logger.info(f"\n🔍 Обработка фильтров: {filters}")

            for key, value in filters.items():
                if value is None or value == "":
                    continue

                logger.info(f"  - Поле: '{key}' = '{value}'")

                # Обработка специальных операторов
                if " >=" in key:
                    field = key.replace(" >=", "")
                    where_clauses.append(f'"{field}" >= %s')
                    params.append(value)
                elif " <=" in key:
                    field = key.replace(" <=", "")
                    where_clauses.append(f'"{field}" <= %s')
                    params.append(value)
                elif " >" in key:
                    field = key.replace(" >", "")
                    where_clauses.append(f'"{field}" > %s')
                    params.append(value)
                elif " <" in key:
                    field = key.replace(" <", "")
                    where_clauses.append(f'"{field}" < %s')
                    params.append(value)
                elif " LIKE" in key or " like" in key:
                    field = key.replace(" LIKE", "").replace(" like", "")
                    where_clauses.append(f'"{field}" LIKE %s')
                    params.append(f'%{value}%')
                else:
                    # Точное совпадение без TRIM
                    where_clauses.append(f'"{key}" = %s')
                    params.append(value)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        if order_by:
            query += f" ORDER BY {order_by}"
        else:
            query += ' ORDER BY "id"'

        query += f" LIMIT {limit} OFFSET {offset}"

        logger.info(f"\n📌 ФИНАЛЬНЫЙ SQL: {query}")
        logger.info(f"📌 ПАРАМЕТРЫ: {params}")

        return self.execute_query(query, params)

    def count_records_with_filters(self, table_name: str, filters: Optional[Dict] = None) -> int:
        """
        Подсчитывает количество записей с учетом фильтров
        """
        query = f'SELECT COUNT(*) as count FROM "{table_name}"'
        params = []
        where_clauses = []

        if filters:
            for key, value in filters.items():
                if value is None or value == "":
                    continue

                if " >=" in key:
                    field = key.replace(" >=", "")
                    where_clauses.append(f'"{field}" >= %s')
                    params.append(value)
                elif " <=" in key:
                    field = key.replace(" <=", "")
                    where_clauses.append(f'"{field}" <= %s')
                    params.append(value)
                elif " >" in key:
                    field = key.replace(" >", "")
                    where_clauses.append(f'"{field}" > %s')
                    params.append(value)
                elif " <" in key:
                    field = key.replace(" <", "")
                    where_clauses.append(f'"{field}" < %s')
                    params.append(value)
                elif " LIKE" in key or " like" in key:
                    field = key.replace(" LIKE", "").replace(" like", "")
                    where_clauses.append(f'"{field}" LIKE %s')
                    params.append(f'%{value}%')
                else:
                    where_clauses.append(f'"{key}" = %s')
                    params.append(value)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        result = self.execute_query(query, params)
        return result[0]['count'] if result else 0

    def insert_record(self, table_name: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Добавляет новую запись в таблицу.
        Если столбец id есть, а в данных id не передан — подставляется следующий id
        (для схем без SERIAL/DEFAULT на id).
        """
        filtered_data = {k: v for k, v in data.items() if k not in ['id']}
        schema = self.get_table_schema(table_name)
        has_id_column = any(c.get('column_name') == 'id' for c in schema)
        explicit_id = data.get('id')
        use_generated_id = has_id_column and explicit_id is None

        if use_generated_id:
            col_list = ['"id"'] + [f'"{k}"' for k in filtered_data.keys()]
            placeholders = [
                f'(SELECT COALESCE(MAX("id"), 0) + 1 FROM "{table_name}")'
            ] + ['%s'] * len(filtered_data)
            values = list(filtered_data.values())
            query = (
                f'INSERT INTO "{table_name}" ({", ".join(col_list)}) '
                f'VALUES ({", ".join(placeholders)}) RETURNING *'
            )
        else:
            row = dict(filtered_data)
            if explicit_id is not None:
                row['id'] = explicit_id
            columns = ', '.join([f'"{col}"' for col in row.keys()])
            placeholders = ', '.join(['%s'] * len(row))
            values = list(row.values())
            query = f'INSERT INTO "{table_name}" ({columns}) VALUES ({placeholders}) RETURNING *'

        return self.execute_query(query, values)

    def update_record(self, table_name: str, record_id: int, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Обновляет запись в таблице по ID
        """
        filtered_data = {k: v for k, v in data.items() if k not in ['id']}

        if not filtered_data:
            return [{"message": "No fields to update"}]

        set_clause = ', '.join([f'"{key}" = %s' for key in filtered_data.keys()])
        values = list(filtered_data.values())
        values.append(record_id)

        query = f'UPDATE "{table_name}" SET {set_clause} WHERE id = %s RETURNING *'
        return self.execute_query(query, values)

    def delete_record(self, table_name: str, record_id: int) -> List[Dict[str, Any]]:
        """
        Удаляет запись из таблицы по ID
        """
        query = f'DELETE FROM "{table_name}" WHERE id = %s'
        return self.execute_query(query, [record_id], fetch=False)

    def get_table_names(self) -> List[str]:
        """
        Получает список всех таблиц в схеме public
        """
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        result = self.execute_query(query)
        return [row['table_name'] for row in result]

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Возвращает информацию о столбцах таблицы
        """
        query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position
        """
        return self.execute_query(query, [table_name])


# Создаем глобальный экземпляр менеджера БД
db_manager = DatabaseManager()