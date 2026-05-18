from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional

# Параметры подключения к БД
DB_PARAMS = {
    'dbname': 'animal_shelter',
    'user': 'postgres',
    'password': 'atymelancholy',
    'host': 'localhost',
    'port': '5432'
}

app = FastAPI(title="Test API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db_connection():
    return psycopg2.connect(**DB_PARAMS)


@app.get("/")
async def root():
    return {"message": "Test API is working"}


@app.get("/animals")
async def get_animals(state_of_health: Optional[str] = None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        if state_of_health:
            # С фильтром
            cursor.execute(
                'SELECT * FROM "Animal" WHERE state_of_health = %s ORDER BY id',
                [state_of_health]
            )
        else:
            # Без фильтра
            cursor.execute('SELECT * FROM "Animal" ORDER BY id LIMIT 100')

        result = cursor.fetchall()
        cursor.close()
        conn.close()

        return {
            "filter": state_of_health,
            "count": len(result),
            "data": [dict(row) for row in result]
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/debug")
async def debug():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Проверяем все значения state_of_health
        cursor.execute('SELECT DISTINCT state_of_health FROM "Animal"')
        values = cursor.fetchall()

        # Проверяем структуру таблицы
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'Animal'
        """)
        columns = cursor.fetchall()

        cursor.close()
        conn.close()

        return {
            "distinct_values": [v[0] for v in values],
            "columns": columns
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)