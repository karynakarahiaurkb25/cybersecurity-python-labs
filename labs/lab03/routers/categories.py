import sqlite3

from fastapi import APIRouter, HTTPException, status

from labs.lab03 import repository
from labs.lab03.schemas import CategoryCreate, CategoryRead

router = APIRouter(prefix="/categories", tags=["Категорії"])


@router.get("", response_model=list[CategoryRead])
def read_categories():
    return repository.get_all_categories()


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(cat: CategoryCreate):
    try:
        return repository.create_category(cat.name)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Категорія з такою назвою вже існує")


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int):
    if category_id <= 0:
        raise HTTPException(status_code=422, detail="ID має бути додатним числом")
    cat = repository.get_category_by_id(category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Категорію не знайдено")
    try:
        repository.delete_category(category_id)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Неможливо видалити непорожню категорію")