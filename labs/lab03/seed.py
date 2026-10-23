import json
import logging
import sqlite3
from contextlib import closing

from labs.lab03.database import BASE_DIR, get_connection, initialize_database

logger = logging.getLogger(__name__)


def seed_database() -> None:
    initialize_database()
    seed_file = BASE_DIR / "data" / "seed.json"
    if not seed_file.exists():
        logger.error(f"Файл {seed_file} не знайдено.")
        return

    with open(seed_file, encoding="utf-8") as f:
        data = json.load(f)

    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] > 0:
            print("База даних вже містить дані. Пропуск заповнення.")
            return

        try:
            with conn:
                for cat in data["categories"]:
                    conn.execute(
                        "INSERT INTO categories (id, name) VALUES (?, ?)",
                        (cat["id"], cat["name"]),
                    )
                for rec in data["records"]:
                    conn.execute(
                        """
                        INSERT INTO records (code, title, category_id, value, status)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (rec["code"], rec["title"], rec["category_id"], rec["value"], rec["status"]),
                    )
            print("Базу даних успішно заповнено початковими даними.")
        except sqlite3.IntegrityError as e:
            print(f"Помилка цілісності під час наповнення бази: {e}")
        except (OSError, ValueError) as e:
            print(f"Непередбачена помилка файлової системи чи даних: {e}")



if __name__ == "__main__":
    seed_database()