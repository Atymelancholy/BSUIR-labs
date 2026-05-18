import os
import json
from typing import List, Dict, Any, Optional

BERKELEY_DATA_DIR = "berkeley_export"

# Схемы таблиц
TABLE_SCHEMAS = {
    "Animal": ["id", "breed", "date_of_receipt", "state_of_health", "type", "id_aviary", "id_employee"],
    "Aviary": ["id", "square", "status", "type", "location"],
    "Employee": ["id", "snp", "telephone", "hire_date", "post"],
    "Volunteer": ["id", "snp", "telephone", "email", "duty"],
    "Adoptive_parent": ["id", "snp", "telephone", "approval_status", "address"],
    "Medical_procedure": ["id", "cost", "amount", "reason", "name"],
    "Feed_supply": ["id", "quantity", "delivery_date", "the_supplier", "type_of_feed"],
    "Adoptive_animal": ["id", "id_adoptive", "id_animal"],
    "Animal_volunteer": ["id", "id_volunteer", "id_animal"],
    "Animal_feed_supply": ["id", "id_animal", "id_feed_supply"],
    "Animal_medical_procedure": ["id", "id_animal", "id_medical", "procedure_date"],
}

ID_COUNTERS_FILE = "berkeley_id_counters.json"

# Кэш для данных
_DATA_CACHE = {}


def _load_data_from_dumps():
    """Загружает данные из текстовых файлов дампов, созданных converter.py"""
    global _DATA_CACHE

    if _DATA_CACHE:
        return _DATA_CACHE

    if not os.path.exists(BERKELEY_DATA_DIR):
        print(f"Directory {BERKELEY_DATA_DIR} not found")
        return {}

    for filename in os.listdir(BERKELEY_DATA_DIR):
        if filename.startswith("dump_") and filename.endswith(".txt"):
            table_name = filename[5:-4]  # убираем "dump_" и ".txt"
            filepath = os.path.join(BERKELEY_DATA_DIR, filename)

            records = []

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Парсим формат db_dump: key=ID data={...}
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('key='):
                        # Извлекаем key и data
                        parts = line.split(' data=', 1)
                        if len(parts) == 2:
                            key_part = parts[0][4:]  # убираем "key="
                            data_part = parts[1]

                            try:
                                # Парсим JSON
                                value = json.loads(data_part)
                                record = {"id": int(key_part)}
                                record.update(value)
                                records.append(record)
                            except json.JSONDecodeError:
                                # Может быть несколько строк JSON
                                try:
                                    # Пробуем найти JSON в строке
                                    import re
                                    json_match = re.search(r'\{.*\}', data_part)
                                    if json_match:
                                        value = json.loads(json_match.group())
                                        record = {"id": int(key_part)}
                                        record.update(value)
                                        records.append(record)
                                except:
                                    pass

                if records:
                    _DATA_CACHE[table_name] = records
                    print(f"Loaded {len(records)} records from {table_name}")

            except Exception as e:
                print(f"Error loading {filename}: {e}")

    # Если нет дампов, создаем тестовые данные
    if not _DATA_CACHE:
        _create_test_data()

    return _DATA_CACHE


def _create_test_data():
    """Создает тестовые данные для демонстрации"""
    global _DATA_CACHE

    # Тестовые данные для Animal
    _DATA_CACHE["Animal"] = [
        {"id": 1, "breed": "Британская короткошерстная", "date_of_receipt": "2023-01-15",
         "state_of_health": "Здоров", "type": "Кошка", "id_aviary": 1, "id_employee": 2},
        {"id": 2, "breed": "Немецкая овчарка", "date_of_receipt": "2023-02-20",
         "state_of_health": "Лечение", "type": "Собака", "id_aviary": 2, "id_employee": 1},
        {"id": 3, "breed": "Шотландская вислоухая", "date_of_receipt": "2023-03-10",
         "state_of_health": "Здоров", "type": "Кошка", "id_aviary": 1, "id_employee": 2},
    ]

    _DATA_CACHE["Aviary"] = [
        {"id": 1, "square": 25.5, "status": "Active", "type": "Indoor", "location": "Block A"},
        {"id": 2, "square": 50.0, "status": "Active", "type": "Outdoor", "location": "Block B"},
        {"id": 3, "square": 30.0, "status": "Maintenance", "type": "Indoor", "location": "Block A"},
    ]

    _DATA_CACHE["Employee"] = [
        {"id": 1, "snp": "Иванов Иван Иванович", "telephone": "+7-999-123-4567",
         "hire_date": "2020-01-15", "post": "Ветеринар"},
        {"id": 2, "snp": "Петрова Мария Сергеевна", "telephone": "+7-999-234-5678",
         "hire_date": "2021-03-20", "post": "Смотритель"},
    ]

    _DATA_CACHE["Volunteer"] = [
        {"id": 1, "snp": "Сидоров Алексей", "telephone": "+7-999-345-6789",
         "email": "alex@mail.ru", "duty": "Выгул собак"},
        {"id": 2, "snp": "Кузнецова Ольга", "telephone": "+7-999-456-7890",
         "email": "olga@mail.ru", "duty": "Уход за кошками"},
    ]

    _DATA_CACHE["Animal_volunteer"] = [
        {"id": 1, "id_volunteer": 1, "id_animal": 2},
        {"id": 2, "id_volunteer": 2, "id_animal": 1},
    ]

    print("Created test data (no dump files found)")


