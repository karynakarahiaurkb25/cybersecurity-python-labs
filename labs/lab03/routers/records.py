import sqlite3
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status

from labs.lab03 import repository
from labs.lab03.schemas import RecordCreate, RecordRead, RecordReplace

router = APIRouter(prefix="/records", tags=["Записи"])


@router.get("", response_model=list[RecordRead])
def get_records(
    category_id: int | None = Query(None, gt=0),
    status: Literal["new", "in_progress", "done"] | None = None,
    min_value: float | None = Query(None, ge=0.0, le=100.0),
    q: str | None = Query(None, min_length=1, max_length=120),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return repository.get_records(category_id, status, min_value, q, limit, offset)


@router.get("/{record_id}", response_model=RecordRead)
def get_record(record_id: int):
    if record_id <= 0:
        raise HTTPException(status_code=422, detail="ID має бути додатним")
    rec = repository.get_record_by_id(record_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Запис не знайдено")
    return rec


@router.post("", response_model=RecordRead, status_code=status.HTTP_201_CREATED)
def create_record(item: RecordCreate):
    if not repository.get_category_by_id(item.category_id):
        raise HTTPException(status_code=404, detail="Вказана категорія не існує")
    try:
        return repository.create_record(item.model_dump())
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Запис із таким кодом вже існує")


@router.put("/{record_id}", response_model=RecordRead)
def update_record(record_id: int, item: RecordReplace):
    if record_id <= 0:
        raise HTTPException(status_code=422, detail="ID має бути додатним")
    if not repository.get_category_by_id(item.category_id):
        raise HTTPException(status_code=404, detail="Вказана категорія не існує")
    try:
        res = repository.update_record(record_id, item.model_dump())
        if not res:
            raise HTTPException(status_code=404, detail="Запис не знайдено")
        return res
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Конфлікт унікальності коду")


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(record_id: int):
    if record_id <= 0:
        raise HTTPException(status_code=422, detail="ID має бути додатним")
    if not repository.delete_record(record_id):
        raise HTTPException(status_code=404, detail="Запис не знайдено")


@router.post("/bulk", response_model=list[RecordRead], status_code=status.HTTP_201_CREATED)
def create_records_bulk(items: list[RecordCreate]):
    if not (1 <= len(items) <= 100):
        raise HTTPException(status_code=422, detail="Кількість записів у пакеті має бути від 1 до 100")

    codes = [i.code for i in items]
    if len(codes) != len(set(codes)):
        raise HTTPException(status_code=409, detail="Пакет містить повторювані коди")

    for item in items:
        if not repository.get_category_by_id(item.category_id):
            raise HTTPException(status_code=404, detail=f"Категорію id={item.category_id} не знайдено")

    try:
        return repository.create_records_bulk([i.model_dump() for i in items])
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Один із записів пакета порушує унікальність коду")