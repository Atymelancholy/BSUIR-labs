import os
import pandas as pd
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
import logging

from database import db_manager
from backup import backup_manager
from queries import ShelterQueries

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация суперпароля (можно вынести в переменные окружения)
SUPERUSER_PASSWORD = "admin"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Сервер запускается...")
    # Проверяем подключение к БД при старте
    try:
        db_manager.get_connection()
        logger.info("✅ Подключение к БД проверено")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
    yield
    logger.info("🛑 Закрытие соединения с БД...")
    db_manager.close_connection()


app = FastAPI(
    title="Animal Shelter API",
    version="2.0-full",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Обработчик ошибок валидации для отладки (можно оставить)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


@app.get("/")
async def root():
    return {"message": "Animal Shelter API"}


@app.get("/api/animals")
async def get_animals(
        state_of_health: Optional[str] = Query(None, description="Фильтр по состоянию здоровья")
):
    """
    Простой эндпоинт для тестирования фильтрации
    """
    try:
        logger.info(f"\n📋 Тестирование фильтрации по state_of_health = '{state_of_health}'")

        if state_of_health:
            # Используем TRIM для сравнения без пробелов
            query = 'SELECT * FROM "Animal" WHERE TRIM(state_of_health) = %s ORDER BY id'
            params = [state_of_health.strip()]

            logger.info(f"SQL: {query}")
            logger.info(f"Params: {params}")

            data = db_manager.execute_query(query, params)
        else:
            # Без фильтра - все записи
            data = db_manager.get_table_data("Animal", limit=100)

        return {
            "filter_applied": state_of_health,
            "count": len(data),
            "data": data
        }

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug/check")
async def debug_check():
    """
    Проверка структуры таблицы и данных
    """
    try:
        # Проверяем все значения state_of_health
        query = """
            SELECT DISTINCT 
                state_of_health,
                COUNT(*) as count,
                '"' || state_of_health || '"' as exact_value
            FROM "Animal" 
            GROUP BY state_of_health
            ORDER BY state_of_health
        """
        stats = db_manager.execute_query(query)

        # Получаем несколько записей для примера
        samples = db_manager.execute_query('SELECT * FROM "Animal" LIMIT 5')

        return {
            "total_records": len(db_manager.get_table_data("Animal", limit=1000)),
            "state_of_health_stats": stats,
            "sample_records": samples
        }

    except Exception as e:
        return {"error": str(e)}


# ----- Новые эндпоинты для лабораторной работы №2 -----

@app.get("/api/tables")
async def get_tables():
    """Возвращает список всех таблиц в базе данных"""
    try:
        tables = db_manager.get_table_names()
        return {"tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/table/{table_name}")
async def get_table_data(
    request: Request,
    table_name: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    order_by: Optional[str] = Query(None)
):
    """Получение данных из таблицы с фильтрацией"""
    # Проверяем существование таблицы
    tables = db_manager.get_table_names()
    if table_name not in tables:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

    # Собираем фильтры из всех query-параметров, исключая известные
    filters = {}
    for key, value in request.query_params.items():
        if key not in ["limit", "offset", "order_by"]:
            filters[key] = value

    data = db_manager.get_table_data_with_filters(
        table_name, filters, limit, offset, order_by
    )
    total = db_manager.count_records_with_filters(table_name, filters)
    return {
        "data": data,
        "pagination": {"total": total, "limit": limit, "offset": offset},
        "filters_applied": filters
    }


@app.get("/api/table/{table_name}/schema")
async def get_table_schema(table_name: str):
    """Возвращает схему таблицы (список полей)"""
    tables = db_manager.get_table_names()
    if table_name not in tables:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
    schema = db_manager.get_table_schema(table_name)
    return {"table": table_name, "columns": schema}


@app.get("/api/table/{table_name}/{record_id}")
async def get_record(table_name: str, record_id: int):
    try:
        tables = db_manager.get_table_names()
        if table_name not in tables:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
        data = db_manager.get_table_data_with_filters(table_name, {"id": record_id}, limit=1)
        if not data:
            raise HTTPException(status_code=404, detail="Record not found")
        return data[0]
    except Exception as e:
        logger.error(f"Ошибка в get_record: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/table/{table_name}")
async def create_record(table_name: str, record: Dict[str, Any] = Body(...)):
    """Создание новой записи"""
    tables = db_manager.get_table_names()
    if table_name not in tables:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
    try:
        result = db_manager.insert_record(table_name, record)
        return {"message": "Record created", "data": result[0] if result else None}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/table/{table_name}/{record_id}")
async def update_record(table_name: str, record_id: int, record: Dict[str, Any] = Body(...)):
    """Обновление записи по ID"""
    tables = db_manager.get_table_names()
    if table_name not in tables:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
    try:
        result = db_manager.update_record(table_name, record_id, record)
        if not result:
            raise HTTPException(status_code=404, detail="Record not found or no changes")
        return {"message": "Record updated", "data": result[0] if result else None}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/table/{table_name}/{record_id}")
async def delete_record(table_name: str, record_id: int):
    """Удаление записи по ID"""
    tables = db_manager.get_table_names()
    if table_name not in tables:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
    try:
        db_manager.delete_record(table_name, record_id)
        return {"message": "Record deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/queries")
async def list_queries():
    """Список доступных специальных запросов"""
    return {
        "queries": [
            {"name": name, "description": ShelterQueries.QUERY_DESCRIPTIONS.get(name, "")}
            for name in ShelterQueries.QUERIES.keys()
        ]
    }


@app.get("/api/queries/{query_name}")
async def execute_query(query_name: str):
    """Выполнение специального запроса по имени"""
    if query_name not in ShelterQueries.QUERIES:
        raise HTTPException(status_code=404, detail="Query not found")
    sql = ShelterQueries.QUERIES[query_name]
    try:
        result = db_manager.execute_query(sql)
        return {"data": result, "query_name": query_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/save-result")
async def save_result(
    data: List[Dict] = Body(..., embed=True),
    file_format: str = Body("excel", embed=True)
):
    """Сохраняет переданные данные в файл на сервере"""
    if not data:
        raise HTTPException(status_code=400, detail="No data to save")
    # Создаем директорию exports, если нет
    os.makedirs("exports", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if file_format == "csv":
        filename = f"query_result_{timestamp}.csv"
        filepath = os.path.join("exports", filename)
        pd.DataFrame(data).to_csv(filepath, index=False, encoding='utf-8')
    else:  # excel
        filename = f"query_result_{timestamp}.xlsx"
        filepath = os.path.join("exports", filename)
        pd.DataFrame(data).to_excel(filepath, index=False)
    return {"message": "File saved", "filepath": filepath}


@app.post("/api/backup")
async def create_backup(password: str = Body(..., embed=True), table_name: Optional[str] = Body(None, embed=True)):
    """Создание бэкапа (требуется пароль суперпользователя)"""
    if password != SUPERUSER_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid password")
    try:
        filepath = backup_manager.create_backup(table_name)
        return {"message": "Backup created", "filepath": filepath}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)