class BerkeleyDBManager:
    def __init__(self, data_dir: str = BERKELEY_DATA_DIR):
        self.data_dir = data_dir
        self._load_counters()
        # Загружаем данные из дампов или тестовые
        self._data = _load_data_from_dumps()

    def _load_counters(self):
        if os.path.exists(ID_COUNTERS_FILE):
            with open(ID_COUNTERS_FILE, 'r') as f:
                self.counters = json.load(f)
        else:
            self.counters = {}

    def _save_counters(self):
        with open(ID_COUNTERS_FILE, 'w') as f:
            json.dump(self.counters, f, indent=2)

    def _next_id(self, table: str) -> int:
        self.counters[table] = self.counters.get(table, 0) + 1
        self._save_counters()
        return self.counters[table]

    def get_table_names(self) -> List[str]:
        tables = list(TABLE_SCHEMAS.keys())
        return sorted(tables)

    def get_table_schema(self, table_name: str) -> List[Dict]:
        if table_name not in TABLE_SCHEMAS:
            return []
        return [{"column_name": col, "data_type": "text", "is_nullable": "YES"}
                for col in TABLE_SCHEMAS[table_name]]

    def get_table_data(self, table_name: str, filters: Dict = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        if table_name not in self._data:
            return []

        data = self._data[table_name].copy()

        # Применяем фильтры
        if filters:
            filtered = []
            for record in data:
                match = True
                for fk, fv in filters.items():
                    if fk in record:
                        if str(record[fk]).lower() != str(fv).lower():
                            match = False
                            break
                if match:
                    filtered.append(record)
            data = filtered

        # Применяем offset и limit
        result = data[offset:offset + limit]

        print(f"[DEBUG] {table_name}: total={len(data)}, returned={len(result)}")
        return result

    def get_record_by_id(self, table_name: str, record_id: int) -> Optional[Dict]:
        if table_name not in self._data:
            return None

        for record in self._data[table_name]:
            if record.get("id") == record_id:
                return record
        return None

    def create_record(self, table_name: str, data: Dict) -> Dict:
        new_id = self._next_id(table_name)
        record = {k: v for k, v in data.items() if k != 'id'}
        record["id"] = new_id

        if table_name not in self._data:
            self._data[table_name] = []
        self._data[table_name].append(record)

        return record

    def update_record(self, table_name: str, record_id: int, data: Dict) -> Optional[Dict]:
        if table_name not in self._data:
            return None

        for i, record in enumerate(self._data[table_name]):
            if record.get("id") == record_id:
                updated = {**record}
                for k, v in data.items():
                    if k != 'id':
                        updated[k] = v
                self._data[table_name][i] = updated
                return updated
        return None

    def delete_record(self, table_name: str, record_id: int) -> bool:
        if table_name not in self._data:
            return False

        for i, record in enumerate(self._data[table_name]):
            if record.get("id") == record_id:
                self._data[table_name].pop(i)
                return True
        return False

    def execute_query(self, query_name: str) -> List[Dict]:
        if query_name == "animals_treatment":
            data = self.get_table_data("Animal")
            return [a for a in data if a.get("state_of_health") in ["Лечение", "Карантин"]]

        elif query_name == "animals_count_by_type":
            data = self.get_table_data("Animal")
            counts = {}
            for a in data:
                t = a.get("type", "Unknown")
                counts[t] = counts.get(t, 0) + 1
            return [{"Тип животного": k, "Количество": v} for k, v in counts.items()]

        elif query_name == "animals_with_volunteers":
            animals = self.get_table_data("Animal")
            links = self.get_table_data("Animal_volunteer")
            volunteers = self.get_table_data("Volunteer")

            vol_map = {v["id"]: v for v in volunteers}
            result = []
            for link in links:
                animal = next((a for a in animals if a["id"] == link.get("id_animal")), None)
                volunteer = vol_map.get(link.get("id_volunteer"))
                if animal and volunteer:
                    result.append({
                        "ID": animal["id"],
                        "Тип": animal.get("type"),
                        "Порода": animal.get("breed"),
                        "Волонтер": volunteer.get("snp"),
                        "Обязанности": volunteer.get("duty")
                    })
            return result

        return []

    def close(self):
        pass


berkeley_manager = BerkeleyDBManager()