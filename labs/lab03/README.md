# Лабораторна робота №3: REST API сервіс обліку використання сховищ (FastAPI + SQLite)

**Варіант 12:** Облік використання сховищ  
* **Одиниця вимірювання:** percent (%)  
* **Порогове значення:** 85.0%  

---

## Встановлення залежностей
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## Ініціалізація та початкове наповнення бази даних
```powershell
python -m labs.lab03.seed
```

## Запуск REST API сервера
```powershell
python -m uvicorn labs.lab03.main:app --reload
```

## Приклади основних HTTP-запитів (cURL)
Отримання інформації про варіант та студента
```powershell
curl -X GET "[http://127.0.0.1:8000/student](http://127.0.0.1:8000/student)"
```

## Перегляд усіх категорій
```powershell
curl -X GET "[http://127.0.0.1:8000/categories](http://127.0.0.1:8000/categories)"
```

## Отримання списку записів з фільтрацією та пагінацією
```powershell
curl -X GET "[http://127.0.0.1:8000/records?category_id=2&status=in_progress&limit=10&offset=0](http://127.0.0.1:8000/records?category_id=2&status=in_progress&limit=10&offset=0)"
```

## Створення нового запису
```powershell
curl -X POST "[http://127.0.0.1:8000/records](http://127.0.0.1:8000/records)" \
     -H "Content-Type: application/json" \
     -d '{
       "code": "V12-99",
       "title": "Тестове сховище резервів",
       "category_id": 1,
       "value": 45.0,
       "status": "new"
     }'
```

## Створення нового запису
```powershell
curl -X GET "[http://127.0.0.1:8000/records/1](http://127.0.0.1:8000/records/1)"
```

## Оновлення запису
```powershell
curl -X PUT "[http://127.0.0.1:8000/records/1](http://127.0.0.1:8000/records/1)" \
     -H "Content-Type: application/json" \
     -d '{
       "code": "V12-01",
       "title": "Оновлене вимірювання сховища 01",
       "category_id": 1,
       "value": 15.5,
       "status": "in_progress"
     }'
```

## Видалення запису
```powershell
curl -X DELETE "[http://127.0.0.1:8000/records/9](http://127.0.0.1:8000/records/9)"
```

## Пакетне додавання записів (Bulk Insert у транзакції)
```powershell
curl -X POST "[http://127.0.0.1:8000/records/bulk](http://127.0.0.1:8000/records/bulk)" \
     -H "Content-Type: application/json" \
     -d '[
       {
         "code": "V12-B1",
         "title": "Пакетний запис 1",
         "category_id": 1,
         "value": 30.0,
         "status": "new"
       },
       {
         "code": "V12-B2",
         "title": "Пакетний запис 2",
         "category_id": 2,
         "value": 70.0,
         "status": "done"
       }
     ]'
```






