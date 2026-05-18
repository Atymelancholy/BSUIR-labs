import os
import shutil
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
import pandas as pd
import logging

from berkeley_manager import berkeley_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPERUSER_PASSWORD = "admin"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Berkeley DB Server starting...")
    yield
    berkeley_manager.close()


app = FastAPI(title="Animal Shelter API (Berkeley DB)", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Animal Shelter API - Berkeley DB"}


@app.get("/api/tables")
async def get_tables():
    tables = berkeley_manager.get_table_names()
    return {"tables": tables}


@app.get("/api/table/{table_name}")
async def get_table_data(
        request: Request,
        table_name: str,
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0)
):
    filters = {}
    for key, value in request.query_params.items():
        if key not in ["limit", "offset"]:
            filters[key] = value

    data = berkeley_manager.get_table_data(table_name, filters, limit, offset)
    total = len(berkeley_manager.get_table_data(table_name, filters, limit=10000))

    return {
        "data": data,
        "pagination": {"total": total, "limit": limit, "offset": offset},
        "filters_applied": filters
    }


@app.get("/api/table/{table_name}/schema")
async def get_table_schema(table_name: str):
    schema = berkeley_manager.get_table_schema(table_name)
    if not schema:
        raise HTTPException(status_code=404, detail=f"Table not found")
    return {"table": table_name, "columns": schema}


@app.get("/api/table/{table_name}/{record_id}")
async def get_record(table_name: str, record_id: int):
    record = berkeley_manager.get_record_by_id(table_name, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@app.post("/api/table/{table_name}")
async def create_record(
        table_name: str,
        record: Dict[str, Any] = Body(...)
):
    try:
        result = berkeley_manager.create_record(table_name, record)
        return {"message": "Record created", "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/table/{table_name}/{record_id}")
async def update_record(
        table_name: str,
        record_id: int,
        record: Dict[str, Any] = Body(...)
):
    updated = berkeley_manager.update_record(table_name, record_id, record)
    if not updated:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"message": "Record updated", "data": updated}


@app.delete("/api/table/{table_name}/{record_id}")
async def delete_record(table_name: str, record_id: int):
    success = berkeley_manager.delete_record(table_name, record_id)
    if not success:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"message": "Record deleted"}


@app.get("/api/queries")
async def list_queries():
    return {
        "queries": [
            {"name": "animals_treatment", "description": "Животные на лечении или карантине"},
            {"name": "animals_count_by_type", "description": "Статистика животных по типам"},
            {"name": "animals_with_volunteers", "description": "Животные с волонтерами"},
        ]
    }


@app.get("/api/queries/{query_name}")
async def execute_query(query_name: str):
    result = berkeley_manager.execute_query(query_name)
    return {"data": result, "query_name": query_name}


@app.post("/api/save-result")
async def save_result(
        data: List[Dict] = Body(..., embed=True),
        file_format: str = Body("excel", embed=True)
):
    os.makedirs("exports", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"result_{timestamp}.{'csv' if file_format == 'csv' else 'xlsx'}"
    filepath = os.path.join("exports", filename)

    df = pd.DataFrame(data)
    if file_format == "csv":
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
    else:
        df.to_excel(filepath, index=False)

    return {"message": "File saved", "filepath": filepath}


@app.post("/api/backup")
async def create_backup(
        password: str = Body(..., embed=True),
        table_name: Optional[str] = Body(None, embed=True)
):
    if password != SUPERUSER_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid password")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)

    if table_name:
        src = os.path.join("berkeley_export", f"{table_name}.db")
        if os.path.exists(src):
            shutil.copy2(src, backup_dir)
    else:
        for f in os.listdir("berkeley_export"):
            if f.endswith(".db"):
                shutil.copy2(os.path.join("berkeley_export", f), backup_dir)

    return {"message": "Backup created", "filepath": backup_dir}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)