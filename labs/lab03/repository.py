from contextlib import closing
from typing import Any

from labs.lab03.database import get_connection


def get_all_categories() -> list[dict[str, Any]]:
    with closing(get_connection()) as conn:
        rows = conn.execute("SELECT id, name FROM categories ORDER BY id ASC").fetchall()
        return [dict(r) for r in rows]


def get_category_by_id(cat_id: int) -> dict[str, Any] | None:
    with closing(get_connection()) as conn:
        row = conn.execute("SELECT id, name FROM categories WHERE id = ?", (cat_id,)).fetchone()
        return dict(row) if row else None


def create_category(name: str) -> dict[str, Any]:
    with closing(get_connection()) as conn:
        with conn:
            cursor = conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
            cat_id = cursor.lastrowid
        return {"id": cat_id, "name": name}


def delete_category(cat_id: int) -> None:
    with closing(get_connection()) as conn, conn:
        conn.execute("DELETE FROM categories WHERE id = ?", (cat_id,))


def get_records(
    category_id: int | None = None,
    status: str | None = None,
    min_value: float | None = None,
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    query = """
        SELECT r.id, r.code, r.title, r.category_id, r.value, r.status, c.name as category_name
        FROM records r
        JOIN categories c ON r.category_id = c.id
    """
    clauses = []
    params: list[Any] = []

    if category_id is not None:
        clauses.append("r.category_id = ?")
        params.append(category_id)
    if status is not None:
        clauses.append("r.status = ?")
        params.append(status)
    if min_value is not None:
        clauses.append("r.value >= ?")
        params.append(min_value)
    if q is not None:
        clauses.append("instr(r.title, ?) > 0")
        params.append(q)

    if clauses:
        query += " WHERE " + " AND ".join(clauses)

    query += " ORDER BY r.id ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with closing(get_connection()) as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_record_by_id(record_id: int) -> dict[str, Any] | None:
    query = """
        SELECT r.id, r.code, r.title, r.category_id, r.value, r.status, c.name as category_name
        FROM records r
        JOIN categories c ON r.category_id = c.id
        WHERE r.id = ?
    """
    with closing(get_connection()) as conn:
        row = conn.execute(query, (record_id,)).fetchone()
        return dict(row) if row else None


def create_record(data: dict[str, Any]) -> dict[str, Any]:
    query = """
        INSERT INTO records (code, title, category_id, value, status)
        VALUES (?, ?, ?, ?, ?)
    """
    with closing(get_connection()) as conn, conn:
        cursor = conn.execute(
            query,
            (
                data["code"],
                data["title"],
                data["category_id"],
                data["value"],
                data["status"],
            ),
        )
        record_id = cursor.lastrowid

    record = get_record_by_id(record_id)
    if not record:
        raise RuntimeError("Не вдалося отримати щойно створений запис.")
    return dict(record)


def update_record(record_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
    query = """
        UPDATE records
        SET code = ?, title = ?, category_id = ?, value = ?, status = ?
        WHERE id = ?
    """
    with closing(get_connection()) as conn:
        cursor = conn.execute(
            query,
            (
                data["code"],
                data["title"],
                data["category_id"],
                data["value"],
                data["status"],
                record_id,
            ),
        )
        conn.commit()

        if cursor.rowcount == 0:
            return None

    return get_record_by_id(record_id)


def delete_record(record_id: int) -> bool:
    with closing(get_connection()) as conn:
        cursor = conn.execute("DELETE FROM records WHERE id = ?", (record_id,))
        conn.commit()
        return cursor.rowcount > 0


def create_records_bulk(records_data: list[dict[str, Any]]) -> list[int]:
    query = """
        INSERT INTO records (code, title, category_id, value, status)
        VALUES (?, ?, ?, ?, ?)
    """
    new_ids = []
    conn = get_connection()
    with closing(conn), conn:
        for item in records_data:
            cursor = conn.execute(
                query,
                (
                    item["code"],
                    item["title"],
                    item["category_id"],
                    item["value"],
                    item["status"],
                ),
            )
            new_ids.append(cursor.lastrowid)
        return new_ids