# SQL ЗАПРОСЫ ИЗ ЛАБОРАТОРНЫХ РАБОТ №5-6

class ShelterQueries:
    """Класс с предопределенными SQL запросами"""

    # ЛР5: Простые запросы с WHERE
    ANIMALS_TREATMENT = """
        SELECT id AS "ID", type AS "Тип животного", breed AS "Порода", 
               state_of_health AS "Состояние здоровья", date_of_receipt AS "Дата поступления" 
        FROM "Animal" 
        WHERE state_of_health IN ('Лечение', 'Карантин') 
        ORDER BY type, breed
    """

    EMPLOYEES_RECENT = """
        SELECT snp AS "ФИО сотрудника", post AS "Должность", 
               telephone AS "Телефон", hire_date AS "Дата приема на работу" 
        FROM "Employee" 
        WHERE hire_date > '2021-01-01' 
        ORDER BY hire_date DESC
    """

    ANIMALS_ACTIVE_AVIARIES = """
        SELECT a.type AS "Тип животного", a.breed AS "Порода", 
               av.square AS "Площадь вольера", av.status AS "Статус вольера", 
               av.location AS "Местоположение" 
        FROM "Animal" a 
        INNER JOIN "Aviary" av ON a.id_aviary = av.id 
        WHERE av.status = 'Active' 
        ORDER BY a.type, av.square DESC
    """

    VOLUNTEERS_SEARCH = """
        SELECT snp AS "ФИО волонтера", telephone AS "Телефон", 
               email AS "Email", duty AS "Обязанности" 
        FROM "Volunteer" 
        WHERE duty LIKE '%собак%' OR duty LIKE '%кошками%' 
        ORDER BY duty
    """

    MEDICAL_PROCEDURES_COST_RANGE = """
        SELECT name AS "Название процедуры", cost AS "Стоимость, руб", 
               amount AS "Количество", reason AS "Причина проведения" 
        FROM "Medical_procedure" 
        WHERE cost BETWEEN 2000 AND 3500 
        ORDER BY cost ASC
    """

    # ЛР5: JOIN запросы
    ANIMALS_WITH_VOLUNTEERS = """
        SELECT a.id AS "ID животного", a.type AS "Тип", a.breed AS "Порода", 
               v.snp AS "ФИО волонтера", v.duty AS "Обязанности волонтера" 
        FROM "Animal" a 
        JOIN "Animal_volunteer" av ON a.id = av.id_animal 
        JOIN "Volunteer" v ON av.id_volunteer = v.id 
        ORDER BY a.type, a.breed
    """

    # ЛР6: Запросы с агрегатными функциями
    ANIMALS_COUNT_BY_TYPE = """
        SELECT type AS "Тип животного", COUNT(*) AS "Количество" 
        FROM "Animal" 
        GROUP BY type 
        ORDER BY "Количество" DESC
    """

    UNIQUE_BREEDS_IN_ACTIVE_AVIARIES = """
        SELECT COUNT(DISTINCT a.breed) AS "Уникальных пород" 
        FROM "Animal" a 
        JOIN "Aviary" av ON a.id_aviary = av.id 
        WHERE av.status = 'Active'
    """

    MAX_OUTDOOR_SQUARE = """
        SELECT type AS "Тип вольера", square AS "Площадь", 
               status AS "Статус", location AS "Местоположение" 
        FROM "Aviary" 
        WHERE type = 'Outdoor' AND square = (SELECT MAX(square) FROM "Aviary" WHERE type = 'Outdoor')
    """

    TOTAL_FEED_SUPPLY = """
        SELECT SUM(quantity) AS "Общее количество корма" 
        FROM "Feed_supply"
    """

    # ЛР6: GROUP BY с HAVING
    AVIARY_AVG_SQUARE = """
        SELECT type AS "Тип вольера", ROUND(AVG(square), 2) AS "Средняя площадь" 
        FROM "Aviary" 
        GROUP BY type 
        HAVING AVG(square) > 20
    """

    # ЛР6: INTERSECT, EXCEPT
    ANIMALS_BOTH_CHEAP_AND_EXPENSIVE = """
        SELECT a.id, a.breed, a.type 
        FROM "Animal" a 
        JOIN "Animal_medical_procedure" amp ON a.id = amp.id_animal 
        JOIN "Medical_procedure" mp ON amp.id_medical = mp.id 
        WHERE mp.cost < 2000

        INTERSECT

        SELECT a.id, a.breed, a.type 
        FROM "Animal" a 
        JOIN "Animal_medical_procedure" amp ON a.id = amp.id_animal 
        JOIN "Medical_procedure" mp ON amp.id_medical = mp.id 
        WHERE mp.cost > 2000 
        ORDER BY id
    """

    EMPTY_AVIARIES = """
        SELECT id, type, status, location 
        FROM "Aviary"

        EXCEPT

        SELECT av.id, av.type, av.status, av.location 
        FROM "Aviary" av 
        JOIN "Animal" a ON av.id = a.id_aviary
    """

    # Дополнительные запросы
    ANIMALS_WITH_DETAILS = """
        SELECT a.id, a.breed, a.type, a.state_of_health, 
               av.location AS aviary_location, av.status AS aviary_status,
               e.snp AS employee_name, e.post AS employee_post
        FROM "Animal" a
        JOIN "Aviary" av ON a.id_aviary = av.id
        JOIN "Employee" e ON a.id_employee = e.id
        ORDER BY a.id
    """

    VOLUNTEER_WORKLOAD = """
        SELECT v.snp AS volunteer_name, v.duty, COUNT(av.id_animal) AS animals_count
        FROM "Volunteer" v
        LEFT JOIN "Animal_volunteer" av ON v.id = av.id_volunteer
        GROUP BY v.id, v.snp, v.duty
        ORDER BY animals_count DESC
    """

    MEDICAL_COSTS_BY_ANIMAL = """
        SELECT a.breed, a.type, COUNT(amp.id_medical) AS procedures_count,
               SUM(mp.cost) AS total_cost
        FROM "Animal" a
        JOIN "Animal_medical_procedure" amp ON a.id = amp.id_animal
        JOIN "Medical_procedure" mp ON amp.id_medical = mp.id
        GROUP BY a.id, a.breed, a.type
        ORDER BY total_cost DESC
    """

    # Словарь для доступа к запросам
    QUERIES = {
        "animals_treatment": ANIMALS_TREATMENT,
        "employees_recent": EMPLOYEES_RECENT,
        "animals_active_aviaries": ANIMALS_ACTIVE_AVIARIES,
        "volunteers_search": VOLUNTEERS_SEARCH,
        "medical_procedures_cost_range": MEDICAL_PROCEDURES_COST_RANGE,
        "animals_with_volunteers": ANIMALS_WITH_VOLUNTEERS,
        "animals_count_by_type": ANIMALS_COUNT_BY_TYPE,
        "unique_breeds_active_aviaries": UNIQUE_BREEDS_IN_ACTIVE_AVIARIES,
        "max_outdoor_square": MAX_OUTDOOR_SQUARE,
        "total_feed_supply": TOTAL_FEED_SUPPLY,
        "aviary_avg_square": AVIARY_AVG_SQUARE,
        "animals_both_cheap_expensive": ANIMALS_BOTH_CHEAP_AND_EXPENSIVE,
        "empty_aviaries": EMPTY_AVIARIES,
        "animals_with_details": ANIMALS_WITH_DETAILS,
        "volunteer_workload": VOLUNTEER_WORKLOAD,
        "medical_costs_by_animal": MEDICAL_COSTS_BY_ANIMAL
    }

    # Описания запросов
    QUERY_DESCRIPTIONS = {
        "animals_treatment": "Животные на лечении или карантине",
        "employees_recent": "Сотрудники, принятые после 2021 года",
        "animals_active_aviaries": "Животные в активных вольерах",
        "volunteers_search": "Волонтеры по уходу за собаками/кошками",
        "medical_procedures_cost_range": "Медицинские процедуры (2000-3500 руб)",
        "animals_with_volunteers": "Животные с закрепленными волонтерами",
        "animals_count_by_type": "Статистика животных по типам",
        "unique_breeds_active_aviaries": "Уникальные породы в активных вольерах",
        "max_outdoor_square": "Вольеры Outdoor с максимальной площадью",
        "total_feed_supply": "Общее количество поставленного корма",
        "aviary_avg_square": "Типы вольеров со средней площадью > 20 м²",
        "animals_both_cheap_expensive": "Животные с дешевыми и дорогими процедурами",
        "empty_aviaries": "Пустые вольеры",
        "animals_with_details": "Животные с детальной информацией",
        "volunteer_workload": "Нагрузка на волонтеров",
        "medical_costs_by_animal": "Медицинские расходы по животным"
    }