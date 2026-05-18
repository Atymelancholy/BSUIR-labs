import os
from datetime import datetime
from typing import Optional, List
from database import db_manager


class BackupManager:
    """Класс для создания резервных копий"""

    def __init__(self, backup_dir: str = "exports"):
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self, table_name: Optional[str] = None) -> str:
        """
        Создает резервную копию таблицы или всей базы данных
        Возвращает путь к файлу бэкапа
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if table_name:
            filename = f"backup_{table_name}_{timestamp}.sql"
            backup_content = self._backup_table(table_name)
        else:
            filename = f"backup_full_database_{timestamp}.sql"
            backup_content = self._backup_all_tables()

        filepath = os.path.join(self.backup_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(backup_content)

        return filepath

    def _backup_table(self, table_name: str) -> str:
        """Создает SQL дамп одной таблицы"""
        content = []
        content.append(f"-- ===========================================")
        content.append(f"-- Backup of table: {table_name}")
        content.append(f"-- Created at: {datetime.now()}")
        content.append(f"-- ===========================================\n")

        # Получаем данные из таблицы
        data = db_manager.get_table_data(table_name, limit=10000)

        if data:
            columns = list(data[0].keys())
            content.append(f"INSERT INTO \"{table_name}\" ({', '.join([f'\"{c}\"' for c in columns])}) VALUES")

            rows = []
            for row in data:
                values = []
                for col in columns:
                    val = row[col]
                    if val is None:
                        values.append("NULL")
                    elif isinstance(val, (int, float)):
                        values.append(str(val))
                    else:
                        # Экранируем кавычки
                        escaped_val = str(val).replace("'", "''")
                        values.append(f"'{escaped_val}'")
                rows.append(f"({', '.join(values)})")

            content.append(",\n".join(rows) + ";")

        return "\n".join(content)

    def _backup_all_tables(self) -> str:
        """Создает SQL дамп всех таблиц"""
        content = []
        content.append(f"-- ===========================================")
        content.append(f"-- FULL DATABASE BACKUP")
        content.append(f"-- Created at: {datetime.now()}")
        content.append(f"-- ===========================================\n")

        tables = db_manager.get_table_names()

        for table in tables:
            content.append(self._backup_table(table))
            content.append("\n")

        return "\n".join(content)

    def restore_from_backup(self, filepath: str) -> bool:
        """
        Восстанавливает данные из файла бэкапа
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            # Разделяем на отдельные команды и выполняем
            commands = sql_content.split(';')
            for cmd in commands:
                cmd = cmd.strip()
                if cmd and not cmd.startswith('--'):
                    try:
                        db_manager.execute_query(cmd, fetch=False)
                    except Exception as e:
                        print(f"Ошибка при выполнении: {cmd[:100]}... - {e}")

            return True
        except Exception as e:
            print(f"Ошибка восстановления: {e}")
            return False


backup_manager = BackupManager()
